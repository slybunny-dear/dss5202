"""Independent checks of research formulas, data provenance and failure cases."""
import copy
import csv
from decimal import Decimal as D
import hashlib
import json
import math
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code"))
from model import (STAGES, evaluate, evaluate_transport, load_config, normalize, rank,
                   transport_analysis, values)
from ahp import compute, matrix, ratio, weights_cr


def read_csv(path):
    with (ROOT / path).open(encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


class ResearchChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = load_config()
        cls.p = values(cls.cfg)
        cls.rows = {r["mode"]: r for r in evaluate(cls.cfg)}
        cls.raw, cls.people, cls.groups, _ = compute(cls.cfg)

    def test_independent_decimal_annual_formulas(self):
        shared = (D("14.8")+D(".84")+D(".99"))*6/26
        expected_e = {"new": shared+7*D(".109")+D(".31844"),
                      "used": shared+7*D(".109")+D(".31844"),
                      "rental": shared+6*D(".109")+240*D(".0287")}
        expected_c = {"new": D(65)+7, "used": D(52)+D("1.99")+7, "rental": 6*D(10)+24*D(2)}
        for mode, row in self.rows.items():
            self.assertAlmostEqual(row["annual_kgco2e"], float(expected_e[mode]), places=12)
            self.assertAlmostEqual(row["annual_spending_sgd"], float(expected_c[mode]), places=12)
            self.assertAlmostEqual(row["annual_kgco2e"], sum(row[s+"_kgco2e"] for s in STAGES))

    def test_transport_care_and_time_boundaries(self):
        for mode in ("new", "used"):
            r = self.rows[mode]
            self.assertEqual((r["cleaning_count"], r["passenger_km"], r["travel_sgd"], r["annual_minutes"]), (7, 0, 0, 120))
            self.assertEqual(r["allocated_delivery_vehicle_km"], 1)
        r = self.rows["rental"]
        self.assertEqual((r["cleaning_count"], r["passenger_km"], r["allocated_delivery_vehicle_km"], r["annual_minutes"]), (6, 240, 0, 780))
        self.assertEqual(r["care_sgd"], 0)

    def test_deposit_and_reference_mass_do_not_change_burdens(self):
        cfg = copy.deepcopy(self.cfg)
        cfg["parameters"]["refundable_deposit"]["value"] = 999
        cfg["parameters"]["reference_mass"]["value"] = 3
        for row in evaluate(cfg):
            self.assertEqual(row["annual_kgco2e"], self.rows[row["mode"]]["annual_kgco2e"])
            self.assertEqual(row["annual_spending_sgd"], self.rows[row["mode"]]["annual_spending_sgd"])

    def test_input_change_propagates_and_remaining_life_rejected(self):
        cfg = copy.deepcopy(self.cfg)
        cfg["parameters"]["events"]["value"] = 4
        row = evaluate(cfg)[0]
        self.assertEqual(row["purchase_sgd"], 65)  # purchase stays full price
        self.assertEqual(row["annual_spending_sgd"], 70)
        self.assertEqual(row["cleaning_count"], 5)
        self.assertNotEqual(row["annual_kgco2e"], self.rows["new"]["annual_kgco2e"])
        cfg["parameters"]["used_prior_wears"]["value"] = 23
        with self.assertRaisesRegex(ValueError, "remaining lifetime"):
            evaluate(cfg)

    def test_source_currency_prices_and_factors(self):
        quotes = {r["mode"]: r for r in read_csv("data/raw/market_quotes.csv")}
        for mode, key in (("new", "new_price"), ("used", "used_price"), ("rent", "rent_per_booking")):
            self.assertEqual(quotes[mode]["currency"], "SGD")
            self.assertEqual(quotes[mode]["currency_original"], "S$")
            self.assertEqual(float(quotes[mode]["price_sgd"]), self.p[key])
        services = {r["service_id"]: r for r in read_csv("data/raw/market_services.csv")}
        for key, sid in (("new_delivery_fee", "M2S_LB_SHIP"), ("used_delivery_fee", "M2S_CAR_U01"), ("refundable_deposit", "M2S_RENT_DEPOSIT")):
            self.assertEqual(self.p[key], float(services[sid]["price_sgd"]))
        factors = {r["factor_id"]: float(r["value"]) for r in read_csv("data/raw/literature_factors.csv")}
        for key, ids in {"manufacturing": ["EF_MFG_PES"], "distribution": ["EF_DIST_PES"],
                         "disposal": ["EF_EOL_PES_GROSS"], "cleaning": ["EF_WET_IT"],
                         "rail": ["EF_RAIL_DIRECT", "EF_RAIL_WTT"], "van": ["EF_VAN_DIRECT", "EF_VAN_WTT"]}.items():
            self.assertAlmostEqual(self.p[key], sum(factors[k] for k in ids), places=14)
        sources = json.loads((ROOT / "data/sources.json").read_text(encoding="utf-8"))
        for param in self.cfg["parameters"].values():
            for sid in param["source"].split(";"):
                self.assertIn(sid, sources)

    def test_original_files_unchanged(self):
        for item in json.loads((ROOT / "data/raw/source_manifest.json").read_text(encoding="utf-8")):
            path = ROOT / "data/raw" / Path(item["file"]).name
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), item["sha256"])
        meta = json.loads((ROOT / "evidence/environment/extraction_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(hashlib.sha256((ROOT / "data/raw/514322_Fulltext.pdf").read_bytes()).hexdigest(), meta["pdf_sha256"])

    def test_raw_completeness_directions_and_group_weights(self):
        self.assertEqual(len(self.raw), 18)
        rows = [r for r in self.people if r["mapping"] == "mild_3_2"]
        self.assertEqual(sum(r["complete"] for r in rows), 17)
        self.assertEqual(sum(r["cr_pass"] for r in rows), 11)
        self.assertEqual(len(self.groups), 1)
        self.assertEqual(len(self.people), 18)
        self.assertEqual(self.cfg["ahp"]["mappings"], {"mild_3_2": [1, 2, 3]})
        missing = next(r for r in rows if r["respondent_id"] == "R017")
        self.assertFalse(missing["complete"])
        self.assertEqual(missing["w_E"], "")
        self.assertLess(ratio(1, [1, 2, 3], False), 1)
        self.assertGreater(ratio(1, [1, 2, 3], True), 1)
        group = next(g for g in self.groups if g["mapping"] == "mild_3_2" and g["subset"] == "all_complete")
        # Independently verified regression values are checks, never production inputs.
        for key, target in zip(("w_E", "w_C", "w_V"), (.24097315381170287, .42953650955036643, .32949033663793076)):
            self.assertAlmostEqual(group[key], target, places=12)
        self.assertAlmostEqual(group["cr"], .005885350076795248, places=12)

    def test_ahp_independent_power_iteration_and_cr(self):
        examples = [matrix(1/3, 3, 3)] + [matrix(r["e_over_c"], r["e_over_v"], r["c_over_v"])
                                              for r in self.people if r["complete"]]
        for a in examples:
            w, lam, ci, cr = weights_cr(a, self.p["ri"])
            v = [1/3]*3
            for _ in range(1000):
                z = [sum(a[i][j]*v[j] for j in range(3)) for i in range(3)]
                total = sum(z)
                z = [x/total for x in z]
                if max(abs(x-y) for x, y in zip(z, v)) < 1e-14:
                    break
                v = z
            for x, y in zip(z, w):
                self.assertAlmostEqual(x, y, places=11)
            self.assertAlmostEqual(ci, (lam-3)/2, places=13)
            self.assertAlmostEqual(cr, ci/.52, places=13)
        with self.assertRaises(ValueError):
            weights_cr([[1, 2, 3], [1, 1, 2], [1, 1, 1]], .52)
        for code in (0, 6, 2.5, float("nan"), True):
            with self.assertRaises(ValueError):
                ratio(code, [1, 2, 3], True)

    def test_unclipped_scores_and_invalid_burdens(self):
        self.assertEqual(normalize([48, 0, 2160], [24, 360, 1080]), [-1, 1, -1])
        for bad in (-1, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                normalize([bad], [24])
        with self.assertRaises(ValueError):
            normalize([1], [0])

    def test_scores_and_rank_are_computed(self):
        g = next(g for g in self.groups if g["mapping"] == "mild_3_2" and g["subset"] == "all_complete")
        ranks = rank(list(self.rows.values()), [g[k] for k in ("w_E", "w_C", "w_V")], self.cfg)
        self.assertEqual([r["mode"] for r in ranks], ["used", "new", "rental"])
        for r in ranks:
            b = self.rows[r["mode"]]
            independent = ((1-b["annual_kgco2e"]/24)*g["w_E"] +
                           (1-b["annual_spending_sgd"]/360)*g["w_C"] +
                           (1-b["annual_minutes"]/1080)*g["w_V"])
            self.assertAlmostEqual(r["score"], independent, places=14)
        self.assertAlmostEqual(ranks[0]["score"], .8412285345110586, places=12)

    def test_transport_scenarios_independent_formula_and_fixed_components(self):
        shared = (D("14.8")+D(".84")+D(".99"))*6/26 + 6*D(".109")
        for alpha in (0, .2, .5, 1):
            rows = {r["mode"]: r for r in evaluate_transport(self.cfg, alpha)}
            r = rows["rental"]
            self.assertAlmostEqual(r["annual_kgco2e"], float(shared+D("6.888")*D(str(alpha))), places=12)
            self.assertAlmostEqual(r["annual_spending_sgd"], 60+48*alpha, places=12)
            self.assertAlmostEqual(r["annual_minutes"], 60+720*alpha, places=12)
            self.assertEqual(r["rental_sgd"], 60)
            self.assertEqual(r["cleaning_count"], 6)
            self.assertEqual(r["handling_minutes"], 60)
            for mode in ("new", "used"):
                self.assertEqual(rows[mode], self.rows[mode])
        for bad in (-.01, 1.01, float("nan"), float("inf"), True):
            with self.assertRaises(ValueError):
                evaluate_transport(self.cfg, bad)

    def test_transport_crossovers_and_ranking_regions(self):
        g = self.groups[0]
        w = [g[k] for k in ("w_E", "w_C", "w_V")]
        result = transport_analysis(self.cfg, w)
        # Direct equations are independent of the production scenario routine.
        base_emissions = float((D("14.8")+D(".84")+D(".99"))*6/26 + 6*D(".109"))
        intercept = w[0]*(1-base_emissions/24) + w[1]*(1-60/360) + w[2]*(1-60/1080)
        decrease = w[0]*6.888/24 + w[1]*48/360 + w[2]*720/1080
        self.assertAlmostEqual(result["rental_score_intercept"], intercept, places=13)
        self.assertAlmostEqual(result["rental_score_slope"], -decrease, places=13)
        for crossing, mode, expected in zip(result["thresholds"], ("used", "new"),
                                            (.0687043934994861, .10666162496186396)):
            b = self.rows[mode]
            score = w[0]*(1-b["annual_kgco2e"]/24)+w[1]*(1-b["annual_spending_sgd"]/360)+w[2]*(1-b["annual_minutes"]/1080)
            self.assertAlmostEqual(crossing["alpha"], (intercept-score)/decrease, places=13)
            self.assertAlmostEqual(crossing["alpha"], expected, places=12)
            ranks = {r["mode"]: r for r in rank(evaluate_transport(self.cfg, crossing["alpha"]), w, self.cfg)}
            self.assertEqual(ranks[mode]["rank"], ranks["rental"]["rank"])
            self.assertAlmostEqual(ranks[mode]["score"], ranks["rental"]["score"], places=13)
        for alpha, expected in ((0, ["rental", "used", "new"]),
                                (.09, ["used", "rental", "new"]),
                                (1, ["used", "new", "rental"])):
            self.assertEqual([r["mode"] for r in rank(evaluate_transport(self.cfg, alpha), w, self.cfg)], expected)

    def test_transport_coefficients_follow_parameters(self):
        w = [self.groups[0][k] for k in ("w_E", "w_C", "w_V")]
        cfg = copy.deepcopy(self.cfg)
        cfg["parameters"]["rail"]["value"] *= 2
        result = transport_analysis(cfg, w)
        coeff = result["rental_burden_coefficients"]
        self.assertAlmostEqual(coeff["annual_kgco2e"]["slope"], 13.776, places=12)
        self.assertEqual(coeff["annual_spending_sgd"]["slope"], 48)
        self.assertEqual(coeff["annual_minutes"]["slope"], 720)
        self.assertLess(result["thresholds"][0]["alpha"], .0687043934994861)
        for key in ("one_way_km", "fare_per_leg", "travel_minutes_per_leg"):
            cfg["parameters"][key]["value"] = 0
        flat = transport_analysis(cfg, w)
        self.assertEqual(flat["rental_score_slope"], 0)
        self.assertTrue(all(r["alpha"] is None for r in flat["thresholds"]))

    def test_exported_results_use_active_original_survey_analysis(self):
        groups = read_csv("results/ahp_group.csv")
        ranks = read_csv("results/rankings.csv")
        self.assertEqual(len(groups), 1)
        self.assertEqual(len(ranks), 3)
        for r in groups+ranks:
            self.assertEqual(r["mapping"], "mild_3_2")
            self.assertEqual(r["subset"], "all_complete")
        self.assertEqual(int(groups[0]["n"]), 17)
        people = read_csv("results/ahp_individual.csv")
        self.assertEqual(len(people), 18)
        self.assertEqual(sum(r["cr_pass"] == "True" for r in people), 11)
        summary = json.loads((ROOT/"results/analysis_summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["data_origin"], "original_survey")
        traffic = read_csv("results/transport_scenarios.csv")
        self.assertEqual(len(traffic), 309)
        for alpha in ("0.0", "1.0"):
            self.assertEqual(len([r for r in traffic if r["alpha"] == alpha]), 3)


if __name__ == "__main__":
    unittest.main()

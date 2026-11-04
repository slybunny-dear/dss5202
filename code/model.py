"""Single annual LCA, LCC and scoring model; values live in parameters.json."""
from pathlib import Path
import json
import math

ROOT = Path(__file__).resolve().parents[1]
MODES = ("new", "used", "rental")
STAGES = ("manufacturing", "distribution", "disposal", "cleaning", "transport")


def load_config():
    return json.loads((ROOT / "data/parameters.json").read_text(encoding="utf-8"))


def values(config):
    return {k: r["value"] for k, r in config["parameters"].items()}


def validate(config):
    p = values(config)
    for k, v in p.items():
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0:
            raise ValueError(f"Invalid nonnegative finite parameter: {k}={v}")
    for k in ("events", "lifetime_wears", "initial_owned_cleans", "cleans_per_wear",
              "used_prior_wears", "rental_legs", "delivery_legs", "delivery_batch", "rental_days"):
        if int(p[k]) != p[k]:
            raise ValueError(f"Expected whole count: {k}")
    for k in ("events", "lifetime_wears", "delivery_batch", "rental_days", "ri",
              "emissions_anchor", "cost_anchor", "time_anchor"):
        if p[k] <= 0:
            raise ValueError(f"Expected positive value: {k}")
    if p["used_prior_wears"] + p["events"] > p["lifetime_wears"]:
        raise ValueError("Used garment has insufficient remaining lifetime")
    if config["study"]["currency"] != "SGD":
        raise ValueError("Quotes are SGD; conversion requires new evidence")
    if p["resale"] != 0 or p["residual"] != 0:
        raise ValueError("This annual-spending study uses zero resale and residual")


def evaluate(config):
    validate(config)
    p = values(config)
    n = p["events"]
    rows = []
    for mode in MODES:
        rent = mode == "rental"
        cleans = n * p["cleans_per_wear"] + (0 if rent else p["initial_owned_cleans"])
        passenger_km = n * p["rental_legs"] * p["one_way_km"] if rent else 0
        delivery_km = 0 if rent else p["delivery_one_way_km"] * p["delivery_legs"] / p["delivery_batch"]
        row = dict(mode=mode, events=n, currency=config["study"]["currency"],
                   allocation_fraction=n / p["lifetime_wears"], cleaning_count=cleans,
                   passenger_km=passenger_km, allocated_delivery_vehicle_km=delivery_km)
        for stage in STAGES[:3]:
            row[stage + "_kgco2e"] = p[stage] * row["allocation_fraction"]
        row["cleaning_kgco2e"] = cleans * p["cleaning"]
        row["transport_kgco2e"] = passenger_km * p["rail"] + delivery_km * p["van"]
        row["annual_kgco2e"] = sum(row[s + "_kgco2e"] for s in STAGES)
        row["purchase_sgd"] = 0 if rent else p[mode + "_price"]
        row["delivery_sgd"] = 0 if rent else p[mode + "_delivery_fee"]
        row["rental_sgd"] = n * p["rent_per_booking"] if rent else 0
        row["care_sgd"] = n * p["rental_extra_care_fee"] if rent else cleans * p["home_care_fee"]
        row["travel_sgd"] = n * p["rental_legs"] * p["fare_per_leg"] if rent else 0
        row["annual_spending_sgd"] = sum(row[k] for k in
                                                ("purchase_sgd", "delivery_sgd", "rental_sgd", "care_sgd", "travel_sgd"))
        row["refundable_deposit_sgd"] = p["refundable_deposit"] if rent else 0
        row["order_minutes"] = 0 if rent else p["order_minutes"]
        row["care_minutes"] = 0 if rent else cleans * p["home_care_minutes"]
        row["handling_minutes"] = n * p["rental_handling_minutes"] if rent else 0
        row["travel_minutes"] = n * p["rental_legs"] * p["travel_minutes_per_leg"] if rent else 0
        row["annual_minutes"] = sum(row[k] for k in ("order_minutes", "care_minutes", "handling_minutes", "travel_minutes"))
        rows.append(row)
    return rows


def normalize(burdens, annual_anchors):
    if len(burdens) != len(annual_anchors):
        raise ValueError("Burden and anchor lengths differ")
    for value, anchor in zip(burdens, annual_anchors):
        if not math.isfinite(value) or value < 0 or not math.isfinite(anchor) or anchor <= 0:
            raise ValueError("Scores require finite nonnegative burdens and positive anchors")
    return [1 - value / anchor for value, anchor in zip(burdens, annual_anchors)]


def evaluate_transport(config, alpha):
    """Scale the attributed rental travel component; other components stay fixed."""
    if isinstance(alpha, bool) or not isinstance(alpha, (int, float)) or not math.isfinite(alpha) or not 0 <= alpha <= 1:
        raise ValueError("Transport attribution alpha must be finite and between 0 and 1")
    rows = evaluate(config)
    rental = next(row for row in rows if row["mode"] == "rental")
    for key in ("passenger_km", "transport_kgco2e", "travel_sgd", "travel_minutes"):
        rental[key] *= alpha
    rental["annual_kgco2e"] = sum(rental[s + "_kgco2e"] for s in STAGES)
    rental["annual_spending_sgd"] = sum(rental[k] for k in
        ("purchase_sgd", "delivery_sgd", "rental_sgd", "care_sgd", "travel_sgd"))
    rental["annual_minutes"] = sum(rental[k] for k in
        ("order_minutes", "care_minutes", "handling_minutes", "travel_minutes"))
    return rows


def rank(rows, weights, config):
    if len(weights) != 3 or any(not math.isfinite(x) or x <= 0 for x in weights) or not math.isclose(sum(weights), 1):
        raise ValueError("Three positive normalized weights required")
    p = values(config)
    anchors = [p[k] * p["events"] for k in ("emissions_anchor", "cost_anchor", "time_anchor")]
    output = []
    for row in rows:
        scores = normalize([row[k] for k in ("annual_kgco2e", "annual_spending_sgd", "annual_minutes")], anchors)
        output.append(dict(mode=row["mode"], emissions_score=scores[0], cost_score=scores[1],
                           convenience_score=scores[2], score=sum(w*s for w, s in zip(weights, scores)),
                           outside_reference_range=any(s < 0 or s > 1 for s in scores)))
    for row in output:
        # Preserve ties at analytical crossover points despite floating-point noise.
        row["rank"] = 1 + sum(other["score"] > row["score"] and
                              not math.isclose(other["score"], row["score"], rel_tol=0, abs_tol=1e-12)
                              for other in output)
    return sorted(output, key=lambda row: (row["rank"], row["mode"]))


def transport_analysis(config, weights):
    """Derive the linear travel-score response and crossings from model parameters."""
    low = evaluate_transport(config, 0)
    high = evaluate_transport(config, 1)
    low_scores = {r["mode"]: r["score"] for r in rank(low, weights, config)}
    high_scores = {r["mode"]: r["score"] for r in rank(high, weights, config)}
    rental_low = next(r for r in low if r["mode"] == "rental")
    rental_high = next(r for r in high if r["mode"] == "rental")
    intercept = low_scores["rental"]
    decrease = intercept - high_scores["rental"]
    coefficients = {
        key: {"intercept": rental_low[key], "slope": rental_high[key] - rental_low[key]}
        for key in ("annual_kgco2e", "annual_spending_sgd", "annual_minutes")
    }
    thresholds = [{"comparison": f"rental_vs_{mode}",
                   "alpha": (intercept - low_scores[mode])/decrease if decrease > 0 else None}
                  for mode in ("used", "new")]
    return {"rental_burden_coefficients": coefficients,
            "rental_score_intercept": intercept, "rental_score_slope": -decrease,
            "thresholds": thresholds}

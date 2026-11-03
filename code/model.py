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
        row["rank"] = 1 + sum(other["score"] > row["score"] for other in output)
    return sorted(output, key=lambda row: (row["rank"], row["mode"]))

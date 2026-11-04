"""Recompute the paper revision from the archived original survey and model.

Usage: python analysis/recompute.py
The default input repository is ../review_repo relative to this paper directory.
All writes are confined to the revision directory. Original inputs are read only.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import numpy as np
from openpyxl import load_workbook


OUTPUT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("--source-repo", type=Path, default=OUTPUT.parent / "review_repo")
args = parser.parse_args()
SOURCE = args.source_repo.resolve()
sys.path.insert(0, str(SOURCE / "code"))
import ahp
import model


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def weighted_score(burdens, weights, anchors):
    return sum(w * (1 - b / u) for w, b, u in zip(weights, burdens, anchors))


def description_row(question, response, count, valid_n):
    return {"question": question, "response": response, "count": count,
            "valid_n": valid_n, "percent": 100 * count / valid_n}


def write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


cfg = model.load_config()
raw, individual, groups, questions = ahp.compute(cfg)
annual = model.evaluate(cfg)
p = model.values(cfg)
anchors = [p[k] * p["events"] for k in ("emissions_anchor", "cost_anchor", "time_anchor")]
assert p["events"] == 6
assert len(raw) == 18
book_path = SOURCE / "data/raw/survey_18.xlsx"
book = load_workbook(book_path, read_only=True, data_only=True)
try:
    records = list(book[cfg["ahp"]["sheet"]].iter_rows(min_row=2, values_only=True))
    records = [r for r in records if any(v is not None for v in r)]
finally:
    book.close()
assert len(records) == len(raw)

q1 = Counter(r[1] for r in records)
q2 = Counter(r[2] for r in records)
q4 = Counter(r[4] for r in records)
description = [description_row("Q1: Student status", "Studying in Singapore", q1["是｜Yes"], 18)]
for key, label in [("0", "0"), ("1–2", "1--2"), ("3–4", "3--4"),
                   ("5–6", "5--6"), ("7或更多｜7 or more", "7 or more")]:
    description.append(description_row("Q2: Events in past 12 months", label, q2[key], 18))
for key, label in [("大概愿意｜Probably yes", "Probably willing"),
                   ("不确定｜Unsure", "Uncertain"),
                   ("大概不愿意｜Probably no", "Probably unwilling"),
                   ("肯定不愿意｜Definitely no", "Definitely unwilling")]:
    description.append(description_row("Q4: Same-style reuse", label, q4[key], 18))

direction_summary = []
for q, col, low, middle, high in [
    ("Q8: Emissions vs. cost", 9, "Emissions", "Equal importance", "Cost"),
    ("Q9: Emissions vs. convenience", 10, "Convenience", "Midpoint", "Emissions"),
    ("Q10: Cost vs. convenience", 11, "Cost", "Midpoint", "Convenience"),
]:
    codes = [int(r[col]) for r in records if r[col] not in (None, "")]
    counts = Counter(codes)
    item = {"question": q, "valid_n": len(codes), "missing_n": 18-len(codes),
            "code_counts": {str(k): counts[k] for k in range(1, 6)}, "directions": []}
    for label, count, code_group in [(low, sum(counts[k] for k in (1, 2)), [1, 2]),
                                    (middle, counts[3], [3]),
                                    (high, sum(counts[k] for k in (4, 5)), [4, 5])]:
        row = description_row(q, label, count, len(codes))
        row["codes"] = code_group
        item["directions"].append(row)
    direction_summary.append(item)

diagnostics = {}
for mapping in cfg["ahp"]["mappings"]:
    complete = [r for r in individual if r["mapping"] == mapping and r["complete"]]
    ri_checks = []
    for ri in (.52, .58):
        passed = [r["respondent_id"] for r in complete if r["ci"] / ri <= .1]
        ri_checks.append({"ri": ri, "pass_n": len(passed), "complete_n": len(complete), "passed_ids": passed})
    distribution = Counter(round(r["cr"], 12) for r in complete)
    diagnostics[mapping] = {"complete_n": len(complete), "ri_checks": ri_checks,
                            "cr_distribution_ri_052": [{"cr": k, "n": v} for k, v in sorted(distribution.items())]}

main_ind = [r for r in individual if r["mapping"] == "main_5_3" and r["complete"]]
main_pass = [r for r in main_ind if r["cr_pass"]]
assert len(main_ind) == 17 and len(main_pass) == 2
assert all([int(r[q]) for q in ("q8", "q9", "q10")] == [3, 3, 3] for r in main_pass)


def group_method(key, label, mapping, subset):
    g = next(r for r in groups if r["mapping"] == mapping and r["subset"] == subset)
    return {"key": key, "label": label, "mapping": mapping, "aggregation": "AIJ",
            "n": g["n"], "individual_pass_n": sum(r["cr_pass"] for r in individual if r["mapping"] == mapping),
            "weights": [g[k] for k in ("w_E", "w_C", "w_V")], "group_cr": g["cr"],
            "group_cr_ri_058": g["ci"] / .58, "group_ci": g["ci"]}


methods = [group_method("main_aij", "Main AIJ", "main_5_3", "all_complete"),
           group_method("mild_aij", "Mild AIJ", "mild_3_2", "all_complete")]
aip = [sum(r[k] for r in main_ind)/len(main_ind) for k in ("w_E", "w_C", "w_V")]
methods.append({"key": "main_aip", "label": "Main AIP", "mapping": "main_5_3",
                "aggregation": "Arithmetic mean of individual priority vectors", "n": 17,
                "individual_pass_n": 2, "weights": aip, "group_cr": None, "group_cr_ri_058": None})
methods.append({"key": "equal", "label": "Equal weights", "mapping": None,
                "aggregation": "Normative equal-weight benchmark", "n": None,
                "individual_pass_n": None, "weights": [1/3]*3, "group_cr": None,
                "group_cr_ri_058": None,
                "equivalent_observed_subset": {"ids": [r["respondent_id"] for r in main_pass],
                                               "n": 2, "each_response": [3, 3, 3], "group_cr": 0}})
methods.append(group_method("mild_pass_aij", "Mild AIJ, screened", "mild_3_2", "cr_pass"))

by_mode = {r["mode"]: r for r in annual}
rent = by_mode["rental"]
traffic_intercepts = [rent["annual_kgco2e"] - rent["transport_kgco2e"],
                      rent["annual_spending_sgd"] - rent["travel_sgd"],
                      rent["annual_minutes"] - rent["travel_minutes"]]
traffic_slopes = [rent["transport_kgco2e"], rent["travel_sgd"], rent["travel_minutes"]]
burden_keys = ["annual_kgco2e", "annual_spending_sgd", "annual_minutes"]
for method in methods:
    assert abs(sum(method["weights"])-1) < 1e-12
    method["baseline_scores"] = model.rank(annual, method["weights"], cfg)
    scores = {r["mode"]: r["score"] for r in method["baseline_scores"]}
    sr0 = weighted_score(traffic_intercepts, method["weights"], anchors)
    slope = sum(w*b/u for w, b, u in zip(method["weights"], traffic_slopes, anchors))
    thresholds = {mode: (sr0-scores[mode])/slope for mode in ("used", "new")}
    for mode, alpha in thresholds.items():
        assert 0 <= alpha <= 1
        assert abs(sr0 - slope*alpha - scores[mode]) < 1e-12
    assert abs(sr0-slope-scores["rental"]) < 1e-12
    method["traffic"] = {"rental_score_intercept": sr0, "rental_score_slope": -slope,
                         "alpha_equal_used": thresholds["used"], "alpha_equal_new": thresholds["new"]}

paths = [SOURCE / "data/parameters.json", book_path, SOURCE / "code/model.py", SOURCE / "code/ahp.py"]
results = {
    "provenance": {"source_repository": str(SOURCE), "revision_date": "2026-11-04",
                   "survey_records": 18, "complete_comparisons": 17,
                   "inputs_sha256": {str(x.relative_to(SOURCE)): sha256(x) for x in paths},
                   "calculation_script_sha256": sha256(Path(__file__))},
    "survey_description": {"sample_n": 18, "profile": description,
                           "pairwise_directions": direction_summary},
    "individual_diagnostics": diagnostics, "methods": methods,
    "annual_burdens": annual, "annual_scoring_anchors": anchors,
    "traffic": {"definition": "Common attributed share of collection/return travel emissions, incremental fares and active travel time",
                "alpha_range": [0, 1], "burden_order": ["kgCO2e/year", "SGD/year", "minutes/year"],
                "rental_burden_intercepts": traffic_intercepts, "rental_burden_slopes": traffic_slopes,
                "retained_rental_handling_minutes": rent["handling_minutes"],
                "used_component_crossovers": [(by_mode["used"][k]-b)/s for k,b,s in zip(burden_keys,traffic_intercepts,traffic_slopes)]},
}
write_text(OUTPUT / "analysis/results.json", json.dumps(results, ensure_ascii=False, indent=2))

# Tables contain only tabular environments; captions and explanatory notes belong to the main manuscript.
lines = [r"\begin{tabularx}{\linewidth}{@{}p{0.31\linewidth}Xrr@{}}", r"\toprule",
         r"Item & Response & $n$ & \%\\", r"\midrule",
         r"\multicolumn{4}{@{}l}{\textit{A. Respondent profile ($N=18$)}}\\"]
previous = None
for row in description:
    q = row["question"] if row["question"] != previous else ""
    lines.append(f"{q} & {row['response']} & {row['count']} & {row['percent']:.1f}" + r"\\")
    previous = row["question"]
lines += [r"\midrule", r"\multicolumn{4}{@{}l}{\textit{B. Pairwise response directions}}\\"]
for item in direction_summary:
    for i, row in enumerate(item["directions"]):
        q = item["question"] if i == 0 else ""
        lines.append(f"{q} & {row['response']} & {row['count']} & {row['percent']:.1f}" + r"\\")
lines += [r"\bottomrule", r"\end{tabularx}"]
write_text(OUTPUT / "tables/survey_description.tex", "\n".join(lines))

lines = [r"\begin{tabularx}{\linewidth}{@{}Xrrrrrr@{}}", r"\toprule",
         r"Method & $n$ & Passed & $w_E$ & $w_C$ & $w_V$ & Group CR\\", r"\midrule"]
for m in methods:
    n = str(m["n"]) if m["n"] is not None else "---"
    passed = str(m["individual_pass_n"]) if m["individual_pass_n"] is not None else "---"
    cr = f"{m['group_cr']:.4f}" if m["group_cr"] is not None else "n.a."
    lines.append(f"{m['label']} & {n} & {passed} & " + " & ".join(f"{w:.3f}" for w in m["weights"]) + f" & {cr}" + r"\\")
lines += [r"\bottomrule", r"\end{tabularx}"]
write_text(OUTPUT / "tables/ahp_comparison.tex", "\n".join(lines))

lines = [r"\begin{tabularx}{\linewidth}{@{}Xrr@{}}", r"\toprule",
         r"Weight specification & Rental = second-hand & Rental = new\\", r"\midrule"]
for m in methods:
    t = m["traffic"]
    lines.append(f"{m['label']} & {100*t['alpha_equal_used']:.2f}\\% & {100*t['alpha_equal_new']:.2f}\\%" + r"\\")
lines += [r"\bottomrule", r"\end{tabularx}"]
write_text(OUTPUT / "tables/traffic_thresholds.tex", "\n".join(lines))

labels = {"new": "New", "used": "Second-hand", "rental": "Rental"}
lines = [r"\begin{tabular}{@{}lrrrrrrr@{}}", r"\toprule",
         r"Option & \co/year & SGD/year & Minutes & $s_E$ & $s_C$ & $s_V$ & $S$ (rank)\\", r"\midrule"]
for row in methods[0]["baseline_scores"]:
    b = by_mode[row["mode"]]
    fields = [labels[row["mode"]], f"{b['annual_kgco2e']:.2f}", f"{b['annual_spending_sgd']:.2f}",
              f"{b['annual_minutes']:.0f}"]
    fields += [f"{row[k]:.4f}" for k in ("emissions_score", "cost_score", "convenience_score")]
    fields += [f"{row['score']:.4f} ({row['rank']})"]
    lines.append(" & ".join(fields) + r"\\")
lines += [r"\bottomrule", r"\end{tabular}"]
write_text(OUTPUT / "tables/ranking.tex", "\n".join(lines))

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8.5, "axes.titlesize": 9,
                     "axes.labelsize": 8.5, "xtick.labelsize": 8, "ytick.labelsize": 8,
                     "pdf.fonttype": 42, "ps.fonttype": 42, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.edgecolor": "#70818a"})
fig, axs = plt.subplots(1, 2, figsize=(6.8, 3.15), gridspec_kw={"width_ratios": [1, 1.12]})
colors = {"used": "#246C77", "new": "#697682", "rental": "#B66A28"}
main = methods[0]
scores = {r["mode"]: r["score"] for r in main["baseline_scores"]}
tr = main["traffic"]
for ax, xmax, title in zip(axs, [1, .15], ["(a) Full attribution range", "(b) Ranking crossover region"]):
    xx = np.linspace(0, xmax, 301)
    ax.plot(xx, np.full_like(xx, scores["used"]), color=colors["used"], lw=1.9, label="Second-hand")
    ax.plot(xx, np.full_like(xx, scores["new"]), color=colors["new"], lw=1.7, ls="--", label="New")
    ax.plot(xx, tr["rental_score_intercept"] + tr["rental_score_slope"]*xx,
            color=colors["rental"], lw=1.9, label="Rental")
    ax.set_xlim(0, xmax)
    ax.set_title(title, loc="left", pad=10)
    ax.xaxis.set_major_formatter(PercentFormatter(1, decimals=0))
    ax.grid(axis="y", color="#dfe5e8", lw=.6, zorder=0)
    ax.set_axisbelow(True)
axs[0].set_ylim(.50, .89)
axs[0].set_yticks([.5, .6, .7, .8, .9])
axs[0].set_xticks([0, .25, .5, .75, 1])
axs[0].set_ylabel("Composite score")
axs[1].set_ylim(.809, .882)
axs[1].set_yticks([.81, .83, .85, .87])
axs[1].set_xticks([0, .05, .10, .15])
for mode, key, texty in [("used", "alpha_equal_used", .872), ("new", "alpha_equal_new", .862)]:
    x = tr[key]
    axs[1].axvline(x, color=colors[mode], ls=":", lw=.9, alpha=.7)
    axs[1].plot([x], [scores[mode]], "o", color=colors[mode], ms=4)
    axs[1].annotate(f"{100*x:.2f}%", xy=(x, scores[mode]), xytext=(x+.004, texty),
                    fontsize=8, color=colors[mode],
                    arrowprops={"arrowstyle": "-", "color": colors[mode], "lw": .7})
handles, labels = axs[0].get_legend_handles_labels()
fig.legend(handles, labels, loc="upper center", ncol=3, frameon=False,
           bbox_to_anchor=(.52, 1.025), handlelength=2.4, columnspacing=2.3)
fig.supxlabel("Attributed share of collection/return travel burden, $\\alpha$", y=.035, fontsize=8.5)
fig.subplots_adjust(left=.09, right=.99, bottom=.22, top=.81, wspace=.25)
figure_dir = OUTPUT / "figures"
figure_dir.mkdir(exist_ok=True)
fig.savefig(figure_dir / "traffic_sensitivity.pdf", bbox_inches="tight", pad_inches=.04)
fig.savefig(figure_dir / "traffic_sensitivity.png", dpi=220, bbox_inches="tight", pad_inches=.04)
plt.close(fig)

fig, ax = plt.subplots(figsize=(6.8, 2.65), layout="constrained")
bottom = np.zeros(3)
for stage, label, color in zip(
    ["manufacturing", "distribution", "disposal", "cleaning", "transport"],
    ["Manufacturing", "Distribution/retail", "Gross disposal", "Cleaning", "Delivery / rail travel"],
    ["#246C77", "#7DA6AC", "#C6D9DB", "#D1AC68", "#AF644D"]):
    vals = np.array([by_mode[m][stage + "_kgco2e"] for m in ("new", "used", "rental")])
    ax.barh([2, 1, 0], vals, left=bottom, color=color, label=label, height=.53,
            edgecolor="white", linewidth=.5)
    bottom += vals
for y, total in zip([2, 1, 0], bottom):
    ax.text(total+.14, y, f"{total:.2f}", va="center", fontsize=9)
ax.set_yticks([2, 1, 0], ["New", "Second-hand", "Rental"])
ax.set_xlim(0, 13.1)
ax.set_xlabel("Annual greenhouse gas emissions (kg CO$_2$e/year)")
ax.set_axisbelow(True)
ax.grid(axis="x", color="#e2e5e6", linewidth=.6)
ax.legend(loc="lower center", bbox_to_anchor=(.45, 1.02), ncol=3, frameon=False, fontsize=8.1)
fig.savefig(figure_dir / "emissions.pdf", bbox_inches="tight")
fig.savefig(figure_dir / "emissions.png", dpi=200, bbox_inches="tight")
plt.close(fig)

print(json.dumps({"survey_n": len(raw), "complete_n": len(main_ind),
                  "methods": [{"key": m["key"], "weights": m["weights"], "group_cr": m["group_cr"],
                               "traffic": m["traffic"]} for m in methods],
                  "outputs": ["analysis/results.json", "tables/survey_description.tex", "tables/ahp_comparison.tex",
                              "tables/traffic_thresholds.tex", "figures/traffic_sensitivity.pdf", "figures/traffic_sensitivity.png"]}, indent=2))

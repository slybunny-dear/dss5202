"""Build report tables and vector figures from the existing model outputs.

Run code/run.py first. This script does not modify the model or input data.
Requires matplotlib in addition to the project's openpyxl dependency.
"""
from pathlib import Path
import csv
import json
import os

os.environ.setdefault("MPLCONFIGDIR", "/private/tmp/dss5202-report-mpl")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
for folder in ("figures", "tables"):
    (HERE / folder).mkdir(exist_ok=True)

def read(name):
    with (ROOT / "results" / name).open(newline="") as f:
        return list(csv.DictReader(f))

annual = {r["mode"]: r for r in read("annual_results.csv")}
groups = [r for r in read("ahp_group.csv") if r["mapping"] == "main_5_3"]
ranks = [r for r in read("rankings.csv") if r["mapping"] == "main_5_3" and r["subset"] == "all_complete"]
labels = {"new": "New", "used": "Second-hand", "rental": "Rental"}

def table(name, spec, header, rows):
    text = "\\begin{tabular}{@{}" + spec + "@{}}\n\\toprule\n"
    text += " & ".join(header) + " \\\\\n\\midrule\n"
    text += "\n".join(" & ".join(map(str, r)) + " \\\\" for r in rows)
    text += "\n\\bottomrule\n\\end{tabular}\n"
    (HERE / "tables" / name).write_text(text)

table("costs.tex", "lrrrrrr", ["Option", "Garment", "Delivery", "Rent", "Care", "Travel", "Total"],
      [[labels[m]] + [f"{float(annual[m][k]):.2f}" for k in
        ("purchase_sgd", "delivery_sgd", "rental_sgd", "care_sgd", "travel_sgd", "annual_spending_sgd")]
       for m in ("new", "used", "rental")])
table("ahp.tex", "lrrrrr", ["Sample", "$n$", "$w_E$", "$w_C$", "$w_V$", "Group CR"],
      [["All complete" if r["subset"] == "all_complete" else "CR-qualified", r["n"]] +
       [f"{float(r[k]):.6f}" for k in ("w_E", "w_C", "w_V", "cr")] for r in groups])
table("ranking.tex", "lrrrrrrr", ["Option", "\\co/year", "SGD/year", "Minutes", "$s_E$", "$s_C$", "$s_V$", "$S$ (rank)"],
      [[labels[r["mode"]], f"{float(annual[r['mode']]['annual_kgco2e']):.4f}",
        f"{float(annual[r['mode']]['annual_spending_sgd']):.2f}",
        f"{float(annual[r['mode']]['annual_minutes']):.0f}"] +
       [f"{float(r[k]):.4f}" for k in ("emissions_score", "cost_score", "convenience_score")] +
       [f"{float(r['score']):.6f} ({r['rank']})"] for r in ranks])
(HERE / "tables/numbers.tex").write_text("% Tables are generated from results CSVs; no final results are hard-coded here.\n")

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "pdf.fonttype": 42,
                     "axes.spines.top": False, "axes.spines.right": False})
colors = ["#246C77", "#7DA6AC", "#C6D9DB", "#D1AC68", "#AF644D"]
stages = ["manufacturing", "distribution", "disposal", "cleaning", "transport"]
stage_labels = ["Manufacturing", "Distribution/retail", "Gross disposal", "Cleaning", "Delivery / rail travel"]
fig, ax = plt.subplots(figsize=(7.0, 2.65), layout="constrained")
bottom = [0., 0., 0.]
for s, label, color in zip(stages, stage_labels, colors):
    vals = [float(annual[m][s + "_kgco2e"]) for m in ("new", "used", "rental")]
    ax.barh([2, 1, 0], vals, left=bottom, color=color, label=label, height=.53,
            edgecolor="white", linewidth=.5)
    bottom = [a+b for a, b in zip(bottom, vals)]
for y, total in zip([2,1,0], bottom):
    ax.text(total+.14, y, f"{total:.4f}", va="center", fontsize=10)
ax.set_yticks([2,1,0], ["New", "Second-hand", "Rental"])
ax.set_xlim(0, 13.1)
ax.set_xlabel("Annual greenhouse gas emissions (kg CO$_2$e/year)")
ax.set_axisbelow(True)
ax.grid(axis="x", color="#e2e5e6", linewidth=.6)
ax.legend(loc="lower center", bbox_to_anchor=(.45, 1.02), ncol=3, frameon=False, fontsize=8.3)
fig.savefig(HERE / "figures/emissions.pdf", bbox_inches="tight")
plt.close(fig)

fig, ax = plt.subplots(figsize=(7.0, 1.35))
ax.set_xlim(0, 10); ax.set_ylim(0, 2); ax.axis("off")
nodes = [(0, "Evidence +\nassumptions"), (2.6, "Annual LCA\n+ LCC + time"),
         (5.2, "AHP weights\n+ fixed scores"), (7.8, "Ranking +\ninterpretation")]
for x, text in nodes:
    ax.add_patch(FancyBboxPatch((x+.04,.5), 2.1,.92, boxstyle="round,pad=0.06,rounding_size=0.04",
                              linewidth=.9, edgecolor="#246C77", facecolor="#EEF4F4"))
    ax.text(x+1.09,.96,text,ha="center",va="center",fontsize=9)
for x in (2.2,4.8,7.4):
    ax.add_patch(FancyArrowPatch((x,.96),(x+.38,.96),arrowstyle="-|>",mutation_scale=11,color="#246C77"))
ax.text(5, .10, "One student | Six events | Same model | Rewearing allowed",ha="center",fontsize=8.6,color="#444444")
fig.savefig(HERE / "figures/framework.pdf", bbox_inches="tight", pad_inches=.03)
plt.close(fig)
summary = {"annual": annual, "main_mapping_groups": groups, "main_ranking": ranks}
(HERE / "build/numerical_audit.json").parent.mkdir(exist_ok=True)
(HERE / "build/numerical_audit.json").write_text(json.dumps(summary, indent=2)+"\n")
print("Generated 3 tables, 2 vector figures, and numerical audit from project CSVs.")

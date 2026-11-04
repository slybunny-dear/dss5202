"""Generate the paper's tables and vector figures from canonical model CSVs.

Run ``python -X utf8 -B code/run.py`` first, then this script.
All analytical values are read from results/. Original inputs remain read-only.
"""
from pathlib import Path
import csv
import json
import os
import tempfile

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "dss5202-matplotlib"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.ticker import PercentFormatter

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
FIGURES = HERE / "figures"
TABLES = HERE / "tables"
for folder in (FIGURES, TABLES):
    folder.mkdir(exist_ok=True)

COLORS = {"used": "#246C77", "new": "#657A8A", "rental": "#B76A2B"}
LABELS = {"new": "New", "used": "Second-hand", "rental": "Rental"}
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 8.3, "axes.titlesize": 9,
    "axes.labelsize": 8.3, "xtick.labelsize": 7.8, "ytick.labelsize": 7.8,
    "pdf.fonttype": 42, "ps.fonttype": 42,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.edgecolor": "#80919A", "axes.linewidth": .7,
    "text.color": "#243746", "axes.labelcolor": "#243746",
    "xtick.color": "#43545D", "ytick.color": "#43545D",
})


def read(name):
    with (ROOT / "results" / name).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_table(name, columns, header, rows):
    text = "\\begin{tabular}{@{}" + columns + "@{}}\n\\toprule\n"
    text += " & ".join(header) + r" \\" + "\n\\midrule\n"
    text += "\n".join(" & ".join(map(str, row)) + r" \\" for row in rows)
    text += "\n\\bottomrule\n\\end{tabular}\n"
    (TABLES / name).write_text(text, encoding="utf-8")


def save(fig, name):
    # Fixed metadata keeps identical figures reproducible across repeated runs.
    fig.savefig(FIGURES / (name + ".pdf"), bbox_inches="tight", pad_inches=.04,
                metadata={"CreationDate": None, "ModDate": None})
    fig.savefig(FIGURES / (name + ".png"), dpi=240, bbox_inches="tight", pad_inches=.04)
    plt.close(fig)


def framework(n):
    fig, ax = plt.subplots(figsize=(6.8, 3.0))
    fig.subplots_adjust(0, 0, 1, 1)
    ax.set(xlim=(0, 100), ylim=(0, 78))
    ax.axis("off")
    ink, teal, grey = "#243746", "#246C77", "#536A77"
    ax.text(50, 74.5, "ONE STUDENT  /  SIX EVENTS PER YEAR  /  THREE OPTIONS",
            ha="center", va="center", fontsize=8.5, fontweight="bold", color=ink)
    ax.plot([2, 98], [70, 70], color="#C7D6DB", lw=.8)

    def box(x, y, w, h, label, lines, accent=teal, fill="#F1F7F7", size=8, body_y=5.4):
        ax.add_patch(FancyBboxPatch((x, y), w, h,
                     boxstyle="round,pad=0.02,rounding_size=1.0",
                     facecolor=fill, edgecolor="#BED0D5", linewidth=.8))
        ax.plot([x+1.1, x+1.1], [y+2, y+h-2], color=accent, lw=2)
        ax.text(x+3, y+h-3.3, label, fontsize=8.3, weight="bold", color=accent, va="center")
        ax.text(x+3, y+body_y, lines, fontsize=size, linespacing=1.45, color=ink, va="center")

    def arrow(start, end, color=grey, connection="arc3,rad=0"):
        ax.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=10,
                     linewidth=1, color=color, connectionstyle=connection,
                     shrinkA=2, shrinkB=2))

    box(2, 49, 27, 16, "PHYSICAL EVIDENCE", "Garment and service data\nPrices, care and transport")
    box(35, 49, 27, 16, "ANNUAL BURDENS", "Carbon emissions (LCA)\nExpenditure (LCC) and time")
    box(2, 28, 27, 16, "ORIGINAL RESPONSES", f"{n} complete response sets\nThree criterion comparisons", accent="#657A8A", fill="#F4F6F8")
    box(35, 28, 27, 16, "AHP PREFERENCES", "1 / 2 / 3 ratio intensities\nGroup criterion weights", accent="#657A8A", fill="#F4F6F8")
    arrow((29, 57), (35, 57))
    arrow((29, 36), (35, 36))
    box(69, 36, 29, 25, "COMPOSITE EVALUATION",
        "Normalize criterion burdens\nApply AHP weights\nRank the three options", fill="#EAF2F4", size=8, body_y=10)
    arrow((62, 57), (69, 53))
    arrow((62, 36), (69, 43))

    ax.add_patch(FancyBboxPatch((2, 3), 96, 19, boxstyle="round,pad=0.02,rounding_size=1.0",
                               facecolor="#FCF7EF", edgecolor="#D9C6AD", linewidth=.8))
    ax.text(5, 17.5, "TRANSPORT SENSITIVITY", fontsize=8.3, weight="bold", color=COLORS["rental"])
    ax.text(5, 10.3, "Vary rental travel attribution, $\\alpha$\nEmissions, fares and travel time",
            fontsize=8, linespacing=1.45, va="center")
    arrow((47, 10.5), (54, 10.5), COLORS["rental"])
    ax.text(57, 10.3, "Recalculate scores with fixed AHP weights\nIdentify ranking changes and crossover shares",
            fontsize=8, linespacing=1.45, va="center")
    arrow((83.5, 36), (83.5, 22), COLORS["rental"])
    save(fig, "framework")


def emissions(annual):
    fig, ax = plt.subplots(figsize=(6.8, 2.35))
    fig.subplots_adjust(left=.14, right=.985, bottom=.22, top=.70)
    modes = ("new", "used", "rental")
    bottoms = [0., 0., 0.]
    for stage, label, color in zip(
        ("manufacturing", "distribution", "disposal", "cleaning", "transport"),
        ("Manufacturing", "Distribution / retail", "Gross disposal", "Cleaning", "Acquisition transport"),
        ("#246C77", "#81A8AD", "#C6DADC", "#D7B374", "#B76A2B"),
    ):
        vals = [float(annual[m][stage + "_kgco2e"]) for m in modes]
        ax.barh([2, 1, 0], vals, left=bottoms, color=color, label=label,
                height=.56, edgecolor="white", linewidth=.55)
        bottoms = [a+b for a,b in zip(bottoms, vals)]
    for y, total in zip([2, 1, 0], bottoms):
        ax.text(total+.13, y, f"{total:.2f}", va="center", fontsize=8.5, weight="bold")
    ax.set_yticks([2, 1, 0], [LABELS[m] for m in modes])
    ax.tick_params(axis="y", length=0, pad=7)
    ax.set_xlim(0, 12.6)
    ax.set_xlabel("Annual greenhouse gas emissions (kg CO$_2$e)", labelpad=7)
    ax.set_axisbelow(True)
    ax.grid(axis="x", color="#E3EAED", linewidth=.6)
    ax.spines["left"].set_visible(False)
    handles, labels = ax.get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(.55, 1.0),
               ncol=3, frameon=False, fontsize=7.9, handlelength=1.5,
               columnspacing=1.8, labelspacing=.7)
    save(fig, "emissions")


def traffic(scenarios, thresholds):
    fig, axs = plt.subplots(1, 2, figsize=(6.8, 2.75), gridspec_kw={"width_ratios": [1, 1.12]})
    fig.subplots_adjust(left=.09, right=.99, bottom=.24, top=.79, wspace=.24)
    by_mode = {m: sorted((r for r in scenarios if r["mode"] == m), key=lambda r: float(r["alpha"]))
               for m in ("used", "new", "rental")}
    for ax, xmax, title in zip(axs, (1., .15), ("(a) Full attribution range", "(b) Ranking crossover region")):
        for mode, style in (("used", "-"), ("new", "--"), ("rental", "-")):
            rows=by_mode[mode]
            ax.plot([float(r["alpha"]) for r in rows], [float(r["score"]) for r in rows],
                    color=COLORS[mode], lw=1.7, ls=style, label=LABELS[mode])
        ax.set_xlim(0, xmax)
        ax.set_title(title, loc="left", pad=9)
        ax.xaxis.set_major_formatter(PercentFormatter(1, decimals=0))
        ax.set_axisbelow(True)
        ax.grid(axis="y", color="#DFE7EA", lw=.6)
    axs[0].set_ylim(.50, .90)
    axs[0].set_xticks([0, .25, .50, .75, 1.])
    axs[0].set_yticks([.5, .6, .7, .8, .9])
    axs[0].set_ylabel("Composite score")
    axs[1].set_ylim(.81, .88)
    axs[1].set_xticks([0, .05, .10, .15])
    axs[1].set_yticks([.81, .83, .85, .87])
    for mode, key, texty in (("used", "rental_vs_used", .871), ("new", "rental_vs_new", .861)):
        x = thresholds[key]
        score = float(by_mode[mode][0]["score"])
        axs[1].axvline(x, color=COLORS[mode], ls=":", lw=.85, alpha=.7)
        axs[1].plot(x, score, "o", color=COLORS[mode], ms=3.8)
        axs[1].annotate(f"{100*x:.2f}%", xy=(x, score), xytext=(x+.003, texty),
                        color=COLORS[mode], fontsize=8,
                        arrowprops={"arrowstyle": "-", "color": COLORS[mode], "lw": .75})
    handles, labels=axs[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(.53, 1.025),
               ncol=3, frameon=False, columnspacing=2.0, handlelength=2.3)
    fig.supxlabel("Attributed share of collection-and-return travel burden, $\\alpha$", y=.045, fontsize=8.3)
    save(fig, "traffic_sensitivity")


def main():
    annual={r["mode"]:r for r in read("annual_results.csv")}
    groups=read("ahp_group.csv")
    ranks=read("rankings.csv")
    assert len(groups)==1 and groups[0]["mapping"]=="mild_3_2" and groups[0]["subset"]=="all_complete"
    assert len(ranks)==3 and {r["mapping"] for r in ranks}=={"mild_3_2"}
    ranks.sort(key=lambda r:int(r["rank"]))
    write_table("costs.tex", "lrrrrrr", ["Option", "Garment", "Delivery", "Rent", "Care", "Travel", "Total"],
        [[LABELS[m]]+[f"{float(annual[m][k]):.2f}" for k in
         ("purchase_sgd","delivery_sgd","rental_sgd","care_sgd","travel_sgd","annual_spending_sgd")]
         for m in ("new","used","rental")])
    write_table("ranking.tex", "lrrrrrrr", ["Option", "\\co/year", "SGD/year", "Minutes", "$s_E$", "$s_C$", "$s_V$", "$S$ (rank)"],
        [[LABELS[r["mode"]],f"{float(annual[r['mode']]['annual_kgco2e']):.2f}",
          f"{float(annual[r['mode']]['annual_spending_sgd']):.2f}",f"{float(annual[r['mode']]['annual_minutes']):.0f}"]+
         [f"{float(r[k]):.4f}" for k in ("emissions_score","cost_score","convenience_score")]+
         [f"{float(r['score']):.4f} ({r['rank']})"] for r in ranks])
    scenarios=read("transport_scenarios.csv")
    thresholds={r["comparison"]:float(r["alpha"]) for r in read("transport_thresholds.csv")}
    framework(int(groups[0]["n"]))
    emissions(annual)
    traffic(scenarios,thresholds)
    print(json.dumps({"tables":2,"figures":3,"mapping":groups[0]["mapping"],
                      "group_n":int(groups[0]["n"]),"thresholds":thresholds},indent=2))


if __name__=="__main__":
    main()

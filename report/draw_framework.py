"""Draw the study's technical route as vector PDF/SVG and a 300 dpi PNG.

The layout separates scope, parallel measurement and preference elicitation,
decision integration, and the transport scenario. It is an original diagram;
literature-informed layout choices are documented beside the manuscript.
"""
from pathlib import Path
import argparse
import csv
import os
import tempfile

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "dss5202-matplotlib"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch


HERE = Path(__file__).resolve().parent
INK = "#263438"
TEAL = "#285D65"
LINE = "#75868B"
LIGHT = "#D2DBDD"


def draw_framework(n, output_dir=None):
    """Draw the analytical route; n is the original complete-response count."""
    if not isinstance(n, int) or n <= 0:
        raise ValueError("The complete-response count must be a positive integer")
    output_dir = Path(output_dir) if output_dir else HERE / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)
    style = {
        "font.family": "DejaVu Sans", "font.size": 8.6,
        "mathtext.fontset": "dejavusans", "text.color": INK,
        "pdf.fonttype": 42, "ps.fonttype": 42,
        "svg.fonttype": "none", "svg.hashsalt": "dss5202-framework-v2",
    }
    with plt.rc_context(style):
        fig, ax = plt.subplots(figsize=(6.8, 3.8))
        fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
        ax.set(xlim=(0, 6.8), ylim=(0, 3.8))
        ax.axis("off")

        def text(x, y, value, size=8.6, bold=False, color=INK, ha="center"):
            return ax.text(x, y, value, fontsize=size, fontweight="bold" if bold else "normal",
                           color=color, ha=ha, va="center", linespacing=1.30)

        def line(xs, ys, color=LINE, width=.7):
            ax.plot(xs, ys, color=color, lw=width, solid_capstyle="butt", zorder=1)

        def box(x, y, w, h, color=LINE, fill="white", width=.7):
            ax.add_patch(Rectangle((x, y), w, h, facecolor=fill, edgecolor=color, lw=width, zorder=0))

        def arrow(x1, y1, x2, y2, color=LINE, width=.75):
            ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                         mutation_scale=7.5, lw=width, color=color, shrinkA=0, shrinkB=0,
                         zorder=2))

        def phase(number, label, y):
            text(.09, y+.11, number, size=10.6, bold=True, color=TEAL, ha="left")
            text(.09, y-.11, label, size=8.0, bold=True, ha="left")

        # Four phase labels provide a reading order without competing boxes.
        phase("01", "Study scope", 3.43)
        phase("02", "Parallel\nassessment", 2.32)
        phase("03", "Decision\nintegration", 1.13)
        phase("04", "Transport\nsensitivity", .33)
        line([.88, .88], [.05, 3.72], color=LIGHT, width=.7)

        # 1. A shared functional unit precedes the three fixed alternatives.
        text(3.89, 3.63, "One NUS student  ·  Six formal events  ·  One year", size=9.0, bold=True)
        for x, label in [(1.06, "New purchase"), (3.02, "Second-hand purchase"), (4.98, "Rental")]:
            box(x, 3.15, 1.75, .29, color=LINE)
            text(x+.875, 3.295, label, size=8.8)
        # All three alternatives share the same measurement and preference route.
        for x in [1.935, 3.895, 5.855]:
            line([x, x], [3.15, 3.055])
        line([1.935, 5.855], [3.055, 3.055])
        arrow(2.79, 3.055, 2.79, 2.94)
        arrow(5.80, 3.055, 5.80, 2.94)

        # 2a. Quantification: common inputs feed three comparable annual burdens.
        box(1.06, 1.61, 3.45, 1.33)
        text(2.785, 2.80, "Annual performance assessment", size=9.1, bold=True, color=TEAL)
        text(2.785, 2.60, "Garment, price, care and travel inputs", size=8.45)
        line([1.20, 4.37], [2.47, 2.47], color=LIGHT)
        centres = [1.635, 2.785, 3.935]
        for x in centres:
            arrow(x, 2.47, x, 2.35)
        for x in [2.21, 3.36]:
            line([x, x], [1.75, 2.32], color=LIGHT)
        for x, title, output, unit in [
            (centres[0], "LCA", r"Emissions, $E_m$", r"kg CO$_2$e / year"),
            (centres[1], "LCC", r"Expenditure, $C_m$", "SGD / year"),
            (centres[2], "Active time", r"Convenience, $T_m$", "min / year"),
        ]:
            text(x, 2.23, title, size=9.0, bold=True)
            text(x, 2.02, output, size=8.3)
            text(x, 1.82, unit, size=8.15)

        # 2b. Preference elicitation retains every complete original response.
        box(4.86, 1.61, 1.87, 1.33)
        text(5.795, 2.80, "Preference elicitation", size=9.0, bold=True, color=TEAL)
        text(5.795, 2.60, f"Complete responses (n = {n})", size=8.4)
        arrow(5.795, 2.47, 5.795, 2.36)
        text(5.795, 2.23, "AHP pairwise comparisons", size=8.5)
        text(5.795, 2.04, "Geometric aggregation · CR", size=8.2)
        arrow(5.795, 1.93, 5.795, 1.85)
        text(5.795, 1.73, r"Criterion weights: $w_E,\ w_C,\ w_V$", size=8.25)

        # 3. Annual burdens and criterion weights enter different calculation steps.
        arrow(2.785, 1.61, 2.785, 1.43)
        line([5.795, 5.795, 4.60], [1.61, 1.53, 1.53])
        arrow(4.60, 1.53, 4.60, 1.43)
        box(1.06, .89, 2.27, .54)
        text(2.195, 1.28, "Linear normalization", size=8.8, bold=True)
        text(2.195, 1.06, r"$s_{mj}=1-B_{mj}/U_j$", size=10)
        arrow(3.33, 1.16, 3.63, 1.16)
        box(3.63, .89, 1.92, .54)
        text(4.59, 1.28, "AHP-weighted score", size=8.8, bold=True)
        text(4.59, 1.075, r"$S_m=\sum_j w_j\,s_{mj}$", size=9.4)
        arrow(5.55, 1.16, 5.84, 1.16)
        text(6.29, 1.16, "Baseline\nranking", size=9.0, bold=True, color=TEAL)

        # 4. The scenario changes rental burdens and reuses the same decision rule.
        arrow(5.30, .89, 5.30, .71)
        box(1.06, .04, 5.67, .67, color=TEAL, width=.8)
        text(1.85, .46, "Travel attribution", size=8.7, bold=True)
        text(1.85, .23, r"$0\leq\alpha\leq1$", size=10)
        arrow(2.59, .38, 2.88, .38, color=TEAL)
        text(3.75, .46, "Rental burdens", size=8.7, bold=True)
        text(3.75, .23, r"$E_R(\alpha),\ C_R(\alpha),\ T_R(\alpha)$", size=9.2)
        arrow(4.65, .38, 4.93, .38, color=TEAL)
        text(5.80, .47, "Rescore and compare", size=8.7, bold=True)
        text(5.80, .26, "Ranking crossovers", size=8.5)
        # A white-backed note makes the fixed preference settings explicit.
        ax.text(3.895, .713, " Fixed weights and scoring references ", ha="center", va="center",
                fontsize=8.1, color=TEAL, bbox={"facecolor":"white", "edgecolor":"none", "pad":.2}, zorder=4)

        fig.savefig(output_dir / "framework.pdf", metadata={"CreationDate":None, "ModDate":None})
        fig.savefig(output_dir / "framework.svg", metadata={"Date":None})
        fig.savefig(output_dir / "framework.png", dpi=300)
        plt.close(fig)
    return {kind: str(output_dir / f"framework.{kind}") for kind in ("pdf", "svg", "png")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=HERE / "figures")
    parser.add_argument("--n", type=int, help="Complete original questionnaire responses")
    args = parser.parse_args()
    n = args.n
    if n is None:
        with (HERE.parent / "results/ahp_group.csv").open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        if len(rows) != 1:
            raise ValueError("Expected the single group AHP result")
        n = int(rows[0]["n"])
    for path in draw_framework(n, args.output_dir).values():
        print(path)


if __name__ == "__main__":
    main()

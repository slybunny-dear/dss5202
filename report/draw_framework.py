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
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, Ellipse, Polygon, Arc


HERE = Path(__file__).resolve().parent
INK = "#202833"
LINE = "#515A66"
BLUE = "#315B9E"
GREEN = "#247855"
PURPLE = "#7150AA"
CORAL = "#B65C3D"


def draw_framework(n, output_dir=None):
    """Draw a colourful, grouped vector schematic of the unchanged study route."""
    if not isinstance(n, int) or n <= 0:
        raise ValueError("The complete-response count must be a positive integer")
    output_dir = Path(output_dir) if output_dir else HERE / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)
    style = {
        "font.family": "DejaVu Sans", "font.size": 8.6,
        "mathtext.fontset": "dejavusans", "text.color": INK,
        "pdf.fonttype": 42, "ps.fonttype": 42,
        "svg.fonttype": "none", "svg.hashsalt": "dss5202-framework-colour-v3",
    }
    with plt.rc_context(style):
        fig, ax = plt.subplots(figsize=(6.8, 3.8))
        fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
        ax.set(xlim=(0, 6.8), ylim=(0, 3.8))
        ax.axis("off")

        def text(x, y, value, size=8.6, bold=False, color=INK, ha="center"):
            return ax.text(x, y, value, fontsize=size, fontweight="bold" if bold else "normal",
                           color=color, ha=ha, va="center", linespacing=1.24, zorder=5)

        def line(xs, ys, color=LINE, width=.9, zorder=2):
            ax.plot(xs, ys, color=color, lw=width, solid_capstyle="round", zorder=zorder)

        def box(x, y, w, h, fill="white", color=INK, width=.8, radius=.045, dashed=False):
            patch = FancyBboxPatch((x, y), w, h,
                boxstyle=f"round,pad=0,rounding_size={radius}",
                facecolor=fill, edgecolor=color, lw=width,
                linestyle=(0, (3.4, 2.4)) if dashed else "solid", zorder=1)
            ax.add_patch(patch)
            return patch

        def arrow(x1, y1, x2, y2, color=INK, width=.95):
            ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                         mutation_scale=8.0, lw=width, color=color, shrinkA=0, shrinkB=0,
                         zorder=3))

        def phase(number, label, y, fill):
            ax.add_patch(Circle((.20, y+.10), .115, facecolor=fill, edgecolor=INK, lw=.9, zorder=2))
            text(.20, y+.10, number, size=9.4, bold=True)
            text(.07, y-.16, label, size=8.15, bold=True, ha="left")

        def icon(kind, x, y, s, color=INK):
            """Small editable vector symbols; text labels carry all meaning."""
            if kind == "dress":
                points = [(-.26,.44),(-.12,.48),(0,.28),(.12,.48),(.26,.44),
                          (.20,.05),(.43,-.46),(-.43,-.46),(-.20,.05)]
                ax.add_patch(Polygon([(x+s*a,y+s*b) for a,b in points], closed=True,
                    facecolor="white", edgecolor=color, lw=.85, joinstyle="round", zorder=4))
                line([x-.19*s,x+.19*s], [y+.04*s,y+.04*s], color, .7, zorder=5)
            elif kind == "reuse":
                ax.add_patch(Arc((x,y), .88*s, .88*s, theta1=30, theta2=180,
                    color=color, lw=1, zorder=4))
                ax.add_patch(Arc((x,y), .88*s, .88*s, theta1=210, theta2=360,
                    color=color, lw=1, zorder=4))
                ax.add_patch(Polygon([(x-.44*s,y),(x-.62*s,y+.15*s),(x-.23*s,y+.13*s)],
                    color=color, zorder=4))
                ax.add_patch(Polygon([(x+.44*s,y),(x+.62*s,y-.15*s),(x+.23*s,y-.13*s)],
                    color=color, zorder=4))
            elif kind == "hanger":
                ax.add_patch(Arc((x,y+.28*s), .30*s, .32*s, theta1=0, theta2=230,
                    color=color, lw=.9, zorder=4))
                line([x+.15*s,x+.15*s,x-.50*s,x+.50*s,x+.15*s],
                     [y+.28*s,y+.02*s,y-.38*s,y-.38*s,y+.02*s], color, .9, zorder=5)
            elif kind == "leaf":
                ax.add_patch(Ellipse((x,y), .59*s, .96*s, angle=-35,
                    facecolor="white", edgecolor=color, lw=.85, zorder=4))
                line([x-.24*s,x+.22*s], [y-.42*s,y+.35*s], color, .75, zorder=5)
            elif kind == "coin":
                ax.add_patch(Circle((x,y), .47*s, facecolor="white", edgecolor=color, lw=.9, zorder=4))
                text(x,y,"$",size=7.5,bold=True,color=color)
            elif kind == "clock":
                ax.add_patch(Circle((x,y), .47*s, facecolor="white", edgecolor=color, lw=.9, zorder=4))
                line([x,x,x+.27*s], [y+.29*s,y,y-.12*s], color, .9, zorder=5)
            elif kind == "survey":
                box(x-.36*s,y-.47*s,.72*s,.94*s,fill="white",color=color,width=.8,radius=.015)
                box(x-.16*s,y+.36*s,.32*s,.17*s,fill="white",color=color,width=.7,radius=.01)
                for dy in [.17,-.07,-.30]:
                    line([x-.19*s,x+.20*s],[y+dy*s,y+dy*s],color,.65,zorder=5)

        # Colour reinforces named stages; icons and colour are never the sole key.
        phase("1", "Study scope", 3.43, "#CDE8FF")
        phase("2", "Parallel\nassessment", 2.32, "#D2F0DC")
        phase("3", "Decision\nintegration", 1.13, "#E1D5FA")
        phase("4", "Transport\nsensitivity", .33, "#FFD5C4")
        ax.plot([.88,.88],[.05,3.72],color="#CCD2D9",lw=.65,ls=(0,(2,3)),zorder=0)

        # 1. A shared functional unit precedes the three fixed alternatives.
        text(3.89, 3.63, "One NUS student  ·  Six formal events  ·  One year", size=9.3, bold=True)
        for x, label, symbol, fill, accent in [
            (1.06,"New purchase","dress","#D7ECFF",BLUE),
            (2.98,"Second-hand purchase","reuse","#D8F2E2",GREEN),
            (4.90,"Rental","hanger","#F8DDEB","#9B3D70"),
        ]:
            box(x,3.15,1.83,.29,fill=fill,color=INK)
            icon(symbol,x+.16,3.295,.19,accent)
            text(x+(1.04 if symbol=="reuse" else .98),3.295,label,
                 size=8.0 if symbol=="reuse" else 8.4,bold=True)
        # All three alternatives share the same measurement and preference route.
        for x in [1.975, 3.895, 5.815]:
            line([x, x], [3.15, 3.055])
        line([1.975, 5.815], [3.055, 3.055])
        arrow(2.79, 3.055, 2.79, 2.94)
        arrow(5.75, 3.055, 5.75, 2.94)

        # 2a. Quantification: common inputs feed three comparable annual burdens.
        box(1.06,1.61,3.45,1.33,fill="#F5F7FA",color="#8B939E",width=.95,dashed=True)
        text(2.785, 2.80, "Annual performance assessment", size=9.1, bold=True)
        text(2.785, 2.60, "Garment, price, care and travel inputs", size=8.35)
        line([1.20, 4.37], [2.47, 2.47], color="#A8B1BD",width=.65)
        centres = [1.635, 2.785, 3.935]
        for x in centres:
            arrow(x, 2.47, x, 2.35)
        for x, title, output, unit, symbol, fill, accent in [
            (centres[0], "LCA", r"Emissions, $E_m$", r"kg CO$_2$e / year","leaf","#CEF1D9",GREEN),
            (centres[1], "LCC", r"Expenditure, $C_m$", "SGD / year","coin","#D7E8FF",BLUE),
            (centres[2], "Active time", r"Convenience, $T_m$", "min / year","clock","#FFE6A6","#885B15"),
        ]:
            box(x-.52,1.70,1.04,.64,fill=fill,color=accent,width=.8,radius=.035)
            icon(symbol,x-.34,2.205,.14,accent)
            text(x+(.13 if symbol=="clock" else .075), 2.205, title,
                 size=8.1 if symbol=="clock" else 8.4, bold=True, color=accent)
            text(x, 2.00, output, size=8.15)
            text(x, 1.81, unit, size=8.1)

        # 2b. Preference elicitation retains every complete original response.
        box(4.77,1.61,1.96,1.33,fill="#F0E8FC",color="#967EB7",width=.95,dashed=True)
        icon("survey",4.93,2.80,.16,PURPLE)
        text(5.84, 2.80, "Preference elicitation", size=8.8, bold=True, color=PURPLE)
        text(5.75, 2.60, f"Complete responses (n = {n})", size=8.4)
        arrow(5.75, 2.47, 5.75, 2.36)
        text(5.75, 2.23, "AHP pairwise comparisons", size=8.3)
        text(5.75, 2.04, "Geometric aggregation · CR", size=8.1)
        arrow(5.75, 1.93, 5.75, 1.85)
        box(4.87,1.645,1.76,.17,fill="#DED0F2",color="#DED0F2",width=.5,radius=.025)
        text(5.75, 1.73, r"Criterion weights: $w_E,\ w_C,\ w_V$", size=8.2,color=PURPLE)

        # 3. Annual burdens and criterion weights enter different calculation steps.
        line([2.785,2.785,2.195],[1.61,1.51,1.51],color=INK)
        arrow(2.195,1.51,2.195,1.43)
        line([5.75, 5.75, 4.60], [1.61, 1.53, 1.53],color=INK)
        arrow(4.60, 1.53, 4.60, 1.43)
        box(1.06,.89,2.27,.54,fill="#DCE9FC",color=INK)
        text(2.195, 1.28, "Linear normalization", size=8.8, bold=True,color=BLUE)
        text(2.195, 1.06, r"$s_{mj}=1-B_{mj}/U_j$", size=10)
        arrow(3.33, 1.16, 3.63, 1.16)
        box(3.63,.89,1.92,.54,fill="#DFD7F6",color=INK)
        text(4.59, 1.28, "AHP-weighted score", size=8.8, bold=True,color=PURPLE)
        text(4.59, 1.075, r"$S_m=\sum_j w_j\,s_{mj}$", size=9.4)
        arrow(5.55, 1.16, 5.90, 1.16)
        box(5.90,.89,.83,.54,fill="#FFF0B7",color=INK)
        text(6.315, 1.16, "Baseline\nranking", size=8.7, bold=True)

        # 4. The scenario changes rental burdens and reuses the same decision rule.
        arrow(5.30, .89, 5.30, .71)
        box(1.06,.04,5.67,.67,fill="#FFF7EF",color="#B98972",width=.95,dashed=True)
        box(1.16,.12,1.52,.48,fill="#FFE6B1",color="#A98442",width=.65,radius=.035)
        box(3.04,.12,1.68,.48,fill="#FFD7C7",color="#B77860",width=.65,radius=.035)
        box(5.08,.12,1.55,.48,fill="#F7DDEB",color="#B07D98",width=.65,radius=.035)
        text(1.92, .46, "Travel attribution", size=8.5, bold=True)
        text(1.92, .23, r"$0\leq\alpha\leq1$", size=10)
        arrow(2.68, .36, 3.04, .36)
        text(3.88, .46, "Rental burdens", size=8.5, bold=True)
        text(3.88, .23, r"$E_R(\alpha),\ C_R(\alpha),\ T_R(\alpha)$", size=9.0)
        arrow(4.72, .36, 5.08, .36)
        text(5.855, .46, "Rescore and compare", size=8.3, bold=True)
        text(5.855, .23, "Ranking crossovers", size=8.3)
        # A white-backed note makes the fixed preference settings explicit.
        ax.text(3.895, .713, " Fixed weights and scoring references ", ha="center", va="center",
                fontsize=8.1, color=CORAL, bbox={"facecolor":"white", "edgecolor":"none", "pad":.2}, zorder=5)

        fig.savefig(output_dir / "framework.pdf", metadata={"CreationDate":None, "ModDate":None})
        fig.savefig(output_dir / "framework.svg", metadata={"Date":None})
        svg_path = output_dir / "framework.svg"
        svg_path.write_text("\n".join(row.rstrip() for row in
            svg_path.read_text(encoding="utf-8").splitlines()) + "\n", encoding="utf-8")
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

"""Render a lecture-style product system with qualitative boundary exchanges.

Resource and emission arrows explain the system boundary; the calculations use
aggregated literature carbon factors rather than measured elementary flows.
"""
from pathlib import Path
import argparse
import json
import os
import tempfile

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "dss5202-matplotlib"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch, FancyArrowPatch

HERE = Path(__file__).resolve().parent
INK = "#263438"
BLUE = "#315D98"
ENVIRONMENT = "#DFEDF7"
SYSTEM = "#E5F0DA"
PROCESS = "#FFF4D8"
FLOW = "#637984"


def draw_lca_boundary(config=None, output_dir=None):
    """Export an editable diagram, reading the study parameters by default."""
    if config is None:
        config = json.loads((HERE.parent / "data/parameters.json").read_text(encoding="utf-8"))
    events = config["parameters"]["events"]["value"]
    output_dir = Path(output_dir) if output_dir else HERE / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)
    style = {"font.family": "DejaVu Sans", "font.size": 8.5,
             "mathtext.fontset": "dejavusans", "text.color": INK,
             "pdf.fonttype": 42, "ps.fonttype": 42,
             "svg.fonttype": "none", "svg.hashsalt": "dss5202-lca-boundary-lecture-v2"}
    with plt.rc_context(style):
        fig, ax = plt.subplots(figsize=(6.8, 4.2))
        fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
        ax.set(xlim=(0, 6.8), ylim=(0, 4.2))
        ax.axis("off")

        def text(x, y, value, size=8.5, bold=False, color=INK, ha="center"):
            return ax.text(x, y, value, fontsize=size,
                           fontweight="bold" if bold else "normal", color=color,
                           ha=ha, va="center", linespacing=1.23, zorder=5)

        def line(xs, ys, resource=False):
            ax.plot(xs, ys, color=FLOW if resource else INK,
                    lw=.65 if resource else .95, solid_capstyle="butt", zorder=2)

        def arrow(x1, y1, x2, y2, resource=False):
            ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                         mutation_scale=7.0 if resource else 8.0,
                         lw=.65 if resource else .95,
                         color=FLOW if resource else INK, shrinkA=0, shrinkB=0, zorder=3))

        def process(x, y, w, h, label, size=8.5):
            ax.add_patch(Rectangle((x, y), w, h, facecolor=PROCESS,
                         edgecolor=BLUE, lw=.75, zorder=1))
            text(x+w/2, y+h/2, label, size=size)

        # Course lecture p.55: environment, boundary, processes, and exchanges.
        text(3.4, 4.075,
             f"Functional unit: {events:g} formalwear uses for one NUS student over one year",
             size=9.0, bold=True)
        ax.add_patch(Rectangle((.06, .36), 6.68, 3.58,
                     facecolor=ENVIRONMENT, edgecolor="none", zorder=-3))
        text(.25, 3.78, "Environment", size=9.0, bold=True, ha="left")
        ax.add_patch(FancyBboxPatch((.18, 1.39), 6.44, 2.13,
                     boxstyle="round,pad=0,rounding_size=.18", facecolor=SYSTEM,
                     edgecolor=BLUE, lw=1.1, linestyle=(0, (4, 2)), zorder=-2))
        boundary_label = text(.43, 3.52, " System boundary ", size=8.7,
                              bold=True, ha="left", color=BLUE)
        boundary_label.set_bbox({"facecolor": ENVIRONMENT, "edgecolor": "none", "pad": .25})

        # The garment chain ends at the lifetime end, independently of the FU year.
        process(.42, 2.38, 1.14, .46, "Manufacturing", size=8.4)
        process(1.91, 2.38, 1.34, .46, "Distribution /\nretail", size=8.5)
        process(3.63, 2.38, .95, .46, "Use", size=9.1)
        process(4.99, 2.38, 1.41, .46,
                "End-of-life treatment\nCollection / incineration", size=8.0)
        for start, stop in [(1.56, 1.91), (3.25, 3.63), (4.58, 4.99)]:
            arrow(start, 2.61, stop, 2.61)
        process(3.63, 1.72, .95, .40, "Cleaning", size=8.6)
        arrow(3.88, 2.38, 3.88, 2.12)
        arrow(4.32, 2.12, 4.32, 2.38)

        # An acquisition-support service enters the garment chain.
        process(1.79, 2.98, 1.76, .45,
                "Transport support\nDelivery (purchases)\nCollection / return (rental)", size=8.0)
        line([3.45, 3.45], [2.98, 2.74])
        arrow(3.45, 2.74, 3.45, 2.61)

        # Materials, energy carriers, and supplied water remain technosphere flows.
        process(.42, 1.63, 2.30, .52,
                "Background supply\nMaterials, energy and water\nEmbedded in stage factors", size=8.2)
        arrow(.99, 2.15, .99, 2.38, resource=True)
        arrow(2.72, 1.92, 3.63, 1.92, resource=True)
        line([.42, .29, .29, 1.59], [1.93, 1.93, 3.205, 3.205], resource=True)
        arrow(1.59, 3.205, 1.79, 3.205, resource=True)

        # Functional service crosses the boundary separately from emissions.
        arrow(4.105, 2.84, 4.105, 3.64)
        text(4.105, 3.785, "Functional output:\nformalwear service", size=8.6, bold=True)

        # Primary resources enter background supply across the lower boundary.
        text(.40, 1.17, "Input flows", size=8.7, bold=True, ha="left")
        text(.40, .91, "Primary resources\n(including energy resources)", size=8.1, ha="left")
        text(.40, .60, "Water", size=8.4, ha="left")
        line([2.40, 2.40], [.60, 1.43], resource=True)
        arrow(2.40, 1.43, 2.40, 1.63, resource=True)
        arrow(2.08, .91, 2.40, .91, resource=True)
        arrow(1.04, .60, 2.40, .60, resource=True)

        # Emissions leave the whole system, following the lecture's aggregate outlet.
        line([4.10, 4.10], [1.39, .84], resource=True)
        arrow(4.10, .84, 4.48, .84, resource=True)
        text(4.58, 1.17, "Output flows (all stages)", size=8.7, bold=True, ha="left")
        text(5.55, .84, "GHG emissions to air\n(e.g., CO$_2$, CH$_4$, N$_2$O)", size=8.5)

        # Impact units describe a calculated indicator rather than a physical flow.
        arrow(.30, .22, .59, .22)
        text(.66, .22, "Garment / service flow", size=7.8, ha="left")
        arrow(3.43, .22, 3.72, .22, resource=True)
        text(3.79, .22, "Background supply / environmental flow", size=7.8, ha="left")
        text(3.40, .075, r"Impact indicator: kg CO$_2$e per functional unit", size=8.5, bold=True)

        fig.savefig(output_dir / "lca_boundary.pdf", metadata={"CreationDate": None, "ModDate": None})
        fig.savefig(output_dir / "lca_boundary.svg", metadata={"Date": None})
        svg_path = output_dir / "lca_boundary.svg"
        svg_path.write_text("\n".join(row.rstrip() for row in
                            svg_path.read_text(encoding="utf-8").splitlines()) + "\n",
                            encoding="utf-8")
        fig.savefig(output_dir / "lca_boundary.png", dpi=300)
        plt.close(fig)
    return {kind: str(output_dir / f"lca_boundary.{kind}") for kind in ("pdf", "svg", "png")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=HERE / "figures")
    args = parser.parse_args()
    for path in draw_lca_boundary(output_dir=args.output_dir).values():
        print(path)


if __name__ == "__main__":
    main()

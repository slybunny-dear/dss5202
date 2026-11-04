"""Render the modelled formalwear product system and annual activity detail.

Solid arrows trace garments. Dotted links expand whole-life use into annual
scenarios; they represent accounting detail rather than additional product flow.
All numeric activity labels are derived from the existing model configuration.
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
from matplotlib.patches import Rectangle, FancyArrowPatch


HERE = Path(__file__).resolve().parent
INK = "#263438"
TEAL = "#285D65"
LINE = "#75868B"
LIGHT = "#B8C5C8"


def draw_lca_boundary(config=None, output_dir=None):
    """Export the LCA diagram using parameters.json unless config is supplied."""
    if config is None:
        config = json.loads((HERE.parent / "data/parameters.json").read_text(encoding="utf-8"))
    p = {key: item["value"] for key, item in config["parameters"].items()}
    n, lifetime = p["events"], p["lifetime_wears"]
    clean_count = n * p["cleans_per_wear"]
    delivery_route = p["delivery_one_way_km"] * p["delivery_legs"]
    delivery = delivery_route / p["delivery_batch"]
    rental_distance = n * p["rental_legs"] * p["one_way_km"]
    fmt = lambda value: f"{value:g}"
    output_dir = Path(output_dir) if output_dir else HERE / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)
    style = {
        "font.family": "DejaVu Sans", "font.size": 8.4,
        "mathtext.fontset": "dejavusans", "text.color": INK,
        "pdf.fonttype": 42, "ps.fonttype": 42,
        "svg.fonttype": "none", "svg.hashsalt": "dss5202-lca-boundary-v1",
    }
    with plt.rc_context(style):
        fig, ax = plt.subplots(figsize=(6.8, 3.5))
        fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
        ax.set(xlim=(0, 6.8), ylim=(0, 3.5))
        ax.axis("off")

        def text(x, y, value, size=8.4, bold=False, color=INK, ha="center"):
            return ax.text(x, y, value, fontsize=size,
                           fontweight="bold" if bold else "normal", color=color,
                           ha=ha, va="center", linespacing=1.25, zorder=4)

        def line(xs, ys, color=LINE, dotted=False, width=.7):
            ax.plot(xs, ys, color=color, lw=width, solid_capstyle="butt",
                    linestyle=(0, (1.2, 2.1)) if dotted else "-", zorder=1)

        def box(x, y, w, h, dashed=False):
            ax.add_patch(Rectangle((x, y), w, h, facecolor="white",
                         edgecolor=LIGHT if dashed else LINE, lw=.7,
                         linestyle=(0, (5, 3)) if dashed else "-", zorder=0))

        def arrow(x1, y1, x2, y2, dotted=False, color=LINE):
            ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                         mutation_scale=7.1, lw=.7, color=color, shrinkA=0, shrinkB=0,
                         linestyle=(0, (1.2, 2.1)) if dotted else "-", zorder=2))

        # The dashed outer boundary encloses every modelled life-cycle process.
        text(3.4, 3.39, f"One student · {fmt(n)} formal events · One year", size=9.1, bold=True)
        box(.08, .43, 6.64, 2.79, dashed=True)
        boundary_label = text(.23, 3.22, " Modelled product system ", size=8.3,
                              bold=True, color=TEAL, ha="left")
        boundary_label.set_bbox({"facecolor": "white", "edgecolor": "none", "pad": .6})

        # This complete lifetime chain distinguishes disposal from annual activity.
        stages = [
            (.22, 1.30, "Manufacturing\n$M$", 8.5),
            (1.76, 1.45, "Distribution / retail\n$D$", 8.5),
            (3.45, 1.33, f"Lifetime use\n{fmt(lifetime)} total wears", 8.5),
            (5.02, 1.56, "End-of-life treatment, $F$\nCollection + incineration\nGross emissions", 7.8),
        ]
        for x, w, label, size in stages:
            box(x, 2.64, w, .46)
            text(x + w/2, 2.87, label, size=size)
        for start, stop in [(1.52, 1.76), (3.21, 3.45), (4.78, 5.02)]:
            arrow(start, 2.87, stop, 2.87)
        text(.24, 2.48, rf"Shared burden per option: $\frac{{{fmt(n)}}}{{{fmt(lifetime)}}}(M+D+F)$",
             size=8.3, color=TEAL, ha="left")

        # Dotted links show an expansion of lifetime use into annual scenarios.
        line([4.115, 4.115], [2.64, 2.37], color=TEAL, dotted=True)
        line([1.20, 5.60], [2.37, 2.37], color=TEAL, dotted=True)
        for x in [1.20, 3.40, 5.60]:
            arrow(x, 2.37, x, 2.30, dotted=True, color=TEAL)
        for x, title in [(1.20, "New purchase"), (3.40, "Second-hand purchase"), (5.60, "Rental")]:
            text(x, 2.23, title, size=9.0, bold=True, color=TEAL)

        # Acquisition and subsequent use form two ownership activity systems.
        delivery_label = ("1 acquisition\n"
                          f"{fmt(delivery_route)} vehicle-km / {fmt(p['delivery_batch'])} garments\n"
                          f"= {fmt(delivery)} allocated vehicle-km")
        for offset in [0, 2.20]:
            centre = 1.20 + offset
            box(.22 + offset, 1.66, 1.96, .46)
            text(centre, 1.89, delivery_label, size=8.0)
            arrow(centre, 1.66, centre, 1.55)
            box(.65 + offset, 1.30, 1.10, .25)
            text(centre, 1.425, f"Initial clean × {fmt(p['initial_owned_cleans'])}", size=8.1)
            line([centre, centre, .65 + offset], [1.30, 1.23, 1.23])
            arrow(.65 + offset, 1.23, .65 + offset, 1.13)
            box(.22 + offset, .82, .86, .31)
            box(1.32 + offset, .82, .86, .31)
            text(.65 + offset, .975, f"Use\n{fmt(n)} wears", size=8.3)
            text(1.75 + offset, .975, f"Clean\n{fmt(clean_count)} cleans", size=8.3)
            arrow(1.08 + offset, .975, 1.32 + offset, .975)
            line([1.75 + offset, 1.75 + offset, .65 + offset], [.82, .70, .70])
            arrow(.65 + offset, .70, .65 + offset, .82)

        # The rental access process includes passenger travel, measured as such.
        box(4.62, 1.66, 1.96, .46)
        text(5.60, 1.89,
             f"{fmt(n)} bookings; collection + return\n"
             f"Passenger travel: {fmt(n)} × {fmt(p['rental_legs'])} × {fmt(p['one_way_km'])}\n"
             f"= {fmt(rental_distance)} passenger-km", size=8.0)
        arrow(5.05, 1.66, 5.05, 1.13)
        box(4.62, .82, .86, .31)
        box(5.72, .82, .86, .31)
        text(5.05, .975, f"Use\n{fmt(n)} wears", size=8.3)
        text(6.15, .975, f"Return / clean\n{fmt(clean_count)} cleans", size=7.8)
        arrow(5.48, .975, 5.72, .975)
        line([6.15, 6.15, 6.00], [1.13, 1.39, 1.39])
        arrow(6.00, 1.39, 6.00, 1.66)
        text(5.60, 1.39, "Service\ncycle", size=8.1)

        text(3.40, .55, "Common cleaning proxy: washing, drying and ironing", size=8.0)
        # Arrow semantics keep accounting detail distinct from physical flow.
        arrow(.22, .285, .51, .285)
        text(.58, .285, "Garment flow", size=7.8, ha="left")
        arrow(2.12, .285, 2.41, .285, dotted=True, color=TEAL)
        text(2.48, .285, "Annual detail / allocation", size=7.8, ha="left")
        text(5.60, .285, "Dashed outline: system boundary", size=7.5)
        text(3.4, .105, r"Calculated result: GHG emissions (kg CO$_2$e / functional unit)",
             size=8.5, bold=True)

        fig.savefig(output_dir / "lca_boundary.pdf", metadata={"CreationDate": None, "ModDate": None})
        fig.savefig(output_dir / "lca_boundary.svg", metadata={"Date": None})
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

"""Silkscreen-only view of the main board: outlines from the KiCad footprints, labels, pads, no copper.

    python silk.py  ->  silk_layout.png (for the screen) + silk_layout_1to1.pdf (print at 100% to test-fit parts)
"""
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle, FancyBboxPatch, Polygon as MPoly
import design, fplib, layout

MM2PT = 72 / 25.4
BOARD, SILK, PAD, HOLE, EDGE, DIM = "#17402b", "#f3f1e8", "#c9b27c", "#0b0f0d", "#d8c46a", "#9fb7a6"
FONT = "DejaVu Sans"

def text(ax, x, y, s, h=1.0, rot=0, ha="center", va="center", color=SILK, weight="normal", family=FONT):
    ax.text(x, y, s, fontsize=h * MM2PT * 1.38, rotation=rot, ha=ha, va=va, color=color, family=family,
            fontweight=weight, zorder=9)

def fp_silk(ax, inst):
    for layer, kind, d, w, filled in inst.fp.graphics:
        if layer != "F.SilkS":
            continue
        lw = max(w, 0.12) * MM2PT
        if kind == "line":
            (x0, y0), (x1, y1) = inst.pt(*d[0]), inst.pt(*d[1])
            ax.plot([x0, x1], [y0, y1], color=SILK, lw=lw, solid_capstyle="round", zorder=7)
        elif kind == "rect":
            (ax0, ay0), (ax1, ay1) = d
            pts = [inst.pt(ax0, ay0), inst.pt(ax1, ay0), inst.pt(ax1, ay1), inst.pt(ax0, ay1)]
            ax.add_patch(MPoly(pts, closed=True, fill=filled, fc=SILK if filled else "none", ec=SILK, lw=lw, zorder=7))
        elif kind == "circle":
            c = inst.pt(*d[0]); r = math.hypot(d[1][0] - d[0][0], d[1][1] - d[0][1])
            ax.add_patch(Circle(c, r, fill=filled, fc=SILK if filled else "none", ec=SILK, lw=lw, zorder=7))
        elif kind == "arc":
            pts = [inst.pt(*p) for p in fplib.arc_points(d)]
            ax.plot([p[0] for p in pts], [p[1] for p in pts], color=SILK, lw=lw, zorder=7)
        elif kind == "poly":
            pts = [inst.pt(*p) for p in d]
            ax.add_patch(MPoly(pts, closed=True, fill=filled, fc=SILK if filled else "none", ec=SILK, lw=lw, zorder=7))

def pads(ax, board):
    from render import _patch
    for p in board.pads:
        g = p["layers"].get("F.Cu")
        if g is not None:
            _patch(ax, g, facecolor=PAD, edgecolor="none", zorder=5)
        if p["drill"]:
            ax.add_patch(Circle(p["c"], p["drill"][0] / 2, color=HOLE, zorder=6))

def labels(ax, b):
    P = b.parts
    def c(ref):
        g = P[ref].courtyard()
        return g.centroid.x, g.centroid.y, g.bounds
    # ICs in sockets: ref + part inside the outline
    for ref, sub in [("U2", "MCP23017 · 0x20"), ("U3", "MCP23017 · 0x21"), ("U4", "ULN2803A · N2 S2"),
                     ("U5", "ULN2803A · O1 K1"), ("U6", "ULN2803A · DRUM M2")]:
        x, y, _ = c(ref)
        text(ax, x, y - 0.9, ref, 1.5, weight="bold"); text(ax, x, y + 1.1, sub, 1.05)
    x, y, _ = c("U7")
    text(ax, x, y - 1.2, "U7", 1.5, rot=90, weight="bold"); text(ax, x + 1.6, y, "74AHCT245 · CALENDAR", 1.05, rot=90)
    # motor sockets: name under the body, wire colours under the pins
    for i, m in enumerate(design.MOTORS):
        x0 = P[f"J{10 + i}"].x
        text(ax, x0 + 5.0, 10.9, m, 1.5, weight="bold")
        for k, col in enumerate("BPYOR"):
            text(ax, x0 + 2.5 * k, 8.9, col, 0.75, color=DIM)
    text(ax, 125.2, 10.6, "B P Y O R =\nblue pink yellow\norange red", 0.7, ha="right", color=DIM)
    # Hall sockets: name and pin legend above
    for i, h in enumerate(design.HALLS):
        inst = P[f"J{20 + i}"]
        text(ax, inst.x + 2.5, inst.y - 5.4, h, 1.3, weight="bold")
        for k, s_ in enumerate(["+", "S", "−"]):
            text(ax, inst.x + 2.5 * k, inst.y - 3.35, s_, 0.75, color=DIM)
    text(ax, 92.0, 76.9, "HALL: + 3V3 · S signal · − GND", 0.8, ha="left", color=DIM)
    # calendar socket
    inst = P["J5"]
    text(ax, inst.x - 4.6, inst.y - 8.75, "CALENDAR · BKA30D-R5", 1.2, rot=90, weight="bold")
    text(ax, inst.x - 0.2, inst.y + 3.9, "1", 0.8, color=DIM)
    text(ax, inst.x + 2.4, inst.y - 3.75, "YEAR 1–4", 0.8, rot=90, color=DIM)
    text(ax, inst.x + 2.4, inst.y - 13.75, "MOON 5–8", 0.8, rot=90, color=DIM)
    text(ax, 119.3, 57.6, "5V IN  ⊕ centre", 1.1, weight="bold")
    # expansion header
    inst = P["J4"]
    for k, s_ in enumerate(["3V3", "GND", "SDA", "SCL", "IO14", "IO34"]):
        text(ax, inst.x + 1.9, inst.y + 2.54 * k, s_, 0.8, ha="left")
    text(ax, 0.9, inst.y - 2.8, "J4 EXP", 1.0, ha="left", weight="bold")
    # everything else: ref + value, placed by hand (board mm)
    small = [
        ("R1 4k7", 58.27, 43.2, 0, "center"), ("R2 4k7", 63.57, 43.2, 0, "center"),
        ("R3 10k", 68.87, 43.2, 0, "center"), ("R4 10k", 74.17, 43.2, 0, "center"),
        ("R5 1k", 89.27, 46.3, 0, "center"), ("R6 1k", 75.77, 46.8, 0, "center"),
        ("R7 10k", 75.77, 55.9, 0, "center"), ("R8 1k", 99.77, 61.3, 0, "center"),
        ("Q1 IRLIB9343", 82.5, 37.9, 0, "center"), ("Q2 2N3904", 81.8, 52.9, 0, "center"),
        ("D2 1N5819", 94.4, 44.9, 0, "center"), ("C1 1000µ", 90.5, 66.8, 0, "center"),
        ("C5", 117.5, 20.6, 0, "center"), ("C6 100n", 38.0, 37.6, 0, "left"), ("C7 100n", 70.1, 37.6, 0, "right"),
        ("PWR", 99.8, 72.1, 0, "center"), ("F1 2.5A", 103.6, 65.0, 90, "center"),
        ("RN1 8×10k", 103.0, 54.6, 0, "center"), ("RN2 7×10k", 67.3, 66.5, 0, "center"),
        ("D1 1N5819", 7.2, 32.3, 90, "center"),
    ]
    for s_, x, y, rot, ha in small:
        text(ax, x, y, s_, 0.95, rot=rot, ha=ha)
    # DevKit outline and notes
    x0, y0, x1, y1 = design.DEVKIT
    ax.add_patch(Rectangle((x0 + 0.1, y0), x1 - x0 - 0.2, y1 - y0, fill=False, ec=SILK, lw=0.15 * MM2PT, ls=(0, (6, 4)), zorder=7))
    text(ax, (x0 + x1) / 2, 50.5, "ESP32-DevKitC-32E", 2.2, weight="bold")
    text(ax, (x0 + x1) / 2, 54.2, "plugs in here · nothing underneath", 1.2)
    text(ax, 1.2, 54.1, "◄ USB", 1.4, ha="left", weight="bold")
    text(ax, 52.6, 54.1, "antenna", 1.0, rot=90)
    text(ax, 5.2, 44.8, "5V", 0.9, color=DIM); text(ax, 49.9, 44.8, "3V3", 0.9, color=DIM)
    text(ax, 49.9, 63.4, "GND", 0.9, color=DIM)
    text(ax, 27.0, 44.8, "J2 side", 0.9, color=DIM); text(ax, 27.0, 63.4, "J3 side", 0.9, color=DIM)
    # title
    text(ax, 68.5, 58.8, "TIDE MACHINE", 2.4, weight="bold")
    text(ax, 68.5, 62.2, "main board · rev A", 1.3)
    text(ax, 68.5, 64.4, "127 × 81.3 mm · all through-hole", 0.95, color=DIM)
    # mounting holes: washer ring
    for (hx, hy) in design.HOLES:
        ax.add_patch(Circle((hx, hy), 3.0, fill=False, ec=SILK, lw=0.15 * MM2PT, zorder=7))

def draw(path_png, path_pdf):
    b = layout.Board()
    W, H, m = design.BOARD_W, design.BOARD_H, 4.0
    fig = plt.figure(figsize=((W + 2 * m) / 25.4, (H + 2 * m) / 25.4))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(-m, W + m); ax.set_ylim(H + m, -m); ax.set_aspect("equal"); ax.axis("off")
    fig.patch.set_facecolor("white")
    ax.add_patch(Rectangle((0, 0), W, H, fc=BOARD, ec=EDGE, lw=0.3 * MM2PT, zorder=0))
    pads(ax, b)
    for inst in b.parts.values():
        fp_silk(ax, inst)
    labels(ax, b)
    for (hx, hy) in design.HOLES:
        ax.add_patch(Circle((hx, hy), 1.6, color="white", zorder=6))
    # scale bar for the printed copy
    ax.plot([0, 50], [H + 2.2, H + 2.2], color="black", lw=0.3 * MM2PT)
    for t in (0, 10, 20, 30, 40, 50):
        ax.plot([t, t], [H + 1.6, H + 2.8], color="black", lw=0.25 * MM2PT)
    ax.text(51.5, H + 2.2, "50 mm: check this before test-fitting parts", fontsize=6, va="center", family=FONT)
    fig.savefig(path_pdf)
    fig.savefig(path_png, dpi=400)
    plt.close(fig)

if __name__ == "__main__":
    draw("silk_layout.png", "silk_layout_1to1.pdf")
    print("silk_layout.png, silk_layout_1to1.pdf")

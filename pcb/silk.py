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
    import silk_labels
    for L in silk_labels.labels():
        text(ax, L["x"], L["y"], L["text"], L["h"], rot=L["rot"], ha=L["ha"],
             weight="bold" if L["bold"] else "normal", color=DIM if L["dim"] else SILK)
    for sh in silk_labels.shapes():
        if sh[0] == "rect_dashed":
            _, x0, y0, x1, y1 = sh
            ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, ec=SILK, lw=0.15 * MM2PT, ls=(0, (6, 4)), zorder=7))
        elif sh[0] == "circle":
            _, x, y, r = sh
            ax.add_patch(Circle((x, y), r, fill=False, ec=SILK, lw=0.15 * MM2PT, zorder=7))

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

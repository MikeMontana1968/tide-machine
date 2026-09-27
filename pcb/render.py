"""PNG previews of the board (placement, copper, silkscreen) with matplotlib."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch
from matplotlib.path import Path
from shapely.geometry import Polygon, MultiPolygon, GeometryCollection

def _patch(ax, g, **kw):
    if g is None or g.is_empty:
        return
    polys = [g] if isinstance(g, Polygon) else [p for p in getattr(g, "geoms", []) if isinstance(p, Polygon)]
    for p in polys:
        verts, codes = [], []
        for ring in [p.exterior] + list(p.interiors):
            xs, ys = ring.coords.xy
            pts = list(zip(xs, ys))
            verts += pts
            codes += [Path.MOVETO] + [Path.LINETO] * (len(pts) - 2) + [Path.CLOSEPOLY]
        ax.add_patch(PathPatch(Path(verts, codes), **kw))

def draw(board, path, routed=None, fills=None, title="", show=("F.Cu", "B.Cu"), courtyards=True, labels=True, silk=None, dpi=150):
    fig, ax = plt.subplots(figsize=(12, 9.5))
    ax.set_aspect("equal"); ax.invert_yaxis()
    W, H = board.outline.bounds[2], board.outline.bounds[3]
    ax.set_xlim(-3, W + 3); ax.set_ylim(H + 3, -3)
    _patch(ax, board.outline, facecolor="#1d3b2a", edgecolor="#d9c36a", lw=1.2, zorder=0)
    col = {"F.Cu": "#c8553d", "B.Cu": "#3d7cc8"}
    if fills:
        for l in show[::-1]:
            if l in fills:
                _patch(ax, fills[l], facecolor=col[l], alpha=0.28, edgecolor="none", zorder=1)
    if routed:
        for l in show[::-1]:
            for seg in routed["tracks"]:
                if seg["layer"] == l:
                    (x0, y0), (x1, y1) = seg["a"], seg["b"]
                    ax.plot([x0, x1], [y0, y1], color=col[l], lw=seg["w"] * 72 / 25.4 * 12 / (W + 6) * 9.5 * 1.25,
                            solid_capstyle="round", alpha=0.9, zorder=3 if l == "F.Cu" else 2)
        for v in routed["vias"]:
            ax.add_patch(plt.Circle(v["c"], v["d"] / 2, color="#e0e0e0", zorder=5))
            ax.add_patch(plt.Circle(v["c"], v["drill"] / 2, color="#111", zorder=6))
    for p in board.pads:
        for l in show[::-1]:
            if l in p["layers"]:
                _patch(ax, p["layers"][l], facecolor="#e8b04a" if len(p["layers"]) > 1 else col[l], edgecolor="none", zorder=4)
        if p["drill"]:
            ax.add_patch(plt.Circle(p["c"], p["drill"][0] / 2, color="#111", zorder=6))
    if silk is not None:
        _patch(ax, silk, facecolor="#f4f4f4", edgecolor="none", zorder=7, alpha=0.95)
    if courtyards:
        for ref, inst in board.parts.items():
            c = inst.courtyard()
            if c is not None:
                _patch(ax, c, facecolor="none", edgecolor="#9ad0ff", lw=0.5, ls="--", zorder=8)
    if labels:
        for ref, inst in board.parts.items():
            c = inst.courtyard()
            if c is None:
                continue
            x, y = c.centroid.x, c.centroid.y
            ax.text(x, y, ref, color="white", fontsize=6, ha="center", va="center", zorder=9,
                    bbox=dict(boxstyle="round,pad=0.1", fc="#00000080", ec="none"))
    ax.set_title(title, fontsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=dpi, facecolor="#10151a")
    plt.close(fig)

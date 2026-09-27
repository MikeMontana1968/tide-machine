"""KiCad footprint (.kicad_mod) reader: pads and graphics, as plain data plus shapely geometry.

Only what the board pipeline needs: pad number/type/shape/size/drill/layers/rotation/roundrect ratio,
and silkscreen / courtyard / fab graphics (lines, rects, circles, arcs, polygons).
"""
import math, re, os
from shapely.geometry import Polygon, Point, LineString, box as sbox
from shapely import affinity

HERE = os.path.dirname(os.path.abspath(__file__))

# ------------------------------------------------------------------ s-expressions ------------------------
_tok = re.compile(r'\s*(?:(\()|(\))|"((?:[^"\\]|\\.)*)"|([^\s()"]+))')

def parse(text):
    stack, cur = [], []
    for m in _tok.finditer(text):
        lp, rp, qs, atom = m.groups()
        if lp:
            stack.append(cur); cur = []
        elif rp:
            done = cur; cur = stack.pop(); cur.append(done)
        elif qs is not None:
            cur.append(Q(qs.replace('\\"', '"')))
        elif atom is not None:
            cur.append(atom)
    return cur[0]

class Q(str):
    """a quoted string, so the writer can quote it again"""

def dump(x, ind=0):
    if isinstance(x, list):
        inner = [dump(e, ind + 1) for e in x]
        one = "(" + " ".join(inner) + ")"
        if len(one) < 100 and "\n" not in one:
            return one
        return "(" + inner[0] + "".join("\n" + "  " * (ind + 1) + s for s in inner[1:]) + ")"
    if isinstance(x, Q):
        return '"' + x.replace('"', '\\"') + '"'
    if isinstance(x, float):
        return f"{x:.4f}".rstrip("0").rstrip(".") if x != int(x) else str(int(x))
    return str(x)

def find(node, key):
    for e in node:
        if isinstance(e, list) and e and e[0] == key:
            return e
    return None

def findall(node, key):
    return [e for e in node if isinstance(e, list) and e and e[0] == key]

def nums(node, key, n=None):
    e = find(node, key)
    if e is None:
        return None
    v = [float(t) for t in e[1:] if not isinstance(t, list) and _isnum(t)]
    return v if n is None else v[:n]

def _isnum(t):
    try:
        float(t); return True
    except ValueError:
        return False

# ------------------------------------------------------------------ footprint ----------------------------
class Pad:
    def __init__(self, e):
        self.num = str(e[1])
        self.kind = e[2]                     # thru_hole | smd | np_thru_hole | connect
        self.shape = e[3]                    # circle | rect | oval | roundrect | custom
        at = nums(e, "at")
        self.x, self.y = at[0], at[1]
        self.rot = at[2] if len(at) > 2 else 0.0
        self.w, self.h = nums(e, "size", 2)
        d = find(e, "drill")
        self.drill = None
        if d is not None:
            v = [float(t) for t in d[1:] if not isinstance(t, list) and _isnum(t)]
            self.drill = (v[0], v[1] if len(v) > 1 and "oval" in d else v[0]) if v else None
        lay = find(e, "layers")
        self.layers = [str(t) for t in lay[1:]] if lay else []
        rr = nums(e, "roundrect_rratio")
        self.rratio = rr[0] if rr else 0.0

    def local_shape(self, grow=0.0):
        """pad outline in footprint coordinates (pad rotation applied), optionally grown"""
        w, h = self.w + 2 * grow, self.h + 2 * grow
        if self.shape == "circle":
            g = Point(0, 0).buffer(w / 2, 32)
        elif self.shape == "oval":
            r = min(w, h) / 2
            g = LineString([(-(w / 2 - r), 0), (w / 2 - r, 0)] if w >= h else [(0, -(h / 2 - r)), (0, h / 2 - r)]).buffer(r, 16) \
                if abs(w - h) > 1e-6 else Point(0, 0).buffer(r, 32)
        elif self.shape == "roundrect":
            r = self.rratio * min(self.w, self.h) + grow
            g = sbox(-w / 2 + r, -h / 2 + r, w / 2 - r, h / 2 - r).buffer(r, 8) if r > 0 else sbox(-w / 2, -h / 2, w / 2, h / 2)
        else:
            g = sbox(-w / 2, -h / 2, w / 2, h / 2)
        g = rotate_ccw(g, self.rot)
        return affinity.translate(g, self.x, self.y)

    @property
    def copper_layers(self):
        L = set()
        for l in self.layers:
            if l in ("*.Cu", "F&B.Cu"):
                L |= {"F.Cu", "B.Cu"}
            elif l in ("F.Cu", "B.Cu"):
                L.add(l)
        return sorted(L)

def rotate_ccw(g, deg):
    """KiCad angles: counter-clockwise on screen, y pointing down -> a clockwise rotation in y-up maths"""
    return affinity.rotate(g, -deg, origin=(0, 0)) if deg else g

class Footprint:
    def __init__(self, name):
        self.name = name
        path = os.path.join(HERE, "footprints", name.split(":")[-1] + ".kicad_mod")
        self.tree = parse(open(path, encoding="utf8").read())
        self.pads = [Pad(e) for e in findall(self.tree, "pad")]
        self.graphics = []                   # (layer, kind, data, width)
        for e in self.tree:
            if not (isinstance(e, list) and e and str(e[0]).startswith("fp_")):
                continue
            lay = find(e, "layer")
            layer = str(lay[1]) if lay else ""
            st = find(e, "stroke")
            wid = nums(st, "width")[0] if st is not None and find(st, "width") else (nums(e, "width") or [0.12])[0]
            fill = find(e, "fill")
            filled = fill is not None and str(fill[1]) in ("yes", "solid")
            k = e[0]
            if k == "fp_line":
                self.graphics.append((layer, "line", [nums(e, "start", 2), nums(e, "end", 2)], wid, False))
            elif k == "fp_rect":
                self.graphics.append((layer, "rect", [nums(e, "start", 2), nums(e, "end", 2)], wid, filled))
            elif k == "fp_circle":
                self.graphics.append((layer, "circle", [nums(e, "center", 2), nums(e, "end", 2)], wid, filled))
            elif k == "fp_arc":
                self.graphics.append((layer, "arc", [nums(e, "start", 2), nums(e, "mid", 2), nums(e, "end", 2)], wid, False))
            elif k == "fp_poly":
                pts = [[float(v) for v in xy[1:3]] for xy in findall(find(e, "pts"), "xy")]
                self.graphics.append((layer, "poly", pts, wid, filled))
        self.attr = (find(self.tree, "attr") or ["attr", "through_hole"])[1]
        ref = [p for p in findall(self.tree, "property") if str(p[1]) == "Reference"]
        self.ref_at = nums(ref[0], "at") if ref else [0, 0, 0]

    def courtyard(self):
        """union of F.CrtYd graphics as a polygon (footprint coordinates)"""
        polys, lines = [], []
        for layer, kind, d, w, f in self.graphics:
            if layer != "F.CrtYd":
                continue
            if kind == "rect":
                (x0, y0), (x1, y1) = d
                polys.append(sbox(min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)))
            elif kind == "circle":
                (cx, cy), (ex, ey) = d
                polys.append(Point(cx, cy).buffer(math.hypot(ex - cx, ey - cy), 32))
            elif kind == "poly":
                polys.append(Polygon(d))
            elif kind == "line":
                lines.append(d)
            elif kind == "arc":
                lines.extend(arc_points_pairs(d))
        if lines:
            from shapely.ops import polygonize, unary_union
            polys += list(polygonize(unary_union([LineString(l) for l in lines])))
        from shapely.ops import unary_union
        return unary_union(polys) if polys else None

def arc_points(d, n=24):
    (x0, y0), (xm, ym), (x1, y1) = d
    # circle through three points
    ax, ay, bx, by, cx, cy = x0, y0, xm, ym, x1, y1
    D = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    if abs(D) < 1e-12:
        return [(x0, y0), (x1, y1)]
    ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) * (cy - ay) + (cx * cx + cy * cy) * (ay - by)) / D
    uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) * (ax - cx) + (cx * cx + cy * cy) * (bx - ax)) / D
    r = math.hypot(ax - ux, ay - uy)
    a0, am, a1 = (math.atan2(p[1] - uy, p[0] - ux) for p in ((ax, ay), (bx, by), (cx, cy)))
    def norm(a):
        return a % (2 * math.pi)
    # go from a0 to a1 through am
    s = norm(am - a0) < norm(a1 - a0)
    span = norm(a1 - a0) if s else -norm(a0 - a1)
    return [(ux + r * math.cos(a0 + span * i / n), uy + r * math.sin(a0 + span * i / n)) for i in range(n + 1)]

def arc_points_pairs(d):
    p = arc_points(d)
    return [[p[i], p[i + 1]] for i in range(len(p) - 1)]

_cache = {}
def load(name):
    if name not in _cache:
        _cache[name] = Footprint(name)
    return _cache[name]

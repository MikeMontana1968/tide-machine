"""Two-layer grid router for the main board (A* with turn and via costs, exact clearance rasters).

    python route.py            # routes every net except GND (the ground pours carry it) -> routes.json
    python route.py --gnd      # after build_board.py --apply: joins any GND pads the pours didn't reach

Reads pads.json (exported by build_board.py from KiCad's own pad shapes) and the net classes in design.py.
Grid 0.254 mm, so the 2.54 mm headers' gaps fall on grid lines. For every query class (a track width or via
size, with its clearance) each piece of copper is rasterised as the region that class's centreline may not
enter; each cell remembers the owning net (-2 if several), so a net may cross its own copper but keeps clear
of everyone else's. KiCad's DRC has the final word.
"""
import sys, json, math, heapq, random, os, time
import numpy as np
import shapely
from shapely.geometry import Polygon, Point, LineString, box as sbox
from scipy.ndimage import distance_transform_edt
import design

HERE = os.path.dirname(os.path.abspath(__file__))
G = 0.254
MARGIN = 0.07
EDGE_CLEAR = 0.3
HOLE_KEEPOUT = 3.3
VIA = {"small": (0.6, 0.3), "power": (0.8, 0.4)}
TCLS = {"Default": design.DEFAULT, **{k: (w, c) for k, (w, c, _) in design.NETCLASS.items()}}
TCLS.setdefault("Gnd", (0.5, 0.25))
QCLS = {f"T_{k}": (w / 2, c) for k, (w, c) in TCLS.items()}
QCLS.update({"V_small": (0.3, 0.2), "V_power": (0.4, 0.25)})
LAYERS = ["F.Cu", "B.Cu"]
DIRS = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]
STEP = [1.0, 1.4142, 1.0, 1.4142, 1.0, 1.4142, 1.0, 1.4142]
PREF = [[1.0, 1.2, 1.5, 1.2, 1.0, 1.2, 1.5, 1.2], [1.5, 1.2, 1.0, 1.2, 1.5, 1.2, 1.0, 1.2]]   # F horizontal, B vertical
TURN = [0.0, 0.3, 1.2, 5.0, 1e9, 5.0, 1.2, 0.3]
VIA_COST = 8.0

def netclass(net):
    if net == "GND":
        return ("Gnd",) + TCLS["Gnd"]
    return design.netclass(net)

class Router:
    def __init__(self, data):
        self.W, self.H = data["W"], data["H"]
        self.nx, self.ny = int(round(self.W / G)) + 1, int(round(self.H / G)) + 1
        self.xs, self.ys = np.arange(self.nx) * G, np.arange(self.ny) * G
        self.pads = []
        for p in data["pads"]:
            layers = {l: Polygon(pts).buffer(0) for l, pts in p["layers"].items() if len(pts) >= 3}
            self.pads.append(dict(p, geo=layers))
        self.nets = sorted({p["net"] for p in self.pads if p["net"]})
        self.netid = {n: i + 1 for i, n in enumerate(self.nets)}
        self.holes_mech = data["holes"]
        self.devkit = data["devkit"]
        self.antenna = data["antenna"]
        self.reset()

    def reset(self):
        self.owner = {(q, l): np.zeros((self.ny, self.nx), np.int32) for q in QCLS for l in range(2)}
        self.cu = [np.zeros((self.ny, self.nx), np.int32) for _ in range(2)]
        self.holes = []
        self.tracks, self.vias = [], []
        self._keepouts()
        for p in self.pads:
            nid = self.netid.get(p["net"], -1)
            c_obj = netclass(p["net"])[2] if p["net"] else 0.2
            for l, g in p["geo"].items():
                self._add(nid, g, LAYERS.index(l), c_obj)
            if p["drill"]:
                self.holes.append((p["c"][0], p["c"][1], p["drill"] / 2))
        for hx, hy in self.holes_mech:
            self.holes.append((hx, hy, 1.6))

    # ------------------------------------------------------------ rasters
    def _cells(self, geom):
        minx, miny, maxx, maxy = geom.bounds
        i0, i1 = max(0, int(math.floor(minx / G))), min(self.nx - 1, int(math.ceil(maxx / G)))
        j0, j1 = max(0, int(math.floor(miny / G))), min(self.ny - 1, int(math.ceil(maxy / G)))
        if i1 < i0 or j1 < j0:
            return None
        X, Y = np.meshgrid(self.xs[i0:i1 + 1], self.ys[j0:j1 + 1])
        shapely.prepare(geom)
        return j0, i0, shapely.contains_xy(geom, X, Y)

    @staticmethod
    def _mark(arr, nid, cells):
        if cells is None:
            return
        j0, i0, m = cells
        sub = arr[j0:j0 + m.shape[0], i0:i0 + m.shape[1]]
        o = sub[m]
        sub[m] = np.where((o == 0) | (o == nid), nid, -2)

    def _add(self, nid, geom, layer, c_obj):
        for q, (hw, c) in QCLS.items():
            self._mark(self.owner[(q, layer)], nid, self._cells(geom.buffer(hw + max(c, c_obj) + MARGIN, 8)))
        cells = self._cells(geom)
        if cells is not None:
            j0, i0, m = cells
            sub = self.cu[layer][j0:j0 + m.shape[0], i0:i0 + m.shape[1]]
            sub[m & (sub == 0)] = nid

    def _keepouts(self):
        board = sbox(0, 0, self.W, self.H)
        antenna = Polygon(self.antenna)
        for q, (hw, c) in QCLS.items():
            bad = board.exterior.buffer(EDGE_CLEAR + hw + MARGIN, 4).union(antenna.buffer(hw + 0.2))
            for hx, hy in self.holes_mech:
                bad = bad.union(Point(hx, hy).buffer(HOLE_KEEPOUT + hw, 24))
            for l in range(2):
                self._mark(self.owner[(q, l)], -3, self._cells(bad))

    def holemask(self, drill):
        m = np.zeros((self.ny, self.nx), bool)
        for x, y, r in self.holes:
            cells = self._cells(Point(x, y).buffer(r + drill / 2 + 0.3, 12))
            if cells:
                j0, i0, mm = cells
                m[j0:j0 + mm.shape[0], i0:i0 + mm.shape[1]] |= mm
        return m

    # ------------------------------------------------------------ copper out
    def add_track(self, net, a, b, w, layer):
        nid = self.netid[net]
        g = LineString([a, b]).buffer(w / 2, 8) if a != b else Point(a).buffer(w / 2, 8)
        self._add(nid, g, layer, netclass(net)[2])
        self.tracks.append(dict(net=net, a=[round(a[0], 4), round(a[1], 4)], b=[round(b[0], 4), round(b[1], 4)], w=w, layer=LAYERS[layer]))

    def add_via(self, net, c, kind):
        nid = self.netid[net]
        d, drill = VIA[kind]
        g = Point(c).buffer(d / 2, 16)
        for l in range(2):
            self._add(nid, g, l, netclass(net)[2])
        self.holes.append((c[0], c[1], drill / 2))
        self.vias.append(dict(net=net, c=[round(c[0], 4), round(c[1], 4)], d=d, drill=drill))

    # ------------------------------------------------------------ search
    def search(self, net, srcs, tgt_mask, max_expand=600000):
        cls, w, c = netclass(net)
        nid = self.netid[net]
        qT = f"T_{cls}"
        vk = "power" if cls in ("Power",) else "small"
        qV = f"V_{vk}"
        freeT = [(self.owner[(qT, l)] == 0) | (self.owner[(qT, l)] == nid) for l in range(2)]
        freeV = ((self.owner[(qV, 0)] == 0) | (self.owner[(qV, 0)] == nid)) & \
                ((self.owner[(qV, 1)] == 0) | (self.owner[(qV, 1)] == nid)) & ~self.holemask(VIA[vk][1])
        tgt = [tgt_mask[l] & freeT[l] for l in range(2)]
        if not (tgt[0].any() or tgt[1].any()):
            return None
        d = [distance_transform_edt(~tgt[l]) if tgt[l].any() else np.full((self.ny, self.nx), 1e6) for l in range(2)]
        h = [np.minimum(d[0], d[1] + VIA_COST), np.minimum(d[1], d[0] + VIA_COST)]
        nx, ny = self.nx, self.ny
        best, par, pq = {}, {}, []
        for (l, j, i, g0) in srcs:
            if not freeT[l][j, i]:
                continue
            k = ((l * ny + j) * nx + i) * 9 + 8
            if g0 < best.get(k, 1e18):
                best[k] = g0; par[k] = -1
                heapq.heappush(pq, (g0 + h[l][j, i], g0, l, j, i, 8))
        n = 0
        while pq:
            f, g, l, j, i, dr = heapq.heappop(pq)
            k = ((l * ny + j) * nx + i) * 9 + dr
            if g > best.get(k, 1e18) + 1e-9:
                continue
            if tgt[l][j, i]:
                path = []
                while k != -1:
                    s = k // 9
                    path.append((s // (nx * ny), (s // nx) % ny, s % nx))
                    k = par[k]
                return path[::-1]
            n += 1
            if n > max_expand:
                return None
            fr, pl, hl = freeT[l], PREF[l], h[l]
            for nd in range(8):
                dx, dy = DIRS[nd]
                i2, j2 = i + dx, j + dy
                if i2 < 0 or j2 < 0 or i2 >= nx or j2 >= ny or not fr[j2, i2]:
                    continue
                tc = 0.0 if dr == 8 else TURN[(nd - dr) % 8]
                if tc > 1e8:
                    continue
                if dx and dy and not (fr[j, i2] or fr[j2, i]):
                    continue                        # don't squeeze diagonally between two blocked cells
                g2 = g + STEP[nd] * pl[nd] + tc
                k2 = ((l * ny + j2) * nx + i2) * 9 + nd
                if g2 < best.get(k2, 1e18) - 1e-9:
                    best[k2] = g2; par[k2] = k
                    heapq.heappush(pq, (g2 + hl[j2, i2], g2, l, j2, i2, nd))
            if freeV[j, i]:
                l2 = 1 - l
                if freeT[l2][j, i]:
                    g2 = g + VIA_COST
                    k2 = ((l2 * ny + j) * nx + i) * 9 + 8
                    if g2 < best.get(k2, 1e18) - 1e-9:
                        best[k2] = g2; par[k2] = k
                        heapq.heappush(pq, (g2 + h[l2][j, i], g2, l2, j, i, 8))
        return None

    def commit(self, net, path, start=None, end=None):
        cls, w, c = netclass(net)
        vk = "power" if cls == "Power" else "small"
        q = lambda v: round(v, 4)                  # compare rounded coordinates, or float noise makes zero-length stubs
        pts = [(l, q(i * G), q(j * G)) for (l, j, i) in path]
        start = (q(start[0]), q(start[1])) if start is not None else None
        end = (q(end[0]), q(end[1])) if end is not None else None
        runs, cur = [], [pts[0]]
        for p in pts[1:]:
            if p[0] != cur[-1][0]:
                runs.append(cur); cur = [p]
                self.add_via(net, (p[1], p[2]), vk)
            else:
                cur.append(p)
        runs.append(cur)
        if start is not None and (start[0], start[1]) != (runs[0][0][1], runs[0][0][2]):
            runs[0].insert(0, (runs[0][0][0], start[0], start[1]))
        if end is not None and (end[0], end[1]) != (runs[-1][-1][1], runs[-1][-1][2]):
            runs[-1].append((runs[-1][-1][0], end[0], end[1]))
        for run in runs:
            l = run[0][0]
            simp = [run[0]]
            for p in run[1:]:
                if (p[1], p[2]) == (simp[-1][1], simp[-1][2]):
                    continue
                if len(simp) >= 2:
                    (_, x0, y0), (_, x1, y1) = simp[-2], simp[-1]
                    cross = (x1 - x0) * (p[2] - y1) - (y1 - y0) * (p[1] - x1)
                    dot = (x1 - x0) * (p[1] - x1) + (y1 - y0) * (p[2] - y1)
                    if abs(cross) < 1e-6 and dot >= 0:
                        simp[-1] = p
                        continue
                simp.append(p)
            for a, b in zip(simp, simp[1:]):
                if (a[1], a[2]) != (b[1], b[2]):
                    self.add_track(net, (a[1], a[2]), (b[1], b[2]), w, l)

    def pad_srcs(self, pad):
        out = []
        for lname, g in pad["geo"].items():
            l = LAYERS.index(lname)
            cells = self._cells(g)
            if cells is None:
                continue
            j0, i0, m = cells
            for jj, ii in zip(*np.nonzero(m)):
                j, i = j0 + jj, i0 + ii
                out.append((l, j, i, 0.8 * math.hypot(i * G - pad["c"][0], j * G - pad["c"][1]) / G))
        return out

    def pad_mask(self, pad, m=None):
        m = m or [np.zeros((self.ny, self.nx), bool) for _ in range(2)]
        for lname, g in pad["geo"].items():
            cells = self._cells(g)
            if cells:
                j0, i0, mm = cells
                m[LAYERS.index(lname)][j0:j0 + mm.shape[0], i0:i0 + mm.shape[1]] |= mm
        return m

    # ------------------------------------------------------------ nets
    def route_net(self, net):
        pads = [p for p in self.pads if p["net"] == net]
        if len(pads) < 2:
            return 0
        nid = self.netid[net]
        # Prim order: grow from the first pad, always the nearest unconnected pad next
        done = [pads[0]]
        todo = pads[1:]
        tree = self.pad_mask(pads[0])
        fails = 0
        while todo:
            todo.sort(key=lambda p: min(math.dist(p["c"], q["c"]) for q in done))
            p = todo.pop(0)
            path = self.search(net, self.pad_srcs(p), tree)
            if path is None:
                fails += 1
                print(f"    unrouted: {net} {p['ref']}.{p['num']}", flush=True)
                continue
            end_pad = None
            l, j, i = path[-1]
            for q in done:
                g = q["geo"].get(LAYERS[l])
                if g is not None and g.contains(Point(i * G, j * G)):
                    end_pad = q
                    break
            nt, nv = len(self.tracks), len(self.vias)
            self.commit(net, path, start=p["c"], end=end_pad["c"] if end_pad else None)
            done.append(p)
            self.pad_mask(p, tree)
            # the tree grows only by what was just committed (not by other, still unconnected, pads of this net)
            for t in self.tracks[nt:]:
                g = LineString([t["a"], t["b"]]).buffer(t["w"] / 2, 8) if t["a"] != t["b"] else Point(t["a"]).buffer(t["w"] / 2)
                cells = self._cells(g)
                if cells:
                    j0, i0, mm = cells
                    tree[LAYERS.index(t["layer"])][j0:j0 + mm.shape[0], i0:i0 + mm.shape[1]] |= mm
            for v in self.vias[nv:]:
                cells = self._cells(Point(v["c"]).buffer(v["d"] / 2, 12))
                if cells:
                    j0, i0, mm = cells
                    for l2 in range(2):
                        tree[l2][j0:j0 + mm.shape[0], i0:i0 + mm.shape[1]] |= mm
        return fails

def order(r, nets):
    def span(n):
        c = [p["c"] for p in r.pads if p["net"] == n]
        xs, ys = [a for a, b in c], [b for a, b in c]
        return (max(xs) - min(xs)) + (max(ys) - min(ys)) if c else 0
    first = ["HOLD", "+5V", "VIN", "ESP_5V", "+3V3"]
    rest = sorted([n for n in nets if n not in first], key=lambda n: (netclass(n)[0] != "Motor", span(n)))
    return [n for n in first if n in nets] + rest

def gnd_pass(drc_file):
    """join GND pads that the pours didn't reach (per KiCad's DRC) to the nearest poured copper"""
    data = json.load(open(os.path.join(HERE, "pads.json")))
    routes = json.load(open(os.path.join(HERE, "routes.json")))
    zones = json.load(open(os.path.join(HERE, "zones.json")))
    drc = json.load(open(os.path.join(HERE, drc_file)))
    r = Router(data)
    for t in routes["tracks"]:
        r.add_track(t["net"], tuple(t["a"]), tuple(t["b"]), t["w"], LAYERS.index(t["layer"]))
    for v in routes["vias"]:
        r.add_via(v["net"], tuple(v["c"]), "power" if v["d"] >= 0.8 else "small")
    tgt = [np.zeros((r.ny, r.nx), bool) for _ in range(2)]
    for lname, polys in zones.items():
        for pts in polys:
            g = Polygon(pts).buffer(-0.15)
            if g.is_empty:
                continue
            cells = r._cells(g)
            if cells:
                j0, i0, m = cells
                tgt[LAYERS.index(lname)][j0:j0 + m.shape[0], i0:i0 + m.shape[1]] |= m
    want = set()
    for u in drc.get("unconnected_items", []):
        for it in u["items"]:
            d = it["description"]
            if "[GND]" in d and d.startswith("PTH pad"):
                num, ref = d.split()[2], d.split()[-1]
                want.add((ref, num))
    added = 0
    for ref, num in sorted(want):
        pad = next(p for p in r.pads if p["ref"] == ref and p["num"] == num)
        path = r.search("GND", r.pad_srcs(pad), tgt)
        if path is None:
            print("  GND unrouted:", ref, num)
            continue
        r.commit("GND", path, start=pad["c"])
        added += 1
    # stitching vias wherever both pours have room: ties every pour fragment to the other layer
    from shapely.ops import unary_union
    fills = {l: unary_union([Polygon(p).buffer(0) for p in polys]) for l, polys in zones.items()}
    both = fills["F.Cu"].intersection(fills["B.Cu"]).buffer(-0.75)
    have = [tuple(v["c"]) for v in r.vias if v["net"] == "GND"]
    freeV = ((r.owner[("V_small", 0)] == 0) | (r.owner[("V_small", 0)] == r.netid["GND"])) &             ((r.owner[("V_small", 1)] == 0) | (r.owner[("V_small", 1)] == r.netid["GND"])) & ~r.holemask(0.3)
    stitched = 0
    if "--stitch" in sys.argv and not both.is_empty:
        step = 24                                  # every ~6 mm
        for j in range(step // 2, r.ny, step):
            for i in range(step // 2, r.nx, step):
                x, y = i * G, j * G
                if not freeV[j, i] or not both.contains(Point(x, y)):
                    continue
                if any(math.dist((x, y), h) < 3.0 for h in have):
                    continue
                r.add_via("GND", (x, y), "small")
                have.append((x, y))
                freeV = ((r.owner[("V_small", 0)] == 0) | (r.owner[("V_small", 0)] == r.netid["GND"])) &                         ((r.owner[("V_small", 1)] == 0) | (r.owner[("V_small", 1)] == r.netid["GND"])) & ~r.holemask(0.3)
                stitched += 1
    # join pour fragments cut off from the main ground (a union-find over fragments, pads and vias)
    frag = [(l, Polygon(p).buffer(0)) for l in ("F.Cu", "B.Cu") for p in zones[l]]
    parent = list(range(len(frag)))
    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]; a = parent[a]
        return a
    def union(a, b):
        parent[find(a)] = find(b)
    links = [Point(v["c"]) for v in r.vias if v["net"] == "GND"] +             [Point(p["c"]) for p in r.pads if p["net"] == "GND" and len(p["geo"]) == 2]
    for pt in links:
        hit = [k for k, (l, g) in enumerate(frag) if g.distance(pt) < 0.05]
        for a_, b_ in zip(hit, hit[1:]):
            union(a_, b_)
    comps = {}
    for k in range(len(frag)):
        comps.setdefault(find(k), []).append(k)
    main = max(comps.values(), key=lambda ks: sum(frag[k][1].area for k in ks))
    joined = 0
    for root, ks in comps.items():
        if ks is main:
            continue
        done_ = False
        for k in ks:
            l, g = frag[k]
            other = "B.Cu" if l == "F.Cu" else "F.Cu"
            main_other = unary_union([frag[m][1] for m in main if frag[m][0] == other])
            spot = g.intersection(main_other).buffer(-0.45)
            if spot.is_empty:
                continue
            cells = r._cells(spot)
            if not cells:
                continue
            j0, i0, m = cells
            for jj, ii in zip(*np.nonzero(m)):
                j, i = j0 + jj, i0 + ii
                if freeV[j, i]:
                    r.add_via("GND", (i * G, j * G), "small"); joined += 1; done_ = True
                    break
            if done_:
                break
        if not done_:
            print("  fragment not joined:", [(frag[k][0], tuple(round(c, 1) for c in frag[k][1].centroid.coords[0]), round(frag[k][1].area, 1)) for k in ks])
    json.dump(dict(tracks=r.tracks, vias=r.vias, failed=routes.get("failed", [])), open(os.path.join(HERE, "routes.json"), "w"), indent=0)
    print(f"GND pass: joined {added} of {len(want)} pads, {stitched} stitching vias, {joined} fragment vias -> routes.json")

def main():
    data = json.load(open(os.path.join(HERE, "pads.json")))
    r = Router(data)
    nets = [n for n in r.nets if n != "GND" and sum(1 for p in r.pads if p["net"] == n) >= 2]
    seq = order(r, nets)
    best = None
    t0 = time.time()
    for attempt in range(6):
        r.reset()
        failed = []
        for n in seq:
            f = r.route_net(n)
            if f:
                failed.append((n, f))
        nfail = sum(f for _, f in failed)
        print(f"pass {attempt + 1}: {len(r.tracks)} tracks, {len(r.vias)} vias, {nfail} failed connections "
              f"{[n for n, _ in failed]}  ({time.time() - t0:.0f}s)", flush=True)
        if best is None or nfail < best[0]:
            best = (nfail, list(r.tracks), list(r.vias), failed)
        if nfail == 0:
            break
        # rip up and retry with the failures first, the rest lightly shuffled
        fn = [n for n, _ in failed]
        rest = [n for n in seq if n not in fn]
        random.seed(attempt)
        k = len(rest)
        rest = sorted(rest, key=lambda n: rest.index(n) + random.uniform(-k * 0.15, k * 0.15))
        seq = fn + rest
    nfail, tracks, vias, failed = best
    json.dump(dict(tracks=tracks, vias=vias, failed=failed), open(os.path.join(HERE, "routes.json"), "w"), indent=0)
    print(f"best: {nfail} failed; {len(tracks)} tracks, {len(vias)} vias -> routes.json")

if __name__ == "__main__":
    if "--gnd" in sys.argv:
        gnd_pass(sys.argv[sys.argv.index("--gnd") + 1])
    else:
        main()

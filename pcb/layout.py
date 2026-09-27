"""Place design.P on the board: world pad geometry, drills, courtyards, and placement checks."""
import math
from shapely.geometry import Point, box as sbox, Polygon
from shapely.ops import unary_union
from shapely import affinity
import design, fplib

GRID = 0.254          # router grid; through-hole anchors snap to it so DIP gaps line up with grid lines

def snap(v):
    return round(v / GRID) * GRID

class Inst:
    def __init__(self, ref, p):
        self.ref, self.p = ref, p
        self.fp = fplib.load(p["fp"])
        grid = "PinSocket" in p["fp"] or "PinHeader" in p["fp"]      # 2.54 mm pitch: put the pad gaps on grid lines
        self.x = snap(p["x"]) if grid else p["x"]
        self.y = snap(p["y"]) if grid else p["y"]
        self.rot = p["rot"]
        self.value = p["value"]

    def xf(self, g):
        return affinity.translate(fplib.rotate_ccw(g, self.rot), self.x, self.y)

    def pt(self, x, y):
        c, s = math.cos(math.radians(self.rot)), math.sin(math.radians(self.rot))
        return (self.x + x * c + y * s, self.y - x * s + y * c)

    def pads(self):
        """[(num, net, world_centre, {layer: polygon}, drill, pad)]"""
        out = []
        for pd in self.fp.pads:
            net = self.p["pads"].get(pd.num, "")
            shape = self.xf(pd.local_shape())
            layers = {l: shape for l in pd.copper_layers}
            out.append((pd.num, net, self.pt(pd.x, pd.y), layers, pd.drill, pd))
        return out

    def courtyard(self):
        c = self.fp.courtyard()
        return self.xf(c) if c is not None else None

class Board:
    def __init__(self):
        self.parts = {ref: Inst(ref, p) for ref, p in design.P.items()}
        self.outline = sbox(0, 0, design.BOARD_W, design.BOARD_H)
        self.pads = []                        # dicts
        for ref, inst in self.parts.items():
            for num, net, c, layers, drill, pd in inst.pads():
                self.pads.append(dict(ref=ref, num=num, net=net, c=c, layers=layers, drill=drill, kind=pd.kind, pad=pd, inst=inst))
        self.nets = sorted({p["net"] for p in self.pads if p["net"]})

    def check_placement(self):
        probs = []
        cy = {r: i.courtyard() for r, i in self.parts.items()}
        refs = sorted(cy)
        for i, a in enumerate(refs):
            if cy[a] is None:
                continue
            if not self.outline.buffer(0.01).contains(cy[a]) and a not in ("J3",):
                over = cy[a].difference(self.outline).area
                if over > 0.05:
                    probs.append(f"{a} courtyard off the board by {over:.1f} mm2")
            for b in refs[i + 1:]:
                if cy[b] is None:
                    continue
                ov = cy[a].intersection(cy[b]).area
                if ov > 0.05:
                    probs.append(f"{a} / {b} courtyards overlap {ov:.1f} mm2")
        # nothing but its own sockets inside the DevKit's outline
        dk = sbox(*design.DEVKIT)
        for r, c in cy.items():
            if c is not None and r not in ("J1", "J2") and c.intersection(dk).area > 0.05:
                probs.append(f"{r} is under the ESP32 DevKit ({c.intersection(dk).area:.1f} mm2)")
        # copper too close to the edge
        edge = self.outline.exterior
        for p in self.pads:
            for l, g in p["layers"].items():
                d = g.distance(edge) if self.outline.contains(g) else -1
                if d < 0.4:
                    probs.append(f"{p['ref']}.{p['num']} pad {d:.2f} mm from the board edge")
                break
        return probs

if __name__ == "__main__":
    b = Board()
    print(len(b.parts), "parts,", len(b.pads), "pads,", len(b.nets), "nets")
    for s in b.check_placement():
        print("  ", s)

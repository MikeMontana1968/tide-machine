"""Pairwise interference check of the whole Rev M model (station_study.py --full).

    python check_interference.py

Intersects every pair of solids whose boxes overlap (manifold3d booleans, the same test as an OpenSCAD
intersection()) and prints the pairs with real overlap. Intended contacts (a bearing on its axle, a magnet in
its pocket, a shaft in its bore) come out as touching faces: zero volume, not listed.
"""
import sys, io, contextlib
sys.argv = ["station_study.py", "--full"]
with contextlib.redirect_stdout(io.StringIO()):
    import station_study as ss

MIN_VOL = 0.05                     # mm^3: below this it's a touching face or numerical noise

def bbox(m):
    b = m.bounding_box()
    return b

def overlap(a, b):
    return all(a[i] < b[i + 3] and b[i] < a[i + 3] for i in range(3))

# expected pairs: parts that are meant to share volume (an axle through a bearing's bore is modelled solid)
EXPECT = [("V623ZZ", "axle"), ("axle", "bracket"), ("axle", "V623ZZ")]

def expected(n1, n2):
    s = (n1 + " | " + n2).lower()
    return any(a.lower() in s and b.lower() in s for a, b in EXPECT)

parts = [(p["name"], p["m"]) for p in ss.parts if not p["m"].is_empty()]
boxes = [bbox(m) for _, m in parts]
hits = []
for i in range(len(parts)):
    for j in range(i + 1, len(parts)):
        if not overlap(boxes[i], boxes[j]):
            continue
        v = (parts[i][1] ^ parts[j][1]).volume()
        if v > MIN_VOL:
            hits.append((v, parts[i][0], parts[j][0]))
hits.sort(reverse=True)
print(f"{len(parts)} solids, {len(hits)} overlapping pairs")
for v, a, b in hits:
    tag = "  (expected)" if expected(a, b) else ""
    print(f"  {v:9.2f} mm3  {a}  <->  {b}{tag}")

"""Export every printed part of the Rev M model as an STL, in its print orientation.

    python export_stl.py        ->  stl/*.stl  (+ stl/README.txt: what each is, how many, how to orient)

Geometry comes straight from station_study.py --full (and rollers.py for the pulley bracket), so the files
match the fit study and the assembly guide. Print orientation follows RESUME.md's printing table: every part
has one flat face on the bed and nothing steeper than 45 degrees above it (printcheck confirmed no supports).
"""
import os, sys, io, contextlib, struct
import numpy as np
sys.argv = ["station_study.py", "--full"]
with contextlib.redirect_stdout(io.StringIO()):
    import station_study as ss
import rollers
from manifold3d import Manifold

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "stl")

def write_stl(m, path):
    mesh = m.to_mesh()
    v = np.asarray(mesh.vert_properties)[:, :3]
    t = np.asarray(mesh.tri_verts)
    tri = v[t]
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    n /= np.linalg.norm(n, axis=1)[:, None] + 1e-12
    with open(path, "wb") as f:
        f.write(b"tide-machine rev M".ljust(80, b" "))
        f.write(struct.pack("<I", len(t)))
        rec = np.zeros(len(t), dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
        rec["n"] = n
        rec["v"] = tri
        f.write(rec.tobytes())

def on_bed(m):
    """centre in x/y, lowest point at z 0"""
    b = m.bounding_box()
    return m.translate([-(b[0] + b[3]) / 2, -(b[1] + b[4]) / 2, -b[2]])

def back_down(m):
    """machine +z (toward the plate) on the bed: a proper 180 degree turn about x, never a mirror"""
    return on_bed(m.rotate([180, 0, 0]))

def front_down(m):
    """machine -z (the viewer's side) on the bed: machine z already points up from it"""
    return on_bed(m)

def axis_y_down(m):
    """a part whose axis runs along machine y (the drum cap): stand the axis vertical"""
    return on_bed(m.rotate([90, 0, 0]))

parts = {p["name"]: p["m"] for p in ss.parts}
def one(name):
    return parts[name]

JOBS = []   # (file, manifold, qty, orientation note)
JOBS.append(("hub_dial.stl", back_down(one("M2 hub + dial")), 5, "dial back down, boss up"))
for name, x, r in ss.ALL_STATIONS:
    key = [k for k in parts if k.startswith(f"{name} arm (r")][0]
    JOBS.append((f"arm_{name}.stl", back_down(parts[key]), 1, f"back down, bearing boss up (pin radius {r:g} mm)"))
JOBS.append(("index_tab.stl", back_down(one("M2 index tab (PLA)")), 5, "flat"))
brk, _ = rollers.build_bracket(rollers.LINE_Z)
JOBS.append(("pulley_bracket.stl", on_bed(brk), 6, "rail face down, as modelled"))
JOBS.append(("pen_carriage_rear.stl", front_down(one("Pen carriage rear plate (PLA)")), 1, "front face down, pulley stub up"))
JOBS.append(("pen_carriage_front.stl", front_down(one("Pen carriage front body (PLA)")), 1, "front face down, pockets open upward"))
JOBS.append(("year_dial.stl", front_down(one("Year dial + hub adapter (outer shaft)")), 1,
             "decal face down. Hub bore is a PLACEHOLDER until the BKA30D-R5's shafts are measured"))
JOBS.append(("moon_disc.stl", front_down(one("Moon disc + hub (inner shaft)")), 1,
             "decal face down. Hub bore is a PLACEHOLDER until the BKA30D-R5's shafts are measured"))
JOBS.append(("calendar_hand.stl", front_down(one("Calendar index hand (PLA)")), 1, "front face down"))
cap = [p["m"] for p in ss.parts if p["name"] == "Drum end cap (printed)"][0]
b = cap.bounding_box()
bore = Manifold.cylinder(b[4] - b[1] + 2, 3.55, 3.55, 48).rotate([-90, 0, 0]).translate(
    [(b[0] + b[3]) / 2, b[1] - 1, (b[2] + b[5]) / 2])
JOBS.append(("drum_end_cap.stl", axis_y_down(cap - bore), 2,
             "flat. 7.1 mm bore added for the 7 mm shaft; how it grips the shaft is not designed yet"))

os.makedirs(OUT, exist_ok=True)
lines = ["Tide Machine rev M: printed parts (from station_study.py --full; regenerate with export_stl.py)", "",
         "PLA, 3 perimeters, no supports. Print the coupons first (RESUME.md, Printing).", ""]
for fn, m, q, note in JOBS:
    write_stl(m, os.path.join(OUT, fn))
    bb = m.bounding_box()
    lines.append(f"{fn:26s} x{q}   {bb[3] - bb[0]:6.1f} x {bb[4] - bb[1]:6.1f} x {bb[5] - bb[2]:5.1f} mm   {note}")
    print(lines[-1])
open(os.path.join(OUT, "README.txt"), "w", encoding="utf8").write("\n".join(lines) + "\n")

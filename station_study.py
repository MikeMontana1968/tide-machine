"""Rev M station study -- two neighbouring stations (O1 and M2, the tightest
pair at the 56 mm pitch) with everything that has to clear everything else:
faceplate, 28BYJ-48 at its true 8 mm shaft offset, Vishay TCST2202 home
sensor at 12 o'clock, two-part rotor (hub + flag disc, bolt-on arm with its
V623ZZ on an M3 axle), coaxial pulley pairs on the top rail
(mirrored threading), rails.

Writes station_study.html (the interactive viewer) and prints the clearances.
Writes NO STL files -- this is a fit study, not a print release.

Machine frame, as in tide_machine.rb: x along the row, y up (crank centreline
y = 0), z toward the viewer is NEGATIVE; the faceplate's front face is z = 0.
"""
import json, math, os
import numpy as np
from manifold3d import Manifold, CrossSection
import rollers

# ------------------------------------------------------------------ inputs --
PITCH      = 56.0
STATIONS   = [("O1", -PITCH, 2.45), ("M2", 0.0, 35.00)]   # (name, shaft x, pin radius)

PLATE_T    = 1.5
BOSS_HOLE  = 9.2      # locates the Ø9 boss; the plate, not the ear bolts, positions the shaft

# 28BYJ-48 (Kiatronics / OSEPP STEPD-01 datasheet)
MOT_D, MOT_L   = 28.0, 19.0
MOT_OFF        = 8.0      # shaft sits this far ABOVE the body centre (wire cover down)
EAR_PITCH      = 35.0
EAR_R, EAR_T   = 3.5, 0.8
EAR_HOLE       = 4.2
COVER_W        = 14.6
COVER_REACH    = 17.0     # past the body centre, on the side away from the shaft
BOSS_D, BOSS_H = 9.0, 1.5
SHAFT_D, SHAFT_LEN, FLATS, FLAT_LEN = 5.0, 10.0, 3.0, 6.0

# Vishay TCST2202 (doc 81147)
S_LEN, S_W, S_H = 24.5, 6.3, 10.8
S_BLOCK_L, S_BLOCK_W = 11.9, 6.0
S_FLANGE_T     = 3.1
S_HOLE_PITCH, S_HOLE_D = 19.0, 3.3
S_GAP          = 3.1
S_AXIS         = 8.2      # beam height above the seating plane (10.8 - 2.6)
S_SLOT_FLOOR   = 3.6      # slot bottom above the seating plane (not dimensioned; generous)
S_LEAD_X, S_LEAD_Y, S_LEAD_L = 2.54, 7.6, 7.8

PAD_T      = 1.5          # printed insulating pad between sensor and aluminium
SENSOR_ANG = 90.0         # 12 o'clock: clear of the motor behind the plate

# rotor stack
HUB_R      = 7.0
GAP_DISC   = 1.0          # sensor top to the flag disc
DISC_T     = 2.0
FIN_T      = 1.2          # radial thickness of the flag fin
FIN_ARC    = 20.0         # degrees
FIN_PAST   = 1.7          # fin tip reaches this far past the beam
ARM_GAP    = 1.0          # arm stands proud of its disc on a boss, so M2's arm clears O1's disc
ARM_T      = 3.0
ARM_END_R  = 5.5
# arm bearing: the same V623ZZ as the rail pulleys, on an M3x8 into a heat-set insert
BOSS_STEP_D, BOSS_STEP_H = 8.0, 1.0      # stepped boss in front of the arm: Ø8 ...
BOSS_RACE_H = 0.5                        # ... then Ø5 (rollers.BRG_RACE_D) on the inner race only
INSERT_D, INSERT_L = 4.0, 4.0            # M3 x 4 heat-set insert, pressed in from the arm's back face (check the maker's hole size)
AXLE_L     = 8.0                         # M3x8 button head + 0.5 washer

# -------------------------------------------------------------- derived z --
z_pad_front   = -PAD_T
z_sensor_top  = z_pad_front - S_H
z_beam        = z_pad_front - S_AXIS
z_slot_floor  = z_pad_front - S_SLOT_FLOOR
z_disc_back   = z_sensor_top - GAP_DISC
z_disc_front  = z_disc_back - DISC_T
z_arm_back    = z_disc_front - ARM_GAP
z_arm_front   = z_arm_back - ARM_T
z_brg_back    = z_arm_front - BOSS_STEP_H - BOSS_RACE_H
z_brg_front   = z_brg_back - rollers.BRG_W
z_line        = (z_brg_back + z_brg_front) / 2
z_axle_tip    = z_brg_front - 0.5 + AXLE_L          # washer 0.5; tip lands inside the insert
z_fin_tip     = z_beam + FIN_PAST
z_shaft_tip   = -(SHAFT_LEN - BOSS_H)          # boss buried in the plate
R_FIN         = HUB_R + 1.25 + S_LEN / 2       # sensor's inner flange clears the hub by 1.25
R_DISC        = R_FIN + FIN_T / 2 + 1.5

assert abs(z_line - rollers.LINE_Z) < 1e-6, f"rollers.py LINE_Z should be {z_line:.2f}"

# ----------------------------------------------------------------- helpers --
def box(x0, x1, y0, y1, z0, z1):
    x0, x1 = sorted((x0, x1)); y0, y1 = sorted((y0, y1)); z0, z1 = sorted((z0, z1))
    return Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])

def zcyl(x, y, r, z0, z1, n=48):
    z0, z1 = sorted((z0, z1))
    return Manifold.cylinder(z1 - z0, r, r, n).translate([x, y, z0])

def zprism(cs, z0, z1):
    z0, z1 = sorted((z0, z1))
    return cs.extrude(z1 - z0).translate([0, 0, z0])

def circ(x, y, r, n=48):
    return CrossSection.circle(r, n).translate([x, y])

def revolve_z(profile, x, y, n=64):
    """profile [(radius, z), ...] revolved about a z-parallel axis at (x, y)"""
    cs = CrossSection([[(r, z) for r, z in profile]])
    m = cs.revolve(n)                         # about Y, profile in XY
    return m.rotate([90, 0, 0]).translate([x, y, 0])     # +90 about X maps profile y -> z

def annular_sector(r0, r1, a0, a1, n=24):
    pts = [(r1 * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
            r1 * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]
    pts += [(r0 * math.cos(math.radians(a1 - (a1 - a0) * i / n)),
             r0 * math.sin(math.radians(a1 - (a1 - a0) * i / n))) for i in range(n + 1)]
    return CrossSection([pts])

def polar(r, deg):
    return r * math.cos(math.radians(deg)), r * math.sin(math.radians(deg))

# --------------------------------------------------------------- the parts --
parts = []
def add(name, m, color, group, rotor=-1, opacity=1.0):
    parts.append(dict(name=name, m=m, color=color, group=group, rotor=rotor, opacity=opacity))

X0, X1 = -PITCH - 44, 44          # section of the machine shown

# faceplate, with every hole this study knows about
plate = box(X0, X1, -82, 82, 0, PLATE_T)
for _, xs, _ in STATIONS:
    plate -= zcyl(xs, 0, BOSS_HOLE / 2, -1, 3)
    for sx in (-1, 1):
        plate -= zcyl(xs + sx * EAR_PITCH / 2, -MOT_OFF, 1.6, -1, 3, 24)   # M3 clearance
    cx, cy = polar(R_FIN, SENSOR_ANG)
    for d in (-S_HOLE_PITCH / 2, S_HOLE_PITCH / 2):
        plate -= zcyl(xs + cx, cy + d, 1.6, -1, 3, 24)
    plate -= box(xs + cx - 3.0, xs + cx + 3.0, cy - 6.0, cy + 6.0, -1, 3)  # lead window
add("Faceplate, 1.5 aluminium", plate, "#B9C3CB", "plate", opacity=0.92)

# rails: 1x2 pine, top and bottom
for sy in (1, -1):
    add("Rail, 1x2 pine", box(X0 - 6, X1 + 6, sy * 70, sy * (70 + 19.05), 0, -38.1),
        "#D8B98A", "rails", opacity=0.35)

for si, (nm, xs, r) in enumerate(STATIONS):
    # ---- motor, behind the plate -------------------------------------------
    by = -MOT_OFF
    body = zcyl(xs, by, MOT_D / 2, PLATE_T, PLATE_T + MOT_L, 64)
    ears = zprism(CrossSection.hull(circ(xs - EAR_PITCH / 2, by, EAR_R) + circ(xs + EAR_PITCH / 2, by, EAR_R)),
                  PLATE_T, PLATE_T + EAR_T)
    for sx in (-1, 1):
        ears -= zcyl(xs + sx * EAR_PITCH / 2, by, EAR_HOLE / 2, 0, 5, 24)
    add(f"{nm} 28BYJ-48", body + ears + zcyl(xs, 0, BOSS_D / 2, 0, PLATE_T), "#8C969E", "motors")
    add(f"{nm} wire cover", box(xs - COVER_W / 2, xs + COVER_W / 2, by - COVER_REACH, by - 9,
                                PLATE_T + 1, PLATE_T + MOT_L - 2), "#2F7FC1", "motors")
    shaft = zcyl(xs, 0, SHAFT_D / 2, 0, z_shaft_tip + FLAT_LEN, 32) + \
            (zcyl(xs, 0, SHAFT_D / 2, z_shaft_tip + FLAT_LEN, z_shaft_tip, 32) ^
             box(xs - 3, xs + 3, -FLATS / 2, FLATS / 2, z_shaft_tip, z_shaft_tip + FLAT_LEN))
    add(f"{nm} shaft", shaft, "#C9CFD4", "motors", rotor=si)

    # ---- home sensor: pad + TCST2202 ------------------------------------------
    cx, cy = polar(R_FIN, SENSOR_ANG); cx += xs
    hy = (cy - S_HOLE_PITCH / 2, cy + S_HOLE_PITCH / 2)
    pad = box(cx - 4.25, cx + 4.25, cy - S_LEN / 2 - 0.75, cy + S_LEN / 2 + 0.75, 0, z_pad_front)
    for h in hy: pad -= zcyl(cx, h, 1.6, 1, -3, 24)
    pad -= box(cx - 2.2, cx + 2.2, cy - 5.0, cy + 5.0, 1, -3)
    add(f"{nm} sensor pad (PLA)", pad, "#3B4650", "sensor")

    fl = zprism(CrossSection.hull(circ(cx, hy[0], S_W / 2) + circ(cx, hy[1], S_W / 2)),
                z_pad_front, z_pad_front - S_FLANGE_T)
    for h in hy: fl -= zcyl(cx, h, S_HOLE_D / 2, 0, -6, 24)
    blk = box(cx - S_BLOCK_W / 2, cx + S_BLOCK_W / 2, cy - S_BLOCK_L / 2, cy + S_BLOCK_L / 2,
              z_pad_front, z_sensor_top)
    blk -= box(cx - 4, cx + 4, cy - S_GAP / 2, cy + S_GAP / 2, z_slot_floor, z_sensor_top - 1)
    add(f"{nm} TCST2202", fl + blk, "#16191C", "sensor")
    leads = None
    for lx in (-S_LEAD_X / 2, S_LEAD_X / 2):
        for ly in (-S_LEAD_Y / 2, S_LEAD_Y / 2):
            l = box(cx + lx - 0.225, cx + lx + 0.225, cy + ly - 0.2, cy + ly + 0.2,
                    z_pad_front, z_pad_front + S_LEAD_L)
            leads = l if leads is None else leads + l
    add(f"{nm} TCST2202 leads", leads, "#D9C27A", "sensor")
    add(f"{nm} beam", box(cx - 0.12, cx + 0.12, cy - S_GAP / 2, cy + S_GAP / 2, z_beam - 0.12, z_beam + 0.12),
        "#E0443A", "sensor")

    # ---- rotor part 1: hub + flag disc + fin (prints disc-down, fin up) ----
    hub = zcyl(xs, 0, HUB_R, -0.5, z_disc_back, 48) + zcyl(xs, 0, R_DISC, z_disc_back, z_disc_front, 96) + \
          zcyl(xs, 0, HUB_R + 5.0, z_disc_front, z_arm_back, 48)      # boss the arm bolts to
    fin = zprism(annular_sector(R_FIN - FIN_T / 2, R_FIN + FIN_T / 2, 180 - FIN_ARC / 2, 180 + FIN_ARC / 2)
                 .translate([xs, 0]), z_disc_back, z_fin_tip)
    dbore = (circ(xs, 0, SHAFT_D / 2 + 0.1, 32) ^
             CrossSection.square([6, FLATS + 0.1], center=True).translate([xs, 0]))
    hub -= zprism(dbore, 1, z_shaft_tip - 0.3)
    hub -= Manifold.cylinder(HUB_R + 1, 1.25, 1.25, 16).rotate([90, 0, 0]).translate([xs, HUB_R + 0.5, z_shaft_tip + FLAT_LEN / 2])
    for a in (60, 300):                       # two M2 screws take the arm; keyed by their spacing
        px, py = polar(HUB_R + 3.0, a)
        hub -= zcyl(xs + px, py, 0.8, z_disc_back + 0.5, z_arm_back - 1, 16)
    add(f"{nm} hub + flag disc", hub + fin, "#E7E1D6", "rotor", rotor=si)

    # ---- rotor part 2: arm + stepped boss (prints flat, boss up) -------------
    arm = zprism(CrossSection.hull(circ(xs, 0, HUB_R + 5.0) + circ(xs + r, 0, ARM_END_R)), z_arm_back, z_arm_front)
    arm += zcyl(xs + r, 0, BOSS_STEP_D / 2, z_arm_front, z_arm_front - BOSS_STEP_H, 48)
    arm += zcyl(xs + r, 0, rollers.BRG_RACE_D / 2, z_arm_front - BOSS_STEP_H, z_brg_back, 48)
    for a in (60, 300):
        px, py = polar(HUB_R + 3.0, a)
        arm -= zcyl(xs + px, py, 1.1, z_arm_back + 1, z_arm_front - 1, 16)
    arm -= zcyl(xs + r, 0, INSERT_D / 2, z_arm_back + 1, z_arm_back - INSERT_L, 32)      # insert, from the back
    arm -= zcyl(xs + r, 0, 1.6, z_arm_back - INSERT_L + 0.01, z_brg_back - 1, 24)        # M3 clearance through the race ring
    add(f"{nm} arm (r {r:.2f})", arm, "#C98B3B" if nm == "M2" else "#8D6BBF", "rotor", rotor=si)
    add(f"{nm} M3x4 heat-set insert", zcyl(xs + r, 0, 2.3, z_arm_back, z_arm_back - INSERT_L, 24) -
        zcyl(xs + r, 0, 1.5, z_arm_back + 1, z_arm_back - INSERT_L - 1, 16), "#C9A34E", "rotor", rotor=si)

    # ---- arm bearing: V623ZZ, inner race clamped, outer race carries the line --
    vp = [(1.5, z_brg_back), (6.0, z_brg_back), (6.0, z_line + 0.9), (rollers.BRG_ROOT_R, z_line),
          (6.0, z_line - 0.9), (6.0, z_brg_front), (1.5, z_brg_front)]
    add(f"{nm} arm V623ZZ", revolve_z(vp, xs + r, 0), "#AEB7BE", "rotor", rotor=si)
    add(f"{nm} M3x8 axle + washer", zcyl(xs + r, 0, 1.5, z_axle_tip, z_brg_front - 0.5, 16) +
        zcyl(xs + r, 0, 3.5, z_brg_front, z_brg_front - 0.5, 24) +
        zcyl(xs + r, 0, 2.85, z_brg_front - 0.5, z_brg_front - 2.15, 24), "#6F7880", "rotor", rotor=si)

    # ---- pulley bracket: two V623ZZ on one axle, directly above the shaft ------
    brk, info = rollers.build_bracket(z_line)
    add(f"{nm} pulley bracket", rollers.to_machine(brk).translate([xs, 0, 0]), "#5E7F97", "rollers")
    zin, zout = rollers.threading(nm, z_line)
    byy = info["axle_y"]
    for zc, role in ((zin, "in"), (zout, "out")):
        side = "front" if zc < z_line else "rear"
        vp = [(1.5, zc + 2), (6.0, zc + 2), (6.0, zc + 1.1), (rollers.BRG_ROOT_R, zc),
              (6.0, zc - 1.1), (6.0, zc - 2), (1.5, zc - 2)]
        add(f"{nm} V623ZZ, {side} ({role})", revolve_z(vp, xs, byy), "#AEB7BE", "rollers")
    add(f"{nm} 3x5x0.5 shim", zcyl(xs, byy, 2.5, z_line - rollers.SHIM / 2, z_line + rollers.SHIM / 2, 24), "#C9A34E", "rollers")
    add(f"{nm} M3x20 axle + nyloc", zcyl(xs, byy, 1.5, info["z_rear"] + 4.0, info["z_front"] - 1.7, 16) +
        zcyl(xs, byy, 2.75, info["z_front"], info["z_front"] - 1.7, 24) +
        zcyl(xs, byy, 3.1, info["z_rear"], info["z_rear"] + 4.0, 6), "#6F7880", "rollers")

# ------------------------------------------------------------- clearances --
o1, m2 = STATIONS
arm_reach_m2 = m2[2] + ARM_END_R
brg_reach_m2 = m2[2] + rollers.BRG_OD / 2
clear = [
    ("Flag disc to sensor top",               GAP_DISC),
    ("Fin tip past the beam",                 FIN_PAST),
    ("Fin tip to slot floor",                 z_slot_floor - z_fin_tip),
    ("Fin to each slot wall",                 (S_GAP - FIN_T) / 2),
    ("Hub to sensor inner flange",            R_FIN - S_LEN / 2 - HUB_R),
    ("Sensor leads to motor body (behind plate)", R_FIN - S_LEAD_Y / 2 - (MOT_D / 2 - MOT_OFF)),
    ("M2 arm over O1 flag disc (z gap)",      ARM_GAP),
    ("M2 arm to O1 boss (same plane)",         PITCH - arm_reach_m2 - (HUB_R + 5.0)),
    ("M2 arm bearing to O1 arm bearing",      PITCH - brg_reach_m2 - (o1[2] + rollers.BRG_OD / 2)),
    ("Flag discs, neighbour to neighbour",    PITCH - 2 * R_DISC),
    ("M2 arm bearing to rail pulleys (top)",  rollers.AXLE_Y - rollers.BRG_OD / 2 - brg_reach_m2),
    ("Axle tip short of the arm's back face", z_arm_back - z_axle_tip),
    ("Line legs in front of the arm face",    z_arm_front - rollers.planes(z_line)[1]),
    ("Line legs to neighbour's arm bearing",  PITCH - (o1[2] + rollers.BRG_ROOT_R) - brg_reach_m2),
    ("Pulley brackets, neighbour to neighbour", PITCH - 2 * rollers.HALF_X),
]
stack = [
    ("Faceplate front face", 0.0), ("Sensor seat (pad front)", z_pad_front), ("Slot floor", z_slot_floor),
    ("Fin tip", z_fin_tip), ("Beam", z_beam), ("Shaft tip", z_shaft_tip), ("Sensor top", z_sensor_top),
    ("Flag disc back", z_disc_back), ("Flag disc front", z_disc_front), ("Arm back", z_arm_back), ("Arm front", z_arm_front),
    ("Rear pulley plane", rollers.planes(z_line)[1]), ("Arm bearing groove", z_line),
    ("Front pulley plane", rollers.planes(z_line)[0]), ("Arm bearing front", z_brg_front), ("Axle head", z_brg_front - 2.15),
]

print(f"fin radius {R_FIN:.2f}, flag disc radius {R_DISC:.2f}, line plane z {z_line:.2f}")
for k, v in clear: print(f"  {k:44s} {v:6.2f} mm")
bad = [k for k, v in clear if v < 0.5]
print("  ALL CLEAR" if not bad else f"  INTERFERENCE: {bad}")

# ---------------------------------------------------------------- export --
out = []
for p in parts:
    mesh = p["m"].to_mesh()
    v = np.asarray(mesh.vert_properties)[:, :3].copy()
    t = np.asarray(mesh.tri_verts).astype(int)
    v[:, 2] *= -1                 # machine z (front negative) -> three z (front positive)
    t = t[:, ::-1]                # the mirror flips winding back
    out.append(dict(name=p["name"], color=p["color"], group=p["group"], rotor=p["rotor"],
                    opacity=p["opacity"], v=np.round(v, 2).ravel().tolist(), t=t.ravel().tolist()))
def fleet(r):
    # worst leg fleet angle: plane offset over the shortest leg (pulley tangent to arm-bearing tangent)
    best = 1e9
    for th in np.linspace(0, 2 * math.pi, 721):
        px, py = r * math.cos(th), r * math.sin(th)
        for ex, sg in ((-rollers.BRG_ROOT_R, 1), (rollers.BRG_ROOT_R, -1)):
            dx, dy = ex - px, rollers.AXLE_Y - py
            d, al = math.hypot(dx, dy), math.atan2(dy, dx)
            phi = al + sg * math.acos(rollers.BRG_ROOT_R / d)
            best = min(best, math.hypot(ex - px - rollers.BRG_ROOT_R * math.cos(phi), rollers.AXLE_Y - py - rollers.BRG_ROOT_R * math.sin(phi)))
    return math.degrees(math.atan(rollers.PLANE_DZ / best))

sts = []
for n, x, r in STATIONS:
    zi, zo = rollers.threading(n, z_line)
    sts.append(dict(name=n, x=x, r=r, zIn=-zi, zOut=-zo, fleet=round(fleet(r), 1),
                    order=("front" if zi < z_line else "rear") + " in, " + ("front" if zo < z_line else "rear") + " out"))
    print(f"  {n}: {sts[-1]['order']}, worst leg fleet angle {sts[-1]['fleet']} deg")
data = dict(parts=out, stations=sts,
            line=dict(z=-z_line, y=rollers.LINE_Y, rollerR=rollers.BRG_ROOT_R, rollerY=rollers.AXLE_Y,
                      sleeveR=rollers.BRG_ROOT_R, x0=X0, x1=X1),
            clear=[[k, round(v, 2)] for k, v in clear], stack=[[k, round(v, 2)] for k, v in stack],
            fin=dict(r=round(R_FIN, 2), disc=round(R_DISC, 2)))
tmpl = open("station_study.tmpl.html", encoding="utf8").read()
open("station_study.html", "w", encoding="utf8").write(tmpl.replace("/*DATA*/null", json.dumps(data, separators=(",", ":"))))
print(f"station_study.html  ({os.path.getsize('station_study.html')/1024:.0f} KB, {len(out)} parts)")

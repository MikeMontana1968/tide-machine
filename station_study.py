"""Rev M fit study -- Hall sensing, shrunk depth stack.

    python station_study.py          ->  station_study.html  (O1 + M2, the tightest pair)
    python station_study.py --full   ->  revm_model.html     (whole machine: five stations, calendar dial,
                                                              pen carriage, drum, frame)

Everything that has to clear everything else: faceplate (1.5 aluminium -- never steel, the
Hall sensors look through it), 28BYJ-48 at its true 8 mm shaft offset, a DRV5013-class Hall
latch on a thumbnail PCB behind the plate with its chip nested in a window, a pair of 5x2 N52
magnets (opposite poles) in the back of each dial, two-part rotor (hub + Ø52 dial, bolt-on arm
carrying a V623ZZ), coaxial pulley pairs on the top rail with mirrored threading, the four-bearing
pen carriage in front of the line, and the BKA30D-R5 calendar (year dial + moon disc, concentric).

Prints the clearances. Writes NO STL files -- this is a fit study, not a print release.
The BKA30D-R5 body, shaft positions and hub adapters are PLACEHOLDERS until a motor is measured.

Machine frame, as in tide_machine.rb: x along the row, y up (crank centreline y = 0), z toward
the viewer is NEGATIVE; the faceplate's front face is z = 0.
"""
import json, math, os, sys
import numpy as np
from manifold3d import Manifold, CrossSection
import rollers

# ------------------------------------------------------------------ inputs --
FULL       = "--full" in sys.argv
PITCH      = 56.0
ALL_STATIONS = [("S2", -4 * PITCH, 8.75), ("N2", -3 * PITCH, 7.35), ("K1", -2 * PITCH, 3.50),
                ("O1", -PITCH, 2.45), ("M2", 0.0, 35.00)]          # (name, shaft x, pin radius)
STATIONS   = ALL_STATIONS if FULL else ALL_STATIONS[3:]
SIGMA      = {"M2": 28.9841042, "S2": 30.0, "N2": 28.4397295, "K1": 15.0410686, "O1": 13.9430356}
START_ANG  = {"S2": 150, "N2": 300, "K1": 80, "O1": 40, "M2": 250}   # arbitrary starting angles for the viewer

PLATE_T    = 1.5
RAIL_Y     = rollers.RAIL_Y          # 76: rails 152 apart
RAIL_T     = 19.05
SOCKET     = 9.0
BOSS_HOLE  = 9.2                     # locates the Ø9 boss; the plate, not the ear bolts, positions the shaft

# 28BYJ-48 (Kiatronics / OSEPP STEPD-01 datasheet)
MOT_D, MOT_L   = 28.0, 19.0
MOT_OFF        = 8.0                 # shaft sits this far ABOVE the body centre (wire cover down)
EAR_PITCH      = 35.0
EAR_R, EAR_T   = 3.5, 0.8
EAR_HOLE       = 4.2
EAR_HEAD       = 2.4                 # M3 pan head (or nut) standing proud of the plate's front face
COVER_W        = 14.6
COVER_REACH    = 17.0
BOSS_D, BOSS_H = 9.0, 1.5
SHAFT_D, SHAFT_LEN, FLATS, FLAT_LEN = 5.0, 10.0, 3.0, 6.0

# Hall sensing: DRV5013-class latch, SOT-23, on a thumbnail PCB behind the plate
HALL_R     = 20.5                    # sensor radius, at 12 o'clock under each dial
HALL_WIN   = 3.4                     # square window in the plate; the chip nests in it
SOT_L, SOT_W, SOT_H = 2.9, 1.6, 1.1
HALL_PCB   = (10.0, 16.0, 1.6)       # w, h, t
HALL_DEPTH = 0.5                     # sensing element below the chip's top face
MAG_D, MAG_T = 5.0, 2.0              # N52 discs, a pair, opposite poles toward the sensor
MAG_SEP    = MAG_D + 0.5             # centre to centre, along the direction of travel

# rotor stack (shrunk: nothing tall in front of the plate any more)
HUB_R      = 7.0
DISC_GAP   = 1.1                     # dial back to the ear-bolt heads
DISC_T     = 2.5                     # houses the 2 mm magnets with a 0.5 mm skin in front
ARM_GAP    = 2.5                     # boss: M2's arm clears O1's dial, and the shaft tip ends flush with the arm's back
ARM_T      = 3.0
ARM_END_R  = 5.5
BOSS_STEP_D, BOSS_STEP_H = 8.0, 1.0  # stepped boss in front of the arm: Ø8 ...
BOSS_RACE_H = 0.5                    # ... then Ø5 on the bearing's inner race only
INSERT_D, INSERT_L = 4.0, 4.0        # M3 x 4 heat-set insert, from the arm's back face
AXLE_L     = 8.0                     # M3x8 button head + 0.5 washer
R_DISC     = 26.0                    # Ø52 dial, carries the decal (decals.py)
NOTCH      = 1.2                     # V-notch in the dial rim at the pin direction: the decal's coral tick sits over it
TAB_R0, TAB_R1, TAB_T = R_DISC + 1.0, R_DISC + 7.0, 4.5   # index tab at 12 o'clock, just outside the rim

# pen carriage: four V623ZZ on two 3 mm steel rods, IN FRONT of the line
PEN_X      = 70.0
PEN_ROD_D  = 3.0
V_HALF     = 45.0                    # half-angle of the bearing's V (90 deg assumed -- MEASURE)
PEN_BX     = 12.0
PEN_S      = 14.0
PEN_POCKET = rollers.BRG_W / 2 + 0.5
PEN_ROD_C  = rollers.BRG_ROOT_R + (PEN_ROD_D / 2) / math.sin(math.radians(V_HALF))
PEN_ROD_DX = PEN_BX + PEN_ROD_C
PEN_BODY_X = PEN_BX + 4.0
PEN_GAP_X  = PEN_BX - 5.0
PEN_ARM    = 25.0
DRUM_R, DRUM_BORE, DRUM_L, DRUM_Z = 44.45, 38.95, 130.0, -24.0   # drum axis on the carriage's mid-plane
DRUM_X     = PEN_X + PEN_BODY_X + PEN_ARM + DRUM_R

# calendar: BKA30D-R5 dual-concentric gauge stepper; year dial (outer shaft) + moon disc (inner shaft)
CAL_X, CAL_Y = -3.5 * PITCH, -48.0   # below and between N2 and K1
BKA_L, BKA_W, BKA_T = 59.5, 31.5, 8.9                 # housing, long axis vertical -- PLACEHOLDER shaft at centre
CAL_PCB    = (36.0, 68.0, 1.6)
MOON_R, MOON_T, MOON_GAP = 16.0, 2.5, 1.0             # Ø32 moon disc, 1 mm in front of the year dial
MOON_HALL_R = 9.0                                     # moon magnets and its sensor at 6 o'clock, r 9
YEAR_H     = 365.2422 * 24.0
SYNODIC_H  = 29.530589 * 24.0

PLATE_X    = (-4 * PITCH - 29.0, 30.0)
RAIL_X     = (-4 * PITCH - 38.0, DRUM_X + DRUM_R + 25.0)

# -------------------------------------------------------------- derived z --
z_disc_back   = -(EAR_HEAD + DISC_GAP)
z_disc_front  = z_disc_back - DISC_T
z_arm_back    = z_disc_front - ARM_GAP
z_arm_front   = z_arm_back - ARM_T
z_brg_back    = z_arm_front - BOSS_STEP_H - BOSS_RACE_H
z_brg_front   = z_brg_back - rollers.BRG_W
z_line        = (z_brg_back + z_brg_front) / 2
z_axle_tip    = z_brg_front - 0.5 + AXLE_L
z_shaft_tip   = -(SHAFT_LEN - BOSS_H)
z_chip_top    = PLATE_T - SOT_H                          # chip sits on the PCB's front face, nested in the window
z_hall        = z_chip_top + HALL_DEPTH
z_moon_back   = z_disc_front - MOON_GAP
z_moon_front  = z_moon_back - MOON_T
z_hand        = (z_moon_front - 1.0, z_moon_front - 2.5)  # calendar index hand, 1.5 thick, in front of the moon disc
PLANE_REAR, PLANE_FRONT = rollers.planes(z_line)[1], rollers.planes(z_line)[0]
PEN_ZR     = PLANE_FRONT - 1.5                            # carriage body clears the front-plane leg
PEN_BZ     = PEN_ZR - 2.5 - PEN_POCKET                    # bearings/rods: 2.5 rear plate, then the pocket
PEN_ZF     = PEN_BZ - PEN_POCKET - 4.0

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
    cs = CrossSection([[(r, z) for r, z in profile]])
    return cs.revolve(n).rotate([90, 0, 0]).translate([x, y, 0])

def polar(r, deg):
    return r * math.cos(math.radians(deg)), r * math.sin(math.radians(deg))

def v623(x, y, zc):
    """a V623ZZ centred on plane zc"""
    return revolve_z([(1.5, zc + 2), (6.0, zc + 2), (6.0, zc + 0.9), (rollers.BRG_ROOT_R, zc),
                      (6.0, zc - 0.9), (6.0, zc - 2), (1.5, zc - 2)], x, y)

def ycyl(x, z, r0, r1, y0, y1, n=96):
    m = Manifold.cylinder(y1 - y0, r1, r1, n).rotate([-90, 0, 0]).translate([x, y0, z])
    if r0 > 0:
        m -= Manifold.cylinder(y1 - y0 + 2, r0, r0, n).rotate([-90, 0, 0]).translate([x, y0 - 1, z])
    return m

parts = []
def add(name, m, color, group, rotor=-1, opacity=1.0):
    parts.append(dict(name=name, m=m, color=color, group=group, rotor=rotor, opacity=opacity))

def magnet_pockets(cx, cy, r, ang, z_back, depth, chamfer=False):
    """two pockets on a dial's back face, straddling angle ang (deg) at radius r. chamfer: a 0.3 x 45 deg lead-in
    at the mouth, for dials printed with their back on the bed (elephant's foot narrows the mouth)"""
    dth = math.degrees(MAG_SEP / 2 / r)
    m = None
    for a in (ang - dth, ang + dth):
        px, py = polar(r, a)
        p = zcyl(cx + px, cy + py, MAG_D / 2 + 0.05, z_back + 0.5, z_back - depth, 32)
        if chamfer:
            p += Manifold.cylinder(0.35, MAG_D / 2 + 0.05, MAG_D / 2 + 0.40, 32).rotate([180, 0, 0]).translate([cx + px, cy + py, z_back + 0.001])
        m = p if m is None else m + p
    return m

def magnets(cx, cy, r, ang, z_back, label, rotor):
    dth = math.degrees(MAG_SEP / 2 / r)
    for a, pole in ((ang - dth, "N"), (ang + dth, "S")):
        px, py = polar(r, a)
        add(f"{label} magnet, 5x2 N52, {pole} toward the sensor", zcyl(cx + px, cy + py, MAG_D / 2, z_back, z_back - MAG_T, 24),
            "#B04A3A" if pole == "N" else "#3A5FB0", "sensor", rotor=rotor)

def hall_board(cx, cy, label):
    """thumbnail PCB behind the plate; the SOT-23 chip nests in the plate window"""
    w, h, t = HALL_PCB
    add(f"{label} Hall PCB (behind the plate)", box(cx - w / 2, cx + w / 2, cy - h / 2, cy + h / 2, PLATE_T, PLATE_T + t), "#2E6B3F", "sensor")
    add(f"{label} Hall latch, DRV5013 (SOT-23)", box(cx - SOT_W / 2, cx + SOT_W / 2, cy - SOT_L / 2, cy + SOT_L / 2, z_chip_top, PLATE_T),
        "#16191C", "sensor")

# ---------------------------------------------------------------- faceplate --
X0, X1 = PLATE_X if FULL else (-PITCH - 44, 44)
RX0, RX1 = RAIL_X if FULL else (X0 - 6, X1 + 6)
plate = box(X0, X1, -(RAIL_Y + 12), RAIL_Y + 12, 0, PLATE_T)
for _, xs, _ in STATIONS:
    plate -= zcyl(xs, 0, BOSS_HOLE / 2, -1, 3)
    for sx in (-1, 1):
        plate -= zcyl(xs + sx * EAR_PITCH / 2, -MOT_OFF, 1.6, -1, 3, 24)            # motor ears, M3
    plate -= box(xs - HALL_WIN / 2, xs + HALL_WIN / 2, HALL_R - HALL_WIN / 2, HALL_R + HALL_WIN / 2, -1, 3)
    for dy in (-5.5, 5.5):
        plate -= zcyl(xs, HALL_R + dy, 1.1, -1, 3, 16)                               # Hall PCB, M2
    plate -= zcyl(xs, TAB_R1 - 2.0, 1.1, -1, 3, 16)                                  # index tab, M2
if FULL:
    plate -= zcyl(CAL_X, CAL_Y, 6.0, -1, 3)                                           # BKA shafts + hub adapters
    for (hx, hy) in ((CAL_X, CAL_Y + HALL_R), (CAL_X, CAL_Y - MOON_HALL_R)):
        plate -= box(hx - HALL_WIN / 2, hx + HALL_WIN / 2, hy - HALL_WIN / 2, hy + HALL_WIN / 2, -1, 3)
    for sx in (-1, 1):
        for sy in (-1, 1):
            plate -= zcyl(CAL_X + sx * 14.0, CAL_Y + sy * 30.0, 1.1, -1, 3, 16)     # calendar PCB, M2
    plate -= zcyl(CAL_X + 2.8, CAL_Y + 32.0, 1.1, -1, 3, 16)                          # index hand, M2
add("Faceplate, 1.5 aluminium (never steel)", plate, "#B9C3CB", "plate", opacity=0.92)

for sy in (1, -1):
    add("Rail, 1x2 pine", box(RX0, RX1, sy * RAIL_Y, sy * (RAIL_Y + RAIL_T), 0, -38.1), "#D8B98A", "rails", opacity=0.35)
if FULL:
    for px0 in (RX0, RX1 - RAIL_T):
        add("End post, 1x2 pine", box(px0, px0 + RAIL_T, -RAIL_Y, RAIL_Y, 0, -38.1), "#D8B98A", "rails", opacity=0.35)

# ----------------------------------------------------------------- stations --
for si, (nm, xs, r) in enumerate(STATIONS):
    by = -MOT_OFF
    body = zcyl(xs, by, MOT_D / 2, PLATE_T, PLATE_T + MOT_L, 64)
    ears = zprism(CrossSection.hull(circ(xs - EAR_PITCH / 2, by, EAR_R) + circ(xs + EAR_PITCH / 2, by, EAR_R)),
                  PLATE_T, PLATE_T + EAR_T)
    for sx in (-1, 1):
        ears -= zcyl(xs + sx * EAR_PITCH / 2, by, EAR_HOLE / 2, 0, 5, 24)
    add(f"{nm} 28BYJ-48", body + ears + zcyl(xs, 0, BOSS_D / 2, 0, PLATE_T), "#8C969E", "motors")
    add(f"{nm} wire cover", box(xs - COVER_W / 2, xs + COVER_W / 2, by - COVER_REACH, by - 9,
                                PLATE_T + 1, PLATE_T + MOT_L - 2), "#2F7FC1", "motors")
    heads = None
    for sx in (-1, 1):
        h = zcyl(xs + sx * EAR_PITCH / 2, by, 2.75, 0, -EAR_HEAD, 24)
        heads = h if heads is None else heads + h
    add(f"{nm} motor-ear screws, M3 pan head", heads, "#6F7880", "motors")
    shaft = zcyl(xs, 0, SHAFT_D / 2, 0, z_shaft_tip + FLAT_LEN, 32) + \
            (zcyl(xs, 0, SHAFT_D / 2, z_shaft_tip + FLAT_LEN, z_shaft_tip, 32) ^
             box(xs - 3, xs + 3, -FLATS / 2, FLATS / 2, z_shaft_tip, z_shaft_tip + FLAT_LEN))
    add(f"{nm} shaft", shaft, "#C9CFD4", "motors", rotor=si)

    hall_board(xs, HALL_R, nm)
    tab = box(xs - 3.0, xs + 3.0, TAB_R0, TAB_R1, 0, -TAB_T) - \
          zprism(CrossSection([[(xs - 3.1, TAB_R0 - 0.1), (xs + 3.1, TAB_R0 - 0.1), (xs, TAB_R0 + 3.0)]]), 1, -TAB_T - 1)
    add(f"{nm} index tab (PLA)", tab, "#3B4650", "sensor")

    # rotor part 1: hub + Ø52 dial, magnet pair in the back at 180 deg from the pin (prints flat, dial down)
    # no rear collar: the dial prints back-down with the boss growing up. The D-bore grips 5 mm of flats and carries
    # the torque; a snug fit plus a drop of removable threadlocker holds it axially (the line pulls in-plane)
    hub = zcyl(xs, 0, R_DISC, z_disc_back, z_disc_front, 96) + zcyl(xs, 0, HUB_R + 5.0, z_disc_front, z_arm_back, 48)
    dbore = (circ(xs, 0, SHAFT_D / 2 + 0.1, 32) ^ CrossSection.square([6, FLATS + 0.1], center=True).translate([xs, 0]))
    hub -= zprism(dbore, 1, z_arm_back - 1)
    for a in (60, 300):
        px, py = polar(HUB_R + 3.0, a)
        hub -= zcyl(xs + px, py, 0.8, z_disc_back + 0.5, z_arm_back - 1, 16)
    hub -= zprism(CrossSection([[(xs + R_DISC + 0.5, -NOTCH), (xs + R_DISC + 0.5, NOTCH), (xs + R_DISC - NOTCH, 0)]]),
                  z_disc_back + 0.5, z_disc_front - 0.5)
    hub -= magnet_pockets(xs, 0, HALL_R, 180.0, z_disc_back, MAG_T, chamfer=True)
    add(f"{nm} hub + dial", hub, "#E7E1D6", "rotor", rotor=si)
    magnets(xs, 0, HALL_R, 180.0, z_disc_back, nm, si)

    # rotor part 2: arm + stepped boss (prints flat, boss up)
    arm = zprism(CrossSection.hull(circ(xs, 0, HUB_R + 5.0) + circ(xs + r, 0, ARM_END_R)), z_arm_back, z_arm_front)
    arm += zcyl(xs + r, 0, BOSS_STEP_D / 2, z_arm_front, z_arm_front - BOSS_STEP_H, 48)
    arm += zcyl(xs + r, 0, rollers.BRG_RACE_D / 2, z_arm_front - BOSS_STEP_H, z_brg_back, 48)
    for a in (60, 300):
        px, py = polar(HUB_R + 3.0, a)
        arm -= zcyl(xs + px, py, 1.1, z_arm_back + 1, z_arm_front - 1, 16)
    arm -= zcyl(xs + r, 0, INSERT_D / 2, z_arm_back + 1, z_arm_back - INSERT_L, 32)
    arm -= zcyl(xs + r, 0, 1.6, z_arm_back - INSERT_L + 0.01, z_brg_back - 1, 24)
    add(f"{nm} arm (r {r:.2f})", arm, "#C98B3B" if nm == "M2" else "#8D6BBF", "rotor", rotor=si)
    add(f"{nm} arm V623ZZ", v623(xs + r, 0, z_line), "#AEB7BE", "rotor", rotor=si)
    add(f"{nm} M3x8 axle + washer", zcyl(xs + r, 0, 1.5, z_axle_tip, z_brg_front - 0.5, 16) +
        zcyl(xs + r, 0, 3.5, z_brg_front, z_brg_front - 0.5, 24) +
        zcyl(xs + r, 0, 2.85, z_brg_front - 0.5, z_brg_front - 2.15, 24), "#6F7880", "rotor", rotor=si)

    # pulley bracket: two V623ZZ on one axle, directly above the shaft
    brk, info = rollers.build_bracket(z_line)
    add(f"{nm} pulley bracket", rollers.to_machine(brk).translate([xs, 0, 0]), "#5E7F97", "rollers")
    zin, zout = rollers.threading(nm, z_line)
    byy = info["axle_y"]
    for zc, role in ((zin, "in"), (zout, "out")):
        add(f"{nm} V623ZZ, {'front' if zc < z_line else 'rear'} ({role})", v623(xs, byy, zc), "#AEB7BE", "rollers")
    add(f"{nm} 3x5x0.5 shim", zcyl(xs, byy, 2.5, z_line - rollers.SHIM / 2, z_line + rollers.SHIM / 2, 24), "#C9A34E", "rollers")
    add(f"{nm} M3x20 axle + nyloc", zcyl(xs, byy, 1.5, info["z_rear"] + 4.0, info["z_front"] - 1.7, 16) +
        zcyl(xs, byy, 2.75, info["z_front"], info["z_front"] - 1.7, 24) +
        zcyl(xs, byy, 3.1, info["z_rear"], info["z_rear"] + 4.0, 6), "#6F7880", "rollers")

# --------------------------------------------------- pen + drum (full only) --
BRIDGE_UNDER = rollers.AXLE_Y + rollers.BRG_OD / 2 + rollers.BRG_CLEAR
PEN_YHI = min(rollers.AXLE_Y - rollers.BRG_OD - 2.0,
              BRIDGE_UNDER - 1.0 - rollers.BRG_OD / 2 - PEN_S)
PEN_YLO = -RAIL_Y + 2.0 + rollers.BRG_OD / 2
PEN_YC  = (PEN_YHI + PEN_YLO) / 2
SUM_R   = sum(r for _, _, r in ALL_STATIONS)
if FULL:
    zin, zout = PLANE_REAR, PLANE_FRONT        # row index 5 is odd: in rear, out front (the anchor)
    brk, info = rollers.build_bracket(z_line)
    add("Pen bracket", rollers.to_machine(brk).translate([PEN_X, 0, 0]), "#5E7F97", "rollers")
    add("Pen bracket V623ZZ, rear (in)", v623(PEN_X, info["axle_y"], zin), "#AEB7BE", "rollers")
    add("Pen-zero anchor (screw-adjustable), front plane", zcyl(PEN_X, info["axle_y"], 3.0, zout + 1.5, zout - 1.5, 24), "#C9A34E", "rollers")
    add("Pen bracket M3x20 axle", zcyl(PEN_X, info["axle_y"], 1.5, info["z_rear"] + 4.0, info["z_front"] - 1.7, 16), "#6F7880", "rollers")
    for sx in (-1, 1):
        add(f"Pen guide rod, {PEN_ROD_D:g} mm steel", Manifold.cylinder(2 * (RAIL_Y + SOCKET), PEN_ROD_D / 2, PEN_ROD_D / 2, 24)
            .rotate([-90, 0, 0]).translate([PEN_X + sx * PEN_ROD_DX, -(RAIL_Y + SOCKET), PEN_BZ]), "#9AA3AA", "pen")
    top = PEN_S + 5.0
    u = CrossSection.square([2 * PEN_BODY_X, 10.0]).translate([-PEN_BODY_X, -5.0]) + \
        CrossSection.square([PEN_BODY_X - PEN_GAP_X, top + 5.0]).translate([PEN_GAP_X, -5.0]) + \
        CrossSection.square([PEN_BODY_X - PEN_GAP_X, top + 5.0]).translate([-PEN_BODY_X, -5.0])
    # two flat parts clamped by the axles: REAR PLATE (prints front-face-down, pulley stub up) and FRONT BODY
    # (front plate + spacer frame, prints front-face-down so each pocket is a notch open at the top)
    z_split = PEN_BZ + PEN_POCKET
    rear = zprism(u.translate([PEN_X, 0]), PEN_ZR, z_split)
    front = zprism(u.translate([PEN_X, 0]), z_split, PEN_ZF)
    brgs, shims = None, None
    for sx in (-1, 1):
        for byc in (0.0, PEN_S):
            bx = PEN_X + sx * PEN_BX
            front -= box(bx - sx * 7.0, bx + sx * 7.0, byc - 6.5, byc + 6.5, z_split + 0.5, PEN_BZ - PEN_POCKET)
            front += zcyl(bx, byc, rollers.BRG_RACE_D / 2, PEN_BZ - PEN_POCKET, PEN_BZ - PEN_POCKET + 0.5, 24)
            hole = zcyl(bx, byc, 1.6, PEN_ZR + 1, PEN_ZF - 1, 16)
            if sx > 0:          # slotted on the +x side: set a light preload against the rods, then lock
                hole = zprism(CrossSection.hull(circ(bx - 0.6, byc, 1.6, 16) + circ(bx + 0.6, byc, 1.6, 16)), PEN_ZR + 1, PEN_ZF - 1)
            rear -= hole; front -= hole
            b = v623(bx, byc, PEN_BZ) + zcyl(bx, byc, 1.5, PEN_ZF + 16.0, PEN_ZF, 12) + \
                zcyl(bx, byc, 2.85, PEN_ZF, PEN_ZF - 1.65, 24) + zcyl(bx, byc, 3.2, PEN_ZR, PEN_ZR + 2.4, 6)
            brgs = b if brgs is None else brgs + b
            sh = zcyl(bx, byc, 2.5, z_split, z_split - 0.5, 24)   # rear-side spacer: a 3x5x0.5 shim, not a printed boss
            shims = sh if shims is None else shims + sh
    # pen pulley rides BEHIND the carriage on a short stub of the rear plate, in the line plane
    rear += zcyl(PEN_X, 0, BOSS_STEP_D / 2, PEN_ZR, z_brg_front - BOSS_RACE_H, 32) + \
            zcyl(PEN_X, 0, rollers.BRG_RACE_D / 2, z_brg_front - BOSS_RACE_H, z_brg_front, 32)
    rear -= zcyl(PEN_X, 0, 1.6, z_brg_front + 1, z_split - 1, 16)
    front -= zcyl(PEN_X, 0, 1.6, z_split + 1, PEN_ZF + INSERT_L, 16)                 # M3 clearance
    front -= zcyl(PEN_X, 0, INSERT_D / 2, PEN_ZF + INSERT_L, PEN_ZF - 1, 32)         # insert, pressed in from the front
    add("Pen carriage rear plate (PLA)", rear, "#B5654A", "pen", rotor=100)
    add("Pen carriage front body (PLA)", front, "#A8583E", "pen", rotor=100)
    add("Carriage V623ZZ x4 on M3x16 axles + nuts (+x pair slotted for preload)", brgs, "#AEB7BE", "pen", rotor=100)
    add("Carriage 3x5x0.5 shims x4 (rear side)", shims, "#C9A34E", "pen", rotor=100)
    add("Pen pulley V623ZZ (behind the carriage)", v623(PEN_X, 0, z_line) +
        zcyl(PEN_X, 0, 1.5, z_brg_back, PEN_ZF + 1.0, 16) + zcyl(PEN_X, 0, 2.85, z_brg_back, z_brg_back + 1.65, 24),
        "#AEB7BE", "pen", rotor=100)
    arm_y = PEN_S / 2
    add("Pen arm + nib", box(PEN_X + PEN_BODY_X - 3.0, DRUM_X - DRUM_R - 1.5, arm_y - 2, arm_y + 2, DRUM_Z + 2, DRUM_Z - 2) +
        Manifold.cylinder(1.5, 0.6, 0.3, 12).rotate([0, 90, 0]).translate([DRUM_X - DRUM_R - 1.5, arm_y, DRUM_Z]), "#3B4650", "pen", rotor=100)
    add("Drum, 3in Sch 40 PVC", ycyl(DRUM_X, DRUM_Z, DRUM_BORE, DRUM_R, -DRUM_L / 2, DRUM_L / 2), "#E9E6DF", "pen", rotor=200)
    add("Chart paper", ycyl(DRUM_X, DRUM_Z, DRUM_R + 0.05, DRUM_R + 0.25, -60, 60), "#FBFAF6", "pen", rotor=200, opacity=0.95)
    for sy in (-1, 1):
        y0 = DRUM_L / 2 - 6 if sy > 0 else -DRUM_L / 2
        add("Drum end cap (printed)", ycyl(DRUM_X, DRUM_Z, 0, DRUM_BORE, y0, y0 + 6, 64), "#5E7F97", "pen", rotor=200)
    add("Drum shaft, 7 mm", ycyl(DRUM_X, DRUM_Z, 0, 3.5, -(RAIL_Y + RAIL_T), RAIL_Y + RAIL_T + 5.0, 24), "#9AA3AA", "pen", rotor=200)
    add("Drum 28BYJ-48 (mount not designed)", ycyl(DRUM_X + MOT_OFF, DRUM_Z, 0, MOT_D / 2, RAIL_Y + RAIL_T, RAIL_Y + RAIL_T + MOT_L, 48), "#8C969E", "pen")

    # ---- calendar: BKA30D-R5 (PLACEHOLDER body, shafts assumed at its centre) -------------
    cx, cy = CAL_X, CAL_Y
    w, h, t = CAL_PCB
    add("Calendar PCB: BKA30D-R5 + 2 Hall latches (behind the plate)", box(cx - w / 2, cx + w / 2, cy - h / 2, cy + h / 2, PLATE_T, PLATE_T + t), "#2E6B3F", "motors")
    add("BKA30D-R5 dual-shaft gauge stepper (placeholder)", box(cx - BKA_W / 2, cx + BKA_W / 2, cy - BKA_L / 2, cy + BKA_L / 2,
        PLATE_T + t, PLATE_T + t + BKA_T), "#23272B", "motors")
    for (hx, hy, lab) in ((cx, cy + HALL_R, "Year"), (cx, cy - MOON_HALL_R, "Moon")):
        add(f"{lab} Hall latch, DRV5013 (SOT-23)", box(hx - SOT_W / 2, hx + SOT_W / 2, hy - SOT_L / 2, hy + SOT_L / 2, z_chip_top, PLATE_T),
            "#16191C", "sensor")
    # year dial on the OUTER (tube) shaft: same Ø52 outline, magnet pair at r 20.5, centre clears the moon hub
    yd = zcyl(cx, cy, R_DISC, z_disc_back, z_disc_front, 96) + zcyl(cx, cy, 5.5, 0.5, z_disc_back, 32)
    yd -= zcyl(cx, cy, 2.6, 2, z_disc_front - 1, 24)
    yd -= zprism(CrossSection([[(cx + R_DISC + 0.5, cy - NOTCH), (cx + R_DISC + 0.5, cy + NOTCH), (cx + R_DISC - NOTCH, cy)]]),
                 z_disc_back + 0.5, z_disc_front - 0.5)
    yd -= magnet_pockets(cx, cy, HALL_R, 180.0, z_disc_back, MAG_T)
    add("Year dial + hub adapter (outer shaft)", yd, "#E7E1D6", "rotor", rotor=400)
    magnets(cx, cy, HALL_R, 180.0, z_disc_back, "Year", 400)
    # moon disc on the INNER shaft, 1 mm in front of the year dial
    md = zcyl(cx, cy, MOON_R, z_moon_back, z_moon_front, 96) + zcyl(cx, cy, 2.4, z_disc_back, z_moon_back, 24)
    md -= magnet_pockets(cx, cy, MOON_HALL_R, 180.0, z_moon_back, MAG_T)
    add("Moon disc + hub (inner shaft)", md, "#F4F1E8", "rotor", rotor=300)
    magnets(cx, cy, MOON_HALL_R, 180.0, z_moon_back, "Moon", 300)
    # one index hand at 12 o'clock reads both: crosses the year ring and stops at the moon's rim
    # hand centred on 12 o'clock; base flush with the hand's -x side, so the part prints lying on that side
    base = box(cx - 1.2, cx + 6.8, cy + 28.0, cy + 36.0, 0, z_hand[1])
    hand = box(cx - 1.2, cx + 1.2, cy + MOON_R + 1.0, cy + 36.0, z_hand[0], z_hand[1])
    add("Calendar index hand (PLA)", base + hand, "#3B4650", "sensor")

# ------------------------------------------------------------- clearances --
o1, m2 = STATIONS[-2], STATIONS[-1]
arm_reach_m2 = m2[2] + ARM_END_R
brg_reach_m2 = m2[2] + rollers.BRG_OD / 2
clear = [
    ("Dial back to the motor-ear screw heads",  DISC_GAP),
    ("Hall PCB behind plate to motor body top",  (HALL_R - HALL_PCB[1] / 2) - (MOT_D / 2 - MOT_OFF)),
    ("Index tab behind M2's arm",               (-TAB_T) - z_arm_back),
    ("Index tab to the dial rim",               TAB_R0 - R_DISC),
    ("M2 arm over O1's dial (z gap)",           ARM_GAP),
    ("M2 arm to O1 boss (same plane)",          PITCH - arm_reach_m2 - (HUB_R + 5.0)),
    ("M2 arm bearing to O1 arm bearing",        PITCH - brg_reach_m2 - (o1[2] + rollers.BRG_OD / 2)),
    ("Dials, neighbour to neighbour",           PITCH - 2 * R_DISC),
    ("M2 arm bearing to rail pulleys (top)",    rollers.AXLE_Y - rollers.BRG_OD / 2 - brg_reach_m2),
    ("Axle tip short of the arm's back face",   z_arm_back - z_axle_tip),
    ("Line legs in front of the arm face",      z_arm_front - PLANE_REAR),
    ("Line legs to neighbour's arm bearing",    PITCH - (o1[2] + rollers.BRG_ROOT_R) - brg_reach_m2),
    ("Pulley brackets, neighbour to neighbour", PITCH - 2 * rollers.HALF_X),
]
if FULL:
    clear += [
        ("M2 arm bearing to pen guide rod",         PEN_X - PEN_ROD_DX - PEN_ROD_D / 2 - brg_reach_m2),
        ("Pen rod to carriage body",                PEN_ROD_DX - PEN_ROD_D / 2 - PEN_BODY_X),
        ("Carriage U-gap to pen bracket cheeks",    PEN_GAP_X - 5.0),
        ("Carriage body in front of the line legs", PLANE_FRONT - PEN_ZR),
        ("Drum to right end post",                  RAIL_X[1] - RAIL_T - (DRUM_X + DRUM_R)),
        ("Pen travel: window less the 114.1 needed", (PEN_YHI - PEN_YLO) - 2 * SUM_R),
        ("Year dial to the N2 and K1 dials",        math.hypot(PITCH / 2, CAL_Y) - 2 * R_DISC),
        ("Year dial to the bottom rail",            (CAL_Y - R_DISC) + RAIL_Y),
        ("Moon disc to the year dial (z gap)",      MOON_GAP),
        ("Index hand in front of the moon disc",    z_moon_front - z_hand[0]),
        ("Calendar PCB to N2/K1 wire covers",       PITCH / 2 - CAL_PCB[0] / 2 - COVER_W / 2),
        ("Calendar PCB to N2/K1 motor ears",        (CAL_Y + CAL_PCB[1] / 2) * -1 - (MOT_OFF + EAR_R)),
        ("Index-hand base to the year dial rim",    28.0 - R_DISC),
        ("Carriage axle nuts to the pen pulley and bracket bearings", PEN_BX - 3.2 - rollers.BRG_OD / 2),
    ]
stack = [
    ("Hall element (chip nested in a plate window)", z_hall), ("Faceplate front face", 0.0),
    ("Motor-ear screw heads", -EAR_HEAD), ("Dial back = magnet faces", z_disc_back), ("Dial front", z_disc_front),
    ("Arm back", z_arm_back), ("Shaft tip", z_shaft_tip), ("Arm front", z_arm_front),
    ("Rear pulley plane", PLANE_REAR), ("Arm bearing groove (line)", z_line), ("Front pulley plane", PLANE_FRONT),
    ("Arm bearing front", z_brg_front), ("Pen carriage body", PEN_ZR), ("Pen rods / carriage bearings", PEN_BZ),
]
print(f"line plane z {z_line:.2f}; Hall element z {z_hall:+.2f}, magnet gap {z_hall - z_disc_back:.2f} mm")
for k, v in clear:
    print(f"  {k:44s} {v:6.2f} mm")
bad = [k for k, v in clear if v < 0.5]
print("  ALL CLEAR" if not bad else f"  INTERFERENCE: {bad}")

# ---------------------------------------------------------------- export --
out = []
for p in parts:
    mesh = p["m"].to_mesh()
    v = np.asarray(mesh.vert_properties)[:, :3].copy()
    t = np.asarray(mesh.tri_verts).astype(int)
    v[:, 2] *= -1
    t = t[:, ::-1]
    out.append(dict(name=p["name"], color=p["color"], group=p["group"], rotor=p["rotor"],
                    opacity=p["opacity"], v=np.round(v, 2).ravel().tolist(), t=t.ravel().tolist()))

def fleet(r):
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
                    rate=SIGMA[n] / SIGMA["M2"], a0=START_ANG[n],
                    order=("front" if zi < z_line else "rear") + " in, " + ("front" if zo < z_line else "rear") + " out"))
    print(f"  {n}: {sts[-1]['order']}, worst leg fleet angle {sts[-1]['fleet']} deg")
m2rate = 360.0 / (360.0 / SIGMA["M2"])
data = dict(parts=out, stations=sts,
            line=dict(z=-z_line, y=rollers.LINE_Y, rollerR=rollers.BRG_ROOT_R, rollerY=rollers.AXLE_Y,
                      sleeveR=rollers.BRG_ROOT_R, x0=(STATIONS[0][1] - 26) if FULL else X0, x1=X1),
            pen=(dict(x=PEN_X, yc=PEN_YC, yHi=PEN_YHI, yLo=PEN_YLO, zIn=-PLANE_REAR, zOut=-PLANE_FRONT) if FULL else None),
            drum=(dict(x=DRUM_X, z=-DRUM_Z) if FULL else None),
            moon=(dict(x=CAL_X, y=CAL_Y, rate=(360.0 / SYNODIC_H) / SIGMA["M2"], a0=0.0) if FULL else None),
            year=(dict(x=CAL_X, y=CAL_Y, rate=(360.0 / YEAR_H) / SIGMA["M2"], a0=0.0) if FULL else None),
            views=(dict(iso=[[-60, 0, 10], 900, 0.5, 0.28], front=[[-60, 0, 10], 980, 0, 0],
                        sensor=[[0, 20.5, 2], 110, 0.9, 0.35], side=[[0, 0, 10], 420, 1.5708, 0.02],
                        back=[[-60, 5, 0], 820, 2.75, 0.22]) if FULL else
                   dict(iso=[[-22, 4, 8], 400, 0.55, 0.30], front=[[-22, 0, 8], 470, 0, 0],
                        sensor=[[0, 20.5, 2], 110, 0.9, 0.35], side=[[0, 0, 8], 300, 1.5708, 0.02],
                        back=[[-22, 5, 0], 360, 2.75, 0.22])),
            clear=[[k, round(v, 2)] for k, v in clear], stack=[[k, round(v, 2)] for k, v in stack])
tmpl = open("station_study.tmpl.html", encoding="utf8").read()
OUT = "revm_model.html" if FULL else "station_study.html"
if FULL:
    a = tmpl.index('<p class="lede">'); b = tmpl.index('</p>', a) + 4
    tmpl = tmpl[:a] + ('<p class="lede">The whole Rev M machine: five arm stations at the equal 56&nbsp;mm pitch, '
        'each with a Hall latch looking through a window in the faceplate at a magnet pair in the back of its Ø52 dial, under six '
        'pulley brackets on the top rail. Below N2 and K1, a BKA30D-R5 turns the year dial and, in front of it, the moon disc. '
        'The line runs from the far anchor at S2 through every station to the pen, whose carriage now rides <b>in front</b> of the line on four '
        'V623ZZ and two 3&nbsp;mm rods. <b>Play</b> turns each arm at its constituent&rsquo;s relative rate, and the pen rides at half the '
        'summed take-up. The BKA body, its shaft positions and the drum motor mount are placeholders.</p>') + tmpl[b:]
    tmpl = tmpl.replace("<title>Arm Station Study</title>", "<title>Tide Machine Rev M</title>", 1)
    tmpl = tmpl.replace("<h1>Arm Station Study</h1>", "<h1>Tide Machine, Rev M</h1>", 1)
    tmpl = tmpl.replace('aria-label="3D model of two tide machine stations"', 'aria-label="3D model of the whole Rev M tide machine"', 1)
open(OUT, "w", encoding="utf8").write(tmpl.replace("/*DATA*/null", json.dumps(data, separators=(",", ":"))))
print(f"{OUT}  ({os.path.getsize(OUT)/1024:.0f} KB, {len(out)} parts)")

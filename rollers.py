"""Pulley bracket for the Rev M tide machine -- one per station, six in all.

Each bracket screws to the INNER face of the TOP rail, directly above its
station's shaft, and carries TWO V-groove bearings (V623ZZ, 3 x 12 x 4) side
by side on ONE M3 axle: a FRONT pulley and a REAR pulley, 4.5 mm apart.

Threading, per station: the line arrives along the rail, wraps 90 deg over its
IN pulley and drops on the +x side (x = +root radius) to the arm's bearing,
U-turns under it, climbs on the -x side to its OUT pulley, wraps 90 deg over the
top and leaves along the rail. The order is MIRRORED at alternate stations
(row index even: in = front, out = rear; odd: in = rear, out = front), so every
run between stations stays in one plane. Only the legs are skewed, +/-2.25 mm
over the leg length.

Machine frame: x along the row, y up (crank centreline y = 0), z toward the
viewer is NEGATIVE (the faceplate is at z = 0, rails run from 0 to -38.1).

Print frame (what an STL would be in): the face that sits against the rail is
on the bed, the two clevis cheeks stand up as walls, the axle hole runs
horizontally as a teardrop. No support needed.

    python rollers.py        ->  pulley_bracket.stl  (+ a console summary)
    import rollers           ->  build_bracket(), to_machine(), threading()  (writes nothing)

Rev M values that are not in tide_machine.rb's CFG yet live here. Move them
into CFG when the Ruby catches up, and parse them from there like faceplate.py.
"""
import numpy as np
from manifold3d import Manifold, CrossSection

# ---------------------------------------------------------------- inputs --
RAIL_Y      = 76.0    # inner face of the top rail: rails 152 apart (Rev M; Rev L was 140)
LINE_Y      = RAIL_Y - 6.0    # the line runs along the pulley tops, 6 below the rail face
LINE_Z      = -15.0   # arm-bearing groove plane, from station_study.py's depth stack
# the arm carries the same V623ZZ, so its groove matches BRG_ROOT_R and the legs hang vertical

BRG_OD      = 12.0    # V623ZZ
BRG_W       = 4.0
BRG_ROOT_R  = 4.8     # line radius at the V root -- MEASURE when they arrive
BRG_RACE_D  = 5.0     # inner-race OD: bosses and shim touch this and nothing else
SHIM        = 0.5     # between the two bearings: 3 x 5 x 0.5, NOT an M3 washer (it rubs the shields)

AXLE_D      = 3.3     # M3 clearance
CHEEK_T     = 3.0
BOSS_H      = 0.5     # cheek boss to the outer bearing face, each side
LOBE_R      = 5.0     # cheek material round the axle
BRG_CLEAR   = 1.0     # bearing OD to the bridge underside
FLOAT       = 0.2     # axial float in the bearing stack, so a slightly fat print can't pinch the bearings

HALF_X      = 15.0    # bridge half-width
SCREW_X     = 11.0    # two #4 wood screws, either side of the clevis, on the pulley plane midline
SCREW_D     = 3.2
SCREW_HEAD  = 6.2     # countersink diameter

ROW = ["S2", "N2", "K1", "O1", "M2"]      # far end -> pen

# -------------------------------------------------------------- derived --
PLANE_DZ  = (SHIM + BRG_W) / 2               # each pulley plane from the arm-bearing plane
AXLE_Y    = LINE_Y - BRG_ROOT_R              # pulley centre height
BRIDGE_T  = RAIL_Y - (AXLE_Y + BRG_OD / 2 + BRG_CLEAR)


def planes(line_z=LINE_Z):
    """(front, rear) pulley plane z"""
    return line_z - PLANE_DZ, line_z + PLANE_DZ


def threading(name, line_z=LINE_Z):
    """(z_in, z_out) for a station, mirrored at alternate stations"""
    front, rear = planes(line_z)
    return (front, rear) if ROW.index(name) % 2 == 0 else (rear, front)


def build_bracket(line_z=LINE_Z):
    """the bracket in PRINT frame; to_machine() takes it to the machine frame"""
    stack = SHIM / 2 + BRG_W + BOSS_H + FLOAT / 2   # cheek inner face from the arm-bearing plane
    z_rear_in, z_front_in = line_z + stack, line_z - stack
    z_rear, z_front = z_rear_in + CHEEK_T, z_front_in - CHEEK_T
    assert BRIDGE_T >= 3.0, f"bridge only {BRIDGE_T:.2f} mm"
    assert z_rear < -1.0, "rear cheek runs into the faceplate plane"
    assert z_front > -38.1, "front cheek past the rail's front face"

    Za = RAIL_Y - AXLE_Y                        # print frame: Z = RAIL_Y - y

    def box(x0, x1, y0, y1, z0, z1):
        return Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])

    def xz_prism(cs, y0, y1):
        """extrude a CrossSection drawn in (X, Z) along Y from y0 to y1"""
        return cs.extrude(y1 - y0).rotate([90, 0, 0]).translate([0, y1, 0])

    part = box(-HALF_X, HALF_X, z_front, z_rear, 0, BRIDGE_T)
    lobe = CrossSection.circle(LOBE_R, 64).translate([0, Za]) + \
           CrossSection.square([2 * LOBE_R, Za]).translate([-LOBE_R, 0])
    part += xz_prism(lobe, z_rear_in, z_rear)
    part += xz_prism(lobe, z_front, z_front_in)
    boss = CrossSection.circle(BRG_RACE_D / 2, 48).translate([0, Za])
    part += xz_prism(boss, z_rear_in - BOSS_H, z_rear_in)
    part += xz_prism(boss, z_front_in, z_front_in + BOSS_H)

    r = AXLE_D / 2                              # teardrop: point toward +Z prints without support
    tip = CrossSection.square([r * np.sqrt(2)] * 2, center=True).rotate(45).translate([0, r * 0.5])
    part -= xz_prism((CrossSection.circle(r, 48) + tip).translate([0, Za]), z_front - 1, z_rear + 1)

    for sx in (-1, 1):
        part -= Manifold.cylinder(BRIDGE_T + 2, SCREW_D / 2, SCREW_D / 2, 32).translate([sx * SCREW_X, line_z, -1])
        h = SCREW_HEAD / 2                      # countersink on the underside, where the head sits
        part -= Manifold.cylinder(h + 0.01, 0.01, h + 0.01, 48).translate([sx * SCREW_X, line_z, BRIDGE_T - h])

    notch = CrossSection([[(-1.5, 0), (1.5, 0), (0, 1.8)]]).extrude(BRIDGE_T + 2).translate([0, z_front - 0.001, -1])
    part -= notch                               # station centre mark, front edge

    return part, dict(axle_y=AXLE_Y, bridge_t=BRIDGE_T, z_rear=z_rear, z_front=z_front,
                      z_rear_in=z_rear_in, z_front_in=z_front_in, planes=planes(line_z))


def to_machine(m):
    """print frame (X=x, Y=z, Z=RAIL_Y-y) -> machine frame"""
    return m.transform([[1, 0, 0, 0], [0, 0, -1, RAIL_Y], [0, 1, 0, 0]])


if __name__ == "__main__":
    part, info = build_bracket()
    mesh = part.to_mesh()
    verts, tris = np.asarray(mesh.vert_properties)[:, :3], np.asarray(mesh.tri_verts)
    with open("pulley_bracket.stl", "wb") as f:
        f.write(b"tide machine pulley bracket".ljust(80, b" "))
        f.write(np.uint32(len(tris)).tobytes())
        rec = np.zeros(len(tris), dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
        tri = verts[tris]
        nrm = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        rec["n"] = nrm / (np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-12)
        rec["v"] = tri
        f.write(rec.tobytes())
    lo, hi = verts.min(0), verts.max(0)
    fz, rz = info["planes"]
    print("pulley_bracket.stl -- print 6 (five stations + the pen)")
    print(f"  footprint      : {hi[0]-lo[0]:.1f} x {hi[1]-lo[1]:.1f} mm, {hi[2]-lo[2]:.1f} tall")
    print(f"  volume         : {part.volume()/1000:.2f} cm3, genus {part.genus()}")
    print(f"  pulleys        : axle at y {AXLE_Y:.2f}, planes z {fz:.2f} (front) / {rz:.2f} (rear)")
    print(f"  cheeks         : z {info['z_rear']:.2f} to {info['z_front']:.2f}; bridge {BRIDGE_T:.2f} thick")
    print(f"  threading      : " + ", ".join(f"{n} in {'front' if threading(n)[0] < LINE_Z else 'rear'}" for n in ROW))
    print(f"  hardware each  : 2 x V623ZZ, 1 x 3x5x0.5 shim, M3x20 + nyloc, 2 x #4 x 3/4\" flat-head wood screw")

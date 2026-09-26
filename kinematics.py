"""Rev M station kinematics -- the ONE place the line geometry and the firmware
inverse live. decals.py warps its scales with it; the firmware lookup tables
should be generated from it too, so a dial can never disagree with its arm.

A station: an arm of radius r on the motor shaft carries a V623ZZ. The line
comes over the IN pulley, drops on the +x side, U-turns under the arm bearing,
climbs on the -x side to the OUT pulley. Both pulleys sit on one axle directly
above the shaft (rollers.py), in planes +/-PLANE_DZ either side of the arm
bearing's groove.

Conventions
  phase phi (deg): the station's output is r*cos(phi) -- phi = 0 is that
                   constituent's high water, the pin at the top of its travel.
  arm angle theta (deg): world angle of the pin from +x, counterclockwise seen
                   from the front. The firmware inverse turns the arm at an
                   uneven rate so the line length is exactly sinusoidal in phi.
"""
import math
import numpy as np
import rollers

A_LEG = rollers.BRG_ROOT_R        # legs leave the pulleys at x = +/- the root radius
H_EYE = rollers.AXLE_Y            # ... at the pulley axle height
R_ARM = rollers.BRG_ROOT_R        # the arm carries the same bearing
DZ    = rollers.PLANE_DZ          # each pulley plane from the arm-bearing plane


def loop_length(px, py, a=A_LEG, H=H_EYE, R=R_ARM, dz=DZ):
    """line length through one station: two legs (3D, including the plane offset) + the wrap"""
    L, phis = 0.0, []
    for ex, sg in ((-a, 1), (a, -1)):
        dx, dy = ex - px, H - py
        d, al = math.hypot(dx, dy), math.atan2(dy, dx)
        phi = al + sg * math.acos(min(1.0, R / d))
        tx, ty = px + R * math.cos(phi), py + R * math.sin(phi)
        L += math.hypot(math.hypot(ex - tx, H - ty), dz)
        phis.append(phi)
    wrap = 2 * math.pi - ((phis[0] - phis[1]) % (2 * math.pi))
    return L + R * wrap


class Station:
    """firmware inverse for one arm radius r: theta(phi), tabulated"""

    def __init__(self, r, n=4096):
        self.r = r
        t = np.linspace(-90.0, 270.0, 2 * n + 1)
        self.th = t
        self.L = np.array([loop_length(r * math.cos(math.radians(a)), r * math.sin(math.radians(a))) for a in t])
        self.Lmin = loop_length(0.0, r)       # pin at the top: shortest loop, highest output
        self.Lmax = loop_length(0.0, -r)
        self.Lmid, self.Lhalf = (self.Lmin + self.Lmax) / 2, (self.Lmax - self.Lmin) / 2
        self.n = n

    def theta(self, phi):
        """arm angle (deg) for phase phi (deg): the line length is Lmid - Lhalf*cos(phi)"""
        phi = math.radians(phi)
        Lt = self.Lmid - self.Lhalf * math.cos(phi)
        rising = math.sin(phi) < 0             # output increasing: pin on the rising half
        if rising:                              # theta in [-90, 90], L falling
            seg_t, seg_L = self.th[:self.n + 1], self.L[:self.n + 1]
            return float(np.interp(-Lt, -seg_L, seg_t))
        seg_t, seg_L = self.th[self.n:], self.L[self.n:]   # theta in [90, 270], L rising
        return float(np.interp(Lt, seg_L, seg_t))

    def output(self, theta):
        """station output (mm of take-up / 2) for an arm angle -- for checks"""
        return (self.Lmid - loop_length(self.r * math.cos(math.radians(theta)),
                                        self.r * math.sin(math.radians(theta)))) / 2


if __name__ == "__main__":
    # self-check: the inverse must reproduce r*cos(phi) exactly
    for r in (35.0, 8.75, 2.45):
        s = Station(r, n=16384)
        err = max(abs(s.output(s.theta(p)) - r * math.cos(math.radians(p))) for p in np.linspace(0, 359, 720))
        dev = [s.theta(p) - (90 + p) for p in np.linspace(0, 359, 720)]   # counterclockwise: theta ~ 90 + phi
        dev = [((d + 180) % 360) - 180 for d in dev]
        print(f"r {r:5.2f}: inverse error {err*1000:.2f} um, arm departs from uniform by "
              f"{(max(dev)-min(dev))/2:.2f} deg")

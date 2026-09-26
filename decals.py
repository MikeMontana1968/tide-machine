"""Dial decals for the Rev M tide machine: five station dials + the moon-phase dial.

    python decals.py   ->  decals_1to1.pdf   (Letter, 1:1, two pages of 7 + a 100 mm calibration bar each)

Each decal goes on the front of a flag disc (Ø52, with the arm's Ø24 boss in the
middle) and is read against a fixed index on the sensor pad at 12 o'clock.

Scales read ASTRONOMICAL time, and they are warped:
  * S2  local mean solar time, 12 h (a real clock face)
  * M2  local lunar time, 12 lunar hours (0 = mean Moon on your meridian)
  * K1  local sidereal time, 24 h
  * N2  hours of its 12 h 39.5 m period (N2 - M2 is the Moon's mean anomaly)
  * O1  hours of its 25 h 49.2 m period (K1 - O1 tracks the Moon's declination)
  * YEAR  months, month-anchored ticks (8th, 15th, 22nd, 29th), 366 slots; Feb 29 skipped in common years
  * MOON  days since new moon, with phase icons (Ø32, on the BKA30D-R5's inner shaft)
The firmware inverse turns each arm at an uneven rate, so each tick sits where the
arm really is at that time, from kinematics.py -- M2's ticks move by up to 15.7 deg.

A coral HW tick marks where that constituent's own high water falls (phase lag G).
The index reads true time only for the constituent set, longitude and epoch the
decals were printed for: G and the nodal correction u move the ticks. Reprint
with the arms whenever the constituents change, and for each deployment year.

PLACEHOLDER INPUTS below (illustrative semidiurnal coast, Port San Luis
longitude). Replace G with NOAA CO-OPS "Phase (GMT)" values for the chosen port.
"""
import math, datetime as dt
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.units import mm
from reportlab.lib.colors import Color, black, white
import kinematics

# ------------------------------------------------------------------ inputs --
PIN_SCALE = 35.0
CONST = {   # amplitude (m), Greenwich phase lag G (deg) -- PLACEHOLDERS (Marigram Sandbox "semidiurnal coast")
    "M2": (1.00, 0.0), "S2": (0.25, 20.0), "N2": (0.21, 350.0), "K1": (0.10, 120.0), "O1": (0.07, 105.0)}
SPEED = {"M2": 28.9841042, "S2": 30.0, "N2": 28.4397295, "K1": 15.0410686, "O1": 13.9430356}   # deg/h
LON_E = -120.76                              # east longitude, deg (Port San Luis, CA -- placeholder)
EPOCH = dt.datetime(2026, 10, 15, 0, 0)      # UT, mid-deployment: sets the nodal corrections u
SYNODIC = 29.530589                          # days

R_OUT, R_HOLE = 26.0, 12.25                  # decal rim; hole clears the arm's Ø24 boss
INK   = Color(0.10, 0.13, 0.16)
MUTED = Color(0.36, 0.42, 0.47)
CORAL = Color(0.85, 0.35, 0.19)


# --------------------------------------------------------------- astronomy --
def julian_centuries(t):
    jd = (t - dt.datetime(2000, 1, 1, 12, 0)).total_seconds() / 86400.0 + 2451545.0
    return (jd - 2451545.0) / 36525.0

def fundamentals(t):
    """Schureman/Doodson mean longitudes (deg): T (= mean-sun hour angle + 180), s, h, p, N"""
    c = julian_centuries(t)
    ut = t.hour + t.minute / 60 + t.second / 3600
    return dict(T=15.0 * ut,
                s=218.3164477 + 481267.88123421 * c,
                h=280.46646 + 36000.76983 * c,
                p=83.3532465 + 4069.0137287 * c,
                N=125.04452 - 1934.136261 * c)

def nodal_u(t):
    """Schureman's nodal phase corrections (deg) -- constant enough over a 60-day run"""
    N = math.radians(fundamentals(t)["N"])
    s1, s2, s3 = math.sin(N), math.sin(2 * N), math.sin(3 * N)
    m2 = -2.14 * s1
    return {"M2": m2, "N2": m2, "S2": 0.0,
            "K1": -8.86 * s1 + 0.68 * s2 - 0.07 * s3,
            "O1": 10.80 * s1 - 1.34 * s2 + 0.19 * s3}

# Each dial: reading A (in its own unit) <-> Greenwich equilibrium argument V (Schureman, as NOAA uses).
#   S2: V = 2T;  A = local mean solar time (h)       ->  V = 30 A - 2 lon
#   M2: V = 2(T - s + h); A = local lunar time (lunar h)  ->  V = 30 A - 2 lon
#   K1: V = T + h - 90;  LST = T + h - 180 + lon     ->  V = 15 A - lon + 90
#   N2: V = 2T - 3s + 2h + p; A = hours of its own period from local zero  ->  V = sigma A - 2 lon
#   O1: V = T - 2s + h + 90;  A likewise              ->  V = sigma A - lon + 90
DIALS = {
    "S2": dict(name="SUN, TWICE DAILY", unit="LOCAL MEAN SOLAR TIME", per=12.0, v=lambda A: 30 * A - 2 * LON_E,
               minor=0.25, major=1, label=lambda A: str(12 if round(A) % 12 == 0 else int(round(A)) % 12)),
    "M2": dict(name="MOON, TWICE DAILY", unit="LUNAR HOURS", per=12.0, v=lambda A: 30 * A - 2 * LON_E,
               minor=0.25, major=1, label=lambda A: str(int(round(A)) % 12)),
    "K1": dict(name="SIDEREAL DAY", unit="LOCAL SIDEREAL TIME", per=24.0, v=lambda A: 15 * A - LON_E + 90,
               minor=0.5, major=2, label=lambda A: str(int(round(A)) % 24)),
    "N2": dict(name="MOON'S DISTANCE", unit="HOURS OF 12 h 39.5 m", per=360 / SPEED["N2"],
               v=lambda A: SPEED["N2"] * A - 2 * LON_E, minor=0.25, major=1, label=lambda A: str(int(round(A)))),
    "O1": dict(name="MOON, DAILY", unit="HOURS OF 25 h 49.2 m", per=360 / SPEED["O1"],
               v=lambda A: SPEED["O1"] * A - LON_E + 90, minor=0.5, major=2, label=lambda A: str(int(round(A)))),
}


# ---------------------------------------------------------------- drawing --
ROT = -90.0   # print orientation only: the pin direction (disc angle 0) at the bottom, the name across the top

def P(cx, cy, ang, r):
    """decal point: ang in the disc frame (deg, 0 = the pin direction, counterclockwise)"""
    a = math.radians(ang + ROT)
    return cx + r * math.cos(a) * mm, cy + r * math.sin(a) * mm

def arc_text(c, text, cx, cy, r, centre_ang, size, font="Helvetica-Bold", outward=True, color=INK):
    """characters along an arc, reading left to right, centred on centre_ang"""
    c.setFillColor(color); c.setFont(font, size)
    widths = [c.stringWidth(ch, font, size) / mm for ch in text]
    total = sum(widths) + 0.35 * (len(text) - 1)
    span = math.degrees(total / r)
    sgn = -1 if outward else 1                 # outward (top of dial): letters march clockwise
    a = centre_ang - sgn * span / 2
    for ch, w in zip(text, widths):
        step = math.degrees((w + 0.35) / r)
        mid = a + sgn * math.degrees(w / 2 / r)
        x, y = P(cx, cy, mid, r)
        c.saveState(); c.translate(x, y)
        c.rotate(mid + ROT - 90 if outward else mid + ROT + 90)
        c.drawCentredString(0, -size * 0.35, ch); c.restoreState()
        a += sgn * step

def radial_tick(c, cx, cy, ang, r0, r1, w, color=INK):
    c.setStrokeColor(color); c.setLineWidth(w)
    x0, y0 = P(cx, cy, ang, r0); x1, y1 = P(cx, cy, ang, r1)
    c.line(x0, y0, x1, y1)

def upright_label(c, cx, cy, ang, r, text, size=7.0):
    x, y = P(cx, cy, ang, r)
    c.setFillColor(INK); c.setFont("Helvetica-Bold", size)
    c.saveState(); c.translate(x, y); c.rotate(ang + ROT - 90); c.drawCentredString(0, -size * 0.35, text); c.restoreState()

def blank(c, cx, cy, sym, r_out=None, r_hole=None):
    r_out = R_OUT if r_out is None else r_out
    r_hole = R_HOLE if r_hole is None else r_hole
    c.setStrokeColor(MUTED); c.setLineWidth(0.3)
    c.setFillColor(white)
    c.circle(cx, cy, r_out * mm, stroke=1, fill=1)             # cut line
    c.circle(cx, cy, r_hole * mm, stroke=1, fill=0)            # cut line
    # alignment: this tick goes over the notch in the disc rim (disc angle 0)
    radial_tick(c, cx, cy, 0.0, r_out, r_out - 2.2, 1.0, CORAL)

def moon_icon(c, x, y, r, age_frac, rot=0.0):
    """phase icon, upright when it reaches the index: dark disc, lit part bounded by the limb and an
    elliptical terminator; lit on the right while waxing (northern-hemisphere view)"""
    c.saveState(); c.translate(x, y); c.rotate(rot); x = y = 0
    c.setFillColor(INK); c.setStrokeColor(INK); c.setLineWidth(0.3)
    c.circle(x, y, r, stroke=1, fill=1)
    k = math.cos(2 * math.pi * age_frac)       # terminator's x-scale: +1 new, -1 full
    waxing = age_frac < 0.5
    p = c.beginPath()
    steps = 24
    for i in range(steps + 1):                 # lit limb (right while waxing)
        a = -math.pi / 2 + math.pi * i / steps
        sx = math.cos(a) if waxing else -math.cos(a)
        (p.moveTo if i == 0 else p.lineTo)(x + r * sx, y + r * math.sin(a))
    for i in range(steps + 1):                 # terminator back down
        a = math.pi / 2 - math.pi * i / steps
        sx = k * math.cos(a)
        p.lineTo(x + r * (sx if waxing else -sx), y + r * math.sin(a))
    p.close()
    c.setFillColor(white); c.drawPath(p, stroke=0, fill=1)
    c.restoreState()

def station_decal(c, cx, cy, sym):
    d = DIALS[sym]; amp, G = CONST[sym]
    st = kinematics.Station(PIN_SCALE * amp)
    u = nodal_u(EPOCH)[sym]
    def psi(A):                                # disc angle under the 12 o'clock index when the dial reads A
        phi = d["v"](A) + u - G                 # station phase: 0 at its high water
        return 90.0 - st.theta(phi)
    blank(c, cx, cy, sym)
    n = int(round(d["per"] / d["minor"]))
    for j in range(n):
        A = j * d["minor"]
        if A > d["per"] - 1e-6:
            break
        major = abs(A / d["major"] - round(A / d["major"])) < 1e-6
        radial_tick(c, cx, cy, psi(A), R_OUT - 0.5, R_OUT - (3.6 if major else 2.0), 0.55 if major else 0.3)
        if major:
            upright_label(c, cx, cy, psi(A), R_OUT - 5.9, d["label"](A))
    # HW: the constituent's own high water (phi = 0)
    hw = 90.0 - st.theta(0.0)
    radial_tick(c, cx, cy, hw, R_OUT + 0.0, R_OUT - 4.6, 1.2, CORAL)
    x, y = P(cx, cy, hw, R_OUT - 8.9)
    c.setFillColor(CORAL); c.setFont("Helvetica-Bold", 4.2)
    c.saveState(); c.translate(x, y); c.rotate(hw + ROT - 90); c.drawCentredString(0, -1.4, "HW"); c.restoreState()
    # name (top of the band, opposite the pin/arm) and unit + symbol (bottom)
    # both lines across the top, clear of M2's arm (which covers the bottom of its own dial)
    arc_text(c, d["name"], cx, cy, 16.2, 180.0, 5.0, outward=True)
    arc_text(c, f"{sym}  ·  {d['unit']}", cx, cy, 13.9, 180.0, 3.4, font="Helvetica", outward=True, color=MUTED)

MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
MONTH_START = [0, 31, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335, 366]     # leap-year layout: 366 slots

def year_decal(c, cx, cy):
    """annulus on the year dial; the moon disc (Ø32) covers the middle. 366 slots: in common years the firmware
    steps over Feb 29 at midnight on Feb 28. Home (the magnet pair at disc angle 180) = Jan 1, 00:00."""
    r_out, r_hole = R_OUT, 16.6
    blank(c, cx, cy, "YEAR", r_out, r_hole)
    def psi(day):
        return 180.0 - 360.0 * day / 366.0      # reads clockwise like every other dial
    for m in range(12):
        d0 = MONTH_START[m]
        radial_tick(c, cx, cy, psi(d0), r_out - 0.3, r_out - 5.2, 0.7)                  # month boundary
        for dom in (8, 15, 22, 29):                                                        # month-anchored "weeks"
            day = d0 + dom - 1
            if day >= MONTH_START[m + 1]:
                continue
            leap_only = (m == 1 and dom == 29)
            radial_tick(c, cx, cy, psi(day), r_out - 0.3, r_out - (1.6 if leap_only else 2.6),
                        0.25 if leap_only else 0.4, MUTED if leap_only else INK)
        mid = (d0 + MONTH_START[m + 1]) / 2
        upright_label(c, cx, cy, psi(mid), 20.3, MONTHS[m], 5.6)

def moon_decal(c, cx, cy):
    """Ø32 moon disc in front of the year dial: days since new moon, phase icons. Home = new moon."""
    r_out, r_hole = 16.0, 2.6
    blank(c, cx, cy, "MOON", r_out, r_hole)
    def psi(age):
        return 180.0 - 360.0 * age / SYNODIC    # uniform rate; reads clockwise like the station dials
    for day in range(30):
        big = day % 5 == 0
        radial_tick(c, cx, cy, psi(day), r_out - 0.3, r_out - (2.4 if big else 1.3), 0.45 if big else 0.25)
        if big:
            upright_label(c, cx, cy, psi(day), r_out - 4.0, str(day), 4.8)
    radial_tick(c, cx, cy, psi(SYNODIC), r_out - 0.3, r_out - 2.4, 0.25, MUTED)
    for i in range(8):
        age = SYNODIC * i / 8
        x, y = P(cx, cy, psi(age), 8.2)
        moon_icon(c, x, y, 1.05 * mm, i / 8, rot=psi(age) + ROT - 90)


# ------------------------------------------------------------------ sheet --
def sheet(path="decals_1to1.pdf"):
    W, H = 215.9 * mm, 279.4 * mm
    c = rl_canvas.Canvas(path, pagesize=(W, H))
    c.setTitle("Tide machine dial decals, 1:1")
    c.setFont("Helvetica-Bold", 10); c.setFillColor(INK)
    c.drawString(14 * mm, H - 14 * mm, "Tide machine Rev M  ·  dial decals  ·  print at 100% (no scaling)")
    c.setFont("Helvetica", 6.5); c.setFillColor(MUTED)
    u = nodal_u(EPOCH)
    c.drawString(14 * mm, H - 19 * mm,
                 f"PLACEHOLDER constituents (illustrative coast), longitude {LON_E:+.2f}, epoch {EPOCH:%Y-%m-%d} UT "
                 f"(u: K1 {u['K1']:+.1f}, O1 {u['O1']:+.1f}, M2 {u['M2']:+.1f} deg). Reprint with NOAA values.")
    c.drawString(14 * mm, H - 23 * mm,
                 "Cut on the grey circles. The coral tick goes over the notch in the dial rim. Read against the index at 12 o'clock.")
    c.drawString(14 * mm, H - 27 * mm,
                 "Calendar: the year annulus goes on the Ø52 year dial; the small moon decal goes on the Ø32 moon disc in front of it.")
    order = ["S2", "N2", "K1", "O1", "M2", "YEAR", "MOON"]
    pitch_x, pitch_y = 64.0, 62.0
    for page in range(2):                       # two full sets, one per page
        if page:
            c.setFont("Helvetica-Bold", 10); c.setFillColor(INK)
            c.drawString(14 * mm, H - 14 * mm, "Tide machine Rev M  ·  dial decals  ·  spare set  ·  print at 100%")
        for i, sym in enumerate(order):
            col, row = i % 3, i // 3
            cx = (14 + 32 + col * pitch_x) * mm
            cy = H - (32 + 30 + row * pitch_y) * mm
            if sym == "MOON":
                moon_decal(c, cx, cy)
            elif sym == "YEAR":
                year_decal(c, cx, cy)
            else:
                station_decal(c, cx, cy, sym)
        # calibration bar
        y = 12 * mm
        c.setStrokeColor(INK); c.setLineWidth(0.6)
        c.line(14 * mm, y, 114 * mm, y)
        for k in range(11):
            c.line((14 + 10 * k) * mm, y, (14 + 10 * k) * mm, y + (3 if k % 5 == 0 else 1.8) * mm)
        c.setFont("Helvetica", 6.5); c.setFillColor(INK)
        c.drawString(117 * mm, y, "100 mm -- measure before cutting")
        c.showPage()
    c.save()
    return path


if __name__ == "__main__":
    p = sheet()
    u = nodal_u(EPOCH)
    print(f"{p}: 2 pages, one full set of 7 decals each, placeholder constituents, lon {LON_E:+.2f}, epoch {EPOCH:%Y-%m-%d}")
    print("nodal u (deg): " + ", ".join(f"{k} {v:+.2f}" for k, v in u.items()))
    for sym in ("S2", "N2", "K1", "O1", "M2"):
        st = kinematics.Station(PIN_SCALE * CONST[sym][0])
        d = DIALS[sym]
        ps = [90 - st.theta(d["v"](A) + u[sym] - CONST[sym][1]) for A in [k * d["per"] / 360 for k in range(360)]]
        steps = [((ps[k + 1] - ps[k] + 180) % 360) - 180 for k in range(359)]
        print(f"  {sym}: tick spacing ranges {min(steps):.3f} to {max(steps):.3f} deg per 1/360 turn (uniform = 1.000)")

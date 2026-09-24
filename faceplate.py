# -*- coding: utf-8 -*-
"""Faceplate drawings, generated FROM tide_machine.rb so they cannot drift.

Outputs into Desktop\\tide-machine\\:
  faceplate_CUT.dxf         geometry only, mm, one layer -- THIS is the vendor file
  faceplate_REF.dxf         same + annotation on separate layers, for your CAD
  faceplate_1to1_A3.pdf     A3 landscape, exact 1:1, dimensioned + hole schedule
  faceplate_1to1_tiled.pdf  Letter landscape: cover + 2 tiles, exact 1:1
"""
import io, os, re
from collections import Counter

RB  = r'C:\Users\mikem\Desktop\tide-machine\tide_machine.rb'
OUT = r'C:\Users\mikem\Desktop\tide-machine'

# ---------------------------------------------------------------- read CFG
src = io.open(RB, encoding='utf-8').read()
cfg_txt = re.search(r'CFG = \{(.*?)\n  \}', src, re.S).group(1)

def num(key):
    m = re.search(r':%s\s*=>\s*(-?[\d.]+)' % key, cfg_txt)
    if not m:
        raise KeyError(key)
    return float(m.group(1))

def arr(key):
    m = re.search(r':%s\s*=>\s*\[([^\]]*)\]' % key, cfg_txt)
    return [float(v) for v in re.findall(r'-?[\d.]+', m.group(1))]

PX0, PX1 = num('plate_x0'), num('plate_x1')
PY0, PY1 = num('plate_y0'), num('plate_y1')
PT       = num('plate_t')
XS       = arr('x')
AMP      = arr('amp')
PIN_S    = num('pin_scale')
DMARG    = num('disc_margin')
BOSS_D   = num('boss_d')
RAIL_Y   = num('rail_y')
SCR_P    = num('screw_pitch')

SHAFT_CLR   = BOSS_D + 0.5          # matches self.shaft_clear
SCREW_Y     = (RAIL_Y + PY1) / 2.0  # matches self.screw_y
MOTOR_PCD   = 35.0                  # 28BYJ-48 mounting holes, centre to centre
MOTOR_HOLE  = 3.2                   # M3
PLATE_SCREW = 4.0                   # clearance for a #6 wood screw
SENSOR_HOLE = 3.2                   # M3, sensor bracket
SENSOR_PCD  = 9.0                   # two holes across the bracket
SYM = ['M2', 'S2', 'N2', 'K1', 'O1']
PW, PH = PX1 - PX0, PY1 - PY0

def screw_xs():
    n = int(round((PX1 - PX0) / SCR_P))
    return [PX0 + 12.0 + (PX1 - PX0 - 24.0) * k / float(n) for k in range(n + 1)]

def disc_r(i):
    return PIN_S * AMP[i] + DMARG

# ---------------------------------------------------------------- hole list
holes = []   # (x, y, dia, note)
for i, x in enumerate(XS):
    holes.append((x, 0.0, SHAFT_CLR, '%s shaft clearance' % SYM[i]))
    for s in (-1, 1):
        holes.append((x + s * MOTOR_PCD / 2.0, 0.0, MOTOR_HOLE, '%s motor M3' % SYM[i]))
    for s in (-1, 1):
        holes.append((x + s * SENSOR_PCD / 2.0, disc_r(i) + 3.0, SENSOR_HOLE,
                      '%s sensor bracket M3' % SYM[i]))
for x in screw_xs():
    for y in (SCREW_Y, -SCREW_Y):
        holes.append((x, y, PLATE_SCREW, 'frame screw #6'))

outline = [(PX0, PY0), (PX1, PY0), (PX1, PY1), (PX0, PY1)]

# ---------------------------------------------------------------- DXF (R12)
def dxf(path, annotate):
    o = []
    def t(code, val):
        o.append('%d\n%s' % (code, val))
    t(0, 'SECTION'); t(2, 'HEADER')
    t(9, '$ACADVER');     t(1, 'AC1009')
    t(9, '$INSUNITS');    t(70, '4')          # 4 = millimetres
    t(9, '$MEASUREMENT'); t(70, '1')          # metric
    t(9, '$LUNITS');      t(70, '2')          # decimal
    t(9, '$EXTMIN'); t(10, '%.4f' % PX0); t(20, '%.4f' % PY0); t(30, '0.0')
    t(9, '$EXTMAX'); t(10, '%.4f' % PX1); t(20, '%.4f' % PY1); t(30, '0.0')
    t(0, 'ENDSEC')

    layers = ['CUT'] + (['REF_TEXT', 'REF_MARKS'] if annotate else [])
    t(0, 'SECTION'); t(2, 'TABLES')
    t(0, 'TABLE'); t(2, 'LAYER'); t(70, str(len(layers)))
    for name in layers:
        t(0, 'LAYER'); t(2, name); t(70, '0')
        t(62, str(7 if name == 'CUT' else (3 if name == 'REF_TEXT' else 1)))
        t(6, 'CONTINUOUS')
    t(0, 'ENDTAB'); t(0, 'ENDSEC')

    t(0, 'SECTION'); t(2, 'ENTITIES')
    t(0, 'POLYLINE'); t(8, 'CUT'); t(66, '1'); t(70, '1')   # 70=1 -> closed
    t(10, '0.0'); t(20, '0.0'); t(30, '0.0')
    for (vx, vy) in outline:
        t(0, 'VERTEX'); t(8, 'CUT')
        t(10, '%.4f' % vx); t(20, '%.4f' % vy); t(30, '0.0')
    t(0, 'SEQEND'); t(8, 'CUT')
    for (hx, hy, d, _n) in holes:
        t(0, 'CIRCLE'); t(8, 'CUT')
        t(10, '%.4f' % hx); t(20, '%.4f' % hy); t(30, '0.0'); t(40, '%.4f' % (d / 2.0))

    if annotate:
        def text(x, y, h, s):
            t(0, 'TEXT'); t(8, 'REF_TEXT')
            t(10, '%.4f' % x); t(20, '%.4f' % y); t(30, '0.0')
            t(40, '%.2f' % h); t(1, s)
        for i, x in enumerate(XS):
            text(x + 6, -17.0, 5.0, SYM[i])
            text(x + 6, -24.0, 3.0, 'x = %+.0f' % x)
            text(x + 6, disc_r(i) + 7.0, 3.0, '%s home sensor bkt' % SYM[i])
        text(PX0 + 6, PY1 - 10, 5.0, 'M2 / LEFT END')
        text(PX1 - 82, PY1 - 10, 5.0, 'PEN + DRUM END ->')
        text(PX0 + 6, PY0 + 5, 3.0,
             'FRONT FACE UP. %.0f x %.0f x %.1f' % (PW, PH, PT))
        for (hx, hy, d, _n) in holes:                       # centre crosses
            for (dx, dy) in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                t(0, 'LINE'); t(8, 'REF_MARKS')
                t(10, '%.4f' % (hx + dx * d * 0.9))
                t(20, '%.4f' % (hy + dy * d * 0.9)); t(30, '0.0')
                t(11, '%.4f' % (hx + dx * d * 1.6))
                t(21, '%.4f' % (hy + dy * d * 1.6)); t(31, '0.0')
    t(0, 'ENDSEC'); t(0, 'EOF')
    io.open(path, 'w', encoding='ascii', newline='\r\n').write('\n'.join(o) + '\n')
    return path

# ---------------------------------------------------------------- PDF
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.units import mm

BLK = (0, 0, 0)
RED = (0.78, 0.16, 0.16)
GRY = (0.62, 0.62, 0.62)
BLU = (0.13, 0.34, 0.66)

def draw_plate(c, ox, oy, dims=True, full=True):
    """1:1 -- plate (0,0) lands on page point (ox, oy)."""
    def P(x, y):
        return (ox + x * mm, oy + y * mm)

    c.setStrokeColorRGB(*BLK); c.setLineWidth(0.8)
    p0 = P(PX0, PY0)
    c.rect(p0[0], p0[1], PW * mm, PH * mm, stroke=1, fill=0)

    c.setStrokeColorRGB(*GRY); c.setLineWidth(0.25); c.setDash(6, 3)
    for x in XS:
        c.line(P(x, PY0)[0], P(x, PY0)[1], P(x, PY1)[0], P(x, PY1)[1])
    c.line(P(PX0 - 8, 0)[0], P(PX0 - 8, 0)[1], P(PX1 + 8, 0)[0], P(PX1 + 8, 0)[1])
    c.setDash()

    for (hx, hy, d, _n) in holes:
        cx, cy = P(hx, hy)
        c.setStrokeColorRGB(*BLK); c.setLineWidth(0.8)
        c.circle(cx, cy, d / 2.0 * mm, stroke=1, fill=0)
        c.setStrokeColorRGB(*RED); c.setLineWidth(0.3)
        r = max(d * 0.85, 2.4) * mm
        c.line(cx - r, cy, cx + r, cy)
        c.line(cx, cy - r, cx, cy + r)

    if not dims:
        return

    c.setFillColorRGB(*BLK)
    for i, x in enumerate(XS):
        c.setFont('Helvetica-Bold', 9)
        c.drawCentredString(P(x, -19)[0], P(x, -19)[1], SYM[i])
        c.setFont('Helvetica', 6)
        c.drawCentredString(P(x, -25)[0], P(x, -25)[1], 'x %+.0f' % x)
        c.drawCentredString(P(x, disc_r(i) + 7)[0], P(x, disc_r(i) + 7)[1],
                            '%s sensor bkt' % SYM[i])

    # end markers -- the pattern is NOT symmetric, so a flipped plate is scrap
    c.setFont('Helvetica-Bold', 8); c.setFillColorRGB(*BLU)
    c.drawString(P(PX0 + 5, 64)[0], P(PX0 + 5, 64)[1], 'M2 / LEFT END')
    c.drawRightString(P(PX1 - 5, 64)[0], P(PX1 - 5, 64)[1],
                      'PEN + DRUM END \u2192')
    c.setFont('Helvetica-Bold', 7)
    c.drawString(P(PX0 + 5, -64)[0], P(PX0 + 5, -64)[1],
                 'FRONT FACE UP  (this side faces the pen)')

    # ---- dimensions
    c.setStrokeColorRGB(*BLU); c.setFillColorRGB(*BLU); c.setLineWidth(0.4)

    def dim_h(x0, x1, y, label, tick=2.0):
        q0, q1 = P(x0, y), P(x1, y)
        c.line(q0[0], q0[1], q1[0], q1[1])
        for q in (q0, q1):
            c.line(q[0], q[1] - tick * mm, q[0], q[1] + tick * mm)
        c.setFont('Helvetica', 6.5)
        c.drawCentredString((q0[0] + q1[0]) / 2.0, q0[1] + 1.5 * mm, label)

    def dim_v(y0, y1, x, label, tick=2.0):
        q0, q1 = P(x, y0), P(x, y1)
        c.line(q0[0], q0[1], q1[0], q1[1])
        for q in (q0, q1):
            c.line(q[0] - tick * mm, q[1], q[0] + tick * mm, q[1])
        c.saveState()
        c.translate(q0[0], (q0[1] + q1[1]) / 2.0); c.rotate(90)
        c.setFont('Helvetica', 6.5); c.drawCentredString(0, 1.2 * mm, label)
        c.restoreState()

    chain = [PX0] + XS + [PX1]
    for a, b in zip(chain, chain[1:]):
        g = b - a
        dim_h(a, b, -34, ('%.0f' if abs(g - round(g)) < 1e-6 else '%.2f') % g)
    if full:                        # a clipped tile would show half a dimension
        dim_h(PX0, PX1, PY0 - 13, 'OVERALL  %.0f' % PW, 3.0)
        dim_v(PY0, PY1, PX0 - 13, 'OVERALL  %.0f' % PH, 3.0)
    dim_v(0, SCREW_Y, PX0 + 30, 'frame screw row  %.0f' % SCREW_Y)
    dim_h(XS[0] - MOTOR_PCD / 2, XS[0] + MOTOR_PCD / 2, 12,
          'motor PCD %.0f' % MOTOR_PCD)
    dim_h(XS[0] - SENSOR_PCD / 2, XS[0] + SENSOR_PCD / 2, disc_r(0) + 13,
          'bkt %.0f' % SENSOR_PCD)
    sx = screw_xs()
    dim_h(sx[0], sx[1], PY1 + 7,
          'screw pitch %.2f  (%d equal)' % (sx[1] - sx[0], len(sx) - 1))

def scale_bar(c, x, y):
    c.setStrokeColorRGB(*BLK); c.setFillColorRGB(*BLK); c.setLineWidth(1.0)
    c.line(x, y, x + 100 * mm, y)
    for t in range(0, 101, 10):
        h = 2.6 if t % 50 == 0 else 1.6
        c.line(x + t * mm, y - h * mm, x + t * mm, y + h * mm)
    c.setFont('Helvetica-Bold', 7.5)
    c.drawString(x + 103 * mm, y - 1.3 * mm,
                 'THIS BAR IS 100 mm \u2014 measure it before trusting this sheet')

def title_block(c, x, y, extra):
    """Draws downward from (x, y). Returns the y of the last line."""
    c.setFillColorRGB(*BLK)
    c.setFont('Helvetica-Bold', 12)
    c.drawString(x, y, 'TIDE MACHINE  \u2014  FACEPLATE')
    c.setFont('Helvetica', 8)
    lines = [
        'Material   1.5 mm sheet, aluminium or mild steel.   %.0f \u00d7 %.0f mm.  '
        'Deburr both faces; no finish required.' % (PW, PH),
        'Origin   (0, 0) is the M2 motor shaft. y = 0 is the crank centreline, '
        'shared by all five stations.',
        'Holes   5 \u00d7 \u00d8%.1f shaft clearance    10 \u00d7 \u00d8%.1f motor M3 '
        '(%.0f PCD, on y = 0)' % (SHAFT_CLR, MOTOR_HOLE, MOTOR_PCD),
        '             10 \u00d7 \u00d8%.1f sensor-bracket M3    %d \u00d7 \u00d8%.1f frame screw, '
        '#6 clearance, on y = \u00b1%.0f' % (SENSOR_HOLE, 2 * len(screw_xs()),
                                            PLATE_SCREW, SCREW_Y),
        'Asymmetric   the station pattern is not centred \u2014 a mirrored plate is '
        'scrap. M2 end on the left, front face up.',
        'PRINT AT 100% / ACTUAL SIZE.   Any "fit to page" or "shrink to printable '
        'area" destroys the 1:1 scale.',
    ] + extra
    for k, s in enumerate(lines):
        c.drawString(x, y - (5.5 + 4.4 * k) * mm, s)
    return y - (5.5 + 4.4 * len(lines)) * mm

def hole_schedule(c, W, H):
    c.setFillColorRGB(*BLK); c.setFont('Helvetica-Bold', 12)
    c.drawString(20 * mm, H - 18 * mm, 'FACEPLATE \u2014 HOLE SCHEDULE')
    c.setFont('Helvetica', 8)
    c.drawString(20 * mm, H - 24 * mm,
                 'Ordinates in mm from the M2 shaft centre, %d holes. For hand-marking, '
                 'or for checking the DXF opened right.' % len(holes))
    rows = sorted(holes, key=lambda h: (-h[2], h[0], h[1]))
    per = 18
    cols = (len(rows) + per - 1) // per
    for ci in range(cols):
        cx = (22 + ci * 76) * mm
        cy = H - 34 * mm
        c.setFont('Helvetica-Bold', 7.5)
        c.drawString(cx, cy, 'X'); c.drawString(cx + 17 * mm, cy, 'Y')
        c.drawString(cx + 33 * mm, cy, '\u00d8'); c.drawString(cx + 42 * mm, cy, 'purpose')
        c.setLineWidth(0.4); c.setStrokeColorRGB(*BLK)
        c.line(cx, cy - 1.4 * mm, cx + 60 * mm, cy - 1.4 * mm)
        c.setFont('Helvetica', 7)
        for ri, (hx, hy, d, n) in enumerate(rows[ci * per:(ci + 1) * per]):
            ry = cy - (5.0 + ri * 4.2) * mm
            c.drawRightString(cx + 13 * mm, ry, '%+.2f' % hx)
            c.drawRightString(cx + 30 * mm, ry, '%+.2f' % hy)
            c.drawRightString(cx + 39 * mm, ry, '%.1f' % d)
            c.drawString(cx + 42 * mm, ry, n)
    ty = H - 34 * mm - (5.0 + per * 4.2) * mm - 10 * mm
    c.setFont('Helvetica-Bold', 8)
    c.drawString(22 * mm, ty, 'Tally')
    c.setFont('Helvetica', 8)
    for k, (d, n) in enumerate(sorted(Counter(round(h[2], 2) for h in holes).items())):
        c.drawString(22 * mm, ty - (4.8 + 4.2 * k) * mm, '%2d \u00d7 \u00d8%.1f mm' % (n, d))
    edge = min(min(abs(h[0] - PX0), abs(PX1 - h[0]),
                   abs(h[1] - PY0), abs(PY1 - h[1])) - h[2] / 2.0 for h in holes)
    c.setFont('Helvetica-Bold', 8)
    c.drawString(196 * mm, ty, 'Laser sanity check against 1.5 mm stock')
    c.setFont('Helvetica', 8)
    c.drawString(196 * mm, ty - 4.8 * mm,
                 'smallest hole  %.1f mm  \u2265 t (%.1f)' % (min(h[2] for h in holes), PT))
    c.drawString(196 * mm, ty - 9.0 * mm,
                 'thinnest hole-to-edge wall  %.1f mm  \u2265 t' % edge)
    c.drawString(196 * mm, ty - 13.2 * mm,
                 'geometry all closed: 1 outline + %d circles, nothing else' % len(holes))
    c.drawString(196 * mm, ty - 17.4 * mm,
                 'faceplate_CUT.dxf carries exactly this and no text')

def pdf_a3(path):
    W, H = 420 * mm, 297 * mm                      # A3 landscape
    c = rl_canvas.Canvas(path, pagesize=(W, H))
    c.setTitle('Tide Machine faceplate 1:1 (A3)')
    ox = (W - PW * mm) / 2.0 - PX0 * mm
    oy = H - 32 * mm - PY1 * mm
    draw_plate(c, ox, oy)
    yb = title_block(c, 26 * mm, oy + (PY0 - 30) * mm,
                     ['Sheet 1 of 2 \u2014 A3 landscape, 420 \u00d7 297. Sheet 2 is the hole '
                      'schedule.'])
    scale_bar(c, 26 * mm, yb - 7 * mm)
    c.showPage()
    hole_schedule(c, W, H)
    c.showPage(); c.save()
    return path

def pdf_tiled(path):
    W, H = 279.4 * mm, 215.9 * mm                  # Letter landscape
    SAFE = 12.7                                    # inside any printer's margin
    LAP = 30.0
    c = rl_canvas.Canvas(path, pagesize=(W, H))
    c.setTitle('Tide Machine faceplate 1:1, tiled for Letter')

    yb = title_block(c, SAFE * mm, (H / mm - SAFE) * mm,
                     ['Sheets 2\u20133 are the plate at 1:1, split into two tiles with a '
                      '%.0f mm overlap.' % LAP,
                      'Print both at 100%, trim sheet 3 on its red registration line, and '
                      'tape it over the matching line on sheet 2.',
                      'Then measure the 100 mm bar on BOTH sheets before marking anything.'])
    scale_bar(c, SAFE * mm, yb - 9 * mm)
    c.setFont('Helvetica', 7.5); c.setFillColorRGB(0.35, 0.35, 0.35)
    c.drawString(SAFE * mm, (SAFE + 5) * mm,
                 'Generated from tide_machine.rb \u2014 the model is the source of truth for '
                 'every dimension on these sheets.')
    c.showPage()

    tiles, step = 2, PW / 2.0
    band_h = PH
    bx = SAFE
    by = H / mm - SAFE - 7.0 - band_h - PY1 + PY1   # top of band under the header
    by = H / mm - SAFE - 7.0 - band_h
    for t in range(tiles):
        cut0 = PX0 + t * step - (LAP if t else 0.0)
        cut1 = PX0 + (t + 1) * step + (LAP if t < tiles - 1 else 0.0)
        ox = (bx - cut0) * mm
        oy = (by - PY0) * mm

        c.saveState()
        p = c.beginPath()
        p.rect(bx * mm, (by - 30) * mm, (cut1 - cut0) * mm, (band_h + 34) * mm)
        c.clipPath(p, stroke=0, fill=0)
        draw_plate(c, ox, oy, full=False)
        c.restoreState()

        c.setStrokeColorRGB(*RED); c.setLineWidth(0.5); c.setFillColorRGB(*RED)
        seams = ([cut1 - LAP / 2.0] if t < tiles - 1 else []) + \
                ([cut0 + LAP / 2.0] if t else [])
        for sxm in seams:
            px = ox + sxm * mm
            c.setDash(4, 3)
            c.line(px, (by - 5) * mm, px, (by + band_h + 3) * mm)
            c.setDash()
            for yy in (by - 5, by + band_h + 3):
                c.circle(px, yy * mm, 2.2 * mm, stroke=1, fill=0)
                c.line(px - 3.6 * mm, yy * mm, px + 3.6 * mm, yy * mm)
                c.line(px, yy * mm - 3.6 * mm, px, yy * mm + 3.6 * mm)
            c.saveState()
            c.translate(px - 1.5 * mm, (by + band_h * 0.30) * mm); c.rotate(90)
            c.setFont('Helvetica-Bold', 7)
            c.drawCentredString(0, 0, 'REGISTRATION \u2014 trim / align here')
            c.restoreState()

        c.setFillColorRGB(*BLK); c.setFont('Helvetica-Bold', 9)
        c.drawString(bx * mm, (H / mm - SAFE - 3) * mm,
                     'FACEPLATE 1:1   TILE %d of %d   x %+.0f to %+.0f mm   '
                     'print at 100%%, do not scale' % (t + 1, tiles, cut0, cut1))
        scale_bar(c, bx * mm, (by - 20) * mm)
        c.showPage()
    c.save()
    return path

# ---------------------------------------------------------------- run
made = [dxf(os.path.join(OUT, 'faceplate_CUT.dxf'), False),
        dxf(os.path.join(OUT, 'faceplate_REF.dxf'), True),
        pdf_a3(os.path.join(OUT, 'faceplate_1to1_A3.pdf')),
        pdf_tiled(os.path.join(OUT, 'faceplate_1to1_tiled.pdf'))]

old = os.path.join(OUT, 'faceplate_1to1.pdf')
if os.path.exists(old):
    os.remove(old)

print('plate    : %.1f x %.1f x %.1f mm' % (PW, PH, PT))
print('holes    : %d' % len(holes))
for d, n in sorted(Counter(round(h[2], 2) for h in holes).items()):
    print('    %2d x %.1f' % (n, d))
print('screw xs : %s' % ', '.join('%.2f' % v for v in screw_xs()))
print('disc r   : %s' % ', '.join('%.2f' % disc_r(i) for i in range(len(XS))))
edge = min(min(abs(h[0] - PX0), abs(PX1 - h[0]), abs(h[1] - PY0), abs(PY1 - h[1]))
           - h[2] / 2.0 for h in holes)
print('min hole %.1f >= t %.1f   min wall %.1f >= t   OK'
      % (min(h[2] for h in holes), PT, edge))
print()
for f in made:
    print('%8d B  %s' % (os.path.getsize(f), os.path.basename(f)))

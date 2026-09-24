# -*- coding: utf-8 -*-
"""Rail drawings, generated FROM tide_machine.rb so they cannot drift.

The rails are pine you cut yourself, so these are DRILLING TEMPLATES, not a
vendor cut file. Tape a sheet to the wood, centre-punch, drill.

  rails_1to1_A2.pdf      A2 landscape, every face at 1:1 on one sheet
  rails_1to1_tiled.pdf   cover + 3 Letter tiles, same thing on a home printer
  rails_REF.dxf          all faces on named layers, for your CAD or a router
"""
import io, os, re
from collections import Counter

RB  = r'C:\Users\mikem\Desktop\tide-machine\tide_machine.rb'
OUT = r'C:\Users\mikem\Desktop\tide-machine'

src = io.open(RB, encoding='utf-8').read()
cfg = re.search(r'CFG = \{(.*?)\n  \}', src, re.S).group(1)

def num(k):
    return float(re.search(r':%s\s*=>\s*(-?[\d.]+)' % k, cfg).group(1))

def arr(k):
    return [float(v) for v in
            re.findall(r'-?[\d.]+', re.search(r':%s\s*=>\s*\[([^\]]*)\]' % k, cfg).group(1))]

RX0, RX1 = num('rail_x0'), num('rail_x1')
RZ0, RZ1 = num('rail_z0'), num('rail_z1')
RT       = num('rail_t')            # rail height -- the 19.05 dimension
RY       = num('rail_y')
POST_W   = num('post_w')
ROD_X    = arr('rod_x') + arr('pen_rod_x')
ROD_Z    = num('rod_z')
ROD_D    = num('rod_hole_d')
SOCK     = num('socket_deep')
ROD_LEN  = num('rod_len')
RING_Z   = num('ring_z')
RING_D   = num('ring_hole_d')
RING_DX  = num('ring_dx')
DRUM_X   = num('drum_x')
DRUM_D   = num('drum_shaft_d')
PX0, PX1 = num('plate_x0'), num('plate_x1')
PY1      = num('plate_y1')
SCR_P    = num('screw_pitch')
STATIONS = arr('x') + [num('pen_x')]
SYM      = ['M2', 'S2', 'N2', 'K1', 'O1', 'PEN']

RL       = RX1 - RX0                # 470 rail length
DEPTH    = abs(RZ1 - RZ0)           # 38.1 front-to-rear
POST_L   = 2.0 * RY                 # 140 post length
SCREW_Y  = (RY + PY1) / 2.0
SCREW_IN = SCREW_Y - RY             # how far in from the inner edge
PILOT_D  = 2.0                      # #6 pilot in pine

def screw_xs():
    n = int(round((PX1 - PX0) / SCR_P))
    return [PX0 + 12.0 + (PX1 - PX0 - 24.0) * k / float(n) for k in range(n + 1)]

def ring_pairs():
    return sorted([x + s * RING_DX for x in STATIONS for s in (-1, 1)])

# v is measured FROM THE REAR EDGE -- the face the faceplate screws to
INNER = ([(x, -ROD_Z, ROD_D, 'rod socket') for x in ROD_X]
         + [(x, -RING_Z, RING_D, 'screw-eye pilot') for x in ring_pairs()]
         + [(DRUM_X, -ROD_Z, DRUM_D, 'drum shaft, THROUGH')])
REAR = [(x, SCREW_IN, PILOT_D, 'faceplate pilot') for x in screw_xs()]

from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.units import mm

BLK = (0, 0, 0)
RED = (0.78, 0.16, 0.16)
GRY = (0.62, 0.62, 0.62)
BLU = (0.13, 0.34, 0.66)

def strip(c, ox, oy, height, feats, mirror, title, sub, win, xr=None):
    """One face at 1:1.  ox,oy = the FULL strip's lower-left in page points.
    win = (left_pt, width_mm) of the part actually visible, which is what all
    the text anchors to -- on a tile the full strip's ends are off the page."""
    def du(x):
        return (RX1 - x) if mirror else (x - RX0)

    def P(x, v):
        return (ox + du(x) * mm, oy + v * mm)

    wl, ww = win
    wr = wl + ww * mm
    c.setStrokeColorRGB(*BLK); c.setLineWidth(0.8)
    c.rect(ox, oy, RL * mm, height * mm, stroke=1, fill=0)

    for (x, v, d, note) in feats:
        if xr and not (xr[0] - 1 <= x <= xr[1] + 1):
            continue
        cx, cy = P(x, v)
        c.setStrokeColorRGB(*BLK)
        c.setLineWidth(1.1 if 'THROUGH' in note else 0.7)
        c.circle(cx, cy, d / 2.0 * mm, stroke=1, fill=0)
        if 'THROUGH' in note:
            c.circle(cx, cy, (d / 2.0 + 1.2) * mm, stroke=1, fill=0)
        c.setStrokeColorRGB(*RED); c.setLineWidth(0.3)
        r = max(d * 0.8, 2.2) * mm
        c.line(cx - r, cy, cx + r, cy); c.line(cx, cy - r, cx, cy + r)

    c.setFillColorRGB(*BLU); c.setFont('Helvetica-Bold', 6.5)
    c.drawString(wl + 2 * mm, oy + 1.6 * mm,
                 'REAR EDGE \u2014 the faceplate screws to this face')
    c.drawString(wl + 2 * mm, oy + (height - 3.8) * mm, 'FRONT EDGE')

    # which way machine x runs across the visible window: the whole ballgame
    lo = (RX1 - (wl - ox) / mm) if mirror else (RX0 + (wl - ox) / mm)
    hi = (RX1 - (wr - ox) / mm) if mirror else (RX0 + (wr - ox) / mm)
    c.setFont('Helvetica-Bold', 7); c.setFillColorRGB(*RED)
    c.drawRightString(wr - 2 * mm, oy + 1.6 * mm,
                      'machine x %+0.0f \u2192 %+0.0f   (%s)'
                      % (lo, hi, 'RIGHT TO LEFT' if mirror else 'LEFT TO RIGHT'))

    c.setFillColorRGB(*BLK); c.setFont('Helvetica-Bold', 9)
    c.drawString(wl, oy + (height + 9) * mm, title)
    c.setFont('Helvetica', 7); c.setFillColorRGB(0.3, 0.3, 0.3)
    c.drawString(wl, oy + (height + 4.5) * mm, sub)

    c.setStrokeColorRGB(*GRY); c.setLineWidth(0.25); c.setFillColorRGB(*BLU)
    c.setFont('Helvetica', 5.5)
    for i, x in enumerate(STATIONS):
        if xr and not (xr[0] <= x <= xr[1]):
            continue
        p = P(x, 0)
        c.setDash(3, 2); c.line(p[0], oy, p[0], oy + height * mm); c.setDash()
        c.drawCentredString(p[0], oy - 4.4 * mm, '%s  x%+0.0f' % (SYM[i], x))

def legend(c, x, y):
    c.setFillColorRGB(*BLK); c.setFont('Helvetica-Bold', 8)
    c.drawString(x, y, 'Drill schedule')
    rows = [
        ('7 \u00d7  \u00d8%.1f \u00d7 %.0f deep, BLIND' % (ROD_D, SOCK),
         'guide-rod sockets, %.0f mm from the rear edge' % -ROD_Z),
        ('12 \u00d7  \u00d8%.1f \u00d7 %.0f deep' % (RING_D, SOCK),
         'screw-eye pilots, %.0f mm from the rear edge' % -RING_Z),
        ('1 \u00d7  \u00d8%.1f THROUGH (%.2f)' % (DRUM_D, RT),
         'drum shaft at x %+.1f, both rails' % DRUM_X),
        ('5 \u00d7  \u00d8%.1f \u00d7 ~10 deep' % PILOT_D,
         'faceplate pilots \u2014 REAR face, %.0f mm in from the inner edge' % SCREW_IN),
    ]
    for k, (a, b) in enumerate(rows):
        yy = y - (5.0 + 4.4 * k) * mm
        c.setFont('Helvetica', 7.5); c.setFillColorRGB(*BLK); c.drawString(x, yy, a)
        c.setFillColorRGB(0.35, 0.35, 0.35); c.drawString(x + 46 * mm, yy, b)
    yy = y - (5.0 + 4.4 * len(rows)) * mm
    c.setFillColorRGB(*BLK); c.setFont('Helvetica-Oblique', 7)
    c.drawString(x, yy - 2 * mm,
                 'The screw-eye pilots leave only %.1f mm of wood to the front edge \u2014 '
                 'drill them square or pine will blow out.' % (DEPTH + RING_Z))
    return yy - 2 * mm

def cutlist(c, x, y):
    c.setFillColorRGB(*BLK); c.setFont('Helvetica-Bold', 8)
    c.drawString(x, y, 'Cut list')
    c.setFont('Helvetica', 7.5)
    rows = [
        '2 \u00d7 rail   1\u00d72 pine, %.0f mm  (%.2f \u00d7 %.1f actual)' % (RL, RT, DEPTH),
        '2 \u00d7 post   1\u00d72 pine, %.0f mm  \u2014 stands between the rails' % POST_L,
        '7 \u00d7 rod    \u00d85 mm, %.0f mm  \u2014 socket bottom to socket bottom' % ROD_LEN,
        'One 8 ft 1\u00d72 covers all four wood parts (%.0f mm needed).'
        % (2 * RL + 2 * POST_L),
    ]
    for k, s in enumerate(rows):
        c.drawString(x, y - (5.0 + 4.4 * k) * mm, s)
    return y - (5.0 + 4.4 * len(rows)) * mm

def ordinates(c, x, y):
    c.setFillColorRGB(*BLK); c.setFont('Helvetica-Bold', 8)
    c.drawString(x, y, 'Ordinates  (machine x, mm; measure rather than trust the print)')
    cols = [('Rod sockets  \u00d8%.1f, v %.0f' % (ROD_D, -ROD_Z),
             ['%+.0f' % v for v in ROD_X] + ['\u2014'] * 5),
            ('Screw eyes  \u00d8%.1f, v %.0f' % (RING_D, -RING_Z),
             ['%+.0f' % v for v in ring_pairs()]),
            ('Faceplate pilots  \u00d8%.1f, v %.0f' % (PILOT_D, SCREW_IN),
             ['%+.2f' % v for v in screw_xs()]),
            ('Drum shaft  \u00d8%.1f, v %.0f' % (DRUM_D, -ROD_Z),
             ['%+.1f  THROUGH' % DRUM_X])]
    for ci, (hdr, vals) in enumerate(cols):
        cx = x + ci * 46 * mm
        c.setFont('Helvetica-Bold', 7); c.setFillColorRGB(*BLK)
        c.drawString(cx, y - 5 * mm, hdr)
        c.setLineWidth(0.4); c.line(cx, y - 6.4 * mm, cx + 42 * mm, y - 6.4 * mm)
        c.setFont('Helvetica', 7)
        for ri, v in enumerate(vals):
            c.drawString(cx, y - (10.0 + 4.0 * ri) * mm, v)
    return y - (10.0 + 4.0 * 12) * mm

def handed(c, x, y):
    c.setFillColorRGB(*RED); c.setFont('Helvetica-Bold', 8.5)
    c.drawString(x, y, 'THE TWO RAILS ARE MIRROR IMAGES. Use the template with the '
                       'matching name.')
    c.setFillColorRGB(*BLK); c.setFont('Helvetica', 7.5)
    rows = [
        'Both rails carry the same features at the same machine (x, z) \u2014 but each is '
        'drilled on its INNER face, the one that looks',
        'at the other rail. Laying the top rail inner-face-up turns it over, so with the '
        'rear edge toward you on both, machine x',
        'runs left-to-right on one rail and right-to-left on the other. Drill both from '
        'one template and the second rail is scrap.',
        'Each template names its rail and states which way x runs. Register the REAR EDGE '
        'first, then the end.',
    ]
    for k, s in enumerate(rows):
        c.drawString(x, y - (5.0 + 4.0 * k) * mm, s)
    return y - (5.0 + 4.0 * len(rows)) * mm

def scale_bar(c, x, y):
    c.setStrokeColorRGB(*BLK); c.setFillColorRGB(*BLK); c.setLineWidth(1.0)
    c.line(x, y, x + 100 * mm, y)
    for t in range(0, 101, 10):
        h = 2.6 if t % 50 == 0 else 1.6
        c.line(x + t * mm, y - h * mm, x + t * mm, y + h * mm)
    c.setFont('Helvetica-Bold', 7.5)
    c.drawString(x + 103 * mm, y - 1.3 * mm,
                 'THIS BAR IS 100 mm \u2014 measure it before trusting this sheet')

INNER_SUB = ('inner face, %.0f \u00d7 %.2f. 7 blind rod sockets, 12 screw-eye pilots, '
             '1 through hole for the drum shaft.' % (RL, DEPTH))
REAR_SUB  = ('rear face, %.0f \u00d7 %.2f. The SAME for both rails \u2014 the pilots sit %.0f mm '
             'in from the inner edge either way.' % (RL, RT, SCREW_IN))

def pdf_a2(path):
    W, H = 594 * mm, 420 * mm
    c = rl_canvas.Canvas(path, pagesize=(W, H))
    c.setTitle('Tide Machine rails 1:1 (A2)')
    ox = (W - RL * mm) / 2.0
    full = (ox, RL)

    c.setFillColorRGB(*BLK); c.setFont('Helvetica-Bold', 13)
    c.drawString(ox, H - 16 * mm,
                 'TIDE MACHINE  \u2014  RAILS AND FRAME    drilling templates, 1:1')
    c.setFont('Helvetica', 8)
    c.drawString(ox, H - 22 * mm,
                 '1\u00d72 pine. Templates, not a cut file \u2014 tape a sheet to the wood, '
                 'centre-punch every cross, then drill.   PRINT AT 100% / ACTUAL SIZE.')

    y = H - 36 * mm - DEPTH * mm
    strip(c, ox, y, DEPTH, INNER, False,
          'TOP RAIL \u2014 inner face (drill this face)', INNER_SUB, full)
    y = y - 22 * mm - DEPTH * mm
    strip(c, ox, y, DEPTH, INNER, True,
          'BOTTOM RAIL \u2014 inner face (drill this face)', INNER_SUB, full)
    y = y - 22 * mm - RT * mm
    strip(c, ox, y, RT, REAR, False, 'EITHER RAIL \u2014 rear face', REAR_SUB, full)

    y = y - 26 * mm - DEPTH * mm
    c.setStrokeColorRGB(*BLK); c.setLineWidth(0.8)
    c.rect(ox, y, POST_L * mm, DEPTH * mm, stroke=1, fill=0)
    c.setFillColorRGB(*BLK); c.setFont('Helvetica-Bold', 9)
    c.drawString(ox, y + (DEPTH + 5) * mm, 'END POST \u2014 2 off, blank')
    c.setFont('Helvetica', 7); c.setFillColorRGB(0.3, 0.3, 0.3)
    for k, s in enumerate([
            '%.0f \u00d7 %.1f from the same 1\u00d72. Stands on end between the rails and '
            'closes the box.' % (POST_L, DEPTH),
            'No joinery drawn \u2014 that is still an open item. Fit the rails and rods dry, '
            'get it square,',
            'then fasten the posts to whatever you have.']):
        c.drawString(ox + (POST_L + 10) * mm, y + (DEPTH - 6 - 5 * k) * mm, s)

    yb = handed(c, ox, y - 14 * mm)
    y2 = legend(c, ox, yb - 8 * mm)
    cutlist(c, ox + 250 * mm, yb - 8 * mm)
    y3 = ordinates(c, ox, y2 - 10 * mm)
    scale_bar(c, ox + 250 * mm, y3 + 30 * mm)
    c.showPage(); c.save()
    return path

def pdf_tiled(path):
    W, H = 279.4 * mm, 215.9 * mm
    SAFE, LAP, TILES = 12.7, 30.0, 3
    c = rl_canvas.Canvas(path, pagesize=(W, H))
    c.setTitle('Tide Machine rails 1:1, tiled for Letter')

    c.setFillColorRGB(*BLK); c.setFont('Helvetica-Bold', 12)
    c.drawString(SAFE * mm, (H / mm - SAFE) * mm,
                 'TIDE MACHINE  \u2014  RAILS AND FRAME    drilling templates, 1:1')
    c.setFont('Helvetica', 8)
    for k, s in enumerate([
            '1\u00d72 pine, %.2f \u00d7 %.1f actual. Two rails %.0f mm long plus two %.0f mm '
            'end posts.' % (RT, DEPTH, RL, POST_L),
            'Templates, not a cut file \u2014 tape a sheet to the wood, centre-punch every '
            'cross, then drill.',
            'Sheets 2\u20134 carry the rail at 1:1 in three tiles with a %.0f mm overlap; '
            'each tile shows all three faces.' % LAP,
            'Print at 100%, trim each tile on its red registration line, and tape the run '
            'together before marking anything.']):
        c.drawString(SAFE * mm, (H / mm - SAFE - 6 - 4.4 * k) * mm, s)
    yb = handed(c, SAFE * mm, (H / mm - SAFE - 32) * mm)
    y2 = legend(c, SAFE * mm, yb - 8 * mm)
    cutlist(c, SAFE * mm, y2 - 10 * mm)
    scale_bar(c, SAFE * mm, (SAFE + 5) * mm)
    c.showPage()

    step = RL / TILES
    for t in range(TILES):
        c0 = RX0 + t * step - (LAP if t else 0.0)
        c1 = RX0 + (t + 1) * step + (LAP if t < TILES - 1 else 0.0)
        c.setFillColorRGB(*BLK); c.setFont('Helvetica-Bold', 9)
        c.drawString(SAFE * mm, (H / mm - SAFE - 2) * mm,
                     'RAILS 1:1   TILE %d of %d   machine x %+0.0f to %+0.0f   '
                     'print at 100%%, do not scale' % (t + 1, TILES, c0, c1))

        rows = [(DEPTH, INNER, False, 'TOP RAIL \u2014 inner face', INNER_SUB),
                (DEPTH, INNER, True,  'BOTTOM RAIL \u2014 inner face', INNER_SUB),
                (RT,    REAR,  False, 'EITHER RAIL \u2014 rear face', REAR_SUB)]
        y = H / mm - SAFE - 22.0
        for (ht, feats, mir, ttl, sub) in rows:
            y -= ht
            d0 = (RX1 - c1) if mir else (c0 - RX0)
            d1 = (RX1 - c0) if mir else (c1 - RX0)
            ox = SAFE * mm - d0 * mm
            c.saveState()
            p = c.beginPath()
            p.rect(SAFE * mm, (y - 7) * mm, (d1 - d0) * mm, (ht + 20) * mm)
            c.clipPath(p, stroke=0, fill=0)
            strip(c, ox, y * mm, ht, feats, mir, ttl, sub,
                  (SAFE * mm, d1 - d0), xr=(c0, c1))
            c.restoreState()
            y -= 20.0

        c.setStrokeColorRGB(*RED); c.setLineWidth(0.5); c.setFillColorRGB(*RED)
        for edge, here in ((c1 - LAP / 2.0, t < TILES - 1), (c0 + LAP / 2.0, bool(t))):
            if not here:
                continue
            px = SAFE * mm + (edge - c0) * mm
            c.setDash(4, 3)
            c.line(px, (y + 6) * mm, px, (H / mm - SAFE - 6) * mm)
            c.setDash()
            for yy in (y + 6, H / mm - SAFE - 6):
                c.circle(px, yy * mm, 2.2 * mm, stroke=1, fill=0)
                c.line(px - 3.6 * mm, yy * mm, px + 3.6 * mm, yy * mm)
                c.line(px, yy * mm - 3.6 * mm, px, yy * mm + 3.6 * mm)
            c.saveState()
            c.translate(px - 1.5 * mm, (y + 26) * mm); c.rotate(90)
            c.setFont('Helvetica-Bold', 6.5)
            c.drawCentredString(0, 0, 'REGISTRATION \u2014 trim / align here')
            c.restoreState()

        scale_bar(c, SAFE * mm, (SAFE + 3) * mm)
        c.showPage()
    c.save()
    return path

# ---------------------------------------------------------------- DXF (R12)
def dxf(path):
    ents = []
    def circle(layer, x, y, d):
        ents.append(('CIRCLE', layer, x, y, d / 2.0))
    def poly(layer, pts):
        ents.append(('POLYLINE', layer, pts))
    def text(layer, x, y, h, s):
        ents.append(('TEXT', layer, x, y, h, s))

    bands = [('TOP_INNER', 0.0,    DEPTH, INNER, False,
              'TOP RAIL inner face -- machine x LEFT to RIGHT (%+.0f at u=0)' % RX0),
             ('BOT_INNER', -60.0,  DEPTH, INNER, True,
              'BOTTOM RAIL inner face -- machine x RIGHT to LEFT (%+.0f at u=0)' % RX1),
             ('REAR_FACE', -120.0, RT,    REAR,  False,
              'EITHER RAIL rear face -- faceplate pilots, %.0f mm in from the inner edge'
              % SCREW_IN)]
    for (layer, y0, ht, feats, mir, note) in bands:
        poly(layer, [(0.0, y0), (RL, y0), (RL, y0 + ht), (0.0, y0 + ht)])
        for (x, v, d, _n) in feats:
            circle(layer, (RX1 - x) if mir else (x - RX0), y0 + v, d)
        text('REF_TEXT', 0.0, y0 + ht + 5.0, 4.0, note)
        text('REF_TEXT', 0.0, y0 - 7.0, 3.0,
             'v is measured from the REAR EDGE, which is the band line at y = %.1f' % y0)
    poly('POST', [(0.0, -180.0), (POST_L, -180.0), (POST_L, -180.0 + DEPTH),
                  (0.0, -180.0 + DEPTH)])
    text('REF_TEXT', 0.0, -180.0 + DEPTH + 5.0, 4.0,
         'END POST x2 -- %.0f long, blank (joinery still open)' % POST_L)
    text('REF_TEXT', 0.0, -200.0, 4.0,
         'Rails are wood you cut: these bands are drilling references, not a cut file.')

    xs = [e[2] for e in ents if e[0] != 'POLYLINE'] + \
         [p[0] for e in ents if e[0] == 'POLYLINE' for p in e[2]]
    ys = [e[3] for e in ents if e[0] != 'POLYLINE'] + \
         [p[1] for e in ents if e[0] == 'POLYLINE' for p in e[2]]

    o = []
    def t(code, val):
        o.append('%d\n%s' % (code, val))
    t(0, 'SECTION'); t(2, 'HEADER')
    t(9, '$ACADVER');     t(1, 'AC1009')
    t(9, '$INSUNITS');    t(70, '4')
    t(9, '$MEASUREMENT'); t(70, '1')
    t(9, '$LUNITS');      t(70, '2')
    t(9, '$EXTMIN'); t(10, '%.4f' % min(xs)); t(20, '%.4f' % min(ys)); t(30, '0.0')
    t(9, '$EXTMAX'); t(10, '%.4f' % max(xs)); t(20, '%.4f' % max(ys)); t(30, '0.0')
    t(0, 'ENDSEC')

    layers = ['TOP_INNER', 'BOT_INNER', 'REAR_FACE', 'POST', 'REF_TEXT']
    t(0, 'SECTION'); t(2, 'TABLES')
    t(0, 'TABLE'); t(2, 'LAYER'); t(70, str(len(layers)))
    for k, name in enumerate(layers):
        t(0, 'LAYER'); t(2, name); t(70, '0')
        t(62, str([5, 3, 4, 6, 2][k])); t(6, 'CONTINUOUS')
    t(0, 'ENDTAB'); t(0, 'ENDSEC')

    t(0, 'SECTION'); t(2, 'ENTITIES')
    for e in ents:
        if e[0] == 'POLYLINE':
            _k, layer, pts = e
            t(0, 'POLYLINE'); t(8, layer); t(66, '1'); t(70, '1')
            t(10, '0.0'); t(20, '0.0'); t(30, '0.0')
            for (vx, vy) in pts:
                t(0, 'VERTEX'); t(8, layer)
                t(10, '%.4f' % vx); t(20, '%.4f' % vy); t(30, '0.0')
            t(0, 'SEQEND'); t(8, layer)
        elif e[0] == 'CIRCLE':
            _k, layer, x, y, r = e
            t(0, 'CIRCLE'); t(8, layer)
            t(10, '%.4f' % x); t(20, '%.4f' % y); t(30, '0.0'); t(40, '%.4f' % r)
        else:
            _k, layer, x, y, h, s = e
            t(0, 'TEXT'); t(8, layer)
            t(10, '%.4f' % x); t(20, '%.4f' % y); t(30, '0.0')
            t(40, '%.2f' % h); t(1, s)
    t(0, 'ENDSEC'); t(0, 'EOF')
    io.open(path, 'w', encoding='ascii', newline='\r\n').write('\n'.join(o) + '\n')
    return path

made = [pdf_a2(os.path.join(OUT, 'rails_1to1_A2.pdf')),
        pdf_tiled(os.path.join(OUT, 'rails_1to1_tiled.pdf')),
        dxf(os.path.join(OUT, 'rails_REF.dxf'))]

print('rail     : %.0f long, %.2f x %.1f section (1x2 pine)' % (RL, RT, DEPTH))
print('post     : %.0f long, 2 off' % POST_L)
print('inner face: %d holes' % len(INNER))
for d, n in sorted(Counter(round(h[2], 2) for h in INNER).items()):
    print('    %2d x %.1f' % (n, d))
print('rear face : %d x %.1f at %.0f mm in from the inner edge'
      % (len(REAR), PILOT_D, SCREW_IN))
print('rod sockets  x %s   v %.0f' % (', '.join('%+.0f' % x for x in ROD_X), -ROD_Z))
print('eye pilots   x %s   v %.0f' % (', '.join('%+.0f' % x for x in ring_pairs()), -RING_Z))
print('margins   : rod %.1f to front / %.1f to rear;  eye %.1f to front / %.1f to rear'
      % (DEPTH + ROD_Z, -ROD_Z, DEPTH + RING_Z, -RING_Z))
mind = min(abs(a - b) for i, a in enumerate(ring_pairs() + ROD_X)
           for b in (ring_pairs() + ROD_X)[i + 1:]) if True else 0
print('closest two inner-face centres: %.1f mm apart' % mind)
print()
for f in made:
    print('%8d B  %s' % (os.path.getsize(f), os.path.basename(f)))

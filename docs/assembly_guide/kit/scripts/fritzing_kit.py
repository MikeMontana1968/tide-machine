#!/usr/bin/env python3
"""
fritzing_kit.py -- write a Fritzing sketch (.fzz) from Python, with every part a
custom part carried inside the file, so every pin position is known and every
wire lands on its pin. Pair with Fritzing's headless export:

    & 'C:\Program Files\Fritzing\Fritzing.exe' -svg <folder>   # SVG of every view

Typical project script (see references/examples/startracker_gen_fritzing.py):

    import fritzing_kit as FK
    ctrl = FK.board_part('board.kicad_pcb', 'My controller', harness={...})
    bat = FK.Part('battery', 'Battery 12 V', 'BT', 120, 62, art_svg)   # mm art
    bat.conn('+', 'positive', 18, 2, 'R', 0)
    S = FK.Sketch()
    a = S.place(ctrl, (0, 0), (0, 0), (0, 0))         # breadboard, schematic, pcb (mm)
    b = S.place(bat, (-200, 20), FK.level(...), (-80, 0))
    S.wire(b, '+', a, 'J1.1 +12V', FK.RED, sag=-14)
    S.save('wiring.fzz')

Conventions that make it work:
  - part SVGs are authored in mm; Fritzing's scene is 90 px/in (MM below)
  - a wire's geometry is absolute scene px from its connector0 end; bezier
    control points are relative to that start
  - breadboard wires carry wireFlags 64, schematic traces 128
  - embedded parts live in the zip as part.<moduleId>.fzp and
    svg.<view>.<file>.svg; the instance path is the .fzp name without 'part.'
  - both ends of every connection are written (part side and wire side)
"""
import math
import os
import sys
import zipfile
from xml.sax.saxutils import escape

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kicad_board as KB  # noqa: E402
from kicad_board import rot, load_board  # noqa: E402,F401
MM = 90 / 25.4          # scene px per mm
PROJECT = 'flatpack'    # set from the project's generator: names the custom parts (moduleIds, file names, family)
SCH_P = 2.54            # schematic pin pitch, mm (0.1 in grid)

# wire colours (Fritzing's own palette names in the comments)
RED, BLACK, BLUE, YELLOW, GREEN = '#cc1414', '#404040', '#418dd9', '#ffe24d', '#47cc79'
ORANGE, PURPLE, WHITE, GREY = '#ef6100', '#ab58a2', '#ffffff', '#999999'


def f(v):
    return ('%.3f' % v).rstrip('0').rstrip('.')



def f(v):
    return ('%.3f' % v).rstrip('0').rstrip('.')


def arc_path(s, m, e):
    """SVG arc through three points."""
    (x1, y1), (x2, y2), (x3, y3) = s, m, e
    d = 2 * (x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))
    if abs(d) < 1e-9:
        return 'M%s %sL%s %s' % (f(x1), f(y1), f(x3), f(y3))
    ux = ((x1**2 + y1**2) * (y2 - y3) + (x2**2 + y2**2) * (y3 - y1) + (x3**2 + y3**2) * (y1 - y2)) / d
    uy = ((x1**2 + y1**2) * (x3 - x2) + (x2**2 + y2**2) * (x1 - x3) + (x3**2 + y3**2) * (x2 - x1)) / d
    r = math.hypot(x1 - ux, y1 - uy)
    cross = (x2 - x1) * (y3 - y1) - (y2 - y1) * (x3 - x1)
    sweep = 1 if cross > 0 else 0
    a1, a3 = math.atan2(y1 - uy, x1 - ux), math.atan2(y3 - uy, x3 - ux)
    a2 = math.atan2(y2 - uy, x2 - ux)
    span = (a3 - a1) % (2 * math.pi) if sweep else (a1 - a3) % (2 * math.pi)
    large = 1 if span > math.pi else 0
    return 'M%s %sA%s %s 0 %d %d %s %s' % (f(x1), f(y1), f(r), f(r), large, sweep, f(x3), f(y3))


class Part:
    def __init__(self, key, title, label, w, h, art, desc=''):
        self.key, self.title, self.label, self.w, self.h, self.art, self.desc = key, title, label, w, h, art, desc
        self.conns = []         # (name, description, bb x, bb y, schematic side)
        self.sch_left, self.sch_right = [], []

    def conn(self, name, desc, x, y, side, slot=None):
        cid = 'connector%d' % len(self.conns)
        self.conns.append(dict(id=cid, name=name, desc=desc, x=x, y=y, side=side))
        (self.sch_left if side == 'L' else self.sch_right).append((cid, name, slot))
        return cid

    @property
    def module_id(self):
        return '%s_%s_v1' % (PROJECT, self.key)

    # -- files -------------------------------------------------------------
    def fn(self, view):
        return '%s_%s_%s.svg' % (PROJECT, self.key, view)

    def fzp(self):
        c = []
        for k in self.conns:
            c.append('''  <connector id="%(id)s" name="%(name)s" type="female">
   <description>%(desc)s</description>
   <views>
    <breadboardView><p layer="breadboard" svgId="%(id)spin"/></breadboardView>
    <schematicView><p layer="schematic" svgId="%(id)spin" terminalId="%(id)sterminal"/></schematicView>
    <pcbView><p layer="copper0" svgId="%(id)spin"/><p layer="copper1" svgId="%(id)spin"/></pcbView>
   </views>
  </connector>''' % dict(id=k['id'], name=escape(k['name']), desc=escape(k['desc'])))
        return '''<?xml version="1.0" encoding="UTF-8"?>
<module fritzingVersion="1.0.8" moduleId="%s">
 <version>1</version>
 <author>%s gen_fritzing.py (flatpack-guide kit)</author>
 <title>%s</title>
 <label>%s</label>
 <description>%s</description>
 <tags><tag>%s</tag></tags>
 <properties><property name="family">%s</property><property name="variant">%s</property></properties>
 <views>
  <iconView><layers image="icon/%s"><layer layerId="icon"/></layers></iconView>
  <breadboardView><layers image="breadboard/%s"><layer layerId="breadboard"/></layers></breadboardView>
  <schematicView><layers image="schematic/%s"><layer layerId="schematic"/></layers></schematicView>
  <pcbView><layers image="pcb/%s"><layer layerId="copper0"/><layer layerId="silkscreen"/><layer layerId="copper1"/></layers></pcbView>
 </views>
 <connectors>
%s
 </connectors>
</module>
''' % (self.module_id, PROJECT, escape(self.title), self.label, escape(self.desc), PROJECT, PROJECT, self.key,
       self.fn('icon'), self.fn('breadboard'), self.fn('schematic'), self.fn('pcb'), '\n'.join(c))

    def bb_svg(self, layer='breadboard'):
        pins = ''.join('<rect id="%spin" x="%s" y="%s" width="1.2" height="1.2" fill="none" stroke="none"/>'
                       % (k['id'], f(k['x'] - 0.6), f(k['y'] - 0.6)) for k in self.conns)
        return ('<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" '
                'width="%smm" height="%smm" viewBox="0 0 %s %s"><g id="%s">%s%s</g></svg>\n'
                % (f(self.w), f(self.h), f(self.w), f(self.h), layer, self.art, pins))

    # schematic: a box with pins on two sides, 0.1 in grid
    def sch_geom(self):
        nl = max([s for _, _, s in self.sch_left if s is not None] + [len(self.sch_left) - 1, 0]) + 1
        nr = max([s for _, _, s in self.sch_right if s is not None] + [len(self.sch_right) - 1, 0]) + 1
        rows = max(nl, nr, 2)
        longest = max([len(n) for _, n, _ in self.sch_left + self.sch_right] + [6])
        bw = max(6 * SCH_P, math.ceil((longest * 1.6 * (2 if self.sch_left and self.sch_right else 1) + 4) / SCH_P) * SCH_P)
        bw = max(bw, math.ceil((len(self.title) * 1.7 + 4) / SCH_P) * SCH_P) if len(self.title) < 34 else bw
        pl = SCH_P * 2
        W = bw + (pl if self.sch_left else 0) + (pl if self.sch_right else 0)
        H = (rows + 2) * SCH_P
        x0 = pl if self.sch_left else 0
        return dict(rows=rows, bw=bw, pl=pl, W=W, H=H, x0=x0)

    def sch_terminal(self, cid):
        g = self.sch_geom()
        for side, lst in (('L', self.sch_left), ('R', self.sch_right)):
            for i, (c, n, slot) in enumerate(lst):
                if c == cid:
                    row = slot if slot is not None else i
                    y = (row + 1.5) * SCH_P
                    return (0.0 if side == 'L' else g['W']), y
        raise KeyError(cid)

    def sch_svg(self):
        g = self.sch_geom()
        x0, bw, pl, W, H = g['x0'], g['bw'], g['pl'], g['W'], g['H']
        s = ['<rect x="%s" y="%s" width="%s" height="%s" fill="#FFFFFF" stroke="#000000" stroke-width="0.25"/>'
             % (f(x0), f(SCH_P * 0.5), f(bw), f(H - SCH_P))]
        s.append('<text x="%s" y="%s" font-family="Droid Sans, Noto Sans, Arial, sans-serif" font-size="2.2" text-anchor="middle" fill="#000000">%s</text>'
                 % (f(x0 + bw / 2), f(SCH_P * 0.5 - 0.8), escape(self.title)))
        for side, lst in (('L', self.sch_left), ('R', self.sch_right)):
            for i, (c, n, slot) in enumerate(lst):
                row = slot if slot is not None else i
                y = (row + 1.5) * SCH_P
                if side == 'L':
                    xa, xb, tx, anc = 0, pl, pl + 0.8, 'start'
                else:
                    xa, xb, tx, anc = W, W - pl, W - pl - 0.8, 'end'
                s.append('<line id="%spin" x1="%s" y1="%s" x2="%s" y2="%s" stroke="#555555" stroke-width="0.25"/>'
                         % (c, f(xa), f(y), f(xb), f(y)))
                s.append('<rect id="%sterminal" x="%s" y="%s" width="0.01" height="0.01" fill="none"/>' % (c, f(xa - 0.005), f(y - 0.005)))
                s.append('<text x="%s" y="%s" font-family="Droid Sans, Noto Sans, Arial, sans-serif" font-size="1.7" text-anchor="%s" fill="#555555">%s</text>'
                         % (f(tx), f(y + 0.6), anc, escape(n)))
        return ('<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="%smm" height="%smm" '
                'viewBox="0 0 %s %s"><g id="schematic">%s</g></svg>\n' % (f(W), f(H), f(W), f(H), ''.join(s)))

    def pcb_svg(self):
        n = len(self.conns)
        W, H = max(n * 2.54, 2.54) + 2, 4.54
        pads = ''.join('<circle id="%spin" cx="%s" cy="2.27" r="0.8" fill="none" stroke="#F7BD13" stroke-width="0.5"/>'
                       % (k['id'], f(1 + 1.27 + i * 2.54)) for i, k in enumerate(self.conns))
        return ('<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="%smm" height="%smm" '
                'viewBox="0 0 %s %s"><g id="silkscreen"><rect x="0.2" y="0.2" width="%s" height="%s" fill="none" '
                'stroke="#000000" stroke-width="0.2"/></g><g id="copper1"><g id="copper0">%s</g></g></svg>\n'
                % (f(W), f(H), f(W), f(H), f(W - 0.4), f(H - 0.4), pads))


def text(x, y, s, size=2.2, fill='#ffffff', anchor='middle', weight='bold', rot=0):
    tr = ' transform="rotate(%s %s %s)"' % (f(rot), f(x), f(y)) if rot else ''
    return ('<text x="%s" y="%s" font-family="Droid Sans, Noto Sans, Arial, sans-serif" font-size="%s" font-weight="%s" fill="%s" text-anchor="%s"%s>%s</text>'
            % (f(x), f(y), f(size), weight, fill, anchor, tr, escape(s)))


# --------------------------------------------------------------------------
# a PCB part drawn from its KiCad layout
# --------------------------------------------------------------------------
def edge_box(pcb_path):
    """(x0, y0, x1, y1) of the board's Edge.Cuts, KiCad mm"""
    t = KB.parse(open(pcb_path, encoding='utf8').read())
    xs, ys = [], []
    for n in KB.kids(t, 'gr_rect') + KB.kids(t, 'gr_line'):
        ly = KB.kid(n, 'layer')
        if ly and ly[1] == 'Edge.Cuts':
            for k in ('start', 'end'):
                p = KB.kid(n, k); xs.append(float(p[1])); ys.append(float(p[2]))
    return (min(xs), min(ys), max(xs), max(ys)) if xs else (0.0, 0.0, 100.0, 100.0)


def edge_size(pcb_path):
    x0, y0, x1, y1 = edge_box(pcb_path)
    return x1 - x0, y1 - y0


def load_board_at_origin(pcb_path):
    """load_board(), shifted so the Edge.Cuts corner is (0, 0): part art and crops are then in board mm"""
    fps, pads, silk, texts, segs, vias = load_board(pcb_path)
    ox, oy = edge_box(pcb_path)[:2]
    if not (ox or oy):
        return fps, pads, silk, texts, segs, vias
    sh = lambda q: (q[0] - ox, q[1] - oy)
    fps = {r: (x - ox, y - oy, a, n) for r, (x, y, a, n) in fps.items()}
    for pl in pads.values():
        for q in pl:
            q['x'] -= ox; q['y'] -= oy
    silk = [(g[0], sh(g[1]), g[2]) if g[0] == 'C' else (g[0],) + tuple(sh(q) for q in g[1:]) for g in silk]
    for tx in texts:
        tx['x'] -= ox; tx['y'] -= oy
    segs = [(a - ox, b - oy, c - ox, d - oy, w) for a, b, c, d, w in segs]
    vias = [(x - ox, y - oy) for x, y in vias]
    return fps, pads, silk, texts, segs, vias


def board_art(pcb_path, modules=(), terminal_colour='#2c6fb8'):
    """Breadboard art for a board: green substrate, F.Cu tracks, vias, front
    silkscreen and text, pads; then what stands on it -- screw terminals, pin
    headers, USB-A receptacles -- recognised by footprint name, and any
    modules you describe:
        modules = [dict(sockets=['J20', 'J21'], label='ESP32', kind='esp32'),
                   dict(sockets=['J30', 'J31'], label='TMC2209', kind='stepstick')]
    Returns (svg_art, pads, width_mm, height_mm, usb_mouths)."""
    fps, pads, silk, texts, segs, vias = load_board_at_origin(pcb_path)
    W, H = edge_size(pcb_path)
    a = ['<rect x="0" y="0" width="%s" height="%s" rx="1.5" fill="#1f5c2e" stroke="#123a1c" stroke-width="0.4"/>' % (f(W), f(H))]
    a.append('<g stroke="#2f7a40" stroke-linecap="round" fill="none">%s</g>' % ''.join(
        '<line x1="%s" y1="%s" x2="%s" y2="%s" stroke-width="%s"/>' % (f(x1), f(y1), f(x2), f(y2), f(w)) for x1, y1, x2, y2, w in segs))
    a.append(''.join('<circle cx="%s" cy="%s" r="0.45" fill="#c9a227"/>' % (f(x), f(y)) for x, y in vias))
    sl = []
    for g in silk:
        if g[0] == 'L':
            sl.append('<line x1="%s" y1="%s" x2="%s" y2="%s"/>' % (f(g[1][0]), f(g[1][1]), f(g[2][0]), f(g[2][1])))
        elif g[0] == 'C':
            sl.append('<circle cx="%s" cy="%s" r="%s"/>' % (f(g[1][0]), f(g[1][1]), f(g[2])))
        else:
            sl.append('<path d="%s"/>' % arc_path(g[1], g[2], g[3]))
    a.append('<g stroke="#f2f2f2" stroke-width="0.15" fill="none">%s</g>' % ''.join(sl))
    for tx in texts:
        anc = {'left': 'start', 'right': 'end'}.get(tx['just'], 'middle')
        a.append(text(tx['x'], tx['y'] + tx['size'] * 0.35, tx['s'], size=tx['size'] * 0.95, fill='#f2f2f2',
                      anchor=anc, weight='normal', rot=-tx['a']))
    for ref, pl in pads.items():
        for p in pl:
            if p['num'] == '' or fps[ref][3].startswith('MountingHole'):
                a.append('<circle cx="%s" cy="%s" r="1.6" fill="#ffffff" stroke="#c9a227" stroke-width="1.2"/>' % (f(p['x']), f(p['y'])))
                continue
            r = min(p['w'], p['h']) / 2
            if p['shape'] in ('rect', 'roundrect'):
                a.append('<rect x="%s" y="%s" width="%s" height="%s" fill="#c9a227"/>' % (f(p['x'] - r), f(p['y'] - r), f(2 * r), f(2 * r)))
            else:
                a.append('<circle cx="%s" cy="%s" r="%s" fill="#c9a227"/>' % (f(p['x']), f(p['y']), f(r)))
            a.append('<circle cx="%s" cy="%s" r="%s" fill="#0d2413"/>' % (f(p['x']), f(p['y']), f(min(p['drill'] / 2, r * 0.7))))

    usb = {}
    for ref, (_, _, _, name) in fps.items():
        pl = [p for p in pads.get(ref, []) if p['num'] not in ('', 'SH')]
        if not pl:
            continue
        px = [p['x'] for p in pl]; py = [p['y'] for p in pl]
        if 'TerminalBlock' in name:
            a.append('<rect x="%s" y="%s" width="%s" height="%s" rx="0.6" fill="%s" stroke="#1b4a7d" stroke-width="0.3"/>'
                     % (f(min(px) - 2.6), f(min(py) - 4.4), f(max(px) - min(px) + 5.2), f(max(py) - min(py) + 8), terminal_colour))
            for q in pl:
                a.append('<circle cx="%s" cy="%s" r="1.7" fill="#c8ccd0" stroke="#6b7075" stroke-width="0.25"/>' % (f(q['x']), f(q['y'] - 1.2)))
        elif 'PinHeader' in name:
            a.append('<rect x="%s" y="%s" width="%s" height="%s" fill="#1a1a1a"/>'
                     % (f(min(px) - 1.27), f(min(py) - 1.27), f(max(px) - min(px) + 2.54), f(max(py) - min(py) + 2.54)))
            for q in pl:
                a.append('<rect x="%s" y="%s" width="0.64" height="0.64" fill="#e3c35a"/>' % (f(q['x'] - 0.32), f(q['y'] - 0.32)))
        elif 'USB_A' in name:
            ux = (min(px) + max(px)) / 2
            a.append('<rect x="%s" y="-1.5" width="14" height="14" rx="0.5" fill="#b9bec4" stroke="#6b7075" stroke-width="0.3"/>'
                     '<rect x="%s" y="-1.5" width="10" height="3" fill="#2a2a2a"/>' % (f(ux - 7), f(ux - 5)))
            usb[ref] = (ux, 0.0)
    for m in modules:
        pl = sum((pads.get(r, []) for r in m['sockets']), [])
        if not pl:
            continue
        px = [p['x'] for p in pl]; py = [p['y'] for p in pl]
        e = 3 if m.get('kind') == 'esp32' else 2
        x0, y0, x1, y1 = min(px) - e, min(py) - e, max(px) + e, max(py) + e
        fill = {'esp32': '#1b1b1b', 'stepstick': '#6a2c91'}.get(m.get('kind'), '#2b5d8f')
        a.append('<rect x="%s" y="%s" width="%s" height="%s" rx="1" fill="%s" stroke="#000" stroke-width="0.3"/>'
                 % (f(x0), f(y0), f(x1 - x0), f(y1 - y0), fill))
        if m.get('kind') == 'esp32':
            a.append('<rect x="%s" y="%s" width="18" height="16" fill="#9aa3ab" stroke="#6b7075" stroke-width="0.3"/>' % (f(x1 - 24), f(y0 + 4.7)))
        if m.get('kind') == 'stepstick':
            a.append('<rect x="%s" y="%s" width="9" height="9" fill="#7d8388"/>' % (f((x0 + x1) / 2 - 4.5), f((y0 + y1) / 2 - 4.5)))
        a.append(text((x0 + x1) / 2, (y0 + y1) / 2 + 0.8, m.get('label', ''), 2.2))
    return ''.join(a), pads, W, H, usb


def board_part(pcb_path, title, harness, key='controller', modules=(), labels=None, desc=''):
    """A board as a Fritzing part. harness says which connectors wires reach
    and where each pin sits on the schematic symbol:
        harness = {'J1': dict(names=['+12V', 'GND'], side='L', rows=[0, 3]),
                   'J4': dict(names=['A1', 'A2', 'B1', 'B2'], side='R', rows=[0, 1, 2, 3]),
                   'J2': dict(names=['USB-A'], side='R', rows=[8], usb=True)}
    Connector names become '<ref>.<pin> <name>' ('J2 USB-A' for a USB mouth),
    which is what Sketch.wire() takes. labels = {'J1': 'J1 12V IN', ...} puts
    a white tag beside each harness connector."""
    art, pads, W, H, usb = board_art(pcb_path, modules)
    for ref, s in (labels or {}).items():
        q = pads[ref][0]
        a = '<rect x="%s" y="%s" width="%s" height="3.4" rx="0.6" fill="#ffffff" opacity="0.92"/>' % (
            f(q['x'] + 5 - len(s) * 0.9), f(q['y'] - 6.2), f(len(s) * 1.8))
        art += a + text(q['x'] + 5, q['y'] - 3.6, s, 2.2, '#123a1c')
    p = Part(key, title, 'U', W, H, art, desc or 'drawn from %s' % os.path.basename(pcb_path))
    for ref, h in harness.items():
        if h.get('usb'):
            x, y = usb[ref]
            p.conn('%s %s' % (ref, h['names'][0]), h['names'][0], x, y, h['side'], h['rows'][0])
            continue
        for i, n in enumerate(h['names']):
            q = next(pp for pp in pads[ref] if pp['num'] == str(i + 1))
            p.conn('%s.%d %s' % (ref, i + 1, n), '%s pin %d, %s' % (ref, i + 1, n), q['x'], q['y'], h['side'], h['rows'][i])
    return p


def level(board, part, pin, board_pin, left, gap_slots=12):
    """Schematic x, y (mm) for part so its pin sits level with board_pin --
    which makes every schematic trace one straight line. Board at 0, 0."""
    bc = next(k for k in board.conns if k['name'] == board_pin)
    pc = next(k for k in part.conns if k['name'] == pin)
    _, by = board.sch_terminal(bc['id']); _, py = part.sch_terminal(pc['id'])
    x = -gap_slots * SCH_P - part.sch_geom()['W'] if left else board.sch_geom()['W'] + gap_slots * SCH_P
    return x, by - py

def crossings(paths):
    """How many times square-drawn wires cross: each path is a list of points
    joined by horizontal/vertical runs."""
    segs = []
    for w, pts in enumerate(paths):
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            segs.append((w, min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1), abs(y1 - y0) < 1e-6))
    n = 0
    for i, a in enumerate(segs):
        for b in segs[i + 1:]:
            if a[0] == b[0] or a[5] == b[5]:
                continue
            h, v = (a, b) if a[5] else (b, a)
            if h[1] < v[1] < h[3] and v[2] < h[2] < v[4]:
                n += 1
    return n


class Sketch:
    def __init__(self):
        self.idx = 5000
        self.inst = []        # (part, model index, bb xy mm, sch xy mm, pcb xy mm)
        self.links = {}       # (model idx, connector id) -> list of (other idx, other conn, view)
        self.wires = []

    def nid(self):
        self.idx += 1
        return self.idx

    def place(self, part, bb, sch, pcbxy):
        mi = self.nid()
        self.inst.append(dict(part=part, mi=mi, bb=bb, sch=sch, pcb=pcbxy))
        return mi

    def find(self, mi):
        return next(i for i in self.inst if i['mi'] == mi)

    def pin_bb(self, mi, cname):
        i = self.find(mi); c = next(k for k in i['part'].conns if k['name'] == cname)
        return (i['bb'][0] + c['x']) * MM, (i['bb'][1] + c['y']) * MM, c['id']

    def pin_sch(self, mi, cname):
        i = self.find(mi); c = next(k for k in i['part'].conns if k['name'] == cname)
        tx, ty = i['part'].sch_terminal(c['id'])
        return (i['sch'][0] + tx) * MM, (i['sch'][1] + ty) * MM, c['id']

    def link(self, a, ac, b, bc, view):
        self.links.setdefault((a, ac, view), []).append((b, bc))

    def pin_mm(self, mi, cname):
        x, y, _ = self.pin_bb(mi, cname)
        return x / MM, y / MM

    def wire(self, a, an, b, bn, color, sag=0.0, mils=22.2222):
        """one breadboard wire (curved) and one schematic trace, same two pins"""
        x0, y0, ac = self.pin_bb(a, an)
        x1, y1, bc = self.pin_bb(b, bn)
        wb = self.nid()
        dx, dy = x1 - x0, y1 - y0
        self.wires.append(dict(kind='bb', mi=wb, x=x0, y=y0, dx=dx, dy=dy, color=color, mils=mils,
                               cp=((dx * 0.3, dy * 0.3 + sag * MM), (dx * 0.7, dy * 0.7 + sag * MM)),
                               c0=[(a, ac, 'part')], c1=[(b, bc, 'part')]))
        self.link(a, ac, wb, 'connector0', 'bb'); self.link(b, bc, wb, 'connector1', 'bb')
        self.sch_trace(a, an, b, bn)

    def route(self, a, an, b, bn, color, via, mils=22.2222):
        """one breadboard wire drawn square: straight runs through the bend
        points `via` (breadboard mm), chained end to end the way Fritzing
        stores a wire with bendpoints; plus the schematic trace. Prefer this
        to wire() for harnesses: square runs never hide under each other and
        any crossing reads as a crossing."""
        pts = [self.pin_bb(a, an)[:2]] + [(x * MM, y * MM) for x, y in via] + [self.pin_bb(b, bn)[:2]]
        ac, bc = self.pin_bb(a, an)[2], self.pin_bb(b, bn)[2]
        ids = [self.nid() for _ in range(len(pts) - 1)]
        for k, mi in enumerate(ids):
            (x0, y0), (x1, y1) = pts[k], pts[k + 1]
            c0 = [(a, ac, 'part')] if k == 0 else [(ids[k - 1], 'connector1', 'wire')]
            c1 = [(b, bc, 'part')] if k == len(ids) - 1 else [(ids[k + 1], 'connector0', 'wire')]
            self.wires.append(dict(kind='bb', mi=mi, x=x0, y=y0, dx=x1 - x0, dy=y1 - y0, color=color, mils=mils,
                                   cp=None, c0=c0, c1=c1))
        self.link(a, ac, ids[0], 'connector0', 'bb'); self.link(b, bc, ids[-1], 'connector1', 'bb')
        self.sch_trace(a, an, b, bn)

    def bundle(self, a, b, pins, y_top, y_bot):
        """A harness between two pin rows, one above the other: each wire
        drops from its pin on `a`, runs across at its own level between y_top
        and y_bot (mm), and drops onto its pin on `b`. The levels are ordered
        for the fewest crossings the two pin orders allow (all at 90 deg).
        pins: [(a pin name, b pin name, colour)]. Returns the crossing count."""
        import itertools
        ends = [(self.pin_mm(a, an), self.pin_mm(b, bn)) for an, bn, _ in pins]
        n = len(pins)
        levels = [y_top + (y_bot - y_top) * k / max(n - 1, 1) for k in range(n)]
        paths = lambda perm: [[s, (s[0], levels[perm[i]]), (d[0], levels[perm[i]]), d] for i, (s, d) in enumerate(ends)]
        orders = itertools.permutations(range(n)) if n <= 7 else [tuple(range(n)), tuple(reversed(range(n)))]
        best = min(orders, key=lambda perm: crossings(paths(perm)))
        for i, (an, bn, c) in enumerate(pins):
            s, d = ends[i]
            self.route(a, an, b, bn, c, [(s[0], levels[best[i]]), (d[0], levels[best[i]])])
        return crossings(paths(best))

    def sch_trace(self, a, an, b, bn):
        sx0, sy0, ac = self.pin_sch(a, an)
        sx1, sy1, bc = self.pin_sch(b, bn)
        ws = self.nid()
        self.wires.append(dict(kind='sch', mi=ws, x=sx0, y=sy0, dx=sx1 - sx0, dy=sy1 - sy0,
                               c0=[(a, ac, 'part')], c1=[(b, bc, 'part')]))
        self.link(a, ac, ws, 'connector0', 'sch'); self.link(b, bc, ws, 'connector1', 'sch')

    # ---- XML ---------------------------------------------------------------
    def conn_xml(self, mi, view, layer, wlayer):
        out = []
        for (m, c, v), lst in sorted(self.links.items()):
            if m != mi or v != view:
                continue
            cs = ''.join('<connect connectorId="%s" modelIndex="%d" layer="%s"/>' % (oc, om, wlayer) for om, oc in lst)
            out.append('<connector connectorId="%s" layer="%s"><geometry x="0" y="0"/><connects>%s</connects></connector>' % (c, layer, cs))
        return '<connectors>%s</connectors>' % ''.join(out) if out else ''

    def fz(self):
        parts = []
        for n, i in enumerate(self.inst):
            p = i['part']
            parts.append('''<instance moduleIdRef="%s" modelIndex="%d" path="%s">
  <title>%s%d</title>
  <views>
   <breadboardView layer="breadboard"><geometry z="%s" x="%s" y="%s"/>%s</breadboardView>
   <schematicView layer="schematic"><geometry z="%s" x="%s" y="%s"/>%s</schematicView>
   <pcbView layer="copper0"><geometry z="%s" x="%s" y="%s"/></pcbView>
  </views>
 </instance>''' % (p.module_id, i['mi'], p.module_id + '.fzp', p.label, n + 1,
                   f(2.5 + n * 0.001), f(i['bb'][0] * MM), f(i['bb'][1] * MM), self.conn_xml(i['mi'], 'bb', 'breadboard', 'breadboardWire'),
                   f(2.5 + n * 0.001), f(i['sch'][0] * MM), f(i['sch'][1] * MM), self.conn_xml(i['mi'], 'sch', 'schematic', 'schematicTrace'),
                   f(1.5 + n * 0.001), f(i['pcb'][0] * MM), f(i['pcb'][1] * MM)))
        wires = []
        for n, w in enumerate(self.wires):
            if w['kind'] == 'bb':
                view, layer, plyr, flags = 'breadboardView', 'breadboardWire', 'breadboardbreadboard', 64
                bez = ('<bezier><cp0 x="%s" y="%s"/><cp1 x="%s" y="%s"/></bezier>'
                       % (f(w['cp'][0][0]), f(w['cp'][0][1]), f(w['cp'][1][0]), f(w['cp'][1][1]))) if w['cp'] else ''
                extras = '<wireExtras mils="%s" color="%s" opacity="1" banded="0">%s</wireExtras>' % (f(w['mils']), w['color'], bez)
                z = 3.5 + n * 0.0001
            else:
                view, layer, plyr, flags = 'schematicView', 'schematicTrace', 'schematic', 128
                extras = '<wireExtras mils="9.7222" color="#404040" opacity="1" banded="0"/>'
                z = 5.5 + n * 0.0001

            def cx(lst):
                # a part pin sits on the part's layer; a bendpoint joins the next wire on the wire layer
                return ''.join('<connect connectorId="%s" modelIndex="%d" layer="%s"/>' % (c, m, plyr if kind == 'part' else layer)
                               for m, c, kind in lst)
            wires.append('''<instance moduleIdRef="WireModuleID" modelIndex="%d" path="wire.fzp">
  <title>Wire%d</title>
  <views>
   <%s layer="%s">
    <geometry z="%s" x="%s" y="%s" x1="0" y1="0" x2="%s" y2="%s" wireFlags="%d"/>
    %s
    <connectors>
     <connector connectorId="connector0" layer="%s"><geometry x="0" y="0"/><connects>%s</connects></connector>
     <connector connectorId="connector1" layer="%s"><geometry x="0" y="0"/><connects>%s</connects></connector>
    </connectors>
   </%s>
  </views>
 </instance>''' % (w['mi'], n + 1, view, layer, f(z), f(w['x']), f(w['y']), f(w['dx']), f(w['dy']), flags, extras,
                   layer, cx(w['c0']), layer, cx(w['c1']), view))
        return '''<?xml version="1.0" encoding="UTF-8"?>
<module fritzingVersion="1.0.8">
 <views>
  <view name="breadboardView" backgroundColor="#ffffff" gridSize="0.1in" showGrid="0" alignToGrid="0" viewFromBelow="0"/>
  <view name="schematicView" backgroundColor="#ffffff" gridSize="0.1in" showGrid="0" alignToGrid="0" viewFromBelow="0"/>
  <view name="pcbView" backgroundColor="#333333" gridSize="0.05in" showGrid="0" alignToGrid="0" viewFromBelow="0"/>
 </views>
 <title>wiring</title>
 <instances>
%s
%s
 </instances>
</module>
''' % ('\n'.join(parts), '\n'.join(wires))

    def save(self, path, name='wiring'):
        """Write the .fzz: the sketch plus every custom part it uses."""
        parts = []
        for i in self.inst:
            if i['part'] not in parts:
                parts.append(i['part'])
        with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
            z.writestr('%s.fz' % name, self.fz())
            for p in parts:
                z.writestr('part.%s.fzp' % p.module_id, p.fzp())
                z.writestr('svg.breadboard.%s' % p.fn('breadboard'), p.bb_svg())
                z.writestr('svg.icon.%s' % p.fn('icon'), p.bb_svg('icon'))
                z.writestr('svg.schematic.%s' % p.fn('schematic'), p.sch_svg())
                z.writestr('svg.pcb.%s' % p.fn('pcb'), p.pcb_svg())
        return path
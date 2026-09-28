#!/usr/bin/env python3
"""Fritzing wiring project for the Tide Machine: the main board and everything plugged into it.

    python gen_fritzing.py        ->  tide_wiring.fzz   (build.py runs this, then Fritzing's headless -svg export)

Generated, not hand-drawn (the flatpack-guide kit's fritzing_kit.py). Every part is a custom part carried in the .fzz,
so every pin position is known and every wire lands on it:
  - the main board is drawn from pcb/tide_main.kicad_pcb: silkscreen, pads, tracks and connector positions
  - six 28BYJ-48s, five Hall carriers, the calendar carrier (BKA30D-R5 + the year and moon latches) and the
    5 V supply are drawn here, in mm
Pin names and harness order come from pcb/design.py (the board's netlist), so the drawing and the board agree.

Breadboard view: the leads in their real colours. Schematic view: each part placed with its pins level with the
board pins they meet, so every trace is one straight line.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.expanduser(r'~\.claude\skills\flatpack-guide\scripts'))
sys.path.insert(0, os.path.join(ROOT, 'pcb'))
import fritzing_kit as FK   # noqa: E402
import design as D          # noqa: E402

FK.PROJECT = 'tidemachine'
PCB = os.path.join(ROOT, 'pcb', 'tide_main.kicad_pcb')
OUT = os.path.join(HERE, 'tide_wiring.fzz')
T = FK.text
LEAD = {'A': '#418dd9', 'B': '#e88aba', 'C': '#ffe24d', 'D': '#ef6100', 'HOLD': FK.RED}   # 28BYJ-48 lead colours
PINK = '#e88aba'

MOTOR_J = {m: 'J%d' % (10 + i) for i, m in enumerate(D.MOTORS)}          # DRUM J10 ... S2 J15
HALL_J = {h: 'J%d' % (20 + i) for i, h in enumerate(D.HALLS)}           # YEAR J20, MOON J21, M2 J22 ... S2 J26


def pad_names(ref):
    p = D.P[ref]['pads']
    return [p[str(i + 1)] for i in range(len(p))]


# ---- schematic rows on the board symbol (left: calendar, halls, power; right: motors)
L_ROWS = {'J20': [0, 1, 2], 'J21': [4, 5, 6], 'J5': list(range(8, 16))}
for i, h in enumerate(['M2', 'O1', 'K1', 'N2', 'S2']):
    L_ROWS[HALL_J[h]] = [19 + 6 * i + k for k in range(3)]
L_ROWS['J3'] = [50, 51, 52]
R_ROWS = {MOTOR_J[m]: [7 * i + k for k in range(5)] for i, m in enumerate(D.MOTORS)}

harness = {}
for ref, rows in L_ROWS.items():
    harness[ref] = dict(names=pad_names(ref), side='L', rows=rows)
for ref, rows in R_ROWS.items():
    harness[ref] = dict(names=pad_names(ref), side='R', rows=rows)
labels = {MOTOR_J[m]: '%s %s' % (MOTOR_J[m], m) for m in D.MOTORS}
labels.update({HALL_J[h]: '%s %s' % (HALL_J[h], h) for h in D.HALLS})
labels.update({'J5': 'J5 CAL', 'J3': 'J3 5V'})
board = FK.board_part(PCB, 'Tide Machine main board (rev B)', harness, key='mainboard',
                      modules=[dict(sockets=['J1', 'J2'], label='ESP32-C6-LCD', kind='esp32')], labels=labels,
                      desc='pcb/tide_main.kicad_pcb, 140 x 81.28 mm, drawn from the KiCad layout; the C6 shown fitted')


def conn_name(ref, pin):
    return '%s.%d %s' % (ref, pin, pad_names(ref)[pin - 1])


# ---- parts, art in mm
def motor(name):
    a = ('<path d="M4 18 A3.5 3.5 0 0 1 4 11 H32 A3.5 3.5 0 0 1 32 18 Z" fill="#b9bec4" stroke="#6b7075" stroke-width="0.3"/>'
         '<circle cx="18" cy="15" r="14" fill="#c9ced3" stroke="#6b7075" stroke-width="0.4"/>'
         '<circle cx="18" cy="7" r="4.5" fill="#dfe3e6" stroke="#6b7075" stroke-width="0.3"/><circle cx="18" cy="7" r="2.5" fill="#f2f2f2"/>'
         '<rect x="10.7" y="22" width="14.6" height="10" rx="1" fill="#2f7fc1" stroke="#1b4a7d" stroke-width="0.3"/>'
         + T(18, 18.5, name, 3.4, '#2a2a2a') + T(18, 28.5, '28BYJ-48', 1.8, '#ffffff', weight='normal'))
    for i, k in enumerate(['A', 'B', 'C', 'D', 'HOLD']):
        x = 13 + 2.5 * i
        a += '<line x1="%s" y1="32" x2="%s" y2="44" stroke="%s" stroke-width="0.9"/>' % (FK.f(x), FK.f(x), LEAD[k])
    p = FK.Part('motor_%s' % name.lower(), '28BYJ-48 (%s)' % name, 'M', 36, 44, a, '5 V unipolar stepper, 64:1; leads blue, pink, yellow, orange, red')
    for i, k in enumerate(['A', 'B', 'C', 'D', 'HOLD']):
        p.conn(k, {'A': 'blue', 'B': 'pink', 'C': 'yellow', 'D': 'orange', 'HOLD': 'red (common)'}[k], 13 + 2.5 * i, 43.4, 'L', i)
    return p


def hall(name):
    a = ('<rect x="0" y="0" width="10" height="16" rx="0.5" fill="#c9b27c" stroke="#8a7443" stroke-width="0.3"/>'
         + ''.join('<circle cx="%s" cy="%s" r="0.35" fill="#8a7443"/>' % (FK.f(1.27 + 2.54 * i), FK.f(1.27 + 2.54 * j)) for i in range(4) for j in range(6))
         + '<path d="M3 3 H7 V6 A2 2 0 0 1 3 6 Z" fill="#1d1d1d"/>' + '<rect x="3.2" y="9" width="3.6" height="1.6" rx="0.8" fill="#e8a33a"/>'
         + T(5, 13.4, name, 2.2, '#2a2a2a'))
    p = FK.Part('hall_%s' % name.lower(), 'Hall carrier (%s)' % name, 'H', 10, 16, a, 'DRV5013 latch (TO-92) + 100 nF on perfboard; lead + S -')
    for i, n in enumerate(['+', 'S', '-']):
        p.conn(n, {'+': '3.3 V', 'S': 'latch output', '-': 'ground'}[n], 2.5 + 2.5 * i, 15.4, 'R', i)
    return p


def calendar():
    a = ('<path d="M0 0 H36 V62 L32 68 H4 L0 62 Z" transform="translate(36 68) rotate(180)" fill="#c9b27c" stroke="#8a7443" stroke-width="0.3"/>'
         '<rect x="2.25" y="4.25" width="31.5" height="59.5" rx="1" fill="#2b2f33" stroke="#111" stroke-width="0.3"/>'
         '<circle cx="18" cy="34" r="4" fill="#9aa3ab"/><circle cx="18" cy="34" r="1.6" fill="#dfe3e6"/>'
         + T(18, 12, 'BKA30D-R5', 2.6) + T(18, 16, 'placeholder', 1.8, '#cfd3d6', weight='normal')
         + '<path d="M16 50 H20 V53 A2 2 0 0 1 16 53 Z" fill="#1d1d1d"/><path d="M16 20 H20 V23 A2 2 0 0 1 16 23 Z" fill="#1d1d1d"/>'
         + T(24, 23, 'year', 1.8, '#ffffff', 'start', 'normal') + T(24, 53, 'moon', 1.8, '#ffffff', 'start', 'normal'))
    p = FK.Part('calendar', 'Calendar carrier', 'CAL', 36, 68, a, 'BKA30D-R5 gauge stepper + year and moon latches on perfboard (outline: 4 x 6 corner cuts)')
    for i, n in enumerate(['Y+', 'YS', 'Y-']):
        p.conn(n, 'year latch ' + n[1:], 5 + 2.5 * i, 67.4, 'R', i)
    for i, n in enumerate(['M+', 'MS', 'M-']):
        p.conn(n, 'moon latch ' + n[1:], 15 + 2.5 * i, 67.4, 'R', 4 + i)
    for i, n in enumerate(['Y1', 'Y2', 'Y3', 'Y4', 'M1', 'M2', 'M3', 'M4']):
        p.conn(n, ('year' if n[0] == 'Y' else 'moon') + ' coil ' + n[1], 0.6, 26 + 2.5 * i, 'R', 8 + i)
    return p


def psu():
    a = ('<rect x="0" y="0" width="34" height="26" rx="3" fill="#2b2f33" stroke="#111" stroke-width="0.4"/>'
         + T(17, 11, '5 V  3 A', 3.6) + T(17, 16, 'regulated', 2, '#cfd3d6', weight='normal')
         + '<path d="M17 26 C17 34 4 34 4 40" fill="none" stroke="#1d1d1d" stroke-width="1.6"/>'
         '<rect x="0.5" y="40" width="7" height="9" rx="1" fill="#1d1d1d"/>' + T(4, 53, '5.5 x 2.1', 1.6, '#2a2a2a', weight='normal'))
    p = FK.Part('psu', '5 V 3 A supply', 'PS', 34, 54, a, 'MEAN WELL GST18U05-P1J or similar, centre positive')
    p.conn('+', 'centre pin, +5 V', 2.5, 48.6, 'R', 0)
    p.conn('-', 'sleeve, ground', 5.5, 48.6, 'R', 1)
    return p


S = FK.Sketch()
b = S.place(board, (0, 0), (0, 0), (0, 0))

# motors above the board, in the order of their sockets
for i, m in enumerate(D.MOTORS):
    part = motor(m)
    j = MOTOR_J[m]
    mi = S.place(part, (-52 + 42 * i, -78), FK.level(board, part, 'A', conn_name(j, 1), False), (-60 + 20 * i, -60))
    for k, key in enumerate(['A', 'B', 'C', 'D', 'HOLD']):
        S.wire(mi, key, b, conn_name(j, k + 1), LEAD[key], sag=4)

# station Hall carriers below the board, each under its socket so the leads run straight down
_, PADS, *_ = FK.load_board_at_origin(PCB)
def pin_xy(ref, n):
    q = next(q for q in PADS[ref] if q['num'] == str(n))
    return q['x'], q['y']
for i, h in enumerate(['M2', 'O1', 'K1', 'N2', 'S2']):
    part = hall(h)
    j = HALL_J[h]
    px, py = pin_xy(j, 1)
    mi = S.place(part, (px - 2.5, py + 26), FK.level(board, part, '+', conn_name(j, 1), True), (20 * i, 100))
    for k, (n, col) in enumerate([('+', FK.RED), ('S', FK.YELLOW), ('-', FK.BLACK)]):
        S.wire(mi, n, b, conn_name(j, k + 1), col, sag=0)

# the calendar carrier on the right: coils to J5, its two latches to J20 / J21
cal = calendar()
ci = S.place(cal, (170, -8), FK.level(board, cal, 'Y+', conn_name('J20', 1), True), (170, 0))
coil_cols = [FK.BLUE, PINK, FK.YELLOW, FK.ORANGE, FK.GREEN, FK.PURPLE, FK.GREY, FK.WHITE]
for k, n in enumerate(['Y1', 'Y2', 'Y3', 'Y4', 'M1', 'M2', 'M3', 'M4']):
    S.wire(ci, n, b, conn_name('J5', k + 1), coil_cols[k], sag=-3)
for lat, j in (('Y', 'J20'), ('M', 'J21')):
    for k, (sfx, col) in enumerate([('+', FK.RED), ('S', FK.YELLOW), ('-', FK.BLACK)]):
        S.wire(ci, lat + sfx, b, conn_name(j, k + 1), col, sag=30 + 4 * k)

# the supply into J3
ps = psu()
pi = S.place(ps, (178, 78), FK.level(board, ps, '+', conn_name('J3', 1), True), (180, 90))
S.wire(pi, '+', b, conn_name('J3', 1), FK.RED, sag=6)
S.wire(pi, '-', b, conn_name('J3', 2), FK.BLACK, sag=10)

S.save(OUT, 'tide_wiring')
print('wrote', OUT)

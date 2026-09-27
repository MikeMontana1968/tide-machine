"""Silkscreen labels and marks as plain data (board mm), shared by silk.py (preview) and build_board.py (KiCad).

labels(): [dict(text, x, y, h, rot, ha, bold, dim)]   h = text height in mm; dim = a small legend
shapes(): [("rect_dashed", x0, y0, x1, y1) | ("circle", x, y, r)]
Positions follow the parts in design.P, so moving a part moves its label.
"""
import design

P = design.P

def _dip_centre(ref):
    p = P[ref]
    pins = {"DIP18": 18, "DIP20": 20, "DIP28": 28}[[k for k, v in design.FP.items() if v == p["fp"]][0]]
    if p["rot"] == 90:
        return p["x"] + (pins / 2 - 1) * 2.54 / 2, p["y"] - 3.81
    return p["x"] + 3.81, p["y"] + (pins / 2 - 1) * 2.54 / 2

def labels():
    L = []
    def t(s, x, y, h=1.0, rot=0, ha="center", bold=False, dim=False):
        L.append(dict(text=s, x=x, y=y, h=h, rot=rot, ha=ha, bold=bold, dim=dim))
    xy = lambda r: (P[r]["x"], P[r]["y"])
    # ICs in sockets: ref + part inside the outline
    for ref, sub in [("U2", "MCP23017 · 0x20"), ("U3", "MCP23017 · 0x21"), ("U8", "MCP23017 · 0x22 · CALENDAR"),
                     ("U4", "ULN2803A · N2 S2"), ("U5", "ULN2803A · O1 K1"), ("U6", "ULN2803A · DRUM M2"),
                     ("U7", "74AHCT245 · CALENDAR 5V")]:
        x, y = _dip_centre(ref)
        t(ref, x, y - 0.9, 1.5, bold=True); t(sub, x, y + 1.1, 1.05)
    # motor sockets: name under the body, wire colours under the pins
    for i, m in enumerate(design.MOTORS):
        x0 = P[f"J{10 + i}"]["x"]
        t(m, x0 + 5.0, 10.9, 1.5, bold=True)
        for k, col in enumerate("BPYOR"):
            t(col, x0 + 2.5 * k, 8.9, 0.8, dim=True)
    for k, s in enumerate(["B P Y O R =", "blue pink yellow", "orange red"]):
        t(s, design.BOARD_W - 2.0, 9.8 + k, 0.8, ha="right", dim=True)
    # Hall sockets: name and pin legend above
    for i, h in enumerate(design.HALLS):
        x, y = xy(f"J{20 + i}")
        t(h, x + 2.5, y - 5.4, 1.3, bold=True)
        for k, s in enumerate(["+", "S", "−"]):
            t(s, x + 2.5 * k, y - 3.35, 0.8, dim=True)
    t("HALL: + 3V3 · S signal · − GND", 92.0, 70.9, 0.8, ha="left", dim=True)
    # calendar socket and jack
    x, y = xy("J5")
    t("CALENDAR · YEAR 1–4 · MOON 5–8", x - 3.5, y - 8.75, 0.9, rot=90, bold=True)
    t("1", x - 0.2, y + 3.9, 0.8, dim=True)
    t("5V IN  ⊕ centre", 131.0, 57.3, 1.1, bold=True)
    # expansion header
    x, y = xy("J4")
    for k, s in enumerate(["3V3", "GND", "SDA", "SCL", "IO1", "IO3"]):
        t(s, x + 1.9, y + 2.54 * k, 0.8, ha="left")
    t("J4 EXP", 0.9, y - 2.8, 1.0, ha="left", bold=True)
    # small parts: ref + value, placed relative to the part
    def lab(ref, text, dx, dy, rot=0, ha="center"):
        x, y = xy(ref)
        t(text, x + dx, y + dy, 0.95, rot=rot, ha=ha)
    for k, (r, v) in enumerate((("R1", "4k7"), ("R2", "4k7"), ("R3", "10k"), ("R9", "10k"), ("R4", "10k"))):
        lab(r, f"{r} {v}", 1.27, 2.3 if k % 2 == 0 else 3.6)          # below, staggered: they're 5.3 mm apart
    lab("R5", "R5 1k", 1.27, -2.2)
    lab("R6", "R6 1k", 1.27, 2.3)
    lab("R7", "R7 10k", 1.27, 2.3)
    lab("R8", "R8 1k", -2.0, 0, ha="right")
    lab("LED1", "PWR", -2.0, 0, ha="right")
    lab("C1", "C1 1000µ", 2.5, 6.3)
    lab("C5", "C5", 0, -5.3)
    lab("C6", "C6 100n", 4.3, 0, ha="left")
    lab("C7", "C7 100n", -1.8, 0, ha="right")
    lab("C8", "C8 100n", 4.3, 0, ha="left")
    lab("Q1", "Q1 IRLIB9343", 2.54, -4.2)
    lab("Q2", "Q2 2N3904", 2.54, 3.1)
    lab("D1", "D1 1N5819", -2.6, -5.1, rot=90)
    lab("D2", "D2 1N5819", 5.08, 2.4)
    lab("F1", "F1 2.5A", -2.2, -3.0, rot=90)
    lab("RN1", "RN1 8×10k", 10.16, -2.4)
    lab("RN2", "RN2 7×10k", 8.9, -2.4)
    # ESP32-C6 area
    x0, y0, x1, y1 = design.DEVKIT
    cx = (x0 + x1) / 2 + 2.8
    t("ESP32-C6-LCD-1.47", cx, 51.9, 1.55, bold=True)
    t("plugs in here", cx, 54.6, 1.1)
    t("nothing underneath", cx, 56.3, 1.1)
    t("◄ USB", 0.9, 53.3, 1.2, ha="left", bold=True)
    t("antenna", 34.9, 53.3, 0.9, rot=90)
    for k, s in enumerate(["TX", "RX", "13", "12", "23", "20", "19", "18", "9"]):
        t(s, design.ESP_X1 + 2.54 * k, design.ESP_YT + 2.2, 0.8, dim=True)
    for k, s in enumerate(["5V", "G", "3V3", "0", "1", "2", "3", "4", "5"]):
        t(s, design.ESP_X1 + 2.54 * k, design.ESP_YB - 2.2, 0.8, dim=True)
    # title
    t("TIDE MACHINE", 110.0, 74.0, 2.4, bold=True)
    t("main board · rev B · ESP32-C6", 110.0, 77.2, 1.1)
    t(f"{design.BOARD_W:g} × {design.BOARD_H:.1f} mm · all through-hole", 110.0, 79.2, 0.9, dim=True)
    return L

def shapes():
    x0, y0, x1, y1 = design.DEVKIT
    S = [("rect_dashed", max(0.5, x0), y0 - 0.65, x1 + 0.2, y1 + 0.65)]     # just outside the socket strips' outlines
    S += [("circle", hx, hy, 3.0) for hx, hy in design.HOLES]
    return S

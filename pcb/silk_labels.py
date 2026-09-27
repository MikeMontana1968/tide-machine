"""Silkscreen labels and marks as plain data (board mm), shared by silk.py (preview) and build_board.py (KiCad).

labels(): [dict(text, x, y, h, rot, ha, bold, dim)]   h = text height in mm; dim = a small legend
shapes(): [("rect_dashed", x0, y0, x1, y1) | ("circle", x, y, r)]
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
    # ICs in sockets: ref + part inside the outline
    for ref, sub in [("U2", "MCP23017 · 0x20"), ("U3", "MCP23017 · 0x21"), ("U4", "ULN2803A · N2 S2"),
                     ("U5", "ULN2803A · O1 K1"), ("U6", "ULN2803A · DRUM M2")]:
        x, y = _dip_centre(ref)
        t(ref, x, y - 0.9, 1.5, bold=True); t(sub, x, y + 1.1, 1.05)
    x, y = _dip_centre("U7")
    t("U7", x, y - 1.2, 1.5, rot=90, bold=True); t("74AHCT245 · CALENDAR", x + 1.6, y, 1.05, rot=90)
    # motor sockets: name under the body, wire colours under the pins
    for i, m in enumerate(design.MOTORS):
        x0 = P[f"J{10 + i}"]["x"]
        t(m, x0 + 5.0, 10.9, 1.5, bold=True)
        for k, col in enumerate("BPYOR"):
            t(col, x0 + 2.5 * k, 8.9, 0.8, dim=True)
    t("B P Y O R =", 125.2, 9.8, 0.8, ha="right", dim=True)
    t("blue pink yellow", 125.2, 10.8, 0.8, ha="right", dim=True)
    t("orange red", 125.2, 11.8, 0.8, ha="right", dim=True)
    # Hall sockets: name and pin legend above
    for i, h in enumerate(design.HALLS):
        p = P[f"J{20 + i}"]
        t(h, p["x"] + 2.5, p["y"] - 5.4, 1.3, bold=True)
        for k, s in enumerate(["+", "S", "−"]):
            t(s, p["x"] + 2.5 * k, p["y"] - 3.35, 0.8, dim=True)
    t("HALL: + 3V3 · S signal · − GND", 92.0, 76.9, 0.8, ha="left", dim=True)
    # calendar socket and jack
    p = P["J5"]
    t("CALENDAR · YEAR 1–4 · MOON 5–8", p["x"] - 4.0, p["y"] - 8.75, 0.9, rot=90, bold=True)
    t("1", p["x"] - 0.2, p["y"] + 3.9, 0.8, dim=True)
    t("5V IN  ⊕ centre", 119.3, 57.6, 1.1, bold=True)
    # expansion header
    p = P["J4"]
    for k, s in enumerate(["3V3", "GND", "SDA", "SCL", "IO14", "IO34"]):
        t(s, p["x"] + 1.9, p["y"] + 2.54 * k, 0.8, ha="left")
    t("J4 EXP", 0.9, p["y"] - 2.8, 1.0, ha="left", bold=True)
    # everything else: ref + value, placed by hand
    for s, x, y, rot, ha in [
        ("R1 4k7", 58.27, 43.2, 0, "center"), ("R2 4k7", 63.57, 43.2, 0, "center"),
        ("R3 10k", 68.87, 43.2, 0, "center"), ("R4 10k", 74.17, 43.2, 0, "center"),
        ("R5 1k", 89.27, 46.3, 0, "center"), ("R6 1k", 75.77, 46.8, 0, "center"),
        ("R7 10k", 75.77, 55.9, 0, "center"), ("R8 1k", 99.77, 61.3, 0, "center"),
        ("Q1 IRLIB9343", 82.5, 37.9, 0, "center"), ("Q2 2N3904", 82.44, 52.9, 0, "center"),
        ("D2 1N5819", 94.4, 44.9, 0, "center"), ("C1 1000µ", 90.5, 66.8, 0, "center"),
        ("C5", 117.5, 20.6, 0, "center"), ("C6 100n", 39.2, 37.6, 0, "left"), ("C7 100n", 70.1, 37.6, 0, "right"),
        ("PWR", 99.8, 72.1, 0, "center"), ("F1 2.5A", 103.6, 65.0, 90, "center"),
        ("RN1 8×10k", 103.0, 54.6, 0, "center"), ("RN2 7×10k", 67.3, 66.5, 0, "center"),
        ("D1 1N5819", 7.2, 32.3, 90, "center")]:
        t(s, x, y, 0.95, rot=rot, ha=ha)
    # DevKit area
    x0, y0, x1, y1 = design.DEVKIT
    t("ESP32-DevKitC-32E", (x0 + x1) / 2, 50.5, 2.2, bold=True)
    t("plugs in here · nothing underneath", (x0 + x1) / 2, 54.2, 1.2)
    t("◄ USB", 1.2, 54.1, 1.4, ha="left", bold=True)
    t("antenna", 52.6, 54.1, 1.0, rot=90)
    t("5V", 5.2, 44.8, 0.9, dim=True); t("3V3", 49.9, 44.8, 0.9, dim=True); t("GND", 49.9, 63.4, 0.9, dim=True)
    t("J2 side", 27.0, 44.8, 0.9, dim=True); t("J3 side", 27.0, 63.4, 0.9, dim=True)
    # title
    t("TIDE MACHINE", 68.5, 58.8, 2.4, bold=True)
    t("main board · rev A", 68.5, 62.2, 1.3)
    t(f"{design.BOARD_W:g} × {design.BOARD_H:.1f} mm · all through-hole", 68.5, 64.4, 0.95, dim=True)
    return L

def shapes():
    x0, y0, x1, y1 = design.DEVKIT
    S = [("rect_dashed", x0 + 0.5, y0 - 0.65, x1 + 0.2, y1 + 0.65)]     # just outside the socket strips' own outlines
    S += [("circle", hx, hy, 3.0) for hx, hy in design.HOLES]
    return S

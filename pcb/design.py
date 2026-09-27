"""Tide Machine main board: parts, footprints, placement and netlist, as data. ALL THROUGH-HOLE.

One 127.0 x 81.28 mm (5 x 3.2 in) two-layer board, mounted on 4 x M3 x 30 standoffs behind the faceplate,
over the stepper motors. Everything else is wired to it:

    top edge     six 28BYJ-48 sockets (JST-XH 5-pin: the motor's own plug, blue pink yellow orange red)
    bottom edge  seven Hall latches (JST-XH 3-pin)
    right edge   the BKA30D-R5 calendar motor (JST-XH 8-pin) and the 5 V barrel jack
    left edge    the ESP32-DevKitC-32E's USB (the DevKit sits in two 1x19 female headers, nothing underneath it)
                 and an expansion header (I2C for an RTC later, two spare GPIOs)

ICs are DIP in sockets; resistors 1/4 W axial standing up (2.54 mm pitch) or bussed SIP networks.
The calendar motor is driven straight from the 74AHCT245's 5 V outputs, one gauge motor at a time
(it moves ~1 deg/day; the AX1201728SG's microstepping bought nothing and it only comes as SMD).

This file is the input to the KiCad build (build_board.py, run under KiCad's Python). Coordinates are
board-relative mm (origin top-left, y down); rotations are KiCad's (degrees, counter-clockwise on screen).
Footprint anchors are KiCad's own (pad 1 for all of these). At rot 90 a DIP has pin 1 bottom-left, pins
rising to the right along the bottom row, and the last pin above pin 1.
"""

BOARD_W, BOARD_H = 127.0, 81.28
HOLES = [(3.5, 3.5), (123.5, 3.5), (3.5, 77.78), (123.5, 77.78)]      # M3, for 30 mm standoffs to the plate
DEVKIT = (0.0, 40.152, 54.4, 68.052)     # the DevKit's own outline (54.4 x 27.9): every other part stays out of it
ESP_PIN1_X = 50.038                      # antenna end right; pin 19 at x 4.318 puts the USB end flush with the left edge

FP = {
    "DIP18": "Package_DIP:DIP-18_W7.62mm_Socket",
    "DIP20": "Package_DIP:DIP-20_W7.62mm_Socket",
    "DIP28": "Package_DIP:DIP-28_W7.62mm_Socket",
    "RV": "Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P2.54mm_Vertical",
    "SIP8": "Resistor_THT:R_Array_SIP8",
    "SIP9": "Resistor_THT:R_Array_SIP9",
    "CD": "Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P2.50mm",
    "CP10": "Capacitor_THT:CP_Radial_D10.0mm_P5.00mm",
    "DO41": "Diode_THT:D_DO-41_SOD81_P10.16mm_Horizontal",
    "TO220": "Package_TO_SOT_THT:TO-220-3_Vertical",
    "TO92": "Package_TO_SOT_THT:TO-92_Inline",
    "LED3": "LED_THT:LED_D3.0mm",
    "PTC": "Fuse:Fuse_Bourns_MF-RG300",
    "XH3": "Connector_JST:JST_XH_B3B-XH-A_1x03_P2.50mm_Vertical",
    "XH5": "Connector_JST:JST_XH_B5B-XH-A_1x05_P2.50mm_Vertical",
    "XH8": "Connector_JST:JST_XH_B8B-XH-A_1x08_P2.50mm_Vertical",
    "SOCK19": "Connector_PinSocket_2.54mm:PinSocket_1x19_P2.54mm_Vertical",
    "HDR6": "Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical",
    "JACK": "Connector_BarrelJack:BarrelJack_CUI_PJ-102AH_Horizontal",
    "HOLE": "MountingHole:MountingHole_3.2mm_M3",
}

MOTORS = ["DRUM", "M2", "O1", "K1", "N2", "S2"]          # left to right on the board = machine +x to -x as seen
                                                         # from behind, so each cable runs straight to its motor
HALLS = ["YEAR", "MOON", "M2", "O1", "K1", "N2", "S2"]   # bottom edge, left to right
COIL = "ABCD"                                            # A blue, B pink, C yellow, D orange; red = HOLD

# MCP23017 port bit -> motor wire, ordered so the traces don't cross. Firmware reads this table.
#   U3 (0x21) GPA drives ULN U6 (DRUM, M2);  U2 (0x20) GPA drives U5 (O1, K1), GPB drives U4 (N2, S2)
MOTOR_BITS = {
    "DRUM": [("U3", "GPA", 7), ("U3", "GPA", 6), ("U3", "GPA", 5), ("U3", "GPA", 4)],
    "M2":   [("U3", "GPA", 3), ("U3", "GPA", 2), ("U3", "GPA", 1), ("U3", "GPA", 0)],
    "O1":   [("U2", "GPA", 7), ("U2", "GPA", 6), ("U2", "GPA", 5), ("U2", "GPA", 4)],
    "K1":   [("U2", "GPA", 3), ("U2", "GPA", 2), ("U2", "GPA", 1), ("U2", "GPA", 0)],
    "N2":   [("U2", "GPB", 7), ("U2", "GPB", 6), ("U2", "GPB", 5), ("U2", "GPB", 4)],
    "S2":   [("U2", "GPB", 3), ("U2", "GPB", 2), ("U2", "GPB", 1), ("U2", "GPB", 0)],
}
ULN_OF = {"DRUM": ("U6", 0), "M2": ("U6", 4), "O1": ("U5", 0), "K1": ("U5", 4), "N2": ("U4", 0), "S2": ("U4", 4)}
HALL_BITS = {"M2": 0, "O1": 1, "K1": 2, "N2": 3, "S2": 4}          # U3 GPB0-4, left to right like the sockets

# calendar: ESP32 GPIO -> 74AHCT245 A input -> B output -> J5 pin -> BKA30D-R5 coil end
CAL_GPIO = {"Y1": 16, "Y2": 17, "Y3": 18, "Y4": 19, "M1": 23, "M2": 4, "M3": 13, "M4": 26}
CAL_ORDER = ["M4", "M3", "M2", "M1", "Y4", "Y3", "Y2", "Y1"]       # 245 channels 1-8 (A1-A8 / B1-B8)
CAL_PIN = {"Y1": 1, "Y2": 2, "Y3": 3, "Y4": 4, "M1": 5, "M2": 6, "M3": 7, "M4": 8}   # J5

def mcp_pin(port, bit):
    return (21 + bit) if port == "GPA" else (1 + bit)

P = {}

def part(ref, fp, value, mpn, x, y, rot, pads, note=""):
    P[ref] = dict(fp=FP[fp], value=value, mpn=mpn, x=x, y=y, rot=rot, pads={str(k): v for k, v in pads.items()}, note=note)

# ---- ESP32-DevKitC-32E sockets: DevKit J2 (3V3 ... 5V) on the top row, J3 (GND, IO23 ... CLK) on the bottom;
#      pin 1 of both at the right (antenna) end, USB at the left edge. Rows 25.4 apart (the DevKitC V4 is 27.9 wide).
J3PIN = {23: 2, 22: 3, 21: 6, 19: 8, 18: 9, 5: 10, 17: 11, 16: 12, 4: 13, 0: 14, 2: 15, 15: 16}
J2PIN = {36: 3, 39: 4, 34: 5, 35: 6, 32: 7, 33: 8, 25: 9, 26: 10, 27: 11, 14: 12, 12: 13, 13: 15}
top = {1: "GND", 7: "GND", J3PIN[22]: "SCL", J3PIN[21]: "SDA"}
bot = {1: "+3V3", 14: "GND", 19: "ESP_5V", J2PIN[32]: "HALL_YEAR", J2PIN[33]: "HALL_MOON", J2PIN[25]: "PWM",
       J2PIN[27]: "MCP_INT", J2PIN[14]: "IO14", J2PIN[34]: "IO34"}
for ch, g in CAL_GPIO.items():
    (top if g in J3PIN else bot)[(J3PIN if g in J3PIN else J2PIN)[g]] = f"CTL_{ch}"
part("J1", "SOCK19", "ESP32 J3 side", "1x19 female header, 2.54 mm, 8.5 mm tall", ESP_PIN1_X, 66.802, 270, top,
     "DevKit J3: GND IO23 IO22 TX RX IO21 GND IO19 IO18 IO5 IO17 IO16 IO4 IO0 IO2 IO15 D1 D0 CLK")
part("J2", "SOCK19", "ESP32 J2 side", "1x19 female header, 2.54 mm, 8.5 mm tall", ESP_PIN1_X, 41.402, 270, bot,
     "DevKit J2: 3V3 EN VP VN IO34 IO35 IO32 IO33 IO25 IO26 IO27 IO14 IO12 GND IO13 D2 D3 CMD 5V")

# ---- motor sockets, top edge (courtyards touching)
for i, m in enumerate(MOTORS):
    part(f"J{10 + i}", "XH5", f"MOTOR {m}", "JST B5B-XH-A", 10.15 + 19.3 * i, 4.6, 0,
         {1: f"{m}_A", 2: f"{m}_B", 3: f"{m}_C", 4: f"{m}_D", 5: "HOLD"}, "28BYJ-48 plug: blue pink yellow orange red")

# ---- ULN2803A (DIP-18): inputs 1-8 (1B-8B), 9 GND, 10 COM, outputs 18..11 (1C..8C)
for u, x in (("U6", 14.732), ("U5", 53.34), ("U4", 92.456)):
    pads = {9: "GND", 10: "HOLD"}
    for m, (uu, off) in ULN_OF.items():
        if uu == u:
            for k in range(4):
                pads[1 + off + k] = f"{m}_IN{COIL[k]}"
                pads[18 - off - k] = f"{m}_{COIL[k]}"
    part(u, "DIP18", "ULN2803A", "ULN2803A (DIP-18) + socket", x, 21.59, 90, pads)

# ---- MCP23017-E/SP (DIP-28): 1-8 GPB0-7, 9 VDD, 10 VSS, 12 SCL, 13 SDA, 15-17 A0-A2, 18 RESET, 19 INTB, 21-28 GPA0-7
def mcp(ref, x, a0, extra):
    pads = {9: "+3V3", 10: "GND", 12: "SCL", 13: "SDA", 15: a0, 16: "GND", 17: "GND", 18: "MCP_RST"}
    for m, bits in MOTOR_BITS.items():
        for k, (u, port, bit) in enumerate(bits):
            if u == ref:
                pads[mcp_pin(port, bit)] = f"{m}_IN{COIL[k]}"
    pads.update(extra)
    part(ref, "DIP28", "MCP23017", "MCP23017-E/SP (DIP-28) + socket", x, 34.29, 90, pads)

mcp("U2", 51.308, "GND", {})                                                                     # address 0x20
mcp("U3", 13.97, "+3V3", {19: "MCP_INT", **{1 + b: f"HALL_{h}" for h, b in HALL_BITS.items()}})  # address 0x21

# ---- 74AHCT245 (DIP-20): drives the calendar coils at 5 V. 1 DIR, 2-9 A1-A8, 10 GND, 18..11 B1..B8, 19 OE, 20 VCC
pads = {1: "+5V", 10: "GND", 19: "GND", 20: "+5V"}
for k, ch in enumerate(CAL_ORDER):
    pads[2 + k] = f"CTL_{ch}"
    pads[18 - k] = f"CAL_{ch}"
part("U7", "DIP20", "74AHCT245", "SN74AHCT245N (DIP-20) + socket", 108.0, 29.0, 0, pads,
     "calendar coil driver; drive one gauge motor at a time (38 mA per chip)")
part("J5", "XH8", "CALENDAR", "JST B8B-XH-A", 122.8, 52.0, 90, {v: f"CAL_{k}" for k, v in CAL_PIN.items()},
     "BKA30D-R5: 1-4 motor A (year, outer shaft), 5-8 motor B (moon, inner); coils are pins 1-2 / 3-4 of each")
part("RN1", "SIP9", "8x10k bussed", "Bourns 4609X-101-103LF", 103.0, 30.5, 270,
     {1: "GND", **{2 + k: f"CTL_{ch}" for k, ch in enumerate(["Y1", "Y2", "Y3", "Y4", "M1", "M2", "M3", "M4"])}},
     "holds the calendar coils off while the ESP32 boots")

# ---- Hall latches, bottom edge (3V3, OUT, GND), and their pull-ups
for i, h in enumerate(HALLS):
    part(f"J{20 + i}", "XH3", f"HALL {h}", "JST B3B-XH-A", 10.15 + 11.9 * i, 76.88, 0, {1: "+3V3", 2: f"HALL_{h}", 3: "GND"},
         "DRV5013 (TO-92): 3V3, OUT, GND")
part("RN2", "SIP8", "7x10k bussed", "Bourns 4608X-101-103LF", 58.4, 69.0, 0,
     {1: "+3V3", **{2 + i: f"HALL_{h}" for i, h in enumerate(HALLS)}}, "Hall pull-ups (DRV5013 is open-drain)")

# ---- power: jack -> PTC -> +5V bus; high-side PWM switch for the motor common (HOLD)
part("J3", "JACK", "5V IN", "CUI (Same Sky) PJ-102AH, 5.5 x 2.1 mm", 113.3, 66.0, 90, {1: "VIN", 2: "GND", 3: "GND"},
     "centre positive")
part("F1", "PTC", "PTC 2.5A", "Bourns MF-R250 (2.5 A hold, radial)", 106.0, 68.0, 90, {1: "VIN", 2: "+5V"})
part("C1", "CP10", "1000uF 10V", "1000 uF 10 V radial, 10 mm dia, 5 mm pitch", 88.0, 60.0, 0, {1: "+5V", 2: "GND"})
part("Q1", "TO220", "IRLIB9343", "IRLIB9343PBF logic-level P-FET, TO-220", 80.0, 42.5, 0, {1: "Q1_G", 2: "HOLD", 3: "+5V"})
part("R5", "RV", "1k", "1/4 W", 88.0, 48.5, 0, {1: "Q1_G", 2: "+5V"}, "gate pull-up: 1k so the gate turns off fast at 20 kHz")
part("Q2", "TO92", "2N3904", "2N3904 NPN, TO-92 (E B C)", 80.5, 49.0, 0, {1: "GND", 2: "Q2_B", 3: "Q1_G"})
part("R6", "RV", "1k", "1/4 W", 74.5, 49.0, 0, {1: "PWM", 2: "Q2_B"})
part("R7", "RV", "10k", "1/4 W", 74.5, 53.5, 0, {1: "Q2_B", 2: "GND"}, "holds the motors off while the ESP32 boots")
part("D2", "DO41", "1N5819", "1N5819 Schottky", 89.3, 42.0, 0, {1: "HOLD", 2: "GND"}, "freewheel path when the PWM switch opens")
part("D1", "DO41", "1N5819", "1N5819 Schottky", 10.4, 37.5, 90, {1: "ESP_5V", 2: "+5V"}, "5 V to the DevKit; blocks USB back-feed")
part("LED1", "LED3", "PWR", "3 mm LED, green", 98.5, 68.5, 0, {1: "GND", 2: "LED_A"})
part("R8", "RV", "1k", "1/4 W", 98.5, 63.5, 0, {1: "LED_A", 2: "+5V"})

# ---- decoupling, right at each chip's supply pins
part("C5", "CD", "100nF", "100 nF ceramic, 2.5 mm pitch", 117.5, 25.8, 90, {1: "+5V", 2: "GND"}, "74AHCT245")
part("C6", "CD", "100nF", "100 nF ceramic, 2.5 mm pitch", 34.29, 37.6, 0, {1: "+3V3", 2: "GND"}, "U3")
part("C7", "CD", "100nF", "100 nF ceramic, 2.5 mm pitch", 71.63, 37.6, 0, {1: "+3V3", 2: "GND"}, "U2")

# ---- I2C / interrupt / reset pull-ups
part("R1", "RV", "4.7k", "1/4 W", 57.0, 40.7, 0, {1: "SDA", 2: "+3V3"})
part("R2", "RV", "4.7k", "1/4 W", 62.3, 40.7, 0, {1: "SCL", 2: "+3V3"})
part("R3", "RV", "10k", "1/4 W", 67.6, 40.7, 0, {1: "MCP_INT", 2: "+3V3"})
part("R4", "RV", "10k", "1/4 W", 72.9, 40.7, 0, {1: "MCP_RST", 2: "+3V3"})

# ---- expansion header on the left edge: I2C for an RTC later, two free ESP32 pins
part("J4", "HDR6", "EXP", "1x06 male header, 2.54 mm", 2.54, 11.43, 0, {
    1: "+3V3", 2: "GND", 3: "SDA", 4: "SCL", 5: "IO14", 6: "IO34"}, "3V3 GND SDA SCL IO14 IO34(input only)")

for i, (hx, hy) in enumerate(HOLES):
    part(f"H{i + 1}", "HOLE", "M3", "M3 x 30 standoff", hx, hy, 0, {})

# ---- net classes: name -> (track width, clearance, nets)
NETCLASS = {
    "Power": (1.0, 0.25, ["+5V", "VIN", "HOLD", "GND"]),
    "Supply": (0.5, 0.2, ["ESP_5V", "+3V3"]),
    "Motor": (0.4, 0.2, [f"{m}_{c}" for m in MOTORS for c in COIL]),
}
DEFAULT = (0.25, 0.2)

def netclass(net):
    for name, (w, c, members) in NETCLASS.items():
        if net in members:
            return name, w, c
    return "Default", DEFAULT[0], DEFAULT[1]

def nets():
    out = {}
    for ref, p in P.items():
        for pad, n in p["pads"].items():
            out.setdefault(n, []).append((ref, pad))
    return out

if __name__ == "__main__":
    n = nets()
    print(len(P), "parts,", len(n), "nets")
    for k in sorted(n):
        if len(n[k]) < 2:
            print("  single-pin net:", k, n[k])

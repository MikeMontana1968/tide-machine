"""Tide Machine main board: parts, footprints, placement and netlist, as data. ALL THROUGH-HOLE.

One 140.0 x 81.28 mm (5.5 x 3.2 in) two-layer board, mounted on 4 x M3 x 30 standoffs behind the faceplate,
over the stepper motors. Everything else is wired to it:

    top edge     six 28BYJ-48 sockets (JST-XH 5-pin: the motor's own plug, blue pink yellow orange red)
    bottom edge  seven Hall latches (JST-XH 3-pin)
    right edge   the BKA30D-R5 calendar motor (JST-XH 8-pin) and the 5 V barrel jack
    left edge    the ESP32-C6-LCD-1.47's USB-C (the Waveshare board sits in two 1x9 female headers, nothing
                 underneath it) and an expansion header (I2C for an RTC later, two spare GPIOs)

The ESP32-C6 board has only 8 free, safe GPIOs, so three MCP23017s do the I/O: 0x20 and 0x21 drive the six
steppers through three ULN2803As (0x21 also reads the five station Hall latches), and 0x22 drives the calendar
coils through a 74AHCT245 (5 V) and reads the year and moon latches. The ESP32 uses five pins: I2C, two
interrupts, and the hold PWM.

ICs are DIP in sockets; resistors 1/4 W axial standing up (2.54 mm pitch) or bussed SIP networks.
The calendar motor is driven straight from the 74AHCT245's 5 V outputs, one gauge motor at a time.

This file is the input to the KiCad build (build_board.py, run under KiCad's Python). Coordinates are
board-relative mm (origin top-left, y down); rotations are KiCad's (degrees, counter-clockwise on screen).
Footprint anchors are KiCad's own (pad 1 for all of these). At rot 90 a DIP has pin 1 bottom-left, pins
rising to the right along the bottom row, and the last pin above pin 1.
"""

BOARD_W, BOARD_H = 140.0, 81.28
HOLES = [(3.5, 3.5), (136.5, 3.5), (3.5, 77.78), (136.5, 77.78)]     # M3, for 30 mm standoffs to the plate

# Waveshare ESP32-C6-LCD-1.47: 36.37 x 20.32, two 1x9 rows 17.78 apart, first pins 11.31 from the USB end.
# Mounted USB-C out of the left edge; the antenna end faces into the board.
ESP_X1 = 11.43                           # pad 1 of both sockets (the USB end), on the 0.254 grid
ESP_YT, ESP_YB = 44.45, 62.23            # top row (TXD ... GPIO9), bottom row (5V ... GPIO5)
DEVKIT = (ESP_X1 - 11.31, ESP_YT - 1.27, ESP_X1 - 11.31 + 36.37, ESP_YB + 1.27)   # its outline: keep other parts out
ANTENNA_KEEPOUT = [(33.2, DEVKIT[1]), (DEVKIT[2], DEVKIT[1]), (DEVKIT[2], DEVKIT[3]), (33.2, DEVKIT[3])]

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
    "TO92": "Package_TO_SOT_THT:TO-92_Inline_Wide",
    "LED3": "LED_THT:LED_D3.0mm",
    "PTC": "Fuse:Fuse_Bourns_MF-RG300",
    "XH3": "Connector_JST:JST_XH_B3B-XH-A_1x03_P2.50mm_Vertical",
    "XH5": "Connector_JST:JST_XH_B5B-XH-A_1x05_P2.50mm_Vertical",
    "XH8": "Connector_JST:JST_XH_B8B-XH-A_1x08_P2.50mm_Vertical",
    "SOCK9": "Connector_PinSocket_2.54mm:PinSocket_1x09_P2.54mm_Vertical",
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

# calendar: U8 (MCP23017 0x22) GPA bit -> 74AHCT245 A input -> B output -> J5 pin -> BKA30D-R5 coil end
CAL_BITS = {"Y1": 0, "Y2": 1, "Y3": 2, "Y4": 3, "M1": 4, "M2": 5, "M3": 6, "M4": 7}   # U8 GPA0-7
CAL_ORDER = ["M4", "M3", "M2", "M1", "Y4", "Y3", "Y2", "Y1"]       # 245 channels 1-8 (A1-A8 / B1-B8)
CAL_PIN = {"Y1": 1, "Y2": 2, "Y3": 3, "Y4": 4, "M1": 5, "M2": 6, "M3": 7, "M4": 8}   # J5
CAL_HALL_BITS = {"YEAR": 0, "MOON": 1}                              # U8 GPB0-1

# ESP32-C6 GPIO use (the rest of the header pins stay unconnected)
ESP_GPIO = {18: "SCL", 19: "SDA", 20: "INT_A", 23: "INT_B", 2: "PWM", 1: "IO1", 3: "IO3"}

def mcp_pin(port, bit):
    return (21 + bit) if port == "GPA" else (1 + bit)

P = {}

def part(ref, fp, value, mpn, x, y, rot, pads, note=""):
    P[ref] = dict(fp=FP[fp], value=value, mpn=mpn, x=x, y=y, rot=rot, pads={str(k): v for k, v in pads.items()}, note=note)

# ---- ESP32-C6-LCD-1.47 sockets, pad 1 at the USB (left) end of each row
TOP_ROW = ["TXD", 17, 13, 12, 23, 20, 19, 18, 9]        # 17 = RXD (GPIO17), TXD = GPIO16
BOT_ROW = ["5V", "GND", "3V3", 0, 1, 2, 3, 4, 5]
def esp_pads(row):
    out = {}
    for k, name in enumerate(row):
        n = {"5V": "ESP_5V", "GND": "GND", "3V3": "+3V3"}.get(name) if isinstance(name, str) else ESP_GPIO.get(name)
        if n:
            out[k + 1] = n
    return out
part("J1", "SOCK9", "ESP32-C6 top row", "1x9 female header, 2.54 mm, about 8.5 mm tall", ESP_X1, ESP_YT, 90, esp_pads(TOP_ROW),
     "ESP32-C6-LCD-1.47: TXD RXD 13 12 23 20 19 18 9 (from the USB end)")
part("J2", "SOCK9", "ESP32-C6 bottom row", "1x9 female header, 2.54 mm, about 8.5 mm tall", ESP_X1, ESP_YB, 90, esp_pads(BOT_ROW),
     "ESP32-C6-LCD-1.47: 5V GND 3V3 0 1 2 3 4 5 (from the USB end)")

# ---- motor sockets, top edge
MPITCH = 21.0
for i, m in enumerate(MOTORS):
    part(f"J{10 + i}", "XH5", f"MOTOR {m}", "JST B5B-XH-A", 10.15 + MPITCH * i, 4.6, 0,
         {1: f"{m}_A", 2: f"{m}_B", 3: f"{m}_C", 4: f"{m}_D", 5: "HOLD"}, "28BYJ-48 plug: blue pink yellow orange red")

# ---- ULN2803A (DIP-18): inputs 1-8 (1B-8B), 9 GND, 10 COM, outputs 18..11 (1C..8C); centred under their socket pairs
for u, x in (("U6", 15.494), ("U5", 57.404), ("U4", 99.568)):
    pads = {9: "GND", 10: "HOLD"}
    for m, (uu, off) in ULN_OF.items():
        if uu == u:
            for k in range(4):
                pads[1 + off + k] = f"{m}_IN{COIL[k]}"
                pads[18 - off - k] = f"{m}_{COIL[k]}"
    part(u, "DIP18", "ULN2803A", "ULN2803A (DIP-18) + socket", x, 21.59, 90, pads)

# ---- MCP23017-E/SP (DIP-28): 1-8 GPB0-7, 9 VDD, 10 VSS, 12 SCL, 13 SDA, 15-17 A0-A2, 18 RESET, 19 INTB, 21-28 GPA0-7
def mcp(ref, x, y, addr, extra):
    a = [("+3V3" if (addr >> k) & 1 else "GND") for k in range(3)]
    pads = {9: "+3V3", 10: "GND", 12: "SCL", 13: "SDA", 15: a[0], 16: a[1], 17: a[2], 18: "MCP_RST"}
    for m, bits in MOTOR_BITS.items():
        for k, (u, port, bit) in enumerate(bits):
            if u == ref:
                pads[mcp_pin(port, bit)] = f"{m}_IN{COIL[k]}"
    pads.update(extra)
    part(ref, "DIP28", "MCP23017", "MCP23017-E/SP (DIP-28) + socket", x, y, 90, pads)

mcp("U2", 55.372, 34.29, 0, {})                                                                          # 0x20
mcp("U3", 13.462, 34.29, 1, {19: "INT_A", **{1 + b: f"HALL_{h}" for h, b in HALL_BITS.items()}})         # 0x21
mcp("U8", 40.64, 54.61, 2, {19: "INT_B", **{21 + b: f"CTL_{c}" for c, b in CAL_BITS.items()},
                            **{1 + b: f"HALL_{h}" for h, b in CAL_HALL_BITS.items()}})                   # 0x22

# ---- 74AHCT245 (DIP-20): drives the calendar coils at 5 V. 1 DIR, 2-9 A1-A8, 10 GND, 18..11 B1..B8, 19 OE, 20 VCC
pads = {1: "+5V", 10: "GND", 19: "GND", 20: "+5V"}
for k, ch in enumerate(CAL_ORDER):
    pads[2 + k] = f"CTL_{ch}"
    pads[18 - k] = f"CAL_{ch}"
part("U7", "DIP20", "74AHCT245", "SN74AHCT245N (DIP-20) + socket", 80.01, 54.61, 90, pads,
     "calendar coil driver; drive one gauge motor at a time (38 mA per chip)")
part("J5", "XH8", "CALENDAR", "JST B8B-XH-A", 135.8, 50.0, 90, {v: f"CAL_{k}" for k, v in CAL_PIN.items()},
     "BKA30D-R5: 1-4 motor A (year, outer shaft), 5-8 motor B (moon, inner); coils are pins 1-2 / 3-4 of each")
part("RN1", "SIP9", "8x10k bussed", "Bourns 4609X-101-103LF", 78.74, 60.3, 0,
     {1: "GND", **{2 + k: f"CTL_{ch}" for k, ch in enumerate(["Y1", "Y2", "Y3", "Y4", "M1", "M2", "M3", "M4"])}},
     "holds the calendar coils off until U8 is set up (its outputs start as inputs)")

# ---- Hall latches, bottom edge (3V3, OUT, GND), and their pull-ups
for i, h in enumerate(HALLS):
    part(f"J{20 + i}", "XH3", f"HALL {h}", "JST B3B-XH-A", 10.15 + 11.9 * i, 76.88, 0, {1: "+3V3", 2: f"HALL_{h}", 3: "GND"},
         "DRV5013 (TO-92): 3V3, OUT, GND")
part("RN2", "SIP8", "7x10k bussed", "Bourns 4608X-101-103LF", 44.45, 69.0, 0,
     {1: "+3V3", **{2 + i: f"HALL_{h}" for i, h in enumerate(HALLS)}}, "Hall pull-ups (DRV5013 is open-drain)")

# ---- power: jack -> PTC -> +5V bus; high-side PWM switch for the motor common (HOLD)
part("J3", "JACK", "5V IN", "CUI (Same Sky) PJ-102AH, 5.5 x 2.1 mm", 126.3, 66.0, 90, {1: "VIN", 2: "GND", 3: "GND"},
     "centre positive")
part("F1", "PTC", "PTC 2.5A", "Bourns MF-R250 (2.5 A hold, radial)", 120.5, 68.5, 90, {1: "VIN", 2: "+5V"})
part("C1", "CP10", "1000uF 10V", "1000 uF 16 V radial, 10 mm dia, 5 mm pitch", 106.0, 62.5, 0, {1: "+5V", 2: "GND"})
part("Q1", "TO220", "IRLIB9343", "IRLIB9343PBF logic-level P-FET, TO-220", 110.0, 41.0, 0, {1: "Q1_G", 2: "HOLD", 3: "+5V"})
part("R5", "RV", "1k", "1/4 W", 120.0, 47.5, 0, {1: "Q1_G", 2: "+5V"}, "gate pull-up: 1k so the gate turns off fast at 20 kHz")
part("Q2", "TO92", "2N3904", "2N3904 NPN, TO-92 (E B C)", 110.5, 47.5, 0, {1: "GND", 2: "Q2_B", 3: "Q1_G"})
part("R6", "RV", "1k", "1/4 W", 110.5, 53.0, 0, {1: "PWM", 2: "Q2_B"})
part("R7", "RV", "10k", "1/4 W", 116.0, 53.0, 0, {1: "Q2_B", 2: "GND"}, "holds the motors off while the ESP32 boots")
part("D2", "DO41", "1N5819", "1N5819 Schottky", 120.0, 41.0, 0, {1: "HOLD", 2: "GND"}, "freewheel path when the PWM switch opens")
part("D1", "DO41", "1N5819", "1N5819 Schottky", 9.9, 37.5, 90, {1: "ESP_5V", 2: "+5V"}, "5 V to the ESP32 board; blocks USB back-feed")
part("LED1", "LED3", "PWR", "3 mm LED, green", 99.0, 67.5, 0, {1: "GND", 2: "LED_A"})
part("R8", "RV", "1k", "1/4 W", 99.0, 63.5, 0, {1: "LED_A", 2: "+5V"})

# ---- decoupling, right at each chip's supply pins
part("C5", "CD", "100nF", "100 nF ceramic, 2.5 mm pitch", 106.3, 46.8, 90, {1: "+5V", 2: "GND"}, "74AHCT245")
part("C6", "CD", "100nF", "100 nF ceramic, 2.5 mm pitch", 33.782, 37.6, 0, {1: "+3V3", 2: "GND"}, "U3")
part("C7", "CD", "100nF", "100 nF ceramic, 2.5 mm pitch", 75.692, 37.6, 0, {1: "+3V3", 2: "GND"}, "U2")
part("C8", "CD", "100nF", "100 nF ceramic, 2.5 mm pitch", 60.96, 57.9, 0, {1: "+3V3", 2: "GND"}, "U8")

# ---- I2C / interrupt / reset pull-ups
part("R1", "RV", "4.7k", "1/4 W", 57.0, 40.7, 0, {1: "SDA", 2: "+3V3"})
part("R2", "RV", "4.7k", "1/4 W", 62.3, 40.7, 0, {1: "SCL", 2: "+3V3"})
part("R3", "RV", "10k", "1/4 W", 67.6, 40.7, 0, {1: "INT_A", 2: "+3V3"})
part("R9", "RV", "10k", "1/4 W", 72.9, 40.7, 0, {1: "INT_B", 2: "+3V3"})
part("R4", "RV", "10k", "1/4 W", 78.2, 40.7, 0, {1: "MCP_RST", 2: "+3V3"})

# ---- expansion header on the left edge: I2C for an RTC later, two free ESP32 pins
part("J4", "HDR6", "EXP", "1x06 male header, 2.54 mm", 2.54, 11.43, 0, {
    1: "+3V3", 2: "GND", 3: "SDA", 4: "SCL", 5: "IO1", 6: "IO3"}, "3V3 GND SDA SCL GPIO1 GPIO3")

for i, (hx, hy) in enumerate(HOLES):
    part(f"H{i + 1}", "HOLE", "M3", "M3 x 30 standoff", hx, hy, 0, {})

# ---- net classes: name -> (track width, clearance, nets). GND is poured, not routed.
NETCLASS = {
    "Power": (1.0, 0.25, ["+5V", "VIN", "HOLD"]),
    "Gnd": (0.5, 0.2, ["GND"]),                    # 0.2: Freerouting never sees GND (the pours carry it)
    "Supply": (0.5, 0.2, ["ESP_5V"]),
    "Logic3V3": (0.3, 0.2, ["+3V3"]),              # ~50 mA: narrow enough to pass between 2.54 mm pads
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

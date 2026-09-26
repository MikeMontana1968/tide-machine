"""Build pack for the Rev M tide machine: bill of materials + wiring.

    python buildpack.py   ->  bom.csv          (order list, opens in Excel)
                              build_pack.html  (BOM + wiring diagram + pin map; published as an artifact)

One source for both, so the order list and the page cannot disagree.
Quantities follow the Rev M design in RESUME.md / station_study.py.
"""
import csv, html

VERIFY = "verify"
LATER = "later"

BOM = [
    # section, item, spec / part number, need, order, notes, flag
    ("Motion", "Stepper + driver board", "28BYJ-48 5 V (64:1) with ULN2003 board, sold as a kit", "6", "7",
     "Five stations + the drum. A 10-pack is usually cheaper per unit.", ""),
    ("Motion", "Dual-shaft gauge stepper", "BKA30D-R5 (continuous 360° version)", "1", "2",
     "Calendar: outer shaft = year dial, inner shaft = moon disc. Confirm both shafts spin all the way round, and measure shaft diameters and lengths, before building around it.", VERIFY),
    ("Motion", "V-groove bearing", "V623ZZ, 3 × 12 × 4 mm", "22", "25",
     "12 rail pulleys, 5 arms, 1 pen pulley, 4 pen carriage. Measure the groove root radius (4.8 assumed) and V angle (90° assumed) on arrival.", VERIFY),
    ("Motion", "Steel rod", "3 mm ground stainless (h6), or 1/8″ (3.175 mm) O-1 drill rod", "2 × 170 mm", "2 × 300 mm",
     "Pen guide rods, cut to 170 socket bottom to socket bottom. 4 mm and up won't seat in the V623's groove.", ""),
    ("Motion", "Shim washer", "3 × 5 × 0.5 mm (OD must be 5 mm or less)", "10", "20",
     "Between the two bearings in each pulley bracket (6), and behind each pen-carriage bearing (4). A standard M3 washer rubs the bearing shields.", ""),
    ("Motion", "Monofilament line", "0.30 mm fluorocarbon (about 12 lb)", "about 2 m", "1 spool",
     "Not nylon: nylon absorbs moisture and wanders with humidity.", ""),
    ("Motion", "Crimp sleeves", "Aluminium or copper, 0.6–0.8 mm ID, for 0.3 mm line", "4", "20", "Crimp, don't knot.", ""),

    ("Sensing", "Hall-effect latch", "TI DRV5013, SOT-23 (DBZ) package", "7", "10",
     "Five stations + year + moon. Choose a variant that switches at a few mT, so a nearby motor's stray field can't trip it; bench-test one beside a running 28BYJ-48.", VERIFY),
    ("Sensing", "Magnets", "N52 neodymium disc, 5 × 2 mm, axially magnetised", "14 (7 pairs)", "20",
     "Glued into the pockets in the back of each dial, opposite poles facing the sensor.", ""),
    ("Sensing", "Sensor boards", "SOT-23-to-DIP breakout boards (or a small custom PCB, 10 × 16 mm)", "7", "10",
     "Each carries the latch, a 10 kΩ pull-up and a 100 nF capacitor. The chip nests in a window in the faceplate.", ""),

    ("Electronics", "Microcontroller", "ESP32-DevKitC-32E (ESP32-WROOM-32E)", "1", "2", "", ""),
    ("Electronics", "I/O expander", "MCP23017-E/SP, DIP-28", "2", "3",
     "#1 at 0x20 drives four stations; #2 at 0x21 drives M2, the drum, and reads the five station Hall latches.", ""),
    ("Electronics", "Gauge-motor driver", "AX1201728SG quad micro-step driver, step/dir (VID6606 is equivalent) + SOIC-28 breakout", "1", "2",
     "Drives the BKA30D-R5's two motors. Confirm pinout and input thresholds from its datasheet.", VERIFY),
    ("Electronics", "Level shifter", "SN74AHCT245N, DIP-20", "1", "2",
     "3.3 V to 5 V for the gauge driver's step, direction and reset lines.", ""),
    ("Electronics", "P-channel MOSFET", "AO3401A, SOT-23 (on a breakout)", "1", "3",
     "PWM hold: switches the motors' 5 V. Fit it if the holding-torque test says you need it.", ""),
    ("Electronics", "N-channel MOSFET", "2N7000, TO-92", "1", "5", "Gate driver for the P-channel switch.", ""),
    ("Electronics", "Power supply", "5 V 3 A regulated, 5.5 × 2.1 mm barrel plug", "1", "1",
     "Peak draw about 1.5 A with every motor energised.", ""),
    ("Electronics", "Barrel jack", "5.5 × 2.1 mm, panel or PCB mount", "1", "2", "", ""),
    ("Electronics", "Schottky diode", "1N5819", "1", "5",
     "Between the 5 V bus and the ESP32's 5 V pin, so USB and the supply never fight.", ""),
    ("Electronics", "Electrolytic capacitor", "1000 µF 10 V", "1", "2", "Across 5 V and GND near the ULN2003 boards.", ""),
    ("Electronics", "Ceramic capacitors", "100 nF", "12", "25", "One at every IC and sensor board.", ""),
    ("Electronics", "Resistors", "1/4 W: 10 kΩ (×12), 4.7 kΩ (×2), 100 Ω (×1), 100 kΩ (×1)", "16", "an assortment",
     "Hall pull-ups, MCP23017 resets, I²C pull-ups, MOSFET gate.", ""),
    ("Electronics", "Prototype board", "Double-sided perfboard, about 70 × 90 mm", "2", "3",
     "Main board; calendar board (carries the BKA30D-R5 and its two Hall latches behind the faceplate).", ""),
    ("Electronics", "Sockets and headers", "DIP-28 (×2), DIP-20 (×1) sockets; 2.54 mm headers", "", "an assortment", "", ""),
    ("Electronics", "Wire and connectors", "3-core 26 AWG + JST-XH 3-pin (Hall runs); hookup wire", "7 Hall runs", "JST-XH kit + 5 m wire", "", ""),

    ("Fasteners", "M3 × 20 + nyloc", "Button or socket head", "6", "10", "Pulley-bracket axles.", ""),
    ("Fasteners", "M3 × 8 button head", "", "5", "10", "Arm bearing axles.", ""),
    ("Fasteners", "M3 × 16 button head", "", "5", "10",
     "Pen-pulley axle (into the carriage insert), and the 4 carriage bearing axles, which clamp the carriage's two halves.", ""),
    ("Fasteners", "M3 hex nuts", "", "4", "10", "Carriage bearing axles, on the rear plate.", ""),
    ("Fasteners", "M3 × 8 pan head + nut", "Head 2.4 mm tall or less", "12", "20", "Motor ears. The dials clear the heads by 1.1 mm.", ""),
    ("Fasteners", "M3 washers", "", "12", "25", "", ""),
    ("Fasteners", "M3 × 4 heat-set inserts", "OD about 4.6 mm", "6", "20", "Five arms + the pen carriage.", ""),
    ("Fasteners", "M2 × 6 + nut", "", "30", "50", "Arm to hub, Hall boards, calendar board, index tabs, index hand.", ""),
    ("Fasteners", "#4 × 3/4″ flat-head wood screws", "", "12", "20", "Pulley brackets.", ""),
    ("Fasteners", "#6 × 3/4″ wood screws", "", "14", "25", "Faceplate to rails; end posts.", ""),

    ("Frame and materials", "Pine 1 × 2", "19 × 38 mm actual, 8 ft length", "1288 mm", "1 (+1 for mistakes)",
     "Two rails about 492 mm, two posts 152 mm.", ""),
    ("Frame and materials", "Faceplate", "1.5 mm (0.063″) 5052 aluminium, laser cut, about 283 × 176 mm", "1", "not yet",
     "The DXF comes from the Ruby port. Never steel: the Hall sensors look through it.", LATER),
    ("Frame and materials", "PVC pipe", "3″ Schedule 40", "130 mm", "a short length", "The drum.", ""),
    ("Frame and materials", "Drum shaft and bearing", "7 mm steel or brass rod about 200 mm; PTFE tube or bushing; M8 washer", "1 set", "1 set", "", ""),
    ("Frame and materials", "Pen", "Fine fibre-tip, 0.3–0.5 mm", "1", "2", "", ""),
    ("Frame and materials", "Leaf spring", "0.1–0.2 mm spring-steel shim strip", "1", "a small piece", "Pen contact force, about 0.05 N.", ""),
    ("Frame and materials", "Pen ballast", "Steel or lead shot (or tungsten putty)", "about 20 g", "1 pack", "Brings the carriage to 41 g all-up.", ""),
    ("Frame and materials", "PLA filament", "", "about 300 g", "1 spool if not on hand", "", ""),
    ("Frame and materials", "Clear silicone adhesive", "Any small tube (RTV type)", "a dab", "1 tube if not on hand",
     "Fallback only, for a station hub or calendar adapter that's loose on its shaft after the D-bore test coupon. It peels off. Not threadlocker: it barely cures against plastic.", ""),
    ("Frame and materials", "Decal stock", "Laser-printable white vinyl sticker paper, Letter", "1 sheet", "1 pack", "For decals_1to1.pdf.", ""),
]

# wiring: (from, to, signal) -- the pin map printed on the page
PINS = [
    ("Power", [
        ("5 V supply +", "5 V bus", "+5V"),
        ("5 V bus", "ESP32 5V pin, through 1N5819", "+5V"),
        ("5 V bus", "AO3401A source; 10 kΩ to its gate", "+5V"),
        ("AO3401A drain", "HOLD rail → all six ULN2003 boards (+)", "HOLD"),
        ("2N7000 drain / source", "AO3401A gate / GND", "HOLD"),
        ("5 V bus", "74AHCT245 VCC (20), AX1201728SG VDD", "+5V"),
        ("ESP32 3V3", "MCP23017 VDD (9) ×2, all seven Hall boards, pull-ups", "3V3"),
        ("GND", "Every board, sensor and the supply −", "GND"),
        ("1000 µF", "Across 5 V / GND at the ULN2003 boards", "+5V"),
    ]),
    ("ESP32", [
        ("GPIO21 (SDA)", "MCP23017 #1 & #2 SDA (13); 4.7 kΩ to 3V3", "I²C"),
        ("GPIO22 (SCL)", "MCP23017 #1 & #2 SCL (12); 4.7 kΩ to 3V3", "I²C"),
        ("GPIO27", "← MCP23017 #2 INTB (19): station Hall edge interrupt", "INT"),
        ("GPIO25", "→ 100 Ω → 2N7000 gate (100 kΩ to GND): PWM hold, 20 kHz", "PWM"),
        ("GPIO16", "→ 74AHCT245 A1 (2) → B1 (18) → AX STEP, motor A (year)", "CAL"),
        ("GPIO17", "→ A2 (3) → B2 (17) → AX CW/CCW, motor A", "CAL"),
        ("GPIO18", "→ A3 (4) → B3 (16) → AX STEP, motor B (moon)", "CAL"),
        ("GPIO19", "→ A4 (5) → B4 (15) → AX CW/CCW, motor B", "CAL"),
        ("GPIO23", "→ A5 (6) → B5 (14) → AX RESET", "CAL"),
        ("GPIO32", "← Year Hall OUT", "HALL"),
        ("GPIO33", "← Moon Hall OUT", "HALL"),
    ]),
    ("MCP23017 #1 (0x20: A0, A1, A2 to GND; RESET 18 to 3V3 via 10 kΩ)", [
        ("GPA0–3 (21–24)", "ULN2003 #1 IN1–4 → S2", "MOTOR"),
        ("GPA4–7 (25–28)", "ULN2003 #2 IN1–4 → N2", "MOTOR"),
        ("GPB0–3 (1–4)", "ULN2003 #3 IN1–4 → K1", "MOTOR"),
        ("GPB4–7 (5–8)", "ULN2003 #4 IN1–4 → O1", "MOTOR"),
    ]),
    ("MCP23017 #2 (0x21: A0 to 3V3, A1 and A2 to GND; RESET to 3V3 via 10 kΩ)", [
        ("GPA0–3 (21–24)", "ULN2003 #5 IN1–4 → M2", "MOTOR"),
        ("GPA4–7 (25–28)", "ULN2003 #6 IN1–4 → drum", "MOTOR"),
        ("GPB0–4 (1–5)", "← Hall OUT: S2, N2, K1, O1, M2", "HALL"),
        ("GPB5–7 (6–8)", "spare", ""),
        ("INTB (19)", "→ ESP32 GPIO27 (open-drain, pulled up)", "INT"),
    ]),
    ("Calendar board (behind the faceplate)", [
        ("74AHCT245 DIR (1) / OE (19)", "5 V (A → B) / GND; unused A6–A8 to GND", "CAL"),
        ("AX1201728SG motor A outputs", "BKA30D-R5 motor A, pins 1–4", "CAL"),
        ("AX1201728SG motor B outputs", "BKA30D-R5 motor B, pins 1–4", "CAL"),
        ("Year / Moon Hall latches", "On the same board, chips nested in faceplate windows", "HALL"),
    ]),
    ("Each Hall board (DRV5013)", [
        ("VCC / GND", "3V3 / GND, 100 nF across them", "3V3"),
        ("OUT (open drain)", "10 kΩ to 3V3, to its MCP23017 or ESP32 input", "HALL"),
    ]),
]

# ----------------------------------------------------------------- outputs --
with open("bom.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["Section", "Item", "Spec / part number", "Need", "Order", "Notes", "Flag"])
    for row in BOM:
        w.writerow([row[0], row[1], row[2], row[3], row[4], row[5],
                    {"verify": "VERIFY BEFORE BUILDING AROUND IT", "later": "NOT YET"}.get(row[6], "")])

def esc(s):
    return html.escape(s, quote=False)

rows, current = [], None
for sec, item, spec, need, order, notes, flag in BOM:
    if sec != current:
        rows.append(f'<tr class="sec"><th colspan="4" scope="colgroup">{esc(sec)}</th></tr>')
        current = sec
    pill = {"verify": '<span class="pill verify">verify first</span>',
            "later": '<span class="pill later">not yet</span>'}.get(flag, "")
    rows.append(f'<tr><td class="item">{esc(item)}{pill}<div class="spec">{esc(spec)}</div></td>'
                f'<td class="num">{esc(need)}</td><td class="num">{esc(order)}</td><td class="note">{esc(notes)}</td></tr>')
pin_html = []
for title, conns in PINS:
    pin_html.append(f'<tr class="sec"><th colspan="3" scope="colgroup">{esc(title)}</th></tr>')
    for a, b, sig in conns:
        tag = f'<span class="net n-{sig.lower().replace(chr(178), "2").replace("+", "p")}">{esc(sig)}</span>' if sig else ""
        pin_html.append(f'<tr><td class="pin">{esc(a)}</td><td>{esc(b)}</td><td>{tag}</td></tr>')

n_verify = sum(1 for r in BOM if r[6] == VERIFY)
tmpl = open("build_pack.tmpl.html", encoding="utf8").read()
page = (tmpl.replace("{{BOM}}", "\n".join(rows)).replace("{{PINS}}", "\n".join(pin_html))
            .replace("{{NLINES}}", str(len(BOM))).replace("{{NVERIFY}}", str(n_verify)))
open("build_pack.html", "w", encoding="utf8").write(page)
print(f"bom.csv ({len(BOM)} lines, {n_verify} to verify, 1 not yet) and build_pack.html written")

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
    ("Motion", "Stepper motor", "28BYJ-48 5 V (64:1), usually sold as a kit with a ULN2003 board", "6", "7",
     "Five stations + the drum. The motors plug straight into the main board; the kit's driver boards aren't needed. A 10-pack is usually cheaper per unit.", ""),
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

    ("Sensing", "Hall-effect latch", "TI DRV5013AGQLPG (±6 mT, through-hole TO-92); a few DRV5013BCQLPG (±12 mT) to compare", "7", "10",
     "Five stations + year + moon. Choose a variant that switches at a few mT, so a nearby motor's stray field can't trip it; bench-test one beside a running 28BYJ-48. The TO-92 needs a slightly larger plate window than the old SOT-23 plan.", VERIFY),
    ("Sensing", "Magnets", "N52 neodymium disc, 5 × 2 mm, axially magnetised", "14 (7 pairs)", "20",
     "Glued into the pockets in the back of each dial, opposite poles facing the sensor.", ""),
    ("Sensing", "Sensor carriers", "Cut from the perfboard below, about 10 × 16 mm each", "7", "",
     "Each holds a latch flat in its plate window, with a 100 nF capacitor across its supply and a 3-core lead to the main board.", ""),

    ("Main board", "Printed circuit board", "2-layer, 1.6 mm, 140 × 81.3 mm (5.5 × 3.2 in), from the Gerbers in pcb/", "1", "5 (the usual minimum)",
     "Routed and DRC-clean: upload pcb/tide_main_gerbers.zip to JLCPCB (2 layers, 1.6 mm, HASL). Mounts behind the faceplate on four standoffs.", ""),
    ("Main board", "Microcontroller", "Waveshare ESP32-C6-LCD-1.47 (ESP32-C6, 1.47-inch 172 × 320 LCD)", "1", "a 2-pack",
     "Bought separately. Plugs into the socket below, USB-C out of the board's left edge. Uses GPIO 18/19 (I²C), 20 and 23 (interrupts), 2 (hold PWM); 1 and 3 go to the expansion header.", ""),
    ("Main board", "ESP32 socket", "1 × 9 female header, 2.54 mm pitch, about 8.5 mm tall (Samtec SSW-109-01-T-S)", "2", "3",
     "The C6 board plugs in, so it can be swapped or flashed off the board. Rows are 17.78 mm apart.", ""),
    ("Main board", "I/O expander", "MCP23017-E/SP, DIP-28", "3", "4",
     "0x20 drives O1, K1, N2, S2; 0x21 drives M2 and the drum and reads the five station latches; 0x22 drives the calendar coils and reads the year and moon latches.", ""),
    ("Main board", "Motor driver", "ULN2803A, DIP-18 (8 Darlingtons with clamp diodes)", "3", "4",
     "Two motors each. The clamp common goes to the switched HOLD rail.", ""),
    ("Main board", "Calendar driver", "SN74AHCT245N, DIP-20", "1", "2",
     "Takes the 0x22 expander's eight 3.3 V outputs and drives the BKA30D-R5's coils at 5 V, one motor at a time. The calendar creeps about 1°/day, so microstepping buys nothing.", ""),
    ("Main board", "IC sockets", "DIP-28 (×3), DIP-18 (×3), DIP-20 (×1)", "7", "7", "", ""),
    ("Main board", "P-channel MOSFET", "IRLIB9343PBF, TO-220 (logic level: rated at −4.5 V gate)", "1", "2",
     "PWM hold: switches the motors' 5 V. Stands upright; no heatsink at 1.2 A.", ""),
    ("Main board", "NPN transistor", "2N3904, TO-92", "1", "5", "Drives the P-FET's gate from the ESP32's 3.3 V.", ""),
    ("Main board", "Schottky diode", "1N5819, DO-41", "2", "5",
     "One feeds the ESP32's 5 V pin (so USB and the supply never fight); one gives the motor current a path when the PWM switch opens.", ""),
    ("Main board", "Resettable fuse", "Bourns MF-R250 (2.5 A hold), radial", "1", "2", "Between the jack and the 5 V bus.", ""),
    ("Main board", "Electrolytic capacitor", "1000 µF 10 V radial, 10 mm dia, 5 mm lead pitch", "1", "2", "", ""),
    ("Main board", "Ceramic capacitors", "100 nF, 2.5 mm lead pitch", "11", "25", "Four on the main board, one on each Hall carrier.", ""),
    ("Main board", "Resistors", "1/4 W, mounted upright: 1 kΩ (×3), 10 kΩ (×4), 4.7 kΩ (×2)", "9", "an assortment",
     "P-FET gate pull-up, transistor base, LED; base pull-down, two interrupt pull-ups and the reset pull-up; I²C pull-ups.", ""),
    ("Main board", "Resistor networks", "Bussed 10 kΩ SIP: Bourns 4608X-101-103LF (8-pin) and 4609X-101-103LF (9-pin)", "1 each", "2 each",
     "Hall pull-ups; pull-downs that hold the calendar coils off until the 0x22 expander is set up.", ""),
    ("Main board", "LED", "3 mm, green", "1", "5", "Power indicator.", ""),
    ("Main board", "Barrel jack", "Same Sky PJ-102AH, 5.5 mm, 2.0 mm pin, PCB mount", "1", "2", "The 2.0 mm pin is the standard mate for a 5.5 × 2.1 plug.", ""),
    ("Main board", "Board connectors", "JST-XH headers: B5B-XH-A (×6, motors), B3B-XH-A (×7, Halls), B8B-XH-A (×1, calendar)", "14", "16",
     "The 28BYJ-48's own plug fits B5B-XH-A.", ""),
    ("Main board", "Cable connectors", "JST XHP-3 (×7) and XHP-8 (×1) housings, SXH-001T-P0.6 crimps", "8 housings", "a JST-XH kit",
     "For the Hall and calendar leads. A kit with a crimp tool is easiest.", ""),
    ("Main board", "Expansion header", "1 × 6 male, 2.54 mm", "1", "1", "3V3, GND, SDA, SCL, GPIO1, GPIO3: room for an RTC later.", ""),
    ("Main board", "Power supply", "5 V 3 A regulated, 5.5 × 2.1 mm plug, centre positive (MEAN WELL GST18U05-P1J)", "1", "1",
     "Peak draw about 1.5 A with every motor energised.", ""),

    ("Off-board wiring", "Prototype board", "Double-sided perfboard, about 70 × 90 mm", "1", "2",
     "Calendar carrier (holds the BKA30D-R5 behind the plate) and the seven Hall carriers.", ""),
    ("Off-board wiring", "Wire", "3-core 26 AWG for the Hall runs; 8-core (or ribbon) for the calendar", "7 Hall runs + 1", "5 m of each", "", ""),

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
    ("Fasteners", "M3 × 30 standoffs + M3 × 6 screws", "Female-female hex, brass or nylon", "4 + 8", "4 + 10",
     "Main board to the back of the faceplate, clear of the motors (20.5 deep).", ""),

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

# Mouser order: the electronics only, by manufacturer part number, so Mouser's BOM Tool matches each line itself.
# (mfr part number, manufacturer, qty, Mouser number where confirmed, board refs, description, note)
# Quantities include spares. Not from Mouser: 28BYJ-48 motors, BKA30D-R5, the PCB, bearings, magnets, hardware.
MOUSER = [
    ("SSW-109-01-T-S", "Samtec", 3, "", "J1, J2", "Socket strip 1x9, 2.54 mm, through hole: the ESP32-C6 socket",
     "Any 1x9 2.54 mm female header about 8.5 mm tall will do. (The Waveshare ESP32-C6-LCD-1.47 itself is bought separately.)"),
    ("MCP23017-E/SP", "Microchip", 4, "", "U2, U3, U8", "I/O expander, I2C, DIP-28 (0.3 in)", ""),
    ("ULN2803A", "STMicroelectronics", 4, "511-ULN2803A", "U4, U5, U6", "8x Darlington array, DIP-18", ""),
    ("SN74AHCT245N", "Texas Instruments", 2, "", "U7", "Octal buffer, TTL inputs, DIP-20", ""),
    ("110-43-328-41-001000", "Mill-Max", 3, "", "U2, U3, U8", "DIP socket 28-pin, 0.300 in rows", "0.3 in (skinny) -- not the 0.6 in 28-pin."),
    ("110-43-318-41-001000", "Mill-Max", 3, "", "U4-U6", "DIP socket 18-pin, 0.300 in", ""),
    ("110-43-320-41-001000", "Mill-Max", 1, "", "U7", "DIP socket 20-pin, 0.300 in", ""),
    ("IRLIB9343PBF", "Infineon", 2, "", "Q1", "P-channel MOSFET, logic level, -55 V, TO-220 FullPAK", ""),
    ("2N3904BU", "onsemi", 5, "", "Q2", "NPN transistor, TO-92", ""),
    ("1N5819G", "onsemi", 5, "", "D1, D2", "Schottky diode 1 A 40 V, DO-41", ""),
    ("MF-R250", "Bourns", 2, "", "F1", "PTC resettable fuse 2.5 A hold, radial, 5.1 mm leads", ""),
    ("EEU-FR1C102", "Panasonic", 2, "", "C1", "Electrolytic 1000 uF 16 V, 10 x 16 mm, 5 mm pitch", ""),
    ("C320C104K5R5TA", "KEMET", 25, "", "C5-C8 + Hall carriers", "Ceramic 100 nF 50 V X7R, radial, 2.54 mm leads", ""),
    ("MFR-25FBF52-1K", "YAGEO", 10, "", "R5, R6, R8", "Resistor 1 k 1/4 W 1% metal film", ""),
    ("MFR-25FBF52-10K", "YAGEO", 10, "", "R3, R4, R7, R9", "Resistor 10 k 1/4 W 1% metal film", ""),
    ("MFR-25FBF52-4K7", "YAGEO", 10, "", "R1, R2", "Resistor 4.7 k 1/4 W 1% metal film", ""),
    ("4608X-101-103LF", "Bourns", 2, "", "RN2", "Resistor network 7x 10 k bussed, SIP-8", ""),
    ("4609X-101-103LF", "Bourns", 2, "", "RN1", "Resistor network 8x 10 k bussed, SIP-9", ""),
    ("WP710A10GD", "Kingbright", 2, "604-WP710A10GD", "LED1", "LED 3 mm green", ""),
    ("PJ-102AH", "Same Sky", 2, "490-PJ-102AH", "J3", "DC jack 5.5 mm, 2.0 mm pin, through hole",
     "2.0 mm pin is the standard mate for a '5.5 x 2.1' plug. Don't use a 2.5 mm plug."),
    ("B5B-XH-A(LF)(SN)", "JST", 7, "", "J10-J15", "XH header 5-pin, top entry", "The 28BYJ-48's own plug fits."),
    ("B3B-XH-A(LF)(SN)", "JST", 8, "", "J20-J26", "XH header 3-pin, top entry", ""),
    ("B8B-XH-A(LF)(SN)", "JST", 2, "", "J5", "XH header 8-pin, top entry", ""),
    ("XHP-3", "JST", 10, "", "Hall cables", "XH housing 3-pin", ""),
    ("XHP-8", "JST", 2, "", "Calendar cable", "XH housing 8-pin", ""),
    ("SXH-001T-P0.6", "JST", 50, "", "Hall + calendar cables", "XH crimp contact, 22-28 AWG", "Crimp with a generic JST-XH crimper."),
    ("61300611121", "Wurth Elektronik", 2, "", "J4", "Pin header 1x6, 2.54 mm", ""),
    ("DRV5013AGQLPG", "Texas Instruments", 8, "", "Hall carriers", "Hall latch +/-6 mT, TO-92 (LPG)",
     "Bench-test beside a running 28BYJ-48 before building seven carriers."),
    ("DRV5013BCQLPG", "Texas Instruments", 3, "", "(bench test)", "Hall latch +/-12 mT, TO-92 (LPG)",
     "The less sensitive variant, in case motor stray fields trip the AG."),
    ("GST18U05-P1J", "MEAN WELL", 1, "", "(power)", "5 V 3 A wall adapter, 5.5 x 2.1 mm plug, centre positive",
     "The SGA18U05-P1J is being discontinued. Any 5 V 3 A centre-positive 5.5 x 2.1 adapter will do."),
]

# wiring: (from, to, signal) -- the pin map printed on the page
PINS = [
    ("Power (main board)", [
        ("5 V jack J3, centre pin", "MF-R250 fuse F1 → +5V bus", "+5V"),
        ("+5V bus", "1000 µF C1; the ESP32-C6 board's 5V pin through 1N5819 D1", "+5V"),
        ("+5V bus", "IRLIB9343 Q1 source (3); 1 kΩ to its gate (1)", "+5V"),
        ("Q1 drain (2)", "HOLD rail → pin 5 (red) of all six motor sockets, and COM (10) of all three ULN2803A", "HOLD"),
        ("2N3904 Q2 collector / emitter", "Q1 gate / GND", "HOLD"),
        ("1N5819 D2", "anode GND, cathode HOLD: the freewheel path", "HOLD"),
        ("+5V bus", "74AHCT245 VCC (20) and DIR (1)", "+5V"),
        ("ESP32-C6 3V3 (out)", "MCP23017 VDD (9) ×3, Hall sockets pin 1, pull-ups, expansion header (800 mA regulator)", "3V3"),
        ("GND", "Every chip, socket and the supply −; poured on both layers", "GND"),
    ]),
    ("ESP32-C6-LCD-1.47 (in its socket)", [
        ("GPIO19 (SDA)", "MCP23017 ×3 SDA (13); 4.7 kΩ to 3V3; expansion pin 3", "I²C"),
        ("GPIO18 (SCL)", "MCP23017 ×3 SCL (12); 4.7 kΩ to 3V3; expansion pin 4", "I²C"),
        ("GPIO20", "← MCP23017 0x21 INTB (19), 10 kΩ pull-up: station Hall edges", "INT"),
        ("GPIO23", "← MCP23017 0x22 INTB (19), 10 kΩ pull-up: year / moon Hall edges", "INT"),
        ("GPIO2", "→ 1 kΩ → 2N3904 base (10 kΩ to GND): PWM hold, 20 kHz", "PWM"),
        ("GPIO1, GPIO3", "expansion pins 5, 6 (spare)", ""),
        ("on the board itself", "LCD 6, 7, 14, 15, 21, 22; SD card 4, 5; RGB LED 8; USB 12, 13; BOOT 9 (all left alone)", ""),
    ]),
    ("MCP23017 0x20 (A0–A2 to GND; RESET 18 to 3V3 via 10 kΩ, shared by all three)", [
        ("GPA7–4 (28–25)", "ULN2803A 1B–4B → O1 socket A–D", "MOTOR"),
        ("GPA3–0 (24–21)", "ULN2803A 5B–8B → K1 socket A–D", "MOTOR"),
        ("GPB7–4 (8–5)", "ULN2803A 1B–4B → N2 socket A–D", "MOTOR"),
        ("GPB3–0 (4–1)", "ULN2803A 5B–8B → S2 socket A–D", "MOTOR"),
    ]),
    ("MCP23017 0x21 (A0 to 3V3, A1 and A2 to GND)", [
        ("GPA7–4 (28–25)", "ULN2803A 1B–4B → drum socket A–D", "MOTOR"),
        ("GPA3–0 (24–21)", "ULN2803A 5B–8B → M2 socket A–D", "MOTOR"),
        ("GPB0–4 (1–5)", "← Hall sockets M2, O1, K1, N2, S2 (10 kΩ bussed pull-ups)", "HALL"),
        ("INTB (19)", "→ ESP32 GPIO20", "INT"),
    ]),
    ("MCP23017 0x22 (A1 to 3V3, A0 and A2 to GND)", [
        ("GPA0–3 (21–24)", "→ 74AHCT245 → year motor coil ends 1–4 (calendar socket 1–4)", "CAL"),
        ("GPA4–7 (25–28)", "→ 74AHCT245 → moon motor coil ends 1–4 (calendar socket 5–8)", "CAL"),
        ("GPB0, GPB1 (1, 2)", "← year, moon Hall sockets", "HALL"),
        ("INTB (19)", "→ ESP32 GPIO23", "INT"),
    ]),
    ("Sockets on the board edge", [
        ("Motor ×6 (JST-XH 5)", "1 A blue, 2 B pink, 3 C yellow, 4 D orange (ULN outputs); 5 red (HOLD)", "MOTOR"),
        ("Hall ×7 (JST-XH 3)", "1 3V3, 2 OUT, 3 GND", "HALL"),
        ("Calendar (JST-XH 8)", "1–4 year coil ends (74AHCT245 B8–B5), 5–8 moon (B4–B1); coils are 1–2 and 3–4 of each", "CAL"),
        ("Expansion (1 × 6)", "3V3, GND, SDA, SCL, GPIO1, GPIO3", "I²C"),
    ]),
    ("Each Hall carrier (DRV5013, TO-92)", [
        ("VCC / GND", "3V3 / GND, 100 nF across them", "3V3"),
        ("OUT (open drain)", "to its socket pin 2; the pull-up is on the main board", "HALL"),
    ]),
]

# ----------------------------------------------------------------- outputs --
with open("bom.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["Section", "Item", "Spec / part number", "Need", "Order", "Notes", "Flag"])
    for row in BOM:
        w.writerow([row[0], row[1], row[2], row[3], row[4], row[5],
                    {"verify": "VERIFY BEFORE BUILDING AROUND IT", "later": "NOT YET"}.get(row[6], "")])

with open("mouser_bom.csv", "w", newline="", encoding="ascii") as f:
    w = csv.writer(f)
    w.writerow(["Mouser Part Number", "Manufacturer Part Number", "Manufacturer", "Quantity", "Description", "Customer Part Number", "Notes"])
    for mpn, mfr, qty, mno, refs, desc, note in MOUSER:
        w.writerow([mno, mpn, mfr, qty, desc, refs, note])

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

mouser_html = [f'<tr><td class="item">{esc(mpn)}<div class="spec">{esc(mfr)}{" · " + esc(mno) if mno else ""}</div></td>'
               f'<td class="num">{qty}</td><td class="note">{esc(desc)}{"<br><i>" + esc(note) + "</i>" if note else ""}</td></tr>'
               for mpn, mfr, qty, mno, refs, desc, note in MOUSER]
n_verify = sum(1 for r in BOM if r[6] == VERIFY)
n_later = sum(1 for r in BOM if r[6] == LATER)
tmpl = open("build_pack.tmpl.html", encoding="utf8").read()
page = (tmpl.replace("{{BOM}}", "\n".join(rows)).replace("{{PINS}}", "\n".join(pin_html))
            .replace("{{NLINES}}", str(len(BOM))).replace("{{NVERIFY}}", str(n_verify)).replace("{{NLATER}}", str(n_later)).replace("{{MOUSER}}", "\n".join(mouser_html))
            .replace("{{NMOUSER}}", str(len(MOUSER))))
open("build_pack.html", "w", encoding="utf8").write(page)
print(f"bom.csv ({len(BOM)} lines, {n_verify} to verify, {n_later} not yet), mouser_bom.csv ({len(MOUSER)} lines) and build_pack.html written")

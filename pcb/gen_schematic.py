"""Write tide_main.kicad_sch from design.py: KiCad's own symbols, one net label on every connected pin.

    python gen_schematic.py     ->  tide_main.kicad_sch

A label-connected schematic of exactly the netlist the board is built from (design.py), so the two can't
disagree. Symbols come from KiCad 10's installed libraries (derived symbols flattened); unused pins get
no-connect flags. Laid out by function on an A2 sheet.
"""
import os, uuid, math
import fplib, design
from fplib import Q, parse, dump, find, findall, nums

HERE = os.path.dirname(os.path.abspath(__file__))
SYMLIB = r"C:\Program Files\KiCad\10.0\share\kicad\symbols"
OUT = os.path.join(HERE, "tide_main.kicad_sch")
U = lambda: Q(str(uuid.uuid4()))

# design.py footprint key -> KiCad symbol, and the value shown
def symbol_for(ref, p):
    fp = p["fp"]
    if "DIP-28" in fp: return "Interface_Expansion:MCP23017x-x-SP"
    if "DIP-18" in fp: return "Transistor_Array:ULN2803A"
    if "DIP-20" in fp: return "74xx:74HC245"
    if "R_Array_SIP9" in fp: return "Device:R_Network08"
    if "R_Array_SIP8" in fp: return "Device:R_Network07"
    if "R_Axial" in fp: return "Device:R"
    if "CP_Radial" in fp: return "Device:C_Polarized"
    if "C_Disc" in fp: return "Device:C"
    if "DO-41" in fp: return "Device:D_Schottky"
    if "LED" in fp: return "Device:LED"
    if "TO-220" in fp: return "Transistor_FET:Q_PMOS_GDS"
    if "TO-92" in fp: return "Transistor_BJT:2N3904"
    if "Fuse" in fp: return "Device:Polyfuse"
    if "BarrelJack" in fp: return "Connector:Barrel_Jack_Switch"
    if "MountingHole" in fp: return "Mechanical:MountingHole"
    n = len(fplib.load(fp).pads)
    return f"Connector_Generic:Conn_01x{n:02d}"

_libs = {}
def lib_symbol(lib_id):
    lib, name = lib_id.split(":")
    if lib not in _libs:
        tree = parse(open(os.path.join(SYMLIB, lib + ".kicad_sym"), encoding="utf8").read())
        _libs[lib] = {str(e[1]): e for e in tree if isinstance(e, list) and e and e[0] == "symbol"}
    syms = _libs[lib]
    e = syms[name]
    ext = find(e, "extends")
    if ext is None:
        return rename(e, name, lib_id)
    base = lib_symbol(f"{lib}:{ext[1]}")                      # flattened parent, already named lib:parent
    out = [x for x in base if not (isinstance(x, list) and x and x[0] == "property")]
    out[1] = Q(lib_id)
    props = [x for x in e if isinstance(x, list) and x and x[0] == "property"]
    pnames = {str(x[1]) for x in props}
    props += [x for x in base if isinstance(x, list) and x and x[0] == "property" and str(x[1]) not in pnames]
    # sub-symbols carry the parent's name: rename to this one
    body = []
    for x in out[2:]:
        if isinstance(x, list) and x and x[0] == "symbol":
            x = [x[0], Q(str(x[1]).replace(str(ext[1]), name, 1))] + x[2:]
        body.append(x)
    return [out[0], Q(lib_id)] + props + [x for x in body if not (isinstance(x, list) and x and x[0] == "extends")]

def rename(e, name, lib_id):
    out = [e[0], Q(lib_id)]
    for x in e[2:]:
        if isinstance(x, list) and x and x[0] == "extends":
            continue
        out.append(x)
    return out

def pins_of(sym):
    """[(number, x, y, angle)] in symbol coordinates (y up), from every unit"""
    out = []
    def walk(n):
        for c in n:
            if isinstance(c, list) and c:
                if c[0] == "pin":
                    at = nums(c, "at")
                    num = find(c, "number")
                    out.append((str(num[1]), at[0], at[1], at[2] if len(at) > 2 else 0.0))
                else:
                    walk(c)
    walk(sym)
    return out

def unhide_pins(sym):
    """power pins hidden in the library would join nets by name: make every pin visible and explicit"""
    def walk(n):
        for i, c in enumerate(n):
            if isinstance(c, list) and c:
                if c[0] == "pin":
                    n[i] = [x for x in c if not (x == "hide" or (isinstance(x, list) and x and x[0] == "hide"))]
                else:
                    walk(c)
    walk(sym)
    return sym

# ------------------------------------------------------------------ layout (sheet mm, y down)
G = 2.54
snap = lambda v: round(v / G) * G
POS = {}
def at(ref, x, y):
    POS[ref] = (snap(x), snap(y))
# power and the hold switch
at("J3", 30, 40); at("F1", 60, 40); at("C1", 80, 45); at("D1", 105, 40); at("R8", 130, 40); at("LED1", 130, 62)
at("Q1", 175, 45); at("R5", 195, 32); at("D2", 215, 45); at("Q2", 175, 80); at("R6", 150, 85); at("R7", 195, 92)
# ESP32-C6 sockets, pull-ups, decoupling, expansion
at("J1", 40, 130); at("J2", 40, 185); at("J4", 40, 245)
for i, r in enumerate(["R1", "R2", "R3", "R9", "R4"]):
    at(r, 100 + 22 * i, 130)
for i, c in enumerate(["C5", "C6", "C7", "C8"]):
    at(c, 100 + 22 * i, 175)
# expanders
at("U3", 250, 140); at("U2", 350, 140); at("U8", 450, 140)
# drivers
at("U6", 250, 290); at("U5", 350, 290); at("U4", 450, 290)
at("U7", 250, 390); at("RN1", 330, 380); at("J5", 400, 390)
# edge connectors
for i in range(6):
    at(f"J{10 + i}", 520 + (i % 3) * 25, 250 + (i // 3) * 40)
for i in range(7):
    at(f"J{20 + i}", 100 + 25 * i, 300)
at("RN2", 140, 340)
for i in range(4):
    at(f"H{i + 1}", 500 + 15 * i, 40)

# ------------------------------------------------------------------ build
def prop(name, value, x, y, hide=False, angle=0):
    eff = ["effects", ["font", ["size", 1.27, 1.27]]]
    if hide:
        eff.append(["hide", "yes"])
    return ["property", Q(name), Q(value), ["at", round(x, 3), round(y, 3), angle], eff]

def label(net, x, y, angle):
    just = {0: ["justify", "left", "bottom"], 180: ["justify", "right", "bottom"],
            90: ["justify", "left", "bottom"], 270: ["justify", "right", "bottom"]}[angle]
    return ["label", Q(net), ["at", round(x, 3), round(y, 3), angle], ["fields_autoplaced", "yes"],
            ["effects", ["font", ["size", 1.27, 1.27]], just], ["uuid", U()]]

def main():
    root = str(uuid.uuid4())
    libs, items = {}, []
    for ref, p in design.P.items():
        lib_id = symbol_for(ref, p)
        if lib_id not in libs:
            libs[lib_id] = unhide_pins(lib_symbol(lib_id))
        sym = libs[lib_id]
        X, Y = POS[ref]
        pins = pins_of(sym)
        ys = [-py for _, _, py, _ in pins] or [0]
        xs = [px for _, px, _, _ in pins] or [0]
        top, bot = Y + min(ys) - 3.0, Y + max(ys) + 3.0
        value = p["value"] if not p["value"].startswith(("ESP32", "MOTOR", "HALL", "CALENDAR", "EXP", "5V IN")) else p["value"]
        s = ["symbol", ["lib_id", Q(lib_id)], ["at", X, Y, 0], ["unit", 1], ["exclude_from_sim", "no"],
             ["in_bom", "yes"], ["on_board", "yes"], ["dnp", "no"], ["uuid", U()],
             prop("Reference", ref, X, top), prop("Value", value, X, bot),
             prop("Footprint", p["fp"], X, bot + 2.5, hide=True), prop("Datasheet", "~", X, bot + 5, hide=True),
             prop("Description", p.get("mpn", ""), X, bot + 7.5, hide=True)]
        for num, px, py, a in pins:
            s.append(["pin", Q(num), ["uuid", U()]])
        s.append(["instances", ["project", Q("tide_main"), ["path", Q("/" + root), ["reference", Q(ref)], ["unit", 1]]]])
        items.append(s)
        for num, px, py, a in pins:
            x, y = X + px, Y - py
            net = p["pads"].get(num)
            if net:
                la = {0: 180, 180: 0, 90: 270, 270: 90}[int(round(a)) % 360]
                items.append(label(net, x, y, la))
            else:
                items.append(["no_connect", ["at", round(x, 3), round(y, 3)], ["uuid", U()]])
    # power flags: tell ERC the supplies are driven (the board's supply comes in through J3 and the C6's regulator)
    flag = unhide_pins(lib_symbol("power:PWR_FLAG"))
    libs["power:PWR_FLAG"] = flag
    for k, net in enumerate(["+5V", "+3V3", "GND", "HOLD", "VIN", "ESP_5V"]):
        X, Y = snap(330 + 18 * k), snap(40)
        items.append(["symbol", ["lib_id", Q("power:PWR_FLAG")], ["at", X, Y, 0], ["unit", 1], ["exclude_from_sim", "no"],
                      ["in_bom", "no"], ["on_board", "no"], ["dnp", "no"], ["uuid", U()],
                      prop("Reference", f"#FLG0{k + 1}", X, Y - 6, hide=True), prop("Value", "PWR_FLAG", X, Y - 4),
                      prop("Footprint", "", X, Y, hide=True), prop("Datasheet", "~", X, Y, hide=True),
                      ["pin", Q("1"), ["uuid", U()]],
                      ["instances", ["project", Q("tide_main"), ["path", Q("/" + root), ["reference", Q(f"#FLG0{k + 1}")], ["unit", 1]]]]])
        items.append(label(net, X, Y, 270))
    sch = ["kicad_sch", ["version", 20231120], ["generator", Q("tide_gen_schematic")], ["generator_version", Q("1.0")],
           ["uuid", Q(root)], ["paper", Q("A2")],
           ["title_block", ["title", Q("Tide Machine main board")], ["rev", Q("B")], ["company", Q("generated from pcb/design.py")]],
           ["lib_symbols"] + list(libs.values())] + items + [["sheet_instances", ["path", Q("/"), ["page", Q("1")]]]]
    open(OUT, "w", encoding="utf8").write(dump(sch) + "\n")
    print(f"wrote {OUT}: {len(design.P)} symbols, {len(libs)} library symbols")

if __name__ == "__main__":
    main()

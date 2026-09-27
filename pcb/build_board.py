"""Build the KiCad board from design.py, and apply routes to it. Run with KiCad's Python:

    "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" build_board.py            # place + nets + zones -> tide_main.kicad_pcb, pads.json
    "C:\\Program Files\\KiCad\\10.0\\bin\\python.exe" build_board.py --apply    # add routes.json's tracks/vias, fill zones, save

Board coordinates in design.py are board-relative; the board sits at (OX, OY) on the KiCad page.
"""
import sys, os, json
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import design, silk_labels

FPLIB = r"C:\Program Files\KiCad\10.0\share\kicad\footprints"
BOARD = os.path.join(HERE, "tide_main.kicad_pcb")
OX, OY = 40.0, 40.0
GRID = 0.254
MM = pcbnew.FromMM
KI_SAFE = {"◄": "<", "⊕": "(+)"}          # glyphs the stroke font may lack
_sp = os.path.join(HERE, "solid_pads.json")
SOLID = {tuple(x) for x in json.load(open(_sp))} if os.path.exists(_sp) else set()

def V(x, y):
    return pcbnew.VECTOR2I(MM(x + OX), MM(y + OY))

def deg(a):
    return pcbnew.EDA_ANGLE(a, pcbnew.DEGREES_T)

def snap(v):
    return round(v / GRID) * GRID

def anchor(p):
    grid = "PinSocket" in p["fp"] or "PinHeader" in p["fp"]      # same rule as layout.py
    return (snap(p["x"]), snap(p["y"])) if grid else (p["x"], p["y"])

def rules(board):
    ds = board.GetDesignSettings()
    ds.m_MinClearance = MM(0.2)
    ds.m_TrackMinWidth = MM(0.2)
    ds.m_CopperEdgeClearance = MM(0.3)
    ds.m_HoleClearance = MM(0.25)
    ds.m_ViasMinSize = MM(0.5)
    ds.m_ViasMinAnnularWidth = MM(0.13)
    ns = ds.m_NetSettings
    d = ns.GetDefaultNetclass()
    d.SetTrackWidth(MM(design.DEFAULT[0])); d.SetClearance(MM(design.DEFAULT[1]))
    d.SetViaDiameter(MM(0.6)); d.SetViaDrill(MM(0.3))
    for name, (w, c, members) in design.NETCLASS.items():
        nc = pcbnew.NETCLASS(name)
        nc.SetTrackWidth(MM(w)); nc.SetClearance(MM(c))
        nc.SetViaDiameter(MM(0.8 if name == "Power" else 0.6)); nc.SetViaDrill(MM(0.4 if name == "Power" else 0.3))
        ns.SetNetclass(name, nc)
        for m in members:
            ns.SetNetclassPatternAssignment(m, name)
    ns.RecomputeEffectiveNetclasses()

def text(board, L):
    s = L["text"]
    for a, b in KI_SAFE.items():
        s = s.replace(a, b)
    t = pcbnew.PCB_TEXT(board)
    t.SetText(s)
    t.SetLayer(pcbnew.F_SilkS)
    h = L["h"]
    t.SetTextSize(pcbnew.VECTOR2I(MM(h), MM(h)))
    t.SetTextThickness(MM(max(0.12, h * (0.2 if L["bold"] else 0.14))))
    t.SetTextAngle(deg(L["rot"]))
    t.SetHorizJustify({"center": pcbnew.GR_TEXT_H_ALIGN_CENTER, "left": pcbnew.GR_TEXT_H_ALIGN_LEFT,
                       "right": pcbnew.GR_TEXT_H_ALIGN_RIGHT}[L["ha"]])
    t.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER)
    t.SetPosition(V(L["x"], L["y"]))
    board.Add(t)

def line(board, layer, a, b, w, dashed=False):
    if dashed:                                  # KiCad 10's Python doesn't expose stroke styles: draw the dashes
        import math
        L = math.hypot(b[0] - a[0], b[1] - a[1]); dash, gap = 1.5, 1.0
        t = 0.0
        while t < L:
            t1 = min(t + dash, L)
            p = (a[0] + (b[0] - a[0]) * t / L, a[1] + (b[1] - a[1]) * t / L)
            q = (a[0] + (b[0] - a[0]) * t1 / L, a[1] + (b[1] - a[1]) * t1 / L)
            line(board, layer, p, q, w)
            t += dash + gap
        return
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(V(*a)); s.SetEnd(V(*b))
    s.SetLayer(layer); s.SetWidth(MM(w))
    board.Add(s)

def circle(board, layer, c, r, w):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_CIRCLE)
    s.SetCenter(V(*c)); s.SetEnd(V(c[0] + r, c[1]))
    s.SetLayer(layer); s.SetWidth(MM(w))
    board.Add(s)

def zone(board, net, layer, pts, rule_area=False):
    z = pcbnew.ZONE(board)
    z.SetLayer(layer)
    ol = z.Outline()
    ol.NewOutline()
    for x, y in pts:
        ol.Append(MM(x + OX), MM(y + OY))
    if rule_area:
        z.SetIsRuleArea(True)
        z.SetDoNotAllowZoneFills(True); z.SetDoNotAllowTracks(True); z.SetDoNotAllowVias(True)
        z.SetDoNotAllowPads(False); z.SetDoNotAllowFootprints(False)

    else:
        z.SetNet(net)
        z.SetLocalClearance(MM(0.3))
        z.SetMinThickness(MM(0.25))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        z.SetThermalReliefGap(MM(0.3))
        z.SetThermalReliefSpokeWidth(MM(0.5))
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    board.Add(z)
    return z

def build(zones=True, path=BOARD):
    board = pcbnew.NewBoard(path)
    rules(board)
    open(BOARD.replace(".kicad_pcb", ".kicad_dru"), "w").write(DRU)
    nets = {}
    for n in sorted({n for p in design.P.values() for n in p["pads"].values()}):
        ni = pcbnew.NETINFO_ITEM(board, n)
        board.Add(ni)
        nets[n] = ni
    for ref, p in design.P.items():
        lib, name = p["fp"].split(":")
        fp = pcbnew.FootprintLoad(os.path.join(FPLIB, lib + ".pretty"), name)
        if fp is None:
            raise SystemExit(f"footprint not found: {p['fp']}")
        fp.SetReference(ref)
        fp.SetValue(p["value"])
        fp.Reference().SetVisible(False)          # silk_labels prints its own, placed by hand
        x, y = anchor(p)
        fp.SetPosition(V(x, y))
        fp.SetOrientation(deg(p["rot"]))
        for pad in fp.Pads():
            n = p["pads"].get(pad.GetNumber())
            if n:
                pad.SetNet(nets[n])
            if (ref, pad.GetNumber()) in SOLID:          # tracks block their thermal spokes: connect solid
                pad.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
        board.Add(fp)
    W, H = design.BOARD_W, design.BOARD_H
    for a, b in (((0, 0), (W, 0)), ((W, 0), (W, H)), ((W, H), (0, H)), ((0, H), (0, 0))):
        line(board, pcbnew.Edge_Cuts, a, b, 0.1)
    for L in silk_labels.labels():
        text(board, L)
    for sh in silk_labels.shapes():
        if sh[0] == "rect_dashed":
            _, x0, y0, x1, y1 = sh
            for a, b in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
                line(board, pcbnew.F_SilkS, a, b, 0.15, dashed=True)
        else:
            _, x, y, r = sh
            circle(board, pcbnew.F_SilkS, (x, y), r, 0.15)
    edge = 0.5
    outline = [(edge, edge), (W - edge, edge), (W - edge, H - edge), (edge, H - edge)]
    if zones:
        for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
            zone(board, nets["GND"], layer, outline)
    # no copper under the DevKit's antenna end
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        z = zone(board, None, layer, design.ANTENNA_KEEPOUT, rule_area=True)
        z.SetLayer(layer)
    import math
    for hx, hy in design.HOLES:                  # standoff washer area: no copper, clear of the hole
        ring = [(hx + 3.3 * math.cos(2 * math.pi * k / 24), hy + 3.3 * math.sin(2 * math.pi * k / 24)) for k in range(24)]
        for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
            zone(board, None, layer, ring, rule_area=True)
    pcbnew.SaveBoard(path, board)
    if path == BOARD:
        export_pads(board)
    return board

def export_pads(board):
    out = []
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            rec = dict(ref=fp.GetReference(), num=pad.GetNumber(), net=pad.GetNetname(),
                       c=[pcbnew.ToMM(pad.GetPosition().x) - OX, pcbnew.ToMM(pad.GetPosition().y) - OY],
                       layers={}, drill=None)
            if pad.GetDrillSize().x > 0:
                rec["drill"] = pcbnew.ToMM(max(pad.GetDrillSize().x, pad.GetDrillSize().y))
            for lid, lname in ((pcbnew.F_Cu, "F.Cu"), (pcbnew.B_Cu, "B.Cu")):
                if not pad.IsOnLayer(lid):
                    continue
                ps = pcbnew.SHAPE_POLY_SET()
                pad.TransformShapeToPolygon(ps, lid, 0, MM(0.005), pcbnew.ERROR_OUTSIDE)
                if ps.OutlineCount() == 0:
                    continue
                o = ps.Outline(0)
                rec["layers"][lname] = [[pcbnew.ToMM(o.CPoint(i).x) - OX, pcbnew.ToMM(o.CPoint(i).y) - OY] for i in range(o.PointCount())]
            out.append(rec)
    json.dump(dict(W=design.BOARD_W, H=design.BOARD_H, holes=design.HOLES, devkit=design.DEVKIT,
                   antenna=design.ANTENNA_KEEPOUT, pads=out),
              open(os.path.join(HERE, "pads.json"), "w"), indent=0)
    print(f"{len(out)} pads -> pads.json")

def export_zones(board):
    """filled GND copper per layer, for route.py --gnd"""
    out = {"F.Cu": [], "B.Cu": []}
    for z in board.Zones():
        if z.GetIsRuleArea() or z.GetNetname() != "GND":
            continue
        for lid, lname in ((pcbnew.F_Cu, "F.Cu"), (pcbnew.B_Cu, "B.Cu")):
            if not z.IsOnLayer(lid):
                continue
            ps = z.GetFilledPolysList(lid)
            for k in range(ps.OutlineCount()):
                o = ps.Outline(k)
                out[lname].append([[pcbnew.ToMM(o.CPoint(i).x) - OX, pcbnew.ToMM(o.CPoint(i).y) - OY] for i in range(o.PointCount())])
    json.dump(out, open(os.path.join(HERE, "zones.json"), "w"))

DRU = """(version 1)
"""

def apply():
    board = build()                              # always from scratch: no stale tracks
    r = json.load(open(os.path.join(HERE, "routes.json")))
    def net(name):
        return board.FindNet(name)
    for t in r["tracks"]:
        tr = pcbnew.PCB_TRACK(board)
        tr.SetStart(V(*t["a"])); tr.SetEnd(V(*t["b"]))
        tr.SetWidth(MM(t["w"]))
        tr.SetLayer(pcbnew.F_Cu if t["layer"] == "F.Cu" else pcbnew.B_Cu)
        tr.SetNet(net(t["net"]))
        board.Add(tr)
    for v in r["vias"]:
        via = pcbnew.PCB_VIA(board)
        via.SetPosition(V(*v["c"]))
        via.SetWidth(MM(v["d"]))
        via.SetDrill(MM(v["drill"]))
        via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        via.SetNet(net(v["net"]))
        board.Add(via)
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())
    pcbnew.SaveBoard(BOARD, board)
    export_zones(board)
    print(f"applied {len(r['tracks'])} tracks, {len(r['vias'])} vias; zones filled")

ROUTE_IN = os.path.join(HERE, "route_in.kicad_pcb")
DSN, SES = os.path.join(HERE, "tide_main.dsn"), os.path.join(HERE, "tide_main.ses")

def dsn():
    """Specctra design for Freerouting: the board without its pours, and without the GND net (the pours carry it)"""
    board = build(zones=False, path=ROUTE_IN)
    if not pcbnew.ExportSpecctraDSN(board, DSN):
        raise SystemExit("DSN export failed")
    s = open(DSN, encoding="utf8").read()
    for key in ("(net GND", '(net "GND"'):
        i = s.find(key)
        if i >= 0:
            depth, j = 0, i
            while True:
                if s[j] == "(":
                    depth += 1
                elif s[j] == ")":
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            s = s[:i] + s[j + 1:]
    import re
    s = re.sub(r"(\(class\s+\S+[^()]*?)\sGND(?=[\s)])", r"", s)
    open(DSN, "w", encoding="utf8").write(s)
    print("wrote", DSN)

def ses():
    """read Freerouting's session back and store its tracks and vias as routes.json"""
    board = build(zones=False, path=ROUTE_IN)
    if not pcbnew.ImportSpecctraSES(board, SES):
        raise SystemExit("SES import failed")
    tracks, vias = [], []
    mm = lambda v: round(pcbnew.ToMM(v), 4)
    for t in board.GetTracks():
        if t.GetClass() == "PCB_VIA":
            vias.append(dict(net=t.GetNetname(), c=[mm(t.GetPosition().x) - OX, mm(t.GetPosition().y) - OY],
                             d=mm(t.GetWidth(pcbnew.F_Cu)), drill=mm(t.GetDrillValue())))
        else:
            tracks.append(dict(net=t.GetNetname(), a=[mm(t.GetStart().x) - OX, mm(t.GetStart().y) - OY],
                               b=[mm(t.GetEnd().x) - OX, mm(t.GetEnd().y) - OY], w=mm(t.GetWidth()),
                               layer="F.Cu" if t.GetLayer() == pcbnew.F_Cu else "B.Cu"))
    json.dump(dict(tracks=tracks, vias=vias, failed=[]), open(os.path.join(HERE, "routes.json"), "w"), indent=0)
    print(f"SES: {len(tracks)} tracks, {len(vias)} vias -> routes.json")

if __name__ == "__main__":
    if "--dsn" in sys.argv:
        dsn()
    elif "--ses" in sys.argv:
        ses()
    elif "--apply" in sys.argv:
        apply()
    else:
        build()
        print("wrote", BOARD)

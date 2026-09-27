"""Build, route, check and fix the main board until KiCad's DRC is clean, then plot fab files.

    python make_board.py                # full run: routes from scratch with Freerouting (if installed)
    python make_board.py --own-router   # route with route.py instead
    python make_board.py --keep         # reuse routes.json, just rebuild/fix/check/plot
"""
import subprocess, json, sys, os, shutil, zipfile, glob
HERE = os.path.dirname(os.path.abspath(__file__))
KI = r"C:\Program Files\KiCad\10.0\bin"
PY, CLI = os.path.join(KI, "python.exe"), os.path.join(KI, "kicad-cli.exe")
BOARD = os.path.join(HERE, "tide_main.kicad_pcb")
FR_DIR = os.path.join(os.path.expanduser("~"), "Tools", "freerouting")   # Freerouting jar + a portable Java 25

def run(args, quiet=True):
    p = subprocess.run(args, cwd=HERE, capture_output=True, text=True)
    out = "\n".join(l for l in (p.stdout + p.stderr).splitlines() if "memory leak" not in l)
    if p.returncode:
        raise SystemExit(f"FAILED: {' '.join(args)}\n{out}")
    if not quiet:
        print(out.strip().splitlines()[-1] if out.strip() else "")
    return out

def drc(name="drc.json"):
    run([CLI, "pcb", "drc", "--format", "json", "--severity-all", "--units", "mm", "-o", name, BOARD])
    return json.load(open(os.path.join(HERE, name)))

def main():
    if "--keep" not in sys.argv:
        run([PY, "build_board.py"], quiet=False)
        java = sorted(glob.glob(os.path.join(FR_DIR, "jdk-*", "bin", "java.exe")))
        jar = sorted(glob.glob(os.path.join(FR_DIR, "freerouting-*.jar")))
        if java and jar and "--own-router" not in sys.argv:
            run([PY, "build_board.py", "--dsn"], quiet=False)
            if os.path.exists(os.path.join(HERE, "tide_main.ses")):
                os.remove(os.path.join(HERE, "tide_main.ses"))
            out = run([java[-1], "-jar", jar[-1], "-de", "tide_main.dsn", "-do", "tide_main.ses", "-mp", "100",
                       "--gui.enabled=false"])
            summary = [l for l in out.splitlines() if "Auto-routing stage completed" in l]
            print("Freerouting:", summary[-1].split("final score:")[-1].strip() if summary else "no summary")
            run([PY, "build_board.py", "--ses"], quiet=False)
        else:
            run([sys.executable, "route.py"], quiet=False)
    run([PY, "build_board.py", "--apply"], quiet=False)     # fill the pours once, then stitch them together
    run([sys.executable, "route.py", "--gnd", "drc_none.json", "--stitch"], quiet=False)
    solid = set(tuple(x) for x in json.load(open(os.path.join(HERE, "solid_pads.json")))) if os.path.exists(os.path.join(HERE, "solid_pads.json")) else {("J1", "1")}
    for it in range(8):
        json.dump(sorted(solid), open(os.path.join(HERE, "solid_pads.json"), "w"))
        run([PY, "build_board.py", "--apply"], quiet=False)
        d = drc()
        errs = [v for v in d["violations"] if v["severity"] == "error"]
        unc = d.get("unconnected_items", [])
        print(f"  check {it + 1}: {len(errs)} errors, {len(unc)} unconnected, {len(d['violations']) - len(errs)} warnings")
        starved = [v for v in errs if v["type"] == "starved_thermal"]
        for v in starved:
            for i in v["items"]:
                if i["description"].startswith("PTH pad"):
                    w = i["description"].split()
                    solid.add((w[-1], w[2]))
        gnd_unc = [u for u in unc if any("[GND]" in i["description"] for i in u["items"])]
        if gnd_unc:
            run([sys.executable, "route.py", "--gnd", "drc.json"], quiet=False)
        if not errs and not unc:
            break
        if not starved and not gnd_unc:
            break
    others = [v for v in errs if v["type"] != "starved_thermal"]
    for v in others:
        print("  ERROR", v["type"], v["description"][:90], [i["description"][:50] for i in v["items"]])
    for u in unc:
        print("  UNCONNECTED", [i["description"][:60] for i in u["items"]])
    return not errs and not unc

def plot():
    g = os.path.join(HERE, "gerbers")
    shutil.rmtree(g, ignore_errors=True); os.makedirs(g)
    run([CLI, "pcb", "export", "gerbers", "-o", g + os.sep, "--subtract-soldermask",
         "-l", "F.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,F.Paste,B.Paste,Edge.Cuts", BOARD])
    run([CLI, "pcb", "export", "drill", "-o", g + os.sep, "--format", "excellon", "--excellon-separate-th",
         "--generate-map", "--map-format", "pdf", BOARD])
    z = os.path.join(HERE, "tide_main_gerbers.zip")
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as f:
        for n in sorted(os.listdir(g)):
            if not n.endswith(".pdf"):
                f.write(os.path.join(g, n), n)
    for side in ("top", "bottom"):
        run([CLI, "pcb", "render", "-o", os.path.join(HERE, f"render_{side}.png"), "--side", side,
             "--width", "2400", "--height", "1600", "--quality", "high", "--background", "opaque", BOARD])
    print("gerbers:", sorted(os.listdir(g)))
    print("wrote", z, "and render_top.png / render_bottom.png")

if __name__ == "__main__":
    ok = main()
    print("DRC CLEAN" if ok else "DRC NOT CLEAN")
    if ok or "--plot" in sys.argv:
        plot()

#!/usr/bin/env python3
"""
build.py -- assemble a flat-pack assembly guide into one self-contained HTML
file, and print it to PDF.

    python build.py                # everything
    python build.py --no-fritzing  # reuse the last Fritzing export in _build/
    python build.py --no-pdf

Reads guide.json next to it (paths relative to that file; every key but
"page", "out" and "scripts" is optional):

{
  "page": "guide.html",                    // the hand-written page
  "pre": ["gen_geom.py"],                  // scripts to run first (python), e.g. data the figures read
  "out": "myproject_guide.html",           // the built file (PDF lands beside it)
  "scripts": ["engine.js", "figs_common.js", "figs_pcb.js", "figs_project.js"],
  "kicad_pcb": "../../hardware/x/x.kicad_pcb",   // -> window.BOARD (isometric board)
  "kicad_sch": "../../hardware/x/x.kicad_sch",   // -> <!--FZ:kicad|alt-->
  "fritzing": {
    "generator": "../../hardware/fritzing/gen_fritzing.py",   // writes the .fzz
    "fzz": "../../hardware/fritzing/wiring.fzz",
    "board_first": true,             // the board is the sketch's first instance
    "crops": {"power": [-212, -26, 245, 118]}   // close-ups, board mm: x y w h
  }
}

In the page, these comments are replaced with inline SVG:
  <!--ASSETS-->                  hidden <symbol>s + window.BOARD / BOARD_INFO (put right after <body>'s sprite)
  <!--FZ:bb|alt text-->          Fritzing breadboard view, whole
  <!--FZ:<crop>|alt text-->      a close-up from "crops"
  <!--FZ:sch|alt text-->         Fritzing schematic view
  <!--FZ:kicad|alt text-->       the KiCad schematic, fitted to its drawing (put it in a .zoomer)
"""
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(sys.argv[0] if __name__ == '__main__' else __file__))
CFG_DIR = os.getcwd() if os.path.exists(os.path.join(os.getcwd(), 'guide.json')) else HERE
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

FRITZING = r'C:\Program Files\Fritzing\Fritzing.exe'
KICAD_CLI = r'C:\Program Files\KiCad\10.0\bin\kicad-cli.exe'
BROWSERS = [r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
            r'C:\Program Files\Google\Chrome\Application\chrome.exe']
MIL_PER_MM = 1000 / 25.4       # Fritzing exports in thousandths of an inch


def P(rel):
    return os.path.normpath(os.path.join(CFG_DIR, rel))


def read(p):
    with open(p, encoding='utf8') as fh:
        return fh.read()


def run(cmd, **kw):
    print('>', ' '.join('"%s"' % c if ' ' in c else c for c in cmd))
    subprocess.run(cmd, check=True, **kw)


def svg_parts(text):
    """(viewBox, inner markup) of an exported SVG, ids and comments stripped
    (Fritzing and KiCad exports use no url(#id) references, so this is safe)."""
    m = re.search(r'<svg\b[^>]*>', text)
    vb = re.search(r'viewBox="([^"]+)"', m.group(0)).group(1)
    inner = text[m.end():text.rindex('</svg>')]
    inner = re.sub(r'<\?xml[^>]*\?>|<!--.*?-->|<desc>.*?</desc>|<title>.*?</title>', '', inner, flags=re.S)
    return vb, re.sub(r'\sid="[^"]*"', '', inner)


def kicad_clean(text):
    """KiCad draws each character as strokes over a hidden <text>. Drop the
    strokes, show the text in its group's colour: ~1/4 the size, searchable."""
    text = re.sub(r'<g class="stroked-text">.*?</g>', '', text, flags=re.S)
    out, colour, pos = [], '#000000', 0
    for m in re.finditer(r'stroke:(#[0-9A-Fa-f]{6})|<text\b([^>]*)>', text):
        out.append(text[pos:m.start()])
        if m.group(1):
            colour = m.group(1); out.append(m.group(0))
        else:
            attrs = m.group(2).replace('opacity="0"', '').replace('stroke-opacity="0"', '')
            out.append('<text%s fill="%s" stroke="none" font-family="Noto Sans, Arial, sans-serif">' % (attrs, colour))
        pos = m.end()
    out.append(text[pos:])
    return re.sub(r'\n', ' ', re.sub(r'(\d+\.\d{2})\d+', r'\1', ''.join(out)))


def main():
    # guide.json may carry // comments (whole-line or after whitespace, so a
    # URL's // survives) and a BOM (PowerShell's Set-Content writes one)
    raw = open(os.path.join(CFG_DIR, 'guide.json'), encoding='utf-8-sig').read()
    cfg = json.loads(re.sub(r'(^|\s)//[^\n]*', r'\1', raw, flags=re.M))
    build = os.path.join(CFG_DIR, '_build')
    os.makedirs(build, exist_ok=True)
    for pre in cfg.get('pre', []):
        run([sys.executable, P(pre)], cwd=CFG_DIR)
    fz = cfg.get('fritzing')
    symbols, extra = [], ''

    # ---- Fritzing: generate the sketch, export its views headless
    bb = sc = None
    if fz:
        fx = os.path.join(build, 'fritzing')
        if '--no-fritzing' not in sys.argv:
            if fz.get('generator'):
                run([sys.executable, P(fz['generator'])])
            shutil.rmtree(fx, ignore_errors=True); os.makedirs(fx)
            shutil.copy(P(fz['fzz']), fx)
            run([FRITZING, '-svg', fx], timeout=600)
        stem = os.path.splitext(os.path.basename(fz['fzz']))[0]
        bb = read(os.path.join(fx, stem + '_breadboard.svg'))
        sc = read(os.path.join(fx, stem + '_schematic.svg'))
        bb_vb, bb_in = svg_parts(bb); sc_vb, sc_in = svg_parts(sc)
        symbols += ['<symbol id="fz-bb" viewBox="%s">%s</symbol>' % (bb_vb, bb_in),
                    '<symbol id="fz-sch" viewBox="%s">%s</symbol>' % (sc_vb, sc_in)]
        # the board's (0,0) in the export: its group carries the first translate()
        t = re.search(r'translate\(([-\d.]+),\s*([-\d.]+)\)', bb)
        ox, oy = float(t.group(1)), float(t.group(2))

    # ---- KiCad schematic
    ki_vb = ki_in = None
    if cfg.get('kicad_sch'):
        run([KICAD_CLI, 'sch', 'export', 'svg', '--output', build, '--exclude-drawing-sheet',
             '--no-background-color', P(cfg['kicad_sch'])])
        name = os.path.splitext(os.path.basename(cfg['kicad_sch']))[0] + '.svg'
        ki_vb, ki_in = svg_parts(kicad_clean(read(os.path.join(build, name))))
        # label-connected schematics export as islands: draw each net's connections under the symbols
        import kicad_nets
        ki_in = kicad_nets.overlay(P(cfg['kicad_sch'])) + ki_in
        symbols.append('<symbol id="ki-sch" viewBox="%s">%s</symbol>' % (ki_vb, ki_in))

    # ---- KiCad board -> window.BOARD for the isometric drawings
    if cfg.get('kicad_pcb'):
        import kicad_board
        extra = '\n<script>window.BOARD=%s;window.BOARD_INFO=%s;</script>' % (
            kicad_board.board_json(P(cfg['kicad_pcb'])), kicad_board.board_info_json(P(cfg['kicad_pcb'])))

    html = '<meta charset="utf-8">\n' + read(P(cfg['page']))
    for f in cfg['scripts']:
        src = P(f) if os.path.exists(P(f)) else os.path.join(os.path.dirname(HERE), 'assets', f)
        html = html.replace('<script src="%s"></script>' % f, '<script>\n%s\n</script>' % read(src))
    html = html.replace('<!--ASSETS-->', '<svg width="0" height="0" style="position:absolute" aria-hidden="true">%s</svg>%s'
                        % (''.join(symbols), extra))

    def use(sym, vb_full, vb, cls, alt):
        W, H = vb_full.split()[2:]
        return ('<svg class="%s" viewBox="%s" role="img" aria-label="%s"><use href="#%s" x="0" y="0" width="%s" height="%s"/></svg>'
                % (cls, vb, alt, sym, W, H))

    def fill(m):
        kind, alt = m.group(1), m.group(2)
        if (kind == 'kicad' and not ki_in) or (kind != 'kicad' and not fz):
            src = 'kicad_sch' if kind == 'kicad' else 'fritzing'
            return '<p class="fzcap">[%s: add "%s" to guide.json to fill this in]</p>' % (alt, src)
        if kind == 'bb':
            return use('fz-bb', bb_vb, bb_vb, 'fzimg', alt)
        if kind == 'sch':
            return use('fz-sch', sc_vb, sc_vb, 'fzimg sch', alt)
        if kind == 'kicad':
            xs, ys = [], []
            for mm in re.finditer(r'[ML]\s*([-\d.]+)[ ,]([-\d.]+)', ki_in):
                xs.append(float(mm.group(1))); ys.append(float(mm.group(2)))
            fit = '%.1f %.1f %.1f %.1f' % (min(xs) - 8, min(ys) - 8, max(xs) - min(xs) + 16, max(ys) - min(ys) + 16)
            return use('ki-sch', ki_vb, fit, 'kiimg', alt)
        x, y, w, h = fz['crops'][kind]
        crop = '%.1f %.1f %.1f %.1f' % (ox + x * MIL_PER_MM, oy + y * MIL_PER_MM, w * MIL_PER_MM, h * MIL_PER_MM)
        return use('fz-bb', bb_vb, crop, 'fzimg crop', alt)
    html, n = re.subn(r'<!--FZ:(\w+)\|([^>]*?)-->', fill, html)

    out = P(cfg['out'])
    with open(out, 'w', encoding='utf8', newline='\n') as fh:
        fh.write(html)
    print('wrote %s  (%d KB, %d exported figures)' % (out, os.path.getsize(out) // 1024, n))
    if '--no-pdf' not in sys.argv:
        pdf(out, build)


def pdf(out_html, build):
    """Headless Edge/Chrome print. The page's @media print rules make one sheet
    per Letter page; the virtual time budget lets fonts and figures finish.
    A throwaway profile keeps it away from any browser you have open."""
    exe = next((e for e in BROWSERS if os.path.exists(e)), None)
    if not exe:
        print('no Edge or Chrome found; skipping the PDF'); return
    out = os.path.splitext(out_html)[0] + '.pdf'
    run([exe, '--headless=new', '--disable-gpu', '--no-pdf-header-footer', '--user-data-dir=' + os.path.join(build, 'pdf-profile'),
         '--virtual-time-budget=20000', '--print-to-pdf=' + out, 'file:///' + out_html.replace('\\', '/')], timeout=300)
    print('wrote %s  (%d KB)' % (out, os.path.getsize(out) // 1024))


if __name__ == '__main__':
    main()

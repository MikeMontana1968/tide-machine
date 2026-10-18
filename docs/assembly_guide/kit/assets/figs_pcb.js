/* figs_pcb.js -- a PCB in isometric, placed from its KiCad layout (window.BOARD,
   injected by build.py; configure with window.GUIDE_BOARD), and the electronics
   inventory cards: part, schematic symbol, silkscreen letter.
   Board mm -> world: world x = board y, world y = board x, so the board's top
   edge (J1, J2) is at the back and its right edge (J4) runs off to the right.
   GUIDE_BOARD.region = [x0, y0, x1, y1] (the Edge.Cuts rectangle, board mm) for a
   board not drawn at the origin; .empty = refs of IC sockets to show without chips;
   modules: kind 'esp32' | 'stepstick' | 'lcd' (display on top, usb 'L'|'R'),
   outline = [x0, y0, x1, y1] to override the socket-pad box. */
(function () {
  'use strict';
  var FIG = window.FIG = window.FIG || {};
  var flat = function (s, w, h, svg) { s.raw(svg, [0, 0, w, h]); return { scale: 1, pad: 0 }; };
  function T(x, y, t, o) {
    o = o || {};
    return '<text class="' + (o.cls || 'tx') + '" x="' + x + '" y="' + y + '" font-size="' + (o.size || 12) + '" text-anchor="' + (o.a || 'middle') + '">' +
      String(t).replace(/&/g, '&amp;').replace(/</g, '&lt;') + '</text>';
  }

  /* ---------------- the isometric board ---------------- */
  function fpByRef(ref) { return (window.BOARD || []).find(function (f) { return f.r === ref; }); }
  function bbox(pads, e) {
    e = e || 0;
    var xs = pads.map(function (p) { return p[0]; }), ys = pads.map(function (p) { return p[1]; });
    return [Math.min.apply(null, xs) - e, Math.min.apply(null, ys) - e, Math.max.apply(null, xs) + e, Math.max.apply(null, ys) + e];
  }
  function mid(pads) { var b = bbox(pads); return [(b[0] + b[2]) / 2, (b[1] + b[3]) / 2]; }
  function padN(fp, n) { return fp.p.find(function (p) { return p[2] === n; }) || fp.p[0]; }

  // draw list: each item {k: depth key, fn}
  function B(s, b, z, h, cls) { s.box(b[1], b[0], z, b[3] - b[1], b[2] - b[0], h, { cls: cls || 'f' }); }
  function Cy(s, kx, ky, z, r, h, o) { s.cyl(ky, kx, z, r, h, o); }

  function partItems(fp) {
    var f = fp.f, p = fp.p, it = [], c = p.length ? mid(p) : [0, 0];
    function add(fn, ht) { it.push({ k: c[0] + c[1] + (ht || 0) * 0.001, fn: fn }); }
    if (/^MountingHole/.test(f)) return it;
    if (/CP_Radial_D10/.test(f)) add(function (s) { Cy(s, c[0], c[1], 0, 5, 16, { rings: [4.2] }); }, 16);
    else if (/CP_Radial_D8/.test(f)) add(function (s) { Cy(s, c[0], c[1], 0, 4, 11.5, { rings: [3.3] }); }, 11.5);
    else if (/C_Disc/.test(f)) add(function (s) { B(s, [c[0] - 2.5, c[1] - 1.1, c[0] + 2.5, c[1] + 1.1], 0, 5); }, 5);
    else if (/R_Axial/.test(f)) {
      var a = padN(fp, '1'), b2 = padN(fp, '2');
      add(function (s) { Cy(s, a[0], a[1], 0, 1.25, 6.3); s.polyline([[a[1], a[0], 6.3], [a[1], a[0], 7.6], [b2[1], b2[0], 7.6], [b2[1], b2[0], 0]], 'l'); }, 7);
    } else if (/(D_DO|R_Axial).*Horizontal/.test(f)) {     // lying flat between its pads, band at pad 1 (K)
      var h1 = padN(fp, '1'), h2 = padN(fp, '2'), hz = Math.abs(h1[0] - h2[0]) > Math.abs(h1[1] - h2[1]), isD = /D_DO/.test(f);
      var dr = /DO-201/.test(f) ? 2.7 : /DO-15/.test(f) ? 1.8 : 1.35, dl = /DO-201/.test(f) ? 9.5 : /DO-15/.test(f) ? 7.6 : isD ? 5.2 : 6.3;
      add(function (s) {
        var a0 = hz ? Math.min(h1[0], h2[0]) : Math.min(h1[1], h2[1]), a1 = hz ? Math.max(h1[0], h2[0]) : Math.max(h1[1], h2[1]);
        var m0 = (a0 + a1) / 2 - dl / 2, m1 = (a0 + a1) / 2 + dl / 2, zc = dr + 0.4;
        [h1, h2].forEach(function (q) {
          var e = hz ? (q[0] < (a0 + a1) / 2 ? m0 : m1) : (q[1] < (a0 + a1) / 2 ? m0 : m1);
          s.polyline([[q[1], q[0], 0], [q[1], q[0], zc], hz ? [q[1], e, zc] : [e, q[0], zc]], 'l');
        });
        B(s, hz ? [m0, c[1] - dr, m1, c[1] + dr] : [c[0] - dr, m0, c[0] + dr, m1], zc - dr, 2 * dr, isD ? 'kd2' : 'f');
        if (isD) {                                                                  // cathode band
          var k = hz ? (h1[0] < h2[0] ? m0 + 0.6 : m1 - 1.6) : (h1[1] < h2[1] ? m0 + 0.6 : m1 - 1.6);
          B(s, hz ? [k, c[1] - dr, k + 1.0, c[1] + dr] : [c[0] - dr, k, c[0] + dr, k + 1.0], zc - dr, 2 * dr + 0.02, 'f');
        }
      }, 2 * dr + 0.4);
    } else if (/D_DO/.test(f)) {
      var body = /CathodeUp/.test(f) ? padN(fp, '2') : padN(fp, '1'), oth = /CathodeUp/.test(f) ? padN(fp, '1') : padN(fp, '2');
      var r = /DO-201/.test(f) ? 2.7 : /DO-15/.test(f) ? 1.8 : 1.35, h = /DO-201/.test(f) ? 9.5 : /DO-15/.test(f) ? 7.6 : 5.2;
      add(function (s) { Cy(s, body[0], body[1], 0, r, h, { cls: 'kd2' }); s.polyline([[body[1], body[0], h], [body[1], body[0], h + 1.3], [oth[1], oth[0], h + 1.3], [oth[1], oth[0], 0]], 'l'); }, h);
    } else if (/LED_D3/.test(f)) add(function (s) { Cy(s, c[0], c[1], 0, 1.5, 4.2); Cy(s, c[0], c[1], 4.2, 1.1, 0.9); }, 5);
    else if (/TO-92/.test(f)) { var m = padN(fp, '2'); add(function (s) { Cy(s, m[0], m[1] + 0.8, 3, 2.4, 4.6); }, 7.6); }
    else if (/TO-220/.test(f)) {
      var bb = bbox(p), cx = (bb[0] + bb[2]) / 2, py = p[0][1], w = /TO-220-5/.test(f) ? 10.4 : 10.2;
      add(function (s) {
        B(s, [cx - w / 2, py - 3.4, cx + w / 2, py - 2.1], 3, 21, 'm');           // tab, behind
        B(s, [cx - w / 2, py - 2.1, cx + w / 2, py + 2.4], 3, 15);                 // body
        p.forEach(function (q) { s.line([q[1], q[0], 0], [q[1], q[0], 3], 'l'); });
        if (((window.GUIDE_BOARD || {}).heatsinks || []).indexOf(fp.r) >= 0) {   // clip-on heatsink
          B(s, [cx - 8, py - 9.5, cx + 8, py - 3.4], 5, 20, 'm');
          for (var i = -6; i <= 6; i += 3) s.line([py - 9.5, cx + i, 25], [py - 3.4, cx + i, 25], 't');
        }
      }, 24);
    } else if (/L_Radial_D12/.test(f)) add(function (s) { Cy(s, c[0], c[1], 0, 6, 10, { rings: [4.5, 2] }); }, 10);
    else if (/Fuseholder/.test(f)) {
      var p1 = p.filter(function (q) { return q[2] === '1'; }), p2 = p.filter(function (q) { return q[2] === '2'; });
      var m1 = mid(p1), m2 = mid(p2), vert = Math.abs(m1[1] - m2[1]) > Math.abs(m1[0] - m2[0]);
      add(function (s) {
        [m1, m2].forEach(function (m) { B(s, vert ? [m[0] - 3, m[1] - 1, m[0] + 3, m[1] + 1] : [m[0] - 1, m[1] - 3, m[0] + 1, m[1] + 3], 0, 8, 'm'); });
        B(s, vert ? [c[0] - 2.5, m1[1], c[0] + 2.5, m2[1]] : [m1[0], c[1] - 2.5, m2[0], c[1] + 2.5], 3.5, 5);
      }, 8.5);
    } else if (/TerminalBlock/.test(f)) {
      add(function (s) {
        var b3 = bbox(p); B(s, [b3[0] - 2.5, b3[1] - 4, b3[2] + 2.5, b3[3] + 4], 0, 10);
        p.forEach(function (q) { s.hole(q[1] - 1.2, q[0], 10, 1.4, 2); });
      }, 10);
    } else if (/PinSocket/.test(f)) {
      add(function (s) { B(s, bbox(p, 1.27), 0, 8.5); p.forEach(function (q) { s.ell(q[1], q[0], 8.5, 0.45, 'k'); }); }, 8.5);
    } else if (/PinHeader/.test(f)) {
      add(function (s) { B(s, bbox(p, 1.27), 0, 2.5); p.forEach(function (q) { Cy(s, q[0], q[1], 2.5, 0.35, 6, { cls: 'm' }); }); }, 8.5);
    } else if (/USB_A/.test(f)) {
      var bu = bbox(p.filter(function (q) { return q[2] !== 'SH'; }));
      add(function (s) { B(s, [bu[0] - 4, -1, bu[2] + 4, bu[3] + 4], 0, 7, 'm'); s.box(-1.2, bu[0] - 2, 1.5, 0.6, bu[2] - bu[0] + 4, 3, { cls: 'k' }); }, 7);
    } else if (/SW_PUSH/.test(f)) {
      add(function (s) { B(s, bbox(p, 0), 0, 3.5); Cy(s, c[0], c[1], 3.5, 1.75, 1.6); }, 5);
    } else if (/DIP-\d+/.test(f)) {                       // IC socket, chip fitted (GUIDE_BOARD.empty lists bare sockets)
      var bd = bbox(p), lx = bd[2] - bd[0] >= bd[3] - bd[1], p1 = padN(fp, '1');
      var e1 = lx ? (Math.abs(p1[0] - bd[0]) < 1 ? bd[0] : bd[2]) : (Math.abs(p1[1] - bd[1]) < 1 ? bd[1] : bd[3]);
      var sk = lx ? [bd[0] - 1.3, bd[1] - 1.1, bd[2] + 1.3, bd[3] + 1.1] : [bd[0] - 1.1, bd[1] - 1.3, bd[2] + 1.1, bd[3] + 1.3];
      var ch = lx ? [bd[0] - 1.0, bd[1] + 0.6, bd[2] + 1.0, bd[3] - 0.6] : [bd[0] + 0.6, bd[1] - 1.0, bd[2] - 0.6, bd[3] + 1.0];
      var bare = ((window.GUIDE_BOARD || {}).empty || []).indexOf(fp.r) >= 0;
      add(function (s) {
        B(s, sk, 0, 3.2);
        var nt = lx ? [e1 + (e1 === bd[0] ? 0.4 : -0.4), c[1]] : [c[0], e1 + (e1 === bd[1] ? 0.4 : -0.4)];
        if (bare) { s.ell(nt[1], nt[0], 3.2, 0.9, 'k'); p.forEach(function (q) { s.ell(q[1], q[0], 3.2, 0.45, 'k'); }); return; }
        B(s, ch, 3.2, 3.3, 'kd2');
        s.ell(nt[1], nt[0], 6.5, 0.9, 'f');                                         // the notch, at the pin-1 end
      }, 6.5);
    } else if (/R_Array_SIP/.test(f)) {                   // bussed network: dot at pin 1 (the common)
      var bs = bbox(p), q1 = padN(fp, '1'), sx = bs[2] - bs[0] >= bs[3] - bs[1];
      add(function (s) {
        B(s, sx ? [bs[0] - 1.3, c[1] - 1.1, bs[2] + 1.3, c[1] + 1.1] : [c[0] - 1.1, bs[1] - 1.3, c[0] + 1.1, bs[3] + 1.3], 0, 5, 'kd2');
        s.ell(q1[1], q1[0], 5, 0.55, 'f');
      }, 5);
    } else if (/JST_XH/.test(f)) {                        // vertical XH header: housing, pin tips
      var bx = bbox(p), hx = bx[2] - bx[0] >= bx[3] - bx[1];
      add(function (s) {
        var hb = hx ? [bx[0] - 2.45, c[1] - 2.9, bx[2] + 2.45, c[1] + 2.9] : [c[0] - 2.9, bx[1] - 2.45, c[0] + 2.9, bx[3] + 2.45];
        B(s, hb, 0, 7);
        B(s, [hb[0] + 0.8, hb[1] + 0.8, hb[2] - 0.8, hb[3] - 0.8], 7, 0.01, 'sh');
        p.forEach(function (q) { s.box(q[1] - 0.32, q[0] - 0.32, 7, 0.64, 0.64, 0.01, { cls: 'm' }); });
      }, 7);
    } else if (/BarrelJack/.test(f)) {                    // mouth toward the nearest board edge
      var bj = bbox(p), Rg = (window.GUIDE_BOARD || {}).region || [0, 0, 150, 100];
      var dE = [bj[0] - Rg[0], Rg[2] - bj[2], bj[1] - Rg[1], Rg[3] - bj[3]], side = dE.indexOf(Math.min.apply(null, dE));
      var jb = side === 1 ? [bj[0] - 1.5, c[1] - 4.5, Rg[2] + 1.2, c[1] + 4.5] : side === 0 ? [Rg[0] - 1.2, c[1] - 4.5, bj[2] + 1.5, c[1] + 4.5]
        : side === 3 ? [c[0] - 4.5, bj[1] - 1.5, c[0] + 4.5, Rg[3] + 1.2] : [c[0] - 4.5, Rg[1] - 1.2, c[0] + 4.5, bj[3] + 1.5];
      add(function (s) {
        B(s, jb, 0, 11, 'kd2');
        if (side === 1) s.vcirc(c[1], jb[2], 5.5, 3.2, 'y', 'k');
        if (side === 3) s.vcirc(jb[3], c[0], 5.5, 3.2, 'x', 'k');
      }, 11);
    } else if (/Fuse_Bourns|PTC|Varistor/.test(f)) {       // radial disc (resettable fuse): stands on its leads
      var bf = bbox(p), vf = bf[3] - bf[1] > bf[2] - bf[0];
      add(function (s) { B(s, vf ? [c[0] - 1.6, bf[1] - 2, c[0] + 1.6, bf[3] + 2] : [bf[0] - 2, c[1] - 1.6, bf[2] + 2, c[1] + 1.6], 2.5, 9); }, 11.5);
    } else if (/Jumper|Wire/.test(f)) {
      return it;
    }
    return it;
  }

  // the modules, seated on their sockets. window.GUIDE_BOARD.modules lists
  // them: {sockets: ['J20','J21'], kind: 'esp32'|'stepstick'|'plain', label}
  function moduleItems() {
    var it = [], cfg = (window.GUIDE_BOARD || {}).modules || [];
    cfg.forEach(function (m) {
      var pads = [];
      m.sockets.forEach(function (r) { var fp = fpByRef(r); if (fp) pads = pads.concat(fp.p); });
      if (!pads.length) return;
      var b = m.outline || bbox(pads, m.kind === 'esp32' ? 2.6 : 1.9), cx = (b[0] + b[2]) / 2, cy = (b[1] + b[3]) / 2;
      it.push({ k: cx + cy + 0.02, fn: function (s) {
        B(s, b, 8.5, 1.6);
        if (m.kind === 'esp32') {
          B(s, [b[0] + 6, b[1] + 5, b[0] + 30, b[3] - 5], 10.1, 1.0);            // OLED or label area
          B(s, [b[2] - 20, b[1] + 6, b[2] - 5, b[3] - 6], 10.1, 0.8, 'm');      // the WROOM can
          B(s, [b[0] - 1.5, cy - 4, b[0] + 4, cy + 4], 10.1, 2.8, 'm');         // USB
        } else if (m.kind === 'lcd') {                                               // a board with a display on top
          var ul = m.usb !== 'R';
          B(s, [b[0] + (ul ? 6 : 2), b[1] + 1.2, b[2] - (ul ? 2 : 6), b[3] - 1.2], 10.1, 1.2);
          B(s, [b[0] + (ul ? 8 : 4), b[1] + 2.4, b[2] - (ul ? 4 : 8), b[3] - 2.4], 11.3, 0.01, 'disp');
          B(s, ul ? [b[0] - 0.8, cy - 4.5, b[0] + 6.5, cy + 4.5] : [b[2] - 6.5, cy - 4.5, b[2] + 0.8, cy + 4.5], 10.1, 3.2, 'm');
        } else if (m.kind === 'stepstick') {
          B(s, [cx - 4.5, cy - 4.5, cx + 4.5, cy + 4.5], 10.1, 5, 'm');         // heatsink
          for (var i = -3; i <= 3; i += 1.5) s.line([cy - 4.5, cx + i, 15.1], [cy + 4.5, cx + i, 15.1], 't');
        }
      } });
    });
    return it;
  }
  function drawBoard(s, o) {
    o = o || {};
    var R = o.region || (window.GUIDE_BOARD || {}).region || [0, 0, 150, 100];   // board kx0 ky0 kx1 ky1 (Edge.Cuts)
    B(s, R, -1.6, 1.6, 'pcbf');
    (window.BOARD || []).forEach(function (fp) {
      if (/^MountingHole/.test(fp.f) && fp.p.length) {
        var q = fp.p[0];
        if (q[0] > R[0] && q[0] < R[2] && q[1] > R[1] && q[1] < R[3]) s.hole(q[1], q[0], 0, 1.6, 1.6);
      }
    });
    var items = [];
    (window.BOARD || []).forEach(function (fp) {
      if (!fp.p.length) return;
      var c = mid(fp.p);
      if (c[0] < R[0] || c[0] > R[2] || c[1] < R[1] || c[1] > R[3]) return;
      items = items.concat(partItems(fp));
    });
    if (o.modules !== false) items = items.concat(moduleItems());
    items.sort(function (a, b) { return a.k - b.k; });
    items.forEach(function (it) { it.fn(s); });
  }
  // callout list -> column labels outside the board
  function callouts(s, list) {
    var out = [];
    list.forEach(function (c) {
      var fp = fpByRef(c[0]); if (!fp || !fp.p.length) return;
      var m = mid(fp.p);
      out.push({ pt: [m[1], m[0], c[1]], text: c[2], side: c[3] });
    });
    s.callouts(out, { size: 12.5 });
  }

  // Overview: the whole board, assembled. Callouts from
  // window.GUIDE_BOARD.callouts = [[ref, z of the part top, text, 'L'|'R'?], ...];
  // with none given, every connector (J*) and IC/module (U*) is labelled.
  FIG.pcb_iso = function (s) {
    if (!window.BOARD) { s.raw('<text x="0" y="12">board data missing: run build.py</text>', [0, 0, 260, 20]); return { scale: 1 }; }
    drawBoard(s);
    var cfg = window.GUIDE_BOARD || {};
    var list = cfg.callouts || window.BOARD.filter(function (f) { return /^(J|U)\d/.test(f.r) && f.p.length; })
      .map(function (f) { return [f.r, 9, f.r + '  ' + (f.v || '')]; });
    callouts(s, list);
    return { w: cfg.overviewWidth || 760 };
  };
  // Close-up of one region, for the orientation step:
  // window.GUIDE_BOARD.detail = {region: [x0, y0, x1, y1] board mm, callouts: [...]}
  FIG.pcb_iso_detail = function (s) {
    if (!window.BOARD) return { scale: 1 };
    var d = (window.GUIDE_BOARD || {}).detail || { region: [0, 0, 60, 60], callouts: [] };
    drawBoard(s, { region: d.region, modules: false });
    callouts(s, d.callouts || []);
    return { w: d.width || 520 };
  };
  /* ---------------- electronics inventory: part, symbol, letter ---------------- */
  var SYM = {
    R: '<path class="l" d="M0 20h10l3 -7 6 14 6 -14 6 14 6 -14 6 14 3 -7h10"/>',
    C: '<path class="l" d="M0 20h26M34 20h26M26 8v24M34 8v24"/>',
    CP: '<path class="l" d="M0 20h26M26 8v24M40 8q-8 12 0 24M36 20h24"/><path class="l" d="M16 8h6M19 5v6"/>',
    D: '<path class="l" d="M0 20h22M38 20h22M38 8v24"/><path class="f" d="M22 8l16 12-16 12z"/>',
    DZ: '<path class="l" d="M0 20h22M38 20h22M34 6l4 2v24l4 2"/><path class="f" d="M22 8l16 12-16 12z"/>',
    DS: '<path class="l" d="M0 20h22M38 20h22M34 11v-3h4v24h4v-3"/><path class="f" d="M22 8l16 12-16 12z"/>',
    TVS: '<path class="l" d="M0 20h14M46 20h14M30 8v24"/><path class="f" d="M14 8l16 12-16 12z"/><path class="f" d="M46 8l-16 12 16 12z"/>',
    LED: '<path class="l" d="M0 20h22M38 20h22M38 8v24M34 4l8 -8M40 8l8 -8"/><path class="f" d="M22 8l16 12-16 12z"/><path class="k" d="M42 -4l-5 1 4 3zM48 0l-5 1 4 3z"/>',
    NPN: '<circle class="l" cx="30" cy="20" r="17"/><path class="l" d="M0 20h22M22 10v20M22 15l14 -9v-10M22 25l14 9v10"/><path class="k" d="M36 34l-7 -1 3 -5z"/>',
    PNP: '<circle class="l" cx="30" cy="20" r="17"/><path class="l" d="M0 20h22M22 10v20M22 15l14 -9v-10M22 25l14 9v10"/><path class="k" d="M23 26l7 0 -3 5z"/>',
    PMOS: '<circle class="l" cx="30" cy="20" r="17"/><path class="l" d="M0 26h18M18 10v16M24 8v24M24 12h10v-12M24 28h10v12M24 20h10v-8"/><path class="k" d="M33 20l-6 -3v6z"/>',
    L: '<path class="l" d="M0 20h8a5.5 5.5 0 0 1 11 0a5.5 5.5 0 0 1 11 0a5.5 5.5 0 0 1 11 0a5.5 5.5 0 0 1 11 0h8"/>',
    F: '<path class="l" d="M0 20h12M48 20h12"/><rect class="f" x="12" y="13" width="36" height="14"/><path class="l" d="M12 20h36"/>',
    SW: '<path class="l" d="M0 26h14M46 26h14M14 26l0 0M46 26l0 0M16 16h28M30 16v-10M24 6h12"/><circle class="f" cx="16" cy="26" r="2.5"/><circle class="f" cx="44" cy="26" r="2.5"/>',
    U: '<rect class="f" x="12" y="2" width="36" height="36"/><path class="l" d="M0 10h12M0 20h12M0 30h12M48 20h12"/>',
    J: '<path class="l" d="M0 6h40M0 20h40M0 34h40"/><circle class="f" cx="44" cy="6" r="4"/><circle class="f" cx="44" cy="20" r="4"/><circle class="f" cx="44" cy="34" r="4"/>',
    RN: '<path class="l" d="M4 4h52M8 4v6M22 4v6M36 4v6M50 4v6"/>' + [8, 22, 36, 50].map(function (x) { return '<rect class="f" x="' + (x - 3) + '" y="10" width="6" height="16"/><path class="l" d="M' + x + ' 26v10"/>'; }).join('') + '<circle class="k" cx="4" cy="4" r="2.2"/>',
    DC: '<path class="l" d="M0 10h30M0 30h40v-8M30 4v12h12"/><path class="f" d="M40 18l-4 6h8z"/>',
    PTC: '<path class="l" d="M0 20h12M48 20h12M16 34l28 -28M44 6h6"/><rect class="f" x="12" y="13" width="36" height="14"/>',
    MOD: '<rect class="f" x="10" y="2" width="40" height="36" rx="3"/><rect class="disp" x="16" y="8" width="28" height="18"/><path class="l" d="M0 32h10M50 32h10"/>',
    JP: '<circle class="f" cx="8" cy="20" r="4"/><circle class="f" cx="30" cy="20" r="4"/><circle class="f" cx="52" cy="20" r="4"/><rect class="l" x="1" y="12" width="36" height="16" rx="6"/>'
  };
  function card(art, sym, letter) {
    return '<g>' + art + '</g><path class="grid" d="M104 8V88"/>' +
      '<g transform="translate(118 18)">' + SYM[sym] + '</g>' + T(148, 86, letter, { size: 18, cls: 'tx cnt' });
  }
  function lead(x1, y1, x2, y2) { return '<path class="lead" d="M' + x1 + ' ' + y1 + 'L' + x2 + ' ' + y2 + '"/>'; }
  var ART = {
    res: lead(4, 48, 24, 48) + lead(76, 48, 96, 48) + '<rect class="f" x="24" y="40" width="52" height="16" rx="7"/><path class="l" d="M34 40v16M42 40v16M50 40v16M66 40v16"/>',
    cer: lead(40, 58, 40, 90) + lead(60, 58, 60, 90) + '<ellipse class="f" cx="50" cy="42" rx="20" ry="18"/>' + T(50, 47, '104', { size: 11, cls: 'mono' }),
    elec: lead(40, 76, 40, 94) + lead(60, 76, 60, 88) + '<rect class="f" x="30" y="14" width="40" height="62" rx="3"/><rect class="stripe2" x="58" y="14" width="12" height="62"/><path class="lp" d="M61 36h6M61 52h6"/>',
    diode: lead(4, 48, 30, 48) + lead(70, 48, 96, 48) + '<rect class="kd" x="30" y="40" width="40" height="16" rx="2"/><rect class="stripe" x="60" y="40" width="5" height="16"/>',
    zener: lead(4, 48, 34, 48) + lead(66, 48, 96, 48) + '<rect class="f" x="34" y="42" width="32" height="12" rx="5"/><rect class="kd" x="58" y="42" width="4" height="12"/>',
    tvs: lead(4, 48, 28, 48) + lead(72, 48, 96, 48) + '<rect class="kd" x="28" y="38" width="44" height="20" rx="3"/>',
    schottky: lead(4, 48, 24, 48) + lead(76, 48, 96, 48) + '<rect class="kd" x="24" y="36" width="52" height="24" rx="3"/><rect class="stripe" x="64" y="36" width="6" height="24"/>',
    led: lead(42, 60, 42, 94) + lead(58, 60, 58, 86) + '<path class="f" d="M36 60V34a14 14 0 0 1 28 0V60Z"/><path class="f" d="M32 60H66V66H32Z"/>',
    to92: lead(38, 64, 38, 92) + lead(50, 64, 50, 92) + lead(62, 64, 62, 92) + '<path class="f" d="M30 64V30H70V64Z"/>' + T(50, 50, '3904', { size: 9, cls: 'mono' }),
    to220: lead(38, 70, 38, 94) + lead(50, 70, 50, 94) + lead(62, 70, 62, 94) + '<rect class="m" x="28" y="6" width="44" height="24"/><circle class="f" cx="50" cy="17" r="5"/><rect class="f" x="28" y="28" width="44" height="42"/>',
    to220_5: [34, 42, 50, 58, 66].map(function (x, i) { return lead(x, 70, x, i % 2 ? 88 : 94); }).join('') + '<rect class="m" x="28" y="6" width="44" height="24"/><circle class="f" cx="50" cy="17" r="5"/><rect class="f" x="28" y="28" width="44" height="42"/>',
    ind: lead(40, 70, 40, 92) + lead(60, 70, 60, 92) + '<rect class="f" x="24" y="24" width="52" height="46" rx="6"/><path class="t" d="M28 36h44M28 46h44M28 56h44"/>',
    fuse: '<rect class="m" x="10" y="36" width="12" height="24"/><rect class="m" x="78" y="36" width="12" height="24"/><rect class="f" x="18" y="40" width="64" height="16" rx="6"/><path class="t" d="M22 48h56"/>',
    sw: [30, 70].map(function (x) { return lead(x, 66, x, 90); }).join('') + '<rect class="f" x="24" y="40" width="52" height="26"/><circle class="f" cx="50" cy="40" r="10"/>',
    term: '<rect class="f" x="10" y="30" width="80" height="40" rx="3"/>' + [30, 70].map(function (x) { return '<circle class="f" cx="' + x + '" cy="44" r="9"/><path class="l" d="M' + (x - 6) + ' 44h12"/>'; }).join('') + '<rect class="k" x="20" y="58" width="20" height="8"/><rect class="k" x="60" y="58" width="20" height="8"/>',
    header: '<rect class="k" x="10" y="54" width="80" height="12"/>' + [20, 35, 50, 65, 80].map(function (x) { return '<rect class="m" x="' + (x - 2) + '" y="26" width="4" height="54"/>'; }).join(''),
    socket: '<rect class="f" x="10" y="36" width="80" height="30"/>' + [20, 35, 50, 65, 80].map(function (x) { return '<rect class="k" x="' + (x - 3) + '" y="40" width="6" height="6"/>' + lead(x, 66, x, 82); }).join(''),
    usb: '<rect class="m" x="14" y="24" width="72" height="44"/><rect class="k" x="24" y="34" width="52" height="14"/>' + [30, 42, 54, 66].map(function (x) { return lead(x, 68, x, 84); }).join(''),
    shunt: '<rect class="f" x="30" y="30" width="40" height="34" rx="4"/><rect class="k" x="38" y="36" width="8" height="8"/><rect class="k" x="54" y="36" width="8" height="8"/>',
    dip: [18, 30, 42, 54, 66, 78].map(function (x) { return lead(x, 62, x, 80) + lead(x, 26, x, 18); }).join('') + '<rect class="kd" x="10" y="26" width="80" height="36" rx="2"/><path class="stripe" d="M10 38a6 6 0 0 1 0 12z"/><circle class="stripe" cx="19" cy="54" r="2.4"/>',
    sip: [16, 27, 38, 49, 60, 71, 82].map(function (x) { return lead(x, 58, x, 84); }).join('') + '<rect class="kd" x="8" y="28" width="84" height="30" rx="3"/><circle class="stripe" cx="16" cy="36" r="3"/>',
    xh: '<rect class="f" x="12" y="30" width="76" height="36"/><rect class="sh" x="17" y="35" width="66" height="24"/>' + [26, 42, 58, 74].map(function (x) { return '<rect class="m" x="' + (x - 2) + '" y="40" width="4" height="12"/>' + lead(x, 66, x, 84); }).join(''),
    dc: '<rect class="kd" x="14" y="24" width="58" height="46" rx="3"/><rect class="kd" x="72" y="30" width="16" height="34"/><circle class="stripe" cx="80" cy="47" r="9"/><circle class="kd" cx="80" cy="47" r="3.5"/>' + [24, 44, 62].map(function (x) { return lead(x, 70, x, 86); }).join(''),
    ptc: lead(40, 72, 40, 94) + lead(60, 72, 60, 94) + '<rect class="f" x="26" y="18" width="48" height="54" rx="16"/>' + T(50, 50, 'R250', { size: 10, cls: 'mono' }),
    module: '<rect class="pcb" x="6" y="22" width="88" height="44" rx="3"/><rect class="disp" x="24" y="28" width="56" height="32" rx="2"/><rect class="m" x="0" y="37" width="14" height="14" rx="3"/>' + [20, 36, 52, 68, 84].map(function (x) { return lead(x, 66, x, 84); }).join('')
  };
  var EC = {
    ec_r: ['res', 'R', 'R'], ec_c: ['cer', 'C', 'C'], ec_cp: ['elec', 'CP', 'C'], ec_dz: ['zener', 'DZ', 'D'],
    ec_tvs: ['tvs', 'TVS', 'D'], ec_ds: ['schottky', 'DS', 'D'], ec_led: ['led', 'LED', 'LED'],
    ec_pmos: ['to220', 'PMOS', 'Q'], ec_npn: ['to92', 'NPN', 'Q'], ec_pnp: ['to92', 'PNP', 'Q'],
    ec_u: ['to220_5', 'U', 'U'], ec_l: ['ind', 'L', 'L'], ec_f: ['fuse', 'F', 'F'], ec_sw: ['sw', 'SW', 'SW'],
    ec_term: ['term', 'J', 'J'], ec_hdr: ['header', 'J', 'J'], ec_sock: ['socket', 'J', 'J'], ec_usb: ['usb', 'J', 'J'],
    ec_shunt: ['shunt', 'JP', 'JP'],
    ec_dip: ['dip', 'U', 'U'], ec_sip: ['sip', 'RN', 'RN'], ec_xh: ['xh', 'J', 'J'], ec_dc: ['dc', 'DC', 'J'],
    ec_ptc: ['ptc', 'PTC', 'F'], ec_mod: ['module', 'MOD', 'J']
  };
  Object.keys(EC).forEach(function (k) {
    FIG[k] = function (s) { var e = EC[k]; return flat(s, 200, 96, card(ART[e[0]], e[1], e[2])); };
  });
})();

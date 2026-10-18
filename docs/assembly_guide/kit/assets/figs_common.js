/* figs_common.js -- flat (2D) figures any build guide can use: the little person,
   tools, check panels, PCB part-orientation panels, and the multimeter. */
(function () {
  'use strict';
  var FIG = window.FIG = window.FIG || {};
  var flat = function (s, w, h, svg) { s.raw(svg, [0, 0, w, h]); return { scale: 1, pad: 0 }; };
  function T(x, y, t, o) {
    o = o || {};
    return '<text class="' + (o.cls || 'tx') + '" x="' + x + '" y="' + y + '" font-size="' + (o.size || 12) + '" text-anchor="' + (o.a || 'middle') + '"' + (o.style ? ' style="' + o.style + '"' : '') + '>' +
      String(t).replace(/&/g, '&amp;').replace(/</g, '&lt;') + '</text>';
  }
  function L(x1, y1, x2, y2, c) { return '<path class="' + (c || 't') + '" d="M' + x1 + ' ' + y1 + 'L' + x2 + ' ' + y2 + '"/>'; }
  function lead(x, y, tx, ty, t) { return '<circle class="k" cx="' + x + '" cy="' + y + '" r="2"/>' + L(x, y, tx, ty) + T(tx + (tx < x ? -4 : 4), ty + 4, t, { a: tx < x ? 'end' : 'start' }); }
  function pad(x, y, sq, r) { r = r || 8; return sq ? '<rect class="pad" x="' + (x - r) + '" y="' + (y - r) + '" width="' + 2 * r + '" height="' + 2 * r + '"/><circle class="drill" cx="' + x + '" cy="' + y + '" r="' + r * 0.42 + '"/>' : '<circle class="pad" cx="' + x + '" cy="' + y + '" r="' + r + '"/><circle class="drill" cx="' + x + '" cy="' + y + '" r="' + r * 0.42 + '"/>'; }
  function board(x, y, w, h) { return '<rect class="pcb" x="' + x + '" y="' + y + '" width="' + w + '" height="' + h + '" rx="3"/>'; }
  function guide(x, y1, y2) { return '<path class="dl" d="M' + x + ' ' + y1 + 'V' + y2 + '"/>'; }
  function arrowUp(x, y) { return '<path class="ar" d="M' + x + ' ' + y + 'l-8 12h5v14h6v-14h5z"/>'; }
  function arrowDown(x, y) { return '<path class="ar" d="M' + x + ' ' + y + 'l-8 -12h5v-14h6v14h5z"/>'; }

  /* ---------------- the little person ---------------- */
  function man(x, y, sc, mood) {
    var mouth = mood === 'sad' ? '<path class="l" d="M37 39 Q45 33 53 39"/>' : mood === 'hmm' ? '<path class="l" d="M37 37 Q41 34 45 37 Q49 40 53 37"/>' : '<path class="l" d="M36 34 Q45 43 54 34"/>';
    return '<g transform="translate(' + x + ' ' + y + ') scale(' + sc + ')">' +
      '<path class="l" d="M22 70 C4 80 6 100 22 104"/><path class="l" d="M68 70 C86 80 84 100 68 104"/>' +
      '<path class="f" d="M28 50 C12 60 8 88 16 110 L21 150 H69 L74 110 C82 88 78 60 62 50 Z"/>' +
      '<path class="l" d="M45 124 V150"/>' +
      '<ellipse class="f" cx="45" cy="28" rx="18" ry="21"/>' +
      '<circle class="k" cx="38.5" cy="24" r="1.9"/><circle class="k" cx="51.5" cy="24" r="1.9"/>' + mouth + '</g>';
  }
  FIG.man_ok = function (s) { return flat(s, 100, 160, man(5, 4, 1, 'ok')); };
  FIG.man_hmm = function (s) {
    return flat(s, 170, 160, man(5, 4, 1, 'hmm') + '<circle class="f" cx="128" cy="40" r="26"/>' + T(128, 52, '?', { size: 34, cls: 'cnt' }) +
      '<circle class="f" cx="96" cy="70" r="5"/><circle class="f" cx="86" cy="84" r="3"/>');
  };
  FIG.man_call = function (s) {
    return flat(s, 300, 160, man(5, 4, 1, 'ok') +
      '<path class="l" d="M60 20 c14 -4 18 10 8 16"/>' +
      '<path class="l" d="M70 40 C120 70 130 120 180 118"/>' +
      '<rect class="f" x="180" y="60" width="110" height="90" rx="4"/>' + T(235, 88, 'RESUME.md', { size: 14, cls: 'cnt' }) +
      T(235, 110, 'DESIGN_NOTES.md', { size: 11 }) + T(235, 128, 'PCB.md', { size: 11 }) + T(235, 144, 'FIRMWARE.md', { size: 11 }));
  };

  /* ---------------- tools ---------------- */
  FIG.tools = function (s) {
    var g = '';
    // hex keys
    g += '<path class="k" d="M20 20 h8 v70 h-8z"/><path class="k" d="M20 82 h26 v8 h-26z"/>' + T(33, 112, '2.5 mm hex') + T(33, 126, '1.5 mm hex', { size: 11 });
    // calipers
    g += '<path class="f" d="M80 20 h110 v12 h-110z"/><path class="f" d="M84 32 h10 v34 l-10 -8z"/><path class="f" d="M140 32 h12 v34 l-12 -8z"/><rect class="f" x="138" y="14" width="28" height="24" rx="3"/>' + T(135, 112, 'calipers');
    // countersink bit
    g += '<path class="m" d="M222 20 h10 v44 l12 14 h-34 l12 -14z"/><path class="l" d="M218 78 l9 18 l9 -18"/>' + T(228, 112, 'countersink');
    // soldering iron
    g += '<path class="f" d="M270 90 l18 -18 l30 -30 l8 8 l-30 30 l-18 18z"/><path class="l" d="M326 42 l14 -14"/>' + T(305, 112, 'iron, flux');
    // flush cutters
    g += '<path class="f" d="M372 96 l10 -46 l6 0 l-4 46z"/><path class="f" d="M408 96 l-10 -46 l-6 0 l4 46z"/><path class="k" d="M382 50 l6 -26 l4 26z"/>' + T(390, 112, 'flush cutters');
    // multimeter
    g += '<rect class="f" x="440" y="20" width="46" height="72" rx="6"/><rect class="f" x="447" y="27" width="32" height="18"/>' + T(463, 41, '5.00', { size: 10, cls: 'mono' }) + '<circle class="l" cx="463" cy="68" r="11"/>' + T(463, 112, 'multimeter');
    // cut-off wheel
    g += '<circle class="f" cx="530" cy="50" r="24"/><circle class="k" cx="530" cy="50" r="4"/><path class="f" d="M530 50 l40 30 l-6 8 l-38 -32z"/>' + T(540, 112, 'cut-off wheel');
    return flat(s, 590, 130, g);
  };

  /* ---------------- check panels ---------------- */
  FIG.roll_ok = function (s) {
    return flat(s, 220, 90, '<path class="l" d="M10 70 H210"/><rect class="m" x="40" y="58" width="140" height="11" rx="2"/><rect class="m" x="34" y="54" width="7" height="19" rx="1"/>' +
      '<path class="ra" d="M70 40 H150"/><path class="k" d="M150 34 l12 6 l-12 6z"/>' + T(110, 88, 'rolls flat, no daylight'));
  };
  FIG.roll_no = function (s) {
    return flat(s, 220, 90, '<path class="l" d="M10 70 H210"/><path class="m" d="M40 66 Q110 46 180 66 L180 55 Q110 36 40 55 Z"/>' +
      '<path class="l" d="M100 70 V58 M112 70 V55 M124 70 V57"/>' + T(110, 88, 'rocks, shows a gap'));
  };
  FIG.square_ok = function (s) {
    return flat(s, 160, 110, '<rect class="f" x="10" y="80" width="140" height="14"/><rect class="m" x="72" y="20" width="10" height="60"/><rect class="m" x="66" y="94" width="22" height="5"/>' +
      '<path class="f" d="M92 80 V24 h8 v48 h40 v8z"/>');
  };
  FIG.square_no = function (s) {
    return flat(s, 160, 110, '<rect class="f" x="10" y="80" width="140" height="14"/><path class="m" d="M72 80 L88 22 L97 24 L82 80 Z"/><rect class="m" x="66" y="94" width="22" height="5"/>' +
      '<path class="f" d="M106 80 V24 h8 v48 h30 v8z"/>');
  };
  function bearingSection(x, y) {
    return '<rect class="m" x="' + (x - 40) + '" y="' + y + '" width="16" height="30"/><rect class="m" x="' + (x + 24) + '" y="' + y + '" width="16" height="30"/>' +
      '<rect class="m" x="' + (x - 21) + '" y="' + y + '" width="9" height="30"/><rect class="m" x="' + (x + 12) + '" y="' + y + '" width="9" height="30"/>' +
      '<circle class="f" cx="' + (x - 18.5) + '" cy="' + (y + 15) + '" r="0"/><circle class="k" cx="' + (x - 22.5) + '" cy="' + (y + 15) + '" r="4"/><circle class="k" cx="' + (x + 22.5) + '" cy="' + (y + 15) + '" r="4"/>';
  }
  FIG.press_ok = function (s) {
    return flat(s, 200, 150, '<path class="f" d="M40 70 H56 V140 H40Z M144 70 H160 V140 H144Z"/>' + bearingSection(100, 80) +
      '<path class="f" d="M58 20 H76 V76 H58Z M124 20 H142 V76 H124Z M58 20 H142 V32 H58Z"/>' + arrowDown(100, 14) + T(100, 148, 'push the OUTER race'));
  };
  FIG.press_no = function (s) {
    return flat(s, 200, 150, '<path class="f" d="M40 70 H56 V140 H40Z M144 70 H160 V140 H144Z"/>' + bearingSection(100, 80) +
      '<path class="f" d="M80 30 H120 V78 H80Z"/>' + arrowDown(100, 24) + T(100, 148, 'inner race: brinells balls'));
  };
  /* ---------------- known-issue sections ---------------- */
  // Rev B tower, half section: plate clamped between flange and disc
  /* ---------------- PCB orientation panels ---------------- */
  // each: part drawn above its footprint, dashed guides from legs to pads
  FIG.pcb_legend = function (s) {
    var c = function (i, j) { return [15 + i * 170, 12 + j * 110]; }, g = '';
    var cell = function (i, j, draw, t1) { var p = c(i, j); g += '<g transform="translate(' + (p[0] + 10) + ' ' + p[1] + ')">' + board(0, 0, 130, 70) + draw + '</g>' + T(p[0] + 75, p[1] + 90, t1, { size: 11 }); };
    cell(0, 0, pad(45, 35, true) + pad(85, 35, false), 'square pad = pin 1, +, or K');
    cell(1, 0, '<circle class="silk" cx="65" cy="35" r="26"/>' + pad(50, 35, true) + pad(80, 35, false) + T(22, 26, '+', { size: 16, cls: 'silkt' }), '"+" = long leg');
    cell(2, 0, '<path class="silk" d="M50 58 A24 24 0 1 1 88 50 L88 20"/>' + pad(56, 35, false) + pad(80, 35, true), 'flat edge = flat of the part');
    cell(0, 1, '<rect class="silk" x="22" y="18" width="86" height="30"/><rect class="silkk" x="22" y="14" width="86" height="6"/>' + pad(40, 56, true, 6) + pad(65, 56, false, 6) + pad(90, 56, false, 6), 'bold bar = tab side');
    cell(1, 1, '<circle class="silk" cx="50" cy="35" r="17"/>' + pad(50, 35, false, 7) + '<path class="silk" d="M67 35 H80"/>' + pad(88, 35, true, 7), 'circle = body stands here');
    cell(2, 1, pad(30, 35, true, 6) + pad(50, 35, false, 6) + pad(70, 35, false, 6) + pad(90, 35, false, 6) + T(30, 20, '1', { size: 15, cls: 'silkt' }), '"1" = socket pin 1');
    return flat(s, 520, 230, g);
  };
  function standing(body, bentTo, kind) {
    // body over pad at x=150, bent top lead into pad at x=bentTo
    var g = '';
    if (kind === 'res') {
      g += '<rect class="f" x="136" y="60" width="28" height="78" rx="10"/>';
      [74, 86, 98, 110].forEach(function (y) { g += '<path class="l" d="M137 ' + y + 'H163"/>'; });
      g += '<path class="l" d="M137 126H163"/>';
    } else {
      g += '<rect class="kd" x="137" y="62" width="26" height="74" rx="3"/><rect class="stripe" x="137" y="68" width="26" height="9"/>';
    }
    g += '<path class="lead" d="M150 138 V184"/><path class="lead" d="M150 60 V40 Q150 30 ' + (bentTo + (bentTo < 150 ? 10 : -10)) + ' 30 Q' + bentTo + ' 30 ' + bentTo + ' 40 V184"/>';
    return g;
  }
  FIG.pcb_res = function (s) {
    var g = board(40, 196, 220, 50) + '<circle class="silk" cx="150" cy="221" r="19"/><path class="silk" d="M169 221 H172"/>' + pad(150, 221, false) + pad(180, 221, false);
    g += standing(0, 180, 'res') + guide(150, 186, 210) + guide(180, 186, 210);
    g += lead(150, 202, 124, 168, 'body over the circle') + T(250, 100, 'no polarity', { a: 'end', size: 12 });
    return flat(s, 300, 256, g);
  };
  FIG.pcb_diode = function (s) {
    var g = board(40, 196, 220, 50) + '<circle class="silk" cx="150" cy="221" r="19"/>' + pad(150, 221, false) + pad(110, 221, true) + T(84, 226, 'K', { size: 15, cls: 'silkt' });
    g += standing(0, 110, 'diode') + guide(150, 186, 210) + guide(110, 186, 210);
    g += lead(163, 72, 220, 60, 'stripe at the TOP') + lead(110, 120, 58, 120, 'bent lead');
    return flat(s, 300, 256, g);
  };
  FIG.pcb_cap = function (s) {
    var g = board(30, 196, 240, 60) + '<circle class="silk" cx="150" cy="226" r="0"/>' + '<circle class="silk" cx="150" cy="226" r="0"/>';
    g += '<path class="silk" d="M150 196 m-58 0"/>';
    g = board(30, 190, 240, 62) + '<circle class="silk" cx="150" cy="221" r="44" />';
    g += pad(128, 221, true) + pad(172, 221, false) + T(84, 212, '+', { size: 20, cls: 'silkt' });
    g += '<path class="f" d="M108 40 H192 V150 H108 Z"/><rect class="stripe2" x="170" y="40" width="22" height="110"/>';
    [66, 90, 114].forEach(function (y) { g += '<path class="lp" d="M176 ' + y + 'H186"/>'; });
    g += '<ellipse class="f" cx="150" cy="40" rx="42" ry="6"/>';
    g += '<path class="lead" d="M128 150 V196"/><path class="lead" d="M172 150 V184"/>' + guide(128, 196, 208) + guide(172, 186, 208);
    g += lead(128, 172, 60, 170, 'long leg = +') + lead(192, 96, 252, 96, 'stripe = minus');
    return flat(s, 300, 260, g);
  };
  FIG.pcb_led = function (s) {
    var g = board(40, 190, 220, 62) + '<path class="silk" d="M168 207 A26 26 0 1 0 168 235"/><path class="silk" d="M168 207 V235"/>';
    g += pad(135, 221, false) + pad(165, 221, true) + T(196, 226, 'K', { size: 15, cls: 'silkt' });
    g += '<path class="f" d="M122 110 V70 A28 28 0 0 1 178 70 V110 Z"/><path class="f" d="M116 110 H178 V120 H116 Z"/><path class="l" d="M178 110 V120"/>';
    g += '<path class="lead" d="M135 120 V200"/><path class="lead" d="M165 120 V184"/>' + guide(165, 186, 210);
    g += lead(165, 150, 196, 150, 'short leg, flat side') + lead(135, 160, 70, 160, 'long leg');
    return flat(s, 320, 260, g);
  };
  FIG.pcb_to92 = function (s) {
    var g = board(20, 176, 260, 70);
    g += '<path class="silk" d="M100 226 A38 38 0 0 1 176 226 Z"/>' + pad(108, 214, true, 7) + pad(138, 214, false, 7) + pad(168, 214, false, 7);
    g += '<path class="f" d="M100 124 A38 38 0 0 1 176 124 Z"/>' + T(138, 118, 'top view', { size: 10 });
    g += guide(108, 128, 204) + guide(138, 128, 204) + guide(168, 128, 204);
    g += lead(176, 124, 236, 150, 'flat face') + lead(176, 226, 236, 214, 'flat edge');
    // front view
    g += '<path class="f" d="M22 40 H78 V96 H22 Z"/>' + T(50, 62, '2N', { size: 11, cls: 'mono' }) + T(50, 76, '3904', { size: 11, cls: 'mono' });
    g += '<path class="lead" d="M34 96 V140 M50 96 V140 M66 96 V140"/>' + T(34, 154, 'E', { size: 11 }) + T(50, 154, 'B', { size: 11 }) + T(66, 154, 'C', { size: 11 }) + T(50, 30, 'flat face to you', { size: 10 });
    return flat(s, 290, 256, g);
  };
  FIG.pcb_to220 = function (s, el) {
    var part = (el && el.getAttribute('data-part')) || 'IRF4905';
    var g = board(30, 190, 240, 66);
    g += '<rect class="silk" x="96" y="200" width="108" height="24"/><rect class="silkk" x="96" y="196" width="108" height="6"/>' + pad(125, 238, true, 7) + pad(150, 238, false, 7) + pad(175, 238, false, 7);
    g += '<rect class="m" x="100" y="20" width="100" height="44"/><circle class="f" cx="150" cy="40" r="9"/><rect class="f" x="100" y="60" width="100" height="62"/>' + T(150, 94, part, { size: 12, cls: 'mono' });
    g += '<path class="lead" d="M125 122 V176 M150 122 V176 M175 122 V176"/>' + guide(125, 178, 228) + guide(150, 178, 228) + guide(175, 178, 228);
    g += lead(200, 34, 250, 24, 'metal tab') + lead(204, 199, 256, 176, 'bold bar');
    g += T(125, 138, '1', { size: 11 }) + T(62, 150, 'G D S', { size: 12, cls: 'mono' });
    return flat(s, 300, 262, g);
  };
  FIG.pcb_lm2596 = function (s) {
    var g = board(30, 190, 240, 72);
    g += '<rect class="silk" x="92" y="198" width="116" height="22"/><rect class="silkk" x="92" y="194" width="116" height="6"/>';
    var xs = [110, 130, 150, 170, 190];
    xs.forEach(function (x, i) { g += pad(x, i % 2 ? 250 : 234, i === 0, 6); });
    g += '<rect class="m" x="96" y="20" width="108" height="44"/><circle class="f" cx="150" cy="40" r="9"/><rect class="f" x="96" y="60" width="108" height="62"/>' + T(150, 88, 'LM2596T', { size: 12, cls: 'mono' }) + T(150, 104, '-5.0', { size: 12, cls: 'mono' });
    xs.forEach(function (x, i) { g += '<path class="lead" d="M' + x + ' 122 V' + (i % 2 ? 168 : 150) + ' L' + x + ' ' + (i % 2 ? 176 : 176) + '"/>' + guide(x, 178, i % 2 ? 244 : 228); });
    g += T(110, 138, '1', { size: 11 }) + lead(204, 199, 256, 176, 'tab side') + T(60, 238, '1 3 5', { size: 11, cls: 'mono' }) + T(60, 254, '2 4', { size: 11, cls: 'mono' });
    return flat(s, 300, 268, g);
  };
  FIG.pcb_socket = function (s) {
    var g = board(10, 150, 330, 60), i;
    g += '<rect class="f" x="30" y="160" width="290" height="20"/>';
    for (i = 0; i < 15; i++) g += '<rect class="k" x="' + (37 + i * 19) + '" y="166" width="7" height="7"/>';
    g += T(24, 176, '1', { size: 14, cls: 'silkt', a: 'end' });
    g += '<rect class="f" x="30" y="30" width="290" height="36" rx="3"/>' + T(175, 54, 'module, header pins down', { size: 11 });
    for (i = 0; i < 15; i++) g += '<path class="lead" d="M' + (40.5 + i * 19) + ' 66 V92"/>';
    g += guide(40.5, 96, 160) + guide(306.5, 96, 160) + T(175, 128, 'plug the module in, then solder the socket', { size: 11 });
    return flat(s, 350, 216, g);
  };
  FIG.pcb_fuse = function (s) {
    var g = board(20, 110, 300, 50);
    [90, 250].forEach(function (x, i) {
      var sg = i ? 1 : -1;
      g += '<path class="m" d="M' + (x - 16) + ' 100 V60 Q' + x + ' 36 ' + (x + 16) + ' 60 V100 Z"/>';
      g += '<path class="k" d="M' + (x + sg * 18) + ' 50 h' + (sg * 6) + ' v40 h' + (-sg * 6) + 'z"/>';
    });
    g += '<rect class="f" x="76" y="62" width="188" height="22" rx="10"/>' + T(170, 78, '3 A  5x20', { size: 11, cls: 'mono' });
    g += lead(274, 58, 300, 30, 'stop tab faces OUT');
    return flat(s, 340, 170, g);
  };

  // an axial diode lying flat (DO-41 on a 10.16 mm footprint): band over the square pad
  FIG.pcb_diode_flat = function (s) {
    var g = board(30, 176, 240, 60) + '<rect class="silk" x="112" y="195" width="76" height="22"/><rect class="silkk" x="112" y="195" width="8" height="22"/>';
    g += pad(80, 206, true) + pad(220, 206, false) + T(80, 190, 'K', { size: 15, cls: 'silkt' });
    g += '<rect class="kd" x="112" y="84" width="76" height="26" rx="4"/><rect class="stripe" x="120" y="84" width="9" height="26"/>';
    g += '<path class="lead" d="M112 97 H90 Q80 97 80 107 V176"/><path class="lead" d="M188 97 H210 Q220 97 220 107 V176"/>' + guide(80, 150, 196) + guide(220, 150, 196);
    g += lead(124, 84, 150, 40, 'band over the square pad (K)') + lead(188, 110, 230, 150, 'lies flat');
    return flat(s, 300, 246, g);
  };
  // an IC socket: its notch over the silkscreen notch; then the chip's notch over the socket's
  FIG.pcb_dip = function (s) {
    var g = board(20, 150, 300, 86), i;
    g += '<path class="silk" d="M42 162 H298 V224 H42 V201 A8 8 0 0 0 42 185 Z"/>';
    for (i = 0; i < 7; i++) { g += pad(62 + i * 36, 214, i === 0, 7) + pad(62 + i * 36, 172, false, 7); }
    g += T(62, 244, '1', { size: 14, cls: 'silkt' });
    g += '<rect class="f" x="42" y="30" width="256" height="62" rx="2"/><path class="f" d="M42 50 A11 11 0 0 1 42 72 Z"/>';
    for (i = 0; i < 7; i++) g += '<rect class="k" x="' + (58 + i * 36) + '" y="36" width="8" height="8"/><rect class="k" x="' + (58 + i * 36) + '" y="78" width="8" height="8"/>';
    g += guide(42, 96, 180) + guide(298, 96, 164);
    g += lead(46, 61, 14, 20, 'socket notch') + lead(44, 193, 14, 130, 'silkscreen notch') + T(170, 118, 'notch over notch, pin 1 on the square pad', { size: 11.5 });
    return flat(s, 330, 250, g);
  };
  // a bussed resistor network (SIP): the dot is pin 1, the common
  FIG.pcb_sip = function (s) {
    var g = board(20, 170, 300, 60), i;
    g += '<rect class="silk" x="40" y="186" width="260" height="28"/><path class="silk" d="M66 186 V214"/>';
    for (i = 0; i < 8; i++) g += pad(53 + i * 34, 200, i === 0, 7);
    g += '<rect class="kd" x="40" y="40" width="260" height="50" rx="4"/><circle class="stripe" cx="54" cy="54" r="5"/>' + T(170, 72, '4608X-101-103', { size: 11, cls: 'mono' });
    for (i = 0; i < 8; i++) g += '<path class="lead" d="M' + (53 + i * 34) + ' 90 V150"/>';
    g += guide(53, 150, 190) + guide(291, 150, 190);
    g += lead(54, 54, 20, 24, 'dot = pin 1 = common') + lead(53, 210, 20, 246, 'square pad, bar on the silkscreen');
    return flat(s, 330, 256, g);
  };
  // a vertical JST-XH header: pin 1 on the square pad, housing inside its outline
  FIG.pcb_xh = function (s) {
    var g = board(20, 168, 300, 70), i;
    g += '<rect class="silk" x="60" y="178" width="200" height="52"/>';
    for (i = 0; i < 5; i++) g += pad(90 + i * 35, 196, i === 0, 7);
    g += T(90, 222, '1', { size: 14, cls: 'silkt' });
    g += '<rect class="f" x="60" y="30" width="200" height="92"/><rect class="sh" x="70" y="40" width="180" height="56"/>';
    for (i = 0; i < 5; i++) g += '<rect class="m" x="' + (86 + i * 35) + '" y="50" width="8" height="30"/><path class="lead" d="M' + (90 + i * 35) + ' 122 V150"/>';
    g += '<rect class="f" x="104" y="96" width="112" height="26"/>';
    g += guide(60, 126, 178) + guide(260, 126, 178);
    g += lead(160, 108, 196, 16, 'housing in its outline') + lead(90, 196, 30, 150, 'pin 1');
    return flat(s, 320, 246, g);
  };

  /* ---------------- meter ---------------- */
  FIG.meter = function (s, el) {
    // data-mode: ohm | volt | amp -- the dial points at it, a badge names it,
    // the display shows its unit (a newcomer should not have to infer it)
    var v = el.getAttribute('data-v') || '5.00', a = el.getAttribute('data-a') || '+', b = el.getAttribute('data-b') || 'GND';
    var mode = el.getAttribute('data-mode') || (v === 'OL' ? 'ohm' : 'volt');
    var M = { ohm: ['RESISTANCE', 'Ω', -50], volt: ['VOLTAGE  DC', 'V', 0], amp: ['CURRENT', 'A', 50] }[mode];
    var g = '<rect class="f" x="10" y="8" width="110" height="168" rx="10"/><rect class="disp" x="22" y="20" width="86" height="36" rx="2"/>' +
      T(58, 46, v, { size: 19, cls: 'mono' }) + T(101, 46, v === 'OL' || /[ΩVA]\s*$/.test(v) ? '' : M[1], { size: 11, a: 'end', cls: 'mono' });   // no second unit if the reading has one
    g += '<rect class="k" x="20" y="62" width="90" height="16" rx="3"/>' + T(65, 74, M[0], { size: 10, style: 'fill:var(--paper);font-weight:800' });
    var cx = 65, cy = 124, r = 19;
    [['Ω', -50, 'ohm'], ['V⎓', 0, 'volt'], ['A', 50, 'amp']].forEach(function (m) {
      var t = (m[1] - 90) * Math.PI / 180, on = m[2] === mode;
      g += T(cx + 30 * Math.cos(t), cy + 30 * Math.sin(t) + 4, m[0], { size: on ? 13 : 10, style: on ? 'font-weight:800' : 'fill:var(--ink2);font-weight:500' });
    });
    var tp = (M[2] - 90) * Math.PI / 180;
    g += '<circle class="l" cx="' + cx + '" cy="' + cy + '" r="' + r + '"/><path class="l" style="stroke-width:3" d="M' + cx + ' ' + cy + ' L' +
      (cx + (r - 3) * Math.cos(tp)).toFixed(1) + ' ' + (cy + (r - 3) * Math.sin(tp)).toFixed(1) + '"/>';
    var RED = 'stroke:#d42a22';            // the red lead is red, the black lead ink, as on a real meter
    g += '<circle class="k" cx="40" cy="162" r="5"/><circle cx="90" cy="162" r="5" style="fill:#d42a22"/>';
    g += '<path class="probe" style="' + RED + '" d="M90 162 C140 172 170 60 230 50"/><path class="probe k2" d="M40 162 C80 204 180 162 230 138"/>';
    g += '<path d="M230 46 l26 4 l-26 4z" style="fill:#d42a22"/><path class="k" d="M230 134 l26 4 l-26 4z"/>';
    g += T(262, 44, a, { a: 'start', size: 12 }) + T(262, 132, b, { a: 'start', size: 12 });
    g += T(262, 62, 'red lead', { a: 'start', size: 10, style: 'fill:var(--ink2);font-weight:500' }) + T(262, 150, 'black lead', { a: 'start', size: 10, style: 'fill:var(--ink2);font-weight:500' });
    // named on top: a newcomer may not know the instrument by sight
    return flat(s, 360, 208, T(70, 14, 'DIGITAL VOLTAGE METER', { size: 10, style: 'font-weight:800' }) + '<g transform="translate(0 22)">' + g + '</g>');
  };

  /* ---------------- wiring ---------------- */
  /* ---------------- appendix: the controller board, logically ----------------
     Every block and net below is from hardware/design.py. Signal names, not
     GPIO numbers: the ESP32 pin map is redrawn for the 30-pin module. */
  
})();

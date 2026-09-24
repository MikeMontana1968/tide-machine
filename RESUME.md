# Tide Machine — resume point

**Rev L, 2026-09-24.** Five-constituent harmonic tide predictor. Six carriages in one
row on two identical rails: five crank stations, each direct-driven by its own
28BYJ-48 behind a sheet-metal faceplate, plus the pen as the sixth. One monofilament line
sums them onto a pen writing on a length of PVC pipe.

`tide_machine.rb` is the source of truth — its `CFG` block holds every dimension.
Run it in SketchUp: `load "C:/Users/mikem/Desktop/tide-machine/tide_machine.rb"`

3D viewer: https://claude.ai/artifact/PPe79PuxmdfM8Lc8Z9E5iv
Companions: Marigram Sandbox (interactive harmonic model), `Desktop\tide-harmonics.xlsx`.
Superseded sheets: General Arrangement (geared), Exploded Assembly (concentric rings).

---

## What it does

`h(t) = Σ Hᵢ · cos(σᵢt − gᵢ)` over five constituents, realised mechanically:
crank radius = amplitude, crank angle = phase, Kelvin cable = the summation.

| | r pin | disc r | slot used | crank load | margin |
|---|---|---|---|---|---|
| M2 | 35.00 | 47.0 | 73.0 | 14.0 mN·m | 2.4× |
| S2 | 8.75 | 20.8 | 20.5 | 3.5 | 9.8× |
| N2 | 7.35 | 19.4 | 17.7 | 2.9 | 11.7× |
| K1 | 3.50 | 15.5 | 10.0 | 1.4 | 24.5× |
| O1 | 2.45 | 14.5 | 7.9 | 1.0 | 35.0× |

Accuracy: **12.4% of mean range, worst case, over a 60-day run** (5.1% RMS) against
the full 15-constituent model. Target was 20%.

**Travel chain.** Σr = 57.05 mm. Each moving ring doubles its carriage's displacement,
so the cable end swings ±2Σr = ±114 mm. The cable then wraps a ring on the pen carriage
and anchors to the rail, halving it again: **pen travel = 2Σr = 114 mm**, and the chart
scale comes out as exactly `pin_scale` — **35 mm per metre of tide** (102 mm for a
spring range, 53 mm for a neap).

That last 2:1 is what makes the machine fit. The rails are 140 mm apart and a 16 mm
carriage leaves ~124 mm of stroke; without it the pen would want 228 mm and the drum
would tower over the frame.

---

## Envelope

| | |
|---|---|
| Frame | **1×2 pine** (19.05 × 38.1 actual), two rails 470 mm + two end posts |
| Faceplate | **sheet metal, 321 × 164 × 1.5 mm** |
| Overall depth | ~60 mm (motors +26 behind the plate, rail front at −34) |
| Guide rods | **7**, all 158 mm, shared between neighbouring carriages |
| Carriages | M2 96 × 15.6 × 12 · four at 42 × 15.6 × 12 · pen 42 × 16 × 12 |
| Drum | 3" Sch 40 PVC, OD 88.9, 130 mm long |
| Motors | 6 × 28BYJ-48, bolted **flat** to the sheet (no standoff) |
| Home sensors | 5 photointerrupters, 12 o'clock, front of the plate |

---

## Configuration

**Scale.** `pin_scale = 35`. Everything follows: pen travel = 3.26 × pin_scale, peak M2
torque = 2 × tension × pin_scale. Those two fight; 35 balances them.

**Faceplate.** Sheet metal, **1.5 mm**. Drawings and the hole schedule are in *Faceplate drawings* below. Thickness is a *shaft* decision, not a
stiffness one. A 28BYJ-48 gives 9.5 mm past its mounting face but the first 1.5 mm is a
9 mm boss, so only **8.0 mm is 5 mm shaft**. A 1.5 mm plate buries the boss exactly: it
sits inside the clearance hole and the shaft emerges at the plate's front face with all
8.0 mm forward of it. Every millimetre of extra plate costs a millimetre of shaft.

Grip is 8.0 mm of 8.0 available, from boring the disc **through** (6 mm) plus a 3 mm hub
reaching rearward to the plate face. Strength was never the issue — 14 mN·m on two
flats over 8 mm is 0.12 MPa — and neither is axial retention, since the yoke slot loads
the pin only along Y. A grub screw on a flat is ample.

Clearance hole 10.0 mm (boss + 0.5), two M3 per motor, motor bolted **flat**. If you go
thinner than 1.5 the boss stands proud and the hub grows a counterbore automatically
(`boss_proud`). 1.5 mm aluminium is ~2.9× stiffer in bending than the 3 mm acrylic it
replaces, drills without cracking, and gives the motors a ground plane. What it costs is
the translucency.

**Frame.** **1×2 pine**, 19.05 × 38.1 actual — two rails 470 mm long plus two end
posts between them to close the box. **1×1 is too shallow:** the rail has to span from
the faceplate at z=0 forward to the cable rings at z=−30, with the rod sockets at
−20 in between, and the rings *must* sit forward of the rods or the cable fouls them.
That needs 30 + 4 = **34 mm of depth**. A 25.4 mm section leaves 2.8 mm of wood ahead
of the rod socket and puts the ring 4.6 mm off the front face entirely. 1×2 gives
15.5 mm ahead of the socket and 8.1 mm ahead of the ring.

**No lip — the faceplate screws to the rails' rear faces**, overlapping them by 12 mm,
which is a comfortable landing for a #6 wood screw. Pilot 2 mm into the pine, 3.5 mm
through the sheet; the console prints the pattern. Pilot holes aren't modelled — you
drill them on assembly.

Seven **blind** 5.2 mm rod sockets, 9 mm deep into the 19 mm thickness, leaving 10.1 mm
behind them. Rod spacing and parallelism now come from **one careful drilling session**
rather than from a print. If you pair them, clamp **outer face to outer face** with the
rear edges and ends flush and drill each position from both sides — see *Rail
drawings* below for why that comes out correctly handed, and why clamping the inner
faces together cannot work.

The twelve cable rings become **screw eyes** — the right part for wood, and far better
than drilling 1.4 mm through 19 mm of pine. The carriages keep their drilled holes and
hand-made rings; those are still PLA. The drum shaft runs in a 7 mm hole through the
wood: passable at one revolution a week, but a brass bushing or a scrap of PTFE tube
costs nothing and won't wear oval.

**Guide rods.** 5 mm, **seven**, each shared by the two carriages it sits between — the
locating groove for the one on its right, the floating groove for the one on its left.
158 mm, socket-bottom to socket-bottom. Cut a whisker under; forcing them home splits
the socket walls along the layer lines. Sewing-machine oil: mineral oil is inert to PLA
and takes μ from ~0.25 dry to 0.1, dropping total guide drag from ~0.22 N to ~0.09 N.

**Carriages.** Two classes: 96 mm for M2, 42 mm shared by the other four. 15.6 mm tall,
12 mm thick — webs are 1× slot height above and below. Left groove locates (0.1 mm fit),
right groove floats (0.8 mm), so rod skew is absorbed rather than binding. 2.6 mm drill
dimples on both faces; drill 1.4 mm by hand for the ring.

**Print upright**, on the 96 × 12 footprint, so the end grooves run vertically and come
off as clean bearing surfaces — the only surfaces here that matter. The slot's top wall
then bridges its full length, so turn on support inside the slot; it's a through-window
open at both ends, so it lifts straight out.

**Home sensing.** One photointerrupter per crank — five; the drum doesn't need one
since you tape the paper on by hand anyway. The reason isn't homing (you could index by
hand) but **silent-skip detection**: a flag passing a sensor gives a predicted step count
at a known angle, 116 times over a 60-day run on M2, 466 across all five. Open-loop
steppers otherwise drift with nothing to tell you.

The flag is a **recess, not a tab.** The rims are close — 3.25 mm between M2 and S2,
3.90 between S2 and N2 — and anything protruding sweeps a full circle into its
neighbour. So the disc body stops 3 mm short of its OD and that last ring of rim prints
at **2 mm instead of 6**, with a **12° notch**. Nothing sticks out; the sensor's 3 mm
slot straddles the 2 mm band. Prints with no support: disc flat on the bed, so the
thinned rim is a step down in layer height and the notch is a vertical-walled gap. Band
goes on the **rear** face, leaving the front clear for the arm and pin.

**The notch is centred on the pin**, so the flag-to-pin angle is exact by construction.
Time the edge the band presents entering the beam, always approaching in the running
direction — the machine only turns one way, so sensor hysteresis and gearbox backlash
both land as one constant offset. Resolution is a non-issue: 0.3 mm edge detection at
40 mm radius is 0.43°, which on M2 is 53 seconds of tide phase.

**Sensors at 12 o'clock**, all five identical. The sides are congested (neighbouring
discs at 3 and 9, guide rods just beyond) but there's 23 mm clear above even M2's rim
and 50 mm above the small ones. Bracket occupies z 0…−7 while the carriages live at
−26…−14, so they pass in front wherever they are in their stroke. Slot the bracket's
mounting holes radially and one design serves all five radii.

**Homing can't crash the pen.** Pen position is Σdᵢ, bounded by Σr = 57.05 mm by
construction, against 62.00 mm of available travel. No combination of disc angles can
drive it into a stop, so homing needs no sequencing and no soft limits.

**Crank pins.** 5 mm in a 5.2 mm slot. The slot height *is* the kinematic fit; any
clearance in it is pure backlash reversing twice per revolution. Same stock as the rods.

**Drive.** 28BYJ-48 direct, coaxial behind the plate, no reduction anywhere. ULN2003
boards. **PWM hold** on the common 5 V rail via one N-channel MOSFET and one ESP32
channel: idle at 60% duty (20.6 mN·m, 1.38 W for all six), snap to 100% for the ~30 ms
of a step. ESP32 + 2 × MCP23017 (24 stepper lines + 6 home sensors on 2 GPIO). NTP daily.

**Line.** ~0.3 mm **fluorocarbon** monofilament. At 0.20 N that's ~1% of breaking
strength, so creep over sixty days is sub-millimetre and elastic stretch is a constant
offset absorbed in the pen zero. Nylon is the same price and wrong — it absorbs moisture
and wanders with humidity. Crimp sleeves, not knots.

**Pen.** The **sixth carriage in the row**, closed up against O1 with the same 2 mm gap
and sharing rod 5 with it — so only one extra rod is needed. 42 × 16 × 12, same grooves,
a drilled ring for the cable, a 25 mm arm out to the drum. Return force is a **dead
weight, not a spring**: ballast pocket inside the body, part-filled with lead shot and
capped with epoxy to **41 g all-up**. A slug hung below would reach −80 mm and foul the
bottom rail at full travel. Springs are wrong here because their force varies over the
stroke, which would vary cable tension and therefore every crank torque.

**The pen's zero is set by cable length and nothing else** — hence the screw-adjustable
anchor at the dead end. It is the physical form of Z0 from the spreadsheet, and the one
alignment in this machine that genuinely has to be made.

**Drum.** A 130 mm length of **3" Schedule 40 PVC** (OD 88.9, bore 77.9). *Not* a
printed part — the tube is within a millimetre of what the drum wanted. Print only the
two **end caps**: each plugs the bore, carries the 7 mm shaft and trues up the cut end.
~30 g of PLA against ~250 g for a printed drum that would be rounder only by luck.

The shaft passes through a hole in *both* rails — clearance through the top on its way
to the motor above, a plain bearing in the bottom. No extra bracket. The tube weighs
~260 g, which is nothing to the motor (~4 mN·m total against 34.3) but a real thrust
load: **washer under the bottom cap**. Cut the tube square; a wobbling drum moves the
pen in and out and modulates its contact force.

**Chart speed — still open.** Circumference 279.3 mm.

| rev period | per tidal cycle | sheets over 60 days |
|---|---|---|
| 7 days | 20.6 mm | 9 |
| 5 days | 28.9 mm | 12 |
| 3.5 days | 41.3 mm | 17 |

At 7 days the trace is very steep — 20.6 mm wide per cycle against up to 102 mm of
vertical swing. 3.5 days gives a far more classical marigram. It's a firmware constant,
so try both. Paper: A4 wrapped the long way leaves 17.7 mm of overlap to tape; trim the
210 mm dimension to about 140.

Pen contact force is separate, acts in Z, ~0.05 N from a light leaf spring. Add a manual
lever to retract the nib for sheet changes.

---

## Files

Everything lives in `C:\Users\mikem\Desktop\tide-machine\`.

| File | What |
|---|---|
| `tide_machine.rb` | **the source of truth for every dimension.** `load` it in SketchUp |
| `tide-machine-3d.html` | the Three.js viewer — a parallel implementation, published as an Artifact |
| `faceplate.py` | emits the faceplate DXF + PDFs, parsing `CFG` out of the Ruby |
| `rails.py` | emits the rail templates the same way |
| `RESUME.md` | this file |

The viewer used to live in a session scratchpad, which was a bad place for a
project deliverable; it is now in the project folder with everything else.

**Rev L** put the drawings' holes into the model. The faceplate had been a bare slab;
it now carries all 35 holes as real subtracted geometry from the same arithmetic that
writes the DXF, and the rails gained the five rear-face pilots each so you can see them
line up under the frame screws with the explode slider. Two housekeeping fixes came out
of reading the published page: `M.teeth` was referenced for every disc's flag band but
never defined, so the band was falling back to THREE's default white material; and two
footer notes still asserted printed rails with an acrylic lip and a 3 mm acrylic plate
in present tense, contradicting newer notes in the same list. Those are marked
superseded rather than deleted — the footer is a design log.

---

## Faceplate drawings

Four files, all regenerated by `faceplate.py`, which **parses `CFG` out of
`tide_machine.rb`** rather than restating any dimension. Change the model and re-run;
the drawings cannot drift from it.

| File | For | Contents |
|---|---|---|
| `faceplate_CUT.dxf` | **SendCutSend** | outline + 35 holes, nothing else |
| `faceplate_REF.dxf` | your CAD | same geometry + text and centre marks on separate layers |
| `faceplate_1to1_A3.pdf` | print shop | 1:1 on A3 landscape, dimensioned, + hole schedule |
| `faceplate_1to1_tiled.pdf` | your printer | 1:1 on two Letter tiles, 30 mm overlap |

**The labels are deliberately not in the cut file.** A laser house treats every closed
path in the DXF as something to cut, so a text label in the uploaded file is at best an
order that gets kicked back and at worst a part with the word "M2" cut through it. So
`faceplate_CUT.dxf` carries one closed outline and 35 circles — verified with `ezdxf`:
R12, `$INSUNITS = 4` (mm), nothing crossing the outline, no two holes closer than
1.5 mm. That is the file to upload. Everything you actually want at the bench lives in
`faceplate_REF.dxf` (layers `REF_TEXT` and `REF_MARKS`, toggle them off and it is the
cut file) and in the PDFs. If you ever *do* want marks on the metal, that is an
engraving line item quoted separately from a file that says so — not something to
smuggle into the cut geometry.

**Hole pattern.** 321 × 164 × 1.5 mm, origin on the M2 shaft, `y = 0` the crank
centreline shared by all five stations.

| Count | Ø | Where | Why |
|---|---|---|---|
| 5 | 10.0 | station x, y = 0 | clears the motor's 9 mm boss (`boss_d + 0.5`) |
| 10 | 3.2 | station x ± 17.5, y = 0 | 28BYJ-48 mounting, 35 mm PCD |
| 10 | 3.2 | station x ± 4.5, y = disc_r + 3 | home-sensor bracket |
| 10 | 4.0 | x per `screw_xs`, y = ±76 | #6 clearance into the pine rails |

Station x — M2 −88, S2 −17, N2 +27, K1 +71, O1 +115. Frame screws at
x = −144, −69.75, +4.50, +78.75, +153 (74.25 pitch, five a rail).
Sensor-bracket y — M2 50.0, S2 23.75, N2 22.35, K1 18.5, O1 17.45.

Against 1.5 mm stock: smallest hole 3.2 mm and thinnest hole-to-edge wall 4.0 mm, both
comfortably over the usual "≥ material thickness" laser rule. No guide-rod or
drum-shaft holes — the rods sit at z − 20 behind the plate and the drum is at
x 249.5, past the plate's +165 edge.

**The plate is not symmetric, so a mirrored one is scrap.** The stations sit 68 mm from
the left edge and 50 mm from the right, and the sensor holes are all on +y. Both PDFs
carry `M2 / LEFT END`, `PEN + DRUM END →` and `FRONT FACE UP` for that reason. Check
the 100 mm calibration bar on any sheet before marking metal — "shrink to printable
area" is the default on most drivers and it silently destroys 1:1.

---

## Rail drawings

Three files from `rails.py`, which parses `CFG` out of `tide_machine.rb` the same way
`faceplate.py` does.

| File | For | Contents |
|---|---|---|
| `rails_1to1_A2.pdf` | print shop | every face at 1:1 on one A2 sheet, + drill schedule, cut list, ordinates |
| `rails_1to1_tiled.pdf` | your printer | cover + 3 Letter tiles, 30 mm overlap, all three faces per tile |
| `rails_REF.dxf` | your CAD | each face on its own layer (`TOP_INNER`, `BOT_INNER`, `REAR_FACE`, `POST`) |

**There is no vendor cut file here, and that is the point.** The rails are pine you cut
yourself, so these are **drilling templates**: tape a sheet to the wood, centre-punch
every cross, drill. The DXF is for your own CAD or a router, not for a laser house.

**The two rails are mirror images.** Both carry identical features at identical machine
(x, z), but each is drilled on its **inner** face — the one that looks at the other
rail. Laying the top rail inner-face-up turns it over, so with the rear edge toward you
on both, machine x runs left-to-right on one and right-to-left on the other. Drill both
from one template and the second rail is scrap. Hence a separately named sheet per rail,
each stating which way x runs.

There *is* a clamping trick that gets the hand right for free, and it is the accurate
version of "drill them as a pair": clamp them **outer face to outer face**, rear edges
flush and ends flush, then drill each rod position from both sides of the stack to 9 mm.
Both inner faces end up with the same (u from the end, w from the rear edge) — and
because seating each rail means rotating it about its *transverse* axis, the same
physical end lands at opposite ends of the machine. Clamping them inner-face-to-inner-face
does not work: those are the faces you need to drill.

**Drill schedule**, all ordinates in machine x, `v` measured from the rear edge:

| Count | Ø | Depth | v | Where |
|---|---|---|---|---|
| 7 | 5.2 | 9, blind | 20 | rod sockets: x −137, −39, +5, +49, +93, +137, +181 |
| 12 | 2.0 | 9 | 30 | screw-eye pilots: each station ±6 mm |
| 1 | 7.0 | through 19.05 | 20 | drum shaft at x +249.5, both rails |
| 5 | 2.0 | ~10 | — | faceplate pilots, **rear** face, 6 mm in from the inner edge |

The screw-eye pilots leave only **8.1 mm** of wood to the front edge — drill them
square or pine will blow out. Closest two centres anywhere on the inner face are 12 mm
apart, so nothing crowds anything.

**Cut list:** 2 rails 470 mm, 2 posts 140 mm, both from 1×2 pine (1220 mm of stock,
so one 8 ft length); 7 rods Ø5 × 158 mm. Post joinery is deliberately not drawn
— fit the rails and rods dry, get it square, then fasten the posts to whatever you
have.

---

## Decisions worth not relitigating

1. **Not cycloids.** Tides are a sum of sinusoids. A pin at radius r on a disc turning
   at the constituent's rate gives `r·cos θ` free. Lobes are only legitimate for M4/M6,
   which are true harmonics of M2.
2. **Scotch yoke, never a connecting rod.** Con-rod obliquity error lands at exactly 2×
   the crank frequency — it fabricates a false M4 around 5% of M2. The #1 gotcha.
3. **Direct drive beats gearing** once you PWM the hold. Torque scales with current,
   heat with current squared, so topping up the gearbox is nearly free.
4. **The line passes *around* each carriage, never attaches.** The 180° wrap is what
   turns displacement d into 2d of take-up; tying it would rigidly couple all six.
5. **Sliding rings cost capstan friction a roller wouldn't** (1.87× per station at
   μ 0.2). Accepted deliberately in favour of hand-fabrication. If the pen ever feels
   notchy or direction-dependent, that's where it's coming from.
6. **Backlash in the drive is nearly free** — every shaft turns one direction
   continuously, so it becomes a fixed phase offset absorbed in firmware. Only the
   yokes reverse.
7. **Yoke convention:** horizontal slot, vertical travel, so each station contributes
   `r·sin θ`, not `r·cos θ`. A 90° offset folded into every phase constant. Don't
   forget it.
8. **Both cable legs must be parallel to the carriage's travel.** A moving ring gives
   exactly 2d of take-up only when its legs leave it along the slide direction; splayed
   at angle α it gives 2d·cosα, and α changes as the carriage moves, so the gain isn't
   even constant. One rail ring *between* stations swung M2's gain from 0.78 to 1.77.
   Two rings per station, straddling it by 6 mm, gets residual error to 0.58% of trace.
9. **Layout between stations is therefore free.** Everything between moving rings runs
   fixed point to fixed point, and that distance never changes — so the cable can take
   any path at all between stations and contribute nothing to the sum. Station order,
   spacing, position and even slide direction are unconstrained. Only the local geometry
   at each moving ring matters. The row is a packaging choice, not a functional one.
10. **The viewer and the builder are parallel implementations.** Every visual check in
    this project has been of the Three.js viewer, which has its own geometry code. Three
    placement bugs lived in the Ruby for many revisions because of it: `disc_z()`
    translated by z1 instead of z0 (every solid of revolution a full thickness rearward,
    putting the crank disc and pin *inside* the faceplate), the hub sat forward of the
    disc so it never reached the shaft, and a 4 mm motor standoff ate the shaft length
    the hub needed. **Run the Ruby before trusting a dimension.**
11. **The pen must swing further than any crank** — it carries the sum, so its range is
   Σr = 57.05 against M2's 35.00, a ratio of ΣA/A_M2 = 1.630. That mismatch *is* the
   summation. Over a real 60-day run it reaches +56.6 / −53.5 mm, so the theoretical
   bound is barely conservative.

---

## Open items

- [ ] **Measure the 28BYJ-48's holding torque** at the output shaft, powered and
      unpowered (string, known-radius pulley, add weight until it creeps). The only
      number still resting on a datasheet; it sets how far `hold_duty` can drop.
- [ ] **Replace the placeholder constituents.** Amplitudes and phases throughout are
      illustrative of a semidiurnal coast, not a surveyed station. Pull real ones from
      NOAA CO-OPS for the chosen port — they set every pin radius and every disc.
- [ ] **Decide chart speed** (7 vs 3.5 days per revolution) before committing to paper.
- [ ] Firmware: rates, phase constants (with the sin/cos offset), NTP, PWM hold, homing.
- [ ] Firmware needs three commissioning commands: **go-to-angle** (for verifying pin
      radius — command θ=90°, measure the carriage rise, it should equal r),
      **go-to-zero** (all θ=0 so Σd=0, for setting the pen datum at the anchor screw),
      and a **speedup multiplier**. 1000× is the sweet spot: 92 steps/s on M2, 9% of the
      28BYJ-48's ~15 rpm ceiling, replays the whole 60-day run in 86 minutes and a
      spring/neap envelope in 21. Don't exceed 5000× (45% of max, torque falling off);
      a skip during fast-forward loses the phase reference, so re-home after.
- [ ] Commissioning order: mechanical → set the three slotted pin radii and verify each
      by go-to-angle → direction-check every motor at 1000× (a reversed motor is
      invisible at real speed) → home → pen zero at go-to-zero → 90-minute soak at
      1000× against the sandbox → NTP, re-home, start.
- [ ] Electronics tray placement behind the plate.
- [ ] Run Solid Tools before STL export if watertight solids are wanted; parts are
      modelled as interpenetrating solids inside each group.

---

## If the ULN2003 drop bites

The Darlington eats ~1 V of the 5 V rail — 20% of driving torque. If steps look marginal
at M2, swap to logic-level MOSFETs for a free ~22% before touching anything else.
Beyond that: bipolar conversion (cut the centre-tap trace) for ~1.4×, then a chopper
driver to set current against a thermal budget you choose.

# Tide Machine — resume point

**Rev M, in progress — 2026-09-26.** Five-constituent harmonic tide predictor. Five arm
stations in one row, each direct-driven by its own 28BYJ-48 behind a sheet-metal faceplate.
One monofilament line runs along the top rail over a coaxial pair of V-groove pulleys above
each station, drops to a V-groove bearing on the station's arm, U-turns, and climbs back.
The sum of the five reaches a pen carriage writing on a length of PVC pipe.

> **⚠ The Rev L shop files are stale — do not order or drill from them.** `tide_machine.rb`,
> `faceplate.py` (and `faceplate_CUT.dxf`), `rails.py` and the 3D viewer all still describe
> Rev L: discs, yokes, carriages, screw eyes, the wrong motor offset and the old station x.
> Until they are ported, the Rev M geometry lives in `station_study.py` + `rollers.py`, and
> this file is the spec. See *Files* and *Open items*.

Rev M fit study: https://claude.ai/artifact/RWW9Uh7phZAQicc9Ytd4kd
Marigram Sandbox (harmonics + arm-station kinematics and friction): https://claude.ai/artifact/GJ3wLqHhHAh9vqQBS5SoKS
Rev L 3D viewer (stale): https://claude.ai/artifact/PPe79PuxmdfM8Lc8Z9E5iv
Companion: `Desktop\tide-harmonics.xlsx`.

---

## What it does

`h(t) = Σ Hᵢ · cos(σᵢt − gᵢ)` over five constituents, realised mechanically:
pin radius = amplitude, arm angle = phase, one Kelvin line = the summation.

Rev M, `pin_scale` 35 mm/m, **a V623ZZ at every bend**: rail pulleys, arm bearings, pen
pulley. Order S2 · N2 · K1 · O1 · M2 · pen:

| | pin r | crank load, frictionless | with friction | margin vs pull-in 29.4 |
|---|---|---|---|---|
| M2 | 35.00 | 14.1 mN·m | **14.5** | 2.0× |
| S2 | 8.75 | 3.5 | 4.1 | 7.1× |
| N2 | 7.35 | 3.0 | 3.4 | 8.7× |
| K1 | 3.50 | 1.4 | 1.6 | 19× |
| O1 | 2.45 | 1.0 | 1.1 | 28× |

Friction is now a rounding error. For the record, the superseded PLA sleeve on an Ø8 pin needed oil on every pin:
dry, S2 reached 30.6 mN·m, the motor's pull-in torque. No lubrication is needed now. Lowest line
tension anywhere: 170 mN of 201, so the line can't go slack.

Accuracy: **12.4% of mean range, worst case, over a 60-day run** (5.1% RMS) against the
full 15-constituent model. That's exactly what a perfect five-constituent machine gives, because the
firmware inverse removes the arm's own geometric error. Target was 20%. Turned at constant
speed, the same arms would score 17.6%.

**Travel chain.** Σr = 57.05 mm. Each station's arm bearing takes up twice its own rise, so the
line end swings ±2Σr = ±114 mm. The line then wraps a pulley on the pen carriage and
anchors, halving it again: **pen travel = 2Σr = 114 mm**, and the chart scale comes out as
exactly `pin_scale`, **35 mm per metre of tide** (102 mm for a spring range, 53 for a neap).
That last 2:1 is what makes it fit between rails 140 mm apart.

---

## Envelope

| | |
|---|---|
| Frame | **1×2 pine** (19.05 × 38.1 actual), two rails + two end posts; rail length to be reset for the shorter row |
| Faceplate | **1.5 mm aluminium, ~285 × 164** (exact outline set in the port) |
| Depth | motors 20.5 behind the plate; in front: arm-bearing groove −22.8, pulley brackets to −30.6, rail front −38.1 |
| Stations | 5 × two-part printed rotor (hub + flag disc, bolt-on arm) + a V623ZZ on an M3 axle |
| Bearings | **18 × V623ZZ**: 12 on the top rail (two per bracket, six brackets), 5 on the arms, 1 on the pen carriage |
| Guide rods | **2**, pen carriage only |
| Carriages | pen only |
| Drum | 3" Sch 40 PVC, OD 88.9, 130 mm long |
| Motors | 6 × 28BYJ-48 (five stations + drum), bolted flat, wire covers down |
| Home sensors | 5 × **Vishay TCST2202**, flat on the plate at 12 o'clock |

---

## Configuration

**Station order and spacing.** S2 · N2 · K1 · O1 · M2 · pen, at x −224, −168, −112, −56, 0,
+70, with **equal 56 mm pitch** between the five stations (user's call). At 56 mm, M2's arm (reach 40.5) clears
O1's arm boss (r 12) by 3.5, the tightest gap in that plane. **M2 sits next to the pen**, where its torque is lowest (14.5, against 16.4 at the far end). With a
bearing at every bend the order hardly matters any more. O1 goes beside M2 because it has the smallest sweep.

**Motor (28BYJ-48; Kiatronics / OSEPP STEPD-01 datasheet).** The **shaft sits 8 mm off the body
centre**, on the perpendicular to the ear line; the ear holes are on the body centreline.
Ear holes 2 × Ø4.2 on 35 centres, tabs R3.5, 42 tip to tip. Body Ø28 × 19; wire cover
14.6 wide on the side away from the shaft, reaching 25 mm from the shaft. Boss Ø9 × 1.5.
Shaft Ø5, 3 across flats, **10 ±0.5 from the mounting face, flats only 6 long**.
**Orientation (confirmed): shaft above the body centre, wire covers down.** At 56 mm pitch the
ears leave 14 mm between neighbours. The plate's **Ø9.2 boss hole** locates each shaft. The
ear bolts only clamp: M3 in a Ø4.2 ear hole would let the motor wander ±0.6 mm.
Torque: pull-in **29.4 mN·m** (300 gf·cm), in-traction and self-positioning > 34.3. **Friction torque
59–118 mN·m**: if that means unpowered back-drive torque, the PWM hold could drop to
zero; the bench test decides.

**Faceplate.** 1.5 mm aluminium; the thickness is a *shaft* decision. The 1.5 mm boss sits
inside the plate, so 8.5 mm of shaft stands forward of the front face, the last 6 of it flatted.
Rev M hole schedule, per station at shaft (x, 0):

| Count | Size | Where | Why |
|---|---|---|---|
| 5 | Ø9.2 | (x, 0) | locates the Ø9 boss |
| 10 | Ø3.2 | (x ± 17.5, −8) | motor ears, M3 |
| 10 | Ø3.2 | (x, 11) and (x, 30) | TCST2202 flanges, M3 |
| 5 | 6 × 12 window | centred (x, 20.5) | sensor leads through the plate |
| — | Ø4.0 | y = ±76, spacing to be set | #6 frame screws into the rails' rear faces |

Still true from Rev L: the plate is **not symmetric** (a mirrored plate is scrap). Keep labels
out of the cut DXF. Check the 100 mm calibration bar before marking metal.

**Rotor: two printed parts per station.**
- **Hub + flag disc.** Hub Ø14, D-bore on the shaft over its full 8.5 mm, with an M3 grub screw
  on the flat. Flag disc r 22.6 × 2 mm, whose back face stands 1 mm off the sensor. On its back, a
  **flag fin** 1.2 mm thick (radial) × 20° at r 20.5, reaching 1.7 mm past the beam. On its front,
  a 1 mm × Ø24 **boss** the arm bolts to, so M2's arm passes 1 mm clear over O1's disc. Prints
  disc-down, with the hub and fin growing up.
- **Arm.** 3 mm arm on 2 × M2 into the boss, end lobe r 5.5. In front at radius r, a **stepped
  boss**, Ø8 × 1.0 then Ø5 × 0.5, so only the bearing's inner race touches it. An **M3 × 4 heat-set
  insert** goes in flush from the back face; a nut there would stand proud into the 1 mm gap over
  the neighbour's disc. Prints flat, boss up. **When real constituents arrive, only the arms get reprinted.**
- **Arm bearing.** The **same V623ZZ** as the rail pulleys, on an **M3×8** + washer into the insert,
  with the inner race clamped. The axle tip stops 1 mm short of the arm's back face. This supersedes the thick-printed-pin
  + PLA-sleeve design (user's call, 2026-09-26), which needed oil and let S2 reach pull-in when dry.

**Kinematics: firmware inverse.** An arm moves its pin sideways too. Turned at constant speed that
makes a false M4 (7.8% on its own), so **each arm is driven at an uneven rate from a per-station
lookup table** that makes the line length exactly sinusoidal. M2's speed peaks at 1.24× mean. The
table is built from the exact line geometry: pulley root radius, legs at ±4.8, plane offsets.
The arm bearing and the rail pulleys are the same part, so the legs hang exactly vertical at mid-stroke
whatever the real groove radius turns out to be, and every pin radius is exactly `pin_scale × amp`. A 1 mm geometry error costs about 0.1 mm at the pen.

**Pulleys and threading** (`rollers.py`). One bracket per station, **directly above the
shaft**, on the top rail's inner face: two V623ZZ on one M3×20 + nyloc, a **3 × 5 × 0.5 shim**
between them (inner races only; an M3 washer rubs the shields), 0.5 mm printed bosses on the
cheeks. Pulley axle at y 59.2 (root r 4.8, so the line runs along the tops at y 64). Planes
**−20.55 (rear) and −25.05 (front)**, either side of the arm-bearing groove at −22.8. The bracket is
30 × 15.5, fixed with 2 × #4 either side of the clevis, and neighbouring brackets are 26 mm apart.

Per station: over the IN pulley (90° wrap), down the +x side, U-turn under the arm's bearing, up
the −x side, over the OUT pulley (90°). **The order is mirrored at alternate stations**, so every run
between stations stays in one plane:

| row | S2 | N2 | K1 | O1 | M2 | pen |
|---|---|---|---|---|---|---|
| in over | front | rear | front | rear | front | rear |
| out over | rear | front | rear | front | rear | front = **anchor** |

Leg fleet angle: 2.3–2.6° on the small stations, 5.4° on M2 only at the top of its stroke.
Nothing slides at S2's IN pulley, so the far dead end can tie off right there.

**Home sensing.** One sensor per station: five. The drum doesn't need one. The reason is **silent-skip
detection**, not homing: each flag pass gives a predicted step count at a known angle, 116
times over 60 days on M2 and 466 across all five. Open-loop steppers otherwise drift with nothing
to tell you.
- **Vishay TCST2202** (doc 81147): slotted optical switch, 3.1 slot, 0.5 aperture, 24.5 × 6.3
  × 10.8, beam 8.2 above the seat, flanges Ø3.3 on 19 centres. **The leads leave through the
  seating face.**
- **Flat on the faceplate at 12 o'clock**, on a 1.5 mm printed insulating pad, with the leads through a
  6 × 12 window. At 6 o'clock the leads would run into the motor's wire cover. The line
  runs in front of the arm, so it never reaches the sensor.
- The fin crosses the beam once per turn. The 10–90% transition is 0.4 mm of shutter travel,
  about 1.1° at r 20.5; the switching edge repeats far better than that. Time the edge
  **entering** the beam in the running direction; the machine turns one way only, so
  hysteresis and gearbox backlash become one constant offset in the table.
- Electrical: LED through **180 Ω** from 5 V (about 20 mA each, 100 mA for five). Output with a
  **10 kΩ pull-up to 3.3 V** into the MCP23017.

**Depth stack** (z, mm in front of the plate's front face = negative):

| | z |
|---|---|
| sensor seat (pad front) | −1.5 |
| slot floor / fin tip / beam | −5.1 / −8.0 / −9.7 |
| shaft tip | −8.5 |
| sensor top | −12.3 |
| flag disc | −13.3 to −15.3 |
| arm | −16.3 to −19.3 |
| arm boss (Ø8 / Ø5) | −19.3 to −20.8 |
| rear pulley plane | −20.55 |
| **arm-bearing groove** | **−22.8** (bearing −20.8 to −24.8) |
| front pulley plane | −25.05 |
| arm axle head | −26.95 |
| pulley bracket | −14.05 to −30.55 |

All 15 clearances in the fit study are ≥ 0.95 mm. The tightest is the fin to each slot wall (0.95).

**Homing can't crash the pen.** Pen position is Σdᵢ, bounded by Σr = 57.05 mm, against
62 mm of available travel. No combination of arm angles can reach a stop.

**Drive.** 28BYJ-48 direct, no reduction. ULN2003 boards. **PWM hold** on the common 5 V
rail via one N-channel MOSFET and one ESP32 channel: idle at 60% duty (20.6 mN·m, 1.38 W for
all six), snapping to 100% for the ~30 ms of a step. ESP32 + 2 × MCP23017: 24 stepper lines + 5
home sensors on 2 GPIO. NTP daily.

**Line.** ~0.3 mm **fluorocarbon** monofilament. At 0.20 N it's ~1% of breaking strength:
sub-millimetre creep over sixty days, and elastic stretch is a constant absorbed in the pen
zero. Not nylon: it absorbs moisture and wanders with humidity. Crimp sleeves, not knots.

**Pen — needs its Rev M redesign.** Still: a carriage on **two** rods, return force a **dead weight,
not a spring**, 41 g all-up (0.20 N line tension through the 2:1), a 25 mm arm to the drum, and
contact force ~0.05 N from a light leaf spring with a retract lever. What changes: it
sits at x +70 on its own two rods (no longer sharing a rod with O1). Its moving pulley must run in
the **arm-bearing plane (−22.8)** under the sixth bracket, on its own V623ZZ, and the line's dead end, the
**screw-adjustable anchor**, takes that bracket's front plane. **The pen's zero is set by line
length and nothing else**: the anchor is the physical form of Z0 from the spreadsheet.

**Drum.** 130 mm of **3" Sch 40 PVC** (OD 88.9) with two printed end caps carrying the 7 mm
shaft, through both rails (clearance at the top, plain bearing at the bottom), washer under the bottom
cap. Cut it square. Its x position moves with the shorter row.

**Chart speed — still open.** Circumference 279.3 mm.

| rev period | per tidal cycle | sheets over 60 days |
|---|---|---|
| 7 days | 20.6 mm | 9 |
| 5 days | 28.9 mm | 12 |
| 3.5 days | 41.3 mm | 17 |

7 days draws a very steep trace; 3.5 days is a more classical marigram. It's a firmware constant.
Paper: A4 wrapped the long way leaves 17.7 mm to tape; trim the 210 side to about 140.

**Frame.** 1×2 pine is still right: the pulley bracket reaches z −30.55 against a 38.1 mm
rail, where 1×1 (25.4) would be too shallow. The faceplate screws to the rails' rear faces with a 12 mm overlap.
Rev M rail features:
- **top rail, inner face:** 2 × #4 pilots per pulley bracket at (station x ± 11,
  22.8 from the rear edge), six brackets; 2 pen-rod sockets
- **bottom rail, inner face:** 2 pen-rod sockets
- **both rails:** the drum shaft hole
- **rear faces:** the faceplate pilots

The Rev L rules for drilling the rails as a mirrored pair (clamp **outer face to outer face**, drill from both
sides) still apply to the rod sockets and the drum hole.

---

## Files

Everything lives in `C:\Users\mikem\Desktop\tide-machine\` (a git repo).

| File | Rev | What |
|---|---|---|
| `RESUME.md` | **M** | this file: the spec until the Ruby is ported |
| `station_study.py` → `station_study.html` | **M** | two-station fit study (O1 + M2): every Rev M part, clearances, depth stack. Published (link above). Writes no STLs |
| `station_study.tmpl.html` | **M** | the viewer template it fills |
| `rollers.py` | **M** | pulley bracket: `build_bracket()`, `to_machine()`, `threading()`. Writes `pulley_bracket.stl` only when run directly |
| `sandbox/index.html` | **M** | the Marigram Sandbox source: harmonics, arm kinematics, firmware inverse, friction |
| `tide_machine.rb` | L | SketchUp builder, **stale**: discs, yokes, carriages, screw eyes, motor without its offset |
| `faceplate.py` + `faceplate_*.dxf/pdf` | L | **stale; do not order `faceplate_CUT.dxf`** |
| `rails.py` + `rails_*.pdf/dxf` | L | **stale**: 7 rod sockets, 12 screw-eye pilots |
| `tide-machine-3d.html` | L | **stale** viewer |

---

## Decisions worth not relitigating

1. **Not cycloids.** Tides are a sum of sinusoids; a pin at radius r gives `r·cos θ` free.
   Lobes are only legitimate for M4/M6, true harmonics of M2.
2. **Firmware inverse, not a Scotch yoke** (Rev M; replaces "never a connecting rod"). Arm
   obliquity is real: at constant speed it fabricates a false M4 (7.8% on its own). With one stepper per
   station, the arm is driven at whatever uneven rate makes the line length exactly sinusoidal.
   **Never run an arm at constant speed**, not even in fast-forward.
3. **Direct drive beats gearing** once you PWM the hold. Torque scales with current, heat
   with current squared.
4. **The line passes *around* each arm's bearing, never attaches.** The U-turn is what turns a
   rise d into 2d of take-up.
5. **Every bend in the line, fixed or moving, is a V623ZZ** (Rev M; replaces "sliding rings
   accepted", and then the PLA sleeve). Capstan friction multiplies from bend to bend down the
   line: Rev L as drawn needed ~1250 mN·m on M2, 36× the motor.
6. **Backlash is nearly free.** Every shaft turns one way, so gearbox backlash is a
   constant in the table. The line always pulls each arm bearing toward its pulleys, so its internal
   clearance never reverses either. Rev M has no reversing joint in the drive.
7. **Phase bookkeeping lives in the firmware table** (Rev M; replaces the yoke's `r·sin θ`
   convention). The table maps constituent phase straight to arm angle, including the flag-to-pin
   angle and the direction of rotation.
8. **Legs no longer need to be exactly parallel** (Rev M). Splay changes the station's gain
   along the stroke, but the firmware inverse absorbs any monotonic geometry. Keep them near
   vertical anyway. With the same bearing on the arm and the rail they hang exactly vertical at mid-stroke.
9. **Layout between stations is free for the kinematics** (only the local geometry at each
   arm bearing matters). With a bearing at every bend, friction barely breaks the symmetry (M2 beside
   the pen is 14.5 mN·m, at the far end 16.4). The equal 56 mm pitch is a packaging choice.
10. **Parallel implementations drift.** Three placement bugs lived in the Rev L Ruby because
    the checks were done in a separate viewer. Right now Rev M exists only in `station_study.py`
    and `rollers.py`; **port it to the Ruby before trusting any shop file.**
11. **The pen must swing further than any crank.** It carries the sum: Σr = 57.05 against
    M2's 35.00. A real 60-day run reaches +56.6 / −53.5 mm.
12. **Mirror the threading at alternate stations** (Rev M). With the same order everywhere, each
    run between stations crosses 4.5 mm of depth, 4.6° off-plane at both ends, for the life of the
    machine. Mirrored, those runs are flat and only the legs skew.
13. **The home sensor lies flat on the plate, under the arm, at 12 o'clock** (Rev M). Its leads
    leave through its seat, so behind-the-plate space decides the angle. Everything
    that moves forward of the arm (the arm bearing, the line) stays clear of it by construction.

---

## Open items

- [ ] **Port Rev M into `tide_machine.rb`** (CFG + builders), then regenerate
      `faceplate.py` / `rails.py` outputs and the 3D viewer from it. **Don't order or drill
      Rev L files meanwhile.**
- [ ] **Measure a V623ZZ's groove root radius** when they arrive (4.8 assumed). It sets the
      pulley axle height and feeds the firmware table. The legs stay parallel whatever it is.
      Order 20: 18 fitted + spares.
- [ ] **Pen carriage, Rev M**: two rods at x +70, a moving V623 in the −22.8 plane, the
      screw-adjustable anchor in the sixth bracket's front plane, the ballast pocket.
- [ ] Drum position and rail length for the shorter row; frame-screw spacing on the new
      plate outline.
- [ ] **Measure the 28BYJ-48's holding torque** at the output shaft, powered and unpowered.
      The datasheet's 59–118 mN·m "friction torque" hints the hold could go to zero.
- [ ] **Replace the placeholder constituents** from NOAA CO-OPS for the chosen port. They set
      every pin radius, and only the arms need reprinting.
- [ ] **Decide chart speed** (7 vs 3.5 days per revolution).
- [ ] Firmware: per-station inverse tables from the exact geometry, rates, TCST2202 edge timing,
      skip detection, NTP, PWM hold.
- [ ] Commissioning commands: **go-to-phase** for one station at a time (command the
      constituent phase to 0°, 90°, 180°, 270°; the pen should move ±r); **go-to-zero** (all outputs 0, for the pen datum at the anchor screw);
      a **speedup multiplier** (1000× replays 60 days in 86 minutes; stay under 5000×; re-home
      after any skip).
- [ ] Commissioning order: mechanical → verify each arm's r by go-to-phase → direction-check
      every motor at 1000× → home → pen zero → 90-minute soak at 1000× against the sandbox →
      NTP, re-home, start.
- [ ] Electronics tray behind the plate: wire covers point down, and the sensor leads exit at
      y 16.7–24.3 above each motor.

---

## If the ULN2003 drop bites

The Darlington eats ~1 V of the 5 V rail, 20% of driving torque. If steps look marginal
at M2, swap to logic-level MOSFETs for a free ~22% before touching anything else.
Beyond that: bipolar conversion (cut the centre-tap trace) for ~1.4×, then a chopper
driver to set current against a thermal budget you choose.

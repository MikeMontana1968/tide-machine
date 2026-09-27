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

Rev M full model (all five stations, pen, drum): https://claude.ai/artifact/4bxYWKxQetEjvAZvUuQHdZ
Rev M fit study (O1 + M2): https://claude.ai/artifact/RWW9Uh7phZAQicc9Ytd4kd
Build pack (bill of materials, wiring diagram, pin map): https://claude.ai/artifact/ANQ2MzGFirzXBYaaWWbxXQ
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
That last 2:1 is what makes it fit between the rails, which are now **152 mm apart** (Rev L: 140).

---

## Envelope

| | |
|---|---|
| Frame | **1×2 pine** (19.05 × 38.1 actual), two rails **152 apart** (inner faces) + two 152 end posts; rails ~492 long |
| Faceplate | **1.5 mm aluminium, ~283 × 176** (12 mm landing on each rail; exact outline set in the port) |
| Depth | motors 20.5 behind the plate; in front: dials at −3.5, arm-bearing groove **−15.0**, pen carriage to −30.3, rail front −38.1 |
| Stations | 5 × two-part printed rotor (hub + Ø52 dial, bolt-on arm) + a V623ZZ on an M3 axle |
| Bearings | **22 × V623ZZ**: 12 on the top rail (two per bracket, six brackets), 5 on the arms, 1 pen pulley, 4 carriage bearings |
| Guide rods | **2 × 3 mm steel × 170** (socket bottom to socket bottom), pen carriage only |
| Carriages | pen only |
| Drum | 3" Sch 40 PVC, OD 88.9, 130 mm long |
| Motors | **6 × 28BYJ-48** (five stations + drum), bolted flat, wire covers down; **1 × BKA30D-R5** (calendar) |
| Home sensors | **7 × Hall latch (DRV5013)** behind the plate, each reading a pair of 5 × 2 N52 magnets through a window |
| Dials | 5 × Ø52 station dials + the calendar (Ø52 year dial, Ø32 moon disc), all carrying printed decals (`decals.py`) |

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
| 10 | Ø3.2 | (x ± 17.5, −8) | motor ears, M3 pan head |
| 5 | window, **to re-size** | centred (x, 20.5) | the Hall latch nests in it. Was 3.4 × 3.4 for a SOT-23; the latch is now the through-hole TO-92 (about 4 × 3 × 1.5), so about 4.4 × 3.4 |
| 10 | Ø2.2 | (x, 15) and (x, 26) | Hall board, M2 |
| 5 | Ø2.2 | (x, 31) | index tab, M2 |
| — | Ø4.0 | y = ±82, spacing to be set | #6 frame screws into the rails' rear faces |

Calendar, centred (−140, −48): Ø12 for the BKA30D-R5's shafts and hub adapters; 3.4 windows at (0, +20.5) (year
latch) and (0, −9) (moon latch); 4 × Ø2.2 at (±14, ±30) for the calendar carrier; Ø2.2 at (0, +32) for the index hand.
**The plate must be aluminium, never steel**: the latches look through it.

Still true from Rev L: the plate is **not symmetric** (a mirrored plate is scrap). Keep labels
out of the cut DXF. Check the 100 mm calibration bar before marking metal.

**Rotor: two printed parts per station.**
- **Hub + dial.** No collar behind the dial and no grub screw (the 3.5 mm gap couldn't hold one anyway): the D-bore
  runs through dial and boss and grips **5 mm of the shaft's flats**, which carries the torque. It's a light press
  fit, sized from a test coupon; the line pulls in-plane, so nothing pushes it off. A dab of clear silicone is the
  fallback for a loose one (not threadlocker, which barely cures against plastic). **Dial Ø52 × 2.5**, its back
  **3.5 mm off the plate** (1.1 mm over the motor-ear screw heads). Two **5 × 2 mm pockets** in its back at r 20.5, 180° from the pin,
  take the magnet pair; a V-notch in its rim at the pin direction aligns the decal. On its front, a **2.5 mm × Ø24 boss**
  the arm bolts to: it lets M2's arm pass 2.5 mm over O1's dial, and puts the shaft tip flush with the arm's back.
  Prints flat, dial down, boss up; the pockets get a 0.3 mm lead-in chamfer against elephant's foot.
- **Arm.** 3 mm arm on 2 × M2 into the boss, end lobe r 5.5. In front at radius r, a **stepped boss**, Ø8 × 1.0 then
  Ø5 × 0.5, so only the bearing's inner race touches it. An **M3 × 4 heat-set insert** goes in flush from the back
  face. Prints flat, boss up. **When real constituents arrive, only the arms get reprinted.**
- **Arm bearing.** The **same V623ZZ** as the rail pulleys, on an **M3×8** + washer into the insert, inner race
  clamped. The axle tip stops 1 mm short of the arm's back face. (Supersedes the thick-printed-pin + PLA-sleeve design,
  which needed oil and let S2 reach pull-in when dry.)

**Kinematics: firmware inverse.** An arm moves its pin sideways too. Turned at constant speed that
makes a false M4 (7.8% on its own), so **each arm is driven at an uneven rate from a per-station
lookup table** that makes the line length exactly sinusoidal. M2's speed peaks at 1.24× mean. The
table is built from the exact line geometry: pulley root radius, legs at ±4.8, plane offsets.
The arm bearing and the rail pulleys are the same part, so the legs hang exactly vertical at mid-stroke
whatever the real groove radius turns out to be, and every pin radius is exactly `pin_scale × amp`. A 1 mm geometry error costs about 0.1 mm at the pen.

**Pulleys and threading** (`rollers.py`). One bracket per station, **directly above the
shaft**, on the top rail's inner face: two V623ZZ on one M3×20 + nyloc, a **3 × 5 × 0.5 shim**
between them (inner races only; an M3 washer rubs the shields), 0.5 mm printed bosses on the
cheeks, and **0.2 mm of axial float** between the cheeks so a slightly fat print can't pinch the bearings.
Pulley axle at y 65.2 (root r 4.8, so the line runs along the tops at y 70, 6 below the rail face). Planes
**−12.75 (rear) and −17.25 (front)**, either side of the arm-bearing groove at −15.0. The bracket is
30 × 15.7, fixed with 2 × #4 either side of the clevis, and neighbouring brackets are 26 mm apart.

Per station: over the IN pulley (90° wrap), down the +x side, U-turn under the arm's bearing, up
the −x side, over the OUT pulley (90°). **The order is mirrored at alternate stations**, so every run
between stations stays in one plane:

| row | S2 | N2 | K1 | O1 | M2 | pen |
|---|---|---|---|---|---|---|
| in over | front | rear | front | rear | front | rear |
| out over | rear | front | rear | front | rear | front = **anchor** |

Leg fleet angle: 2.1–2.3° on the small stations, 4.3° on M2 only at the top of its stroke.
Nothing slides at S2's IN pulley, so the far dead end can tie off right there.

**Home sensing: Hall latches** (decided 2026-09-26). One per station, one each for the year dial and the moon disc;
the drum doesn't need one. The reason is **silent-skip detection**, not homing: each pass gives a predicted step count
at a known angle, 116 times over 60 days on M2 and 466 across all five stations.
- **TI DRV5013**-class digital latch, **through-hole TO-92 (LPG)** since 2026-09-26 (no SMD soldering), lying flat on a
  small perfboard carrier (10 × 16 mm) **behind the plate**, nested in its plate window. With the SOT-23 the element sat
  4.4 mm from the magnets; the TO-92's element sits a few tenths deeper, so **re-run the field check** when the window is
  re-sized. Aluminium is transparent to the field.
- **The flag is a magnet pair**: two 5 × 2 N52 discs side by side, opposite poles toward the sensor. The field flips
  sign sharply between them and the latch switches at that zero crossing, so the edge barely moves with gap or
  temperature: **0.15° per mT** of threshold drift at r 20.5 (19 mT/mm), against the **0.7°** a 28BYJ-48 loses per skip.
  A single magnet with a unipolar switch would be ±1–3°, too coarse. The moon disc sits behind the year dial, 8 mm
  from its sensor: about 2° there, 0.17 day, fine for a moon dial. Cross-talk between the two calendar pairs: 0.26 mT.
- Choose a latch variant that switches at a few mT, so a nearby motor's stray field can't trip it; bench-test one
  beside a running 28BYJ-48. The machine turns one way, so each station always reports the same edge.
- Electrical: 3.3 V, open drain, 10 kΩ pull-up and 100 nF on each board, about 3 mA each. Station latches go to
  the 0x21 MCP23017 (interrupt on change → ESP32); the calendar pair go straight to ESP32 pins. See the build pack.

**Dials and decals** (`decals.py` → `decals_1to1.pdf`, decided 2026-09-26). Each dial carries a printed
decal read against a small printed **index tab** at 12 o'clock just outside its rim. The Hall latch is on the same
radius line, so the home event happens at a known reading. The calendar has one **index hand** that crosses the
year dial and stops at the moon disc's rim. **Scales read astronomical time**:

| | name on the dial | scale | zero |
|---|---|---|---|
| S2 | Sun, twice daily | local mean solar time, 12 h clock | mean Sun on the meridian |
| M2 | Moon, twice daily | lunar hours, 12 per turn (62.1 min each) | mean Moon on the meridian |
| K1 | Sidereal day | local sidereal time, 24 h | 0 h LST |
| N2 | Moon's distance | hours of its 12 h 39.5 m period | argument zero; N2 − M2 is the Moon's mean anomaly |
| O1 | Moon, daily | hours of its 25 h 49.2 m period | argument zero; K1 − O1 tracks the Moon's declination |
| Year | (months) | month names; ticks on the 1st, 8th, 15th, 22nd, 29th; 366 slots, Feb 29 skipped in common years | Jan 1 (= home) |
| Moon | Moon phase (Ø32 disc) | days since new moon, 8 phase icons | new moon (= home) |

- **The scales are warped:** each tick sits where the arm really is, computed with `kinematics.py`. M2's ticks move by
  up to 15.7° (±33 min); the others by 1–4°.
- **HW mark:** the coral tick is the constituent's high water, which is also the pin direction, so it goes over the
  rim notch. On M2 the arm itself is the HW pointer.
- **Readings increase clockwise,** like a clock.
- **The decals depend on the constituent set (G), the longitude and the epoch (nodal u)**, so reprint them with the
  arms and for each deployment year.
- Print 1:1 on laser vinyl or waterslide paper (HP M277dw); two pages, a full set of seven on each. Station decals
  are Ø52 with a Ø24.5 hole; the year decal is an annulus (the moon disc covers its middle); the moon decal is Ø32.
- **Verify before printing:** the ±90° convention in K1 and O1's equilibrium arguments (Schureman, as NOAA uses) moves
  those two zeros by 12 h if it's wrong.

**Calendar dial** (decided 2026-09-26). A **BKA30D-R5** dual-concentric gauge stepper (180:1, driven in 1/3° partial steps) at
**(−140, −48)**, below and between N2 and K1, turns two discs: the **Ø52 year dial on its outer shaft** (same outline,
magnet pair and index scheme as a station) and a **Ø32 moon disc on its inner shaft**, 1 mm in front. The motor and
both Hall latches sit on one perfboard calendar carrier (36 × 68) behind the plate, wired to the main board. Year: one
partial step every 8.1 h; home Jan 1. Moon: one every 39 min; home at new moon; drive it to the **true** phase (low-precision ephemeris), not the mean,
which drifts ±0.5 day. Uniform rates, so no inverse tables. Clearances: 3.6 mm to the N2/K1 dials, 2.0 mm to the
bottom rail, 2.7 mm to the neighbouring wire covers. **Placeholders until a motor is in hand:** the family datasheet
lists stops (outer 320°, inner 270°) while the -R5 is sold as 360°, so confirm continuous rotation on both shafts;
shaft diameters, lengths and positions in the housing (none drawn) set the hub adapters. Its dynamic torque is
0.8–1.2 mN·m and its rated load a 2.5 g pointer, so the dials stay light and homing runs slowly.

**Depth stack** (z, mm in front of the plate's front face = negative). With nothing tall in front of the plate,
everything moved 7.8 mm back, which also cuts the line's leverage on each motor's output bushing by about a third:

| | z |
|---|---|
| Hall element (chip in a plate window) | +0.9 |
| motor-ear screw heads | −2.4 |
| **dial back = magnet faces** | **−3.5** (dial −3.5 to −6.0) |
| arm boss | −6.0 to −8.5 |
| shaft tip = arm back | −8.5 |
| arm front | −11.5 |
| rear pulley plane | −12.75 |
| **arm-bearing groove (line plane)** | **−15.0** (bearing −13.0 to −17.0) |
| front pulley plane | −17.25 |
| pen carriage body | −18.75 to −30.25 (rods and carriage bearings at −23.75) |

All 13 clearances in the fit study and all 26 in the full model are at least 1 mm. The pen travel window is
**119.2 mm against 114.1 needed (+5.1)** with 152 mm rails.

**Homing can't crash the pen.** Pen position is Σdᵢ, bounded by Σr = 57.05 mm, against
62 mm of available travel. No combination of arm angles can reach a stop.

**Drive and electronics** (full detail in the build pack). 28BYJ-48 direct, no reduction, plugged into the main board.
**Waveshare ESP32-C6-LCD-1.47** (user's choice, 2026-09-27; 1.47-inch 172 × 320 LCD on board) + **3 × MCP23017**:
0x20 drives O1, K1, N2, S2; 0x21 drives M2 and the drum and reads the five station latches; 0x22 drives the calendar
coils and reads the year and moon latches. Each reading expander raises INTB on a latch edge (0x21 → GPIO20, 0x22 →
GPIO23). The C6 board has only 8 free, safe GPIOs (0, 1, 2, 3, 18, 19, 20, 23: the LCD, SD card, RGB LED and native USB
take the rest), which is why the third expander exists: the ESP32 uses five pins (18 SCL, 19 SDA, 20, 23, 2 = hold
PWM), and 1 and 3 go to the expansion header. Three **ULN2803A** drive the six motors. The BKA30D-R5's coils are
driven **by a 74AHCT245** (3.3 V in from the 0x22 expander, 5 V out), one gauge motor at a time with the coils off
between moves; the AX1201728SG microstep driver was dropped (SMD-only, and the calendar creeps ~1°/day, so microsteps
bought nothing). **PWM hold** through a high-side **P-channel** switch (IRLIB9343,
TO-220, logic level, driven by a 2N3904) on the motors' 5 V, with a 1N5819 freewheel diode, so the ULN2803A logic ground
stays solid: 60% idle, 100% while stepping. Fit it only if the holding-torque test says the motors need it. 5 V 3 A
supply through a 2.5 A resettable fuse; about 1.5 A peak. NTP daily. The firmware tables are in `pcb/design.py`: `MOTOR_BITS`
(MCP bit ↔ motor wire), `HALL_BITS`, `CAL_BITS` and `CAL_HALL_BITS` (the 0x22 expander), `ESP_GPIO`. The C6's LCD is
on the board's top face, so it faces the back of the machine: handy as a status/debug screen from behind.

**Main board** (rev B, 2026-09-27). One **140 × 81.3 mm (5.5 × 3.2 in)** two-layer board, **all through-hole**
(user decision: no SMD), on **4 × M3 × 30 standoffs** at the corners, behind the faceplate, clear of the motors
(20.5 deep). The ESP32-C6-LCD-1.47 sits in two 1 × 9 female headers (rows 17.78 apart; socketed, per the user) with
**nothing underneath it** (user request; the layout check enforces its 36.4 × 20.3 outline) and its **USB-C at the left
edge**; no copper under its antenna end. DIP chips in sockets; 1/4 W resistors standing up; bussed SIP networks for the
pull-ups. Widened from 127 mm for the third expander and some breathing room. Edges: six motor sockets across the top (JST-XH 5: the 28BYJ-48's own plug, so the kit's
ULN2003 boards go unused), seven Hall sockets along the bottom (JST-XH 3), the calendar (JST-XH 8) and the barrel jack on
the right, a 1 × 6 expansion header (3V3, GND, SDA, SCL, GPIO1, GPIO3: room for an RTC) on the left. Parts, placement and
netlist are data in `pcb/design.py`; `python pcb/layout.py` checks courtyards, edges and the DevKit keep-out
(clean). **`python pcb/silk.py`** draws the silkscreen-only layout: `pcb/silk_layout.png`, and
`pcb/silk_layout_1to1.pdf` to print at 100% and test-fit real parts (check its 50 mm bar). **Routed with Freerouting and DRC-clean in KiCad 10** (2026-09-27): 569 track segments, 8 signal vias, GND poured on
both layers with ~95 stitching vias; KiCad's DRC 0 errors / 0 unconnected (2 warnings: the barrel jack's silk runs past
the edge, as the jack overhangs by design). Fab files: `pcb/tide_main_gerbers.zip` (Gerbers + drill, Protel names, for
JLCPCB: 2 layers, 1.6 mm, 140 × 81.28, 0.25 mm min track / 0.2 clearance / 0.3 mm via drill, all standard).
**`python pcb/make_board.py`** regenerates everything from `design.py`: builds the board in KiCad's Python
(`build_board.py`), exports a Specctra DSN without the GND net, runs **Freerouting 2.4.1** headless (jar + a portable
Java 25 in `~\Tools\freerouting`: Freerouting 2.4 needs Java 25), imports the session, pours and stitches ground,
loops on KiCad's DRC until clean, then plots. `--own-router` uses `route.py` (my A* router, from when GitHub was
throttled) instead; `--keep` reuses `routes.json` (silkscreen or rule tweaks without re-routing). Net classes: HOLD/+5V/
VIN 1.0 mm, ESP_5V 0.5, +3V3 0.3 (narrow enough to pass between 2.54 mm pads), motors 0.4, signals 0.25; GND is poured.

**Line.** ~0.3 mm **fluorocarbon** monofilament. At 0.20 N it's ~1% of breaking strength:
sub-millimetre creep over sixty days, and elastic stretch is a constant absorbed in the pen
zero. Not nylon: it absorbs moisture and wanders with humidity. Crimp sleeves, not knots.

**Pen carriage (Rev M; modelled in `revm_model.html`).** Runs on **two 3 mm steel rods** on **four V623ZZ**, two per
rod, each rolling on the inside of its rod. The V grooves locate it front-to-back, the two sides pushing outward
against opposite rods locate it sideways, and the top and bottom pairs stop it rocking. **The +x pair's axle holes are
slotted ±0.6**: set a light preload once, then lock. Rod size is set by the bearing: **3 mm** seats 0.14 below the
V623's lip, **1/8″** 0.08 below; 4 mm and up ride on the lips. **The carriage rides in front of the line** (body z −18.75
to −30.25, 1.5 mm in front of the front-plane leg), with its rods and bearings at z −23.75, mid-depth in the rail. The
**pen pulley rides behind it** on a short stub in the line plane, on an M3 × 16 through the body into an insert in its
front face. Bearing axles at ±12, rods at ±18.92 (90° V assumed), bottom pair on the pen-pulley line, top pair 14 above;
the **U-shaped body** lets the top bearings rise past the pen bracket's cheeks. **Two flat printed parts**: a 2.5 mm
**rear plate** carrying the pulley stub, and a **front body** (4 mm front plate plus the spacer frame, the bearing
pockets open toward the rear plate). The four bearing axles, **M3 × 16 + nut** from the front, clamp rear plate,
3 × 5 × 0.5 shim, inner race and front body together, so the inner races are the spacers. The nuts on the rear face
clear the pen pulley and the bracket bearings by 2.8. Dead weight **41 g all-up** with the
2:1 loop (0.20 N line tension). Pen arm 25 mm to the drum, contact force ~0.05 N from a light leaf spring, and a
retract lever. **The pen's zero is set by line length and nothing else**: the screw-adjustable anchor on the pen
bracket's front plane is the physical form of Z0 from the spreadsheet.

**Drum.** 130 mm of **3" Sch 40 PVC** (OD 88.9) with two printed end caps carrying the 7 mm
shaft, through both rails (clearance at the top, plain bearing at the bottom), washer under the bottom
cap. Cut it square. Its axis sits at x +155.5, z −24, on the pen carriage's mid-plane.

**Chart speed — still open.** Circumference 279.3 mm.

| rev period | per tidal cycle | sheets over 60 days |
|---|---|---|
| 7 days | 20.6 mm | 9 |
| 5 days | 28.9 mm | 12 |
| 3.5 days | 41.3 mm | 17 |

7 days draws a very steep trace; 3.5 days is a more classical marigram. It's a firmware constant.
Paper: A4 wrapped the long way leaves 17.7 mm to tape; trim the 210 side to about 140.

**Frame.** 1×2 pine is still right: the pen carriage reaches z −30.25 against a 38.1 mm rail, where 1×1 (25.4) would
be too shallow. The rails are **152 apart** (posts 152), set by the pen's travel window. The faceplate screws to the
rails' rear faces with a 12 mm overlap. Rev M rail features:
- **top rail, inner face:** 2 × #4 pilots per pulley bracket at (station x ± 11, 15 from the rear edge), six brackets;
  2 pen-rod sockets, Ø3.1 × 9 at (70 ± 18.92, 23.75 from the rear edge)
- **bottom rail, inner face:** the 2 matching pen-rod sockets
- **both rails:** the drum shaft hole at (155.5, 24 from the rear edge)
- **rear faces:** the faceplate pilots

The Rev L rules for drilling the rails as a mirrored pair (clamp **outer face to outer face**, drill from both
sides) still apply to the rod sockets and the drum hole.

**Printing.** Every printed part prints **without support** (overhang check, scratchpad `printcheck.py`: nothing
steeper than 45° off the bed except short bridges: the 5.1 mm magnet-pocket roofs, the insert-hole ledges and the
bracket's teardrop holes).

| Part | Orientation |
|---|---|
| Station hub + dial ×5 | dial back down, boss up |
| Arm ×5 | back down, bearing boss up |
| Index tab ×5 | flat |
| Pulley bracket ×6 | rail face down (as built in `rollers.py`) |
| Pen carriage rear plate | front face down, pulley stub up |
| Pen carriage front body | front face down, pockets open upward |
| Year dial + adapter, moon disc | front (decal) face down |
| Calendar index hand | on its flush side, or front face down |
| Drum end caps ×2 | flat |

PLA, 3 perimeters. Before the real parts, print **coupons**: the D-bore (tune to a light press on the motor flats),
a magnet pocket at 5.1 and 5.2, the 4.0 insert hole, and a PVC-bore ring for the drum cap. Iron the dials' front
faces if the decal shows the layer lines.

---

## Files

Everything lives in `C:\Users\mikem\Desktop\tide-machine\` (a git repo).

| File | Rev | What |
|---|---|---|
| `RESUME.md` | **M** | this file: the spec until the Ruby is ported |
| `station_study.py` → `station_study.html` | **M** | two-station fit study (O1 + M2): every Rev M part, clearances, depth stack. Published (link above). Writes no STLs |
| `buildpack.py` → `bom.csv` + `build_pack.html` | **M** | bill of materials with order quantities, wiring diagram and pin map, from one data source. Published (link above) |
| `build_pack.tmpl.html` | **M** | the build-pack page template, including the wiring diagram |
| `pcb/design.py` | **M** | main board as data: parts, KiCad footprints, placement, netlist, net classes, firmware bit tables |
| `pcb/layout.py`, `pcb/fplib.py`, `pcb/render.py` | **M** | placement checker (courtyards, edges, DevKit keep-out) and preview (`pcb/placement.png`), reading the real KiCad footprints in `pcb/footprints/` |
| `pcb/silk.py` → `pcb/silk_layout.png` + `_1to1.pdf` | **M** | silkscreen-only layout: outlines, refs and values, connector names and pinouts; the PDF is true scale |
| `pcb/silk_labels.py` | **M** | the silkscreen labels as data, shared by the preview and the KiCad board |
| `pcb/make_board.py` | **M** | one command: build → route → pour/stitch → DRC loop → Gerbers, drill, zip, 3D renders |
| `pcb/build_board.py`, `pcb/route.py` | **M** | KiCad-side board builder (run under KiCad's Python) and the two-layer grid router |
| `pcb/tide_main.kicad_pcb` (+ `.kicad_pro`, `.kicad_dru`) | **M** | the routed board, openable in KiCad 10 |
| `pcb/tide_main_gerbers.zip`, `pcb/gerbers/`, `pcb/render_top.png` | **M** | fab files and KiCad's 3D renders |
| `station_study.py --full` → `revm_model.html` | **M** | the whole machine from the same part code: five stations, calendar, six brackets, pen carriage, drum, frame |
| `station_study.tmpl.html` | **M** | the viewer template it fills |
| `kinematics.py` | **M** | line geometry + the firmware inverse (`Station(r).theta(phi)`); the decals use it, and the firmware tables should too |
| `decals.py` → `decals_1to1.pdf` | **M** | the seven decals (five stations, year, moon), warped, astronomical zeros; two pages, a full set on each. **Placeholder constituents** |
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
13. **Hall latches behind the plate, reading a magnet pair** (Rev M; replaces the TCST2202 on the plate). Nothing
    tall in front of the plate means a shallow stack; the opposed-pole pair gives optical-grade edges (0.15°/mT) that a
    single magnet can't. Consequence to remember: **the faceplate must never be steel**.
14. **The pen carriage rides in front of the line** (Rev M). With the line plane at −15 there's no room behind it; in
    front, the rods sit mid-depth in the rail and the pen pulley rides behind the body on a stub.
15. **Every printed part prints without support** (printability review, 2026-09-26). This removed the hub collar
    and grub screw, split the pen carriage into two flat parts, and made the calendar hand flush with its base
    and 1.5 thick. Keep new parts to the same rule: one flat face, everything else growing up from it.
16. **One through-hole main board** (2026-09-26): behind the plate, everything else wired to it; DIP chips in
    sockets, the ESP32 socketed, **no SMD anywhere** (the user can't hand-solder it). That dropped the AX1201728SG for
    direct 74AHCT245 coil drive, moved the Hall latch to the TO-92 package, and replaced the SOT-23 MOSFETs with an
    IRLIB9343 (TO-220) and a 2N3904.
17. **ESP32-C6-LCD-1.47 with three MCP23017s** (2026-09-27, the user's choice of MCU). Its 8 free GPIOs can't carry
    the calendar's 8 coil lines directly, so a third expander (0x22) runs the calendar and its two latches, and the
    ESP32 needs only I²C, two interrupts and the PWM. Board widened to 140 mm.

---

## Open items

- [ ] **Port Rev M into `tide_machine.rb`** (CFG + builders), then regenerate
      `faceplate.py` / `rails.py` outputs and the 3D viewer from it. **Don't order or drill
      Rev L files meanwhile.**
- [x] ~~Route the main board~~: rev B (ESP32-C6) routed by Freerouting, DRC clean (2026-09-27). Open
      `pcb/tide_main.kicad_pcb` in KiCad to inspect; regenerate with `python pcb/make_board.py`.
- [ ] **Firmware for the ESP32-C6:** three MCP23017s at 0x20/0x21/0x22 on GPIO19/18; the tables in `pcb/design.py`.
- [ ] **Order the PCB:** upload `pcb/tide_main_gerbers.zip` to JLCPCB (2 layers, 1.6 mm, HASL, 5 pcs). Print
      `pcb/silk_layout_1to1.pdf` first and test-fit the XH sockets, jack and TO-220.
- [ ] **Order parts:** `bom.csv` / the build pack. On arrival, verify the three flagged items (BKA30D-R5 continuous
      rotation and shaft sizes; V623ZZ groove radius and V angle; DRV5013 variant beside a running motor) before
      designing further around them. Order the PCB only after its DRC is clean.
- [ ] **Faceplate updates for the main board:** re-size the five station Hall windows and the two calendar windows for
      the TO-92 latch (re-run the field check), and add 4 × Ø3.2 for the board's standoffs (position to choose: behind
      the station row, screw heads clear of the dials).
- [ ] **Decal inputs:** NOAA G values, longitude and deployment epoch into `decals.py`; check the K1/O1
      ±90° argument convention against NOAA before printing.
- [ ] **Measure a V623ZZ's groove root radius** when they arrive (4.8 assumed). It sets the
      pulley axle height and feeds the firmware table. The legs stay parallel whatever it is.
      Order 25: 22 fitted + spares.
- [x] ~~Pen travel didn't fit~~: the window was 107.2 against 114.1 with 140 mm rails. **Fixed by rails 152 apart**
      (window 119.2, +5.1; decided 2026-09-26). A one-bearing-per-side carriage would not have helped: both
      ends of the window are set by the pen pulley itself, and two bearings would let the carriage rock.
- [ ] Pen carriage details: ballast pocket, leaf spring and retract lever, pen holder.
- [ ] Drum position and rail length for the shorter row; frame-screw spacing on the new
      plate outline.
- [ ] **Measure the 28BYJ-48's holding torque** at the output shaft, powered and unpowered.
      The datasheet's 59–118 mN·m "friction torque" hints the hold could go to zero.
- [ ] **Replace the placeholder constituents** from NOAA CO-OPS for the chosen port. They set
      every pin radius, and only the arms need reprinting.
- [ ] **Decide chart speed** (7 vs 3.5 days per revolution).
- [ ] Firmware: per-station inverse tables from `kinematics.py`, rates, Hall edge timing (MCP23017 INTB +
      INTCAP), skip detection, the calendar (366-slot year, true moon phase), NTP, PWM hold.
- [ ] Commissioning commands: **go-to-phase** for one station at a time (command the
      constituent phase to 0°, 90°, 180°, 270°; the pen should move ±r); **go-to-zero** (all outputs 0, for the pen datum at the anchor screw);
      a **speedup multiplier** (1000× replays 60 days in 86 minutes; stay under 5000×; re-home
      after any skip).
- [ ] Commissioning order: mechanical → verify each arm's r by go-to-phase → direction-check
      every motor at 1000× → home → pen zero → 90-minute soak at 1000× against the sandbox →
      NTP, re-home, start.
- [ ] Main board position behind the plate (wire covers point down; Hall carriers sit at 12 o'clock above each
      motor; the calendar carrier fills the gap between N2 and K1). 28BYJ-48 leads are ~24 cm: check the drum motor's
      reach, or add an XH extension.

---

## If the Darlington drop bites

The ULN2803A's Darlingtons eat ~1 V of the 5 V rail, 20% of driving torque. If steps look marginal
at M2, swap to logic-level MOSFETs for a free ~22% before touching anything else.
Beyond that: bipolar conversion (cut the centre-tap trace) for ~1.4×, then a chopper
driver to set current against a thermal budget you choose.

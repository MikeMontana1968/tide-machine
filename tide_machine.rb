# ---------------------------------------------------------------------------
#  TIDE MACHINE  --  parametric SketchUp model builder
#  REV G : direct drive. 28BYJ-48 coaxial behind each crank disc, ULN2003,
#          PWM hold on a common rail. No pinions, no gear rims, no reduction.
#
#  Six carriages in one row on two identical rails: five crank stations
#  (M2, S2, N2, K1, O1) plus the pen as the sixth. One monofilament line sums
#  them onto a pen writing on a length of 3" PVC.
#
#  Revision trail: B concentric rings -> C spur-pair row -> D direct drive ->
#  E rails -> F pen carriage + 2:1 -> G cable legs parallel -> H home flags
#  -> I shaft budget recovered -> J faceplate to 1.5 mm sheet metal.
#
#  HOW TO RUN
#    1. SketchUp -> Window -> Ruby Console
#    2. load "C:/Users/mikem/Desktop/tide-machine/tide_machine.rb"
#    3. Re-run any time; it purges the previous build first.
#
#  Set CFG[:explode] = 1.0 for the exploded view.
#  Millimetres. Axes: X right, Y up, Z toward the viewer -- mechanism at
#  negative Z, steppers and electronics at positive Z.
#
#  THE WHOLE TORQUE BUDGET RESTS ON CABLE TENSION. See NOTES at the bottom
#  before you change :pin_scale or hang a heavier pen on it.
# ---------------------------------------------------------------------------

module TideMachine

  CFG = {
    :explode     => 0.0,
    :explode_gap => 90.0,
    :segs        => 48,
    :labels      => true,

    # ---- constituents, left to right --------------------------------------
    :sym         => %w[M2 S2 N2 K1 O1],
    :amp         => [1.00, 0.25, 0.21, 0.10, 0.07],   # metres, illustrative
    :pin_scale   => 35.0,                             # r_pin = pin_scale * amp
    :disc_margin => 12.0,
    :slotted     => [true, true, true, false, false], # K1/O1 print the pin in
    :start_ang   => [0.0, 64.0, 150.0, 232.0, 300.0],
    :x           => [-88.0, -17.0, 27.0, 71.0, 115.0],
    :rod_x       => [-137.0, -39.0, 5.0, 49.0, 93.0, 137.0],  # SHARED
    :rod_gap     =>   2.0,    # between neighbouring carriage faces

    # ---- design loads -----------------------------------------------------
    :tension_n   => 0.20,     # cable tension, N -- counterbalanced pen
    :motor_mNm   => 34.3,     # 28BYJ-48 rated holding torque
    :hold_duty   => 0.60,     # PWM hold on the common motor rail

    # ---- plate ------------------------------------------------------------
    :plate_x0    => -156.0, :plate_x1 => 165.0,
    :plate_y0    =>  -82.0, :plate_y1 =>  82.0,   # 12 mm of screw landing
    :plate_t     => 1.5,      # SHEET METAL -- set by the motor's boss height

    # ---- discs / motors ---------------------------------------------------
    :disc_z      => -9.0,
    :disc_t      => 6.0,
    :hub_d       => 11.0,     # 2.9 mm wall on a 5.2 bore
    :bore_d      =>  5.2,     # runs through disc AND hub: 8 mm of grip
    :boss_d      =>  9.5,     # counterbore clears the motor's 9 mm boss
    :boss_l      =>  1.5,     # and registers the disc on it
    :flag_band   =>  3.0,     # radial width of the thinned rim
    :flag_t      =>  2.0,     # its thickness -- sensor slot straddles this
    :notch_deg   => 12.0,     # gap in the band; centred on the pin
    :sensor_off  =>  1.5,     # beam sits this far inboard of the OD
    :sensor_deep =>  7.0,
    :slot_gap    =>  3.2,     # photointerrupter fork, straddles :flag_t
    :motor_d     => 28.0,
    :motor_l     => 19.0,

    # ---- yokes ------------------------------------------------------------
    :pin_d       => 5.0,     # same stock as the guide rods
    :yoke_z      => -26.0,
    :big         => [true, false, false, false, false],
    :yoke_w_big  => 96.0,     # M2 only
    :slot_len_big=> 76.0,
    :yoke_w_sml  => 42.0,     # shared by S2, N2, K1, O1
    :slot_len_sml=> 24.0,     # sized for S2, the largest of the four
    :web_t       =>  5.2,     # = 1 x slot height, top and bottom
    :groove_fit  =>  2.60,    # LEFT groove: close fit, this one locates
    :groove_free =>  3.30,    # RIGHT groove: clearance, absorbs rod skew
    :dimple_d    =>  2.6,     # drill centring dimple, both faces
    :dimple_deep =>  1.0,
    :ring_y      =>  9.0,     # where the line rides in the ring
    :rod_len     => 158.0,    # one cut length; bottoms in blind sockets
    :yoke_t      => 12.0,
    :slot_h      => 5.2,      # pin + 0.2; this is the kinematic fit
    :rod_d       => 5.0,

    # ---- rails: 1x2 PINE, 19.05 x 38.1 actual. Box frame. -----------------
    :rail_y      => 70.0,     # inner face of each rail
    :rail_t      => 19.05,    # 1x2 pine, thin dimension
    :rail_z0     =>   0.0,    # rear face -- the faceplate screws to this
    :rail_z1     => -38.1,    # front face
    :socket_deep =>   9.0,    # rod sockets, drilled into the inner face
    :screw_pitch =>  75.0,    # faceplate wood screws along each rail
    :post_w      =>  19.05,   # box-frame end posts, same stock
    :rod_hole_d  =>   5.2,
    :rod_z       => -20.0,
    :ring_hole_d =>   2.0,    # pilot for a screw eye in the wood
    :ring_z      => -30.0,
    :ring_dx     =>   6.0,    # rail rings sit +/-this above each station;
                              # keeps both cable legs vertical

    :rail_x0     => -160.0, :rail_x1 => 310.0,

    # ---- pen: a carriage on two guideposts, 2:1 off the cable -------------
    :pen_x       => 159.0,    # shares rod 5 with O1 -- no gap
    :pen_rod_x   => [181.0],  # only ONE new rod
    :pen_h       =>  16.0,
    :pen_arm     =>  25.0,    # reach from carriage face to the drum surface
    :pen_ring_y  =>   5.0,
    :ballast_w   =>  32.0,    # pocket: part-fill to 41 g all-up
    :ballast_h   =>   9.0,
    :ballast_y   =>  -2.0,
    :cable_z     => -30.0,
    :drum_x      => 249.5,
    :drum_shaft_d=>   7.0,    # through BOTH rails: top clearance,
                              # bottom bearing, from the same part
    :drum_d      =>  88.9,    # 3" Sch 40 PVC OD -- do not print this
    :drum_id     =>  77.9,    # its bore; the end caps plug it
    :cap_deep    =>  14.0,
    :drum_y0     =>  -65.0,
    :drum_y1     =>   65.0,
  }

  PALETTE = {
    "PLA Disc"  => [ 31, 111, 178],
    "PLA Part"  => [ 90, 142, 184],
    "Sheet"     => [176, 184, 190],
    "Wood"      => [196, 164, 112],
    "Steel"     => [120, 128, 136],
    "Pin"       => [ 58,  64,  72],
    "Motor"     => [ 70,  89, 106],
    "Board"     => [ 22,  92,  70],
    "Cable"     => [156,  95,  23],
    "Paper"     => [246, 248, 250],
  }

  TAGS = ["01 Crank discs", "02 Pins", "03 Faceplate", "04 Steppers",
          "05 Yokes", "06 Cable", "07 Pen", "08 Electronics",
          "09 Labels", "10 Drum", "11 Home sensors"]

  def self.r_pin(i);  CFG[:pin_scale] * CFG[:amp][i];   end
  def self.disc_r(i); r_pin(i) + CFG[:disc_margin];     end
  # peak load torque at the crank, mN.m  (moving pulley doubles the tension)
  def self.load_mNm(i); 2.0 * CFG[:tension_n] * r_pin(i); end
  def self.margin(i);   CFG[:motor_mNm] / load_mNm(i);   end
  # the slot must span the pin's full horizontal excursion, 2 x r_pin
  def self.big?(i);     CFG[:big][i];                                        end
  def self.slot_len(i); big?(i) ? CFG[:slot_len_big] : CFG[:slot_len_sml];   end
  def self.yoke_w(i);   big?(i) ? CFG[:yoke_w_big]   : CFG[:yoke_w_sml];     end
  # the slot each station needs on its own; the console prints it beside
  # the shared one so an over-tight class shows up immediately
  def self.slot_need(i); 2.0 * r_pin(i) + CFG[:pin_d]; end
  # plate hole only has to clear the boss now, not the hub
  def self.shaft_clear; CFG[:boss_d] + 0.5; end
  # how far the boss sticks out FORWARD of the plate; 0 once plate >= boss
  def self.boss_proud;  [CFG[:boss_l] - CFG[:plate_t], 0.0].max; end
  # faceplate screws land midway across the overlap onto the rail
  def self.screw_y;     (CFG[:rail_y] + CFG[:plate_y1]) / 2.0; end
  def self.screw_xs
    n = ((CFG[:plate_x1] - CFG[:plate_x0]) / CFG[:screw_pitch]).round
    (0..n).map { |k| CFG[:plate_x0] + 12.0 + (CFG[:plate_x1] - CFG[:plate_x0] - 24.0) * k / n.to_f }
  end

  # Every station, cranks plus the pen, in cable order.
  def self.stations; CFG[:x] + [CFG[:pen_x]]; end
  def self.station_ring_y(i)
    i < CFG[:x].length ? CFG[:ring_y] : CFG[:pen_ring_y]
  end
  # Two fixed rings per station, straddling it by :ring_dx.
  def self.ring_pairs
    stations.flat_map { |x| [x - CFG[:ring_dx], x + CFG[:ring_dx]] }
  end

  # =========================================================================
  #  GEOMETRY HELPERS
  # =========================================================================

  def self.lathe(ents, prof, segs = CFG[:segs])
    mesh = Geom::PolygonMesh.new
    step = 2 * Math::PI / segs
    ring = (0...segs).map do |s|
      c, n = Math.cos(s * step), Math.sin(s * step)
      prof.map { |r, y| Geom::Point3d.new((r * c).mm, y.mm, (r * n).mm) }
    end
    segs.times do |s|
      a, b = ring[s], ring[(s + 1) % segs]
      prof.length.times do |i|
        j = (i + 1) % prof.length
        ri, rj = prof[i][0].abs, prof[j][0].abs
        next if ri < 1e-9 && rj < 1e-9
        if    ri < 1e-9 then mesh.add_polygon(a[i], b[j], a[j])
        elsif rj < 1e-9 then mesh.add_polygon(a[i], a[j], b[i])
        else                 mesh.add_polygon(a[i], a[j], b[j], b[i])
        end
      end
    end
    ents.add_faces_from_mesh(mesh, 4)
  end

  def self.box(ents, x0, y0, z0, x1, y1, z1)
    f = ents.add_face([[x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0]]
                        .map { |x, y, z| Geom::Point3d.new(x.mm, y.mm, z.mm) })
    f.reverse! if f.normal.z > 0
    f.pushpull((z1 - z0).mm)
    f
  end

  # solid of revolution about Z, centred on (x, y)
  def self.disc_z(ents, x, y, r_out, r_in, z0, z1, segs = CFG[:segs])
    g = ents.add_group
    h = z1 - z0
    prof = r_in > 0 ? [[r_in, 0], [r_out, 0], [r_out, h], [r_in, h]]
                    : [[0, 0], [r_out, 0], [r_out, h], [0, h]]
    lathe(g.entities, prof, segs)
    g.transform!(Geom::Transformation.rotation(ORIGIN, X_AXIS, Math::PI / 2.0))
    # the rotation puts the solid at local z 0..h, so translate by z0 --
    # translating by z1 put every one of these a full thickness rearward
    g.transform!(Geom::Transformation.translation(
      Geom::Vector3d.new(x.mm, y.mm, z0.mm)))
    g
  end

  def self.rod_y(ents, x, z, r, y0, y1, segs = 12)
    g = ents.add_group
    lathe(g.entities, [[0, y0], [r, y0], [r, y1], [0, y1]], segs)
    g.transform!(Geom::Transformation.translation(
      Geom::Vector3d.new(x.mm, 0, z.mm)))
    g
  end

  # Extrude a closed 2D profile (with optional inner loops) along +Z.
  def self.extrude(ents, outline, holes, z0, z1)
    g = ents.add_group
    e = g.entities
    face = e.add_face(outline.map { |a, b| Geom::Point3d.new(a.mm, b.mm, z0.mm) })
    holes.each do |lp|
      f = e.add_face(lp.map { |a, b| Geom::Point3d.new(a.mm, b.mm, z0.mm) })
      f.erase! if f && f.valid?
    end
    face = e.grep(Sketchup::Face).max_by(&:area) unless face && face.valid?
    d = (z1 - z0).abs
    d = -d if face.normal.z < 0
    face.pushpull(d.mm)
    g
  end

  # Extrude a closed XZ profile along +Y (for features that run the full
  # height of a part, such as the rod grooves).
  def self.extrude_y(ents, outline, y0, y1, holes = [])
    g = ents.add_group
    e = g.entities
    face = e.add_face(outline.map { |a, c| Geom::Point3d.new(a.mm, y0.mm, c.mm) })
    holes.each do |lp|
      f = e.add_face(lp.map { |a, c| Geom::Point3d.new(a.mm, y0.mm, c.mm) })
      f.erase! if f && f.valid?
    end
    face = e.grep(Sketchup::Face).max_by(&:area) unless face && face.valid?
    d = (y1 - y0).abs
    d = -d if face.normal.y < 0
    face.pushpull(d.mm)
    g
  end

  def self.end_w(i); (yoke_w(i) - slot_len(i)) / 2.0; end

  # End block, drawn in XZ so the groove runs the full height of the carriage.
  # The groove centre sits `off` beyond the face, out in the shared-rod gap,
  # so two neighbouring carriages close on the same rod.
  # sgn = +1 right-hand end, -1 left-hand end.
  def self.end_profile(sgn, hw, ew, gr, t, off)
    uo = sgn * hw
    uc = uo + sgn * off
    ui = sgn * (hw - ew)
    zi = Math.sqrt([gr * gr - off * off, 0.0].max)
    f0 = Math.acos([[-sgn * off / gr, 1.0].min, -1.0].max)
    a0, a1 = sgn > 0 ? [2 * Math::PI - f0, f0] : [-f0, f0]
    pts = [[ui, -t / 2.0], [uo, -t / 2.0], [uo, -zi]]
    n = 14
    (0..n).each do |k|
      a = a0 + (a1 - a0) * k / n.to_f
      pts << [uc + gr * Math.cos(a), gr * Math.sin(a)]
    end
    pts << [uo, zi] << [uo, t / 2.0] << [ui, t / 2.0]
    pts
  end

  # Closed XY outline of an annular sector -- extrudes into the flag band.
  def self.sector_outline(cx, r_in, r_out, a0, a1, n = 48)
    pts = (0..n).map do |k|
      t = (a0 + (a1 - a0) * k / n.to_f) * Math::PI / 180.0
      [cx + r_out * Math.cos(t), r_out * Math.sin(t)]
    end
    pts += (0..n).map do |k|
      t = (a1 - (a1 - a0) * k / n.to_f) * Math::PI / 180.0
      [cx + r_in * Math.cos(t), r_in * Math.sin(t)]
    end
    pts
  end

  def self.circle_loop(cx, cy, d)
    r = d / 2.0
    (0...16).map { |k| a = k * 2 * Math::PI / 16; [cx + r * Math.cos(a), cy + r * Math.sin(a)] }
  end

  def self.fix(grp)
    return grp unless grp.respond_to?(:manifold?) && grp.manifold?
    grp.entities.grep(Sketchup::Face).each(&:reverse!) if grp.volume < 0
    grp
  rescue StandardError
    grp
  end

  def self.finish(grp, tag, mat)
    grp.layer = tag if tag
    grp.material = mat if mat
    fix(grp)
  end

  def self.ez(layer); CFG[:explode] * CFG[:explode_gap] * layer; end

  def self.label(ents, text, pt)
    return unless CFG[:labels]
    t = ents.add_text(text, pt, Geom::Vector3d.new(0, 24.mm, -24.mm))
    t.layer = TAGS[8]
  rescue StandardError
    nil
  end

  # =========================================================================
  #  COMPONENTS
  # =========================================================================

  def self.def_motor(model)
    d = model.definitions.add("28BYJ-48 stepper")
    e = d.entities
    r = CFG[:motor_d] / 2.0
    disc_z(e, 0, 0, r, 0, 0, CFG[:motor_l], 32)          # body
    disc_z(e, 0, 0, 4.6, 0, -8.0, 0, 16)                 # boss
    disc_z(e, 0, 0, 2.5, 0, -22.0, 0, 12)                # 5 mm D-shaft stub
    box(e, -r - 8.5, -3.0, 0.0, -r + 2, 3.0, 1.2)        # ears, at the face
    box(e,  r - 2,   -3.0, 0.0,  r + 8.5, 3.0, 1.2)
    d
  end

  def self.def_uln(model)
    d = model.definitions.add("ULN2003 driver board")
    box(d.entities, -17.5, -16.0, 0, 17.5, 16.0, 1.6)
    box(d.entities,  -9.0,  -6.0, 1.6,  9.0,  6.0, 5.0)
    d
  end

  # =========================================================================
  #  SUBASSEMBLIES
  # =========================================================================

  def self.build_plate(ents, mats)
    g  = ents.add_group
    dz = ez(1)
    box(g.entities, CFG[:plate_x0], CFG[:plate_y0], dz,
                    CFG[:plate_x1], CFG[:plate_y1], CFG[:plate_t] + dz)
    finish(g, TAGS[2], mats["Sheet"])
    label(g.entities, format("Faceplate SHEET  %.0f x %.0f x %.1f",
                             CFG[:plate_x1] - CFG[:plate_x0],
                             CFG[:plate_y1] - CFG[:plate_y0], CFG[:plate_t]),
          Geom::Point3d.new(CFG[:plate_x0].mm, (CFG[:plate_y1] + 14).mm, dz.mm))
    g.name = "03 Faceplate"
    g
  end

  def self.build_stations(ents, motor_def, mats)
    g  = ents.add_group
    z0 = CFG[:disc_z]
    z1 = CFG[:disc_z] + CFG[:disc_t]

    CFG[:sym].each_with_index do |sym, i|
      x  = CFG[:x][i]
      rp = r_pin(i)
      dr = disc_r(i)
      a  = CFG[:start_ang][i] * Math::PI / 180.0

      # ---- crank disc, pressed straight onto the motor shaft -----------
      # body stops short of the OD; the last :flag_band of rim is thinned to
      # :flag_t so a photointerrupter's slot can straddle it
      fb = CFG[:flag_band]
      br = CFG[:bore_d] / 2.0
      # the disc is bored THROUGH: its 6 mm counts toward shaft grip, which is
      # the only way to use all 8 mm the motor offers
      d = disc_z(g.entities, x, 0, dr - fb, br, z0, z1)
      finish(d, TAGS[0], mats["PLA Disc"])

      # home flag: the band is continuous EXCEPT for a notch centred on the
      # pin, so the flag-to-pin angle is exact by construction
      nd  = CFG[:notch_deg]
      adg = CFG[:start_ang][i]
      band = extrude(g.entities,
                     sector_outline(x, dr - fb, dr, adg + nd / 2.0,
                                    adg + 360.0 - nd / 2.0),
                     [], z1 - CFG[:flag_t], z1)
      finish(band, TAGS[0], mats["Gear Teeth"]) if band

      # hub reaches REARWARD from the disc, through the plate's clearance
      # hole. Bored 5.2 as far as the boss, then counterbored to clear it --
      # which also registers the disc concentrically on the boss.
      bp  = boss_proud
      hub = disc_z(g.entities, x, 0, CFG[:hub_d] / 2.0, br, z1, -bp, 24)
      finish(hub, TAGS[0], mats["PLA Disc"])
      if bp > 0.1      # only needed if the plate is thinner than the boss
        cb = disc_z(g.entities, x, 0, CFG[:hub_d] / 2.0, CFG[:boss_d] / 2.0,
                    -bp, 0.0, 24)
        finish(cb, TAGS[0], mats["PLA Disc"])
      end

      # amplitude slot, or a printed-in pin boss on the small stations
      feat = g.entities.add_group
      if CFG[:slotted][i]
        box(feat.entities, 7.0, -4.0, z0 - 2.2, dr - 6.0, 4.0, z0)
        finish(feat, TAGS[0], mats["Steel"])
      else
        box(feat.entities, rp - 4.0, -4.0, z0 - 2.2, rp + 4.0, 4.0, z0)
        finish(feat, TAGS[0], mats["Pin"])
      end
      feat.transform!(Geom::Transformation.rotation(ORIGIN, Z_AXIS, a))
      feat.transform!(Geom::Transformation.translation(
        Geom::Vector3d.new(x.mm, 0, 0)))

      # ---- crank pin: short, forward to its own yoke -------------------
      pin = disc_z(g.entities, 0, 0, CFG[:pin_d] / 2.0, 0,
                   CFG[:yoke_z] - 2.0, z0 + 1.0, 12)
      finish(pin, TAGS[1], mats["Pin"])
      pin.transform!(Geom::Transformation.translation(
        Geom::Vector3d.new(rp.mm, 0, 0)))
      pin.transform!(Geom::Transformation.rotation(ORIGIN, Z_AXIS, a))
      pin.transform!(Geom::Transformation.translation(
        Geom::Vector3d.new(x.mm, 0, 0)))

      # ---- yoke carriage --------------------------------------------
      yz0 = CFG[:yoke_z]
      yz1 = CFG[:yoke_z] + CFG[:yoke_t]
      zc  = (yz0 + yz1) / 2.0
      hw  = yoke_w(i) / 2.0
      sl  = slot_len(i) / 2.0
      sh  = CFG[:slot_h] / 2.0
      hh  = sh + CFG[:web_t]
      ew  = end_w(i)
      tt  = CFG[:yoke_t]
      dd  = CFG[:dimple_deep]
      ry  = sh + CFG[:web_t] / 2.0

      low = extrude(g.entities,
                    [[x - sl, -hh], [x + sl, -hh], [x + sl, -sh], [x - sl, -sh]],
                    [], yz0, yz1)
      finish(low, TAGS[4], mats["PLA Part"])

      # upper web in three slices so the drill dimples are real recesses
      up = [[x - sl, sh], [x + sl, sh], [x + sl, hh], [x - sl, hh]]
      dim = [circle_loop(x, ry, CFG[:dimple_d])]
      [[yz0, yz0 + dd, dim], [yz0 + dd, yz1 - dd, []], [yz1 - dd, yz1, dim]].each do |z0, z1, hl|
        w = extrude(g.entities, up, hl, z0, z1)
        finish(w, TAGS[4], mats["PLA Part"])
      end

      # end blocks: LEFT groove locates, RIGHT groove floats
      off = CFG[:rod_gap] / 2.0
      [[-1, CFG[:groove_fit]], [1, CFG[:groove_free]]].each do |sgn, gr|
        blk = extrude_y(g.entities,
                        end_profile(sgn, hw, ew, gr, tt, off)
                          .map { |a, c| [x + a, zc + c] },
                        -hh, hh)
        finish(blk, TAGS[4], mats["PLA Part"])
      end

      # ---- stepper, COAXIAL behind the plate ---------------------------
      mt = Geom::Transformation.translation(Geom::Vector3d.new(
             x.mm, 0, (CFG[:plate_t] + ez(2)).mm))
      m = g.entities.add_instance(motor_def, mt)
      m.layer = TAGS[3]; m.material = mats["Motor"]
      m.name = sym + " drive"

      # no standoff: the motor's ears bolt flat to the plate. Two M3
      # through-holes; a 4 mm spacer would cost 4 mm of shaft the hub needs.

      # home sensor: 12 o'clock, on a bracket bolted to the plate's front
      # face, fork reaching forward to straddle the flag band
      sr = dr - CFG[:sensor_off]
      brk = g.entities.add_group
      box(brk.entities, x - 7, dr - 9, -CFG[:sensor_deep], x + 7, dr + 7, 0)
      finish(brk, TAGS[10], mats["PLA Part"])
      bc = z1 - CFG[:flag_t] / 2.0          # centre of the flag band
      sg = CFG[:slot_gap] / 2.0
      [[bc - sg - 1.4, bc - sg], [bc + sg, bc + sg + 1.4]].each do |fz0, fz1|
        fk = g.entities.add_group
        box(fk.entities, x - 5, sr - 3, fz0, x + 5, sr + 3, fz1)
        finish(fk, TAGS[10], mats["Board"])
      end

      label(g.entities,
            format("%s   r=%.1f   yoke %.0f wide   load %.1f mN.m   %.1fx",
                   sym, rp, yoke_w(i), load_mNm(i), margin(i)),
            Geom::Point3d.new(x.mm, (dr + 6).mm, z0.mm))
    end
    g.name = "Stations"
    g
  end

  # Six rods, not ten: each one is shared by the two carriages it sits between.
  def self.build_rods(ents, mats)
    g = ents.add_group
    zc = CFG[:yoke_z] + CFG[:yoke_t] / 2.0
    (CFG[:rod_x] + CFG[:pen_rod_x]).each do |rx|
      rod = rod_y(g.entities, rx, zc, CFG[:rod_d] / 2.0,
                  -CFG[:rod_len] / 2.0, CFG[:rod_len] / 2.0)
      finish(rod, TAGS[4], mats["Steel"])
    end
    g.name = "Guide rods"
    g
  end

  # Top and bottom rails: 1x2 pine, full length, plus two end posts between
  # them to close the box. No lip -- the faceplate screws to the rear face.
  # The two rails are MIRROR images: identical features at identical (x, z),
  # but each drilled on its inner face, so laying them both inner-face-up
  # with the rear edge toward you reverses x between them. See RAIL DRILLING.
  def self.build_rails(ents, mats)
    g  = ents.add_group
    x0 = CFG[:rail_x0]
    x1 = CFG[:rail_x1]
    z0 = CFG[:rail_z0]
    z1 = CFG[:rail_z1]
    ry = CFG[:rail_y]
    sd = CFG[:socket_deep]

    rod_h  = (CFG[:rod_x] + CFG[:pen_rod_x])
               .map { |rx| circle_loop(rx, CFG[:rod_z], CFG[:rod_hole_d]) }
    eye_h  = ring_pairs.map { |rx| circle_loop(rx, CFG[:ring_z], CFG[:ring_hole_d]) }
    drum_h = [circle_loop(CFG[:drum_x], CFG[:rod_z], CFG[:drum_shaft_d])]
    full   = [[x0, z1], [x1, z1], [x1, z0], [x0, z0]]

    [1, -1].each do |sgn|
      ya = sgn * ry
      yb = sgn * (ry + sd)
      yc = sgn * (ry + CFG[:rail_t])
      # inner slice carries the blind rod sockets and the screw-eye pilots
      finish(extrude_y(g.entities, full, ya, yb, rod_h + eye_h + drum_h),
             TAGS[4], mats["Wood"])
      # outer slice is solid but for the drum shaft, which passes right through
      finish(extrude_y(g.entities, full, yb, yc, drum_h),
             TAGS[4], mats["Wood"])
    end

    # box-frame end posts, between the rails, same stock
    [[x0, x0 + CFG[:post_w]], [x1 - CFG[:post_w], x1]].each do |px0, px1|
      post = g.entities.add_group
      box(post.entities, px0, -ry, z1, px1, ry, z0)
      finish(post, TAGS[4], mats["Wood"])
    end

    # screw eyes: hardware, not printed -- the cable passes through these
    ring_pairs.each do |rx|
      eye = g.entities.add_group
      lathe(eye.entities, [[0, -CFG[:ring_hole_d] / 2.0], [1.0, -CFG[:ring_hole_d] / 2.0],
                           [1.0, 6.0], [0, 6.0]], 10)
      eye.transform!(Geom::Transformation.translation(
        Geom::Vector3d.new(rx.mm, (ry - 6.0).mm, CFG[:ring_z].mm)))
      finish(eye, TAGS[5], mats["Steel"])
    end

    label(g.entities,
          format("1x2 pine, %.1f x %.1f -- faceplate screws to the rear face",
                 CFG[:rail_t], (z0 - z1).abs),
          Geom::Point3d.new(x0.mm, (ry + CFG[:rail_t] + 10).mm, z1.mm))
    g.name = "Rails and frame"
    g
  end

  def self.build_cable(ents, mats)
    g  = ents.add_group
    cz = CFG[:cable_z]
    ry = CFG[:rail_y] - 7.0        # where a ring hung from the rail sits

    dx  = CFG[:ring_dx]
    pts = [Geom::Point3d.new((CFG[:rail_x0] + 12).mm, ry.mm, cz.mm)]
    stations.each_with_index do |x, i|
      # down one leg, round the moving ring, back up the other -- both legs
      # parallel to the carriage's travel, so the take-up is exactly 2 x d
      pts << Geom::Point3d.new((x - dx).mm, ry.mm, cz.mm)
      pts << Geom::Point3d.new(x.mm, station_ring_y(i).mm, cz.mm)
      pts << Geom::Point3d.new((x + dx).mm, ry.mm, cz.mm)
    end
    pts << Geom::Point3d.new((CFG[:pen_x] + 34).mm, ry.mm, cz.mm)
    cab = g.entities.add_group
    cab.entities.add_edges(pts)
    cab.layer = TAGS[5]; cab.material = mats["Cable"]

    # screw-adjustable anchor -- this, and only this, sets the pen's ZERO
    anc = g.entities.add_group
    box(anc.entities, CFG[:pen_x] + 26, ry - 5, cz - 5,
                      CFG[:pen_x] + 40, ry + 5, cz + 5)
    finish(anc, TAGS[5], mats["Steel"])

    label(g.entities, "hand-made rings, drilled 1.4 -- travel = 2 x sum(r sin theta)",
          Geom::Point3d.new((CFG[:plate_x0] + 16).mm, (CFG[:rail_y] + 18).mm, cz.mm))
    g.name = "06 Cable"
    g
  end

  # Pen carriage: same language as the yokes -- a block on two guideposts,
  # locating groove one end, floating groove the other, a drilled ring for
  # the cable, and an arm reaching out to the drum.
  def self.build_pen(ents, mats)
    g   = ents.add_group
    x   = CFG[:pen_x]
    hw  = CFG[:yoke_w_sml] / 2.0
    hh  = CFG[:pen_h] / 2.0
    tt  = CFG[:yoke_t]
    yz0 = CFG[:yoke_z]
    yz1 = yz0 + tt
    zc  = (yz0 + yz1) / 2.0
    ew  = end_w(1)
    off = CFG[:rod_gap] / 2.0

    bw = CFG[:ballast_w] / 2.0
    bh = CFG[:ballast_h] / 2.0
    by = CFG[:ballast_y]
    pocket = [[x - bw, by - bh], [x + bw, by - bh],
              [x + bw, by + bh], [x - bw, by + bh]]
    body = extrude(g.entities,
                   [[x - hw + ew, -hh], [x + hw - ew, -hh],
                    [x + hw - ew,  hh], [x - hw + ew,  hh]],
                   [circle_loop(x, CFG[:pen_ring_y], CFG[:ring_hole_d]), pocket],
                   yz0, yz1)
    finish(body, TAGS[6], mats["PLA Part"])

    # ballast sits INSIDE the carriage -- a slug hung below it would foul the
    # bottom rail at full downward travel
    slug = g.entities.add_group
    box(slug.entities, x - bw + 0.4, by - bh + 0.4, yz0 + 0.4,
                       x + bw - 0.4, by + bh - 0.4, yz1 - 0.4)
    finish(slug, TAGS[6], mats["Steel"])

    [[-1, CFG[:groove_fit]], [1, CFG[:groove_free]]].each do |sgn, gr|
      blk = extrude_y(g.entities,
                      end_profile(sgn, hw, ew, gr, tt, off)
                        .map { |a, c| [x + a, zc + c] },
                      -hh, hh)
      finish(blk, TAGS[6], mats["PLA Part"])
    end

    # arm out to the drum, and the nib
    arm = g.entities.add_group
    box(arm.entities, x + hw - ew, -5.0, zc - 4.0,
                      x + hw + CFG[:pen_arm], 5.0, zc + 4.0)
    finish(arm, TAGS[6], mats["PLA Part"])
    nib = g.entities.add_group
    box(nib.entities, x + hw + CFG[:pen_arm] - 2, -1.6, zc - 1.6,
                      x + hw + CFG[:pen_arm] + 8, 1.6, zc + 1.6)
    finish(nib, TAGS[6], mats["Cable"])

    label(g.entities, "pen carriage -- 2:1 off the cable, ballast to 41 g all-up",
          Geom::Point3d.new((x - hw).mm, (hh + 10).mm, zc.mm))
    g.name = "07 Pen carriage"
    g
  end

  def self.build_drum(ents, motor_def, mats)
    g  = ents.add_group
    x  = CFG[:drum_x]
    r  = CFG[:drum_d] / 2.0
    cz = CFG[:rod_z]

    ri = CFG[:drum_id] / 2.0
    drum = g.entities.add_group
    lathe(drum.entities, [[ri, CFG[:drum_y0]], [r, CFG[:drum_y0]],
                          [r, CFG[:drum_y1]], [ri, CFG[:drum_y1]]], 48)
    finish(drum, TAGS[9], mats["Paper"])

    # the only printed parts of the drum: two caps that plug the bore,
    # centre it on the shaft and true up the ends
    [[CFG[:drum_y0], 1], [CFG[:drum_y1], -1]].each do |ye, dir|
      cap = g.entities.add_group
      lathe(cap.entities,
            [[CFG[:drum_shaft_d] / 2.0, ye],
             [r + 1.5, ye],
             [r + 1.5, ye + dir * 3.0],
             [ri - 0.3, ye + dir * 3.0],
             [ri - 0.3, ye + dir * CFG[:cap_deep]],
             [CFG[:drum_shaft_d] / 2.0, ye + dir * CFG[:cap_deep]]], 40)
      finish(cap, TAGS[9], mats["PLA Part"])
      cap.transform!(Geom::Transformation.translation(
        Geom::Vector3d.new(x.mm, 0, cz.mm)))
    end
    drum.transform!(Geom::Transformation.translation(
      Geom::Vector3d.new(x.mm, 0, cz.mm)))

    # shaft runs the full height, through both rails
    sh = rod_y(g.entities, x, cz, CFG[:drum_shaft_d] / 2.0 - 0.4,
               -(CFG[:rail_y] + CFG[:rail_t] + 2), CFG[:rail_y] + CFG[:rail_t] + 2, 14)
    finish(sh, TAGS[9], mats["Steel"])

    mt = Geom::Transformation.rotation(ORIGIN, X_AXIS, Math::PI / 2.0)
    mt = Geom::Transformation.translation(Geom::Vector3d.new(
           x.mm, (CFG[:rail_y] + CFG[:rail_t] + 4).mm, cz.mm)) * mt
    m = g.entities.add_instance(motor_def, mt)
    m.layer = TAGS[9]; m.material = mats["Motor"]
    m.name = "Drum drive"

    label(g.entities, "drum -- vertical axis, 1 rev / 7 days, 114 mm trace",
          Geom::Point3d.new((x - r).mm, (CFG[:drum_y1] + 8).mm, cz.mm))
    g.name = "10 Drum"
    g
  end

  def self.build_electronics(ents, uln_def, mats)
    g  = ents.add_group
    dz = ez(3)
    zb = CFG[:plate_t] + 30 + dz

    tray = g.entities.add_group
    box(tray.entities, -120, -66, zb, 150, -20, zb + 2.5)
    finish(tray, TAGS[7], mats["PLA Part"])

    6.times do |i|
      t = Geom::Transformation.translation(Geom::Vector3d.new(
            (-102 + i * 42).mm, -43.mm, (zb + 2.5).mm))
      b = g.entities.add_instance(uln_def, t)
      b.layer = TAGS[7]; b.material = mats["Board"]
      b.name = "ULN2003 ##{i + 1}"
    end

    esp = g.entities.add_group
    box(esp.entities, 96, -62, zb + 2.5, 146, -24, zb + 4.1)
    finish(esp, TAGS[7], mats["Board"])

    label(g.entities,
          format("ESP32 + 2x MCP23017 + 1 MOSFET on the common 5 V rail\n" \
                 "PWM hold %.0f%%  =  %.1f mN.m,  %.2f W for all six",
                 CFG[:hold_duty] * 100, CFG[:motor_mNm] * CFG[:hold_duty],
                 6 * 2 * ((0.080 * CFG[:hold_duty]) ** 2) * 50),
          Geom::Point3d.new(-118.mm, -78.mm, zb.mm))
    g.name = "08 Electronics tray"
    g
  end

  # =========================================================================
  #  MAIN
  # =========================================================================

  def self.build!
    model = Sketchup.active_model
    model.start_operation("Build Tide Machine (Rev D)", true)

    old = model.entities.select { |e| e.is_a?(Sketchup::Group) && e.name == "TIDE MACHINE" }
    model.entities.erase_entities(old) unless old.empty?

    TAGS.each { |n| model.layers.add(n) }
    mats = {}
    PALETTE.each do |name, rgb|
      m = model.materials[name] || model.materials.add(name)
      m.color = Sketchup::Color.new(*rgb)
      mats[name] = m
    end

    motor_def  = def_motor(model)
    uln_def    = def_uln(model)

    root = model.entities.add_group
    root.name = "TIDE MACHINE"
    e = root.entities

    build_stations(e, motor_def, mats)
    build_rods(e, mats)
    build_rails(e, mats)
    build_plate(e, mats)
    build_cable(e, mats)
    build_pen(e, mats)
    build_drum(e, motor_def, mats)
    build_electronics(e, uln_def, mats)

    model.commit_operation
    model.active_view.zoom_extents

    sum  = CFG[:amp].inject(:+) * CFG[:pin_scale]
    hold = CFG[:motor_mNm] * CFG[:hold_duty]
    pw   = 6 * 2 * ((0.080 * CFG[:hold_duty]) ** 2) * 50
    puts "-" * 74
    puts "TIDE MACHINE  Rev G  --  direct drive, PWM hold"
    printf("  cable tension %.2f N  ->  %.2f N at each carriage\n",
           CFG[:tension_n], 2 * CFG[:tension_n])
    printf("  %-4s %8s %8s %8s %8s %10s %9s\n",
           "ring", "r_pin", "disc_r", "yoke_w", "slot", "load", "margin")
    CFG[:sym].each_with_index do |s, i|
      printf("  %-4s %8.1f %8.1f %8.1f %5.1f/%-3.0f %7.2f mNm %8.1fx%s\n",
             s, r_pin(i), disc_r(i), yoke_w(i),
             slot_need(i), slot_len(i), load_mNm(i), margin(i),
             CFG[:slotted][i] ? "  (slot)" : "  (pin printed in)")
    end
    printf("  sum r      : %.1f mm   cable end +/-%.0f mm  ->  pen travel %.0f mm\n",
           sum, 2 * sum, 2 * sum)
    printf("  chart      : %.1f mm per metre of tide\n", CFG[:pin_scale])
    printf("  drill      : %.1f mm shaft clearance, 2x M3 per motor\n",
           shaft_clear)
    printf("  shaft grip : %.1f mm of the %.1f mm available%s\n",
           CFG[:disc_t] + CFG[:plate_t] + boss_proud,
           8.0, boss_proud > 0.1 ? "  (hub counterbored)" : "")
    printf("  rails      : 1x2 pine %.2f x %.1f, %.0f long, 2 end posts\n",
           CFG[:rail_t], (CFG[:rail_z0] - CFG[:rail_z1]).abs,
           CFG[:rail_x1] - CFG[:rail_x0])
    printf("  plate screw: %d per rail at y=%.1f, %.0f mm pitch\n",
           screw_xs.length, screw_y, CFG[:screw_pitch])
    printf("  faceplate  : %.0f x %.0f x %.1f mm\n",
           CFG[:plate_x1] - CFG[:plate_x0],
           CFG[:plate_y1] - CFG[:plate_y0], CFG[:plate_t])
    printf("  PWM hold   : %.0f%%  =  %.1f mN.m,  %.2f W for all six motors\n",
           CFG[:hold_duty] * 100, hold, pw)
    printf("  explode    : %.2f\n", CFG[:explode])
    puts "-" * 74
    root
  rescue StandardError => err
    model.abort_operation
    puts "BUILD FAILED: #{err.message}"
    puts err.backtrace.first(6)
    nil
  end
end

TideMachine.build!

# ---------------------------------------------------------------------------
#  NOTES FOR REV D
#
#  THE PEN SETS THE CRANK SIZE. Every torque number here follows from the
#  0.20 N cable tension, and pen drag is the dominant term in that budget.
#  Hence the counterbalance on the pen carriage: its contact force is a
#  DESIGNED number set by a small weight, not whatever a spring happens to
#  give. Hang a heavier pen on this and :pin_scale has to come down.
#
#  DIRECT DRIVE. The crank disc presses straight onto the 28BYJ-48's output
#  shaft, motor coaxial behind the plate. Gone from Rev C: five pinions,
#  five toothed rims, all mesh adjustment, all gear backlash, and the motor
#  offset -- which alone shortened the plate from 300 mm to 180 mm.
#  Peak load at M2 is 2 x 0.20 N x 35 mm = 14 mN.m against 34.3 rated: 2.4x.
#
#  PWM HOLD. Holding torque scales with current, heat with current squared,
#  so topping up the gearbox is nearly free. One N-channel MOSFET in the
#  motors' common 5 V rail, one ESP32 PWM channel:
#      idle   -> PWM at :hold_duty (60% = 20.6 mN.m, 1.38 W for all six)
#      step   -> rail to 100% for ~30 ms, step, back to PWM
#  Collisions are harmless; two motors stepping at once both get full rail.
#  Tune :hold_duty DOWN once you have measured the unpowered holding torque.
#
#  SMALL CRANKS PRINT THEIR PIN IN. K1 at 3.5 mm and O1 at 2.45 mm are too
#  small for a usable adjustment slot, so those two discs carry the pin at a
#  printed-in radius (:slotted). That is more accurate than a slot anyway --
#  amplitude gets set once from your port's constituents and never touched.
#  Re-print the disc if you change ports.
#
#  TWO CARRIAGE CLASSES. M2 needs 73 mm of slot and 93 mm of carriage; the
#  other four all fit inside S2's 20.5 mm, so they share one 40 mm part with
#  a 22 mm slot. A slot longer than a crank needs costs nothing -- it only
#  constrains vertically, so the pin just sweeps less of it -- which is why
#  four different cranks can share one carriage. Two STLs, printed 1 and 4.
#  Station pitch follows from the widths, not a fixed number: 74.5 mm from
#  M2 to S2, then 48 mm between the small ones. Plate 427 x 175.
#
#  CARRIAGE SECTION. Webs above and below the slot are each 1 x slot height
#  (6 mm), so the whole carriage is 18 mm tall and 12 mm thick. At 0.4 N of
#  cable load that is enormously overbuilt; it is thin because there is no
#  reason for it to be thick.
#
#  RAIL DRILLING, AND WHY THE TWO RAILS ARE MIRROR IMAGES. Both rails carry
#  identical features at identical (x, z), but each is drilled on its INNER
#  face -- the one that looks at the other rail. Laying the top rail
#  inner-face-up turns it over, so with the rear edge toward you on both,
#  machine x runs left-to-right on one rail and right-to-left on the other.
#  Drill both from one template and the second rail is scrap. faceplate.py's
#  sibling rails.py emits a separately named template per rail.
#
#  If you want them paired anyway, there is a clamping trick that gets the
#  hand right for free: clamp them OUTER face to outer face, rear edges flush
#  and ends flush, then drill each rod position from both sides of the stack
#  to 9 mm. Both inner faces then carry the same (u from the end, w from the
#  rear edge) -- and because seating each rail in the machine means rotating
#  it about its transverse axis, the same physical end lands at OPPOSITE ends
#  of the machine. That is exactly the mirror the templates draw.
#
#  Rod spacing and parallelism therefore come from that one drilling session
#  rather than from a print, which is the alignment problem the carriages'
#  locate/float grooves were there to survive. Keep the float groove anyway;
#  it costs nothing and now absorbs drilling slop instead of print error.
#
#  RAILS IN WOOD -- AND 1x1 IS TOO SHALLOW. The rail has to span from the
#  faceplate at z=0 forward to the cable rings at z=-30, with the rod sockets
#  at z=-20 in between; the rings must sit FORWARD of the rods or the cable
#  fouls them. That needs |ring z| + an edge margin = 30 + 4 = 34 mm of depth.
#  A 25.4 mm section leaves 2.8 mm of wood ahead of the rod socket and puts
#  the ring 4.6 mm off the front face entirely.
#
#  1x2 PINE (19.05 x 38.1 actual) is the answer: 15.5 mm of wood ahead of the
#  rod socket, 8.1 mm ahead of the ring, a 9 mm socket leaving 10.1 mm behind
#  it, and it is the cheapest, most available stock there is. 1x1.5 hardwood
#  works identically if you want it prettier.
#
#  NO LIP. The faceplate simply screws to the rails' rear faces -- it overlaps
#  them by 12 mm, which is a comfortable landing for a #6 wood screw. Pilot
#  2 mm into the pine, 3.5 mm through the sheet, and the console prints the
#  pattern. Pilot holes are not modelled; you drill them on assembly.
#
#  THE RINGS BECOME SCREW EYES. A closed loop that threads into wood is the
#  right part here, and far better than drilling 1.4 mm through 19 mm of pine.
#  The carriages keep their drilled holes and hand-made rings -- those are PLA.
#
#  THE DRUM SHAFT now runs in a 7 mm hole through the wood. Pine is a passable
#  plain bearing at one revolution a week, but a brass bushing or a scrap of
#  PTFE tube costs nothing and will not wear oval.
#
#  SHEET METAL, 1.5 mm, AND THE MOTOR PICKS THAT NUMBER TOO. The boss is
#  1.5 mm tall, so a 1.5 mm plate buries it exactly: the boss sits inside the
#  clearance hole and the shaft emerges right at the plate's front face with
#  all 8.0 mm of it forward. No hub counterbore, hub OD back to 11, and the
#  clearance hole only has to pass the boss (10.0) rather than the hub.
#
#  1.5 mm aluminium is also about 2.9x stiffer in bending than the 3 mm
#  acrylic it replaces (E.t^3: 69 x 1.5^3 vs 3 x 3^3), it drills and taps
#  without cracking, needs no nylon washers, and gives the motors a ground
#  plane. What it costs is the translucency -- you could see the mechanism
#  through the acrylic, and now you cannot.
#
#  Go thinner than 1.5 and the boss stands proud of the plate; :boss_proud
#  computes that and the hub grows a counterbore automatically. Go thicker
#  and you simply lose shaft, millimetre for millimetre.
#
#  THE SHAFT BUDGET IS THE TIGHTEST THING IN THE MACHINE. A 28BYJ-48 gives
#  9.5 mm past its mounting face, but the first 1.5 mm of that is a 9 mm boss,
#  so there are only 8.0 mm of 5 mm shaft. Bolted flat, the face sits at z=+3,
#  so the boss occupies z [+1.5,+3] and the shaft z [-6.5,+1.5] -- which
#  leaves 6.5 mm of shaft forward of the plate.
#
#  An earlier hub ran z [-3,+3] with a 5 mm bore, driving it straight into the
#  boss; real engagement was 4.5 mm, not the 6 it looked like. Now the bore
#  runs through the DISC as well, z [-9,+1.5], and the hub is counterbored
#  :boss_d over the last :boss_l to clear the boss -- which also registers
#  the disc concentrically on it. Grip: 8.0 mm, every millimetre there is.
#
#  Knock-ons: hub OD went 11 -> 13, because 0.75 mm of wall over a 9.5 mm
#  counterbore is not a wall; and the plate clearance hole 12.5 -> 14.
#  Strength was never the issue -- 14 mN.m on two flats over 8 mm is 0.12 MPa.
#  Axial retention is not either: the yoke slot loads the pin only along Y,
#  so nothing pulls the disc off. A grub screw on a flat is ample.
#
#  THE HOME FLAG IS A RECESS, NOT A TAB. The rims are close: only 3.25 mm
#  between M2's and S2's discs, 3.90 between S2 and N2. Anything protruding
#  radially sweeps a full circle and would strike its neighbour. So the disc
#  body stops :flag_band (3 mm) short of the OD and that last ring of rim is
#  printed at :flag_t (2 mm) instead of 6, with a :notch_deg (12 deg) gap in
#  it. Nothing sticks out; the sensor's 3 mm slot straddles the 2 mm band.
#
#  IT PRINTS WITH NO SUPPORT. The disc lies flat on the bed, so the thinned
#  rim is simply a step down in layer height and the notch is a vertical-
#  walled gap -- both come off clean. Keep the band on the REAR face (the
#  z1 side) so the front stays clear for the arm and pin.
#
#  THE NOTCH IS CENTRED ON THE PIN, which makes the flag-to-pin angle exact
#  by construction rather than something to calibrate. Time the edge the
#  band presents as it enters the beam, always approaching in the running
#  direction -- the machine only ever turns one way, so sensor hysteresis and
#  gearbox backlash both land as one constant offset.
#
#  SENSOR AT 12 O'CLOCK, every station the same. The sides are congested --
#  neighbouring discs at 3 and 9 o'clock, guide rods just beyond them -- but
#  straight up there is 23 mm of clear space above even M2's rim, and the
#  carriages live at z -26..-14 while the bracket occupies 0..-7. Bolt the
#  bracket to the plate's front face and slot its mounting holes radially, so
#  one bracket design serves all five discs despite their different radii.
#
#  DO NOT PRINT THE DRUM. 3" Schedule 40 PVC has an outside diameter of
#  88.9 mm -- within a millimetre of the 90 mm the drum wanted, so the tube
#  is simply the right part. Print only the two END CAPS: each plugs the
#  77.9 mm bore, carries the 7 mm shaft and trues up the cut end. About 30 g
#  of PLA and forty minutes, against 250 g and most of a day for a printed
#  drum that would be rounder only by luck.
#
#  A 130 mm length of Sch 40 weighs about 260 g. That is nothing to the
#  motor (total drum torque is around 4 mN.m against 34.3 available) but it
#  is a real thrust load on the lower rail, so put a washer under the bottom
#  cap. Cut the tube square -- a drum that wobbles moves the pen in and out
#  and modulates its contact force.
#
#  PAPER: circumference is 279.3 mm, so an A4 sheet wrapped the long way
#  gives 17.7 mm of overlap to tape. Trim the 210 mm dimension down to about
#  140 to match the drum height.
#
#  CHART SPEED IS A FIRMWARE CHOICE, and it is worth thinking about. At one
#  revolution per 7 days you get 39.9 mm/day, which is only 20.6 mm per tidal
#  cycle against up to 102 mm of vertical swing -- a very steep trace. One rev
#  per 3.5 days gives 41.3 mm per cycle and a far more classical marigram, at
#  the cost of 17 sheet changes over a 60-day run instead of 9. Going to 4"
#  PVC (OD 114.3) is the other lever: 26.5 mm per cycle at the weekly speed.
#
#  THE DRUM HANGS OFF THE RAILS TOO. Its 7 mm shaft passes through a hole at
#  (:drum_x, :rod_z) in both rails -- clearance through the top one on its way
#  to the motor above, a plain bearing in the bottom one. Same printed part,
#  no extra bracket, and the drum sits between the rails rather than towering
#  over the machine the way it did before the 2:1 halved the pen travel.
#
#  THE PEN IS THE SIXTH STATION. It closes up against O1 with the same 2 mm
#  gap the yokes use, and shares rod 5 with it -- float groove for O1, locating
#  groove for the pen -- so the whole run of six carriages is one continuous
#  pattern and only ONE extra rod is needed, at x = 181. Seven rods total.
#  The drum follows the pen in: axis at x = 250, its surface meeting the nib
#  at the end of a 25 mm arm.
#
#  THE PEN SWINGS FURTHER THAN ANY CRANK, NECESSARILY. It carries the SUM, so
#  its range is sum(r) = 57.05 mm against M2's 35.00 -- a ratio of
#  sum(A)/A_M2 = 1.630. They cannot be made to line up; that mismatch IS the
#  summation. Over a real 60-day run the pen actually reaches +56.6/-53.5 mm,
#  so the theoretical bound is barely conservative and there is no headroom
#  to reclaim by sizing to the realistic excursion instead.
#
#  WHICH IS WHY THE CARRIAGE IS 16 mm, NOT 20, AND THE BALLAST IS INTERNAL.
#  At 16 mm the carriage tops out at 65.1 mm against a rail face at 70.0.
#  A counterweight hung below it would reach -80.1 mm and foul the bottom
#  rail by 10 mm at full downward travel. The 41 g goes in a pocket inside
#  the body instead: part-fill with lead shot and cap with epoxy, then check
#  it on a kitchen scale. All-up mass is the spec, not the pocket volume.
#
#  THE PEN'S ZERO IS SET BY CABLE LENGTH, NOTHING ELSE. Mean sea level on the
#  chart is where the pen sits when every carriage is at mid-travel, and that
#  depends entirely on how long the cable is. Hence the screw-adjustable
#  anchor at the dead end -- it is the physical form of Z0 from the
#  spreadsheet, and it is the one thing that does have to be aligned.
#
#  BOTH CABLE LEGS MUST BE PARALLEL TO THE CARRIAGE'S TRAVEL. A moving ring
#  gives exactly 2 x d of take-up only when the two legs leave it along the
#  direction the carriage slides. If they splay at angle a, the take-up is
#  2 x d x cos(a) -- and a changes as the carriage moves, so the gain is not
#  even constant. An earlier routing put ONE rail ring between each pair of
#  stations, which splayed M2's legs by 58 and 35 mm and swung its gain from
#  0.78 to 1.77 instead of a flat 2.00. That is not a small error; the trace
#  would simply have been wrong.
#
#  The fix is two rail rings per station, straddling it by :ring_dx = 6 mm so
#  both legs run vertically. Residual error is then 0.58% of the trace, against
#  12.4% from harmonic truncation -- irrelevant. Twelve rail rings, not five.
#
#  THE CONSEQUENCE FOR LAYOUT is worth knowing: everything BETWEEN stations now
#  runs fixed ring to fixed ring, and the distance between two fixed points
#  never changes. So the cable can take any path it likes between stations --
#  horizontal, diagonal, round a corner -- and contribute nothing to the sum.
#  Station order, spacing and position are all free. Only the local geometry
#  at each moving ring matters.
#
#  THE PEN IS A MOVING RING, NOT A CABLE END. The cable wraps a ring on the
#  pen carriage and terminates at a fixed anchor on the rail, so the pen
#  travels HALF the cable end: 114 mm instead of 228. That is the only way it
#  fits -- the rails are 140 mm apart, and a 16 mm carriage leaves 124 mm of
#  usable stroke. Chart scale becomes :pin_scale exactly, 35 mm per metre of
#  tide: 102 mm for a spring range, 53 mm for a neap. The price is a halved
#  trace; the alternative is moving the rails to +/-130 and building a 280 mm
#  tall machine for the same information.
#
#  DEAD WEIGHT, NOT A SPRING, AT BOTH ENDS. A spring's force varies with
#  extension, which would vary cable tension over the stroke and therefore
#  vary every crank torque. A hanging weight is constant. 20 g at the take-up
#  end sets tension at 0.20 N; the pen carriage then needs 41 g to balance
#  the 2T the wrap puts on it. Build that into the carriage as a brass slug.
#
#  PEN CONTACT FORCE IS SEPARATE. It acts in Z, against the drum, and should
#  stay independent of the travel mechanism -- a light leaf spring or a small
#  pivoted arm, about 0.05 N. Add a manual lever that retracts the nib for
#  sheet changes; you will be doing that weekly.
#
#  BLIND ROD SOCKETS. The rod holes stop at the lip layer -- 9 mm deep, 1.8
#  diameters of engagement, which is ample for a guide carrying a fifth of a
#  newton. The 3 mm cap layer above them carries only the ring holes, so
#  nothing protrudes through the top or bottom faces and the rails read as
#  solid bars. Rod length is therefore socket-bottom to socket-bottom: 158 mm.
#  Cut them a whisker under and let them sit; do not force them home, or the
#  socket walls will split along the layer lines.
#
#  RAIL SECTION. 1x2 pine, 38.1 deep x 19.05 thick, 470 long, one piece --
#  no lap joints, which is most of the reason to be in wood at all. It does
#  four jobs: lands the faceplate on its rear face, holds the rod ends in
#  blind sockets, carries the twelve screw eyes that replace the fixed
#  pulleys, and ties the frame together through two end posts.
#
#  PLATE THICKNESS IS A SHAFT DECISION, NOT A STIFFNESS ONE. Stiffness was
#  never the constraint: the plate spans only 158 mm between rails and carries
#  about 250 g of motors. Through-bolt the motors, two M3 each.
#
#  PIN AND SLOT MUST MATCH. The slot height IS the kinematic fit -- whatever
#  clearance is in there is pure backlash in the trace, reversing twice per
#  revolution. An earlier revision carried a 3 mm pin in a 6 mm slot, i.e.
#  3 mm of lost motion on a 114 mm trace -- 2.6% of it. Now a 5 mm pin in
#  a 5.2 mm slot, which
#  also lets the pins come off the same stock as the guide rods.
#
#  SIX RODS, NOT TEN. Each rod sits in the 2 mm gap between two neighbouring
#  carriages and serves both: it is the LOCATING groove for the carriage on
#  its right and the FLOATING groove for the one on its left. Station pitch
#  is therefore hw(i) + hw(i+1) + :rod_gap, not a free choice. Halves the
#  number of rod mounts you have to get right.
#
#  DIMPLES, NOT A PRINTED HOLE. The upper web prints in three slices so the
#  2.6 mm centring dimples on the front and back faces are real recesses with
#  solid material between. Drill through by hand -- a 1.4 mm bit clears
#  paper-clip wire with enough slop for the ring to pivot.
#
#  GROOVE PLANE. The rods are vertical, so each groove must run the FULL
#  height of the carriage -- it is a half-cylinder about Y, not a notch in
#  the XY outline. The end blocks are therefore drawn in XZ and extruded
#  along Y, while the two webs are drawn in XY and extruded along Z. An
#  earlier revision cut the groove in the wrong plane, so the rod only
#  touched the carriage near mid-height and the engagement moved as the
#  carriage travelled.
#
#  PRINT UPRIGHT, standing on the 96 x 12 footprint, 15.6 mm tall, so the
#  end grooves run vertically and come off the printer as clean bearing
#  surfaces -- they are the only surfaces here that matter. The cost is the
#  slot: its top wall then bridges the full slot length, so turn on support
#  inside the slot. It is a through-window open at both ends, so the support
#  lifts straight out, and a fine flat needle file cleans what is left.
#
#  ROD GROOVES -- ONE LOCATES, ONE FLOATS. The LEFT groove is a close fit
#  (:groove_fit, 0.1 mm on a 5 mm rod) and does the constraining. The RIGHT
#  groove is deliberately loose (:groove_free, 0.8 mm) and only resists
#  rotation. That is the standard printer/plotter arrangement, and it means
#  the two rods at a station DO NOT have to be parallel: skew is absorbed by
#  the floating side instead of binding the carriage. Build accuracy stops
#  mattering. Both grooves print with vertical walls -- no bridging, no
#  support. Drop the carriage in before the rod tops are fixed.
#
#  The grooves constrain X and rotation; they do not positively capture in Z.
#  Nothing pushes the carriage in Z -- the cable is in-plane and the crank pin
#  is a Z-axis cylinder that simply slides in the slot -- so the close groove
#  plus the pin is enough in service. Add a printed strap across the grooves
#  if you want it captive for handling.
#
#  LUBRICATION. Light mineral oil (sewing machine oil) is chemically inert to
#  PLA and takes PLA-on-steel from about mu 0.25 dry to 0.1, which drops total
#  guide drag across all five carriages from ~0.22 N to ~0.09 N -- most of the
#  way back inside the 0.20 N tension budget the torque figures rest on.
#  Oil collects lint over a 60-day run; wipe and re-oil the rods if the pen
#  starts to feel notchy.
#
#  RING, NOT A PULLEY. The :ring_hole is 1.4 mm -- paper-clip wire plus
#  0.2 mm, so the ring can pivot without slopping. It takes a hand-made
#  ring; the line passes THROUGH that ring, never ties to the carriage --
#  the 180 degree wrap is what turns a displacement d into 2d of take-up.
#  A sliding ring costs capstan friction the way a roller would not, so if
#  the pen ever feels notchy or direction-dependent, that is where it is
#  coming from.
#
#  YOKE CONVENTION. Horizontal slot, vertical travel, so each station gives
#  r*sin(theta), not r*cos(theta). Folded into the phase constants in
#  firmware. Do not forget it.
#
#  CABLE. Fluorocarbon monofilament, ~0.3 mm. At 0.20 N that is about 1% of
#  breaking strength, so creep over sixty days is under a millimetre, and
#  elastic stretch is a constant offset absorbed in the pen zero. Nylon is
#  the same price and wrong: it absorbs moisture and wanders with humidity.
#  Terminate with crimp sleeves, not knots -- mono will not hold a knot.
#
#  IF THE ULN2003 DROP BITES. The Darlington eats ~1 V of the 5 V rail, which
#  is 20% of your driving torque. If steps look marginal at M2, swap to
#  logic-level MOSFETs for a free ~22% before touching anything else.
#
#  TO RESIZE: each moving ring doubles its carriage's displacement, so the
#  cable end swings +/- 2 x sum(r); the ring on the PEN carriage then halves
#  it again, so FULL PEN TRAVEL = 2 x sum(r) = 3.26 x :pin_scale, and the
#  chart scale is :pin_scale mm per metre of tide exactly.
#
#  Peak M2 torque = 2 x :tension_n x :pin_scale, and that fights the travel.
#  :pin_scale = 35 balances them: 2.4x torque margin, a 114 mm marigram on a
#  130 mm drum, and the whole pen stroke inside the 140 mm rail gap.
#
#  After changing it, re-derive :x from the new carriage widths (pitch is
#  hw(i) + hw(i+1) + :rod_gap), then :rod_x from the carriage faces and
#  :pen_x from O1's right face. The rail ring positions follow automatically
#  from :ring_dx. Check the console table: :slot_need must stay under the
#  class :slot_len for every station.
# ---------------------------------------------------------------------------

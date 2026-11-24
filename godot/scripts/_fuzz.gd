extends Node
# test: random driving from many spots; logs anything physically odd
var m; var t = 0.0; var seg_t = 0.0; var rng = RandomNumberGenerator.new(); var last = Vector3.ZERO; var lh = 0.0
var airn = 0; var stall = 0.0; var stats = {}; var spot = 0; var spots = []; var hist = []; var stuck_at = {}
func note(k: String, s: String):
	stats[k] = stats.get(k, 0) + 1
	if stats[k] <= 6: print("BUG %s t%.1f spot%d %s" % [k, t, spot, s])
func _ready():
	m = get_parent(); rng.seed = int(OS.get_environment("SEED")) if OS.get_environment("SEED") != "" else 3
	for r in Traffic.RUNS:
		var p = m.roads[r[0]]
		for i in range(r[1] + 5, r[2] - 5, 25): spots.append([r[0], i])
	_next()
func _next():
	var s = spots[spot % spots.size()]; m.spawn(s[0], s[1]); seg_t = 0.0; last = Vector3(m.car.px, m.car.py, m.car.pz); lh = m.car.hd
func _physics_process(dt):
	t += dt; seg_t += dt; var c: Car = m.car
	if int(seg_t * 2) != int((seg_t - dt) * 2):      # new random input every 0.5 s
		m.touch.gas = rng.randf() < 0.75; m.touch.brake = rng.randf() < 0.12; m.touch.hand = rng.randf() < 0.1
		var st = rng.randf(); m.touch.left = st < 0.25; m.touch.right = st > 0.75
	var p = Vector3(c.px, c.py, c.pz)
	if not (c.speed < 0.5 and m.touch.gas and not m.touch.brake): stall = 0.0
	if not (is_finite(c.px) and is_finite(c.py) and is_finite(c.vx) and is_finite(c.yr)): note("NAN", str(p))
	var jump = Vector2(p.x - last.x, p.z - last.z).length()
	if jump > c.speed * dt * 1.6 + 0.6 and seg_t > 0.1: note("TELEPORT", "%.1f m in one frame to %s from %s, surf %s, history %s" % [jump, p, last, c.surf, str(hist.slice(-6))])
	hist.append("%s/%s/y%.1f" % [c.surf, "air" if c.air else "gnd", c.py]); if hist.size() > 40: hist.pop_front()
	if abs(wrapf(c.hd - lh, -PI, PI)) > 0.25: note("YAWSNAP", "%.2f rad in one frame v%.0f at %s" % [wrapf(c.hd - lh, -PI, PI), c.speed * 3.6, p])
	var g = c.ground(c.px, c.pz, c.py + 3.0)
	if not c.air and g[0] > -50 and c.py < g[0] - 0.4: note("SUNK", "%.2f m under ground at %s" % [g[0] - c.py, p])
	if abs(c.vy) > 25: note("VY", "vy %.1f at %s" % [c.vy, p])
	if c.speed > 95: note("OVERSPEED", "%.0f km/h at %s surf %s" % [c.speed * 3.6, p, c.surf])
	if abs(c.yr) > 6: note("SPIN", "yaw rate %.1f at %s v%.1f vf%.1f surf %s gas %s brake %s hand %s steer %.1f delta %.2f beta %.2f air %s" % [c.yr, p, c.speed, c.vf, c.surf, m.touch.gas, m.touch.brake, m.touch.hand, c.in_steer, c.delta_, c.beta, c.air])
	if abs(c.roll) > 0.7 or abs(c.pitch) > 0.8: note("TILT", "pitch %.2f roll %.2f at %s" % [c.pitch, c.roll, p])
	if c.air and seg_t > 0.5: stats["air_frames"] = stats.get("air_frames", 0) + 1; airn += 1
	elif airn > 0:
		var k = "air_1-3f" if airn <= 3 else ("air_4-12f" if airn <= 12 else "air_long"); stats[k] = stats.get(k, 0) + 1
		if airn <= 3 and stats[k] <= 4: print("BUG MICROAIR %d frames at %s v%.0f" % [airn, p, c.speed * 3.6])
		airn = 0
	if c.speed < 0.5 and m.touch.gas and not m.touch.brake and seg_t > 3:
		stall += dt
		if stall > 2.0 and stall - dt <= 2.0:
			var gA = c.ground(c.px + sin(c.hd) * 2.0, c.pz + cos(c.hd) * 2.0, c.py + 3.0); var cs = m.coll.road_query(c.px, c.pz, c.py)
			note("STALL", "at %s surf %s gear %d rpm %d pitch %.2f roll %.2f ground 2m ahead dy %.2f, road %s, spin %s air %s vf %.2f" % [p, c.surf, c.gear + 1, c.rpm, c.pitch, c.roll, gA[0] - c.py, "d=%.1f" % cs.d if cs.ok else "none", c.spin, c.air, c.vf])
		stats["stuck_frames"] = stats.get("stuck_frames", 0) + 1; var k = "%d,%d" % [int(c.px / 10) * 10, int(c.pz / 10) * 10]; stuck_at[k] = stuck_at.get(k, 0) + 1
	last = p; lh = c.hd
	if seg_t > 25.0: spot += 1; _next()
	if t > float(OS.get_environment("FUZZT")) if OS.get_environment("FUZZT") != "" else 300.0:
		print("STUCK at ", stuck_at)
		print("FUZZ done %.0fs, %d spots, stats %s" % [t, spot, str(stats)]); get_tree().quit()

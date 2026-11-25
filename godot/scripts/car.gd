extends Node3D
class_name Car
# Port of the web game's car model (index.html drive/physics): single-track tyre model, automatic gearbox,
# traction control, drift assist. World plane is xz, heading h: forward = (sin h, cos h).

var V = { m = 1380.0, Iz = 2350.0, a = 1.46, b = 1.26, h = 0.47, r = 0.345, B = 11.5, Br = 14.5, C = 1.42, mu = 1.15, muF = 0.96, muR = 1.10,
	dmax = 0.66, lockD = 0.87, sigma = 0.45, gears = [3.20, 2.28, 1.74, 1.38, 1.12, 0.92], fd = 3.70, eff = 0.88, idle = 950.0, red = 8100.0,
	up = 7600.0, down = 3300.0, brake = 1.18, bias = 0.63, cda = 0.40, down_ = 0.10, rr = 0.012, tqPeak = 660.0, tqRpm = 5900.0 }
const MU := { road = 1.0, dirt = 0.82, grass = 0.74, sand = 0.62, snow = 0.52 }          # off the asphalt: less grip, but still a car you can steer
const RRS := { road = 1.0, dirt = 2.5, grass = 10.0, sand = 13.0, snow = 6.0 }

# input (set by the HUD): steer -1..1 (left negative), gas, brake 0..1, hand bool
var in_steer = 0.0; var in_gas = 0.0; var in_brake = 0.0; var in_hand = false
var assist = true
var tc = true            # traction control in grip driving (player option)
var sens = 1.0           # steering sensitivity: speed and reach of the wheels for an input (player option)
var manual = false       # manual gearbox: gears change only by shift() (player option)
func shift(d: int):
	if not manual or shiftT > 0.0: return
	var g = gear + d
	if g < 0 or g > V.gears.size() - 1: return
	if d < 0:          # no downshift that would throw the engine far past the red line
		var wr = abs(vf) / V.r * 9.5493 * V.gears[g] * V.fd
		if wr > V.red + 400.0: return
	gear = g; shiftT = 0.16 if d > 0 else 0.1

var px = 0.0; var py = 0.0; var pz = 0.0; var hd = 0.0; var vx = 0.0; var vz = 0.0; var vy = 0.0; var yr = 0.0
var delta_ = 0.0; var st_in = 0.0; var thr = 0.0; var brk = 0.0; var af = 0.0; var ar = 0.0; var axf = 0.0; var ayf = 0.0
var gear = 0; var rpm = 950.0; var shiftT = 0.0; var spin = false; var drift = 0.0; var pwr = 0.0; var pb = 0.0
var beta = 0.0; var air = false; var pitch = 0.0; var roll = 0.0; var speed = 0.0; var vf = 0.0; var surf = "road"
var safe = Vector4.ZERO; var safe_t = 0.0
var mu_s = 1.0
signal knocked(o)
signal crashed
var coll: Coll
var bump_t := 0.0
var body: Node3D; var wheels = []; var wheel_spin = 0.0; var rear_spin = 0.0

const CARS = {
	vortex = { name = "Vortex", file = "res://assets/vortex.glb", far = "res://assets/vortex_far.glb", mid = "res://assets/vortex_mid.glb", paint = ["paint"], half = Vector2(2.3, 1.0), yaw = PI, axis = "x", sgn = -1.0, blurb = "Mid-engine hypercar. Light, sharp, drifts on command.",
		veh = { m = 1380.0, Iz = 2350.0, a = 1.46, b = 1.26, h = 0.47, r = 0.345, gears = [3.20, 2.28, 1.74, 1.38, 1.12, 0.92], fd = 3.70, red = 8100.0, up = 7600.0, down = 3300.0, tqPeak = 660.0, tqRpm = 5900.0, cda = 0.40, dmax = 0.66 } },
	calder = { name = "Calder GT", file = "res://assets/calder.glb", far = "res://assets/calder_far.glb", mid = "res://assets/calder_mid.glb", paint = ["Paint_Body", "Paint"], half = Vector2(2.4, 1.0), yaw = 0.0, axis = "z", sgn = -1.0, blurb = "Front-engine V8 grand tourer. Heavier, long and stable; big, slow drifts.",
		veh = { m = 1650.0, Iz = 3550.0, a = 1.38, b = 1.49, h = 0.48, r = 0.35, gears = [3.00, 2.10, 1.60, 1.28, 1.03, 0.84], fd = 3.30, red = 7200.0, up = 6800.0, down = 3000.0, tqPeak = 640.0, tqRpm = 5200.0, cda = 0.38, dmax = 0.62 } } }
var car_id = "vortex"; var spin_axis = "x"; var spin_sgn = -1.0
const EYE = { vortex = Vector3(0.0, 0.21, -0.5), calder = Vector3(0.0, 0.34, -0.52) }          # driver's eyes from the steering wheel centre (the Vortex roof is low)
const STEER_SIGN = { vortex = 1.0, calder = 1.0 }          # which way the steering wheel model turns for a left turn
var opts = {}            # race rivals: { far = true (light model beyond FAR_AT), paint = Color }
var frozen = false       # race countdown: the car holds still on the grid
var player = false       # the player's car: its upgrades and paint come from the career save
const NEAR_TO = 12.0; const MID_TO = 45.0      # rivals: full model, then ~45k, then ~16k triangles

func _ready(): setup(car_id, opts)

func setup(id: String, o := {}):
	car_id = id; opts = o; var C = CARS[id]
	for k in C.veh: V[k] = C.veh[k]
	if player: Progress.load_save(); Progress.tune(id, V)
	spin_axis = C.axis; spin_sgn = C.sgn; wheels = []
	if body: body.queue_free()
	var s = load(C.file).instantiate()
	body = Node3D.new(); add_child(body); body.add_child(s); s.rotation.y = C.yaw          # every model turned to face +Z, the heading direction
	for nm in ["Front_Left", "Front_Right", "Rear_Left", "Rear_Right"]:
		var w: Node3D = s.find_child(nm, true, false)
		if w: wheels.append({ n = w, steer = (w.get_parent() if w.get_parent().name.begins_with("Steer_") else null), front = nm.begins_with("Front") })
	merge_body(s)
	_find_cockpit(s)
	for mi in s.find_children("BodyMerged", "MeshInstance3D", true, false):
		for i in mi.mesh.get_surface_count():
			var m = mi.mesh.surface_get_material(i)
			if m is BaseMaterial3D and (m.resource_name in ["Glass", "Glass_Tint", "Lens_Clear", "Lens_Red"]):
				var d: BaseMaterial3D = m.duplicate(); d.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
				d.albedo_color.a = 0.35 if m.resource_name.begins_with("Lens") else (0.55 if m.resource_name == "Glass_Tint" else 0.3)
				d.roughness = 0.05; mi.set_surface_override_material(i, d)
	if opts.has("paint"): _repaint(s, C.paint, opts.paint)
	elif player and Progress.U(id).paint > 0: _repaint(s, C.paint, Progress.PAINTS[Progress.U(id).paint][1])
	if opts.get("far", false): _add_far(s, C)
	Tod.light_car(body)          # head and tail lights glow at sunset and night
	car_layers(body)

# cars are drawn on render layer 2: they get their sunlight from the car sun, which follows the baked light where they are
static func car_layers(root: Node):
	for g in root.find_children("*", "GeometryInstance3D", true, false): (g as GeometryInstance3D).layers = 2

# a rival's colour: every paint surface of the near model gets a copy of its material in the new colour
func _repaint(s: Node3D, names: Array, col: Color):
	var done = {}
	for mi in s.find_children("*", "MeshInstance3D", true, false):
		for i in mi.mesh.get_surface_count():
			var m = mi.get_surface_override_material(i)
			if m == null: m = mi.mesh.surface_get_material(i)
			if m is BaseMaterial3D and m.resource_name in names:
				if not done.has(m): var d: BaseMaterial3D = m.duplicate(); d.albedo_color = col; done[m] = d
				mi.set_surface_override_material(i, done[m])

# lighter models for rivals: the same materials as the near one (matched by name) on a ~45k and a ~16k version;
# shadows come from the light one only, so a pack of rivals costs little in the shadow pass
func _add_far(s: Node3D, C: Dictionary):
	var by_name = {}
	for mi in s.find_children("*", "MeshInstance3D", true, false):
		mi.visibility_range_end = NEAR_TO; mi.visibility_range_end_margin = 1.5; mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		for i in mi.mesh.get_surface_count():
			var m = mi.get_surface_override_material(i)
			if m == null: m = mi.mesh.surface_get_material(i)
			if m: by_name[m.resource_name] = m
	for lod in [[C.mid, NEAR_TO, MID_TO, GeometryInstance3D.SHADOW_CASTING_SETTING_OFF], [C.far, MID_TO, 0.0, GeometryInstance3D.SHADOW_CASTING_SETTING_OFF],
			[C.far, 0.0, 90.0, GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY]]:
		var f = load(lod[0]).instantiate(); s.add_child(f)
		for mi in f.find_children("*", "MeshInstance3D", true, false):
			mi.visibility_range_begin = lod[1]; mi.visibility_range_end = lod[2]; mi.visibility_range_begin_margin = 1.5; mi.visibility_range_end_margin = 1.5; mi.cast_shadow = lod[3]
			for i in mi.mesh.get_surface_count():
				var m = mi.mesh.surface_get_material(i)
				if m and by_name.has(m.resource_name): mi.set_surface_override_material(i, by_name[m.resource_name])

func place(p: Vector3, h: float):
	px = p.x; py = p.y + 0.05; pz = p.z; hd = h; vx = 0; vz = 0; vy = 0; yr = 0; delta_ = 0; st_in = 0; thr = 0; brk = 0
	af = 0; ar = 0; axf = 0; ayf = 0; gear = 0; rpm = V.idle; shiftT = 0; spin = false; drift = 0; air = false; pitch = 0; roll = 0
	if is_inside_tree():                       # stand on the real surface (camber, kerbs), not on the road's centre-line height
		var g = ground(p.x, p.z, p.y + 1.5)
		if g[0] > -50.0 and abs(g[0] - p.y) < 2.5: py = g[0]
		var fx = sin(h); var fz = cos(h)                       # start already sitting at the slope and camber, not level then tipping over
		var a0 = ground(px + fx * 1.4, pz + fz * 1.4, py + 1)[0]; var a1 = ground(px - fx * 1.4, pz - fz * 1.4, py + 1)[0]
		var a2 = ground(px + fz * 0.85, pz - fx * 0.85, py + 1)[0]; var a3 = ground(px - fz * 0.85, pz + fx * 0.85, py + 1)[0]
		var sp = rest(py, a0, a1, 1.4); var sr = rest(py, a2, a3, 0.85); pitch = sp[0]; roll = sr[0]; body_lift = maxf(sp[1], sr[1])
		position = Vector3(px, py, pz); rotation = Vector3(0, hd, 0); reset_physics_interpolation()          # a jump, not a glide across the map
	safe = Vector4(p.x, p.y, p.z, h)

# how the body sits on three ground points along one axis (ahead, centre, behind at +-half): over a crest it rests on the
# crest and the higher end (no end floating in the air), in a dip on both ends with the middle lifted (no sinking).
# returns [tilt angle, lift of the centre]
static func rest(c: float, f: float, b: float, half: float) -> Array:
	f = maxf(f, c - 2.0); b = maxf(b, c - 2.0)
	if c >= (f + b) * 0.5:
		var t = atan2(f - c, half) if f >= b else atan2(c - b, half)
		return [clampf(t, -0.5, 0.5), 0.0]
	return [clampf(atan2(f - b, half * 2.0), -0.6, 0.6), minf((f + b) * 0.5 - c, 0.4)]

static func lat(a: float, B: float, C: float) -> float: return sin(C * atan(B * a))
static func tyre_angle(a: float) -> float:
	a = wrapf(a, -PI, PI)
	if a > PI / 2: a -= PI
	elif a < -PI / 2: a += PI
	return a
func torque_at(r: float) -> float:
	if r >= V.red: return 0.0
	var x = (r - V.tqRpm) / 4300.0
	return V.tqPeak * max(0.5, 1.0 - x * x * 0.85)

func drive(dt: float):
	mu_s = move_toward(mu_s, MU.get(surf, 0.7) * (Weather.GRIP[Weather.get_level()] if surf == "road" else Weather.GRIP_OFF[Weather.get_level()]), dt * 2.5)          # grip changes over a few tenths of a second: crossing a verge or a seam never jerks the car
	var L = V.a + V.b; var g = 9.81; var mu = V.mu * mu_s
	var stT = -in_steer; var thT = in_gas; var brT = in_brake
	var spd0 = Vector2(vx, vz).length(); var srate = (9.0 if stT * st_in < 0 else 5.5) / (1.0 + spd0 / 40.0) * sens
	st_in += clamp(stT - st_in, -srate * dt, srate * dt); thr += clamp(thT - thr, -dt * 10, dt * 7); brk += clamp(brT - brk, -dt * 12, dt * 9)
	var sub = 4; var h = dt / sub; var r = yr; var wx = vx; var wz = vz; var bx = 0.0; var by = 0.0
	for k in sub:
		var ffx = sin(hd); var ffz = cos(hd); bx = wx * ffx + wz * ffz; by = wx * ffz - wz * ffx
		var spd = Vector2(bx, by).length(); var bt = atan2(by, abs(bx)) if spd > 2 else 0.0
		var slide = clampf((abs(ar) - 0.15) / 0.15, 0, 1) if spd > 4 else 0.0
		var lock = V.dmax + (V.lockD - V.dmax) * slide
		var align = clamp(atan2(by + V.a * r, bx), -lock, lock) if bx > 2 else 0.0
		var rng = minf(lock, max(0.075, V.dmax / (1.0 + pow(max(bx, 0.0) / 12.0, 2) * 1.2)) * lerpf(1.0, sens, 0.7))
		if st_in * align > 0: rng += (lock - rng) * slide
		var yawLim = clampf(1.0 - (abs(r) - 1.1) / 0.9, 0.15, 1.0) if (assist and st_in * r > 0) else 1.0
		var dT = clamp((0.85 if assist else 0.25) * slide * align + st_in * rng * yawLim, -lock, lock)
		delta_ += clamp(dT - delta_, -4.5 * h, 4.5 * h)
		var d = delta_; var cd = cos(d); var sd = sin(d)
		var dfc = V.down_ * spd * spd
		var Fzf = V.m * g * V.b / L - V.m * axf * V.h / L + dfc * 0.45; var Fzr = V.m * g * V.a / L + V.m * axf * V.h / L + dfc * 0.55
		Fzf = max(Fzf, 0.12 * V.m * g); Fzr = max(Fzr, 0.12 * V.m * g)
		var Pf = mu * V.muF * Fzf; var Pr = mu * V.muR * Fzr
		var a_f = tyre_angle(d - atan2(by + V.a * r, bx)); var a_r = tyre_angle(-atan2(by - V.b * r, bx)); var lag = min(1.0, (spd + 0.5) / V.sigma * h)
		af += (a_f - af) * lag; ar += (a_r - ar) * lag
		var rev = bx < 0.5 and brT > 0.1 and thT <= 0.0
		var ratio = (-3.1 * V.fd) if rev else (V.gears[gear] * V.fd)
		var wheelRpm = abs(bx) / V.r * 9.5493 * abs(ratio)
		var sideways = abs(bt) > 0.22
		if shiftT > 0: shiftT -= h
		elif manual:
			if gear > 0 and abs(bx) < 1.0 and thT < 0.1: gear = 0          # stopped: first gear is ready for the next launch
		elif sideways: pass
		elif not rev and gear < 5 and (wheelRpm > V.up or (rpm > V.up and wheelRpm > V.up * 0.72)): gear += 1; shiftT = 0.16
		elif not rev and gear > 0 and wheelRpm * V.gears[gear - 1] / V.gears[gear] < V.down: gear -= 1; shiftT = 0.1
		var launch = V.idle + 2600 * thr; var eng = max(wheelRpm, min(launch, 4200))
		rpm += ((min(V.red, eng + 1800 * thr) if spin else min(eng, V.red + 60)) - rpm) * min(1.0, h * 14)
		var Fdrive = 0.0
		if not (shiftT > 0 or in_hand):
			Fdrive = (-brT * 4200 * (1.0 if bx > -7 else 0.0)) if rev else thr * torque_at(wheelRpm if wheelRpm > V.red else rpm) * ratio * V.eff / V.r
		drift = max(0.0, drift - h * 0.9)
		if in_hand and abs(bx) > 6: drift = 1.2
		if abs(bt) > 0.2 and spd > 6: drift = max(drift, 0.8)
		pwr = (pwr + h) if (abs(st_in) > 0.8 and thr > 0.9 and bx > 4 and bx < 25) else 0.0
		if pwr > 0.4: drift = max(drift, 0.6)
		var ab = abs(bt); var grow = (ab - pb) / h; pb = ab
		if assist and Fdrive > 0 and ab > 0.35 and drift > 0: Fdrive *= clamp(1 - 2.6 * (ab - 0.55) - 0.9 * grow, 0.22, 1)
		if tc and drift <= 0 and Fdrive > 0:
			var lt = Pr * lat(ar, V.Br, V.C); Fdrive = min(Fdrive, 0.95 * sqrt(max(0.0, Pr * Pr - lt * lt)))
		var Fb = 0.0 if rev else brk * V.brake * V.m * g; var sv = sign(bx) if abs(bx) > 0.3 else bx / 0.3
		var Fxf = -sv * min(Fb * V.bias, 0.96 * Pf); var Fyf = Pf * lat(af, V.B, V.C) * sqrt(max(0.0, 1 - pow(Fxf / Pf, 2)))
		var Fxr = 0.0; var Fyr = 0.0; spin = false
		if in_hand and abs(bx) > 0.5: Fxr = -sv * 0.8 * Pr; Fyr = Pr * lat(ar, V.Br, V.C) * 0.45
		else:
			var req = Fdrive - sv * Fb * (1 - V.bias)
			if abs(req) > 0.98 * Pr: spin = Fdrive != 0 and abs(Fdrive) > 0.98 * Pr; Fxr = sign(req) * 0.78 * Pr; Fyr = Pr * lat(ar, V.Br, V.C) * 0.6
			else: Fxr = req; Fyr = Pr * lat(ar, V.Br, V.C) * sqrt(1 - pow(req / Pr, 2))
		var Fd = V.cda * bx * abs(bx) + V.rr * RRS.get(surf, 10.0) * V.m * g * sv
		var Fx = Fxr + Fxf * cd - Fyf * sd - Fd; var Fy = Fyr + Fyf * cd + Fxf * sd; var Mz = V.a * (Fyf * cd + Fxf * sd) - V.b * Fyr
		var ax = Fx / V.m - g * sin(pitch) * 0.9; var ay = Fy / V.m
		wx += (ffx * ax + ffz * ay) * h; wz += (ffz * ax - ffx * ay) * h; r += Mz / V.Iz * h
		var rlim = 1.0 + 0.35 * spd; r = clampf(r, -rlim, rlim)            # no pirouettes at walking pace: a car can only turn so fast for its speed
		hd += r * h
		if bx < -0.3:
			r *= exp(-h * 3.5); var vxx = wx * ffx + wz * ffz; var vyy = (wx * ffz - wz * ffx) * exp(-h * 3)
			if not rev: vxx = move_toward(vxx, 0.0, (4.0 + 9.0 * thT) * h)      # rolling backwards without reverse held: engine braking, and gas stops it quickly
			wx = ffx * vxx + ffz * vyy; wz = ffz * vxx - ffx * vyy
		if spd < 1.2 and thT <= 0:
			var vxx = wx * ffx + wz * ffz; var vyy = (wx * ffz - wz * ffx) * exp(-h * 6); r *= exp(-h * 6)
			var vk = vxx
			if abs(vxx) < 0.6 and not rev: vk = 0.0; vyy = 0.0; r = 0.0; af = 0.0; ar = 0.0       # parked: held still (hill hold), no tyre forces at zero speed
			wx = ffx * vk + ffz * vyy; wz = ffz * vk - ffx * vyy
		axf += (ax - axf) * min(1.0, h * 12); ayf += (ay - ayf) * min(1.0, h * 12)
	beta = atan2(by, abs(bx)) if Vector2(bx, by).length() > 2 else 0.0; yr = r; vx = wx; vz = wz

# ground under a point: ray down onto the map colliders; returns [height, surface]
func ground(x: float, z: float, yref: float) -> Array:
	var q = PhysicsRayQueryParameters3D.create(Vector3(x, yref + 3.0, z), Vector3(x, yref - 60.0, z)); q.collision_mask = 1
	var space = get_world_3d().direct_space_state; var hit = space.intersect_ray(q)
	if hit.is_empty():          # a ray exactly on the seam between two map pieces can slip through: look a few cm aside before calling it the edge
		for o in [Vector3(0.06, 0, 0), Vector3(-0.06, 0, 0), Vector3(0, 0, 0.06), Vector3(0, 0, -0.06)]:
			q.from = Vector3(x, yref + 3.0, z) + o; q.to = Vector3(x, yref - 60.0, z) + o; hit = space.intersect_ray(q)
			if not hit.is_empty(): break
	if hit.is_empty(): return [-100.0, "grass"]
	# a ray on a seam in the road surface can also drop through to the ground under it: a second ray a hair aside settles it
	q.from = Vector3(x + 0.07, yref + 3.0, z + 0.05); q.to = Vector3(x + 0.07, yref - 60.0, z + 0.05); var h2 = space.intersect_ray(q)
	if not h2.is_empty() and h2.position.y > hit.position.y + 0.3 and h2.position.y < hit.position.y + 3.0: hit = h2
	return [hit.position.y, hit.collider.get_meta("surf", "grass")]

func physics(dt: float):
	if frozen: vx = 0.0; vz = 0.0; yr = 0.0; speed = 0.0; vf = 0.0; rpm = lerpf(rpm, V.idle + 3200.0 * in_gas, dt * 6.0); return
	var fx = sin(hd); var fz = cos(hd)
	var G = ground(px, pz, py + 1.0); surf = G[1]
	if not air: drive(dt)
	else: yr *= exp(-dt * 0.8); delta_ *= exp(-dt * 4); hd += yr * dt
	vf = vx * fx + vz * fz
	var nx: float = px + vx * dt; var nz: float = pz + vz * dt
	if coll:
		var w := coll.walls(nx, nz, self); nx = w[0]; nz = w[1]
		var ob := coll.obstacles(nx, nz, self); nx = ob[0]; nz = ob[1]
	var gn0 = ground(nx, nz, py + 1.0)[0]
	if not air and (gn0 < -50.0 or (gn0 < -0.15 and gn0 <= py + 0.02)):          # the edge of the map, or the sea (surface at -0.25): stop at the edge / waterline
		nx = px; nz = pz; var sp0 = Vector2(vx, vz).length(); vx *= -0.25; vz *= -0.25; yr *= 0.5
		if sp0 > 3.0: bump(sp0, "solid")
	px = nx; pz = nz; bump_t -= dt
	if settle > 0.0:          # a crash knocks the car round, but the tyres soon take hold again: the spin dies away instead of sliding on
		settle -= dt; yr *= exp(-dt * 4.0)
		var lat = vx * cos(hd) - vz * sin(hd); var lk = 1.0 - exp(-dt * 3.0)
		vx -= cos(hd) * lat * lk; vz += sin(hd) * lat * lk
	var Gn = ground(px, pz, py + 1.0)
	if not air:
		var dy: float = Gn[0] - py
		if dy < -0.5 - abs(vf) * dt * 0.9: air = true; vy = min(vy, 6.0)
		elif dy > 2.5: px -= vx * dt; pz -= vz * dt; vx *= -0.3; vz *= -0.3      # a step too high to climb (wall, kerb of a cliff): bounce back
		elif surf != "road" and dy < -0.25 and dy / dt < vy - 24.0 * dt - 6.0: air = true      # rough ground dropping away faster than the car can fall: off the edge, not glued down (roads stay smooth)
		else: vy = clamp(dy / dt, -30, 12); py = Gn[0]
	if air:
		vy -= 24 * dt; py += vy * dt
		if py <= Gn[0]:
			if vy < -4.0: landed.emit(-vy)
			py = Gn[0]; air = false; vy = 0
	_odd = not _odd
	var tp = pitch; var tr = roll; var lift = 0.0
	if not air and _odd:          # body pitch and roll from the ground at the four corners: 30 times a second is plenty
		var a0 = ground(px + fx * 1.4, pz + fz * 1.4, py + 1)[0]; var a1 = ground(px - fx * 1.4, pz - fz * 1.4, py + 1)[0]
		var a2 = ground(px + fz * 0.85, pz - fx * 0.85, py + 1)[0]; var a3 = ground(px - fz * 0.85, pz + fx * 0.85, py + 1)[0]
		_corners = [a0 - Gn[0], a1 - Gn[0], a2 - Gn[0], a3 - Gn[0]]          # kept as heights relative to the ground under the car
	if not air and _corners.size() == 4:
		var a0 = Gn[0] + _corners[0]; var a1 = Gn[0] + _corners[1]; var a2 = Gn[0] + _corners[2]; var a3 = Gn[0] + _corners[3]
		var sp = rest(py, a0, a1, 1.4); var sr = rest(py, a2, a3, 0.85); tp = sp[0]; tr = sr[0]; lift = maxf(sp[1], sr[1])
	pitch = lerpf(pitch, tp, 1 - exp(-dt * 9)); roll = lerpf(roll, tr, 1 - exp(-dt * 9)); body_lift = lerpf(body_lift, lift, 1 - exp(-dt * 12))
	speed = Vector2(vx, vz).length()
	if py < -1.0 or Gn[0] < -50:                                        # into the sea or out of the map: back on the nearest road
		var q = nearest_road.call(Vector3(px, py, pz)) if nearest_road.is_valid() else null
		if q: place(q[0], q[1])
		else: place(Vector3(safe.x, safe.y, safe.z), safe.w)
		return
	safe_t += dt
	if safe_t > 0.7 and surf == "road" and not air: safe_t = 0; safe = Vector4(px, py, pz, hd)

var acc = 0.0
func _physics_process(dt):
	var _p0 = Time.get_ticks_usec(); _physics_process_body(dt); Prof.add("car", Time.get_ticks_usec() - _p0)
func _physics_process_body(dt):
	acc = min(acc + dt, 0.1)
	while acc >= 1.0 / 120.0: physics(1.0 / 120.0); acc -= 1.0 / 120.0
	position = Vector3(px, py, pz); rotation = Vector3(0, hd, 0)
	body.rotation = Vector3(-pitch, 0, roll); body.position.y = body_lift
	wheel_spin += vf * dt; rear_spin += (vf + (16 * thr if spin else 0.0) - (vf if in_hand and abs(vf) > 1 else 0.0)) * dt
	for w in wheels:
		var a = spin_sgn * (wheel_spin if w.front else rear_spin) / V.r
		if spin_axis == "x": w.n.rotation.x = a
		else: w.n.rotation.z = a
		if w.steer: w.steer.rotation.y = delta_
	if sw:          # steering wheel: about 11 times the road wheels' angle, round its own centre
		var r = Transform3D(Basis(sw_axis, delta_ * 11.0 * STEER_SIGN.get(car_id, 1.0)), Vector3.ZERO)
		sw.transform = sw_rest * Transform3D(Basis(), sw_c) * r * Transform3D(Basis(), -sw_c)

var body_lift := 0.0
# where the car is drawn this frame: between the last two physics steps (physics interpolation), so the camera and the
# headlights follow the car as seen, not the 60 Hz physics position
func vis_pos() -> Vector3: return get_global_transform_interpolated().origin if is_inside_tree() else Vector3(px, py, pz)
func vis_hd() -> float:
	if not is_inside_tree(): return hd
	var z = get_global_transform_interpolated().basis.z; return atan2(z.x, z.z)
var nearest_road: Callable          # set by the game: position -> [road point, heading] nearest to it
var impact := 0.0         # speed into the last thing hit (m/s), for the crash sound
var impact_kind := "solid"   # car, rail or solid: which crash recordings fit
var settle := 0.0
var _odd := false; var _corners := []         # after a crash: the car straightens out instead of spinning on
signal landed(v)          # back on the ground after a jump, with the speed it came down at
func bump(v := 8.0, kind := ""):
	if kind != "": impact_kind = kind
	if v > 6.0: settle = clampf(v / 20.0, 0.35, 0.9); drift = 0.0
	if bump_t <= 0: bump_t = 0.5 if v < 6.0 else 0.8; impact = v; crashed.emit()

# cockpit: where the driver's eyes are (body space) and the steering wheel, turned with the front wheels
var eye := Vector3(0.0, 1.0, -0.2)
var sw: Node3D; var sw_rest := Transform3D.IDENTITY; var sw_c := Vector3.ZERO; var sw_axis := Vector3.FORWARD
func _find_cockpit(s: Node3D):
	sw = _steering_wheel(s)
	if sw == null: return
	sw_rest = sw.transform
	var box := AABB(); var first = true
	for mi in ([sw] if sw is MeshInstance3D else []) + sw.find_children("*", "MeshInstance3D", true, false):
		var bb: AABB = _rel(mi, sw) * (mi as MeshInstance3D).get_aabb() if mi != sw else (mi as MeshInstance3D).get_aabb()
		box = bb if first else box.merge(bb); first = false
	if first: return
	sw_c = box.get_center()
	var sz = box.size; sw_axis = Vector3.RIGHT if sz.x <= sz.y and sz.x <= sz.z else (Vector3.UP if sz.y <= sz.z else Vector3.BACK)   # the thin side is the column
	var c_body: Vector3 = s.transform * (_rel(sw, s) * sw_c)          # wheel centre in the car's own space (nose +Z)
	eye = c_body + EYE.get(car_id, Vector3(0.0, 0.3, -0.5))
static func _steering_wheel(root: Node) -> Node3D:          # the import names it "Steering" (the column is separate)
	var n = root.find_child("Steering_Wheel", true, false)
	return n if n else root.find_child("Steering", true, false)
static func _rel(n: Node3D, root: Node) -> Transform3D:
	var t = n.transform; var p = n.get_parent()
	while p != null and p != root: t = (p as Node3D).transform * t; p = p.get_parent()
	return t

static var _merged = {}
# one mesh per material for everything that does not move: about 60 parts become a dozen draw calls
func merge_body(root: Node3D):
	var moving := {}
	for w in wheels:
		moving[w.n] = true
		if w.steer: moving[w.steer] = true
	var swn = _steering_wheel(root)
	if swn: moving[swn] = true
	var tools := {}; var mats := {}
	var inv = root.global_transform.affine_inverse()
	if _merged.has(car_id):                     # merged once per car model; rivals and later races reuse it (no hitch at the start)
		for mi in root.find_children("*", "MeshInstance3D", true, false):
			var skip2 = false; var p2: Node = mi
			while p2 and p2 != root:
				if moving.has(p2): skip2 = true; break
				p2 = p2.get_parent()
			if not skip2: mi.queue_free()
		var o2 = MeshInstance3D.new(); o2.mesh = _merged[car_id]; o2.name = "BodyMerged"; root.add_child(o2); return
	for mi in root.find_children("*", "MeshInstance3D", true, false):
		var skip = false; var p: Node = mi
		while p and p != root:
			if moving.has(p): skip = true; break
			p = p.get_parent()
		if skip: continue
		var xf = inv * mi.global_transform
		for i in mi.mesh.get_surface_count():
			var m = mi.get_surface_override_material(i)
			if m == null: m = mi.mesh.surface_get_material(i)
			var key = m.get_instance_id() if m else 0
			if not tools.has(key):
				var st = SurfaceTool.new(); st.begin(Mesh.PRIMITIVE_TRIANGLES); tools[key] = st; mats[key] = m
			tools[key].append_from(mi.mesh, i, xf)
		mi.queue_free()
	var am = ArrayMesh.new()
	for key in tools:
		am = tools[key].commit(am)
		am.surface_set_material(am.get_surface_count() - 1, mats[key])
	var out = MeshInstance3D.new(); out.mesh = am; out.name = "BodyMerged"; root.add_child(out)
	_merged[car_id] = am
	print("car merged into %d surfaces" % am.get_surface_count())

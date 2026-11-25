extends Node3D
class_name Race
# Sprints, hill climbs and circuit laps all over the island, with checkpoints, a timer and three rivals.
# Rivals are real Car instances (same tyre model as the player) driven by a simple racing driver: they follow the route
# with their own line, brake for corners from a speed profile worked out from the route's curvature, overtake round
# slower cars and get put back on the road if they crash. The road is closed for the race (traffic is paused).

const RACES = {
	coast = { name = "Coast Sprint", blurb = "The whole coastal highway, north to south. Long, fast sweepers.",
		segs = [["Ring", 726, 439]], skill = 0.90 },
	peninsula = { name = "Peninsula Climb", blurb = "Down the highway, then hard right and up the peninsula.",
		segs = [["Ring", 470, 600], ["Peninsula Road", 144, 22]], skill = 0.93 },
	lighthouse = { name = "Lighthouse Run", blurb = "From the lighthouse onto the highway and into West Avenue.",
		segs = [["Lighthouse Road", 48, 0], ["Ring", 546, 736], ["West Avenue", 259, 191]], skill = 0.96 },
	summit = { name = "Summit Pass", blurb = "Out of the city and over the mountain. Hairpins between rock walls.",
		segs = [["Summit Pass", 2, 299]], skill = 0.93 },
	descent = { name = "Eagle Descent", blurb = "Along the high ridge, through the tunnel and down the eagle's road. 70 metres of drop.",
		segs = [["Skyline Road", 297, 178], ["Eagle Descent", 0, 104]], skill = 0.95 },
	desert = { name = "Desert Dash", blurb = "Off the highway, across the dunes and past the mesas.",
		segs = [["Dune Road", 126, 7], ["Mesa Roundabout", 3, 22, "arc"], ["Mesa Road", 6, 103], ["East Avenue", 105, 30]], skill = 0.95 },
	serpentine = { name = "Serpentine", blurb = "The hill climb: switchbacks up to the summit, 80 metres of height.",
		segs = [["Serpentine", 2, 226]], skill = 0.97 },
	gp = { name = "Aurelia Grand Prix", blurb = "Two laps of the racing circuit. Flat out on the straight, brave in the esses.",
		segs = [["Circuit", 50, 50, 2]], skill = 0.98 },
	# time-of-day events: raced at sunset or at night whatever the clock says; each opens with a podium in the race it names
	golden = { name = "Golden Fields", blurb = "Sunset on the farm road, past the barns, then north along the coast into the low sun.",
		segs = [["Farm Road", 6, 217], ["Ring", 2000, 1790]], skill = 0.94, tod = 1, after = "lighthouse" },
	harbour = { name = "Harbour Lights", blurb = "At night along the south coast: the harbour lights, then the dark climb west.",
		segs = [["Ring", 100, 560]], skill = 0.96, tod = 2, after = "summit" },
	midnight = { name = "Midnight City", blurb = "Round the edge of the city at night. Four streets, four hard corners, lamps all the way.",
		segs = [["Street N-480", 2, 112], ["Street E260", 0, 192], ["Street N480", 112, 0], ["Street E-300", 192, 8]], skill = 0.97, tod = 2, after = "desert" },
	# solo challenges: medals instead of places (gold, silver, bronze count as 1st, 2nd, 3rd for prize money and unlocks)
	touge = { name = "Touge Drift", blurb = "Down the Summit Pass alone. Angle, speed and linked drifts score; crash or spin and the drift is lost.",
		segs = [["Summit Pass", 298, 2]], skill = 0.93, mode = "drift", medals = [9000, 5000, 2000], after = "summit" },
	trial = { name = "Circuit Time Trial", blurb = "One lap of the racing circuit against the clock, from a standing start. No rivals, no excuses.",
		segs = [["Circuit", 50, 50, 1]], skill = 0.98, mode = "trial", medals = [76.0, 81.0, 87.0], after = "desert" } }
const ORDER = ["coast", "peninsula", "lighthouse", "summit", "descent", "desert", "serpentine", "gp", "golden", "harbour", "midnight", "touge", "trial"]
static func tag(rid: String) -> String:
	var m = RACES[rid].get("mode", "")
	return " · DRIFT" if m == "drift" else (" · TIME TRIAL" if m == "trial" else ["", " · SUNSET", " · NIGHT"][RACES[rid].get("tod", 0)])
static func medal(rid: String, v: float) -> int:          # 1 gold, 2 silver, 3 bronze, 4 none (score: higher is better; time: lower)
	var md = RACES[rid].medals
	for k in 3:
		if (v >= md[k]) if RACES[rid].mode == "drift" else (v > 0.0 and v <= md[k]): return k + 1
	return 4
const MEDAL = ["GOLD", "SILVER", "BRONZE", "NO MEDAL"]
const RIVALS = [
	{ name = "M. Kade", car = "vortex", paint = Color(0.05, 0.16, 0.42), line = -0.45 },
	{ name = "L. Varga", car = "calder", paint = Color(0.03, 0.03, 0.035), line = 0.4 },
	{ name = "R. Sato", car = "vortex", paint = Color(0.62, 0.62, 0.6), line = 0.0 } ]
const START_S = 34.0; const RUNOFF = 45.0; const CP_EVERY = 260.0
const SAVE = "user://races.cfg"

signal finished
var id = ""; var R = {}
var main: Node; var player: Car; var coll: Coll; var traffic: Node
var pts = PackedVector3Array(); var cum = PackedFloat32Array(); var hws = PackedFloat32Array(); var vprof = PackedFloat32Array()
var length = 0.0; var finish_s = 0.0
var cps = []            # route distance of each checkpoint; the last one is the finish
var gates = []
var racers = []         # { car, name, s, done, time, rival, line, stuck, ... } ; racers[0] is the player
var state = "count"; var count = 3.6; var t = 0.0; var next_cp = 0; var result_t = 0.0
var autopilot = false   # test: the player's car is driven by the same racing driver
var hud: Control; var info: Label; var big: Label; var msg: Label; var panel: Control
var wrong_t = 0.0; var off_t = 0.0
var tod_was = -1

static func best(rid: String) -> Array:
	var cf = ConfigFile.new(); cf.load(SAVE)
	return [cf.get_value(rid, "time", 0.0), cf.get_value(rid, "pos", 0)]

static func fmt(x: float) -> String:
	return "%d:%05.2f" % [int(x / 60.0), fmod(x, 60.0)]

func start(rid: String, m: Node):
	id = rid; R = RACES[rid]; main = m; player = m.car; coll = m.coll; traffic = m.traffic
	if R.has("tod"): tod_was = Tod.get_level(); Tod.level = R.tod; Tod.apply(m)          # sunset or night event (not saved)
	_build_route(m.roads)
	_speed_profile()
	traffic.visible = false; traffic.process_mode = Node.PROCESS_MODE_DISABLED; coll.dyn = []
	# checkpoints spread evenly, the finish RUNOFF short of the road end so there is room to stop
	finish_s = length - RUNOFF; var n = maxi(2, int(round((finish_s - START_S) / CP_EVERY)))
	for k in n: cps.append(START_S + (finish_s - START_S) * (k + 1) / n)
	_gate(START_S, "START", Color(1, 1, 1))
	for k in cps.size(): _gate(cps[k], "FINISH" if k == cps.size() - 1 else "CHECKPOINT %d" % (k + 1), Color(1.0, 0.62, 0.08))
	# grid: two rows of two behind the start line, the player on the second row inside
	var grid = [[START_S - 9.0, -0.35], [START_S - 9.0, 0.35], [START_S - 18.0, -0.35], [START_S - 18.0, 0.35]]
	var slots = [grid[2], grid[0], grid[1], grid[3]]       # the player starts on the second row: something to chase
	racers.append(_racer(player, "You", false, 0.0))
	var solo = R.has("mode")
	if solo:
		main.drift.on = R.mode == "drift"; main.drift.pay = false; main.drift.reset()
	for k in (0 if solo else RIVALS.size()):
		var rv = RIVALS[k]; var c = Car.new(); c.car_id = rv.car; c.opts = { far = true, paint = rv.paint }; add_child(c); c.coll = coll
		var r = _racer(c, rv.name, true, rv.line)
		var au = CarAudio.new(); au.car = c; au.positional = true; c.add_child(au); au.ignition(); r.snd = au      # its own engine, as 3D sound
		racers.append(r)
	if solo: slots = [[START_S - 9.0, 0.0]]
	for k in racers.size():
		var sl = slots[k]; var a = at(sl[0]); var p: Vector3 = a[0] + a[2] * (sl[1] * a[3] * 2.0)
		racers[k].car.place(p, atan2(a[1].x, a[1].z)); racers[k].s = sl[0]; racers[k].car.frozen = true
	main.cam_yaw = player.hd
	_make_hud()

func _racer(c: Car, nm: String, rival: bool, line: float) -> Dictionary:
	return { car = c, name = nm, rival = rival, line = line, s = 0.0, done = false, time = 0.0, stuck = 0.0, shift = 0.0, cp = 0 }

# route: the road runs in order, as one polyline with distance along it and half width at each point
func _build_route(roads: Dictionary):
	var joins = []; var prev_arc = false
	for sg in R.segs:
		var is_arc = sg.size() > 3 and str(sg[3]) == "arc"
		if pts.size() > 0: joins.append([pts.size() - 1, 3.5, 7 if (is_arc or prev_arc) else 5])      # into and out of a roundabout: rounded over a longer stretch, never pulled in onto the island in the middle
		prev_arc = is_arc
		var src = roads[sg[0]]; var a: int = sg[1]; var b: int = sg[2]; var st = 1 if b >= a else -1
		var hw = float(main.road_hw.get(sg[0], 5.0)) if main else 5.0
		var n = src.size() / 3; var arc = sg.size() > 3 and str(sg[3]) == "arc"; var laps = int(sg[3]) if sg.size() > 3 and not arc else 0
		var steps = n * laps + int(ceil((START_S + RUNOFF) / 5.0)) + 1 if laps > 0 else abs(b - a)        # laps of a closed road, plus the grid and the run-off
		if arc: steps = posmod(b - a, n); laps = 1          # part of a roundabout, the way the traffic goes round
		var i = a
		for k in steps + 1:
			var q = Vector3(src[i * 3], src[i * 3 + 1], src[i * 3 + 2])
			if pts.size() == 0 or q.distance_to(pts[pts.size() - 1]) > 1.5:
				if pts.size() > 0: length += q.distance_to(pts[pts.size() - 1])
				pts.append(q); cum.append(length); hws.append(hw)
			i = (i + 1) % n if laps > 0 else i + st
	# where two roads meet the polyline has a sharp kink: round it into an arc (corner pulled in by at most ~5 m)
	for jj in joins:
		var j: int = jj[0]; var cap: float = jj[1]; var span: int = jj[2]
		var corner = pts[j]
		for it in 60:
			for i in range(maxi(1, j - span), mini(pts.size() - 1, j + span + 1)):
				var q = pts[i] * 0.5 + (pts[i - 1] + pts[i + 1]) * 0.25; q.y = pts[i].y
				if Vector2(q.x - corner.x, q.z - corner.z).length() < cap or i != j: pts[i] = q
	length = 0.0
	for i in pts.size():
		if i > 0: length += pts[i].distance_to(pts[i - 1])
		cum[i] = length

func at(s: float) -> Array:            # [position, tangent (flat), right (flat), half width]
	s = clampf(s, 0.0, length)
	var lo = 0; var hi = cum.size() - 1
	while hi - lo > 1:
		var mid = (lo + hi) >> 1
		if cum[mid] <= s: lo = mid
		else: hi = mid
	var t_ = clampf((s - cum[lo]) / maxf(cum[hi] - cum[lo], 1e-3), 0.0, 1.0)
	var tg = pts[hi] - pts[lo]; tg.y = 0; tg = tg.normalized()
	return [pts[lo].lerp(pts[hi], t_), tg, Vector3(-tg.z, 0, tg.x), lerpf(hws[lo], hws[hi], t_)]

# nearest route distance to a point, searched around the last known one so the route never jumps across a junction
func project(p: Vector3, hint: float) -> float:
	var lo = 0; var hi = cum.size() - 1
	while hi - lo > 1:
		var mid = (lo + hi) >> 1
		if cum[mid] <= hint: lo = mid
		else: hi = mid
	var best = 1e9; var bs = hint
	for i in range(maxi(0, lo - 10), mini(pts.size() - 1, lo + 14)):
		var a = pts[i]; var b = pts[i + 1]; var d = Vector2(b.x - a.x, b.z - a.z); var L2 = d.length_squared()
		if L2 < 1e-4: continue
		var u = clampf(((p.x - a.x) * d.x + (p.z - a.z) * d.y) / L2, 0.0, 1.0)
		var q = Vector2(a.x + d.x * u, a.z + d.y * u); var dist = q.distance_to(Vector2(p.x, p.z)) + 3.0 * maxf(0.0, abs(p.y - lerpf(a.y, b.y, u)) - 3.0)
		if dist < best: best = dist; bs = cum[i] + (cum[i + 1] - cum[i]) * u
	return bs

# fastest speed at each route point: corner speed from the curvature over ~15 m, then braking back from every corner
func _speed_profile():
	var n = pts.size(); vprof.resize(n)
	for i in n:
		var a = pts[maxi(0, i - 3)]; var b = pts[i]; var c = pts[mini(n - 1, i + 3)]
		var d1 = Vector2(b.x - a.x, b.z - a.z); var d2 = Vector2(c.x - b.x, c.z - b.z)
		var k = 0.0
		if d1.length() > 0.5 and d2.length() > 0.5: k = abs(d1.angle_to(d2)) / ((d1.length() + d2.length()) * 0.5)
		vprof[i] = minf(78.0, sqrt(10.5 / maxf(k, 1e-5)))
	for i in range(n - 2, -1, -1):
		vprof[i] = minf(vprof[i], sqrt(vprof[i + 1] * vprof[i + 1] + 2.0 * 7.5 * (cum[i + 1] - cum[i])))

func vmax_at(s: float) -> float:
	var lo = 0; var hi = cum.size() - 1
	while hi - lo > 1:
		var mid = (lo + hi) >> 1
		if cum[mid] <= s: lo = mid
		else: hi = mid
	return minf(vprof[lo], vprof[hi])

func _gate(s: float, label: String, col: Color):
	var a = at(s); var root = Node3D.new(); add_child(root)
	root.global_transform = Transform3D(Basis.looking_at(-a[1], Vector3.UP), a[0])
	var hw: float = a[3] + 0.9
	var mat = StandardMaterial3D.new(); mat.albedo_color = col * 0.35; mat.emission_enabled = true; mat.emission = col; mat.emission_energy_multiplier = 1.6
	var post = StandardMaterial3D.new(); post.albedo_color = Color(0.08, 0.085, 0.09); post.roughness = 0.5; post.metallic = 0.6
	for sd in [-1.0, 1.0]:
		var p = MeshInstance3D.new(); var bm = BoxMesh.new(); bm.size = Vector3(0.45, 5.6, 0.45); p.mesh = bm; p.material_override = post
		p.position = Vector3(sd * hw, 2.8, 0); root.add_child(p)
	var bar = MeshInstance3D.new(); var bb = BoxMesh.new(); bb.size = Vector3(hw * 2 + 0.45, 0.95, 0.22); bar.mesh = bb; bar.material_override = mat
	bar.position = Vector3(0, 5.3, 0); root.add_child(bar)
	for face in [1.0, -1.0]:
		var l = Label3D.new(); l.text = label; l.font_size = 96; l.pixel_size = 0.0075; l.outline_size = 0; l.modulate = Color(0.05, 0.05, 0.06)
		l.position = Vector3(0, 5.3, 0.125 * face); l.rotation.y = 0.0 if face > 0 else PI; l.double_sided = false; root.add_child(l)
	if label == "START" or label == "FINISH":      # chequered band painted across the road
		var line = MeshInstance3D.new(); var pm = PlaneMesh.new(); pm.size = Vector2(a[3] * 2, 1.6); line.mesh = pm
		var lm = StandardMaterial3D.new(); lm.albedo_texture = _checker(); lm.uv1_scale = Vector3(a[3] * 2 / 1.6, 1, 1); lm.roughness = 0.8
		lm.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS; line.material_override = lm; line.position = Vector3(0, 0.03, 0); root.add_child(line)
	root.visible = label == "START" or gates.size() < 3
	gates.append(root)

static var _chk: ImageTexture
static func _checker() -> ImageTexture:
	if _chk == null:
		var img = Image.create(64, 64, true, Image.FORMAT_RGB8)
		for y in 64:
			for x in 64: img.set_pixel(x, y, Color(0.9, 0.9, 0.9) if ((x >> 4) + (y >> 4)) % 2 == 0 else Color(0.05, 0.05, 0.05))
		img.generate_mipmaps(); _chk = ImageTexture.create_from_image(img)
	return _chk

# ---------------------------------------------------------------- driving
func _physics_process(dt):
	var _p0 = Time.get_ticks_usec(); _physics_process_body(dt); Prof.add("race", Time.get_ticks_usec() - _p0)
func _physics_process_body(dt):
	if state == "count":
		count -= dt
		for r in racers:
			if r.rival: r.car.in_gas = 0.4 if count < 1.5 else 0.0; r.car.in_brake = 1.0
		if count <= 0.0:
			state = "race"
			for r in racers: r.car.frozen = false
	elif state == "race" or state == "result":
		t += dt          # keeps running after the player finishes so the rivals get their own times
		for r in racers:
			var c: Car = r.car
			r.s = project(Vector3(c.px, c.py, c.pz), r.s)
			if not r.done and r.s >= finish_s:
				r.done = true; r.time = t
				if not r.rival: _player_finished()
			if r.rival or autopilot: _drive(r, dt)
		_player_checks(dt)
	# race cars are solid to each other
	var boxes = []
	for r in racers:
		var c: Car = r.car; var h: Vector2 = Car.CARS[c.car_id].half
		boxes.append([c.px, c.pz, h.x, h.y, atan2(-cos(c.hd), sin(c.hd)), c.get_instance_id()])
	coll.dyn2 = boxes

func _drive(r: Dictionary, dt: float):
	var c: Car = r.car; var v = c.speed
	if r.done:                                     # past the line: hold the lane and brake to a stop before the road ends
		var a0 = at(minf(r.s + 8.0, length)); var tgt0: Vector3 = a0[0] + a0[1] * 30.0 + a0[2] * r.line * a0[3]
		c.in_steer = _steer_to(c, tgt0) if v > 2.0 else 0.0; c.in_gas = 0.0; c.in_brake = 1.0 if v > 0.5 else 0.0; c.in_hand = false; return
	# line across the road: own preference, moved aside when a slower car is right ahead
	var want: float = r.line
	for o in racers:
		if o == r: continue
		var gap = o.s - r.s
		if gap > 0.0 and gap < 16.0 and o.car.speed < v + 1.0:
			var oa = at(o.s); var olat = (Vector3(o.car.px, 0, o.car.pz) - oa[0]).dot(oa[2]) / oa[3]
			if abs(olat - want) < 0.45: want = olat - 0.55 if olat > 0.0 else olat + 0.55
	r.shift = move_toward(r.shift, want - r.line, dt * 0.8)
	# slow corner ahead: everyone files into the middle and queues instead of going three wide into the apex
	var tight = clampf((24.0 - minf(vmax_at(r.s + 25.0), vmax_at(r.s + 45.0))) / 10.0, 0.0, 1.0)
	r.tight = move_toward(r.get("tight", 0.0), tight, dt * 0.7)
	var lat = clampf((r.line + r.shift) * (1.0 - r.tight), -0.7, 0.7)
	var look = r.s + 7.0 + v * 0.42
	var a = at(look); var tgt: Vector3 = a[0] + a[2] * lat * a[3]
	c.in_steer = _steer_to(c, tgt)
	# pace: the corner speed ahead times this driver's skill, which bends a little towards the player to keep it a race
	var sk: float = R.skill * (1.0 if not r.rival else (0.985 + 0.012 * RIVALS.find_custom(func(x): return x.name == r.name)))
	if r.rival:
		var lead = r.s - racers[0].s
		sk *= clampf(1.0 - lead / 1200.0, 0.85, 1.03)          # well ahead of the player: ease off; behind: push a little
	sk = minf(sk, 0.985)          # never past the corner speeds of the profile: pushing harder only ran them off the track
	var grip = 0.92 if c.car_id == "calder" else 1.0          # the heavier GT carries less speed through corners
	var vt = minf(vmax_at(r.s + v * 0.25), vmax_at(r.s + v * 0.6)) * sk * grip
	# a car right ahead on the same line: hold station behind it
	for o in racers:
		if o == r: continue
		var gap = o.s - r.s
		if gap > 0.0 and gap < 18.0:
			var oa = at(o.s); var olat = (Vector3(o.car.px, 0, o.car.pz) - oa[0]).dot(oa[2]) / oa[3]
			if abs(olat - lat) < 0.5: vt = minf(vt, o.car.speed + (gap - 8.0) * 0.7)
	c.in_gas = 1.0 if v < vt - 0.8 else (0.35 if v < vt else 0.0)
	c.in_brake = clampf((v - vt - 1.0) / 4.0, 0.0, 1.0); c.in_hand = false
	# crashed or off the road: back onto the route a little further back
	var here = at(r.s); var off = abs((Vector3(c.px, 0, c.pz) - here[0]).dot(here[2])) - here[3]
	var herr = abs(wrapf(atan2(here[1].x, here[1].z) - c.hd, -PI, PI))
	var bad = v < 2.0 or off > 3.5 or (herr > 1.0 and v < 6.0)
	r.stuck = r.stuck + dt * (1.6 if herr > 1.0 else 1.0) if bad else maxf(0.0, r.stuck - dt)
	if r.stuck > 2.0:            # spun, crashed or off the road: back onto the route at the first free spot nearby
		for back in [r.s - 8.0, r.s - 16.0, r.s + 10.0, r.s - 26.0]:
			back = clampf(back, START_S - 10.0, finish_s - 5.0)
			var b = at(back); var pp: Vector3 = b[0] + b[2] * r.line * b[3]; var free = true
			for o in racers:
				if o != r and Vector2(o.car.px - pp.x, o.car.pz - pp.z).length() < 7.0: free = false
			if free:
				if OS.get_environment("RACETEST") != "": print("RESCUE %s s %.0f off %.1f v %.1f at (%.0f %.0f) route (%.0f %.0f) herr %.2f" % [r.name, r.s, off, v, c.px, c.pz, here[0].x, here[0].z, herr])
				c.place(pp, atan2(b[1].x, b[1].z)); r.s = back; r.stuck = 0.0; r.shift = 0.0; break

func _steer_to(c: Car, tgt: Vector3) -> float:
	var want = atan2(tgt.x - c.px, tgt.z - c.pz); var err = wrapf(want - c.hd, -PI, PI)
	return clampf(-err * (2.2 + c.speed * 0.06), -1.0, 1.0)

func _player_checks(dt: float):
	var me = racers[0]
	if state != "race" or me.done: return
	var c: Car = me.car; var a = at(me.s); var lat = (Vector3(c.px, 0, c.pz) - a[0]).dot(a[2])
	while next_cp < cps.size() - 1 and me.s >= cps[next_cp]:
		if abs(lat) < a[3] + 4.0:
			next_cp += 1; _flash("CHECKPOINT  %s" % fmt(t), 1.4)
			for k in gates.size(): gates[k].visible = k >= next_cp + 1 and k <= next_cp + 3
		else: break
	var fwd = c.vx * a[1].x + c.vz * a[1].z
	wrong_t = wrong_t + dt if fwd < -3.0 else 0.0
	off_t = off_t + dt if abs(lat) > a[3] + 20.0 else 0.0
	msg.text = "WRONG WAY" if wrong_t > 1.2 else ("Off the route · tap Reset" if off_t > 1.0 else msg.text)
	if wrong_t <= 1.2 and off_t <= 1.0 and msg.get_meta("t", 0.0) <= 0.0: msg.text = ""

func reset_player():
	var s = START_S if next_cp == 0 else cps[next_cp - 1]
	var a = at(s); player.place(a[0], atan2(a[1].x, a[1].z)); racers[0].s = s; main.cam_yaw = player.hd

func _player_finished():
	next_cp = cps.size(); state = "result"; result_t = 0.0
	for g in gates: g.visible = false
	big.text = "FINISH"; big.visible = true

func standings() -> Array:
	var rs = racers.duplicate()
	rs.sort_custom(func(a, b):
		if a.done and b.done: return a.time < b.time
		if a.done != b.done: return a.done
		return a.s > b.s)
	return rs

# ---------------------------------------------------------------- HUD
func _make_hud():
	hud = Control.new(); hud.set_anchors_preset(Control.PRESET_FULL_RECT); hud.mouse_filter = Control.MOUSE_FILTER_IGNORE; main.hud.add_child(hud)
	var vs = get_viewport().get_visible_rect().size
	var bg = Panel.new(); var sb = Hud.panel_style(12); sb.border_color = Color(Hud.ACCENT.r, Hud.ACCENT.g, Hud.ACCENT.b, 0.5); sb.border_width_bottom = 3; bg.add_theme_stylebox_override("panel", sb)
	bg.size = Vector2(560, 50); bg.position = Vector2(vs.x / 2 - 280 - 20, 20); bg.mouse_filter = Control.MOUSE_FILTER_IGNORE; hud.add_child(bg)
	info = Label.new(); info.add_theme_font_size_override("font_size", 26); info.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	info.size = Vector2(560, 50); info.vertical_alignment = VERTICAL_ALIGNMENT_CENTER; bg.add_child(info)
	big = Label.new(); big.add_theme_font_size_override("font_size", 120); big.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.6)); big.add_theme_constant_override("outline_size", 10)
	big.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER; big.size = Vector2(vs.x, 160); big.position = Vector2(0, vs.y * 0.24); hud.add_child(big)
	msg = Label.new(); msg.add_theme_font_size_override("font_size", 32); msg.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.6)); msg.add_theme_constant_override("outline_size", 6)
	msg.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER; msg.size = Vector2(vs.x, 50); msg.position = Vector2(0, 76); hud.add_child(msg)

func _flash(s: String, d: float):
	msg.text = s; msg.set_meta("t", d)

func _process(dt):
	if not info: return
	var me = racers[0]; var st = standings(); var pos = st.find(me) + 1
	var b = best(id)
	if R.get("mode", "") == "drift":
		info.text = "SCORE %s   ·   %d%%%s" % [Menu._n(main.drift.total), int(100.0 * clampf((me.s - START_S) / (finish_s - START_S), 0, 1)), ("   ·   BEST " + Menu._n(int(b[0]))) if b[0] > 0 else ""]
	elif R.get("mode", "") == "trial":
		info.text = "CP %d/%d   ·   %s   ·   GOLD %s%s" % [mini(next_cp, cps.size()), cps.size(), fmt(me.time if me.done else t), fmt(R.medals[0]), ("   ·   BEST " + fmt(b[0])) if b[0] > 0 else ""]
	else:
		info.text = "POS %d/%d   ·   CP %d/%d   ·   %s%s" % [pos, racers.size(), mini(next_cp, cps.size()), cps.size(), fmt(me.time if me.done else t), ("   ·   BEST " + fmt(b[0])) if b[0] > 0 else ""]
	var mt: float = msg.get_meta("t", 0.0)
	if mt > 0: msg.set_meta("t", mt - dt)
	if state == "count":
		big.visible = true; big.text = str(int(ceil(count - 0.6))) if count > 0.6 else "GO"
		big.add_theme_color_override("font_color", Color(1, 0.75, 0.15) if count > 0.6 else Color(0.5, 1, 0.55))
	elif state == "race":
		big.visible = t < 0.8
	elif state == "result":
		result_t += dt
		var all_done = true
		for r in racers: all_done = all_done and r.done
		if panel == null and (all_done or result_t > 9.0): _results()

func _results():
	if R.has("mode"): _challenge_results(); return
	big.visible = false
	var st = standings(); var pos = st.find(racers[0]) + 1; var me = racers[0]
	var b = best(id); var new_best = b[0] <= 0.0 or me.time < b[0]
	var cf = ConfigFile.new(); cf.load(SAVE)
	if new_best: cf.set_value(id, "time", me.time)
	if b[1] == 0 or pos < b[1]: cf.set_value(id, "pos", pos)
	cf.save(SAVE)
	var prize = Progress.race_done(id, pos) if me.done else [0, ""]
	var vs = get_viewport().get_visible_rect().size
	panel = Panel.new(); var sb = Hud.panel_style(16); sb.bg_color = Color(0.03, 0.05, 0.08, 0.88); sb.border_color = Color(Hud.ACCENT.r, Hud.ACCENT.g, Hud.ACCENT.b, 0.5); sb.border_width_top = 3; panel.add_theme_stylebox_override("panel", sb)
	panel.size = Vector2(620, 470); panel.position = (vs - panel.size) / 2; hud.add_child(panel)
	var place = ["1st", "2nd", "3rd", "4th"][pos - 1]
	_l(panel, "%s  ·  %s" % [place, R.name], 40, Vector2(32, 22)).add_theme_color_override("font_color", Color(1, 0.8, 0.2) if pos == 1 else Color(1, 1, 1))
	_l(panel, ("New best time!  " if new_best else "Best  " + fmt(b[0]) + "   ") + "", 22, Vector2(34, 78)).modulate = Color(1, 1, 1, 0.75)
	var pl = _l(panel, ("+%s credits" % Menu._n(prize[0])) + (("   ·   %s is open" % prize[1]) if prize[1] != "" else ""), 22, Vector2(300, 78)); pl.add_theme_color_override("font_color", Hud.ACCENT)
	for k in st.size():
		var r = st[k]; var y = 124 + k * 50
		var row = _l(panel, "%d.  %s" % [k + 1, r.name], 28, Vector2(40, y)); if not r.rival: row.add_theme_color_override("font_color", Color(1, 0.8, 0.2))
		var tm = fmt(r.time) if r.done else "—"
		if r.done and k > 0 and st[0].done: tm += "   +%.2f" % (r.time - st[0].time)
		_l(panel, tm, 28, Vector2(330, y))
	_b(panel, "RETRY", Vector2(32, 360), func(): main.start_race(id))
	var nx = ORDER[(ORDER.find(id) + 1) % ORDER.size()]
	if Progress.is_open(nx): _b(panel, "NEXT RACE", Vector2(222, 360), func(): main.start_race(nx))
	_b(panel, "FREE ROAM", Vector2(412, 360), func(): main.end_race())
	emit_signal("finished")

func _challenge_results():          # drift score or lap time, a medal, and the prize for it
	big.visible = false; var me = racers[0]; var drift = R.mode == "drift"
	if drift: main.drift.bank()
	var v: float = float(main.drift.total) if drift else me.time
	var md = medal(id, v); var cf = ConfigFile.new(); cf.load(SAVE)
	var old: float = cf.get_value(id, "time", 0.0); var new_best = old <= 0.0 or (v > old if drift else v < old)
	if new_best: cf.set_value(id, "time", v)
	var bp = cf.get_value(id, "pos", 0)
	if bp == 0 or md < bp: cf.set_value(id, "pos", md)
	cf.save(SAVE)
	var prize = Progress.race_done(id, md) if md <= 3 else [0, ""]
	if OS.get_environment("RACETEST") != "": print("CHALLENGE %s value %.2f medal %s prize %s" % [id, v, MEDAL[md - 1], str(prize)])
	var vs = get_viewport().get_visible_rect().size
	panel = Panel.new(); var sb = Hud.panel_style(16); sb.bg_color = Color(0.03, 0.05, 0.08, 0.88); sb.border_color = Color(Hud.ACCENT.r, Hud.ACCENT.g, Hud.ACCENT.b, 0.5); sb.border_width_top = 3; panel.add_theme_stylebox_override("panel", sb)
	panel.size = Vector2(620, 400); panel.position = (vs - panel.size) / 2; hud.add_child(panel)
	var mcol = [Color(1, 0.8, 0.2), Color(0.85, 0.88, 0.92), Color(0.85, 0.55, 0.3), Color(1, 1, 1, 0.7)][md - 1]
	_l(panel, "%s  ·  %s" % [MEDAL[md - 1], R.name], 40, Vector2(32, 22)).add_theme_color_override("font_color", mcol)
	_l(panel, ("%s points" % Menu._n(int(v))) if drift else fmt(v), 56, Vector2(34, 84))
	_l(panel, ("New best!" if new_best else "Best  " + (Menu._n(int(old)) if drift else fmt(old))), 22, Vector2(36, 160)).modulate = Color(1, 1, 1, 0.75)
	var md_s = "Gold %s  ·  Silver %s  ·  Bronze %s" % ([Menu._n(R.medals[0]), Menu._n(R.medals[1]), Menu._n(R.medals[2])] if drift else [fmt(R.medals[0]), fmt(R.medals[1]), fmt(R.medals[2])])
	_l(panel, md_s, 20, Vector2(36, 196)).modulate = Color(1, 1, 1, 0.6)
	var pl = _l(panel, ("+%s credits" % Menu._n(prize[0])) + (("   ·   %s is open" % prize[1]) if prize[1] != "" else ""), 22, Vector2(36, 234)); pl.add_theme_color_override("font_color", Hud.ACCENT)
	_b(panel, "RETRY", Vector2(32, 300), func(): main.start_race(id))
	_b(panel, "FREE ROAM", Vector2(412, 300), func(): main.end_race())
	emit_signal("finished")

func _l(p: Control, s: String, sz: int, pos: Vector2) -> Label:
	var l = Label.new(); l.text = s; l.add_theme_font_size_override("font_size", sz); l.position = pos; p.add_child(l); return l
func _b(p: Control, s: String, pos: Vector2, cb: Callable):
	var b = Button.new(); b.text = s; b.position = pos; b.size = Vector2(176, 72); Hud.style_button(b); b.add_theme_font_size_override("font_size", 24); b.pressed.connect(cb); p.add_child(b)

func stop():
	for r in racers:
		if r.rival: r.car.queue_free()
	player.frozen = false; coll.dyn2 = []
	traffic.visible = true; traffic.process_mode = Node.PROCESS_MODE_INHERIT
	if tod_was >= 0: Tod.level = tod_was; Tod.apply(main)
	main.drift.on = true; main.drift.pay = true; main.drift.reset()
	if hud: hud.queue_free()
	queue_free()

extends Node3D
class_name Traffic
# Background traffic: the five hero-built traffic cars (hatch, saloon, SUV, van, pickup) drive the coast roads on the right-hand lane,
# keep their distance, brake for the player and are solid to the player's car. Each car has a near model (LOD0) and a light far model (LOD1).

const MODELS = ["hatch", "saloon", "suv", "van", "pickup"]
const RADIUS = { hatch = 0.335, saloon = 0.345, suv = 0.385, van = 0.40, pickup = 0.40 }
const WB = { hatch = Vector2(1.35, 1.475), saloon = Vector2(1.585, 1.475), suv = Vector2(1.55, 1.45), van = Vector2(1.58, 1.46), pickup = Vector2(1.84, 1.40) }   # front and rear axle distance from the body centre
const HALF = { hatch = Vector2(2.08, 0.90), saloon = Vector2(2.39, 0.94), suv = Vector2(2.36, 0.98), van = Vector2(2.41, 1.01), pickup = Vector2(2.71, 0.98) }
const PAINT = [Color(0.62, 0.63, 0.64), Color(0.45, 0.46, 0.48), Color(0.02, 0.02, 0.025), Color(0.06, 0.11, 0.24), Color(0.30, 0.02, 0.03),
	Color(0.07, 0.007, 0.016), Color(0.17, 0.33, 0.55), Color(0.40, 0.34, 0.25), Color(0.010, 0.032, 0.017), Color(0.20, 0.21, 0.22), Color(0.55, 0.42, 0.10)]
const LOD_SWITCH = 28.0
# road runs inside the coast slice: [road name, first point, last point, lane offset from the centre line]
const RUNS = [["Ring", 439, 736, 3.4], ["Peninsula Road", 22, 144, 2.4], ["West Avenue", 191, 259, 2.4], ["Lighthouse Road", 0, 48, 2.4]]

var lanes = []          # { p: PackedVector3Array, cum: PackedFloat32Array, len, off }
var cars = []           # { n, lane, dir, d, v, vmax, wheels, r, half }
var scenes = {}
var player: Car
var coll: Coll

func build(roads: Dictionary, count: int):
	for m in MODELS: scenes[m] = load("res://assets/traffic/%s.glb" % m)
	for run in RUNS:
		if not roads.has(run[0]): continue
		var src = roads[run[0]]; var p = PackedVector3Array(); var cum = PackedFloat32Array(); var acc = 0.0
		for i in range(run[1], run[2] + 1):
			var q = Vector3(src[i * 3], src[i * 3 + 1], src[i * 3 + 2])
			if p.size() > 0: acc += q.distance_to(p[p.size() - 1])
			p.append(q); cum.append(acc)
		lanes.append({ p = p, cum = cum, len = acc, off = run[3] })
	var total = 0.0
	for l in lanes: total += l.len
	var rng = RandomNumberGenerator.new(); rng.seed = 7
	for k in count:
		var pick = rng.randf() * total; var li = 0
		while li < lanes.size() - 1 and pick > lanes[li].len: pick -= lanes[li].len; li += 1
		var model: String = MODELS[k % MODELS.size()]
		var c = { lane = li, dir = 1 if rng.randf() < 0.5 else -1, d = clampf(pick, 10.0, lanes[li].len - 10.0), v = 0.0,
			vmax = rng.randf_range(11.0, 16.5) * (0.85 if model in ["van", "pickup"] else 1.0), r = RADIUS[model], half = HALF[model], wb = WB[model] }
		c.v = c.vmax
		for o in cars:
			if o.lane == c.lane and abs(o.d - c.d) < 20.0: c.d = fmod(c.d + 40.0, lanes[li].len - 20.0) + 10.0
		var n: Node3D = scenes[model].instantiate(); add_child(n); c.n = n; c.wheels = []
		_dress(n, rng.randi() % PAINT.size() if rng.randf() < 0.75 else -1, c)
		var ap = AudioStreamPlayer3D.new(); ap.stream = CarAudio.loop_stream("res://assets/audio/eng_2100.ogg"); ap.max_distance = 45.0; ap.unit_size = 4.0
		ap.attenuation_model = AudioStreamPlayer3D.ATTENUATION_INVERSE_DISTANCE; ap.position = Vector3(1.2, 0.6, 0); n.add_child(ap); ap.play(rng.randf() * 10.0); c.snd = ap
		var hp = AudioStreamPlayer3D.new(); hp.stream = load("res://assets/audio/horn.ogg"); hp.max_distance = 120.0; hp.unit_size = 14.0; hp.position = Vector3(1.8, 0.6, 0); n.add_child(hp); c.horn = hp; c.blocked = 0.0; c.honked = 0.0
		var sh = MeshInstance3D.new(); var q = QuadMesh.new(); q.size = Vector2(c.half.x * 2.5, c.half.y * 2.7); q.orientation = PlaneMesh.FACE_Y; sh.mesh = q
		sh.material_override = blob_material(); sh.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF; sh.position = Vector3(0, 0.035, 0); sh.visibility_range_end = 70.0; n.add_child(sh)
		cars.append(c)

# one paint per car, LOD ranges, wheel nodes for spinning
func _dress(n: Node3D, paint: int, c: Dictionary):
	var pm: StandardMaterial3D = null
	for mi in n.find_children("*", "MeshInstance3D", true, false):
		var lod1 = mi.get_parent() != null and String(mi.get_parent().name).begins_with("LOD1")
		if lod1: mi.visibility_range_begin = LOD_SWITCH; mi.visibility_range_begin_margin = 2.0
		else: mi.visibility_range_end = LOD_SWITCH; mi.visibility_range_end_margin = 2.0
		mi.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_DISABLED
		if String(mi.name).contains("_Wheel_"): c.wheels.append(mi)
		if String(mi.name).begins_with("GapLines"): mi.visibility_range_end = 14.0; mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if not lod1 else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		for i in mi.mesh.get_surface_count():
			var m = mi.mesh.surface_get_material(i)
			if not (m is StandardMaterial3D): continue
			if m.resource_name == "Paint":
				if pm == null:
					pm = m.duplicate(); pm.albedo_color = PAINT[paint] if paint >= 0 else m.albedo_color
					var mx = maxf(pm.albedo_color.r, maxf(pm.albedo_color.g, pm.albedo_color.b))
					if mx > 0.64: pm.albedo_color = pm.albedo_color * (0.64 / mx)          # white paint would burn out under the filmic sun
					pm.roughness = 0.22; pm.metallic_specular = 0.7
				mi.set_surface_override_material(i, pm)
			elif m.resource_name in ["Rim", "Chrome"] and String(mi.name).contains("_Wheel_"):
				if not c.has("rim"): c.rim = m.duplicate(); c.rim.roughness = maxf(m.roughness, 0.42); c.rim.metallic = minf(m.metallic, 0.7); c.rim.albedo_color = m.albedo_color.darkened(0.25)
				mi.set_surface_override_material(i, c.rim)
			elif m.resource_name in ["TailLED", "Tail"]:
				if not c.has("tail_" + m.resource_name):
					var tm: StandardMaterial3D = m.duplicate(); tm.emission_enabled = true; tm.emission = Color(1.0, 0.05, 0.03); tm.emission_energy_multiplier = 0.6 if m.resource_name == "TailLED" else 0.15
					c["tail_" + m.resource_name] = tm; c.tails = c.get("tails", []) + [tm]
				mi.set_surface_override_material(i, c["tail_" + m.resource_name])
			elif m.resource_name == "Tyre":
				if not c.has("tyre"): c.tyre = m.duplicate(); c.tyre.albedo_color = Color(0.05, 0.05, 0.052); c.tyre.roughness = 0.86; c.tyre.metallic_specular = 0.35
				mi.set_surface_override_material(i, c.tyre)
			elif m.resource_name == "Glass":
				var g: StandardMaterial3D = m.duplicate(); g.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA; g.albedo_color.a = 0.62; g.roughness = 0.04
				mi.set_surface_override_material(i, g)

func _respawn(c: Dictionary, pp: Vector3) -> bool:
	var cam = get_viewport().get_camera_3d()
	var opts = []
	for li in lanes.size():
		for e in [[2.0, 1], [lanes[li].len - 2.0, -1]]:
			var p: Vector3 = _at(lanes[li], e[0])[0]
			if p.distance_to(pp) < 110.0 or p.distance_to(c.n.global_position) < 40.0: continue
			if cam and cam.is_position_in_frustum(p + Vector3(0, 1, 0)) and p.distance_to(cam.global_position) < 400.0: continue      # never pop in where the player can see
			var free = true
			for o in cars:
				if o != c and o.lane == li and abs(o.d - e[0]) < 14.0: free = false
			if free: opts.append([li, e[0], e[1]])
	if opts.is_empty(): return false
	var o = opts[randi() % opts.size()]; c.lane = o[0]; c.d = o[1]; c.dir = o[2]; c.v = c.vmax * 0.6; c.erase("y")
	return true

static var _blob_mat: StandardMaterial3D
static func blob_material() -> StandardMaterial3D:
	if _blob_mat == null:
		var g = Gradient.new(); g.set_color(0, Color(0, 0, 0, 0.62)); g.set_color(1, Color(0, 0, 0, 0.0)); g.add_point(0.55, Color(0, 0, 0, 0.45))
		var t = GradientTexture2D.new(); t.gradient = g; t.fill = GradientTexture2D.FILL_RADIAL; t.fill_from = Vector2(0.5, 0.5); t.fill_to = Vector2(1.0, 0.5); t.width = 128; t.height = 128
		_blob_mat = StandardMaterial3D.new(); _blob_mat.albedo_texture = t; _blob_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		_blob_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED; _blob_mat.render_priority = 3; _blob_mat.depth_draw_mode = BaseMaterial3D.DEPTH_DRAW_DISABLED
	return _blob_mat

func _at(l: Dictionary, d: float) -> Array:
	var cum: PackedFloat32Array = l.cum; var p: PackedVector3Array = l.p
	var lo = 0; var hi = cum.size() - 1
	while hi - lo > 1:
		var mid = (lo + hi) >> 1
		if cum[mid] <= d: lo = mid
		else: hi = mid
	var seg = maxf(cum[hi] - cum[lo], 1e-3); var t = clampf((d - cum[lo]) / seg, 0.0, 1.0)
	return [p[lo].lerp(p[hi], t), (p[hi] - p[lo]).normalized()]

func _physics_process(dt):
	if lanes.is_empty(): return
	var pp = player.global_position if player else Vector3(1e9, 0, 0)
	var dyn = []
	var space = get_world_3d().direct_space_state
	for c in cars:
		var l = lanes[c.lane]
		# gap to the next car on the same lane and direction, and to the player if he is in our lane ahead
		var gap = 1e9
		for o in cars:
			if o == c or o.lane != c.lane or o.dir != c.dir: continue
			var g = (o.d - c.d) * c.dir
			if g > 0 and g < gap: gap = g
		var a = _at(l, c.d); var pos: Vector3 = a[0]; var t: Vector3 = a[1] * c.dir
		var right = Vector3(-t.z, 0, t.x).normalized()
		var me = pos + right * l.off
		# anything in the way in world space: the player, or another car where roads meet
		for o in cars:
			if o == c: continue
			var to_o: Vector3 = o.n.global_position - me; var ah = to_o.dot(t)
			if ah > 0 and ah < 20 and abs(to_o.dot(right)) < 2.4 and abs(to_o.y) < 3: gap = minf(gap, ah)
		var to_p = pp - me; var ahead = to_p.dot(t)
		var p_block = ahead > 0 and ahead < 30 and abs(to_p.dot(right)) < 2.6 and abs(to_p.y) < 4
		if p_block: gap = minf(gap, ahead)
		# a driver stuck behind the player gives a honk now and then
		c.honked = maxf(0.0, c.honked - dt)
		c.blocked = c.blocked + dt if (p_block and ahead < 16 and c.v < 2.0) else 0.0
		if c.blocked > 1.6 and c.honked <= 0.0: c.horn.pitch_scale = randf_range(0.92, 1.08); c.horn.play(); c.honked = randf_range(6.0, 11.0)
		var vt = c.vmax if gap > 32 else c.vmax * clampf((gap - 8.0) / 24.0, 0.0, 1.0)
		var braking = vt < c.v - 0.3
		c.v = move_toward(c.v, vt, (2.5 if vt > c.v else 7.0) * dt)
		if braking != c.get("braking", false):
			c.braking = braking
			for tm in c.get("tails", []): tm.emission_energy_multiplier = (3.2 if braking else 0.6) * (1.0 if tm.resource_name == "TailLED" else 0.5)
		c.d += c.v * c.dir * dt
		if c.d < 1.0 or c.d > l.len - 1.0:                      # left the map slice: come back in at a road end far from the player
			if not _respawn(c, pp): c.d = clampf(c.d, 1.0, l.len - 1.0); c.v = 0.0
			l = lanes[c.lane]; a = _at(l, c.d); pos = a[0]; t = a[1] * c.dir; right = Vector3(-t.z, 0, t.x).normalized()
		var at = pos + right * l.off
		# stand on four wheels: ray down at each contact patch, the body takes the plane through them so no tyre sinks into the camber
		var up = Vector3.UP; var t2 = Vector3(t.x, 0, t.z).normalized(); var r2 = Vector3(-t2.z, 0, t2.x)
		var hs = []; var n_ok = 0
		for q in [[c.wb.x, 1.0], [c.wb.x, -1.0], [-c.wb.y, 1.0], [-c.wb.y, -1.0]]:
			var wp = at + t2 * q[0] + r2 * (q[1] * c.half.y * 0.85)
			var hit = space.intersect_ray(PhysicsRayQueryParameters3D.create(wp + Vector3(0, 3.0, 0), wp - Vector3(0, 60.0, 0)))
			if hit and abs(hit.position.y - at.y) < 0.8 and hit.collider.get_meta("surf", "") == "road": hs.append(hit.position.y); n_ok += 1
			else: hs.append(at.y)
		c.ground = n_ok > 0
		var fy = (hs[0] + hs[1]) * 0.5; var ry = (hs[2] + hs[3]) * 0.5; var ly = (hs[0] + hs[2]) * 0.5; var ryy = (hs[1] + hs[3]) * 0.5
		var ax = t2 * (c.wb.x + c.wb.y) + Vector3(0, fy - ry, 0); var az = r2 * (2 * c.half.y * 0.85) + Vector3(0, ryy - ly, 0)
		up = az.cross(ax).normalized()
		if up.y < 0: up = -up
		if up.y < 0.8: up = Vector3.UP
		at.y = (fy * c.wb.y + ry * c.wb.x) / (c.wb.x + c.wb.y) + 0.012     # height under the body centre, a hair above so the tread never clips
		c.y = at.y if not c.has("y") else lerpf(c.y, at.y, clampf(dt * 8.0, 0.0, 1.0)); at.y = c.y           # no pops where the road mesh and the centre line disagree
		c.up = c.get("up", up).lerp(up, clampf(dt * 6.0, 0.0, 1.0)).normalized(); up = c.up
		var fw = (t - up * t.dot(up)).normalized(); var rt = fw.cross(up).normalized()
		var target = Transform3D(Basis(fw, up, rt), at)
		c.n.global_transform = target
		for w in c.wheels: w.rotate_object_local(Vector3(0, 0, 1), -c.v * dt / c.r)
		c.snd.pitch_scale = 0.72 + c.v / 38.0; c.snd.volume_db = -14.0 + 5.0 * clampf(c.v / 15.0, 0.0, 1.0)
		dyn.append([at.x, at.z, c.half.x, c.half.y, atan2(-fw.z, fw.x)])
	if coll: coll.dyn = dyn

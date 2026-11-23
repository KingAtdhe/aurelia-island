extends Node3D
class_name Traffic
# Background traffic: the five hero-built traffic cars (hatch, saloon, SUV, van, pickup) drive the coast roads on the right-hand lane,
# keep their distance, brake for the player and are solid to the player's car. Each car has a near model (LOD0) and a light far model (LOD1).

const MODELS = ["hatch", "saloon", "suv", "van", "pickup"]
const RADIUS = { hatch = 0.335, saloon = 0.345, suv = 0.385, van = 0.40, pickup = 0.40 }
const HALF = { hatch = Vector2(2.08, 0.90), saloon = Vector2(2.39, 0.94), suv = Vector2(2.36, 0.98), van = Vector2(2.41, 1.01), pickup = Vector2(2.71, 0.98) }
const PAINT = [Color(0.80, 0.81, 0.82), Color(0.62, 0.63, 0.65), Color(0.02, 0.02, 0.025), Color(0.06, 0.11, 0.24), Color(0.30, 0.02, 0.03),
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
			vmax = rng.randf_range(11.0, 16.5) * (0.85 if model in ["van", "pickup"] else 1.0), r = RADIUS[model], half = HALF[model] }
		c.v = c.vmax
		var n: Node3D = scenes[model].instantiate(); add_child(n); c.n = n; c.wheels = []
		_dress(n, rng.randi() % PAINT.size() if rng.randf() < 0.75 else -1, c)
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
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if not lod1 else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		for i in mi.mesh.get_surface_count():
			var m = mi.mesh.surface_get_material(i)
			if not (m is StandardMaterial3D): continue
			if m.resource_name == "Paint" and paint >= 0:
				if pm == null: pm = m.duplicate(); pm.albedo_color = PAINT[paint]
				mi.set_surface_override_material(i, pm)
			elif m.resource_name == "Glass":
				var g: StandardMaterial3D = m.duplicate(); g.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA; g.albedo_color.a = 0.62; g.roughness = 0.04
				mi.set_surface_override_material(i, g)

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
		var to_p = pp - pos; var ahead = to_p.dot(t); var side = to_p.dot(right) - l.off
		if ahead > 0 and ahead < 30 and abs(side) < 2.6 and abs(to_p.y) < 4: gap = minf(gap, ahead)
		var vt = c.vmax if gap > 32 else c.vmax * clampf((gap - 8.0) / 24.0, 0.0, 1.0)
		c.v = move_toward(c.v, vt, (2.5 if vt > c.v else 7.0) * dt)
		c.d += c.v * c.dir * dt
		if c.d < 2.0 or c.d > l.len - 2.0:                      # end of the run: come back the other way in the other lane
			c.dir = -c.dir; c.d = clampf(c.d, 2.0, l.len - 2.0)
			a = _at(l, c.d); pos = a[0]; t = a[1] * c.dir; right = Vector3(-t.z, 0, t.x).normalized()
		var at = pos + right * l.off
		var up = Vector3.UP
		var hit = space.intersect_ray(PhysicsRayQueryParameters3D.create(at + Vector3(0, 2.5, 0), at - Vector3(0, 3.0, 0)))
		if hit: at.y = hit.position.y; up = hit.normal if hit.normal.y > 0.8 else Vector3.UP
		c.up = c.get("up", up).lerp(up, clampf(dt * 6.0, 0.0, 1.0)).normalized(); up = c.up
		var fw = (t - up * t.dot(up)).normalized(); var rt = fw.cross(up).normalized()
		var target = Transform3D(Basis(fw, up, rt), at)
		c.n.global_transform = c.n.global_transform.interpolate_with(target, clampf(dt * 12.0, 0.0, 1.0)) if c.n.global_position.distance_to(at) < 3.0 else target
		for w in c.wheels: w.rotate_object_local(Vector3(0, 0, 1), -c.v * dt / c.r)
		dyn.append([at.x, at.z, c.half.x, c.half.y, atan2(-fw.z, fw.x)])
	if coll: coll.dyn = dyn

extends Node3D
class_name TyreFX
# Tyre smoke and skid marks for the player's car and the race rivals.
#  - Skid marks: rubber laid down by tyres that slide, spin or lock: one MultiMesh of short ribbon pieces (a ring buffer,
#    the oldest piece is reused), on the road surface under each wheel. Brown on dirt and sand, faint on grass, lighter
#    in the wet.
#  - Smoke: soft billboard puffs from the rear tyres (a pool, simulated here: they drift with the car's speed, rise,
#    grow and fade). Dust off the road, a thin spray in the rain, darker and dimmer at night.
# Both are one draw call each. Counts follow the graphics level.
const MARKS = [500, 1100, 1800]
const PUFFS = [36, 70, 110]
const WIDTH = 0.24          # rubber width of one mark (m)
const STEP = 0.32           # a new piece of mark every this far

var cars := []              # Car nodes that leave marks and smoke
var _st := {}               # car instance id -> per-wheel state
var marks: MultiMesh; var mark_i := 0; var _mark_mi: MultiMeshInstance3D
var puffs: MultiMesh; var _puff_mi: MultiMeshInstance3D; var smoke_mat: ShaderMaterial
var P := []                 # puffs: [pos, vel, age, life, size0, size1, alpha, rot, spin, colour]
var puff_i := 0
var _rate := {}             # spawn accumulators

func _init(): name = "TyreFX"; physics_interpolation_mode = Node.PHYSICS_INTERPOLATION_MODE_OFF

func build():
	var lv = Gfx.get_level()
	# marks
	marks = MultiMesh.new(); marks.transform_format = MultiMesh.TRANSFORM_3D; marks.use_colors = true
	marks.mesh = _strip(); marks.instance_count = MARKS[lv]
	for i in marks.instance_count: marks.set_instance_transform(i, Transform3D(Basis().scaled(Vector3.ZERO), Vector3(0, -1000, 0))); marks.set_instance_color(i, Color(0, 0, 0, 0))
	var mm := ShaderMaterial.new(); mm.shader = load("res://shaders/skid.gdshader")
	_mark_mi = MultiMeshInstance3D.new(); _mark_mi.multimesh = marks; _mark_mi.material_override = mm; _mark_mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_mark_mi.custom_aabb = AABB(Vector3(-5000, -500, -5000), Vector3(10000, 1500, 10000)); add_child(_mark_mi)
	# smoke
	puffs = MultiMesh.new(); puffs.transform_format = MultiMesh.TRANSFORM_3D; puffs.use_colors = true; puffs.use_custom_data = true
	var q := QuadMesh.new(); q.size = Vector2(1, 1); puffs.mesh = q; puffs.instance_count = PUFFS[lv]
	smoke_mat = ShaderMaterial.new(); smoke_mat.shader = load("res://shaders/smoke.gdshader")
	var nt := NoiseTexture2D.new(); nt.width = 128; nt.height = 128; nt.seamless = true; var fn := FastNoiseLite.new(); fn.frequency = 0.035; fn.fractal_octaves = 4; nt.noise = fn
	smoke_mat.set_shader_parameter("noise", nt)
	_puff_mi = MultiMeshInstance3D.new(); _puff_mi.multimesh = puffs; _puff_mi.material_override = smoke_mat; _puff_mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	_puff_mi.custom_aabb = AABB(Vector3(-5000, -500, -5000), Vector3(10000, 1500, 10000)); add_child(_puff_mi)
	P.clear()
	for i in puffs.instance_count:
		P.append([Vector3.ZERO, Vector3.ZERO, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, Color.WHITE])
		puffs.set_instance_transform(i, Transform3D(Basis().scaled(Vector3.ZERO), Vector3(0, -1000, 0))); puffs.set_instance_color(i, Color(1, 1, 1, 0)); puffs.set_instance_custom_data(i, Color(0, 0, 0, 0))

func rebuild():          # graphics level changed
	for c in get_children(): c.queue_free()
	mark_i = 0; puff_i = 0; build()

func add_car(c: Car): if not cars.has(c): cars.append(c)
func clear_marks():
	for i in marks.instance_count: marks.set_instance_color(i, Color(0, 0, 0, 0))

# a flat strip 1 m long (x) and 1 m wide (z), across-uv in UV.y for the soft edges of the rubber
func _strip() -> ArrayMesh:
	var a = []; a.resize(Mesh.ARRAY_MAX)
	a[Mesh.ARRAY_VERTEX] = PackedVector3Array([Vector3(-0.5, 0, -0.5), Vector3(0.5, 0, -0.5), Vector3(0.5, 0, 0.5), Vector3(-0.5, 0, 0.5)])
	a[Mesh.ARRAY_NORMAL] = PackedVector3Array([Vector3.UP, Vector3.UP, Vector3.UP, Vector3.UP])
	a[Mesh.ARRAY_TEX_UV] = PackedVector2Array([Vector2(0, 0), Vector2(1, 0), Vector2(1, 1), Vector2(0, 1)])
	a[Mesh.ARRAY_COLOR] = PackedColorArray([Color.WHITE, Color.WHITE, Color.WHITE, Color.WHITE])
	a[Mesh.ARRAY_INDEX] = PackedInt32Array([0, 2, 1, 0, 3, 2])
	var m = ArrayMesh.new(); m.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, a); return m

# how hard each tyre is sliding: [rear, front], 0..1
static func slide(c: Car) -> Vector2:
	if c.air or c.frozen: return Vector2.ZERO
	var v = c.speed
	var side = clampf((abs(c.beta) - 0.1) / 0.28, 0.0, 1.0) * clampf((v - 4.0) / 8.0, 0.0, 1.0)
	var rear = side
	if c.spin and v > 0.8 and v < 30.0: rear = maxf(rear, clampf(0.55 + c.thr * 0.4, 0.0, 1.0))          # wheelspin
	if c.in_hand and v > 3.0: rear = maxf(rear, 0.85)          # handbrake: locked rear
	var front = clampf((abs(c.beta) - 0.4) / 0.4, 0.0, 1.0) * clampf((v - 6.0) / 8.0, 0.0, 1.0) * 0.6 + clampf((abs(c.af) - 0.16) / 0.2, 0.0, 1.0) * 0.5 * clampf((v - 8.0) / 8.0, 0.0, 1.0)
	return Vector2(rear, minf(front, 1.0))

const SURF_MARK = { road = Color(0.02, 0.02, 0.022, 0.62), dirt = Color(0.2, 0.15, 0.1, 0.45), sand = Color(0.32, 0.25, 0.16, 0.4), grass = Color(0.12, 0.13, 0.06, 0.32), snow = Color(0.5, 0.52, 0.56, 0.4) }
const SURF_SMOKE = { road = Color(0.92, 0.92, 0.93), dirt = Color(0.62, 0.52, 0.4), sand = Color(0.8, 0.7, 0.52), grass = Color(0.55, 0.5, 0.38), snow = Color(0.95, 0.96, 1.0) }

func _process(dt):
	var _p0 = Time.get_ticks_usec()
	if marks == null: return
	var space = get_world_3d().direct_space_state
	var wet = Weather.get_level() > 0
	var live := []
	for c in cars:
		if not is_instance_valid(c) or not c.is_inside_tree(): continue
		live.append(c)
		var s = slide(c); var key = c.get_instance_id()
		if not _st.has(key): _st[key] = [null, null, null, null]
		var xf: Transform3D = c.get_global_transform_interpolated()
		var C = Car.CARS[c.car_id]; var hw: float = C.half.y - 0.2
		var wheels = [[-c.V.b, -hw, s.x], [-c.V.b, hw, s.x], [c.V.a, -hw, s.y], [c.V.a, hw, s.y]]
		var mark_c: Color = SURF_MARK.get(c.surf, SURF_MARK.grass)
		for w in 4:
			var wp: Vector3 = xf * Vector3(wheels[w][1], 0.0, wheels[w][0]); var k: float = wheels[w][2]
			var last = _st[key][w]
			if k < 0.06:
				_st[key][w] = null; continue
			if last == null: _st[key][w] = [wp, k]; continue
			var d = Vector2(wp.x - last[0].x, wp.z - last[0].z).length()
			if d < STEP: continue
			if d > 3.0: _st[key][w] = [wp, k]; continue          # a jump (reset, rescue): start a new mark
			var a = last[0]; var b = wp
			var hit = space.intersect_ray(PhysicsRayQueryParameters3D.create(b + Vector3(0, 1.2, 0), b - Vector3(0, 2.5, 0), 1))
			if hit: b = hit.position
			else: b.y = a.y
			var n: Vector3 = hit.normal if hit else Vector3.UP
			var fwd = (b - a); var ln = fwd.length(); fwd /= ln
			var side = n.cross(fwd).normalized(); var up = fwd.cross(side).normalized()
			var col = mark_c; col.a *= clampf((k + last[1]) * 0.5, 0.0, 1.0) * (0.55 if wet else 1.0)
			marks.set_instance_transform(mark_i, Transform3D(Basis(fwd * (ln + 0.04), up, side * WIDTH), (a + b) * 0.5 + up * 0.012))
			marks.set_instance_color(mark_i, col)
			mark_i = (mark_i + 1) % marks.instance_count
			_st[key][w] = [b, k]
		# smoke from the rear tyres
		if s.x > 0.12:
			var sm: Color = SURF_SMOKE.get(c.surf, SURF_SMOKE.grass)
			var amount = s.x * clampf(0.35 + c.speed / 22.0, 0.35, 1.4) * (0.35 if wet and c.surf == "road" else 1.0) * (0.6 if c.surf == "grass" else 1.0)
			var acc: float = _rate.get(key, 0.0) + dt * 26.0 * amount
			while acc >= 1.0:
				acc -= 1.0
				var side = 1.0 if randf() < 0.5 else -1.0
				var p0: Vector3 = xf * Vector3(side * hw, 0.25, -c.V.b - 0.2)
				_puff(p0, Vector3(c.vx, 0.0, c.vz), sm, clampf(amount, 0.2, 1.0), wet and c.surf == "road")
			_rate[key] = acc
	cars = live
	_step_puffs(dt)
	Prof.add("tyrefx", Time.get_ticks_usec() - _p0)

func _puff(p: Vector3, cv: Vector3, col: Color, k: float, spray: bool):
	var i = puff_i; puff_i = (puff_i + 1) % P.size()
	var v = cv * randf_range(0.12, 0.3) + Vector3(randf_range(-0.8, 0.8), randf_range(0.25, 0.8), randf_range(-0.8, 0.8))
	var life = randf_range(1.6, 2.8) * (0.6 if spray else 1.0)
	P[i] = [p + Vector3(randf_range(-0.2, 0.2), 0.0, randf_range(-0.2, 0.2)), v, 0.0, life, randf_range(0.6, 0.9), randf_range(2.6, 3.8) * (0.7 if spray else 1.0),
		k * (0.32 if spray else 0.5), randf() * TAU, randf_range(-0.6, 0.6), col]

func _step_puffs(dt: float):
	var cam = get_viewport().get_camera_3d()
	var cp: Vector3 = cam.global_position if cam else Vector3.ZERO
	var night = Tod.night(); var eyes = 0.0
	var m = get_parent(); if m and "eyes" in m: eyes = m.eyes
	var lit = lerpf(1.0, 0.22, night) * lerpf(1.0, 0.5, eyes) * (0.85 if Weather.get_level() > 0 else 1.0)
	smoke_mat.set_shader_parameter("light", Color(lit, lit * (0.97 if Tod.get_level() != 1 else 0.88), lit * (0.95 if Tod.get_level() != 1 else 0.8)))
	for i in P.size():
		var q = P[i]
		if q[2] >= q[3]:
			if q[6] > 0.0: q[6] = 0.0; puffs.set_instance_color(i, Color(1, 1, 1, 0)); puffs.set_instance_transform(i, Transform3D(Basis().scaled(Vector3.ZERO), Vector3(0, -1000, 0)))
			continue
		q[2] += dt; var f = q[2] / q[3]
		q[1] *= exp(-dt * 1.6); q[1].y += dt * 0.25; q[0] += q[1] * dt; q[7] += q[8] * dt
		var sz = lerpf(q[4], q[5], 1.0 - pow(1.0 - f, 2.0))
		var a = q[6] * clampf(q[2] / 0.12, 0.0, 1.0) * pow(1.0 - f, 1.6)
		a *= clampf((q[0].distance_to(cp) - 1.0) / 2.5, 0.0, 1.0)          # thin out right at the camera (no grey screen, less overdraw)
		var col: Color = q[9]; col.a = a
		puffs.set_instance_transform(i, Transform3D(Basis().scaled(Vector3.ONE * sz), q[0] + Vector3(0, sz * 0.3, 0)))
		puffs.set_instance_color(i, col); puffs.set_instance_custom_data(i, Color(q[7], f, 0, 0))

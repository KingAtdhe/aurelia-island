extends Node3D
class_name Grass
# Dense modelled grass round the car (source/godot_tools/grass_models.py, art sheet concept 14): clumps scattered on the
# island's grassy ground in 12 m cells out to 40 m, full clumps close up and light ones further out, one MultiMesh per
# type and detail level for the whole ring. Which grass grows where comes from the ground under each spot (raycast onto
# the map colliders) and the region: meadow on fields and coast, lawn in the city and on the mountains, dry grass in the
# desert and the countryside's dry patches, forest grass under the trees, marram grass on the dunes.
const CELL = 12.0
var R_FAR := 40.0           # set by the graphics level (0 = no modelled grass)
const R_NEAR = 10.0
const TYPES = ["meadow", "lawn", "dry", "forest", "dune"]
const SPACING = 1.2          # metres between clumps on full ground

var focus := Vector3.ZERO
var cells := {}               # Vector2i -> { type -> PackedFloat32Array (x y z yaw scale r g b) }
var mm := {}                  # "type:lod" -> MultiMeshInstance3D
var regions = []
var coll: Coll          # roads and trails stay clear of grass
var _last := Vector3(1e9, 0, 0)
var _t := 0.0
var _pending := []
var gmat: ShaderMaterial
func set_radius(r: float):
	R_FAR = r; visible = r > 0.0; set_process(r > 0.0); if gmat: gmat.set_shader_parameter("fade_far", maxf(r, 1.0))
	cells.clear(); _last = Vector3(1e9, 0, 0)

func build(world: Dictionary):
	regions = world["regions"]
	var sc = load("res://assets/grass.glb").instantiate()
	var mat = ShaderMaterial.new(); mat.shader = load("res://shaders/grass.gdshader"); mat.set_shader_parameter("bake", Look._bake()); mat.set_shader_parameter("fade_far", R_FAR); gmat = mat
	for t in TYPES:
		for lod in [0, 1]:
			var mi: MeshInstance3D = sc.find_child("G_%s_LOD%d" % [t, lod], true, false)
			var mesh: Mesh = mi.mesh.duplicate(); mesh.surface_set_material(0, mat)
			var m = MultiMesh.new(); m.transform_format = MultiMesh.TRANSFORM_3D; m.use_colors = true; m.mesh = mesh
			var n = MultiMeshInstance3D.new(); n.multimesh = m; n.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			add_child(n); mm["%s:%d" % [t, lod]] = n
	sc.free()

func _region(x: float, z: float) -> String:
	var best = ""; var bd = 1e9
	for r in regions:
		var d = pow((x - r["x"]) / r["rx"], 2) + pow((z - r["z"]) / r["rz"], 2)
		if d < bd: bd = d; best = r["name"]
	return best if bd < 1.6 else ""

static func _h(i: int) -> float:          # cheap repeatable hash -> 0..1
	var x = (i * 374761393 + 668265263) & 0x7fffffff; x = ((x ^ (x >> 13)) * 1274126177) & 0x7fffffff
	return float(x & 0xffff) / 65535.0

# the grass of one cell: jittered grid, a ray onto the ground at each spot, the ground and the region pick the type
func _make_cell(key: Vector2i) -> Dictionary:
	var out := {}
	var space = get_world_3d().direct_space_state
	var q = PhysicsRayQueryParameters3D.new(); q.collision_mask = 1
	var n = int(CELL / SPACING); var reg = _region((key.x + 0.5) * CELL, (key.y + 0.5) * CELL)
	var seed0 = (key.x * 73856093) ^ (key.y * 19349663)
	for i in n:
		for j in n:
			var s = seed0 + i * 131 + j * 7919
			var x = (key.x + (i + _h(s)) / n) * CELL; var z = (key.y + (j + _h(s + 1)) / n) * CELL
			q.from = Vector3(x, focus.y + 80.0, z); q.to = Vector3(x, focus.y - 120.0, z)
			var hit = space.intersect_ray(q)
			if hit.is_empty(): continue
			var nm = String(hit.collider.get_parent().name); var u = _h(s + 2)
			if hit.normal.y < 0.8: continue          # cliffs and steep banks stay bare
			if coll:
				var rq = coll.road_query(x, z, hit.position.y)
				if rq.ok and abs(rq.d) < rq.r.hw + 0.6: continue
			var t = ""
			if nm.begins_with("TerrainForest"): t = "forest"
			elif nm.begins_with("TerrainSand"): t = "dune" if u < 0.22 else ""
			elif nm.begins_with("TerrainField"): t = "meadow" if u < 0.85 else ("dry" if u < 0.93 else "")
			elif nm.begins_with("Terrain__"):
				match reg:
					"Desert": t = "dry" if u < 0.45 else ""
					"City", "Harbour": t = "lawn"
					"Mountain Roads": t = "lawn" if u < 0.7 else ("meadow" if u < 0.9 else "")
					"Forest Trails": t = "forest" if u < 0.6 else "meadow"
					"Countryside", "Coastal Highway": t = "meadow" if u < 0.88 else "dry"
					_: t = "meadow" if u < 0.8 else "dry"
			elif nm.begins_with("Verge"): t = "lawn" if u < 0.25 else ""
			if t == "": continue
			if not out.has(t): out[t] = PackedFloat32Array()
			var tint = 0.86 + 0.28 * _h(s + 3)
			out[t].append_array([x, hit.position.y - 0.02, z, _h(s + 4) * TAU, 1.05 + 0.65 * _h(s + 5), tint, tint * (0.95 + 0.1 * _h(s + 6)), tint * 0.95])
	return out

func _process(dt):
	_t -= dt
	if _t > 0: return
	_t = 0.15
	var c = Vector2i(floori(focus.x / CELL), floori(focus.z / CELL)); var rc = int(ceil(R_FAR / CELL)) + 1
	# cells to make: nearest first, a few per tick so nothing stalls
	var want := {}
	for ix in range(c.x - rc, c.x + rc + 1):
		for iz in range(c.y - rc, c.y + rc + 1):
			var k = Vector2i(ix, iz); var cc = (Vector2(k) + Vector2(0.5, 0.5)) * CELL
			if cc.distance_to(Vector2(focus.x, focus.z)) < R_FAR + CELL: want[k] = true
	var made = 0
	var todo = want.keys().filter(func(k): return not cells.has(k))
	todo.sort_custom(func(a, b): return (Vector2(a) * CELL).distance_squared_to(Vector2(focus.x, focus.z)) < (Vector2(b) * CELL).distance_squared_to(Vector2(focus.x, focus.z)))
	for k in todo:
		if made >= 4: break
		cells[k] = _make_cell(k); made += 1
	for k in cells.keys():
		if not want.has(k): cells.erase(k)
	if made > 0 or focus.distance_to(_last) > 4.0: _rebuild(); _last = focus

func _rebuild():
	var bufs := {}
	var f2 = Vector2(focus.x, focus.z)
	for k in cells:
		var cd = cells[k]
		for t in cd:
			var a: PackedFloat32Array = cd[t]
			for i in range(0, a.size(), 8):
				var d = Vector2(a[i] - f2.x, a[i + 2] - f2.y).length()
				if d > R_FAR: continue
				var key = "%s:%d" % [t, 0 if d < R_NEAR else 1]
				if not bufs.has(key): bufs[key] = PackedFloat32Array()
				var s = a[i + 4]; var cy = cos(a[i + 3]) * s; var sy = sin(a[i + 3]) * s
				bufs[key].append_array([cy, 0.0, sy, a[i], 0.0, s, 0.0, a[i + 1], -sy, 0.0, cy, a[i + 2], a[i + 5], a[i + 6], a[i + 7], 1.0])
	for key in mm:
		var m: MultiMesh = mm[key].multimesh
		var b: PackedFloat32Array = bufs.get(key, PackedFloat32Array())
		m.instance_count = b.size() / 16
		if b.size() > 0: m.buffer = b

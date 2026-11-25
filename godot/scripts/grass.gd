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
var SPACING = 1.2          # metres between clumps on full ground (1.5 on MEDIUM)

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
	R_FAR = r; SPACING = 1.2 if r >= 40.0 else 1.5; visible = r > 0.0; set_process(r > 0.0); if gmat: gmat.set_shader_parameter("fade_far", maxf(r, 1.0))
	cells.clear(); _last = Vector3(1e9, 0, 0); _shown = []

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
	var segs := PackedFloat32Array()          # road segments that reach this cell: x0 z0 x1 z1 half width (checked per clump, cheaply)
	if coll:
		var c0 = Vector2(key.x * CELL, key.y * CELL)
		var g0 = Vector2i(floori(c0.x / Coll.SG), floori(c0.y / Coll.SG)); var g1 = Vector2i(floori((c0.x + CELL) / Coll.SG), floori((c0.y + CELL) / Coll.SG))
		for ax in range(g0.x - 1, g1.x + 2):
			for az in range(g0.y - 1, g1.y + 2):
				var a = coll.seg.get(Vector2i(ax, az))
				if a == null: continue
				for qi in range(0, a.size(), 2):
					var r = coll.roads[a[qi]]; var i: int = a[qi + 1]; var p: PackedFloat32Array = r.p
					var x0 = p[i * 3]; var z0 = p[i * 3 + 2]; var x1 = p[i * 3 + 3]; var z1 = p[i * 3 + 5]; var hw = r.hw + 0.6
					if maxf(x0, x1) < c0.x - hw or minf(x0, x1) > c0.x + CELL + hw or maxf(z0, z1) < c0.y - hw or minf(z0, z1) > c0.y + CELL + hw: continue
					segs.append_array([x0, z0, x1, z1, hw])
	var near_road = segs.size() > 0
	for i in n:
		for j in n:
			var s = seed0 + i * 131 + j * 7919
			var x = (key.x + (i + _h(s)) / n) * CELL; var z = (key.y + (j + _h(s + 1)) / n) * CELL
			q.from = Vector3(x, focus.y + 80.0, z); q.to = Vector3(x, focus.y - 120.0, z)
			var hit = space.intersect_ray(q)
			if hit.is_empty(): continue
			var nm = String(hit.collider.get_parent().name); var u = _h(s + 2)
			if hit.normal.y < 0.8: continue          # cliffs and steep banks stay bare
			if near_road and (nm.begins_with("Terrain__") or nm.begins_with("Verge")):          # roads and tracks stay bare
				var on_road = false
				for si in range(0, segs.size(), 5):
					var ax0 = segs[si]; var az0 = segs[si + 1]; var dx = segs[si + 2] - ax0; var dz = segs[si + 3] - az0; var L2 = dx * dx + dz * dz
					var tt = clampf(((x - ax0) * dx + (z - az0) * dz) / maxf(L2, 1e-6), 0.0, 1.0)
					var ex = x - ax0 - dx * tt; var ez = z - az0 - dz * tt
					if ex * ex + ez * ez < segs[si + 4] * segs[si + 4]: on_road = true; break
				if on_road: continue
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
			var tint = 0.86 + 0.28 * _h(s + 3); var sc = 1.05 + 0.65 * _h(s + 5); var yw = _h(s + 4) * TAU
			var cy = cos(yw) * sc; var sy = sin(yw) * sc          # the MultiMesh rows, ready to copy in
			out[t].append_array([cy, 0.0, sy, x, 0.0, sc, 0.0, hit.position.y - 0.02, -sy, 0.0, cy, z, tint, tint * (0.95 + 0.1 * _h(s + 6)), tint * 0.95, 1.0])
	return out

func _process(dt):
	var _p0 = Time.get_ticks_usec(); _process_body(dt); Prof.add("grass", Time.get_ticks_usec() - _p0)
func _process_body(dt):
	_t -= dt
	if _t > 0: return
	_t = 0.15
	# at speed the ring shrinks: the grass streaks past and the CPU is better spent elsewhere
	var spd = main_car.speed if main_car else 0.0
	var rr = R_FAR * lerpf(1.0, 0.6, clampf((spd - 18.0) / 30.0, 0.0, 1.0))
	var c = Vector2i(floori(focus.x / CELL), floori(focus.z / CELL)); var rc = int(ceil(rr / CELL)) + 1
	var want := {}
	for ix in range(c.x - rc, c.x + rc + 1):
		for iz in range(c.y - rc, c.y + rc + 1):
			var k = Vector2i(ix, iz); var cc = (Vector2(k) + Vector2(0.5, 0.5)) * CELL
			if cc.distance_to(Vector2(focus.x, focus.z)) < rr + CELL * 0.75: want[k] = true
	var made = 0
	var todo = want.keys().filter(func(k): return not cells.has(k))
	todo.sort_custom(func(a, b): return (Vector2(a) * CELL).distance_squared_to(Vector2(focus.x, focus.z)) < (Vector2(b) * CELL).distance_squared_to(Vector2(focus.x, focus.z)))
	for k in todo:
		if made >= 2: break
		cells[k] = _make_cell(k); made += 1
	if cells.size() > 700:          # cells are kept for a while (driving back costs nothing); far ones go
		for k in cells.keys():
			if (Vector2(k) * CELL).distance_to(Vector2(focus.x, focus.z)) > 260.0: cells.erase(k)
	var set_key = want.keys(); set_key.sort()
	if made > 0 or set_key != _shown or focus.distance_to(_last) > 8.0: _rebuild(want); _last = focus; _shown = set_key

var _shown = []
var main_car: Node
func _rebuild(want: Dictionary):          # copies the ready rows of the cells in the ring (full clumps in the cells nearest the car)
	var bufs := {}
	var f2 = Vector2(focus.x, focus.z)
	for k in want:
		if not cells.has(k): continue
		var cd = cells[k]; var d = ((Vector2(k) + Vector2(0.5, 0.5)) * CELL).distance_to(f2)
		var lod = 0 if d < R_NEAR + CELL * 0.6 else 1
		for t in cd:
			var key = "%s:%d" % [t, lod]
			if not bufs.has(key): bufs[key] = PackedFloat32Array()
			bufs[key].append_array(cd[t])
	for key in mm:
		var m: MultiMesh = mm[key].multimesh
		var b: PackedFloat32Array = bufs.get(key, PackedFloat32Array())
		m.instance_count = b.size() / 16
		if b.size() > 0: m.buffer = b

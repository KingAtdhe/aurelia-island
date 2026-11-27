extends Node3D
class_name Flora
# Trees, plants, rocks, houses and street furniture of the whole island (source/godot_tools/export_flora.py), drawn as
# MultiMeshes per 250 m patch with a near and a far version that swap by distance. Patches are built when the car comes
# near and dropped again behind it; buildings and big rocks are built everywhere at the start (seen from far away).
# Instance data: x y z scale yaw r g b per object.
const DIR = "res://assets/island/"
const CELL = 250.0
# kinds: near model up to r0, far model from r0 to r1 (0 = none); built within r_end + 180 m, dropped past r_end + 380 m
const KIND = { small = [45.0, 0.0], tree = [60.0, 210.0], bld = [130.0, 1100.0], solid = [75.0, 260.0], tiny = [55.0, 140.0] }

var lib := {}                  # model -> { 0: [[mesh, transform]], 1: [...] }
var data: PackedFloat32Array
var species := {}              # sp -> { off, n, model, kind }
var cells := {}                # Vector2i -> { c: Vector2 centre, sp: { sp: PackedInt32Array of instance numbers }, built: { kind: [nodes] } }
var hidden := {}               # "sp:k" -> true (knocked over)
var focus := Vector3.ZERO
var _t := 0.0
var n_inst := 0

static func kind_of(sp: String, info: Dictionary) -> String:
	if sp.begins_with("grass") or sp.begins_with("flowers") or sp == "fern": return "small"
	if sp.begins_with("prop_house") or sp.begins_with("prop_barn") or sp.begins_with("prop_farmhouse") or sp.begins_with("rock_t") or sp in ["prop_lookout", "prop_desert_stop", "prop_shelter", "prop_shelter_hq", "prop_windpump", "prop_beach_bar", "prop_lifeguard", "prop_breakwater", "sandstone"]: return "bld"
	if sp.begins_with("prop_tcar") or sp.begins_with("prop_rk_") or sp.begins_with("prop_reflector") or sp.begins_with("prop_cones") or sp in ["prop_bin", "prop_bin_hq", "prop_hydrant", "prop_mailbox", "prop_mailbox_hq", "prop_newsbox", "prop_trashbags", "prop_bikerack", "prop_scooter", "prop_scooter_hq", "prop_planter", "prop_planter_hq", "prop_bollard_hq"]: return "tiny"
	if info.get("card", -1) >= 0 or sp.begins_with("tree") or sp.begins_with("spruce") or sp.begins_with("palm") or sp in ["oak", "oak_b", "pine", "plane", "plane_b", "birch", "cypress", "fruit"]: return "tree"
	return "solid"

func build(spawn: Vector3):
	focus = spawn
	var untinted := {}          # Saba's Tripo models are textured and shaded in Blender: no per-instance tint (as in the web game)
	for f in ["flora_flora", "flora_kit", "flora_tprops", "flora_trees15"]:
		if not ResourceLoader.exists(DIR + f + ".glb"): continue
		var sc = load(DIR + f + ".glb").instantiate(); add_child(sc); Look.props = true; Look.apply(sc); Look.props = false; sc.visible = false
		for n in sc.get_children():
			var m = String(n.name)
			if not m.begins_with("S_"): continue
			m = m.substr(2); var lod = int(m.substr(m.length() - 1)); var model = m.substr(0, m.length() - 5)
			var parts := []
			for mi in ([n] if n is MeshInstance3D else []) + n.find_children("*", "MeshInstance3D", true, false):
				var mesh: Mesh = mi.mesh.duplicate()
				for si in mesh.get_surface_count():
					var o = mi.get_surface_override_material(si)
					if o == null: o = mesh.surface_get_material(si)
					mesh.surface_set_material(si, _tinted(o))
				parts.append([mesh, sc.global_transform.affine_inverse() * mi.global_transform])
			if not lib.has(model): lib[model] = {}
			lib[model][lod] = parts
			if f == "flora_tprops": untinted[model] = true
		sc.queue_free()
	var idx = JSON.parse_string(FileAccess.get_file_as_string(DIR + "flora.json"))
	data = FileAccess.get_file_as_bytes(DIR + "flora.bin").to_float32_array()
	for sp in idx["species"]:
		var model: String = idx["model"][sp]
		if lib.has("h_" + sp) and Look.LOOK2: model = "h_" + sp          # concept 15: the concept 04 trees instead of the Tripo trees
		if not lib.has(model) or sp in ["grass", "grass_tall"]: continue          # the old grass cards: the modelled grass (grass.gd) took over
		var off = int(idx["species"][sp][0]); var cnt = int(idx["species"][sp][1])
		species[sp] = { off = off, n = cnt, model = model, kind = kind_of(sp, idx["info"].get(sp, {})), tint = not untinted.has(model) }
		var per := {}
		for k in cnt:
			var i = off + k * 8
			var key = Vector2i(floori(data[i] / CELL), floori(data[i + 2] / CELL))
			if not per.has(key): per[key] = PackedInt32Array()
			per[key].append(k)
		for key in per:
			if not cells.has(key): cells[key] = { c = (Vector2(key) + Vector2(0.5, 0.5)) * CELL, sp = {}, built = {} }
			cells[key].sp[sp] = per[key]
		n_inst += cnt
	for key in cells: _update_cell(cells[key], 99)
	_cards(idx["info"])
	print("flora: %d objects, %d species, %d patches" % [n_inst, species.size(), cells.size()])

# impostor cards for every tree, merged into 480 m blocks (port of the web game's cards: same atlas, cells and proportions)
static func _r(kind: String) -> Array:          # draw distances of a kind at the current graphics level
	var k = Gfx.dist(); return [KIND[kind][0] * k, KIND[kind][1] * k]
var card_mat: ShaderMaterial
func refresh():          # graphics level changed: rebuild the patches with the new distances
	if card_mat: card_mat.set_shader_parameter("near_d", _r("tree")[1] - 10.0)
	for key in cells:
		for kind in cells[key].built:
			for n in cells[key].built[kind]: n.queue_free()
		cells[key].built.clear()
	prime()

const ASP = [0.66, 0.66, 1.3, 0.5, 1.0, 0.9]
func _cards(info: Dictionary):
	var mat = ShaderMaterial.new(); mat.shader = load("res://shaders/tree_card.gdshader"); mat.set_shader_parameter("atlas", load(DIR + "tree_cards.png"))
	mat.set_shader_parameter("near_d", _r("tree")[1] - 10.0); card_mat = mat
	var blocks := {}
	for sp in species:
		var cl = int(info.get(sp, {}).get("card", -1))
		if cl < 0 or species[sp].kind != "tree": continue
		var hgt = float(info[sp].get("height", 10.0)); var top = 7 if cl in [2, 4, 5] else 6
		var kt = 0.62 if cl == 2 else (0.9 if cl == 5 else (0.66 if cl == 4 else 0.3))
		var s = species[sp]
		for k in s.n:
			var i = s.off + k * 8
			var x = data[i]; var y = data[i + 1] - 0.22; var z = data[i + 2]; var h = data[i + 3] * hgt; var w = h * ASP[cl]; var ya = data[i + 4]
			var col = Color(data[i + 5], data[i + 6], data[i + 7])
			var bk = Vector2i(floori(x / 480.0), floori(z / 480.0))
			if not blocks.has(bk): blocks[bk] = [PackedVector3Array(), PackedVector2Array(), PackedVector3Array(), PackedColorArray(), PackedInt32Array(), PackedVector2Array()]
			var B = blocks[bk]
			for d in 2:
				var dx = cos(ya + d * PI / 2) * w / 2; var dz = sin(ya + d * PI / 2) * w / 2; var r = _cuv(cl); var n0 = B[0].size()
				B[0].append_array([Vector3(x - dx, y, z - dz), Vector3(x + dx, y, z + dz), Vector3(x + dx, y + h, z + dz), Vector3(x - dx, y + h, z - dz)])
				B[1].append_array([Vector2(r.x, r.w), Vector2(r.y, r.w), Vector2(r.y, r.z), Vector2(r.x, r.z)])
				B[2].append_array([Vector3(-dx, w * 1.6, -dz).normalized(), Vector3(dx, w * 1.6, dz).normalized(), Vector3(dx * 0.6, w * 1.9, dz * 0.6).normalized(), Vector3(-dx * 0.6, w * 1.9, -dz * 0.6).normalized()])
				for q in 4: B[3].append(col); B[5].append(Vector2(x, z))
				B[4].append_array([n0, n0 + 2, n0 + 1, n0, n0 + 3, n0 + 2])
			var t = w * 0.48; var yt = y + h * kt; var r2 = _cuv(top); var n1 = B[0].size()
			B[0].append_array([Vector3(x - t, yt, z + t), Vector3(x + t, yt, z + t), Vector3(x + t, yt, z - t), Vector3(x - t, yt, z - t)])
			B[1].append_array([Vector2(r2.x, r2.w), Vector2(r2.y, r2.w), Vector2(r2.y, r2.z), Vector2(r2.x, r2.z)])
			for q in 4: B[2].append(Vector3.UP); B[3].append(col); B[5].append(Vector2(x, z))
			B[4].append_array([n1, n1 + 2, n1 + 1, n1, n1 + 3, n1 + 2])
	for bk in blocks:
		var B = blocks[bk]; var arr = []; arr.resize(Mesh.ARRAY_MAX)
		arr[Mesh.ARRAY_VERTEX] = B[0]; arr[Mesh.ARRAY_TEX_UV] = B[1]; arr[Mesh.ARRAY_NORMAL] = B[2]; arr[Mesh.ARRAY_COLOR] = B[3]; arr[Mesh.ARRAY_INDEX] = B[4]; arr[Mesh.ARRAY_TEX_UV2] = B[5]
		var am = ArrayMesh.new(); am.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr); am.surface_set_material(0, mat)
		var mi = MeshInstance3D.new(); mi.mesh = am; mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF; mi.visibility_range_end = 2600.0; add_child(mi)

static func _cuv(q: int) -> Vector4:          # atlas cell (4 x 2): u0, u1, v top, v bottom
	var e = 0.006; var r = q / 4
	return Vector4(float(q % 4) / 4.0 + e, float(q % 4 + 1) / 4.0 - e, float(r) / 2.0 + e, float(r + 1) / 2.0 - e)

func prime():
	for key in cells: _update_cell(cells[key], 999)

func _process(dt):
	var _p0 = Time.get_ticks_usec(); _process_body(dt); Prof.add("flora", Time.get_ticks_usec() - _p0)
func _process_body(dt):
	_t -= dt
	if _t > 0: return
	_t = 0.2
	var budget = 3
	for key in cells:
		budget = _update_cell(cells[key], budget)
		if budget <= 0: break

# every plant and prop takes its own tint from the instance data (multiplied in through the vertex colour)
static var _tint := {}
static func _tinted(m: Material) -> Material:
	if not (m is BaseMaterial3D): return m
	if _tint.has(m): return _tint[m]
	var d := (m as BaseMaterial3D).duplicate() as BaseMaterial3D
	if not d.vertex_color_use_as_albedo: d.vertex_color_use_as_albedo = true; d.vertex_color_is_srgb = false
	_tint[m] = d; return d

# build or drop the kinds of one patch for the current focus; returns what is left of this frame's building budget
func _update_cell(c: Dictionary, budget: int) -> int:
	var d = Vector2(focus.x, focus.z).distance_to(c.c)
	for kind in KIND:
		var r = _r(kind); var reach = maxf(r[0], r[1])
		var want = d < reach + 180.0; var keep = d < reach + 380.0
		if c.built.has(kind):
			if not keep:
				for n in c.built[kind]: n.queue_free()
				c.built.erase(kind)
		elif want and budget > 0:
			c.built[kind] = _make(c, kind); budget -= 1
	return budget

func _make(c: Dictionary, kind: String) -> Array:
	var nodes := []
	var r = _r(kind)
	for sp in c.sp:
		var s = species[sp]
		if s.kind != kind: continue
		var ks: PackedInt32Array = c.sp[sp]
		var xs := []; var cs := []
		for k in ks:
			var i = s.off + k * 8
			cs.append(Color(data[i + 5], data[i + 6], data[i + 7]) if s.tint else Color(1, 1, 1))
			if hidden.has("%s:%d" % [sp, k]): xs.append(Transform3D(Basis().scaled(Vector3.ZERO), Vector3.ZERO)); continue
			xs.append(Transform3D(Basis(Vector3.UP, data[i + 4]).scaled(Vector3.ONE * data[i + 3]), Vector3(data[i], data[i + 1], data[i + 2])))
		for lod in [0, 1]:
			if lod == 1 and r[1] == 0.0: continue
			var parts = lib[s.model].get(lod, lib[s.model].get(1 - lod))
			for p in parts:
				var mm := MultiMesh.new(); mm.transform_format = MultiMesh.TRANSFORM_3D; mm.use_colors = true; mm.mesh = p[0]; mm.instance_count = xs.size()
				for k in xs.size(): mm.set_instance_transform(k, xs[k] * p[1]); mm.set_instance_color(k, cs[k])
				var mmi := MultiMeshInstance3D.new(); mmi.multimesh = mm; mmi.set_meta("sp", sp); mmi.set_meta("part", p[1])
				if lod == 0: mmi.visibility_range_end = r[0]; mmi.visibility_range_end_margin = 8.0
				else: mmi.visibility_range_begin = r[0]; mmi.visibility_range_begin_margin = 8.0; mmi.visibility_range_end = r[1]
				mmi.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_DISABLED
				mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF      # baked into the light map
				add_child(mmi); nodes.append(mmi)
	return nodes

# a sign, bin or post the car knocked over disappears from its patch
func hide_instance(sp: String, k: int):
	if not species.has(sp): return
	hidden["%s:%d" % [sp, k]] = true
	var s = species[sp]; var i = s.off + k * 8
	var key = Vector2i(floori(data[i] / CELL), floori(data[i + 2] / CELL))
	if not cells.has(key): return
	var c = cells[key]; var ks: PackedInt32Array = c.sp.get(sp, PackedInt32Array()); var j = ks.find(k)
	if j < 0 or not c.built.has(s.kind): return
	for n in c.built[s.kind]:
		if n.get_meta("sp") == sp: n.multimesh.set_instance_transform(j, Transform3D(Basis().scaled(Vector3.ZERO), Vector3.ZERO))

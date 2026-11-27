class_name Look
# material pass over imported map pieces: the map keeps its colour in vertex colours, so every material uses them
const TSCALE = {"Terrain": 0.2222, "TerrainField": 0.2, "TerrainForest": 0.25, "TerrainRock": 0.0909, "TerrainSand": 0.1815, "TerrainSnow": 0.1428, "TerrainPave": 0.25}
static var _cache := {}
# concept 16 stone and render: the photo is light, these colours give each its tone (glTF keeps only the picture)
const C16COL = { "C16Stone": Color(0.78, 0.66, 0.5), "C16StoneDark": Color(0.5, 0.42, 0.33), "C16Render": Color(0.8, 0.76, 0.68), "C16Panel": Color(0.46, 0.41, 0.36) }
# second look pass (Nov 2026): buildings and kit through shaders/kit.gdshader; LOOK=1 env switches it off for A/B pictures
static var LOOK2 := OS.get_environment("LOOK") != "1"
# third look pass (27 Nov 2026): road wear, shadow tint, depth; LOOK=2 (or 1) switches it off for A/B pictures
static var LOOK3 := not (OS.get_environment("LOOK") in ["1", "2"])
const KIT = ["KitAshlar", "KitCorr", "KitFabric", "KitGalv", "KitIron", "KitPaint", "KitPlanks", "KitPlastic", "KitPwood", "KitRoof", "KitStone", "KitWood",
	"KitTrim", "KitLimestone", "KitSetts", "WallPlaster", "RoofTiles", "PaintedSurface", "Kerb", "C16Stone", "C16StoneDark", "C16Render", "C16Panel"]
static var _sh := {}

static var bake_tex: Texture2D
static var props := false          # set while the flora / props library is converted
const DECALS = ["Markings", "RoadDecals", "RoadDecalsStreet", "Skids", "Puddles", "ContactAO", "ShoreFoam"]
static var _dsh := {}
static func _decal_shader(blend: bool) -> Shader:
	if not _dsh.has(blend):
		var sh = Shader.new(); var code: String = shader("decal").code
		if blend: code = code.replace("render_mode skip_vertex_transform, cull_disabled;", "render_mode skip_vertex_transform, cull_disabled, blend_mix, depth_draw_never;").replace("//ALPHA", "ALPHA = c.a;")
		sh.code = code; _dsh[blend] = sh
	return _dsh[blend]
static func shader(name: String) -> Shader:
	if not _sh.has(name): _sh[name] = load("res://shaders/%s.gdshader" % name)
	return _sh[name]

static func conv(m: Material, has_col: bool) -> Material:
	if m == null: return m
	var key = str(m.get_instance_id()) + str(has_col) + str(props)
	if _cache.has(key): return _cache[key]
	var out: Material = m
	var nm: String = m.resource_name
	var base = nm.trim_prefix("TerrainBlend_")
	if m is BaseMaterial3D:
		var sm := m as BaseMaterial3D
		if TSCALE.has(base):
			var t := ShaderMaterial.new(); t.shader = shader("terrain")
			t.set_shader_parameter("detail", sm.albedo_texture); t.set_shader_parameter("detail_n", sm.normal_texture)
			t.set_shader_parameter("tscale", TSCALE[base]); t.set_shader_parameter("grassy", 1.0 if base in ["Terrain", "TerrainField", "TerrainForest"] else 0.0)
			t.set_shader_parameter("rough", sm.roughness); t.set_shader_parameter("bake", _bake()); t.set_shader_parameter("bake_rect", BAKE_RECT)
			if nm.begins_with("TerrainBlend_"):
				t.set_shader_parameter("blend_layer", 1.0); t.render_priority = 1
				t.shader = _blend_variant()
			out = t
		elif nm == "Asphalt" or nm == "Shoulder" or nm == "Setts":
			var r := ShaderMaterial.new(); r.shader = shader("road")
			r.set_shader_parameter("bake", _bake()); r.set_shader_parameter("bake_rect", BAKE_RECT); r.set_shader_parameter("tex", sm.albedo_texture); r.set_shader_parameter("tex_n", sm.normal_texture); r.set_shader_parameter("asphalt", 1.0 if nm == "Asphalt" else 0.0); r.set_shader_parameter("setts", 1.0 if nm == "Setts" else 0.0)
			out = r
		elif nm in DECALS:
			var dm := ShaderMaterial.new(); var blend = sm.transparency != BaseMaterial3D.TRANSPARENCY_DISABLED
			dm.shader = _decal_shader(blend); dm.set_shader_parameter("tex", sm.albedo_texture); dm.set_shader_parameter("has_tex", 1.0 if sm.albedo_texture else 0.0)
			dm.set_shader_parameter("col", sm.albedo_color); dm.set_shader_parameter("skid", 1.0 if nm == "Skids" else 0.0); dm.set_shader_parameter("rough", sm.roughness); dm.set_shader_parameter("bake", _bake()); dm.set_shader_parameter("bake_rect", BAKE_RECT)
			if blend: dm.render_priority = 2
			out = dm
		elif props and nm in ["WindowGlass", "KitWindow"]:          # parked cars, boats, kiosks: plain dark glass, no rooms behind it
			var gl := StandardMaterial3D.new(); gl.albedo_color = Color(0.04, 0.05, 0.06); gl.roughness = 0.08; gl.metallic_specular = 0.7; out = gl
		elif nm in ["WindowGlass", "KitWindow", "HeroCurtain"]:
			var im := ShaderMaterial.new(); im.shader = shader("interior"); out = im
		elif nm == "FacadeWindows" or nm == "FacadeGlass":          # facades: windows light up at night
			var f := ShaderMaterial.new(); f.shader = shader("facade"); f.set_shader_parameter("tex", sm.albedo_texture)
			f.set_shader_parameter("orm", sm.roughness_texture); f.set_shader_parameter("has_orm", 1.0 if sm.roughness_texture else 0.0)
			f.set_shader_parameter("tex_n", sm.normal_texture); f.set_shader_parameter("has_n", 1.0 if sm.normal_texture else 0.0)
			f.set_shader_parameter("glass", 1.0 if nm == "FacadeGlass" else 0.0); f.set_shader_parameter("use_col", 1.0 if has_col else 0.0)
			out = f
		elif LOOK2 and (nm in KIT or nm.begins_with("KitBrick") or nm.begins_with("KitConcrete") or nm.begins_with("KitPlaster")) and sm.transparency == BaseMaterial3D.TRANSPARENCY_DISABLED and sm.albedo_texture:
			var k := ShaderMaterial.new(); k.shader = shader("kit")          # buildings and street kit: detail, weathering, occlusion
			k.set_shader_parameter("tex", sm.albedo_texture); k.set_shader_parameter("tex_n", sm.normal_texture); k.set_shader_parameter("has_n", 1.0 if sm.normal_texture else 0.0)
			k.set_shader_parameter("tex_orm", sm.roughness_texture); k.set_shader_parameter("has_orm", 1.0 if sm.roughness_texture else 0.0)
			k.set_shader_parameter("col", C16COL.get(nm, sm.albedo_color)); k.set_shader_parameter("use_col", 1.0 if (has_col or props) else 0.0)
			k.set_shader_parameter("rough", sm.roughness); k.set_shader_parameter("metal", sm.metallic if sm.roughness_texture else 0.0)
			k.set_shader_parameter("uv_scale", sm.uv1_scale); k.set_shader_parameter("uv_offset", sm.uv1_offset)
			k.set_shader_parameter("detail_k", 0.0 if nm in ["KitPlastic", "KitPaint"] else (0.5 if nm in ["KitGalv", "KitIron", "KitFabric"] else 1.0))
			k.set_shader_parameter("bake", _bake()); k.set_shader_parameter("bake_rect", BAKE_RECT)
			out = k
		elif LOOK2 and props and nm.begins_with("Leaves") and sm.albedo_texture:          # concept 15/04 trees: leaf cards with shade, sun-through and sway
			var lt = sm.albedo_texture
			if nm == "LeavesHQ" and ResourceLoader.exists("res://assets/island/tex/tex_leaf_atlas_hq.png"): lt = load("res://assets/island/tex/tex_leaf_atlas_hq.png")          # one atlas for both tree files (its import keeps the needles at a distance)
			var lv := ShaderMaterial.new(); lv.shader = shader("leaves"); lv.set_shader_parameter("tex", lt)
			lv.set_shader_parameter("lift", 1.55 if nm == "LeavesHQ" else 1.3); lv.set_shader_parameter("hq_atlas", 1.0 if nm == "LeavesHQ" else 0.0)
			out = lv
		elif LOOK2 and props and nm.begins_with("T_tree") and sm.albedo_texture:          # Tripo trees: shade, colour, sway (shaders/tree.gdshader)
			var tr := ShaderMaterial.new(); tr.shader = shader("tree")
			tr.set_shader_parameter("tex", sm.albedo_texture); tr.set_shader_parameter("tex_n", sm.normal_texture); tr.set_shader_parameter("has_n", 1.0 if sm.normal_texture else 0.0)
			tr.set_shader_parameter("height", {"T_tree_t_cypress": 11.0, "T_tree_t_pine": 12.0}.get(nm, 8.0))
			out = tr
		elif nm == "C16Glass":          # concept 16 curtain walls: dark mirror glass, lit offices at night
			var g16 := ShaderMaterial.new(); g16.shader = shader("glass16"); out = g16
		elif nm == "Water":
			var w := ShaderMaterial.new(); w.shader = shader("water"); w.render_priority = 2; out = w
		elif nm == "Seabed":
			var b := sm.duplicate(); b.albedo_color = Color(0.05, 0.22, 0.26); out = b
		else:
			var d := sm.duplicate() as BaseMaterial3D
			if has_col: d.vertex_color_use_as_albedo = true; d.vertex_color_is_srgb = false      # glTF vertex colours are linear
			if nm in ["ContactAO", "RoadDecals", "Skids", "Puddles", "ShoreFoam", "Shallows", "Markings"]:
				d.render_priority = 2
			if Tod.EMIT.has(nm): Tod.emissive(d, nm)
			if nm == "TreeCards": d = null
			elif nm.begins_with("Leaves") or d.transparency == BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR or nm.begins_with("T_tree"):
				d.cull_mode = BaseMaterial3D.CULL_DISABLED
				if nm.begins_with("Leaves"):
					d.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR; d.alpha_scissor_threshold = 0.4
					d.albedo_color = Color(1.0, 1.0, 0.94)
					d.backlight_enabled = true; d.backlight = Color(0.22, 0.3, 0.12); d.roughness = 1.0; d.metallic_specular = 0.0; d.metallic = 0.0
					d.emission_enabled = true; d.emission = Color(0.035, 0.05, 0.025)
			out = d
	_cache[key] = out
	return out

const BAKE = "res://assets/island/bake_island.png"
const BAKE_RECT = Vector4(-2400.0, -1680.0, 4800.0, 3360.0)          # x0, z0, width, depth of the island light map
static func _bake() -> Texture2D:
	if bake_tex == null: bake_tex = load(BAKE)
	return bake_tex

static var _bv: Shader
static func _blend_variant() -> Shader:
	if _bv == null:
		_bv = Shader.new(); _bv.code = shader("terrain").code.replace("shader_type spatial;", "shader_type spatial;\nrender_mode blend_mix, depth_draw_never;").replace("//BLEND_ALPHA", "ALPHA = clamp(UV2.x, 0.0, 1.0);")
	return _bv

static func apply(root: Node):
	for n in root.find_children("*", "MeshInstance3D", true, false):
		var mi := n as MeshInstance3D; var mesh := mi.mesh
		if mesh == null: continue
		for i in mesh.get_surface_count():
			var fmt = mesh.surface_get_format(i)
			var m = conv(mesh.surface_get_material(i), (fmt & Mesh.ARRAY_FORMAT_COLOR) != 0)
			if m == null: mi.visible = false
			else: mi.set_surface_override_material(i, m)
		if mi.name.begins_with("TreeCards") or mi.name == "Water": mi.visible = false
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		if false and (mi.name.begins_with("Terrain") or mi.name.begins_with("Road") or mi.name.begins_with("Verge") or mi.name.begins_with("Markings") or mi.name.begins_with("Water") or mi.name.begins_with("Shallows") or mi.name.begins_with("Seabed")): pass

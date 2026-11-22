class_name Look
# material pass over imported map pieces: the map keeps its colour in vertex colours, so every material uses them
const TSCALE = {"Terrain": 0.2222, "TerrainField": 0.2, "TerrainForest": 0.25, "TerrainRock": 0.0909, "TerrainSand": 0.1815, "TerrainSnow": 0.1428, "TerrainPave": 0.25}
static var _cache := {}
static var _sh := {}

static func shader(name: String) -> Shader:
	if not _sh.has(name): _sh[name] = load("res://shaders/%s.gdshader" % name)
	return _sh[name]

static func conv(m: Material, has_col: bool) -> Material:
	if m == null: return m
	var key = str(m.get_instance_id()) + str(has_col)
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
			t.set_shader_parameter("rough", sm.roughness)
			if nm.begins_with("TerrainBlend_"):
				t.set_shader_parameter("blend_layer", 1.0); t.render_priority = 1
				t.shader = _blend_variant()
			out = t
		elif nm == "Asphalt" or nm == "Shoulder" or nm == "Setts":
			var r := ShaderMaterial.new(); r.shader = shader("road")
			r.set_shader_parameter("tex", sm.albedo_texture); r.set_shader_parameter("tex_n", sm.normal_texture); r.set_shader_parameter("asphalt", 1.0 if nm == "Asphalt" else 0.0)
			out = r
		elif nm == "Water":
			var w := ShaderMaterial.new(); w.shader = shader("water"); w.render_priority = 2; out = w
		elif nm == "Seabed":
			var b := sm.duplicate(); b.albedo_color = Color(0.05, 0.22, 0.26); out = b
		else:
			var d := sm.duplicate() as BaseMaterial3D
			if has_col: d.vertex_color_use_as_albedo = true; d.vertex_color_is_srgb = true
			if nm in ["ContactAO", "RoadDecals", "Skids", "Puddles", "ShoreFoam", "Shallows", "Markings"]:
				d.render_priority = 2
			if nm == "TreeCards": d = null
			out = d
	_cache[key] = out
	return out

static var _bv: Shader
static func _blend_variant() -> Shader:
	if _bv == null:
		_bv = Shader.new(); _bv.code = shader("terrain").code.replace("shader_type spatial;", "shader_type spatial;\nrender_mode blend_mix, depth_draw_never;")
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
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF if (mi.name.begins_with("Terrain") or mi.name.begins_with("Road") or mi.name.begins_with("Verge") or mi.name.begins_with("Markings") or mi.name.begins_with("Water") or mi.name.begins_with("Shallows") or mi.name.begins_with("Seabed")) else GeometryInstance3D.SHADOW_CASTING_SETTING_ON

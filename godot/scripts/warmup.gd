extends Node3D
class_name Warmup
# Shader warm-up: draws every material the game can show once, behind the loading cover, so the GPU driver compiles
# all the shaders before driving instead of stuttering the first time something new comes into view.
#  - the map: assets/island/warm.scn (one quad per distinct map material, scripts/_make_warm.gd), through Look like the map
#  - everything already in the game: cars, traffic, flora (as MultiMeshes, like the patches), grass, lamps, rain, sky...
#  - both car models with the rivals' light versions, so the first race starts clean
# Each material is drawn with its own render layer (map sun or car sun), once with and once without the headlights' spot
# light, and into the shadow map if its owner casts shadows. Done materials are remembered; later calls (race start,
# graphics change) only draw what is new.
var main
var done := {}          # material instance id -> true
var _warm_scene: Node3D
var busy := false

func _init(m): main = m; name = "Warmup"; physics_interpolation_mode = Node.PHYSICS_INTERPOLATION_MODE_OFF

# what to draw: [material, layers, instanced, casts shadow, multimesh flags]
func _collect() -> Array:
	var out := []; var seen := {}
	var add = func(mat: Material, layers: int, inst: bool, shadow: bool, mm: MultiMesh):
		if mat == null: return
		var key = "%s:%d:%s:%s" % [shader_key(mat), layers, inst, shadow]          # one draw per shader, not per material
		if seen.has(key) or done.has(key): return
		seen[key] = true; out.append([mat, layers, inst, shadow, mm, key])
	for g in main.find_children("*", "GeometryInstance3D", true, false):
		if main.menu and main.menu.is_ancestor_of(g): continue
		var gi := g as GeometryInstance3D; var sh = gi.cast_shadow != GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		if gi.material_override: add.call(gi.material_override, gi.layers, gi is MultiMeshInstance3D, sh, gi.multimesh if gi is MultiMeshInstance3D else null); continue
		var mesh: Mesh = null; var mm: MultiMesh = null
		if gi is MeshInstance3D: mesh = gi.mesh
		elif gi is MultiMeshInstance3D and gi.multimesh: mm = gi.multimesh; mesh = mm.mesh
		if mesh == null: continue
		for i in mesh.get_surface_count():
			var m = (gi as MeshInstance3D).get_surface_override_material(i) if gi is MeshInstance3D else null
			if m == null: m = mesh.surface_get_material(i)
			add.call(m, gi.layers, mm != null, sh, mm)
	if main.flora:          # every plant and prop as the patches draw them (instanced, tinted), not only those near the start
		for model in main.flora.lib:
			for lod in main.flora.lib[model]:
				for p in main.flora.lib[model][lod]:
					for i in p[0].get_surface_count(): add.call(p[0].surface_get_material(i), 1, true, false, null)
	return out

# the rivals' cars as a race sets them up (light versions, paint copies), made once and taken apart again
func _cars():
	for id in Car.CARS:
		var c := Car.new(); c.car_id = id; c.opts = { far = true, paint = Color(0.3, 0.3, 0.32) }; c.process_mode = Node.PROCESS_MODE_DISABLED
		c.visible = false; add_child(c)

func run(cover := true) -> void:
	if busy or DisplayServer.get_name() == "headless": return          # nothing is drawn without a screen
	busy = true
	var t0 = Time.get_ticks_msec()
	if _warm_scene == null and ResourceLoader.exists("res://assets/island/warm.scn"):
		_warm_scene = load("res://assets/island/warm.scn").instantiate(); _warm_scene.visible = false; add_child(_warm_scene)
		Look.apply(_warm_scene)
		_cars()
	var items = _collect()
	if items.is_empty(): busy = false; return
	var veil: CanvasLayer = null
	if cover: veil = _veil()
	var studio = main.get("showroom") != null and main.showroom.active
	if studio: main.showroom.leave(false)          # warm up in the island's light, not the studio's
	await get_tree().process_frame          # the camera has its place for this frame
	# a grid of small quads just in front of the camera (inside the shadow range), kept there while it draws
	var holder := Node3D.new(); add_child(holder)
	var quad := QuadMesh.new(); quad.size = Vector2(0.08, 0.08)
	var n = items.size(); var cols = int(ceil(sqrt(n)))
	for k in n:
		var it = items[k]
		var gi: GeometryInstance3D
		if it[2]:
			var mm := MultiMesh.new(); mm.transform_format = MultiMesh.TRANSFORM_3D
			mm.use_colors = it[4].use_colors if it[4] else true; mm.use_custom_data = it[4].use_custom_data if it[4] else false
			mm.mesh = quad; mm.instance_count = 1; mm.set_instance_transform(0, Transform3D.IDENTITY)
			var mmi := MultiMeshInstance3D.new(); mmi.multimesh = mm; gi = mmi
		else:
			var mi := MeshInstance3D.new(); mi.mesh = quad; gi = mi
		gi.material_override = it[0]; gi.layers = it[1]; gi.extra_cull_margin = 16384.0
		gi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if it[3] else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		holder.add_child(gi); gi.position = Vector3(((k % cols) - cols * 0.5) * 0.09, ((k / cols) - cols * 0.5) * 0.09, -4.0)
	# the headlights' spot light on the grid (night variants) for two frames, then two frames without it (day)
	var spot := SpotLight3D.new(); spot.spot_range = 30.0; spot.spot_angle = 60.0; spot.shadow_enabled = false; holder.add_child(spot)
	for f in 4:
		var cam: Camera3D = main.get_viewport().get_camera_3d()
		if cam: holder.global_transform = cam.global_transform
		spot.visible = f < 2
		await RenderingServer.frame_post_draw
	holder.queue_free()
	if studio: main.showroom.enter()
	for it in items: done[it[5]] = true
	if veil: veil.queue_free()
	print("WARMUP %d materials in %d ms, shader cache %d" % [n, Time.get_ticks_msec() - t0, cache_count()])
	busy = false

func reset(): done.clear()          # graphics level changed: shadow settings change the shaders

func _veil() -> CanvasLayer:
	var cl := CanvasLayer.new(); cl.layer = 100
	var r := ColorRect.new(); r.color = Color(0.03, 0.04, 0.06); r.set_anchors_preset(Control.PRESET_FULL_RECT); cl.add_child(r)
	var l := Label.new(); l.text = "Getting the island ready…"; l.add_theme_font_size_override("font_size", 28); l.modulate = Color(1, 1, 1, 0.8)
	l.set_anchors_preset(Control.PRESET_CENTER); l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER; l.position -= Vector2(200, 20); l.size = Vector2(400, 40); r.add_child(l)
	add_child(cl); return cl

static func cache_count() -> int:          # test: compiled scene shaders on disk (GL shader cache)
	var n = 0; var d = "user://shader_cache/SceneShaderGLES3"
	for sub in DirAccess.get_directories_at(d): n += DirAccess.get_files_at(d + "/" + sub).size()
	return n

# materials that end up with the same shader: same ShaderMaterial shader, or a BaseMaterial3D with the same settings
static func shader_key(m: Material) -> String:
	if m is ShaderMaterial: return "S%d" % ((m as ShaderMaterial).shader.get_instance_id() if (m as ShaderMaterial).shader else 0)
	if not (m is BaseMaterial3D): return "M%d" % m.get_instance_id()
	var b := m as BaseMaterial3D
	var s = [b.get_class(), b.transparency, b.cull_mode, b.shading_mode, b.diffuse_mode, b.specular_mode, b.vertex_color_use_as_albedo, b.vertex_color_is_srgb, b.emission_enabled,
		b.normal_enabled, b.albedo_texture != null, b.normal_texture != null, b.roughness_texture != null, b.metallic_texture != null, b.emission_texture != null,
		b.ao_enabled, b.texture_filter, b.texture_repeat, b.alpha_scissor_threshold, b.billboard_mode, b.no_depth_test, b.depth_draw_mode, b.blend_mode,
		b.backlight_enabled, b.rim_enabled, b.clearcoat_enabled, b.anisotropy_enabled, b.heightmap_enabled, b.subsurf_scatter_enabled, b.refraction_enabled,
		b.detail_enabled, b.uv1_triplanar, b.uv2_triplanar, b.disable_receive_shadows, b.disable_ambient_light, b.disable_fog, b.fixed_size, b.use_point_size,
		b.proximity_fade_enabled, b.distance_fade_mode, b.grow, b.metallic_texture_channel, b.roughness_texture_channel, b.orm_texture != null if b is ORMMaterial3D else false,
		b.texture_channel_albedo if "texture_channel_albedo" in b else 0, b.albedo_texture_force_srgb, b.vertex_color_is_srgb, b.alpha_antialiasing_mode, b.render_priority]
	return str(s).sha1_text().substr(0, 16)

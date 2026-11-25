extends SceneTree
# tool: one tiny mesh for every distinct material in the island's map chunks (base, detail, landmarks, shops), saved as
# assets/island/warm.scn. The game draws these once while it loads (scripts/warmup.gd), so every shader the streamed map
# will need is compiled before driving instead of the first time a new street comes into view.
# Textures are swapped for one 4x4 placeholder: only the material's settings decide which shader it needs.
# run: godot --headless -s res://scripts/_make_warm.gd   (after the chunks change)
func _init():
	var idx = JSON.parse_string(FileAccess.get_file_as_string("res://assets/island/index.json"))
	var ph := ImageTexture.create_from_image(Image.create(4, 4, true, Image.FORMAT_RGBA8))
	var root := Node3D.new(); root.name = "Warm"
	var seen := {}; var n_src = 0
	var names: Array = idx["chunks"].keys()
	for f in DirAccess.get_files_at("res://assets/island/chunks"):          # shop chunks (s_*) are not in the index
		if f.ends_with(".glb") and not names.has(f.get_basename()): names.append(f.get_basename())
	for nm in names:
		var sc = load("res://assets/island/chunks/%s.glb" % nm)
		if sc == null: continue
		var r = sc.instantiate(); n_src += 1
		for mi in r.find_children("*", "MeshInstance3D", true, false):
			var mesh: Mesh = mi.mesh
			if mesh == null: continue
			for i in mesh.get_surface_count():
				var m = mesh.surface_get_material(i)
				if m == null: continue
				var fmt = mesh.surface_get_format(i)
				var has_col = (fmt & Mesh.ARRAY_FORMAT_COLOR) != 0
				var key = _key(m) + "|" + str(has_col)
				if seen.has(key): continue
				seen[key] = true
				var d: Material = m.duplicate()
				if d is BaseMaterial3D:
					for p in ["albedo_texture", "normal_texture", "roughness_texture", "metallic_texture", "emission_texture", "ao_texture", "orm_texture", "detail_albedo", "detail_normal", "detail_mask"]:
						if p in d and d.get(p) != null: d.set(p, ph)
				var q := MeshInstance3D.new(); q.name = "W%d" % seen.size(); q.mesh = _quad(has_col, (fmt & Mesh.ARRAY_FORMAT_TEX_UV2) != 0, d)
				root.add_child(q); q.owner = root
		r.free()
	var ps = PackedScene.new(); ps.pack(root)
	var err = ResourceSaver.save(ps, "res://assets/island/warm.scn", ResourceSaver.FLAG_COMPRESS)
	print("warm: %d chunks, %d distinct materials (save %d)" % [n_src, seen.size(), err])
	root.free(); quit()

# what decides the shader of a material: its name (the game converts by name) and every setting that changes the code
static func _key(m: Material) -> String:
	if not (m is BaseMaterial3D): return m.get_class() + ":" + m.resource_name
	var b := m as BaseMaterial3D; var s = [m.resource_name, b.transparency, b.cull_mode, b.shading_mode, b.vertex_color_use_as_albedo, b.emission_enabled,
		b.normal_enabled, b.albedo_texture != null, b.normal_texture != null, b.roughness_texture != null, b.metallic_texture != null, b.emission_texture != null,
		b.ao_enabled, b.texture_filter, b.texture_repeat, b.alpha_scissor_threshold > 0.0, b.billboard_mode, b.no_depth_test, b.depth_draw_mode, b.blend_mode]
	return str(s)

static func _quad(col: bool, uv2: bool, m: Material) -> ArrayMesh:
	var a = []; a.resize(Mesh.ARRAY_MAX)
	a[Mesh.ARRAY_VERTEX] = PackedVector3Array([Vector3(-0.5, 0, 0), Vector3(0.5, 0, 0), Vector3(0.5, 1, 0), Vector3(-0.5, 1, 0)])
	a[Mesh.ARRAY_NORMAL] = PackedVector3Array([Vector3.BACK, Vector3.BACK, Vector3.BACK, Vector3.BACK])
	a[Mesh.ARRAY_TANGENT] = PackedFloat32Array([1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1])
	a[Mesh.ARRAY_TEX_UV] = PackedVector2Array([Vector2(0, 1), Vector2(1, 1), Vector2(1, 0), Vector2(0, 0)])
	if uv2: a[Mesh.ARRAY_TEX_UV2] = PackedVector2Array([Vector2(0, 1), Vector2(1, 1), Vector2(1, 0), Vector2(0, 0)])
	if col: a[Mesh.ARRAY_COLOR] = PackedColorArray([Color.WHITE, Color.WHITE, Color.WHITE, Color.WHITE])
	a[Mesh.ARRAY_INDEX] = PackedInt32Array([0, 1, 2, 0, 2, 3])
	var am = ArrayMesh.new(); am.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, a); am.surface_set_material(0, m)
	return am

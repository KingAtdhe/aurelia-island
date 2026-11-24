extends SceneTree
# tool: prebuilds the drive colliders of every streamed (d_*) map chunk into assets/island/coll/<chunk>.scn, so the shapes
# are made on the loading thread and putting a chunk in costs the main thread almost nothing.
# run: godot --headless -s res://scripts/_bake_coll.gd
func _init():
	DirAccess.make_dir_recursive_absolute("res://assets/island/coll")
	var idx = JSON.parse_string(FileAccess.get_file_as_string("res://assets/island/index.json"))
	var n_all = 0
	for nm in idx["chunks"]:
		if idx["chunks"][nm]["kind"] != "d": continue
		var sc = load("res://assets/island/chunks/%s.glb" % nm); var root = sc.instantiate()
		var out = Node3D.new(); out.name = "Coll"
		for mi in root.find_children("*", "MeshInstance3D", true, false):
			var surf = Island.surf_of(String(mi.name))
			if surf == "": continue
			var sb = StaticBody3D.new(); sb.name = String(mi.name); sb.set_meta("surf", surf); sb.transform = _xf(mi, root)
			var cs = CollisionShape3D.new(); cs.shape = mi.mesh.create_trimesh_shape(); sb.add_child(cs); out.add_child(sb)
			cs.owner = out; sb.owner = out; n_all += 1
		var ps = PackedScene.new(); ps.pack(out)
		ResourceSaver.save(ps, "res://assets/island/coll/%s.scn" % nm, ResourceSaver.FLAG_COMPRESS)
		root.free(); out.free()
	print("colliders baked: %d bodies" % n_all)
	quit()

func _xf(n: Node3D, root: Node) -> Transform3D:
	var t = n.transform; var p = n.get_parent()
	while p != null and p != root: t = p.transform * t; p = p.get_parent()
	return t

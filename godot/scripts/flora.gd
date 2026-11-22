extends Node3D
class_name Flora
# trees, plants, rocks, houses and street furniture of the coast, drawn as MultiMeshes per 250 m patch,
# a near and a far version that swap by distance (instance data exported from the web game: x y z scale yaw r g b)
const TT = { pine = "tree_t_pine", oak = "tree_t_oak", oak_b = "tree_t_oak", plane = "tree_t_oak", plane_b = "tree_t_oak", fruit = "tree_t_olive", cypress = "tree_t_cypress" }
const CELL = 250.0

func build():
	var lib_scene = load("res://assets/flora_coast.glb").instantiate()
	add_child(lib_scene); Look.apply(lib_scene); lib_scene.visible = false
	var lib := {}
	for n in lib_scene.find_children("S_*", "Node3D", true, false):
		var m = String(n.name).substr(2); var lod = int(m.substr(m.length() - 1)); var sp = m.substr(0, m.length() - 5)
		var parts := []
		for mi in ([n] if n is MeshInstance3D else []) + n.find_children("*", "MeshInstance3D", true, false):
			var mesh: Mesh = mi.mesh.duplicate()
			for si in mesh.get_surface_count():
				var o = mi.get_surface_override_material(si)
				if o: mesh.surface_set_material(si, o)
			parts.append([mesh, lib_scene.global_transform.affine_inverse() * mi.global_transform])
		if not lib.has(sp): lib[sp] = {}
		lib[sp][lod] = parts
	var data = JSON.parse_string(FileAccess.get_file_as_string("res://assets/coast_flora.json"))
	var n_inst := 0
	for sp in data:
		var src = TT.get(sp, sp)
		if not lib.has(src): continue
		var a = data[sp]; var cells := {}
		for i in range(0, a.size(), 8):
			var key = Vector2i(floor(a[i] / CELL), floor(a[i + 2] / CELL))
			if not cells.has(key): cells[key] = []
			cells[key].append(Transform3D(Basis(Vector3.UP, a[i + 4]).scaled(Vector3.ONE * a[i + 3]), Vector3(a[i], a[i + 1], a[i + 2])))
		var small = sp.begins_with("grass") or sp.begins_with("flowers")
		var big = sp.begins_with("prop_house") or sp.begins_with("prop_barn") or sp.begins_with("rock_t") or sp.begins_with("tree") or TT.has(sp) or sp.begins_with("spruce") or sp.begins_with("palm")
		var r0 = 55.0 if small else (140.0 if big else 90.0); var r1 = 0.0 if small else (900.0 if big else 450.0)
		for key in cells:
			var xs: Array = cells[key]; n_inst += xs.size()
			for lod in [0, 1]:
				if lod == 1 and r1 == 0.0: continue
				var parts = lib[src].get(lod, lib[src].get(1 - lod))
				for p in parts:
					var mm := MultiMesh.new(); mm.transform_format = MultiMesh.TRANSFORM_3D; mm.mesh = p[0]; mm.instance_count = xs.size()
					for k in xs.size(): mm.set_instance_transform(k, xs[k] * p[1])
					var mmi := MultiMeshInstance3D.new(); mmi.multimesh = mm
					if lod == 0: mmi.visibility_range_end = r0; mmi.visibility_range_end_margin = 8.0
					else: mmi.visibility_range_begin = r0; mmi.visibility_range_begin_margin = 8.0; mmi.visibility_range_end = r1
					mmi.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_DISABLED
					mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF      # baked
					add_child(mmi)
	lib_scene.queue_free()
	print("flora: %d objects" % n_inst)

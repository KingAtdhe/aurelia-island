extends Node3D
class_name Tunnels
# The island's three road tunnels (Ring by the coast, Skyline Road and Eagle Descent in the mountains), as in the web game:
# the bore walls get pale tiles and a dark vault, two rows of lamps under the crown with warm pools of light on the road,
# and the driver's eyes adjust when the car goes in (main.gd reads inside()).

var list = []
var bores = 0          # { pts: PackedVector3Array (road centre), ceil: PackedFloat32Array, hw, portals: [Vector3, Vector3] }

func build(world: Dictionary, island: Node):
	var names = []; var hws = {}
	for r in world["roads"]: names.append(r["name"]); hws[r["name"]] = float(r["w"]) * 0.5
	var portals = []
	for t in world["tunnels"]:
		var nm: String = names[int(t[0])]; var src = world["roads"][int(t[0])]["pts"]; var a = int(t[1]); var b = a + int(t[2])
		var pts = PackedVector3Array()
		for i in range(a, b + 1): pts.append(Vector3(src[i * 3], src[i * 3 + 1], src[i * 3 + 2]))
		list.append({ pts = pts, hw = hws[nm], ceil = PackedFloat32Array(), road = nm })
		portals.append(pts[0]); portals.append(pts[pts.size() - 1])
	# split the bore out of the bridge/tunnel meshes and give it its own material
	var mat = ShaderMaterial.new(); mat.shader = load("res://shaders/tunnel.gdshader"); mat.set_shader_parameter("conc", load("res://assets/tun_concrete.jpg"))
	var pv = PackedVector4Array()
	for p in portals: pv.append(Vector4(p.x, p.y + 3.0, p.z, 0))
	mat.set_shader_parameter("portals", pv); mat.set_shader_parameter("n_portals", pv.size())
	for mi in island.find_children("Bridges__*", "MeshInstance3D", true, false):
		var box: AABB = mi.global_transform * mi.get_aabb()
		var hit = false
		for t in list:
			for p in t.pts:
				if box.grow(t.hw + 6.0).has_point(p): hit = true; break
			if hit: break
		if hit: _split(mi, mat)
	await get_tree().physics_frame
	await get_tree().physics_frame
	var space = get_world_3d().direct_space_state
	var lamps = []; var pools = []
	for t in list:
		for k in t.pts.size():
			var p: Vector3 = t.pts[k]
			var h = space.intersect_ray(PhysicsRayQueryParameters3D.create(p + Vector3(0, 1.5, 0), p + Vector3(0, 18.0, 0)))
			t.ceil.append(h.position.y if h else p.y + 8.0)
		for k in range(0, t.pts.size(), 2):
			var p: Vector3 = t.pts[k]; var q: Vector3 = t.pts[mini(k + 1, t.pts.size() - 1)] if k + 1 < t.pts.size() else p * 2.0 - t.pts[k - 1]
			var fw = Vector3(q.x - p.x, 0, q.z - p.z).normalized(); var rt = Vector3(fw.z, 0, -fw.x)
			for sd in [-1.0, 1.0]:
				var lp = Vector3(p.x, p.y, p.z) + rt * sd * t.hw * 0.42
				var h = space.intersect_ray(PhysicsRayQueryParameters3D.create(lp + Vector3(0, 1.5, 0), lp + Vector3(0, 18.0, 0)))
				var y = minf((h.position.y if h else p.y + 7.0) - 0.12, p.y + 7.6)
				lamps.append(Transform3D(Basis(rt, Vector3.UP, fw), Vector3(lp.x, y, lp.z)))
			pools.append(Vector3(p.x, p.y + 0.06, p.z))
	# lamps: small bright boxes under the crown
	var lm = StandardMaterial3D.new(); lm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED; lm.albedo_color = Color(1.0, 0.86, 0.62) * 2.2
	var bm = BoxMesh.new(); bm.size = Vector3(0.26, 0.07, 1.3); bm.material = lm
	var mm = MultiMesh.new(); mm.transform_format = MultiMesh.TRANSFORM_3D; mm.mesh = bm; mm.instance_count = lamps.size()
	for k in lamps.size(): mm.set_instance_transform(k, lamps[k])
	var mmi = MultiMeshInstance3D.new(); mmi.multimesh = mm; mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF; add_child(mmi)
	# warm pools of light on the road under each pair of lamps
	var g = Gradient.new(); g.set_color(0, Color(1.0, 0.84, 0.63, 0.95)); g.set_color(1, Color(1.0, 0.75, 0.47, 0.0)); g.add_point(0.45, Color(1.0, 0.78, 0.55, 0.42))
	var gt = GradientTexture2D.new(); gt.gradient = g; gt.fill = GradientTexture2D.FILL_RADIAL; gt.fill_from = Vector2(0.5, 0.5); gt.fill_to = Vector2(1.0, 0.5); gt.width = 64; gt.height = 64
	var pmat = StandardMaterial3D.new(); pmat.albedo_texture = gt; pmat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED; pmat.blend_mode = BaseMaterial3D.BLEND_MODE_ADD
	pmat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA; pmat.depth_draw_mode = BaseMaterial3D.DEPTH_DRAW_DISABLED; pmat.albedo_color = Color(0.34, 0.3, 0.24); pmat.render_priority = 3
	var pm = PlaneMesh.new(); pm.size = Vector2(11, 11); pm.material = pmat
	var mp = MultiMesh.new(); mp.transform_format = MultiMesh.TRANSFORM_3D; mp.mesh = pm; mp.instance_count = pools.size()
	for k in pools.size(): mp.set_instance_transform(k, Transform3D(Basis(), pools[k]))
	print("tunnels: %d, lamps %d, bore pieces %d, ceilings %s" % [list.size(), lamps.size(), bores, str(list.map(func(t): return snappedf(t.ceil[t.ceil.size() / 2] - t.pts[t.pts.size() / 2].y, 0.1)))])
	var mpi = MultiMeshInstance3D.new(); mpi.multimesh = mp; mpi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF; add_child(mpi)

# triangles of the bore (inside the tunnel, above the road) go to their own mesh with the tunnel material; the rest stays
func _split(mi: MeshInstance3D, mat: Material):
	var src: Mesh = mi.mesh; var xf = mi.global_transform
	var out = ArrayMesh.new(); var bore = ArrayMesh.new()
	for s in src.get_surface_count():
		var arr = src.surface_get_arrays(s); var m = mi.get_surface_override_material(s)
		if m == null: m = src.surface_get_material(s)
		var orig = src.surface_get_material(s)
		var idx: PackedInt32Array = arr[Mesh.ARRAY_INDEX]
		if orig == null or orig.resource_name != "PaintedSurface" or idx.is_empty():
			out.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arr); out.surface_set_material(out.get_surface_count() - 1, m); continue
		var v: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
		var keep = PackedInt32Array(); var take = PackedInt32Array()
		for k in range(0, idx.size(), 3):
			var c = xf * ((v[idx[k]] + v[idx[k + 1]] + v[idx[k + 2]]) / 3.0)
			var inside = false
			for t in list:
				for p in t.pts:
					if abs(c.x - p.x) < t.hw + 4.0 and abs(c.z - p.z) < t.hw + 4.0 and Vector2(c.x - p.x, c.z - p.z).length() < t.hw + 4.0 and c.y > p.y - 0.6 and c.y < p.y + 16.0: inside = true; break
				if inside: break
			if inside: take.append_array([idx[k], idx[k + 1], idx[k + 2]])
			else: keep.append_array([idx[k], idx[k + 1], idx[k + 2]])
		if not keep.is_empty():
			var a2 = arr.duplicate(); a2[Mesh.ARRAY_INDEX] = keep; out.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, a2); out.surface_set_material(out.get_surface_count() - 1, m)
		if not take.is_empty():
			var a3 = arr.duplicate(); a3[Mesh.ARRAY_INDEX] = take; bore.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, a3); bore.surface_set_material(bore.get_surface_count() - 1, mat)
	if bore.get_surface_count() == 0: return
	for s in mi.get_surface_override_material_count(): mi.set_surface_override_material(s, null)
	mi.mesh = out
	bores += 1
	var b = MeshInstance3D.new(); b.mesh = bore; b.name = "TunnelBore"; b.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON; mi.add_child(b)

# 0 outside, rising to 1 some 25 m into a tunnel: how far the driver's eyes have to adjust
func inside(p: Vector3) -> float:
	for t in list:
		var n = t.pts.size()
		for k in n:
			var q: Vector3 = t.pts[k]
			if abs(p.x - q.x) < t.hw + 2.0 and abs(p.z - q.z) < t.hw + 2.0 and abs(p.y - q.y) < 4.0 and Vector2(p.x - q.x, p.z - q.z).length() < t.hw + 1.5:
				return clampf(minf(k, n - 1 - k) * 5.0 / 25.0, 0.0, 1.0)
	return 0.0

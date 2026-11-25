extends Node3D
class_name Lamps
# Street lamps (world.json lamps: lamp heads) at night: a glow at each head and a pool of light on the ground under it, two
# MultiMeshes for the whole island (2 draws). Shown at sunset (dim) and night (Tod).
var mats := []
func build(world: Dictionary):
	var pts = world["lamps"]; var space = get_world_3d().direct_space_state
	var glow := MultiMesh.new(); glow.transform_format = MultiMesh.TRANSFORM_3D; glow.mesh = QuadMesh.new(); glow.instance_count = pts.size()
	var pool := MultiMesh.new(); pool.transform_format = MultiMesh.TRANSFORM_3D
	var pm := PlaneMesh.new(); pm.size = Vector2(1, 1); pool.mesh = pm; pool.instance_count = pts.size()
	for i in pts.size():
		var p = Vector3(pts[i][0], pts[i][1], pts[i][2])
		glow.set_instance_transform(i, Transform3D(Basis().scaled(Vector3(2.6, 2.6, 1)), p))
		var q = PhysicsRayQueryParameters3D.create(p + Vector3(0, -0.5, 0), p + Vector3(0, -30, 0)); var h = space.intersect_ray(q)
		var gy = h.position.y if h else p.y - 5.0
		pool.set_instance_transform(i, Transform3D(Basis().scaled(Vector3(15, 1, 15)), Vector3(p.x, gy + 0.08, p.z)))
	for k in 2:
		var mat := ShaderMaterial.new(); mat.shader = load("res://shaders/lamp.gdshader"); mat.set_shader_parameter("pool", float(k)); mats.append(mat)
		var n := MultiMeshInstance3D.new(); n.multimesh = glow if k == 0 else pool; n.material_override = mat
		n.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF; n.layers = 3; add_child(n)
		n.custom_aabb = AABB(Vector3(-2600, -50, -1800), Vector3(5200, 400, 3600))
	set_on(0.0)
func set_on(k: float):
	visible = k > 0.01
	for m in mats: m.set_shader_parameter("on", k)

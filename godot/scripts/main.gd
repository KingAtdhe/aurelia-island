extends Node3D
var cam: Camera3D
var path: Array[Vector3] = []
var t := 0.0
# Aurelia Island (Godot): coast slice

func _ready():
	var env := WorldEnvironment.new(); var e := Environment.new()
	e.background_mode = Environment.BG_SKY; e.sky = Sky.new(); var sm := ProceduralSkyMaterial.new()
	sm.sky_top_color = Color(0.32, 0.52, 0.82); sm.sky_horizon_color = Color(0.72, 0.8, 0.88); sm.ground_horizon_color = Color(0.72, 0.8, 0.88)
	e.sky.sky_material = sm; e.ambient_light_source = Environment.AMBIENT_SOURCE_SKY; e.ambient_light_energy = 0.55
	e.tonemap_mode = Environment.TONE_MAPPER_FILMIC; e.fog_enabled = true; e.fog_light_color = Color(0.75, 0.82, 0.9); e.fog_density = 0.0009
	env.environment = e; add_child(env)
	var sun := DirectionalLight3D.new(); sun.rotation_degrees = Vector3(-38, -35, 0); sun.light_energy = 1.25; sun.shadow_enabled = true; sun.directional_shadow_max_distance = 250; add_child(sun)
	for f in ["res://assets/map/coast_base.glb", "res://assets/map/coast_detail.glb"]:
		var s = load(f)
		if s:
			var n = s.instantiate(); add_child(n); Look.apply(n)
	var sea := MeshInstance3D.new(); var pm := PlaneMesh.new(); pm.size = Vector2(6000, 6000); pm.subdivide_width = 1; sea.mesh = pm
	var wm := ShaderMaterial.new(); wm.shader = load("res://shaders/water.gdshader"); sea.material_override = wm; sea.position = Vector3(-1300, -0.25, 800); add_child(sea)
	var c := Camera3D.new(); c.far = 4000; add_child(c); c.current = true
	cam = c
	var w = JSON.parse_string(FileAccess.get_file_as_string("res://assets/world.json"))
	for r in w["roads"]:
		if r["name"] in ["Lighthouse Road", "Peninsula Road"]:
			var p = r["pts"]
			for i in range(0, p.size(), 3): path.append(Vector3(p[i], p[i + 1], p[i + 2]))
	var shots = OS.get_environment("SHOTS")
	if shots != "":
		await get_tree().process_frame
		var i := 0
		for spec in shots.split(";"):
			var v = spec.split(","); c.position = Vector3(float(v[0]), float(v[1]), float(v[2])); c.look_at(Vector3(float(v[3]), float(v[4]), float(v[5])))
			for k in 3: await RenderingServer.frame_post_draw
			get_viewport().get_texture().get_image().save_png("/tmp/gd_shot_%d.png" % i); i += 1
		get_tree().quit()


func _process(dt):          # until the car is in: a slow drive along the coast road
	if path.size() < 4 or OS.get_environment("SHOTS") != "": return
	t += dt * 3.0; var i := int(t) % (path.size() - 3); var f := t - floor(t)
	var a: Vector3 = path[i].lerp(path[i + 1], f); var b: Vector3 = path[i + 2].lerp(path[i + 3], f)
	cam.position = a + Vector3(0, 3.2, 0); cam.look_at(b + Vector3(0, 2.2, 0))

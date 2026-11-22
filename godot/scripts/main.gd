extends Node3D
# Aurelia Island (Godot): coast slice, drivable

var cam: Camera3D
var car: Car
var roads = {}
var cam_pos = Vector3.ZERO; var cam_yaw = 0.0; var cam_mode = 0
const CAMS = [[5.9, 2.05], [9.5, 3.6], [2.75, 0.62]]
var hud: CanvasLayer; var speed_lbl: Label; var gear_lbl: Label
var touch = { left = false, right = false, gas = false, brake = false, hand = false }

func _ready():
	var env = WorldEnvironment.new(); var e = Environment.new()
	e.background_mode = Environment.BG_SKY; e.sky = Sky.new(); var sm = ProceduralSkyMaterial.new()
	sm.sky_top_color = Color(0.24, 0.44, 0.78); sm.sky_horizon_color = Color(0.66, 0.76, 0.86); sm.ground_horizon_color = Color(0.66, 0.76, 0.86); sm.sun_angle_max = 20
	e.sky.sky_material = sm; e.ambient_light_source = Environment.AMBIENT_SOURCE_SKY; e.ambient_light_energy = 0.55
	e.tonemap_mode = Environment.TONE_MAPPER_FILMIC; e.tonemap_exposure = 0.95; e.fog_enabled = true; e.fog_light_color = Color(0.7, 0.78, 0.86); e.fog_density = 0.0006
	env.environment = e; add_child(env)
	var sun = DirectionalLight3D.new(); sun.rotation_degrees = Vector3(-38, -35, 0); sun.light_energy = 1.25; sun.shadow_enabled = true; sun.directional_shadow_max_distance = 30; add_child(sun)
	for f in ["res://assets/map/coast_base.glb", "res://assets/map/coast_detail.glb"]:
		var s = load(f)
		if s:
			var n = s.instantiate(); add_child(n); Look.apply(n); colliders(n)
	var fl = Flora.new(); add_child(fl); fl.build()
	var sea = MeshInstance3D.new(); var pm = PlaneMesh.new(); pm.size = Vector2(6000, 6000); sea.mesh = pm
	var wm = ShaderMaterial.new(); wm.shader = load("res://shaders/water.gdshader"); sea.material_override = wm; sea.position = Vector3(-1300, -0.25, 800); add_child(sea)
	var w = JSON.parse_string(FileAccess.get_file_as_string("res://assets/world.json"))
	for r in w["roads"]: roads[r["name"]] = r["pts"]
	cam = Camera3D.new(); cam.far = 3000; cam.fov = 62; add_child(cam); cam.current = true
	car = Car.new(); add_child(car)
	spawn("Peninsula Road", 30)
	make_hud()
	if OS.get_environment("SHOTS") != "": run_shots()
	if OS.get_environment("DRIVETEST") != "": drive_test()

func spawn(road: String, i: int):
	var p = roads[road]; var a = Vector3(p[i * 3], p[i * 3 + 1], p[i * 3 + 2]); var b = Vector3(p[i * 3 + 3], p[i * 3 + 4], p[i * 3 + 5])
	car.place(a, atan2(b.x - a.x, b.z - a.z)); cam_yaw = car.hd; cam_pos = a - Vector3(sin(car.hd), 0, cos(car.hd)) * 9 + Vector3(0, 4, 0)

# map pieces the car drives on get a collider; its surface type rides along as metadata
func colliders(root: Node):
	for n in root.find_children("*", "MeshInstance3D", true, false):
		var nm = String(n.name)
		var surf = ""
		if nm.begins_with("Road") or nm.begins_with("Bridges") or nm.begins_with("Pavement") or nm.begins_with("TerrainPave") or nm.begins_with("TunnelPortal"): surf = "road"
		elif nm.begins_with("Verge"): surf = "dirt"
		elif nm.begins_with("TerrainSand"): surf = "sand"
		elif nm.begins_with("Terrain__") or nm.begins_with("TerrainRock") or nm.begins_with("TerrainField") or nm.begins_with("TerrainForest") or nm.begins_with("Rocks") or nm.begins_with("Houses") or nm.begins_with("Structures") or nm.begins_with("Landmark"): surf = "grass"
		if surf == "": continue
		var sb = StaticBody3D.new(); sb.set_meta("surf", surf); var cs = CollisionShape3D.new(); cs.shape = n.mesh.create_trimesh_shape()
		sb.add_child(cs); n.add_child(sb)

func _physics_process(dt):
	var l = touch.left or Input.is_key_pressed(KEY_LEFT) or Input.is_key_pressed(KEY_A); var r = touch.right or Input.is_key_pressed(KEY_RIGHT) or Input.is_key_pressed(KEY_D)
	car.in_steer = (-1.0 if l else 0.0) + (1.0 if r else 0.0)
	car.in_gas = 1.0 if (touch.gas or Input.is_key_pressed(KEY_UP) or Input.is_key_pressed(KEY_W)) else 0.0
	car.in_brake = 1.0 if (touch.brake or Input.is_key_pressed(KEY_DOWN) or Input.is_key_pressed(KEY_S)) else 0.0
	car.in_hand = touch.hand or Input.is_key_pressed(KEY_SPACE)

func _process(dt):
	update_camera(dt)
	if speed_lbl: speed_lbl.text = "%d" % int(car.speed * 3.6); gear_lbl.text = "R" if car.vf < -0.5 and car.in_brake > 0 else str(car.gear + 1)

func update_camera(dt: float):          # port of the web chase camera: swings round the car, follows the slide in a drift
	var fx = sin(car.hd); var fz = cos(car.hd); var sp = car.speed; var dist: float = CAMS[cam_mode][0]; var hgt: float = CAMS[cam_mode][1]
	var c = Vector3(car.px, car.py, car.pz)
	if cam_mode == 2:
		cam.position = c + Vector3(fx * dist, hgt, fz * dist); cam.look_at(c + Vector3(fx * 30, hgt * 0.9, fz * 30)); return
	var vh = atan2(car.vx, car.vz) if sp > 3 else car.hd
	var dh = wrapf(vh - car.hd, -PI, PI)
	var ch = car.hd + clamp(dh, -0.85, 0.85) * 0.62 * (0.0 if car.vf < -1 else 1.0); var d = dist + min(sp, 60.0) * 0.022
	cam_yaw += wrapf(ch - cam_yaw, -PI, PI) * (1 - exp(-dt * 4.2))
	var cs = sin(cam_yaw); var cc = cos(cam_yaw); var ty = car.py + hgt + min(sp, 60.0) * 0.004
	cam_pos.x = car.px - cs * d; cam_pos.z = car.pz - cc * d; cam_pos.y = lerpf(cam_pos.y, ty, 1 - exp(-dt * 6))
	var gq = car.ground(cam_pos.x, cam_pos.z, cam_pos.y + 2)
	cam_pos.y = max(cam_pos.y, gq[0] + 0.6)
	cam.position = cam_pos; cam.look_at(c + Vector3(cs * 4, 1.1, cc * 4))

func circle_tex(r: int, col: Color, label := "") -> Texture2D:
	var img = Image.create(r * 2, r * 2, false, Image.FORMAT_RGBA8)
	for y in r * 2:
		for x in r * 2:
			var d = Vector2(x - r + 0.5, y - r + 0.5).length()
			if d < r - 1: img.set_pixel(x, y, col if d < r - 4 else Color(1, 1, 1, 0.55))
	return ImageTexture.create_from_image(img)

func make_hud():
	hud = CanvasLayer.new(); add_child(hud)
	var vs = get_viewport().get_visible_rect().size
	var mk = func(key: String, pos: Vector2, rad: int, txt: String):
		var b = TouchScreenButton.new(); b.texture_normal = circle_tex(rad, Color(0.08, 0.1, 0.13, 0.45)); b.texture_pressed = circle_tex(rad, Color(0.9, 0.9, 0.95, 0.35))
		var sh = CircleShape2D.new(); sh.radius = rad; b.shape = sh; b.shape_centered = true; b.position = pos - Vector2(rad, rad)
		b.pressed.connect(func(): touch[key] = true); b.released.connect(func(): touch[key] = false)
		var lb = Label.new(); lb.text = txt; lb.add_theme_font_size_override("font_size", 26); lb.position = Vector2(rad - 14, rad - 20); b.add_child(lb)
		hud.add_child(b)
	mk.call("left", Vector2(110, vs.y - 110), 62, "◀")
	mk.call("right", Vector2(260, vs.y - 110), 62, "▶")
	mk.call("gas", Vector2(vs.x - 110, vs.y - 130), 74, "▲")
	mk.call("brake", Vector2(vs.x - 270, vs.y - 100), 58, "▼")
	mk.call("hand", Vector2(vs.x - 390, vs.y - 90), 44, "D")
	speed_lbl = Label.new(); speed_lbl.add_theme_font_size_override("font_size", 56); speed_lbl.position = Vector2(vs.x - 190, 20); hud.add_child(speed_lbl)
	gear_lbl = Label.new(); gear_lbl.add_theme_font_size_override("font_size", 28); gear_lbl.position = Vector2(vs.x - 70, 40); hud.add_child(gear_lbl)
	var cb = Button.new(); cb.text = "Cam"; cb.position = Vector2(20, 20); cb.add_theme_font_size_override("font_size", 24); cb.pressed.connect(func(): cam_mode = (cam_mode + 1) % 3); hud.add_child(cb)
	var rb = Button.new(); rb.text = "Reset"; rb.position = Vector2(100, 20); rb.add_theme_font_size_override("font_size", 24); rb.pressed.connect(func(): car.place(Vector3(car.safe.x, car.safe.y, car.safe.z), car.safe.w)); hud.add_child(rb)

func run_shots():          # test: drive with full throttle and a few steering inputs, screenshot along the way
	var plan = [[0.0, 1.0, 0.0, 2.5], [0.0, 1.0, 0.0, 3.0], [0.0, 1.0, 0.0, 3.0], [0.0, 1.0, 0.0, 3.0], [0.0, 1.0, 0.0, 3.0], [0.0, 0.0, 1.0, 1.0]]
	if OS.get_environment("SHOTS") == "trees": plan = [[0.0, 0.0, 0.0, 1.0]]; car.place(Vector3(-1405, 58, 862), 0.9)
	var i = 0
	for st in plan:
		touch.left = st[0] < 0; touch.right = st[0] > 0; touch.gas = st[1] > 0; touch.brake = st[2] > 0
		await get_tree().create_timer(st[3]).timeout
		await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png("/tmp/gd_shot_%d.png" % i); print("SHOT %d pos %s speed %d gear %d surf %s" % [i, Vector3(car.px, car.py, car.pz), int(car.speed * 3.6), car.gear + 1, car.surf]); i += 1
	get_tree().quit()

func drive_test():          # headless: physics only, prints the state
	touch.gas = true
	for k in 16:
		await get_tree().create_timer(0.5).timeout
		if k == 8: touch.left = true
		if k == 11: touch.left = false; touch.hand = true
		if k == 13: touch.hand = false
		print("T %.1f pos (%.1f %.1f %.1f) v (%.2f %.2f) speed %.1f kmh gear %d rpm %d surf %s air %s beta %.2f" % [k * 0.5, car.px, car.py, car.pz, car.vx, car.vz, car.speed * 3.6, car.gear + 1, car.rpm, car.surf, car.air, car.beta])
	get_tree().quit()

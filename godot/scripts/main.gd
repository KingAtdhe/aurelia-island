extends Node3D
# Aurelia Island (Godot): coast slice, drivable

var cam: Camera3D
var car: Car
var roads = {}
var shake = 0.0
var menu: Menu; var menu_on = false; var orbit = 0.0
var cam_pos = Vector3.ZERO; var cam_yaw = 0.0; var cam_mode = 0
const CAMS = [[5.9, 2.05], [9.5, 3.6], [2.75, 0.62]]
var hud: CanvasLayer; var speed_lbl: Label; var gear_lbl: Label
var traffic: Traffic
var coll: Coll
var race: Race = null
var audio: CarAudio
var view_car = -1          # test shots: look at this traffic car instead of following the player
var touch = { left = false, right = false, gas = false, brake = false, hand = false }

func _ready():
	var env = WorldEnvironment.new(); var e = Environment.new()
	e.background_mode = Environment.BG_SKY; e.sky = Sky.new(); var sm = PanoramaSkyMaterial.new()
	sm.panorama = load("res://assets/sky.png"); sm.energy_multiplier = 1.0          # physical sky rendered in Blender with this sun, plus clouds
	e.sky.sky_material = sm; e.ambient_light_source = Environment.AMBIENT_SOURCE_SKY; e.ambient_light_energy = 0.75; e.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
	e.tonemap_mode = Environment.TONE_MAPPER_FILMIC; e.tonemap_exposure = 1.0; e.fog_enabled = true; e.fog_light_color = Color(0.72, 0.8, 0.88); e.fog_density = 0.0005; e.fog_sky_affect = 0.0
	e.glow_enabled = true; e.glow_intensity = 0.4; e.glow_bloom = 0.05; e.glow_hdr_threshold = 1.2
	env.environment = e; add_child(env)
	var sun = DirectionalLight3D.new(); sun.rotation_degrees = Vector3(-38, -35, 0); sun.light_energy = 1.35; sun.light_color = Color(1.0, 0.95, 0.86); sun.shadow_enabled = true; sun.directional_shadow_max_distance = 30; sun.directional_shadow_mode = DirectionalLight3D.SHADOW_ORTHOGONAL; add_child(sun)
	for f in ["res://assets/map/coast_base.glb", "res://assets/map/coast_detail.glb"]:
		var s = load(f)
		if s:
			var n = s.instantiate(); add_child(n); Look.apply(n); colliders(n)
	var fl = Flora.new(); add_child(fl); fl.build()
	var sea = MeshInstance3D.new(); var pm = PlaneMesh.new(); pm.size = Vector2(6000, 6000); sea.mesh = pm
	var wm = ShaderMaterial.new(); wm.shader = load("res://shaders/water.gdshader"); sea.material_override = wm; sea.position = Vector3(-1300, -0.25, 800); add_child(sea)
	var w = JSON.parse_string(FileAccess.get_file_as_string("res://assets/world.json"))
	for r in w["roads"]: roads[r["name"]] = r["pts"]
	cam = Camera3D.new(); cam.far = 3000; cam.near = 0.12; cam.fov = 62; add_child(cam); cam.current = true
	car = Car.new(); add_child(car)
	var co = Coll.new(); co.load_data("res://assets/coast_coll.json", roads); car.coll = co; coll = co
	car.crashed.connect(func(): shake = 0.35)
	spawn("Peninsula Road", 30)
	audio = CarAudio.new(); audio.car = car; add_child(audio)
	traffic = Traffic.new(); add_child(traffic); traffic.player = car; traffic.coll = co
	traffic.build(roads, int(OS.get_environment("TRAFFIC")) if OS.get_environment("TRAFFIC") != "" else 10)
	make_hud()
	menu_on = OS.get_environment("SHOTS") == "" and OS.get_environment("DRIVETEST") == "" and OS.get_environment("PERF") == "" and OS.get_environment("RACETEST") == ""
	if menu_on or OS.get_environment("SHOTS") == "menu": open_menu()
	if not menu_on: audio.ignition()
	if OS.get_environment("CAR") != "" and OS.get_environment("DRIVETEST") != "": car.setup(OS.get_environment("CAR"))
	if OS.get_environment("SHOTS") != "": run_shots()
	if OS.get_environment("PERF") != "": perf_test()
	if OS.get_environment("DRIVETEST") != "": drive_test()
	if OS.get_environment("TRAFFICTEST") != "": traffic_test()
	if OS.get_environment("RACETEST") != "": race_test(OS.get_environment("RACETEST"))
	if OS.get_environment("ROUTECHECK") != "": var rc = load("res://scripts/_routecheck.gd").new(); add_child(rc)

func start_race(rid: String):
	if race: race.stop(); race = null
	if menu: menu.queue_free(); menu = null
	menu_on = false; hud.visible = true; touch = { left = false, right = false, gas = false, brake = false, hand = false }
	race = Race.new(); add_child(race); race.start(rid, self)
	if not audio.on: audio.ignition()

func end_race():
	if race: race.stop(); race = null

func race_test(rid: String):     # headless or with SHOTS: the player's car drives itself; prints the race as it goes
	if menu: menu.queue_free(); menu = null; menu_on = false; hud.visible = true
	start_race(rid); race.autopilot = true
	var shots = OS.get_environment("RACESHOTS") != ""; var k = 0; var tt = 0.0
	var times = [2.0, 6.0, 14.0, 30.0]
	if shots and OS.get_environment("RACESHOTS") != "1": times = []; for x in OS.get_environment("RACESHOTS").split(","): times.append(float(x))
	while true:
		await get_tree().create_timer(1.0).timeout; tt += 1.0
		var line = "T %3d %-6s draws %d prims %d" % [int(tt), race.state, Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME), Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME)]
		for r in race.racers: line += " | %s s%.0f v%.0f%s" % [r.name.substr(0, 6), r.s, r.car.speed * 3.6, (" FIN " + Race.fmt(r.time)) if r.done else ""]
		print(line)
		if shots and (tt in times or race.panel != null):
			if OS.get_environment("RACESHOTS") == "1" and k > 0 and race.panel == null: continue
			await RenderingServer.frame_post_draw; get_viewport().get_texture().get_image().save_png("/tmp/race_shot_%d.png" % k); k += 1
		if race.panel != null or tt > 240:
			for r in race.standings(): print("RESULT %s %s" % [r.name, Race.fmt(r.time) if r.done else "DNF s=%.0f" % r.s])
			get_tree().quit(); return

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
	if race and race.autopilot: return          # test: the race drives the player's car
	var l = touch.left or Input.is_key_pressed(KEY_LEFT) or Input.is_key_pressed(KEY_A); var r = touch.right or Input.is_key_pressed(KEY_RIGHT) or Input.is_key_pressed(KEY_D)
	car.in_steer = (-1.0 if l else 0.0) + (1.0 if r else 0.0)
	car.in_gas = 1.0 if (touch.gas or Input.is_key_pressed(KEY_UP) or Input.is_key_pressed(KEY_W)) else 0.0
	car.in_brake = 1.0 if (touch.brake or Input.is_key_pressed(KEY_DOWN) or Input.is_key_pressed(KEY_S)) else 0.0
	car.in_hand = touch.hand or Input.is_key_pressed(KEY_SPACE)

func _process(dt):
	update_camera(dt)
	if view_car >= 0 and traffic and view_car < traffic.cars.size():
		var tn: Node3D = traffic.cars[view_car].n; var b = tn.global_transform.basis
		var ang = float(OS.get_environment("VANG")) if OS.get_environment("VANG") != "" else 0.75
		var cd = float(OS.get_environment("VDIST")) if OS.get_environment("VDIST") != "" else 6.2
		cam.global_position = tn.global_position + (b.x * cos(ang) + b.z * sin(ang)) * cd + Vector3(0, 1.5 * cd / 6.2, 0); cam.look_at(tn.global_position + Vector3(0, 0.8 if cd > 4 else 0.4, 0) + b.x * (0.3 if cd > 4 else 1.4))
	if speed_lbl: speed_lbl.text = "%d" % int(car.speed * 3.6); gear_lbl.text = "R" if car.vf < -0.5 and car.in_brake > 0 else str(car.gear + 1)

func update_camera(dt: float):          # port of the web chase camera: swings round the car, follows the slide in a drift
	if menu_on:            # garage: slow orbit round the parked car, framed to the right of the panel
		orbit += dt * 0.25; var c0 = Vector3(car.px, car.py, car.pz)
		cam.position = c0 + Vector3(sin(orbit) * 7.0, 2.2, cos(orbit) * 7.0); cam.look_at(c0 + Vector3(0, 0.6, 0)); cam.h_offset = -1.6
		return
	cam.h_offset = 0.0
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
	shake = maxf(0.0, shake - dt * 1.2)
	var sh: Vector3 = Vector3(randf() - 0.5, randf() - 0.5, randf() - 0.5) * shake * 0.6
	cam.position = cam_pos + sh; cam.look_at(c + Vector3(cs * 4, 1.1, cc * 4))

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
	var mb = Button.new(); mb.text = "Menu"; mb.position = Vector2(200, 20); mb.add_theme_font_size_override("font_size", 24); mb.pressed.connect(func(): end_race(); open_menu()); hud.add_child(mb)
	var rb = Button.new(); rb.text = "Reset"; rb.position = Vector2(100, 20); rb.add_theme_font_size_override("font_size", 24); rb.pressed.connect(reset_car); hud.add_child(rb)

func reset_car():
	if race:
		if race.state != "count": race.reset_player()
	else: car.place(Vector3(car.safe.x, car.safe.y, car.safe.z), car.safe.w)

func run_shots():          # test: drive with full throttle and a few steering inputs, screenshot along the way
	var plan = [[0.0, 1.0, 0.0, 2.5], [0.0, 1.0, 0.0, 3.0], [0.0, 1.0, 0.0, 3.0], [0.0, 1.0, 0.0, 3.0], [0.0, 1.0, 0.0, 3.0], [0.0, 0.0, 1.0, 1.0]]
	if OS.get_environment("SHOTS") == "trees": plan = [[0.0, 0.0, 0.0, 1.0]]; car.place(Vector3(-1405, 58, 862), 0.9)
	if OS.get_environment("CAR") != "": car.setup(OS.get_environment("CAR")); spawn("Peninsula Road", 30)
	if OS.get_environment("SHOTS") == "menu": plan = [[0.0, 0.0, 0.0, 1.5]]
	if OS.get_environment("SHOTS") == "menu" and OS.get_environment("MENUVIEW") == "races" and menu: menu.show_races(true)
	if OS.get_environment("SHOTS") == "traffic":             # park on the Peninsula Road and line the five traffic cars up ahead
		plan = [[0.0, 0.0, 0.0, 0.6], [0.0, 0.0, 0.0, 1.0], [0.0, 0.0, 0.0, 1.0], [0.0, 0.0, 0.0, 1.0], [0.0, 0.0, 0.0, 1.0], [0.0, 0.0, 0.0, 1.0], [0.0, 0.0, 0.0, 1.0]]
		for k in traffic.cars.size():
			var c = traffic.cars[k]
			if k < 5: c.lane = 1; c.dir = -1 if k % 2 == 0 else 1; c.d = 70.0 + k * 16.0; c.vmax = 0.0 if k % 2 == 1 else 6.0; c.v = c.vmax
		if OS.get_environment("SHOTS") == "car": plan = [[0.0, 0.0, 0.0, 1.0]]; cam_mode = 0; car.place(Vector3(-1405, 58, 862), 2.6)
	var i = 0
	for st in plan:
		touch.left = st[0] < 0; touch.right = st[0] > 0; touch.gas = st[1] > 0; touch.brake = st[2] > 0
		if OS.get_environment("SHOTS") == "traffic": view_car = i - 2 if i >= 2 else -1; touch.hand = true
		await get_tree().create_timer(st[3]).timeout
		await RenderingServer.frame_post_draw
		print("PERF draws %d prims %d objects %d vram %.0f MB" % [Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME), Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME), Performance.get_monitor(Performance.RENDER_TOTAL_OBJECTS_IN_FRAME), Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED) / 1048576.0])
		get_viewport().get_texture().get_image().save_png("/tmp/gd_shot_%d.png" % i); print("SHOT %d pos %s speed %d gear %d surf %s" % [i, Vector3(car.px, car.py, car.pz), int(car.speed * 3.6), car.gear + 1, car.surf]); i += 1
	get_tree().quit()

func drive_test():          # headless: physics only, prints the state
	touch.gas = true
	if OS.get_environment("DRIVETEST") == "crash":         # aim at the nearest tree off the road and hold the throttle
		var d = JSON.parse_string(FileAccess.get_file_as_string("res://assets/coast_coll.json")); var best = null; var bd = 1e9
		for o in d["circ"]:
			var dd = Vector2(o[0] - car.px, o[1] - car.pz).length()
			if dd > 25 and dd < bd: bd = dd; best = o
		car.place(Vector3(car.px, car.py, car.pz), atan2(best[0] - car.px, best[1] - car.pz)); print("tree at ", best, " dist ", bd)
	for k in 16:
		await get_tree().create_timer(0.5).timeout
		if k == 8: touch.left = true
		if k == 11: touch.left = false; touch.hand = true
		if k == 13: touch.hand = false
		if OS.get_environment("AUDIODBG") != "": print("   AUDIO ", audio.debug())
		print("T %.1f pos (%.1f %.1f %.1f) v (%.2f %.2f) speed %.1f kmh gear %d rpm %d surf %s air %s beta %.2f" % [k * 0.5, car.px, car.py, car.pz, car.vx, car.vz, car.speed * 3.6, car.gear + 1, car.rpm, car.surf, car.air, car.beta])
	get_tree().quit()

func perf_test():           # draw calls and triangles with each group switched off in turn
	await get_tree().create_timer(1.5).timeout
	var groups = { all = [], no_flora = [], no_map = [] }
	for c in get_children():
		if c is Flora: groups.no_flora.append(c)
		elif c.get_class() == "Node3D" and c != car and not (c is Flora): groups.no_map.append(c)
	for g in ["all", "no_flora", "no_map"]:
		for n in groups[g]: n.visible = false
		for k in 3: await RenderingServer.frame_post_draw
		print("PERF %s draws %d prims %d" % [g, Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME), Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME)])
		for n in groups[g]: n.visible = true
	var fl: Flora = null
	for c in get_children(): if c is Flora: fl = c
	var by := {}
	for m in fl.get_children():
		if m is MultiMeshInstance3D and m.visible:
			var d = m.global_position.distance_to(car.global_position)
			var key = m.get_meta("sp", "?") + ("_0" if m.visibility_range_begin == 0 else "_1")
			var inside = (d >= m.visibility_range_begin - 200) and (m.visibility_range_end == 0 or d <= m.visibility_range_end + 200)
			if inside: by[key] = by.get(key, 0) + m.multimesh.instance_count * m.multimesh.mesh.get_faces().size() / 3
	var keys = by.keys(); keys.sort_custom(func(a, b): return by[a] > by[b])
	for k in keys.slice(0, 12): print("FLORA %s ~%d tris (cells near)" % [k, by[k]])
	get_tree().quit()

func open_menu():
	menu_on = true; hud.visible = false; touch = { left = false, right = false, gas = false, brake = false, hand = false }
	menu = Menu.new(); add_child(menu)
	menu.race.connect(func(rid): start_race(rid))
	menu.drive.connect(func(id):
		if id.begins_with("preview:"): car.setup(id.substr(8)); spawn("Peninsula Road", 30); return
		if car.car_id != id: car.setup(id); spawn("Peninsula Road", 30)
		menu.queue_free(); menu = null; menu_on = false; hud.visible = true; audio.ignition())

func traffic_test():        # headless: watch every traffic car for jumps, sudden turns, overlaps and lost ground
	var last = {}
	for step in 600:
		await get_tree().physics_frame; await get_tree().physics_frame
		for k in traffic.cars.size():
			var c = traffic.cars[k]; var n: Node3D = c.n; var p = n.global_position; var f = n.global_transform.basis.x
			if last.has(k):
				var lp = last[k][0]; var lf = last[k][1]
				var jump = (p - lp).length(); var turn = rad_to_deg(lf.angle_to(f))
				if jump > 1.2 or abs(p.y - lp.y) > 0.25 or turn > 12: print("GLITCH t=%.2f car %d lane %d d %.1f dir %d jump %.2f dy %.2f turn %.1f" % [step / 30.0, k, c.lane, c.d, c.dir, jump, p.y - lp.y, turn])
			last[k] = [p, f]
			if not c.get("ground", true): print("NOGROUND car %d lane %d d %.1f" % [k, c.lane, c.d])
			for j in range(k + 1, traffic.cars.size()):
				var o = traffic.cars[j]
				if o.n.global_position.distance_to(p) < 4.5: print("OVERLAP t=%.2f cars %d %d lanes %d %d dirs %d %d dist %.2f" % [step / 30.0, k, j, c.lane, o.lane, c.dir, o.dir, o.n.global_position.distance_to(p)])
	get_tree().quit()

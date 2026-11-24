extends Node3D
# Aurelia Island (Godot): the whole island, drivable

var cam: Camera3D
var car: Car
var roads = {}
var shake = 0.0
var menu: Menu; var menu_on = false; var orbit = 0.0
var cam_pos = Vector3.ZERO; var cam_yaw = 0.0; var cam_mode = 0; var cam_fix = 0.0
const CAMS = [[5.9, 2.05], [9.5, 3.6], [2.75, 0.62]]
var hud: CanvasLayer; var speed_lbl: Label; var gear_lbl: Label; var minimap
var traffic: Traffic
var coll: Coll
var race: Race = null
var audio: CarAudio
var island: Island
var flora: Flora
var world_roads = []
var road_hw = {}
var landmarks = []          # [name, position] of the island's sights
var tunnels: Tunnels
var grass: Grass
var sun: DirectionalLight3D
var environment: Environment
var eyes = 0.0          # 0 in daylight, 1 deep in a tunnel
var car_sun: DirectionalLight3D
var probe: PackedByteArray; var probe_w = 0; var probe_h = 0; var shade = 1.0
const START = ["Peninsula Road", 30]
var view_car = -1          # test shots: look at this traffic car instead of following the player
var touch = { left = false, right = false, gas = false, brake = false, hand = false }

func _ready():
	var env = WorldEnvironment.new(); var e = Environment.new()
	e.background_mode = Environment.BG_SKY; e.sky = Sky.new(); var sm = PanoramaSkyMaterial.new()
	sm.panorama = load("res://assets/sky.png"); sm.energy_multiplier = 1.0          # physical sky rendered in Blender with this sun, plus clouds
	e.sky.sky_material = sm; e.ambient_light_source = Environment.AMBIENT_SOURCE_SKY; e.ambient_light_energy = 0.75; e.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
	e.tonemap_mode = Environment.TONE_MAPPER_FILMIC; e.tonemap_exposure = 1.0; e.fog_enabled = true; e.fog_light_color = Color(0.72, 0.8, 0.88); e.fog_density = 0.0005; e.fog_sky_affect = 0.0
	e.glow_enabled = true; e.glow_intensity = 0.4; e.glow_bloom = 0.05; e.glow_hdr_threshold = 1.2
	e.adjustment_enabled = true; e.adjustment_contrast = 1.07; e.adjustment_saturation = 1.1          # a touch more punch: the haze and filmic curve flatten the colours
	env.environment = e; add_child(env); environment = e
	sun = DirectionalLight3D.new(); sun.rotation_degrees = Vector3(-38, -35, 0); sun.light_energy = 1.35; sun.light_color = Color(1.0, 0.95, 0.86); sun.shadow_enabled = true; sun.directional_shadow_max_distance = 60; sun.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_2_SPLITS; sun.directional_shadow_split_1 = 0.25; sun.light_cull_mask = 1; add_child(sun)
	# the car sun lights only the cars and dims where the island bake has shade; no shadow map of its own
	# (on the Compatibility renderer a second shadowed sun draws the whole scene again)
	car_sun = sun.duplicate(); car_sun.light_cull_mask = 2; car_sun.shadow_enabled = false; add_child(car_sun)
	_load_probe()
	var w = JSON.parse_string(FileAccess.get_file_as_string("res://assets/world.json"))
	for r in w["roads"]: roads[r["name"]] = r["pts"]; road_hw[r["name"]] = float(r["w"]) * 0.5
	world_roads = w["roads"]
	for l in w["landmarks"]: landmarks.append([l["name"], Vector3(l["pos"][0], l["pos"][1], l["pos"][2])])
	var sp0 = _road_pt(START[0], START[1])
	island = Island.new(); add_child(island); island.load_base(sp0)
	flora = Flora.new(); add_child(flora); flora.build(sp0)
	tunnels = Tunnels.new(); add_child(tunnels); tunnels.build(w, island)
	grass = Grass.new(); add_child(grass); grass.build(w)
	var sea = MeshInstance3D.new(); var pm = PlaneMesh.new(); pm.size = Vector2(16000, 16000); sea.mesh = pm
	var wm = ShaderMaterial.new(); wm.shader = load("res://shaders/water.gdshader"); sea.material_override = wm; sea.position = Vector3(0, -0.25, 0); add_child(sea)
	get_viewport().mesh_lod_threshold = 4.0          # simpler versions of far meshes (LODs made at import): no visible change on a phone screen
	cam = Camera3D.new(); cam.far = 3000; cam.near = 0.12; cam.fov = 62; add_child(cam); cam.current = true
	Progress.load_save()
	car = Car.new(); car.player = true; car.car_id = Progress.car if Progress.car in Progress.cars else "vortex"; add_child(car)
	var co = Coll.new(); co.load_data("res://assets/island/coll.json", roads); car.coll = co; coll = co; grass.coll = co
	car.knocked.connect(func(o): if o.size() > 5: flora.hide_instance(o[4], o[5]))
	car.crashed.connect(func(): shake = 0.35)
	car.nearest_road = nearest_road
	spawn(START[0], START[1])
	audio = CarAudio.new(); audio.car = car; add_child(audio)
	traffic = Traffic.new(); add_child(traffic); traffic.player = car; traffic.coll = co
	traffic.build(roads, int(OS.get_environment("TRAFFIC")) if OS.get_environment("TRAFFIC") != "" else 14, world_roads)
	make_hud()
	menu_on = OS.get_environment("SHOTS") == "" and OS.get_environment("TOUR") == "" and OS.get_environment("PROBE") == "" and OS.get_environment("DRIVETEST") == "" and OS.get_environment("PERF") == "" and OS.get_environment("RACETEST") == "" and OS.get_environment("PHYSTEST") == "" and OS.get_environment("FUZZ") == ""
	if menu_on or OS.get_environment("SHOTS") == "menu": open_menu()
	if not menu_on: audio.ignition()
	if OS.get_environment("CAR") != "" and OS.get_environment("DRIVETEST") != "": car.setup(OS.get_environment("CAR"))
	if OS.get_environment("SHOTS") != "": run_shots()
	if OS.get_environment("PERF") != "": perf_test()
	if OS.get_environment("DRIVETEST") != "": drive_test()
	if OS.get_environment("TRAFFICTEST") != "": traffic_test()
	_prewarm()
	if OS.get_environment("RACETEST") != "": race_test(OS.get_environment("RACETEST"))
	if OS.get_environment("PHYSTEST") != "": phys_test(OS.get_environment("PHYSTEST"))
	if OS.get_environment("FUZZ") != "": add_child(load("res://scripts/_fuzz.gd").new())
	if OS.get_environment("FLOW") != "": add_child(load("res://scripts/_flow.gd").new())
	if OS.get_environment("TOUR") != "": add_child(load("res://scripts/_tour.gd").new())
	if OS.get_environment("PROBE") != "": add_child(load("res://scripts/_probe.gd").new())
	if OS.get_environment("TIMING") != "": add_child(load("res://scripts/_timing.gd").new())
	if OS.get_environment("ROUTECHECK") != "": var rc = load("res://scripts/_routecheck.gd").new(); add_child(rc)

# merge every car model and load the rivals' light models while the game loads, so the first race starts without a hitch
func _prewarm():
	for id in Car.CARS:
		load(Car.CARS[id].far); load(Car.CARS[id].mid)
		if not Car._merged.has(id):
			var c = Car.new(); c.car_id = id; c.process_mode = Node.PROCESS_MODE_DISABLED; add_child(c); c.queue_free()

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
			var worst = island.attach_ms.duplicate(); worst.sort_custom(func(a, b): return a[1] > b[1])
			print("CAREER credits %d unlocked %s" % [Progress.cr, str(Progress.unlocked.keys())])
			print("STREAM %d chunks put in, worst ms %s" % [worst.size(), str(worst.slice(0, 5))])
			get_tree().quit(); return

# nearest point on any road of the island, facing along the road (the direction closer to the car's own heading)
func nearest_road(p: Vector3):
	var best = null; var bd = 1e18
	for r in world_roads:
		if r["type"] in ["dirt", "circuit"] and r["name"] != "Circuit": continue
		var a = roads[r["name"]]; var n = a.size() / 3
		for i in range(0, n - 1):
			var dx = a[i * 3] - p.x; var dz = a[i * 3 + 2] - p.z
			if abs(dx) > 400 or abs(dz) > 400: continue
			var d = dx * dx + dz * dz + pow(a[i * 3 + 1] - p.y, 2) * 4.0
			if d < bd: bd = d; best = [r["name"], i, n - 1]
	if best == null: return null
	var a = roads[best[0]]; var i: int = mini(best[1], best[2] - 1)
	var q0 = Vector3(a[i * 3], a[i * 3 + 1], a[i * 3 + 2]); var q1 = Vector3(a[i * 3 + 3], a[i * 3 + 4], a[i * 3 + 5])
	var h = atan2(q1.x - q0.x, q1.z - q0.z)
	if abs(wrapf(h - car.hd, -PI, PI)) > PI / 2: h += PI
	return [q0, h]

# jump to the nearest road to a place: the map round it is loaded at once so the car never lands in an empty world
func travel_to(p: Vector3):
	var best = null; var bd = 1e18
	for r in world_roads:
		if not (r["type"] in ["hwy", "road", "street"]): continue
		var a = roads[r["name"]]; var n = a.size() / 3
		for i in range(1, n - 2):
			var d = Vector2(a[i * 3] - p.x, a[i * 3 + 2] - p.z).length_squared()
			if d < bd: bd = d; best = [r["name"], i]
	spawn(best[0], best[1]); prime()

func prime():
	var fp = Vector3(car.px, car.py, car.pz)
	island.focus = fp; flora.focus = fp; island.prime(); flora.prime()
	for c in traffic.cars: traffic._respawn(c, fp, true)

# sun visibility from the island light bake (assets/island/bake_sun.bin, 8-bit, island bounds): how much sun reaches a point
func _load_probe():
	var f = FileAccess.open("res://assets/island/bake_sun.bin", FileAccess.READ)
	if f == null: return
	probe_w = f.get_32(); probe_h = f.get_32(); probe = f.get_buffer(probe_w * probe_h)

func sun_at(p: Vector3) -> float:
	if probe_w == 0: return 1.0
	var fx = clampf((p.x + 2400.0) / 4800.0 * probe_w - 0.5, 0.0, probe_w - 1.001); var fy = clampf((p.z + 1680.0) / 3360.0 * probe_h - 0.5, 0.0, probe_h - 1.001)
	var ix = int(fx); var iy = int(fy); var u = fx - ix; var v = fy - iy; var i = iy * probe_w + ix
	return ((probe[i] * (1 - u) + probe[i + 1] * u) * (1 - v) + (probe[i + probe_w] * (1 - u) + probe[i + probe_w + 1] * u) * v) / 255.0

# a short message at the top of the screen (credits earned, places found)
var _toast: Label
func toast(t: String, secs := 2.6):
	if _toast == null:
		_toast = Label.new(); _toast.add_theme_font_size_override("font_size", 28); _toast.add_theme_color_override("font_color", Hud.ACCENT)
		_toast.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.7)); _toast.add_theme_constant_override("outline_size", 6)
		_toast.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER; _toast.size = Vector2(900, 40); _toast.position = Vector2(get_viewport().get_visible_rect().size.x / 2 - 450, 84); hud.add_child(_toast)
	_toast.text = t; _toast.modulate.a = 1.0; _toast.set_meta("t", secs)

# free roam: driving up to one of the island's landmarks for the first time pays a finder's fee
var _lm_t = 0.0
func _landmarks(dt: float):
	if _toast:
		var tt: float = _toast.get_meta("t", 0.0) - dt; _toast.set_meta("t", tt); _toast.modulate.a = clampf(tt / 0.6, 0.0, 1.0)
	_lm_t -= dt
	if _lm_t > 0 or race or menu_on: return
	_lm_t = 0.5
	for l in landmarks:
		var key = "%s@%d,%d" % [l[0], int(l[1].x), int(l[1].z)]
		if Progress.found.has(key): continue
		if Vector2(l[1].x - car.px, l[1].z - car.pz).length() < 110.0:
			Progress.found[key] = true; Progress.earn(Progress.LANDMARK); toast("Discovered: %s   +%d credits" % [l[0], Progress.LANDMARK])

func _road_pt(road: String, i: int) -> Vector3:
	var p = roads[road]; return Vector3(p[i * 3], p[i * 3 + 1], p[i * 3 + 2])

func spawn(road: String, i: int):
	var p = roads[road]; var a = Vector3(p[i * 3], p[i * 3 + 1], p[i * 3 + 2]); var b = Vector3(p[i * 3 + 3], p[i * 3 + 4], p[i * 3 + 5])
	car.place(a, atan2(b.x - a.x, b.z - a.z)); cam_yaw = car.hd; cam_pos = a - Vector3(sin(car.hd), 0, cos(car.hd)) * 9 + Vector3(0, 4, 0)

func _physics_process(dt):
	if race and race.autopilot: return          # test: the race drives the player's car
	var l = touch.left or Input.is_key_pressed(KEY_LEFT) or Input.is_key_pressed(KEY_A); var r = touch.right or Input.is_key_pressed(KEY_RIGHT) or Input.is_key_pressed(KEY_D)
	car.in_steer = (-1.0 if l else 0.0) + (1.0 if r else 0.0)
	car.in_gas = 1.0 if (touch.gas or Input.is_key_pressed(KEY_UP) or Input.is_key_pressed(KEY_W)) else 0.0
	car.in_brake = 1.0 if (touch.brake or Input.is_key_pressed(KEY_DOWN) or Input.is_key_pressed(KEY_S)) else 0.0
	car.in_hand = touch.hand or Input.is_key_pressed(KEY_SPACE)

func _process(dt):
	update_camera(dt)
	_landmarks(dt)
	var fp = Vector3(car.px, car.py, car.pz) if view_car < 0 else cam.global_position
	island.focus = fp; flora.focus = fp; grass.focus = fp
	# eyes adjusting in a tunnel: the sun and the sky fade, exposure opens up a little
	var tin = tunnels.inside(Vector3(car.px, car.py, car.pz)) if tunnels else 0.0
	eyes = move_toward(eyes, tin, dt * (0.9 if tin > eyes else 0.6))
	sun.light_energy = 1.35 * (1.0 - 0.88 * eyes); environment.ambient_light_energy = 0.75 * (1.0 - 0.75 * eyes); environment.tonemap_exposure = 1.0 + 0.12 * eyes
	shade = lerpf(shade, sun_at(Vector3(car.px, car.py, car.pz)), clampf(dt * 5.0, 0.0, 1.0))
	car_sun.light_energy = sun.light_energy * lerpf(0.1, 1.0, shade)
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
	var want = cam_pos + sh; var eye = c + Vector3(0, 1.3, 0)
	var hit = get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(eye, want))
	if hit: want = hit.position + (eye - hit.position).normalized() * 0.45            # a wall, house or hill between: come in front of it, never through
	cam_fix = lerpf(cam_fix, 1.0 if hit else 0.0, 1.0 - exp(-dt * 10.0))
	cam.position = want; cam.look_at(c + Vector3(cs * 4, 1.1, cc * 4))

func circle_tex(r: int, col: Color, label := "") -> Texture2D:          # touch button: soft-edged disc with a light rim
	var img = Image.create(r * 2, r * 2, false, Image.FORMAT_RGBA8)
	for y in r * 2:
		for x in r * 2:
			var d = Vector2(x - r + 0.5, y - r + 0.5).length()
			var a = clampf(r - 1.0 - d, 0.0, 1.0)
			if a <= 0.0: continue
			var rim = clampf(1.0 - abs(d - (r - 3.5)) / 1.6, 0.0, 1.0)
			var shade = 1.0 - 0.25 * (y / float(r * 2))
			var c = Color(col.r * shade, col.g * shade, col.b * shade, col.a).lerp(Color(1, 1, 1, 0.7), rim)
			c.a *= a; img.set_pixel(x, y, c)
	return ImageTexture.create_from_image(img)

func make_hud():
	hud = CanvasLayer.new(); add_child(hud)
	var vs = get_viewport().get_visible_rect().size
	var mk = func(key: String, pos: Vector2, rad: int, txt: String):
		var b = TouchScreenButton.new(); b.texture_normal = circle_tex(rad, Color(0.08, 0.1, 0.13, 0.45)); b.texture_pressed = circle_tex(rad, Color(0.9, 0.9, 0.95, 0.35))
		var sh = CircleShape2D.new(); sh.radius = rad; b.shape = sh; b.shape_centered = true; b.position = pos - Vector2(rad, rad)
		b.pressed.connect(func(): touch[key] = true); b.released.connect(func(): touch[key] = false)
		var lb = Label.new(); lb.text = txt; lb.add_theme_font_size_override("font_size", int(rad * 0.5)); lb.size = Vector2(rad * 2, rad * 2)
		lb.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER; lb.vertical_alignment = VERTICAL_ALIGNMENT_CENTER; lb.modulate = Color(1, 1, 1, 0.9); b.add_child(lb)
		hud.add_child(b)
	mk.call("left", Vector2(110, vs.y - 110), 62, "◀")
	mk.call("right", Vector2(260, vs.y - 110), 62, "▶")
	mk.call("gas", Vector2(vs.x - 110, vs.y - 130), 74, "▲")
	mk.call("brake", Vector2(vs.x - 270, vs.y - 100), 58, "▼")
	mk.call("hand", Vector2(vs.x - 390, vs.y - 90), 44, "D")
	var gauge = Hud.Gauge.new(); gauge.car = car; gauge.size = Vector2(186, 186); gauge.position = Vector2(338, vs.y - 196); gauge.mouse_filter = Control.MOUSE_FILTER_IGNORE; hud.add_child(gauge)
	minimap = Hud.MiniMap.new(self, 230.0); minimap.position = Vector2(vs.x - 250, 20); hud.add_child(minimap)
	var x = 20.0
	for bdef in [["CAM", func(): cam_mode = (cam_mode + 1) % 3], ["RESET", reset_car], ["MENU", func(): end_race(); open_menu()]]:
		var b = Button.new(); b.text = bdef[0]; b.position = Vector2(x, 20); b.custom_minimum_size = Vector2(96, 48); Hud.style_button(b); b.pressed.connect(bdef[1]); hud.add_child(b); x += 108.0

func reset_car():
	if race:
		if race.state != "count": race.reset_player()
	else: car.place(Vector3(car.safe.x, car.safe.y, car.safe.z), car.safe.w)

func run_shots():          # test: drive with full throttle and a few steering inputs, screenshot along the way
	var plan = [[0.0, 1.0, 0.0, 2.5], [0.0, 1.0, 0.0, 3.0], [0.0, 1.0, 0.0, 3.0], [0.0, 1.0, 0.0, 3.0], [0.0, 1.0, 0.0, 3.0], [0.0, 0.0, 1.0, 1.0]]
	if OS.get_environment("SHOTS") == "trees": plan = [[0.0, 0.0, 0.0, 1.0]]; car.place(Vector3(-1405, 58, 862), 0.9)
	if OS.get_environment("CAR") != "": car.setup(OS.get_environment("CAR")); spawn("Peninsula Road", 30)
	if OS.get_environment("SHOTS") == "menu": plan = [[0.0, 0.0, 0.0, 1.5]]
	if OS.get_environment("SHOTS") == "menu" and OS.get_environment("MENUVIEW") != "" and menu: menu.show_page(OS.get_environment("MENUVIEW"))
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
		var d = JSON.parse_string(FileAccess.get_file_as_string("res://assets/island/coll.json")); var best = null; var bd = 1e9
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
	menu.race.connect(func(rid):
		if car.car_id != Progress.car: car.setup(Progress.car)          # the car on show may be one not bought yet
		start_race(rid))
	menu.changed.connect(func(): car.setup(car.car_id))
	menu.travel.connect(func(rg):
		if car.car_id != Progress.car: car.setup(Progress.car)
		travel_to(Vector3(rg[1], 0, rg[2]))
		menu.queue_free(); menu = null; menu_on = false; hud.visible = true; audio.ignition())
	menu.drive.connect(func(id):
		if id.begins_with("preview:"): car.setup(id.substr(8)); spawn(START[0], START[1]); return
		if car.car_id != id: car.setup(id); spawn(START[0], START[1])
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

func phys_test(kind: String):    # test: log the car every physics frame through a scripted scenario
	var t = 0.0; var last = Vector3(car.px, car.py, car.pz); var lp = [car.pitch, car.roll]
	var plan = { start = [[0.0, 3.0, 0, 0, false], [3.0, 7.0, 1, 0, false], [7.0, 9.0, 0, 1, false]],
		crash = [[0.0, 9.0, 1, 0, false]], traffic = [[0.0, 9.0, 1, 0, false]],
		drift = [[0.0, 4.0, 1, 0, false], [4.0, 4.6, 1, 0, true], [4.6, 9.0, 1, 0, false]],
		reverse = [[0.0, 3.0, 0, 1, false], [3.0, 5.0, 0, 0, false], [5.0, 7.0, 1, 0, false], [7.0, 9.0, 0, 1, false]],
		shots = [[0.0, 14.5, 1, 0, false], [14.5, 16.5, 0, 1, false]], offroad = [[0.0, 14.0, 1, 0, false]] }.get(kind, [])
	var tend = 16.5 if kind == "shots" else (14.0 if kind == "offroad" else 9.0)
	car.crashed.connect(func(): print("EV CRASH t%.2f impact %.1f surf %s air %s v %.1f at %s" % [t, car.impact, car.surf, car.air, car.speed * 3.6, Vector3(car.px, car.py, car.pz)]))
	car.landed.connect(func(v): print("EV LANDED t%.2f vy %.1f surf %s v %.1f" % [t, v, car.surf, car.speed * 3.6]))
	var lsurf = car.surf
	if kind == "crash":            # aim at a tree off the road
		var d = JSON.parse_string(FileAccess.get_file_as_string("res://assets/island/coll.json")); var best = null; var bd = 1e9
		for o in d["circ"]:
			var dd = Vector2(o[0] - car.px, o[1] - car.pz).length()
			if dd > 35 and dd < bd: bd = dd; best = o
		car.place(Vector3(car.px, car.py, car.pz), atan2(best[0] - car.px, best[1] - car.pz))
	if kind == "traffic":          # line up behind the nearest traffic car on its lane, 45 m back
		await get_tree().create_timer(0.3).timeout
		var c = traffic.cars[0]; var l = traffic.lanes[c.lane]; var a = traffic._at(l, clampf(c.d - 45.0 * c.dir, 2.0, l.len - 2.0))
		var tg: Vector3 = a[1] * c.dir; var rt = Vector3(-tg.z, 0, tg.x).normalized(); var p0: Vector3 = a[0] + rt * l.off
		car.place(p0, atan2(tg.x, tg.z)); c.vmax = 4.0; c.v = 4.0
	if kind == "drift": touch.right = false
	while t < tend:
		await get_tree().physics_frame; t += 1.0 / Engine.physics_ticks_per_second
		for st in plan:
			if t >= st[0] and t < st[1]: touch.gas = st[2] == 1; touch.brake = st[3] == 1; touch.hand = st[4]
		if kind == "drift": touch.right = t > 3.8 and t < 6.0
		if kind == "offroad": touch.right = t > 3.0 and t < 3.45; touch.left = t > 6.0 and t < 6.6
		if car.surf != lsurf: print("EV SURF t%.2f %s -> %s v %.1f beta %.2f yr %.2f" % [t, lsurf, car.surf, car.speed * 3.6, car.beta, car.yr]); lsurf = car.surf
		var p = Vector3(car.px, car.py, car.pz); var d = p - last
		var flag = ""
		if abs(d.y) > 0.05: flag += " DY"
		if abs(car.pitch - lp[0]) > 0.02 or abs(car.roll - lp[1]) > 0.02: flag += " TILT"
		if car.air: flag += " AIR"
		var nd = 1e9
		for c in traffic.cars: nd = minf(nd, c.n.global_position.distance_to(p))
		if kind == "shots" and t > 14.4:
			var g = car.ground(car.px, car.pz, car.py + 3.0)
			print("SH t%.3f y%.3f ground %.3f (%s) air %s vy%+.2f pitch%+.2f roll%+.2f v%.1f vf%.1f" % [t, car.py, g[0], g[1], car.air, car.vy, car.pitch, car.roll, car.speed * 3.6, car.vf])
		if flag != "" or int(t * 60) % 15 == 0 or nd < 6.0 or t < 0.3:
			print("TR nearest traffic %.1f m" % nd) if nd < 8.0 else null
			print("   AU " + audio.debug())
			if kind == "traffic": var c0 = traffic.cars[0]; print("   T0 free %s v %.1f pos %s" % [c0.get("free", false), c0.v, c0.n.global_position])
			print("PH t%.3f vx%+.2f vz%+.2f hd%.3f yr%+.3f y%.3f dy%+.3f v%.1f vy%+.2f pitch%+.3f roll%+.3f gear%d rpm%d surf %s%s" % [t, car.vx, car.vz, car.hd, car.yr, car.py, d.y, car.speed * 3.6, car.vy, car.pitch, car.roll, car.gear + 1, car.rpm, car.surf, flag])
		last = p; lp = [car.pitch, car.roll]
	get_tree().quit()

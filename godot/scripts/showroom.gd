extends Node3D
class_name Showroom
# The showroom behind the start screen and the garage: the car on a lit turntable in a dark studio, high above the island
# (only cars and the studio are drawn there). Drag sideways to turn the car; it turns slowly on its own otherwise.
# Entering keeps where the car was on the island (the map stays loaded round that spot); leaving puts it back there.
const POS = Vector3(0.0, 700.0, 0.0)
const LAYER = 8          # render layer of the studio (cars are on 2)
var main
var active := false
var saved := Vector4.ZERO          # the car on the island: x, y, z, heading
var env: Environment
var key: DirectionalLight3D
var table: Node3D
var spin := 0.0; var spin_v := 0.0; var idle := 0.0; var orbit := 0.6
var _was = {}

func _init(m): main = m; name = "Showroom"; physics_interpolation_mode = Node.PHYSICS_INTERPOLATION_MODE_OFF

func build():
	position = POS; visible = false
	env = Environment.new(); env.background_mode = Environment.BG_SKY; env.sky = Sky.new()
	var sm = ShaderMaterial.new(); sm.shader = load("res://shaders/studio_sky.gdshader"); env.sky.sky_material = sm
	env.sky.radiance_size = Sky.RADIANCE_SIZE_256
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY; env.ambient_light_energy = 0.55; env.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC; env.tonemap_exposure = 1.05
	env.glow_enabled = true; env.glow_intensity = 0.5; env.glow_bloom = 0.04; env.glow_hdr_threshold = 1.1
	env.adjustment_enabled = true; env.adjustment_contrast = 1.08; env.adjustment_saturation = 1.08
	# floor: dark, softly lit in the middle, fading into the room
	var fl := MeshInstance3D.new(); var pm := PlaneMesh.new(); pm.size = Vector2(160, 160); fl.mesh = pm
	var g := Gradient.new(); g.set_color(0, Color(0.13, 0.135, 0.145)); g.set_color(1, Color(0.0, 0.0, 0.0))
	g.add_point(0.05, Color(0.075, 0.078, 0.085)); g.add_point(0.16, Color(0.012, 0.013, 0.015))
	var gt := GradientTexture2D.new(); gt.gradient = g; gt.fill = GradientTexture2D.FILL_RADIAL; gt.fill_from = Vector2(0.5, 0.5); gt.fill_to = Vector2(1.0, 0.5); gt.width = 512; gt.height = 512
	var fm := StandardMaterial3D.new(); fm.albedo_texture = gt; fm.roughness = 0.5; fm.metallic_specular = 0.18
	fl.material_override = fm; fl.position = Vector3(0, -0.09, 0); _layer(fl); add_child(fl)
	# turntable: brushed dark metal disc with a lit edge ring
	table = Node3D.new(); add_child(table)
	var disc := MeshInstance3D.new(); var cm := CylinderMesh.new(); cm.top_radius = 3.2; cm.bottom_radius = 3.25; cm.height = 0.09; cm.radial_segments = 96; disc.mesh = cm
	var dm := StandardMaterial3D.new(); dm.albedo_color = Color(0.06, 0.062, 0.068); dm.metallic = 0.85; dm.roughness = 0.38
	disc.material_override = dm; disc.position = Vector3(0, -0.045, 0); _layer(disc); table.add_child(disc)
	var ring := MeshInstance3D.new(); var tm := TorusMesh.new(); tm.inner_radius = 3.2; tm.outer_radius = 3.245; tm.rings = 96; tm.ring_segments = 6; ring.mesh = tm
	var rm := StandardMaterial3D.new(); rm.albedo_color = Hud.ACCENT; rm.emission_enabled = true; rm.emission = Color(1.0, 0.45, 0.05); rm.emission_energy_multiplier = 1.1
	ring.material_override = rm; ring.scale = Vector3(1, 0.35, 1); ring.position = Vector3(0, -0.02, 0); _layer(ring); table.add_child(ring)
	for k in 12:          # small marks round the disc so its turning reads
		var mk := MeshInstance3D.new(); var bm := BoxMesh.new(); bm.size = Vector3(0.05, 0.004, 0.34); mk.mesh = bm
		var mm := StandardMaterial3D.new(); mm.albedo_color = Color(0.5, 0.5, 0.52); mm.roughness = 0.5; mk.material_override = mm
		var a = TAU * k / 12.0; mk.position = Vector3(sin(a) * 2.95, 0.001, cos(a) * 2.95); mk.rotation.y = a; _layer(mk); table.add_child(mk)
	# the car stands on this (its ground rays hit the map layer)
	var sb := StaticBody3D.new(); sb.set_meta("surf", "road"); var cs := CollisionShape3D.new(); var bx := BoxShape3D.new(); bx.size = Vector3(12, 1, 12)
	cs.shape = bx; cs.position = Vector3(0, -0.5, 0); sb.add_child(cs); add_child(sb)
	# key light from above front, with a soft shadow on the floor; it lights only the car and the studio
	key = DirectionalLight3D.new(); key.light_cull_mask = 2 | LAYER; key.light_energy = 0.9; key.light_color = Color(1.0, 0.97, 0.93)
	key.shadow_enabled = true; key.directional_shadow_mode = DirectionalLight3D.SHADOW_ORTHOGONAL; key.directional_shadow_max_distance = 18.0; key.shadow_blur = 2.5
	key.rotation_degrees = Vector3(-62, 28, 0); key.visible = false; add_child(key)

func _layer(g: GeometryInstance3D): g.layers = LAYER; g.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF

func enter():
	if active: return
	var car: Car = main.car
	if Vector3(car.px, car.py, car.pz).distance_to(POS) > 50.0: saved = Vector4(car.px, car.py, car.pz, car.hd)          # (not when coming back from a warm-up)
	active = true; visible = true; key.visible = true
	_was = { sun = main.sun.visible, car_sun = main.car_sun.visible }
	main.sun.visible = false; main.car_sun.visible = false
	if main.carenv: main.carenv.visible = false          # in here the studio is what the paint reflects
	var cam: Camera3D = main.cam; cam.environment = env; cam.cull_mask = 2 | LAYER; cam.far = 80.0
	main.traffic.process_mode = Node.PROCESS_MODE_DISABLED
	var b = AudioServer.get_bus_index("Ambience"); if b >= 0: AudioServer.set_bus_mute(b, true)
	car.place(POS, spin); car.frozen = true
	idle = 0.0

func leave(put_back := true):
	if not active: return
	active = false; visible = false; key.visible = false
	main.sun.visible = _was.get("sun", true); main.car_sun.visible = _was.get("car_sun", true)
	if main.carenv: main.carenv.visible = true
	var cam: Camera3D = main.cam; cam.environment = null; cam.cull_mask = 0xFFFFF & ~CarEnv.LAYER; cam.far = Gfx.FAR[Gfx.get_level()]; cam.h_offset = 0.0
	main.traffic.process_mode = Node.PROCESS_MODE_INHERIT
	var b = AudioServer.get_bus_index("Ambience"); if b >= 0: AudioServer.set_bus_mute(b, false)
	var car: Car = main.car; car.frozen = false
	if put_back: car.place(Vector3(saved.x, saved.y, saved.z), saved.w)

func car_changed():          # a different car on the turntable
	if active: main.car.place(POS, spin); main.car.frozen = true

# where the island should stay loaded while the car is up here
func focus() -> Vector3: return Vector3(saved.x, saved.y, saved.z)

func drag(dx: float):          # a swipe across the screen turns the table
	spin_v = clampf(spin_v + dx * 0.012, -6.0, 6.0); idle = 0.0

func update(cam: Camera3D, dt: float):
	idle += dt
	var auto = 0.18 * clampf((idle - 2.5) / 1.5, 0.0, 1.0)
	spin_v = lerpf(spin_v, 0.0, 1.0 - exp(-dt * 2.2))
	spin += (spin_v + auto) * dt
	table.rotation.y = spin
	var car: Car = main.car; car.hd = spin
	var c = POS + Vector3(0, 0.5, 0)
	cam.position = POS + Vector3(sin(orbit) * 6.1, 1.3, cos(orbit) * 6.1); cam.look_at(c)
	var panel = main.menu.shade.size.x if main.menu and main.menu.shade else 470.0
	cam.h_offset = lerpf(cam.h_offset, -1.35 - maxf(0.0, panel - 470.0) * 0.0068, 1.0 - exp(-dt * 6.0))          # the car stays clear of the wider pages
	(env.sky.sky_material as ShaderMaterial).set_shader_parameter("turn", 0.0)

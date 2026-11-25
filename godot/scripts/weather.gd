extends Node3D
class_name Weather
# Weather: CLEAR, RAIN, STORM (start screen button, kept in user://settings.cfg; WEATHER env for tests).
# Rain: streaks round the camera (shaders/rain.gdshader, one draw), an overcast sky, low soft light, wet glossy roads
# (global shader value wx_wet), thicker haze, less grip, and the sound of real rain (source/audio/weather.py).
# Storm: heavier rain, darker, and lightning: the sky flashes and a real thunder roll follows a moment later.
const NAMES = ["CLEAR", "RAIN", "STORM"]
const GRIP = [1.0, 0.86, 0.8]          # asphalt
const GRIP_OFF = [1.0, 0.9, 0.86]      # dirt, grass and sand get a little slippier too
const SUN_K = [1.0, 0.3, 0.2]
const AMB_K = [1.0, 0.85, 0.7]
const FOG_K = [1.0, 2.6, 3.6]
const WET = [0.0, 1.0, 1.0]
const CFG = "user://settings.cfg"
static var level := -1
var main: Node
var rain: MultiMeshInstance3D; var mat: ShaderMaterial
var bed_rain: AudioStreamPlayer; var bed_storm: AudioStreamPlayer; var thunder: AudioStreamPlayer
var thunders := []
var flash := 0.0; var next_bolt := 12.0; var pending := -1.0

static func get_level() -> int:
	if level < 0:
		var c = ConfigFile.new(); level = int(c.get_value("wx", "level", 0)) if c.load(CFG) == OK else 0
		if OS.get_environment("WEATHER") != "": level = NAMES.find(OS.get_environment("WEATHER"))
		level = clampi(level, 0, 2)
	return level
static func set_level(l: int):
	level = clampi(l, 0, 2)
	var c = ConfigFile.new(); c.load(CFG); c.set_value("wx", "level", level); c.save(CFG)

func build(m: Node):
	main = m
	var mm := MultiMesh.new(); mm.transform_format = MultiMesh.TRANSFORM_3D; mm.mesh = QuadMesh.new(); mm.instance_count = 3200
	for i in 3200: mm.set_instance_transform(i, Transform3D.IDENTITY)          # the shader places every streak itself
	mat = ShaderMaterial.new(); mat.shader = load("res://shaders/rain.gdshader")
	rain = MultiMeshInstance3D.new(); rain.multimesh = mm; rain.material_override = mat; rain.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	rain.custom_aabb = AABB(Vector3(-5000, -500, -5000), Vector3(10000, 1000, 10000)); add_child(rain)
	var b = AudioServer.get_bus_index("Ambience")
	bed_rain = _player("wx_rain", true); bed_storm = _player("wx_storm", true); thunder = _player("wx_thunder_0", false)
	for k in 4: thunders.append(load("res://assets/audio/wx_thunder_%d.ogg" % k))
	apply()

func _player(nm: String, loop: bool) -> AudioStreamPlayer:
	var st: AudioStreamOggVorbis = load("res://assets/audio/%s.ogg" % nm); st.loop = loop
	var p := AudioStreamPlayer.new(); p.stream = st; p.bus = "Ambience" if AudioServer.get_bus_index("Ambience") >= 0 else "Master"; add_child(p); return p

func apply():
	var l = get_level()
	rain.visible = l > 0
	mat.set_shader_parameter("amount", [0.0, 0.5, 1.0][l] * (0.6 if Gfx.get_level() == 0 else 1.0))
	mat.set_shader_parameter("speed", 15.0 if l == 2 else 12.0); mat.set_shader_parameter("wind", Vector3(3.0, 0, 1.6) if l == 2 else Vector3(1.0, 0, 0.5))
	RenderingServer.global_shader_parameter_set("wx_wet", WET[l])
	for p in [bed_rain, bed_storm]: p.stop()
	if l == 1: bed_rain.play(randf() * 60.0)
	if l == 2: bed_storm.play(randf() * 60.0); bed_rain.play(randf() * 60.0)
	next_bolt = randf_range(6.0, 14.0)

func _process(dt):
	var _p0 = Time.get_ticks_usec(); _process_body(dt); Prof.add("weather", Time.get_ticks_usec() - _p0)
func _process_body(dt):
	if main == null or main.cam == null: return
	var l = get_level()
	if l == 0: return
	mat.set_shader_parameter("cam", main.cam.global_position)
	mat.set_shader_parameter("bright", 1.1 if Tod.get_level() < 2 else 0.45)
	var tun = 1.0 - (main.eyes if "eyes" in main else 0.0)
	rain.visible = tun > 0.3
	var spd = main.car.speed
	bed_rain.volume_db = linear_to_db(maxf(0.001, tun * (0.9 if l == 1 else 0.5))) - 4.0
	bed_storm.volume_db = linear_to_db(maxf(0.001, tun * 0.9)) - 4.0
	if l == 2:          # lightning, then thunder a moment later (sound travels slower than light)
		next_bolt -= dt
		if next_bolt <= 0.0:
			next_bolt = randf_range(14.0, 32.0); flash = 0.35; pending = randf_range(0.6, 2.8)
		if pending > 0.0:
			pending -= dt
			if pending <= 0.0: thunder.stream = thunders[randi() % thunders.size()]; thunder.volume_db = -3.0 - 6.0 * randf(); thunder.play()
	if flash > 0.0:
		flash -= dt
		var k = (1.0 if fmod(flash, 0.12) > 0.05 else 0.25) * clampf(flash / 0.35, 0.0, 1.0)
		main.environment.ambient_light_energy += 2.5 * k; (main.environment.sky.sky_material as PanoramaSkyMaterial).energy_multiplier = Tod.sky_e() * (1.0 + 3.0 * k)
	elif main.environment.sky.sky_material.energy_multiplier != Tod.sky_e():
		(main.environment.sky.sky_material as PanoramaSkyMaterial).energy_multiplier = Tod.sky_e()

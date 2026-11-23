extends Node
class_name CarAudio
# Player car sound, built only from real recordings (Saba's CC0 uploads, cut into loops in source/audio/make.py):
# two engine loops crossfaded and pitched with the rpm, throttle on/off through a low-pass, tyre squeal from slip, a start-up.

const IDLE_RPM = 1425.0       # firing rate of the idle recording (47.5 Hz, four cylinders)
const MID_RPM = 2808.0        # the on-throttle blip (93.6 Hz)
var car: Car
var idle: AudioStreamPlayer; var mid: AudioStreamPlayer; var skid: AudioStreamPlayer; var start: AudioStreamPlayer
var lp: AudioEffectLowPassFilter
var on = false; var load_ = 0.0; var skid_v = 0.0; var fade = 0.0

static func loop_stream(path: String) -> AudioStream:
	var s = load(path)
	if s is AudioStreamOggVorbis: s.loop = true
	return s

func _ready():
	var bus = AudioServer.get_bus_index("Engine")
	if bus < 0:
		AudioServer.add_bus(); bus = AudioServer.bus_count - 1; AudioServer.set_bus_name(bus, "Engine"); AudioServer.set_bus_send(bus, "Master")
		lp = AudioEffectLowPassFilter.new(); lp.cutoff_hz = 2500; AudioServer.add_bus_effect(bus, lp)
	else: lp = AudioServer.get_bus_effect(bus, 0)
	if AudioServer.get_bus_effect_count(0) == 0:
		var lim = AudioEffectHardLimiter.new(); lim.ceiling_db = -1.0; AudioServer.add_bus_effect(0, lim)      # never clip on a loud crash or a horn over the engine
	idle = _player(loop_stream("res://assets/audio/eng_idle.ogg"), "Engine")
	mid = _player(loop_stream("res://assets/audio/eng_mid.ogg"), "Engine")
	skid = _player(loop_stream("res://assets/audio/skid_loop.ogg"), "Master")
	start = _player(load("res://assets/audio/eng_start.ogg"), "Master")
	for p in [idle, mid, skid]: p.volume_db = -80.0

func _player(s: AudioStream, bus: String) -> AudioStreamPlayer:
	var p = AudioStreamPlayer.new(); p.stream = s; p.bus = bus; add_child(p); return p

# key on: the starter catches, then the idle comes up under it
func ignition():
	on = true; fade = 0.0; start.volume_db = -3.0; start.play()
	for p in [idle, mid, skid]:
		if not p.playing: p.play(randf() * 0.5)

func _process(dt):
	if not car or not on: return
	fade = minf(1.0, fade + dt / 0.9)
	var rpm: float = car.rpm
	var gas: float = car.thr
	load_ = lerpf(load_, gas, clampf(dt * 8.0, 0.0, 1.0))
	# crossfade the two recordings over 1300-2600 rpm, each pitched to the engine speed
	var x = clampf((rpm - 1300.0) / 1300.0, 0.0, 1.0)
	idle.pitch_scale = clampf(rpm / IDLE_RPM, 0.55, 2.2); mid.pitch_scale = clampf(rpm / MID_RPM, 0.5, 3.0)
	var lvl = lerpf(-14.0, -5.0, load_) + 4.0 * clampf((rpm - 3000.0) / 5000.0, 0.0, 1.0)
	var fdb = linear_to_db(maxf(fade, 0.001))
	idle.volume_db = lvl + linear_to_db(maxf(cos(x * PI / 2), 0.001)) + fdb
	mid.volume_db = lvl + linear_to_db(maxf(sin(x * PI / 2), 0.001)) + fdb - 1.0
	lp.cutoff_hz = lerpf(900.0, 6500.0, load_ * 0.7 + clampf(rpm / 8000.0, 0.0, 1.0) * 0.3)    # off throttle the exhaust note goes dull
	# tyres: sideways slip and wheelspin on tarmac
	var slip = clampf((abs(car.beta) - 0.07) / 0.25, 0.0, 1.0) * clampf(car.speed / 8.0, 0.0, 1.0)
	if car.spin and car.speed < 25: slip = maxf(slip, 0.7)
	if car.surf != "road" or car.air: slip = 0.0
	skid_v = move_toward(skid_v, slip, dt * (6.0 if slip > skid_v else 3.5))
	skid.volume_db = linear_to_db(maxf(skid_v, 0.001)) - 4.0; skid.pitch_scale = 0.9 + skid_v * 0.15 + clampf(car.speed / 60.0, 0.0, 0.1)

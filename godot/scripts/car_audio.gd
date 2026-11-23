extends Node
class_name CarAudio
# Player car sound from real recordings only (Saba's CC0 uploads; tools in source/audio).
# Engine: eight steady loops of the recorded engine at fixed rpm. The two nearest the current rpm are crossfaded and
# nudged in pitch only a little, so the engine never "chipmunks" or warbles. Off throttle: quieter and duller.
# Tyres: a squeal loop driven by sideways slip and wheelspin on tarmac.

const RPMS = [900, 1400, 2100, 3000, 4100, 5400, 6900, 8400]
var car: Car
var layers = []; var skid: AudioStreamPlayer; var start: AudioStreamPlayer
var lp: AudioEffectLowPassFilter
var on = false; var load_ = 0.0; var skid_v = 0.0; var fade = 0.0; var arpm = 900.0; var arpm_v = 0.0

static func loop_stream(path: String) -> AudioStream:
	var s = load(path)
	if s is AudioStreamOggVorbis: s.loop = true
	return s

func _ready():
	var bus = AudioServer.get_bus_index("Engine")
	if bus < 0:
		AudioServer.add_bus(); bus = AudioServer.bus_count - 1; AudioServer.set_bus_name(bus, "Engine"); AudioServer.set_bus_send(bus, "Master")
		lp = AudioEffectLowPassFilter.new(); lp.cutoff_hz = 3000; AudioServer.add_bus_effect(bus, lp)
	else: lp = AudioServer.get_bus_effect(bus, 0)
	if AudioServer.get_bus_effect_count(0) == 0:
		var lim = AudioEffectHardLimiter.new(); lim.ceiling_db = -1.0; AudioServer.add_bus_effect(0, lim)
	for r in RPMS:
		var p = _player(loop_stream("res://assets/audio/eng_%d.ogg" % r), "Engine"); p.volume_db = -80.0; layers.append(p)
	skid = _player(loop_stream("res://assets/audio/skid_loop.ogg"), "Master"); skid.volume_db = -80.0
	start = _player(load("res://assets/audio/eng_start.ogg"), "Master")

func _player(s: AudioStream, bus: String) -> AudioStreamPlayer:
	var p = AudioStreamPlayer.new(); p.stream = s; p.bus = bus; add_child(p); return p

func ignition():
	on = true; fade = 0.0; arpm = 900.0; start.volume_db = -4.0; start.play()
	for p in layers: p.play(randf() * 2.0); p.stream_paused = true
	skid.play(); skid.stream_paused = true

func _process(dt):
	if not car or not on: return
	fade = minf(1.0, fade + dt / 1.2)
	# the physics rpm jitters with wheelspin and traction control: the ear gets a damped follower (about 0.1 s)
	var target = clampf(car.rpm, 800.0, 8600.0)
	var k = 90.0; arpm_v += (k * (target - arpm) - 2.0 * sqrt(k) * arpm_v) * dt; arpm += arpm_v * dt
	load_ = lerpf(load_, car.thr, clampf(dt * 5.0, 0.0, 1.0))
	var i = 0
	while i < RPMS.size() - 2 and arpm > RPMS[i + 1]: i += 1
	var a: float = RPMS[i]; var b: float = RPMS[i + 1]; var x = clampf((arpm - a) / (b - a), 0.0, 1.0)
	var lvl = lerpf(-15.0, -6.0, load_) + 3.0 * clampf((arpm - 3000.0) / 5000.0, 0.0, 1.0) + linear_to_db(maxf(fade, 0.001))
	for n in layers.size():
		var p: AudioStreamPlayer = layers[n]; var g = 0.0
		if n == i: g = cos(x * PI / 2)
		elif n == i + 1: g = sin(x * PI / 2)
		p.stream_paused = g < 0.003
		p.volume_db = lvl + linear_to_db(maxf(g, 0.001))
		p.pitch_scale = clampf(arpm / float(RPMS[n]), 0.6, 1.7)
	lp.cutoff_hz = lerpf(1100.0, 7000.0, clampf(load_ * 0.75 + arpm / 8400.0 * 0.25, 0.0, 1.0))
	var slip = clampf((abs(car.beta) - 0.09) / 0.25, 0.0, 1.0) * clampf((car.speed - 4.0) / 8.0, 0.0, 1.0)
	if car.spin and car.speed > 1.0 and car.speed < 22: slip = maxf(slip, 0.6)
	if car.surf != "road" or car.air: slip = 0.0
	skid_v = move_toward(skid_v, slip, dt * (5.0 if slip > skid_v else 3.0))
	skid.stream_paused = skid_v < 0.01
	skid.volume_db = linear_to_db(maxf(skid_v, 0.001)) - 5.0; skid.pitch_scale = 0.92 + skid_v * 0.12

extends Node
class_name CarAudio
# Car sound from real recordings only (Saba's CC0 uploads; build scripts in source/audio: engines.py, sfx.py).
# Every car has its own engine: eight loops made from that car's real recordings (an idle, and a full-throttle pull cut
# by rpm), so its tone at each rpm is what the recording had at that rpm. The two loops nearest the current rpm are
# crossfaded and nudged in pitch only a little. Off throttle the Vortex plays its own real overrun (lift-off) loops;
# the Calder goes quieter and duller. On top: wind and road noise with speed, tyre squeal on slides, crashes by impact speed.
# The same node drives the rivals' cars as 3D sound (positional = true).

const PROFILES = {
	vortex = { rpms = [1000, 2000, 3000, 4000, 5000, 6000, 7000, 8100], off = true, crank = 1.06, skid = 1.06, vol = 0.0 },
	calder = { rpms = [800, 1600, 2400, 3200, 4000, 4900, 5900, 7000], off = false, crank = 0.9, skid = 0.92, vol = 1.0 } }
const CRASH = ["crash_light", "crash_mid", "crash_heavy_a", "crash_heavy_b"]
var car: Car
var positional = false        # rivals: 3D players on their car
var id = ""; var P = {}
var on_l = []; var off_l = []; var skid; var wind; var crank; var crash = []
var lp: AudioEffectLowPassFilter
var on = false; var load_ = 0.0; var skid_v = 0.0; var fade = 0.0; var arpm = 900.0; var arpm_v = 0.0; var bus = "Master"

static func loop_stream(path: String) -> AudioStream:
	var s = load(path)
	if s is AudioStreamOggVorbis: s.loop = true
	return s

func _ready():
	if not positional:
		var b = AudioServer.get_bus_index("Engine")
		if b < 0:
			AudioServer.add_bus(); b = AudioServer.bus_count - 1; AudioServer.set_bus_name(b, "Engine"); AudioServer.set_bus_send(b, "Master")
			lp = AudioEffectLowPassFilter.new(); lp.cutoff_hz = 3000; AudioServer.add_bus_effect(b, lp)
		else: lp = AudioServer.get_bus_effect(b, 0)
		bus = "Engine"
		if AudioServer.get_bus_effect_count(0) == 0:
			var lim = AudioEffectHardLimiter.new(); lim.ceiling_db = -1.0; AudioServer.add_bus_effect(0, lim)
	skid = _player(loop_stream("res://assets/audio/skid_loop.ogg"), "Master"); skid.volume_db = -80.0
	if not positional:
		wind = _player(loop_stream("res://assets/audio/wind_road.ogg"), "Master"); wind.volume_db = -80.0
		crank = _player(load("res://assets/audio/eng_crank.ogg"), "Master")
	for c in CRASH: crash.append(_player(load("res://assets/audio/%s.ogg" % c), "Master"))      # rivals crash audibly too (as 3D sound)
	if car:
		car.crashed.connect(_on_crash)
		car.knocked.connect(func(o): _hit(0, -17.0 if o[2] < 0.35 else -11.0, 1.3 if o[2] < 0.35 else 1.0))                  # a bin, sign or post knocked over
		car.landed.connect(func(v): if v > 6.5: _hit(0 if v < 10.0 else 1, lerpf(-20.0, -6.0, clampf((v - 6.5) / 10.0, 0.0, 1.0)), 0.8))   # coming down from a jump
	_build()

func _player(s: AudioStream, b: String) -> Node:
	var p
	if positional:
		p = AudioStreamPlayer3D.new(); p.max_distance = 90.0; p.unit_size = 7.0; p.attenuation_model = AudioStreamPlayer3D.ATTENUATION_INVERSE_DISTANCE
		p.position = Vector3(0, 0.6, 0); car.add_child(p)
	else:
		p = AudioStreamPlayer.new(); p.bus = b; add_child(p)
	p.stream = s; return p

# the engine loops of the car being driven; rebuilt when the car changes
func _build():
	if not car: return
	id = car.car_id; P = PROFILES.get(id, PROFILES.vortex)
	for p in on_l + off_l:
		if p: p.queue_free()
	on_l = []; off_l = []
	for k in P.rpms.size():
		var p = _player(loop_stream("res://assets/audio/eng_%s_%d.ogg" % [id, k]), bus); p.volume_db = -80.0; on_l.append(p)
		if P.off and k >= 2:
			var q = _player(loop_stream("res://assets/audio/eng_%s_off_%d.ogg" % [id, k]), bus); q.volume_db = -80.0; off_l.append(q)
		else: off_l.append(null)
	if on:
		for p in on_l + off_l:
			if p: p.play(randf() * 3.0); p.stream_paused = true

func ignition():
	on = true; fade = -0.95 if crank else 0.0; arpm = car.V.idle if car else 900.0      # the idle comes in as the starter catches
	if crank: crank.pitch_scale = P.get("crank", 1.0); crank.volume_db = -3.0; crank.play()
	for p in on_l + off_l:
		if p: p.play(randf() * 3.0); p.stream_paused = true
	skid.play(); skid.stream_paused = true
	if wind: wind.play(randf() * 5.0); wind.stream_paused = true

func _on_crash():
	var v: float = car.impact
	_hit(0 if v < 9.0 else (1 if v < 16.0 else 2 + randi() % 2), lerpf(-18.0, 0.0, clampf((v - 2.5) / 19.0, 0.0, 1.0)))

func _hit(k: int, db: float, pitch := 1.0):
	if crash.is_empty(): return
	var p = crash[k]; p.pitch_scale = randf_range(0.93, 1.05) * pitch; p.volume_db = db + (6.0 if positional else 0.0); p.play()

func _process(dt):
	if not car: return
	if car.car_id != id: _build(); ignition()
	if not on: return
	fade = minf(1.0, fade + dt / (0.5 if crank else 0.3))
	# the physics rpm jitters with wheelspin and traction control: the ear gets a damped follower (about 0.1 s)
	var target = clampf(car.rpm, 700.0, 8600.0)
	var kk = 90.0; arpm_v += (kk * (target - arpm) - 2.0 * sqrt(kk) * arpm_v) * dt; arpm += arpm_v * dt
	load_ = lerpf(load_, car.thr, clampf(dt * 5.0, 0.0, 1.0))
	var R: Array = P.rpms; var i = 0
	while i < R.size() - 2 and arpm > R[i + 1]: i += 1
	var a: float = R[i]; var b: float = R[i + 1]; var x = clampf((arpm - a) / (b - a), 0.0, 1.0)
	var top = clampf((arpm - 2500.0) / 5000.0, 0.0, 1.0)
	var base = (lerpf(-14.0, -5.0, load_) + 3.0 * top + P.vol) + linear_to_db(maxf(fade, 0.001)) + (4.0 if positional else 0.0)
	var offmix = clampf((0.35 - load_) / 0.3, 0.0, 1.0) if P.off else 0.0           # lifting off: the car's real overrun takes over
	for n in on_l.size():
		var g = 0.0
		if n == i: g = cos(x * PI / 2)
		elif n == i + 1: g = sin(x * PI / 2)
		var pitch = clampf(arpm / float(R[n]), 0.7, 1.45)
		var po = off_l[n]; var go = g * offmix if po else 0.0; var gn = g * (1.0 - offmix) if po else g
		var p = on_l[n]; p.stream_paused = gn < 0.003; p.volume_db = base + linear_to_db(maxf(gn, 0.001)); p.pitch_scale = pitch
		if po: po.stream_paused = go < 0.003; po.volume_db = base - 2.0 + linear_to_db(maxf(go, 0.001)); po.pitch_scale = pitch
	if lp: lp.cutoff_hz = lerpf(1600.0 if not P.off else 2600.0, 9000.0, clampf(load_ * 0.75 + arpm / 8400.0 * 0.25, 0.0, 1.0))
	# tyres: squeal with sideways slip and wheelspin, on tarmac only
	var slip = clampf((abs(car.beta) - 0.09) / 0.25, 0.0, 1.0) * clampf((car.speed - 4.0) / 8.0, 0.0, 1.0)
	if car.spin and car.speed > 1.0 and car.speed < 22: slip = maxf(slip, 0.6)
	if car.surf != "road" or car.air: slip = 0.0
	skid_v = move_toward(skid_v, slip, dt * (5.0 if slip > skid_v else 3.0))
	skid.stream_paused = skid_v < 0.01
	skid.volume_db = linear_to_db(maxf(skid_v, 0.001)) - (5.0 if not positional else 0.0); skid.pitch_scale = (0.92 + skid_v * 0.12) * P.skid
	# wind and road roar: from about 30 km/h, louder and brighter with speed (the recording is at 80 km/h)
	if wind:
		var s = car.speed * 3.6; var wv = clampf((s - 25.0) / 140.0, 0.0, 1.0)
		wind.stream_paused = wv < 0.01; wind.volume_db = lerpf(-30.0, -7.0, wv) + linear_to_db(maxf(fade, 0.001)); wind.pitch_scale = clampf(0.75 + s / 80.0 * 0.25, 0.75, 1.35)

func debug() -> String:           # test: which loops are playing, at what level and pitch
	var o = "rpm %4d load %.2f |" % [arpm, load_]
	for n in on_l.size():
		if not on_l[n].stream_paused: o += " on%d %+.0fdB x%.2f" % [n, on_l[n].volume_db, on_l[n].pitch_scale]
		if off_l[n] and not off_l[n].stream_paused: o += " off%d %+.0fdB" % [n, off_l[n].volume_db]
	if wind and not wind.stream_paused: o += " | wind %+.0fdB" % wind.volume_db
	if not skid.stream_paused: o += " | skid %+.0fdB" % skid.volume_db
	for p in crash:
		if p.playing: o += " | CRASH %s %+.0fdB" % [p.stream.resource_path.get_file(), p.volume_db]
	return o

extends Node
class_name Ambience
# The island's own sound round the car, from real field recordings (source/audio/ambience.py, CREDITS.md): sea waves near
# the shore, running water by the rivers and lakes, birds in the countryside and the forest by day, crickets at dusk and
# night, wind in the trees in the forest and the mountains, open wind in the desert and up high. Six looping beds, each
# faded to where the car is (assets/island/ambience.bin: distance to the sea and to water), the region it is in and the
# time of day; all of it ducks under the engine as the car speeds up and goes quiet in tunnels.
const BEDS = ["waves", "stream", "birds", "crickets", "trees", "wind"]
var players := {}
var lv := {}                 # current level 0..1 per bed
var main: Node
var map := PackedByteArray(); var mw := 0; var mh := 0
var regions := []
var _t := 0.0
var want := {}

func build(m: Node, world: Dictionary):
	main = m; regions = world["regions"]
	var b = AudioServer.get_bus_index("Ambience")
	if b < 0: AudioServer.add_bus(); b = AudioServer.bus_count - 1; AudioServer.set_bus_name(b, "Ambience"); AudioServer.set_bus_send(b, "Master")
	for nm in BEDS:
		var st: AudioStreamOggVorbis = load("res://assets/audio/amb_%s.ogg" % nm); st.loop = true
		var p := AudioStreamPlayer.new(); p.stream = st; p.bus = "Ambience"; p.volume_db = -80.0; add_child(p)
		players[nm] = p; lv[nm] = 0.0; want[nm] = 0.0
	var f = FileAccess.open("res://assets/island/ambience.bin", FileAccess.READ)
	if f: mw = f.get_16(); mh = f.get_16(); map = f.get_buffer(mw * mh * 2)

func _dist(p: Vector3) -> Vector2:          # metres to the sea, to running water
	if mw == 0: return Vector2(999, 999)
	var c = clampi(int(round((p.x + 2400.0) / 12.0)), 0, mw - 1); var r = clampi(int(round((-p.z + 1680.0) / 12.0)), 0, mh - 1)
	var i = (r * mw + c) * 2
	return Vector2(map[i] * 4.0, map[i + 1] * 4.0)

func _region(p: Vector3) -> Dictionary:          # how much the car is in each region (1 at the centre, fading out past its edge)
	var out = {}
	for g in regions:
		var d = sqrt(pow((p.x - g["x"]) / g["rx"], 2) + pow((p.z - g["z"]) / g["rz"], 2))
		out[g["name"]] = clampf(1.4 - d, 0.0, 1.0)
	return out

func _process(dt):
	if main == null or main.car == null: return
	_t -= dt
	if _t <= 0.0:
		_t = 0.25
		var p = Vector3(main.car.px, main.car.py, main.car.pz); var d = _dist(p); var g = _region(p)
		var night = Tod.night(); var day = 1.0 - night
		var city = g.get("City", 0.0); var forest = g.get("Forest Trails", 0.0); var desert = g.get("Desert", 0.0)
		var mount = g.get("Mountain Roads", 0.0); var high = clampf((p.y - 55.0) / 50.0, 0.0, 1.0)
		var green = maxf(g.get("Countryside", 0.0), maxf(g.get("Coastal Highway", 0.0), g.get("Racing Circuit", 0.0) * 0.5))
		want.waves = clampf(1.0 - (d.x - 40.0) / 420.0, 0.0, 1.0) * (1.0 - 0.7 * city)          # surf carries a long way inland
		want.stream = clampf(1.0 - (d.y - 10.0) / 110.0, 0.0, 1.0) * 0.8
		want.birds = day * clampf(maxf(forest, green * 0.8) + 0.25 * (1.0 - city) + 0.12, 0.0, 1.0) * (1.0 - 0.7 * desert) * (1.0 - 0.6 * high) * 0.8
		want.crickets = clampf(night * 1.2 - 0.15, 0.0, 1.0) * (1.0 - 0.75 * city) * (1.0 - 0.8 * high) * (1.0 - 0.5 * desert)
		want.trees = clampf(maxf(forest * 0.75, mount * 0.6) + high * 0.4, 0.0, 1.0) * (1.0 - 0.8 * desert)
		want.wind = clampf(desert * 0.9 + high * 0.8 + 0.15 * (1.0 - city), 0.0, 1.0)
		if Weather.get_level() > 0:          # rain: the birds and crickets go quiet, the storm wind picks up
			want.birds *= 0.1; want.crickets *= 0.3; want.wind = minf(1.0, want.wind + 0.25 * (Weather.get_level() - 1))
	var spd = main.car.speed; var duck = lerpf(1.0, 0.35, clampf((spd - 8.0) / 40.0, 0.0, 1.0))      # the engine and the wind of speed take over
	var tun = 1.0 - (main.eyes if "eyes" in main else 0.0)
	var on = 0.0 if main.menu_on and false else 1.0
	for nm in BEDS:
		lv[nm] = move_toward(lv[nm], want[nm], dt * 0.4)
		var a = lv[nm] * duck * tun * on
		var pl: AudioStreamPlayer = players[nm]
		if a < 0.01:
			if pl.playing: pl.stop()
			continue
		if not pl.playing: pl.play(randf() * pl.stream.get_length() * 0.9)
		pl.volume_db = linear_to_db(a) - 6.0

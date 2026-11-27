extends Node3D
class_name FreeRoam
# Things to do between races: speed traps and drift zones all over the island, and a daily challenge.
#  - speed trap: drive past the sign; the speed is measured and your best kept; a new best pays (km/h x 2 credits)
#  - drift zone: from the start board to the end board, every drift point counts; a new best pays (score / 15)
#  - daily challenge (Progress.daily): one task picked from the date, paid once (DAILY_PAY)
# Signs are Label3D boards on poles; the minimap shows them. Nothing here runs during a race or in the menu.
const TRAPS = [["Ring", 300], ["Ring", 900], ["Ring", 1500], ["West Avenue", 130], ["East Avenue", 140], ["Dune Road", 64], ["Skyline Road", 150], ["Beach Flyover", 40]]
const ZONES = [["Summit Pass", 60, 160, "Summit hairpins"], ["Serpentine", 40, 150, "Serpentine"], ["Eagle Descent", 15, 100, "Eagle's road"],
	["Skyline Road", 200, 290, "Skyline ridge"], ["Canyon Road", 10, 95, "Canyon"], ["Lake Trail", 120, 220, "Lake trail (dirt)"]]
const DAILY_PAY = 3000
var main
var traps := []          # [position, forward, name, was_near]
var zones := []          # [start pos, start fwd, end pos, points (PackedVector3Array), name]
var active := -1; var zone_start := 0.0; var zone_t := 0.0
var _t := 0.0

func _init(m): main = m; name = "FreeRoam"; physics_interpolation_mode = Node.PHYSICS_INTERPOLATION_MODE_OFF

func build():
	for k in TRAPS.size():
		var a = _pt(TRAPS[k][0], TRAPS[k][1]); traps.append([a[0], a[1], "%s speed trap" % TRAPS[k][0], false])
		_sign(a[0], a[1], "SPEED TRAP", Color(1.0, 0.62, 0.08), 6.0)
	for k in ZONES.size():
		var z = ZONES[k]; var p = main.roads[z[0]]; var pts := PackedVector3Array()
		for i in range(z[1], z[2] + 1): pts.append(Vector3(p[i * 3], p[i * 3 + 1], p[i * 3 + 2]))
		var s = _pt(z[0], z[1]); var e = _pt(z[0], z[2])
		zones.append([s[0], s[1], e[0], pts, z[3]])
		_sign(s[0], s[1], "DRIFT ZONE", Color(0.35, 0.85, 1.0), 7.0); _sign(e[0], e[1], "ZONE END", Color(0.35, 0.85, 1.0), 7.0)

func _pt(road: String, i: int) -> Array:
	var p = main.roads[road]; var n = p.size() / 3; i = clampi(i, 0, n - 2)
	var a = Vector3(p[i * 3], p[i * 3 + 1], p[i * 3 + 2]); var b = Vector3(p[i * 3 + 3], p[i * 3 + 4], p[i * 3 + 5])
	return [a, (b - a).normalized()]

# a board on a pole beside the road (right-hand verge), lit at night like the signs in town
func _sign(p: Vector3, fwd: Vector3, text: String, col: Color, side: float):
	var right = Vector3(-fwd.z, 0, fwd.x).normalized(); var base = p + right * side
	var pole := MeshInstance3D.new(); var cm := CylinderMesh.new(); cm.top_radius = 0.08; cm.bottom_radius = 0.1; cm.height = 4.2; pole.mesh = cm
	var pm := StandardMaterial3D.new(); pm.albedo_color = Color(0.35, 0.36, 0.38); pm.metallic = 0.7; pm.roughness = 0.4; pole.material_override = pm
	pole.position = base + Vector3(0, 2.1, 0); pole.visibility_range_end = 400.0; add_child(pole)
	var l := Label3D.new(); l.text = text; l.font_size = 96; l.pixel_size = 0.012; l.modulate = col; l.outline_size = 18; l.outline_modulate = Color(0, 0, 0, 0.8)
	l.billboard = BaseMaterial3D.BILLBOARD_FIXED_Y; l.position = base + Vector3(0, 4.9, 0); l.visibility_range_end = 400.0; l.no_depth_test = false; add_child(l)

func _process(dt):
	if main.race or main.menu_on or main.car == null: return
	_t -= dt
	var c: Car = main.car; var p = Vector3(c.px, c.py, c.pz)
	for t in traps:          # passing a trap: measured as you go by it
		var near = p.distance_to(t[0]) < 11.0
		if near and not t[3]: _trap(t, c)
		t[3] = near
	if active < 0:
		if _t > 0: return
		_t = 0.15
		for k in zones.size():
			var z = zones[k]
			if p.distance_to(z[0]) < 12.0 and Vector2(c.vx, c.vz).dot(Vector2(z[1].x, z[1].z)) > 3.0:
				active = k; zone_start = main.drift.total + main.drift.cur; zone_t = 0.0
				var b = best("zone%d" % k); main.toast("DRIFT ZONE · %s%s" % [z[4], ("   ·   best %s" % Menu._n(b)) if b > 0 else ""], 3.0)
	else:
		var z = zones[active]; zone_t += dt
		var off = 1e9
		for q in z[3]: off = minf(off, Vector2(q.x - p.x, q.z - p.z).length_squared())
		if p.distance_to(z[2]) < 14.0: _zone_end(true)
		elif off > 45.0 * 45.0 or zone_t > 240.0: _zone_end(false)

func _trap(t: Array, c: Car):
	var kmh = int(c.speed * 3.6)
	if kmh < 30: return
	var key = "trap%d" % traps.find(t); var b = best(key); var msg = "SPEED TRAP · %d km/h" % kmh
	if kmh > b:
		set_best(key, kmh); var pay = kmh * 2; Progress.earn(pay); msg += "   ·   NEW BEST  +%s credits" % Menu._n(pay)
	elif b > 0: msg += "   ·   best %d" % b
	main.toast(msg, 3.0); daily_check("trap", traps.find(t), kmh)

func _zone_end(finished: bool):
	var k = active; active = -1
	if not finished: main.toast("DRIFT ZONE · left the road", 2.0); return
	main.drift.bank(); var score = int(main.drift.total - zone_start)
	var key = "zone%d" % k; var b = best(key); var msg = "%s · %s points" % [zones[k][4].to_upper(), Menu._n(score)]
	if score > b and score > 0:
		set_best(key, score); var pay = int(score / 15.0); Progress.earn(pay); msg += "   ·   NEW BEST  +%s credits" % Menu._n(pay)
	elif b > 0: msg += "   ·   best %s" % Menu._n(b)
	main.toast(msg, 3.5); daily_check("zone", k, score)

static func best(key: String) -> int: return int(Progress.records.get(key, 0))
static func set_best(key: String, v: int): Progress.records[key] = v; Progress.save()

# ---------------------------------------------------------------- daily challenge
static func today() -> int:
	var d = Time.get_date_dict_from_system(); return d.year * 10000 + d.month * 100 + d.day
static func daily() -> Dictionary:          # { kind, k, target, text }
	var seed_ = today(); var r = RandomNumberGenerator.new(); r.seed = seed_
	match r.randi() % 3:
		0:
			var k = r.randi() % TRAPS.size(); var tgt = [200, 220, 240][r.randi() % 3]
			return { kind = "trap", k = k, target = tgt, text = "Hit %d km/h at the %s speed trap" % [tgt, TRAPS[k][0]] }
		1:
			var k = r.randi() % ZONES.size(); var tgt = [3000, 5000, 8000][r.randi() % 3]
			return { kind = "zone", k = k, target = tgt, text = "Score %s in the %s drift zone" % [Menu._n(tgt), ZONES[k][3]] }
		_:
			var open = Race.ORDER.filter(func(rid): return Progress.is_open(rid) and not Race.RACES[rid].has("mode"))
			var rid = open[r.randi() % open.size()]
			return { kind = "race", k = rid, target = 1, text = "Win %s" % Race.RACES[rid].name }
static func daily_done() -> bool: return int(Progress.records.get("daily_done", 0)) == today()
func daily_check(kind, k, value):
	if daily_done(): return
	var d = daily()
	if d.kind == kind and d.k == k and value >= d.target:
		Progress.records["daily_done"] = today(); Progress.earn(DAILY_PAY)
		main.toast("DAILY CHALLENGE DONE  +%s credits" % Menu._n(DAILY_PAY), 4.0)

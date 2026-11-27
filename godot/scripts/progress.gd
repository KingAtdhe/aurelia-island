extends RefCounted
class_name Progress
# Career: credits, cars owned, upgrades and paint per car, races unlocked, landmarks found. Saved to user://progress.cfg.
# Same economy as the web game (index.html PROG / UPG / PAINTS), with race prize money in place of drift points.

static var SAVE = "user://progress.cfg" if OS.get_environment("CAREERSAVE") == "" else OS.get_environment("CAREERSAVE")
const PRICE = { vortex = 0, calder = 25000 }
const UPG = [
	{ k = "eng", name = "Engine", d = ["Stock", "Stage 1  +8% torque", "Stage 2  +16% torque", "Stage 3  +25% torque"], cost = [4000, 9000, 18000] },
	{ k = "tyre", name = "Tyres", d = ["Street", "Sport  +4% grip", "Semi-slick  +8% grip"], cost = [5000, 12000] },
	{ k = "kit", name = "Drift kit", d = ["Stock lock", "Angle kit", "Pro angle kit"], cost = [6000, 14000] },
	{ k = "wt", name = "Weight", d = ["Stock", "Light  -50 kg", "Stripped  -100 kg"], cost = [5000, 11000] } ]
const PAINTS = [["Factory", Color(0, 0, 0, 0)], ["Pearl white", Color("e8e8e4")], ["Midnight", Color("0f1420")], ["Racing green", Color("0b4a2a")], ["Sunset orange", Color("e2560c")],
	["Electric blue", Color("0a4fd6")], ["Gold", Color("c89a2a")], ["Graphite", Color("3a3d42")], ["Violet", Color("5a1a8a")]]
const PAINT_COST = 1500
const PRIZE = [1.0, 0.6, 0.35, 0.12]          # share of a race's purse by finishing place
const LANDMARK = 250

static var cr := 0
static var car := "vortex"
static var cars := ["vortex"]
static var up := {}
static var unlocked := {}
static var found := {}
static var records := {}          # free roam: best speed per trap, best score per drift zone, the daily challenge done
static var _loaded := false

static func load_save():
	if _loaded: return
	_loaded = true
	var cf = ConfigFile.new(); cf.load(SAVE)
	cr = cf.get_value("p", "cr", 5000)          # a new career starts with enough for a first upgrade
	car = cf.get_value("p", "car", "vortex"); cars = cf.get_value("p", "cars", ["vortex"])
	up = cf.get_value("p", "up", {}); unlocked = cf.get_value("p", "unlocked", {}); found = cf.get_value("p", "found", {}); records = cf.get_value("p", "records", {})

static func save():
	var cf = ConfigFile.new(); cf.load(SAVE)
	for k in ["cr", "car", "cars", "up", "unlocked", "found", "records"]: cf.set_value("p", k, _v(k))
	cf.save(SAVE)
static func _v(k: String):
	match k:
		"cr": return cr
		"car": return car
		"cars": return cars
		"up": return up
		"unlocked": return unlocked
		"found": return found
		"records": return records
	return null

static func U(id: String) -> Dictionary:
	if not up.has(id): up[id] = { eng = 0, tyre = 0, kit = 0, wt = 0, paint = 0, owned = [0] }
	return up[id]

static func spend(n: int) -> bool:
	if cr < n: return false
	cr -= n; save(); return true

static func earn(n: int):
	if n <= 0: return
	cr += n; save()

# a race's purse grows with its length and difficulty; the first three races are always open, each next one opens with a podium in the one before
static func purse(rid: String) -> int:
	return int(round((1200.0 + 900.0 * Race.ORDER.find(rid)) * (2.0 if rid == "gp" else 1.0) / 100.0)) * 100
static func is_open(rid: String) -> bool:
	var k = Race.ORDER.find(rid)
	if k < 3 or unlocked.has(rid): return true
	var pb = Race.best(Race.RACES[rid].get("after", Race.ORDER[k - 1]))[1]          # a podium from before the career existed counts too
	return pb >= 1 and pb <= 3
static func race_done(rid: String, pos: int) -> Array:          # [credits won, name of a race this unlocked or ""]
	var won = int(round(purse(rid) * PRIZE[pos - 1] / 50.0)) * 50; earn(won)
	var k = Race.ORDER.find(rid); var opened = ""
	if pos <= 3:
		for nx in Race.ORDER:          # the next race in the career, or an event that opens after this one
			var by = Race.RACES[nx].get("after", "" if Race.ORDER.find(nx) == 0 else Race.ORDER[Race.ORDER.find(nx) - 1])
			if by == rid and not unlocked.has(nx) and opened == "":
				var was_open = is_open(nx); unlocked[nx] = true; save()
				if not was_open: opened = Race.RACES[nx].name
	return [won, opened]

# vehicle numbers for a car with its upgrades (applied on top of the car's base set)
static func tune(id: String, V: Dictionary):
	var u = U(id); var base = Car.CARS[id].veh
	V.tqPeak = base.tqPeak * [1.0, 1.08, 1.16, 1.25][u.eng]
	V.mu = 1.15 * [1.0, 1.04, 1.08][u.tyre]
	V.lockD = [0.87, 0.96, 1.05][u.kit]
	V.m = base.m - [0.0, 50.0, 100.0][u.wt]; V.Iz = base.Iz * V.m / base.m

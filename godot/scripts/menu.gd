extends CanvasLayer
class_name Menu
# start screen and garage: pick a car, drive; the car turns slowly on the road behind the panel
signal drive(car_id)
signal race(race_id)
signal travel(region)
const REGIONS = [["Coastal Highway", -1300, 780], ["City", 0, 20], ["Harbour", -350, 700], ["Mountain Roads", -150, -900], ["Forest Trails", -1350, -420],
	["Desert", 1380, -620], ["Racing Circuit", 1260, 355], ["Countryside", 700, 900], ["Heliport", 1715, 1010]]
var ids = ["vortex", "calder"]; var idx = 0
var title: Label; var name_lbl: Label; var blurb: Label; var stats: Label; var root: Control
var car_ui = []; var race_ui = []; var travel_ui = []; var shade: ColorRect

func _ready():
	root = Control.new(); root.set_anchors_preset(Control.PRESET_FULL_RECT); add_child(root)
	shade = ColorRect.new(); shade.color = Color(0.04, 0.05, 0.07, 0.55); shade.set_anchors_preset(Control.PRESET_LEFT_WIDE); shade.custom_minimum_size = Vector2(460, 0); shade.size = Vector2(460, 2000); root.add_child(shade)
	title = _lbl("AURELIA ISLAND", 44, Vector2(40, 40)); _lbl("The whole island", 20, Vector2(42, 98)).modulate = Color(1, 1, 1, 0.6)
	name_lbl = _lbl("", 36, Vector2(40, 180)); blurb = _lbl("", 18, Vector2(40, 232)); blurb.autowrap_mode = TextServer.AUTOWRAP_WORD; blurb.size = Vector2(380, 80)
	stats = _lbl("", 18, Vector2(40, 310)); stats.modulate = Color(1, 1, 1, 0.75)
	car_ui = [name_lbl, blurb, stats]
	car_ui.append(_btn("◀", Vector2(40, 400), Vector2(80, 64), func(): pick(-1)))
	car_ui.append(_btn("▶", Vector2(130, 400), Vector2(80, 64), func(): pick(1)))
	car_ui.append(_btn("FREE ROAM", Vector2(40, 480), Vector2(300, 72), func(): emit_signal("drive", ids[idx])))
	car_ui.append(_btn("RACES", Vector2(40, 564), Vector2(146, 64), func(): show_races(true)))
	car_ui.append(_btn("TRAVEL", Vector2(194, 564), Vector2(146, 64), func(): show_travel(true)))
	for k in REGIONS.size():
		var rg = REGIONS[k]
		var bt = _btn(rg[0], Vector2(40 + (k / 5) * 400, 150 + (k % 5) * 90), Vector2(385, 80), func(): emit_signal("travel", rg)); bt.add_theme_font_size_override("font_size", 24); travel_ui.append(bt)
	travel_ui.append(_btn("BACK", Vector2(440, 150 + 4 * 90), Vector2(180, 80), func(): show_travel(false)))
	# race list: three sprints with the best time and place so far; the race uses the car picked above
	var y = 150; var k = 0
	for rid in Race.ORDER:
		var R = Race.RACES[rid]; var b = Race.best(rid)
		var bt = _btn("", Vector2(40 + (k / 4) * 400, y + (k % 4) * 104), Vector2(385, 94), func(): emit_signal("race", rid)); bt.alignment = HORIZONTAL_ALIGNMENT_LEFT
		bt.text = "  %s\n  %s" % [R.name, ("best %s · %s" % [Race.fmt(b[0]), ["1st", "2nd", "3rd", "4th"][b[1] - 1]]) if b[0] > 0 else "not raced yet"]
		bt.add_theme_font_size_override("font_size", 22); race_ui.append(bt); k += 1
	race_ui.append(_btn("BACK", Vector2(40, y + 4 * 104 + 6), Vector2(180, 64), func(): show_races(false)))
	show_races(false)
	pick(0)

func show_races(on: bool):
	for c in car_ui: c.visible = not on
	for c in travel_ui: c.visible = false
	for c in race_ui: c.visible = on
	shade.size.x = 880 if on else 460

func show_travel(on: bool):
	for c in car_ui: c.visible = not on
	for c in race_ui: c.visible = false
	for c in travel_ui: c.visible = on
	shade.size.x = 880 if on else 460

func _lbl(t: String, sz: int, pos: Vector2) -> Label:
	var l = Label.new(); l.text = t; l.add_theme_font_size_override("font_size", sz); l.position = pos; root.add_child(l); return l
func _btn(t: String, pos: Vector2, sz: Vector2, cb: Callable) -> Button:
	var b = Button.new(); b.text = t; b.position = pos; b.size = sz; b.add_theme_font_size_override("font_size", 30); b.pressed.connect(cb); root.add_child(b); return b

func pick(d: int):
	idx = (idx + d + ids.size()) % ids.size(); var C = Car.CARS[ids[idx]]
	name_lbl.text = C.name; blurb.text = C.blurb
	var v = C.veh; stats.text = "%d kg · %d Nm · redline %d rpm\n%d gears · %s" % [v.m, v.tqPeak, v.red, v.gears.size(), "mid-engine" if ids[idx] == "vortex" else "front-engine V8"]
	if d != 0: emit_signal("drive", "preview:" + ids[idx])

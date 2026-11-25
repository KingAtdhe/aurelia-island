extends CanvasLayer
class_name Menu
# Start screen: pick a car (buy it when it is not yours yet), drive, race, travel, and the garage for upgrades and paint.
# The car turns slowly on the road behind the panel.
signal drive(car_id)
signal race(race_id)
signal travel(region)
signal changed          # upgrades or paint bought: the car on show is rebuilt
signal gfx              # graphics level changed
signal tod              # time of day changed
const REGIONS = [["Coastal Highway", -1300, 780], ["City", 0, 20], ["Harbour", -350, 700], ["Mountain Roads", -150, -900], ["Forest Trails", -1350, -420],
	["Desert", 1380, -620], ["Racing Circuit", 1260, 355], ["Countryside", 700, 900], ["Heliport", 1715, 1010]]
var ids = ["vortex", "calder"]; var idx = 0
var title: Label; var name_lbl: Label; var blurb: Label; var stats: Label; var credits: Label; var note: Label; var root: Control
var go_btn: Button; var garage_btn: Button; var gfx_btn: Button; var tod_btn: Button
var car_ui = []; var race_ui = []; var travel_ui = []; var garage_ui = []; var shade: ColorRect

func _ready():
	Progress.load_save(); idx = maxi(0, ids.find(Progress.car))
	root = Control.new(); root.set_anchors_preset(Control.PRESET_FULL_RECT); add_child(root)
	shade = ColorRect.new(); shade.color = Color(0.04, 0.05, 0.07, 0.6); shade.size = Vector2(460, 2000); root.add_child(shade)
	title = _lbl("AURELIA ISLAND", 44, Vector2(40, 34))
	credits = _lbl("", 22, Vector2(42, 92)); credits.add_theme_color_override("font_color", Hud.ACCENT)
	note = _lbl("", 20, Vector2(40, 670)); note.modulate = Color(1, 0.85, 0.6)
	name_lbl = _lbl("", 36, Vector2(40, 150)); blurb = _lbl("", 18, Vector2(40, 200)); blurb.autowrap_mode = TextServer.AUTOWRAP_WORD; blurb.size = Vector2(380, 80)
	stats = _lbl("", 18, Vector2(40, 278)); stats.modulate = Color(1, 1, 1, 0.75)
	car_ui = [name_lbl, blurb, stats]
	car_ui.append(_btn("◀", Vector2(40, 368), Vector2(80, 64), func(): pick(-1)))
	car_ui.append(_btn("▶", Vector2(130, 368), Vector2(80, 64), func(): pick(1)))
	go_btn = _btn("FREE ROAM", Vector2(40, 446), Vector2(300, 68), _go); car_ui.append(go_btn)
	car_ui.append(_btn("RACES", Vector2(40, 524), Vector2(146, 60), func(): show_page("races")))
	car_ui.append(_btn("TRAVEL", Vector2(194, 524), Vector2(146, 60), func(): show_page("travel")))
	garage_btn = _btn("GARAGE", Vector2(40, 594), Vector2(146, 60), func(): show_page("garage")); car_ui.append(garage_btn)
	gfx_btn = _btn("", Vector2(194, 594), Vector2(146, 60), _gfx); gfx_btn.add_theme_font_size_override("font_size", 20); car_ui.append(gfx_btn); _gfx_text()
	tod_btn = _btn("", Vector2(348, 594), Vector2(100, 60), _tod); tod_btn.add_theme_font_size_override("font_size", 18); car_ui.append(tod_btn); _tod_text()
	for k in REGIONS.size():
		var rg = REGIONS[k]
		var bt = _btn(rg[0], Vector2(40 + (k / 5) * 400, 150 + (k % 5) * 90), Vector2(385, 80), func(): if _owned(): emit_signal("travel", rg)); bt.add_theme_font_size_override("font_size", 24); travel_ui.append(bt)
	travel_ui.append(_btn("BACK", Vector2(440, 150 + 4 * 90), Vector2(180, 80), func(): show_page("")))
	_build_races()
	show_page("")
	pick(0)

func _gfx():          # graphics LOW -> MEDIUM -> HIGH -> LOW
	Gfx.set_level((Gfx.get_level() + 1) % 3); _gfx_text(); emit_signal("gfx")
func _tod():          # time of day DAY -> SUNSET -> NIGHT -> DAY
	Tod.set_level((Tod.get_level() + 1) % 3); _tod_text(); emit_signal("tod")
func _tod_text(): tod_btn.text = "TIME\n" + Tod.NAMES[Tod.get_level()]
func _gfx_text(): gfx_btn.text = "GRAPHICS\n" + Gfx.NAMES[Gfx.get_level()]

# ---------------------------------------------------------------- pages
func show_page(p: String):
	if p == "garage" and not _owned(): return
	for c in car_ui: c.visible = p == ""
	for c in race_ui: c.visible = p == "races"
	for c in travel_ui: c.visible = p == "travel"
	for c in garage_ui: c.visible = p == "garage"
	if p == "garage": _build_garage()
	if p == "races": _build_races(); for c in race_ui: c.visible = true
	shade.size.x = 460 if p == "" else (620 if p == "garage" else (1240 if p == "races" else 880))
	_refresh()

func _refresh():
	credits.text = "%s credits" % _n(Progress.cr)

func _build_races():
	for c in race_ui: c.queue_free()
	race_ui = []
	var y = 140; var k = 0
	for rid in Race.ORDER:
		var R = Race.RACES[rid]; var b = Race.best(rid); var open = Progress.is_open(rid)
		var bt = _btn("", Vector2(40 + (k / 4) * 400, y + (k % 4) * 104), Vector2(385, 94), func(): if open and _owned(): emit_signal("race", rid)); bt.alignment = HORIZONTAL_ALIGNMENT_LEFT
		var line2 = ("best %s · %s" % [Race.fmt(b[0]), ["1st", "2nd", "3rd", "4th"][b[1] - 1]]) if b[0] > 0 else "prize %s credits" % _n(Progress.purse(rid))
		if not open: line2 = "podium in %s to open" % Race.RACES[R.get("after", Race.ORDER[k - 1])].name
		bt.text = "  %s%s\n  %s" % [R.name, Race.tag(rid), line2]; bt.add_theme_font_size_override("font_size", 22)
		if not open: bt.modulate = Color(1, 1, 1, 0.45)
		race_ui.append(bt); k += 1
	race_ui.append(_btn("BACK", Vector2(40, y + 4 * 104 + 6), Vector2(180, 64), func(): show_page("")))
	for c in race_ui: c.visible = false

func _build_garage():
	for c in garage_ui: c.queue_free()
	garage_ui = []
	var id = ids[idx]; var u = Progress.U(id); var y = 140
	garage_ui.append(_lbl("Garage · %s" % Car.CARS[id].name, 30, Vector2(40, y - 10)))
	y += 46
	for g in Progress.UPG:
		var lv: int = u[g.k]; var mx = g.d.size() - 1
		var l = _lbl("%s · %s" % [g.name, g.d[lv].split("  ")[0]], 22, Vector2(40, y + 12)); garage_ui.append(l)
		var dots = _lbl("●".repeat(lv) + "○".repeat(mx - lv), 20, Vector2(286, y + 14)); dots.modulate = Hud.ACCENT; garage_ui.append(dots)
		if lv < mx:
			var cost: int = g.cost[lv]; var nm: String = g.d[lv + 1].split("  ")[0]
			var b = _btn("%s · %s" % [nm, _n(cost)], Vector2(340, y), Vector2(250, 56), func():
				if Progress.spend(cost): u[g.k] += 1; Progress.save(); emit_signal("changed"); _build_garage(); _show(garage_ui); _refresh()
				else: _note("Not enough credits"))
			b.add_theme_font_size_override("font_size", 20); if Progress.cr < cost: b.modulate = Color(1, 1, 1, 0.5)
			garage_ui.append(b)
		else:
			var m = _lbl("fully fitted", 20, Vector2(350, y + 14)); m.modulate = Color(1, 1, 1, 0.5); garage_ui.append(m)
		y += 68
	garage_ui.append(_lbl("Paint  ·  %s each, yours to keep" % _n(Progress.PAINT_COST), 22, Vector2(40, y + 8)))
	y += 46
	for k in Progress.PAINTS.size():
		var pc = Progress.PAINTS[k]; var b = Button.new(); b.position = Vector2(40 + k * 62, y); b.size = Vector2(56, 56)
		var sb = StyleBoxFlat.new(); sb.bg_color = pc[1] if k > 0 else Color(0.2, 0.2, 0.22); sb.set_corner_radius_all(10)
		sb.border_color = Hud.ACCENT if u.paint == k else Color(1, 1, 1, 0.25); sb.set_border_width_all(4 if u.paint == k else 1)
		for st in ["normal", "hover", "pressed"]: b.add_theme_stylebox_override(st, sb)
		b.text = "" if (k == 0 or k in u.owned) else "1.5k"; b.add_theme_font_size_override("font_size", 13)
		if k == 0: b.text = "orig."
		var lum = pc[1].get_luminance() if k > 0 else 0.0
		for st in ["font_color", "font_hover_color", "font_pressed_color"]: b.add_theme_color_override(st, Color(0.05, 0.05, 0.06) if lum > 0.5 else Color(1, 1, 1))
		b.tooltip_text = pc[0]
		b.pressed.connect(func():
			if not (k in u.owned) and k > 0:
				if not Progress.spend(Progress.PAINT_COST): _note("Not enough credits"); return
				u.owned.append(k)
			u.paint = k; Progress.save(); emit_signal("changed"); _build_garage(); _show(garage_ui); _refresh())
		root.add_child(b); garage_ui.append(b)
	garage_ui.append(_btn("BACK", Vector2(40, y + 90), Vector2(180, 60), func(): show_page("")))

func _show(a: Array):
	for c in a: c.visible = true

# ---------------------------------------------------------------- cars
func _owned() -> bool: return ids[idx] in Progress.cars

func _go():
	var id = ids[idx]
	if not _owned():
		var price: int = Progress.PRICE[id]
		if not Progress.spend(price): _note("You need %s credits. Win races to earn them." % _n(price)); return
		Progress.cars.append(id); Progress.save(); _note("%s is yours." % Car.CARS[id].name); pick(0); _refresh(); return
	Progress.car = id; Progress.save()
	emit_signal("drive", id)

func pick(d: int):
	idx = (idx + d + ids.size()) % ids.size(); var id = ids[idx]; var C = Car.CARS[id]
	name_lbl.text = C.name; blurb.text = C.blurb
	var V = {}; for k in C.veh: V[k] = C.veh[k]
	Progress.tune(id, V)
	stats.text = "%d kg · %d Nm · redline %d rpm\n%d gears · %s" % [V.m, V.tqPeak, V.red, V.gears.size(), "mid-engine" if id == "vortex" else "front-engine V8"]
	go_btn.text = "FREE ROAM" if _owned() else "BUY · %s" % _n(Progress.PRICE[id])
	garage_btn.modulate = Color(1, 1, 1, 1.0 if _owned() else 0.4)
	note.text = ""
	if d != 0: emit_signal("drive", "preview:" + id)

func _note(s: String): note.text = s

static func _n(x: int) -> String:          # 25000 -> 25,000
	var s = str(abs(x)); var out = ""
	while s.length() > 3: out = "," + s.substr(s.length() - 3) + out; s = s.substr(0, s.length() - 3)
	return ("-" if x < 0 else "") + s + out

func _lbl(t: String, sz: int, pos: Vector2) -> Label:
	var l = Label.new(); l.text = t; l.add_theme_font_size_override("font_size", sz); l.position = pos; root.add_child(l); return l
func _btn(t: String, pos: Vector2, sz: Vector2, cb: Callable) -> Button:
	var b = Button.new(); b.text = t; b.position = pos; b.size = sz; Hud.style_button(b); b.add_theme_font_size_override("font_size", 28); b.pressed.connect(cb); root.add_child(b); return b

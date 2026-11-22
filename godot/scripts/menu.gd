extends CanvasLayer
class_name Menu
# start screen and garage: pick a car, drive; the car turns slowly on the road behind the panel
signal drive(car_id)
var ids = ["vortex", "calder"]; var idx = 0
var title: Label; var name_lbl: Label; var blurb: Label; var stats: Label; var root: Control

func _ready():
	root = Control.new(); root.set_anchors_preset(Control.PRESET_FULL_RECT); add_child(root)
	var shade = ColorRect.new(); shade.color = Color(0.04, 0.05, 0.07, 0.55); shade.set_anchors_preset(Control.PRESET_LEFT_WIDE); shade.custom_minimum_size = Vector2(460, 0); shade.size = Vector2(460, 2000); root.add_child(shade)
	title = _lbl("AURELIA ISLAND", 44, Vector2(40, 40)); _lbl("Coast · Godot preview", 20, Vector2(42, 98)).modulate = Color(1, 1, 1, 0.6)
	name_lbl = _lbl("", 36, Vector2(40, 180)); blurb = _lbl("", 18, Vector2(40, 232)); blurb.autowrap_mode = TextServer.AUTOWRAP_WORD; blurb.size = Vector2(380, 80)
	stats = _lbl("", 18, Vector2(40, 310)); stats.modulate = Color(1, 1, 1, 0.75)
	_btn("◀", Vector2(40, 420), Vector2(80, 64), func(): pick(-1))
	_btn("▶", Vector2(130, 420), Vector2(80, 64), func(): pick(1))
	_btn("DRIVE", Vector2(40, 510), Vector2(300, 80), func(): emit_signal("drive", ids[idx]))
	pick(0)

func _lbl(t: String, sz: int, pos: Vector2) -> Label:
	var l = Label.new(); l.text = t; l.add_theme_font_size_override("font_size", sz); l.position = pos; root.add_child(l); return l
func _btn(t: String, pos: Vector2, sz: Vector2, cb: Callable):
	var b = Button.new(); b.text = t; b.position = pos; b.size = sz; b.add_theme_font_size_override("font_size", 30); b.pressed.connect(cb); root.add_child(b)

func pick(d: int):
	idx = (idx + d + ids.size()) % ids.size(); var C = Car.CARS[ids[idx]]
	name_lbl.text = C.name; blurb.text = C.blurb
	var v = C.veh; stats.text = "%d kg · %d Nm · redline %d rpm\n%d gears · %s" % [v.m, v.tqPeak, v.red, v.gears.size(), "mid-engine" if ids[idx] == "vortex" else "front-engine V8"]
	if d != 0: emit_signal("drive", "preview:" + ids[idx])

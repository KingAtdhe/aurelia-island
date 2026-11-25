extends Control
class_name DriftScore
# Drift scoring (port of the web game's DS): points flow while the car slides forward above 25 km/h at 12-100 degrees,
# rate = speed x angle factor x multiplier. The multiplier grows with a long drift and with drifts linked within 1.6 s (up to
# x5). Straightening out banks the points; a crash or a spin loses them. In free roam a banked drift of 50+ pays 1 credit per
# 10 points; in the Touge Drift event the run's total counts instead (pay = false).
var car: Car
var on := true; var pay := true
var cur := 0.0; var mul := 1.0; var total := 0; var t := 0.0; var gap := 99.0; var active := false
var show := 0.0; var pts: Label; var sub: Label

func _ready():
	set_anchors_preset(Control.PRESET_FULL_RECT); mouse_filter = Control.MOUSE_FILTER_IGNORE
	var vs = get_viewport().get_visible_rect().size
	pts = Label.new(); pts.add_theme_font_size_override("font_size", 46); pts.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.65)); pts.add_theme_constant_override("outline_size", 8)
	pts.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER; pts.size = Vector2(600, 60); pts.position = Vector2(vs.x / 2 - 300, 122); add_child(pts)
	sub = Label.new(); sub.add_theme_font_size_override("font_size", 20); sub.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.65)); sub.add_theme_constant_override("outline_size", 5)
	sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER; sub.size = Vector2(600, 30); sub.position = Vector2(vs.x / 2 - 300, 178); add_child(sub)
	reset()

func reset():
	cur = 0.0; mul = 1.0; total = 0; t = 0.0; gap = 99.0; active = false; show = 0.0
	if pts: pts.text = ""; sub.text = ""

func bank():
	if cur > 0.0:
		var p = int(round(cur)); total += p; _flash("+" + Menu._n(p), "DRIFT", Color(0.5, 1.0, 0.6))
		if pay and p >= 50: Progress.earn(int(round(p / 10.0)))
	cur = 0.0; mul = 1.0; t = 0.0; active = false

func fail(why: String):
	if cur > 50.0: _flash(why, "DRIFT LOST", Color(1.0, 0.35, 0.3))
	cur = 0.0; mul = 1.0; t = 0.0; active = false; gap = 99.0

func _flash(a: String, b: String, c: Color):
	pts.text = a; sub.text = b; pts.add_theme_color_override("font_color", c); show = 1.6

func _process(dt):
	if car == null: return
	var kmh = car.speed * 3.6; var ab = abs(car.beta) * 57.3
	var ok = on and not car.air and car.vf > 1.0 and kmh > 25.0 and ab > 12.0 and ab < 100.0 and not car.frozen
	if ab > 110.0 and cur > 0.0: fail("SPUN OUT")
	if ok:
		if not active:
			active = true
			if gap < 1.6: mul = minf(5.0, mul + 0.5)          # linked drifts
		gap = 0.0; t += dt
		mul = minf(5.0, maxf(mul, 1.0 + floor(t / 2.5) * 0.5))
		var af = clampf((ab - 12.0) / 33.0, 0.0, 1.25); var sf = 1.0 if car.surf == "road" else (0.5 if car.surf == "dirt" else 0.0)
		cur += dt * kmh * 1.1 * af * sf * mul
	elif active:
		gap += dt
		if gap > 1.6: bank()
	else: gap += dt
	if show > 0.0: show -= dt; visible = true
	elif cur > 0.0:
		visible = true; pts.text = "%s  x%.1f" % [Menu._n(int(round(cur))), mul]; sub.text = "%d°  DRIFT" % int(round(ab)); pts.add_theme_color_override("font_color", Color(1, 1, 1))
	else: visible = false

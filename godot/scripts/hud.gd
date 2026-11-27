extends RefCounted
class_name Hud
# The driving HUD: a round rev counter with the speed and gear (bottom centre) and a minimap turned with the car (top right)
# showing the roads, the race rivals, the next checkpoint and the traffic.

const ACCENT = Color(1.0, 0.62, 0.08)
const PANEL = Color(0.04, 0.06, 0.09, 0.62)

static func panel_style(radius := 14) -> StyleBoxFlat:
	var sb = StyleBoxFlat.new(); sb.bg_color = PANEL; sb.set_corner_radius_all(radius); sb.border_color = Color(1, 1, 1, 0.12); sb.set_border_width_all(1)
	sb.content_margin_left = 16; sb.content_margin_right = 16; sb.content_margin_top = 6; sb.content_margin_bottom = 6
	return sb

static func style_button(b: Button):
	var n = panel_style(12); var p = panel_style(12); p.bg_color = Color(ACCENT.r, ACCENT.g, ACCENT.b, 0.55)
	b.add_theme_stylebox_override("normal", n); b.add_theme_stylebox_override("hover", n); b.add_theme_stylebox_override("pressed", p); b.add_theme_stylebox_override("focus", StyleBoxEmpty.new())
	b.add_theme_font_size_override("font_size", 22); b.add_theme_color_override("font_color", Color(0.95, 0.96, 0.98))

class Gauge extends Control:
	var car: Car
	var rpm_s = 0.0
	func _process(dt):
		if car: rpm_s = lerpf(rpm_s, car.rpm, clampf(dt * 14.0, 0.0, 1.0))
		queue_redraw()
	func _draw():
		if car == null: return
		var c = size / 2.0; var R = minf(size.x, size.y) / 2.0 - 6.0; var k_ = R / 109.0
		var red = car.V.red; var top = ceilf((red + 600.0) / 1000.0) * 1000.0
		var a0 = deg_to_rad(135.0); var a1 = deg_to_rad(405.0)
		var ang = func(r): return a0 + (a1 - a0) * clampf(r / top, 0.0, 1.0)
		draw_circle(c, R + 4.0, Color(0.03, 0.05, 0.07, 0.72))
		draw_arc(c, R - 8.0, a0, a1, 64, Color(1, 1, 1, 0.13), 10.0, true)
		draw_arc(c, R - 8.0, ang.call(red), a1, 24, Color(0.85, 0.12, 0.1, 0.55), 10.0, true)
		var f = clampf(rpm_s / top, 0.0, 1.0)
		var col = Color(0.95, 0.96, 0.98).lerp(ACCENT, clampf((rpm_s - red * 0.7) / (red * 0.25), 0.0, 1.0))
		if rpm_s > red - 150.0: col = Color(1.0, 0.22, 0.15)
		draw_arc(c, R - 8.0, a0, ang.call(rpm_s), 64, col, 10.0, true)
		var font = ThemeDB.fallback_font
		for k in int(top / 1000.0) + 1:
			var a = ang.call(k * 1000.0); var dir = Vector2(cos(a), sin(a))
			draw_line(c + dir * (R - 22.0), c + dir * (R - 15.0), Color(1, 1, 1, 0.55), 2.0, true)
			draw_string(font, c + dir * (R - 34.0 * k_) - Vector2(8, -6), str(k), HORIZONTAL_ALIGNMENT_CENTER, 16, int(14 * k_), Color(1, 1, 1, 0.6))
		var kmh = int(car.speed * 3.6)
		draw_string(font, c + Vector2(-80, 16 * k_), str(kmh), HORIZONTAL_ALIGNMENT_CENTER, 160, int(52 * k_), Color(1, 1, 1))
		draw_string(font, c + Vector2(-40, 38 * k_), "km/h", HORIZONTAL_ALIGNMENT_CENTER, 80, int(14 * k_), Color(1, 1, 1, 0.55))
		var g = "R" if car.vf < -0.5 and car.in_brake > 0 else str(car.gear + 1)
		var gb = Rect2(c + Vector2(-17, R * 0.45), Vector2(34, 30))
		draw_rect(gb, Color(ACCENT.r, ACCENT.g, ACCENT.b, 0.9)); draw_string(font, gb.position + Vector2(0, 24), g, HORIZONTAL_ALIGNMENT_CENTER, 34, 24, Color(0.05, 0.05, 0.06))

class MiniMap extends Control:
	var main: Node
	var tex: TextureRect
	var span_m = 280.0
	const X0 = -2400.0; const Z0 = -1680.0; const SX = 4800.0; const SZ = 3360.0
	func _init(m: Node, sz: float):
		main = m; size = Vector2(sz, sz); mouse_filter = Control.MOUSE_FILTER_IGNORE
		tex = TextureRect.new(); tex.expand_mode = TextureRect.EXPAND_IGNORE_SIZE; tex.stretch_mode = TextureRect.STRETCH_SCALE; tex.texture = load("res://assets/minimap.png")
		tex.custom_minimum_size = size; tex.size = size
		tex.mouse_filter = Control.MOUSE_FILTER_IGNORE; tex.show_behind_parent = true          # the markers are drawn by this control, on top
		var sm = ShaderMaterial.new(); sm.shader = load("res://shaders/minimap.gdshader"); sm.set_shader_parameter("map", tex.texture); tex.material = sm; add_child(tex)
	func _process(dt):
		var car: Car = main.car
		span_m = lerpf(span_m, 220.0 + car.speed * 4.0, clampf(dt * 1.5, 0.0, 1.0))
		var sm: ShaderMaterial = tex.material
		sm.set_shader_parameter("center", Vector2((car.px - X0) / SX, (car.pz - Z0) / SZ))
		sm.set_shader_parameter("fwd", Vector2(sin(car.hd), cos(car.hd)))
		sm.set_shader_parameter("span", Vector2(span_m / SX, span_m / SZ))
		queue_redraw()
	func _to_screen(p: Vector3) -> Vector2:          # world point -> minimap pixel (car at the centre, heading up), or NAN outside
		var car: Car = main.car; var fx = sin(car.hd); var fz = cos(car.hd)
		var dx = p.x - car.px; var dz = p.z - car.pz
		var u = (dx * -fz + dz * fx) / span_m; var v = -(dx * fx + dz * fz) / span_m
		return Vector2(u, v)
	func _dot(p: Vector3, col: Color, r: float, clamp_edge := false):
		var q = _to_screen(p); var R = size.x / 2.0
		if q.length() > 0.86:
			if not clamp_edge: return
			q = q.normalized() * 0.86
		draw_circle(size / 2.0 + q * R, r + 1.5, Color(0, 0, 0, 0.6)); draw_circle(size / 2.0 + q * R, r, col)
	func _draw():
		var c = size / 2.0
		if main.traffic and main.traffic.visible:
			for tc in main.traffic.cars: _dot(tc.n.global_position, Color(0.75, 0.78, 0.82), 3.0)
		if main.get("freeroam") and not main.race:          # speed traps (orange) and drift-zone starts (blue)
			for t in main.freeroam.traps: _dot(t[0], ACCENT, 4.0)
			for z in main.freeroam.zones: _dot(z[0], Color(0.35, 0.85, 1.0), 4.0)
		if main.race:
			var rc = main.race
			if rc.next_cp < rc.cps.size():
				var a = rc.at(rc.cps[rc.next_cp]); _dot(a[0], ACCENT, 6.0, true)
			for r in rc.racers:
				if r.rival: _dot(Vector3(r.car.px, 0, r.car.pz), Color(0.95, 0.25, 0.2), 5.0)
		var tri = PackedVector2Array([c + Vector2(0, -11), c + Vector2(8, 8), c + Vector2(0, 4), c + Vector2(-8, 8)])
		draw_colored_polygon(tri, Color(0, 0, 0, 0.6)); draw_colored_polygon(PackedVector2Array([c + Vector2(0, -9), c + Vector2(6, 6), c + Vector2(0, 3), c + Vector2(-6, 6)]), ACCENT)

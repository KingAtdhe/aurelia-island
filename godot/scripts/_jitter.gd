extends Node
# test: smoothness of the drawn car and the chase camera at a frame rate that does not match the 60 Hz physics
# JITTER=<fps> (default 45). Prints how even the car's on-screen motion is: per-frame speed of the drawn car against
# its real speed, and the frame-to-frame wobble of the car relative to the camera (0 = perfectly steady).
var m; var t := 0.0; var last := Vector3.ZERO; var last_rel := Vector3.ZERO; var last_d := Vector3.ZERO
var ratios := []; var wob := []
func _ready():
	m = get_parent(); m.menu_on = false
	if m.menu: m.menu.queue_free(); m.menu = null
	m.hud.visible = true
	Engine.max_fps = int(OS.get_environment("JITTER")) if int(OS.get_environment("JITTER")) > 0 else 45
	m.touch.gas = true
func _process(dt):
	t += dt
	var p: Vector3 = m.car.vis_pos(); var rel: Vector3 = p - m.cam.global_position
	if t > 3.0 and t < 9.0 and dt > 0.0:
		var v = (p - last).length() / dt
		if m.car.speed > 5.0: ratios.append(v / m.car.speed)
		var d = rel - last_rel; wob.append((d - last_d).length()); last_d = d
	last = p; last_rel = rel
	if t >= 9.0:
		print("JITTER fps %d interp %s  speed ratio mean %.3f sd %.3f  cam wobble mean %.4f m max %.4f m" % [Engine.max_fps, str(get_tree().physics_interpolation), _mean(ratios), _sd(ratios), _mean(wob), _max(wob)])
		get_tree().quit()
func _mean(a) -> float:
	var s = 0.0
	for x in a: s += x
	return s / maxf(1, a.size())
func _sd(a) -> float:
	var mu = _mean(a); var s = 0.0
	for x in a: s += (x - mu) * (x - mu)
	return sqrt(s / maxf(1, a.size()))
func _max(a) -> float:
	var s = 0.0
	for x in a: s = maxf(s, x)
	return s

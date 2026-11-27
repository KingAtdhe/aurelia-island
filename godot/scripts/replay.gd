extends Node
class_name Replay
# Replays and photo mode.
#  - Recording: always on while driving: the player's car and any race rivals, 30 times a second, the last 60 s.
#  - REPLAY (HUD button, and on the race results): the game pauses and the recording plays back with TV cameras
#    (chase, trackside posts that cut as the car passes, a low orbit); tap CAM to change, SLOW for half speed, EXIT.
#  - PHOTO (HUD button, or from a replay): the picture freezes; drag to orbit the car, ZOOM changes the lens, SAVE writes
#    a PNG to the phone's Pictures/AureliaIsland folder (or the game's own folder if Android does not allow it).
const HZ = 30.0; const KEEP = 60.0
const F = 9          # floats per car per sample: px py pz hd pitch roll delta wheel_spin rear_spin
var main
var rec := {}        # car instance id -> { car, data: PackedFloat32Array }
var t_rec := 0.0; var n_rec := 0
var mode := ""       # "", "replay", "photo"
var pt := 0.0; var speed := 1.0; var cam_kind := 0; var post := Vector3.ZERO; var post_t := 0.0
var orbit := Vector2(0.6, 0.25); var dist := 6.0; var fov := 55.0
var ui: CanvasLayer; var info: Label; var cam: Camera3D
var _was_cam: Camera3D

func _init(m): main = m; name = "Replay"; process_mode = Node.PROCESS_MODE_ALWAYS

func cars() -> Array:
	var out = [main.car]
	if main.race: for r in main.race.racers: if r.rival and is_instance_valid(r.car): out.append(r.car)
	return out

func clear(): rec.clear(); n_rec = 0

func _physics_process(dt):
	if mode != "" or main.menu_on or get_tree().paused: return
	t_rec += dt
	if t_rec < 1.0 / HZ: return
	t_rec -= 1.0 / HZ; n_rec += 1
	var cap = int(KEEP * HZ)
	for c in cars():
		var key = c.get_instance_id()
		if not rec.has(key): rec[key] = { car = c, data = PackedFloat32Array(), first = n_rec - 1 }
		var d: PackedFloat32Array = rec[key].data
		d.append_array([c.px, c.py, c.pz, c.hd, c.pitch, c.roll, c.delta_, c.wheel_spin, c.rear_spin])
		if d.size() > cap * F: rec[key].data = d.slice(d.size() - cap * F); rec[key].first = n_rec - cap

func length() -> float:
	var n = 0
	for k in rec: n = maxi(n, rec[k].data.size() / F)
	return n / HZ

# ---------------------------------------------------------------- replay
func start_replay():
	if mode != "" or length() < 2.0: return
	mode = "replay"; pt = 0.0; speed = 1.0; cam_kind = 0; post_t = 0.0
	_pause(true); _ui(["CAM", "SLOW", "PHOTO", "EXIT"])

func _process(dt):
	if mode == "": return
	if mode == "replay":
		pt += dt * speed
		if pt >= length() - 0.05: pt = 0.0
		_pose_all(pt)
		_replay_cam(dt)
		info.text = "REPLAY   %s   %d / %d s" % [["CHASE", "TV", "ORBIT"][cam_kind], int(pt), int(length())]
	elif mode == "photo":
		_photo_cam()

func _pose_all(tt: float):
	var total = length()
	for k in rec:
		var e = rec[k]; var c: Car = e.car
		if not is_instance_valid(c): continue
		var d: PackedFloat32Array = e.data; var n = d.size() / F
		var off = total - n / HZ          # a car recorded for less time than the longest starts later
		var f = (tt - off) * HZ
		if f < 0.0: f = 0.0
		var i = mini(int(f), n - 2); var u = clampf(f - i, 0.0, 1.0); var a = i * F; var b = a + F
		c.px = lerpf(d[a], d[b], u); c.py = lerpf(d[a + 1], d[b + 1], u); c.pz = lerpf(d[a + 2], d[b + 2], u); c.hd = lerp_angle(d[a + 3], d[b + 3], u)
		c.pitch = lerpf(d[a + 4], d[b + 4], u); c.roll = lerpf(d[a + 5], d[b + 5], u); c.delta_ = lerpf(d[a + 6], d[b + 6], u)
		c.wheel_spin = lerpf(d[a + 7], d[b + 7], u); c.rear_spin = lerpf(d[a + 8], d[b + 8], u)
		c.pose()

func _replay_cam(dt: float):
	var c: Car = main.car; var p = Vector3(c.px, c.py + 0.7, c.pz); var fw = Vector3(sin(c.hd), 0, cos(c.hd))
	cam.fov = 55.0
	match cam_kind:
		0: cam.global_position = p - fw * 6.5 + Vector3(0, 1.6, 0); cam.look_at(p + fw * 3.0)
		1:          # trackside: a post ahead of the car; cut to a new one once the car has passed it
			post_t -= dt
			if post_t <= 0.0 or (post - p).dot(fw) < -25.0:
				var best = null
				for sd in ([7.0, -7.0] if randf() < 0.5 else [-7.0, 7.0]):          # a post on the verge that stands on open ground, not inside a bank
					var q = p + fw * 45.0 + Vector3(-fw.z, 0, fw.x) * sd
					var g = c.ground(q.x, q.z, p.y + 8.0)[0]
					if g > -50.0 and g < p.y + 3.0: best = Vector3(q.x, g + 1.0 + randf() * 1.6, q.z); break
				post = best if best != null else p + fw * 30.0 + Vector3(0, 3.0, 0); post_t = 6.0
			cam.global_position = post; cam.look_at(p); cam.fov = clampf(2.0 * rad_to_deg(atan(5.5 / maxf(post.distance_to(p), 1.0))), 10.0, 55.0)          # zoomed so the car fills a good part of the frame
		2:
			orbit.x += dt * 0.35; var o = Vector3(sin(orbit.x), 0.0, cos(orbit.x)) * 5.5
			cam.global_position = p + o + Vector3(0, 0.25, 0); cam.look_at(p)

# ---------------------------------------------------------------- photo mode
func start_photo():
	if mode == "": _pause(true)
	mode = "photo"; dist = 6.0; fov = 50.0
	var c: Car = main.car; var v = main.cam.global_position - Vector3(c.px, c.py, c.pz)
	orbit = Vector2(atan2(v.x, v.z), clampf(asin(clampf(v.normalized().y, -0.9, 0.9)), 0.02, 1.2)); dist = clampf(v.length(), 3.0, 12.0)
	_ui(["ZOOM +", "ZOOM -", "SAVE", "EXIT"])

func _photo_cam():
	var c: Car = main.car; var p = Vector3(c.px, c.py + 0.6, c.pz)
	var o = Vector3(sin(orbit.x) * cos(orbit.y), sin(orbit.y), cos(orbit.x) * cos(orbit.y)) * dist
	cam.global_position = p + o; cam.look_at(p); cam.fov = fov
	info.text = "PHOTO   drag to move round the car"

func _input(e):
	if mode != "photo": return
	if (e is InputEventScreenDrag) or (e is InputEventMouseMotion and (e.button_mask & MOUSE_BUTTON_MASK_LEFT)):
		orbit.x -= e.relative.x * 0.008; orbit.y = clampf(orbit.y + e.relative.y * 0.006, 0.02, 1.3)

func save_photo():
	ui.visible = false; main.hud.visible = false
	await RenderingServer.frame_post_draw
	var img = get_viewport().get_texture().get_image()
	ui.visible = true; main.hud.visible = mode == ""
	var stamp = Time.get_datetime_string_from_system().replace(":", "-")
	var dirs = [OS.get_system_dir(OS.SYSTEM_DIR_PICTURES) + "/AureliaIsland", "user://photos"]
	for d in dirs:
		if d.begins_with("/AureliaIsland"): continue
		DirAccess.make_dir_recursive_absolute(d)
		var f = d + "/aurelia_%s.png" % stamp
		if img.save_png(f) == OK: info.text = "Saved: %s" % (f if not f.begins_with("user://") else "in the game folder"); return
	info.text = "Could not save the picture"

# ---------------------------------------------------------------- common
func stop():
	if mode == "": return
	mode = ""; _pause(false)
	for k in rec:          # back to where the cars really are
		var c: Car = rec[k].car
		if is_instance_valid(c): var d: PackedFloat32Array = rec[k].data; _set_last(c, d)
	if ui: ui.queue_free(); ui = null
	if cam: cam.queue_free(); cam = null
	if _was_cam: _was_cam.make_current()

func _set_last(c: Car, d: PackedFloat32Array):
	if d.size() < F: return
	var a = d.size() - F
	c.px = d[a]; c.py = d[a + 1]; c.pz = d[a + 2]; c.hd = d[a + 3]; c.pitch = d[a + 4]; c.roll = d[a + 5]; c.delta_ = d[a + 6]; c.pose(); c.reset_physics_interpolation()

func _pause(on: bool):
	get_tree().paused = on; main.hud.visible = not on
	for k in rec:
		var c = rec[k].car
		if is_instance_valid(c): c.physics_interpolation_mode = Node.PHYSICS_INTERPOLATION_MODE_OFF if on else Node.PHYSICS_INTERPOLATION_MODE_INHERIT
	if on and cam == null:
		_was_cam = main.cam; cam = Camera3D.new(); cam.near = 0.1; cam.far = main.cam.far; cam.cull_mask = main.cam.cull_mask
		cam.physics_interpolation_mode = Node.PHYSICS_INTERPOLATION_MODE_OFF; main.add_child(cam); cam.global_transform = main.cam.global_transform; cam.make_current()

func _ui(buttons: Array):
	if ui: ui.queue_free()
	ui = CanvasLayer.new(); ui.layer = 50; ui.process_mode = Node.PROCESS_MODE_ALWAYS; add_child(ui)
	var vs = get_viewport().get_visible_rect().size
	info = Label.new(); info.add_theme_font_size_override("font_size", 24); info.position = Vector2(30, 24); info.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.7)); info.add_theme_constant_override("outline_size", 6); ui.add_child(info)
	var x = vs.x - 20.0 - buttons.size() * 132.0
	for t in buttons:
		var b = Button.new(); b.text = t; b.position = Vector2(x, vs.y - 84); b.custom_minimum_size = Vector2(120, 60); Hud.style_button(b); ui.add_child(b); x += 132.0
		b.pressed.connect(_press.bind(t))

func _press(t: String):
	if t == "CAM": cam_kind = (cam_kind + 1) % 3; post_t = 0.0
	elif t == "SLOW": speed = 0.4 if speed > 0.5 else 1.0
	elif t == "PHOTO": start_photo()
	elif t == "ZOOM +": fov = maxf(15.0, fov - 7.0)
	elif t == "ZOOM -": fov = minf(80.0, fov + 7.0)
	elif t == "SAVE": save_photo()
	elif t == "EXIT": stop()

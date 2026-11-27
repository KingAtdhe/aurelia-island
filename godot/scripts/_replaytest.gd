extends Node
# test: REPLAYTEST=1 drives 6 s, plays it back (chase and TV cameras), opens photo mode and saves a picture
var m
func _ready():
	m = get_parent(); m.menu_on = false
	if m.menu: m.menu.queue_free(); m.menu = null
	m.hud.visible = true; m.touch.gas = true
	await get_tree().create_timer(6.0).timeout
	m.touch.gas = false
	var before = Vector3(m.car.px, m.car.py, m.car.pz)
	var r: Replay = m.replay
	print("REPLAY recorded %.1f s" % r.length())
	r.start_replay()
	for k in 40: await get_tree().process_frame
	await RenderingServer.frame_post_draw; get_viewport().get_texture().get_image().save_png("/tmp/replay_0.png")
	print("REPLAY at %.1f car %s paused %s" % [r.pt, Vector3(m.car.px, m.car.py, m.car.pz), get_tree().paused])
	r._press("CAM")
	for k in 40: await get_tree().process_frame
	await RenderingServer.frame_post_draw; get_viewport().get_texture().get_image().save_png("/tmp/replay_1.png")
	r._press("PHOTO")
	for k in 5: await get_tree().process_frame
	await r.save_photo()
	print("REPLAY photo: ", r.info.text)
	r._press("EXIT")
	for k in 5: await get_tree().process_frame
	print("REPLAY back: paused %s car %s (before %s)" % [get_tree().paused, Vector3(m.car.px, m.car.py, m.car.pz), before])
	get_tree().quit()

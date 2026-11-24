extends Node
# test: drops the car at places all over the island and takes a picture of each once the map round it has streamed in
# TOUR="Road:frac,Road:frac,..." (frac 0..1 along the road), optional TOURCAM=high for a raised view
var m
func _ready():
	m = get_parent(); m.menu_on = false
	if m.menu: m.menu.queue_free(); m.menu = null
	m.hud.visible = true
	var spots = OS.get_environment("TOUR").split(",")
	var k = 0
	for s in spots:
		var a = s.split(":")
		if a[0] == "P":         # P:x:y:z:heading -> the car at that spot, facing (sin h, cos h)
			m.car.place(Vector3(float(a[1]), float(a[2]), float(a[3])), float(a[4])); m.prime()
		else:
			var road = a[0]; var p = m.roads[road]; var n = p.size() / 3
			var i = clampi(int(float(a[1]) * (n - 2)), 0, n - 2)
			m.spawn(road, i)
		m.car.frozen = true
		var t0 = Time.get_ticks_msec()
		for w in 400:
			await get_tree().process_frame
			if m.island.ready_around() and w > 30: break
		if a.size() > 5:          # P:x:y:z:h:cx,cy,cz -> a free camera at cx,cy,cz looking at x,y,z
			var cp = a[5].split(";"); var cam := Camera3D.new(); m.add_child(cam); cam.far = 4000.0
			cam.global_position = Vector3(float(cp[0]), float(cp[1]), float(cp[2])); cam.look_at(Vector3(float(a[1]), float(a[2]), float(a[3]))); cam.make_current()
		for w in 20: await get_tree().process_frame
		await RenderingServer.frame_post_draw
		var nm = "/tmp/tour_%02d.png" % k
		get_viewport().get_texture().get_image().save_png(nm)
		print("TOUR %d %s pos %s tris %d draws %d prims %d (%.1f s)" % [k, s, Vector3(m.car.px, m.car.py, m.car.pz), m.island.loaded_tris, Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME), Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME), (Time.get_ticks_msec() - t0) / 1000.0])
		k += 1
	var worst = m.island.attach_ms.duplicate(); worst.sort_custom(func(a, b): return a[1] > b[1])
	print("ATTACH worst ", worst.slice(0, 6))
	get_tree().quit()

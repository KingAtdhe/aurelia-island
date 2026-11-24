extends Node
# test: put the car at PROBE="x,y,z" and drive off in four directions, printing what holds it
func _ready():
	var m = get_parent(); m.menu_on = false
	if m.menu: m.menu.queue_free(); m.menu = null
	var a = OS.get_environment("PROBE").split(","); var P = Vector3(float(a[0]), float(a[1]), float(a[2]))
	await get_tree().create_timer(0.5).timeout
	var sp = m.get_world_3d().direct_space_state
	for dz in [0.0, -0.5, -1.0, -2.0]:
		var q = PhysicsRayQueryParameters3D.create(P + Vector3(0, 4.0, dz), P + Vector3(0, -60.0, dz)); var hh = sp.intersect_ray(q)
		if hh: print("PROBE ray dz %.1f y %.2f %s / %s" % [dz, hh.position.y, hh.collider.get_parent().name, hh.collider.get_parent().get_parent().name])
	for h in [PI, PI - 0.3, PI + 0.3]:
		m.car.place(P, h); m.touch.gas = true
		for k in 6:
			await get_tree().create_timer(0.5).timeout
			var c = m.car
			print("PROBE h%.2f t%.1f pos (%.1f %.1f %.1f) v %.2f vf %.2f surf %s air %s gear %d thr %.2f rpm %d pitch %.3f roll %.3f spin %s hand %s shift %.2f yr %.2f hd %.2f" % [h, k * 0.5, c.px, c.py, c.pz, c.speed, c.vf, c.surf, c.air, c.gear + 1, c.thr, c.rpm, c.pitch, c.roll, c.spin, c.in_hand, c.shiftT, c.yr, c.hd])
	get_tree().quit()

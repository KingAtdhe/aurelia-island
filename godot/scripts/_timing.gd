extends Node
func _ready():
	var m = get_parent(); await get_tree().create_timer(1.0).timeout
	m.menu.emit_signal("drive", "vortex"); await get_tree().create_timer(0.5).timeout
	for k in 2:
		var t0 = Time.get_ticks_usec(); m.start_race("coast"); print("TIME start_race #%d %.0f ms" % [k, (Time.get_ticks_usec() - t0) / 1000.0])
		await get_tree().create_timer(1.0).timeout
	var t1 = Time.get_ticks_usec(); m.car.setup("calder"); print("TIME car.setup calder %.0f ms" % ((Time.get_ticks_usec() - t1) / 1000.0))
	var t2 = Time.get_ticks_usec(); m.open_menu(); print("TIME open_menu %.0f ms" % ((Time.get_ticks_usec() - t2) / 1000.0))
	get_tree().quit()

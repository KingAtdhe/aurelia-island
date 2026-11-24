extends Node
# test: menu and race flows done over and over; checks nothing is left behind
var m
func check(tag: String):
	await get_tree().create_timer(0.5).timeout
	var cars = get_tree().root.find_children("*", "Car", true, false).size()
	var players = 0
	for n in get_tree().root.find_children("*", "", true, false):
		if n is AudioStreamPlayer or n is AudioStreamPlayer3D: players += 1
	print("FLOW %-22s cars %d  race %s  traffic vis %s proc %s  frozen %s  dyn2 %d  hud kids %d  audio players %d  menu %s" % [tag, cars, m.race != null, m.traffic.visible, m.traffic.process_mode, m.car.frozen, m.coll.dyn2.size(), m.hud.get_child_count(), players, m.menu != null])
func _ready():
	m = get_parent()
	await get_tree().create_timer(1.0).timeout; await check("start (menu)")
	m.menu.emit_signal("drive", "vortex"); await check("free roam")
	m.start_race("coast"); await get_tree().create_timer(2.0).timeout; await check("race coast")
	m.start_race("coast"); await get_tree().create_timer(2.0).timeout; await check("retry")
	m.start_race("peninsula"); await get_tree().create_timer(5.0).timeout; await check("next race (racing)")
	m.end_race(); m.open_menu(); await check("menu mid-race")
	m.menu.pick(1); await get_tree().create_timer(0.5).timeout; await check("menu preview calder")
	m.menu.emit_signal("drive", "calder"); await check("free roam calder")
	m.reset_car(); await check("reset")
	m.start_race("lighthouse"); await get_tree().create_timer(5.0).timeout; m.reset_car(); await check("race + reset")
	m.end_race(); await check("free roam again")
	for k in 5: m.start_race("coast"); await get_tree().create_timer(0.3).timeout
	m.end_race(); await check("5 quick restarts")
	get_tree().quit()

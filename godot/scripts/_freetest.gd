extends Node
# test: FREETEST=1 drives through a speed trap and a drift zone and checks the daily challenge text
var m
func _ready():
	m = get_parent(); m.menu_on = false
	if m.menu: m.menu.queue_free(); m.menu = null
	var f: FreeRoam = m.freeroam
	print("FREE traps %d zones %d daily: %s" % [f.traps.size(), f.zones.size(), FreeRoam.daily().text])
	var t = f.traps[0]; m.car.place(t[0] - t[1] * 80.0, atan2(t[1].x, t[1].z)); m.touch.gas = true
	for k in 600:
		await get_tree().physics_frame
		if m._toast and m._toast.text.begins_with("SPEED"): break
	print("FREE trap -> ", m._toast.text if m._toast else "none", " (best ", FreeRoam.best("trap0"), ")")
	m.touch.gas = false
	var z = f.zones[0]; m.car.place(z[0] - z[1] * 6.0, atan2(z[1].x, z[1].z)); m.car.vx = z[1].x * 12.0; m.car.vz = z[1].z * 12.0
	for k in 30: await get_tree().physics_frame
	print("FREE zone active ", f.active, " toast ", m._toast.text)
	m.drift.total += 4200          # as if drifted along the zone
	m.car.place(z[2], atan2(z[1].x, z[1].z))
	for k in 30: await get_tree().physics_frame
	print("FREE zone end -> ", m._toast.text, " active ", f.active, " best ", FreeRoam.best("zone0"))
	get_tree().quit()

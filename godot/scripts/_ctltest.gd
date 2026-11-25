extends Node
# test: CTLTEST=1 checks the control options on the player's car: manual gearbox, traction control off, steering sensitivity
var m
func _ready():
	m = get_parent(); m.menu_on = false
	if m.menu: m.menu.queue_free(); m.menu = null
	var c: Car = m.car
	# manual gearbox: no shifts by itself, shifts on request, first gear again when stopped
	c.manual = true; m.touch.gas = true
	for k in 120: await get_tree().physics_frame
	print("CTL manual 2 s: gear %d rpm %d speed %.0f" % [c.gear + 1, c.rpm, c.speed * 3.6])
	c.shift(1); for k in 30: await get_tree().physics_frame
	c.shift(1); for k in 60: await get_tree().physics_frame
	print("CTL manual after two upshifts: gear %d rpm %d speed %.0f" % [c.gear + 1, c.rpm, c.speed * 3.6])
	c.shift(-1); c.shift(-1); for k in 12: await get_tree().physics_frame
	print("CTL manual downshift: gear %d rpm %d (red %d)" % [c.gear + 1, c.rpm, c.V.red])
	m.touch.gas = false; m.touch.brake = true
	for k in 400:
		await get_tree().physics_frame
		if c.speed < 0.3: break
	m.touch.brake = false; for k in 20: await get_tree().physics_frame
	print("CTL manual stopped: gear %d" % [c.gear + 1])
	c.manual = false
	# traction control off: full throttle with lock from a standstill spins the rear
	for tc in [true, false]:
		c.tc = tc; m.spawn(m.START[0], m.START[1]); var spins = 0
		m.touch.gas = true
		for k in 150:
			await get_tree().physics_frame
			if c.spin: spins += 1
		m.touch.gas = false
		print("CTL traction %s: wheelspin frames %d of 150, speed %.0f" % [tc, spins, c.speed * 3.6])
	c.tc = true
	# sensitivity: wheel angle a moment after full left at 60 km/h
	for sn in [0.6, 1.0, 1.4]:
		c.sens = sn; m.spawn(m.START[0], m.START[1]); m.touch.gas = true
		while c.speed < 16.7: await get_tree().physics_frame
		m.touch.gas = false; m.touch.left = true
		for k in 9: await get_tree().physics_frame
		print("CTL sensitivity %.1f: wheel angle after 0.15 s %.2f deg" % [sn, rad_to_deg(abs(c.delta_))])
		m.touch.left = false
		for k in 60: await get_tree().physics_frame
	c.sens = 1.0
	get_tree().quit()

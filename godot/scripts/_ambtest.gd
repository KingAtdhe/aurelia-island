extends Node
# test: AMBTEST=1 puts the car at a few places and prints how loud each ambient bed wants to be there
func _ready():
	var m = get_parent(); m.menu_on = false
	if m.menu: m.menu.queue_free(); m.menu = null
	var spots = { beach = ["Beach Flyover", 0.3], city = ["Street N-160", 0.5], forest = ["Ring", 0.43], river = ["Ring", 0.45], desert = ["Dune Road", 0.5], summit = ["Skyline Road", 0.8], fields = ["Farm Road", 0.5] }
	for k in spots:
		var p = m.roads[spots[k][0]]; var n = p.size() / 3; m.spawn(spots[k][0], int(spots[k][1] * (n - 2))); m.car.frozen = true
		await get_tree().create_timer(0.6).timeout
		var w = m.ambience.want; var s = ""
		for b in Ambience.BEDS: s += " %s %.2f" % [b, w[b]]
		print("AMB %-7s %s%s  at %s d %s" % [k, Tod.NAMES[Tod.get_level()], s, Vector3(m.car.px, m.car.py, m.car.pz), m.ambience._dist(Vector3(m.car.px, m.car.py, m.car.pz))])
	get_tree().quit()

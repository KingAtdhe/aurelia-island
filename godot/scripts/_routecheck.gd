extends Node
func _ready():
	await get_tree().create_timer(0.5).timeout
	var m = get_parent(); var co: Coll = m.coll
	for rid in Race.ORDER:
		var r = Race.new(); r.R = Race.RACES[rid]; r._build_route(m.roads)
		var seen = {}
		var s = 0.0
		while s < r.length:
			var a = r.at(s); var p: Vector3 = a[0]
			var cell = co.grid.get(Vector2i(floor(p.x / Coll.OG), floor(p.z / Coll.OG)))
			if cell:
				for o in cell.o + cell.c:
					var d = Vector2(o[0] - p.x, o[1] - p.z).length()
					var lat = (Vector3(o[0], 0, o[1]) - a[0]).dot(a[2])
					if abs(lat) < a[3] + 1.5 and abs((Vector3(o[0], 0, o[1]) - a[0]).dot(a[1])) < 3.0 and not seen.has(str(o)):
						seen[str(o)] = 1; print("OBST %s s%.0f lat %.1f (hw %.1f) %s" % [rid, s, lat, a[3], str(o)])
			s += 2.0
		r.free()
	get_tree().quit()

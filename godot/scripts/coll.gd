extends RefCounted
class_name Coll
# obstacles and road-side walls exported from the web game; same push-out rules as its physics()
const OG = 40.0; const SG = 48.0
var grid = {}            # Vector2i -> { o = [], c = [], k = [] }
var roads = []           # { p = PackedFloat32Array, n, hw, wall, lim }
var seg = {}             # Vector2i -> [road index, segment index, ...]
var dyn = []             # moving boxes (traffic), same layout as the static boxes
var dyn2 = []            # race cars: [x, z, half length, half width, angle, owner instance id]; a car never collides with its own box
var hits = []            # traffic cars knocked this frame: [traffic index, push x, push z]  (traffic boxes carry -1 - index as element 5)

func _put(kind: String, o: Array, rad: float):
	for gx in range(floor((o[0] - rad) / OG), floor((o[0] + rad) / OG) + 1):
		for gz in range(floor((o[1] - rad) / OG), floor((o[1] + rad) / OG) + 1):
			var k = Vector2i(gx, gz)
			if not grid.has(k): grid[k] = { o = [], c = [], k = [] }
			grid[k][kind].append(o)

func load_data(path: String, road_pts: Dictionary):
	var d = JSON.parse_string(FileAccess.get_file_as_string(path))
	for o in d["box"]: _put("o", o, Vector2(o[2], o[3]).length() + 2)
	for o in d["circ"]: _put("c", o, o[2] + 2)
	for o in d["knock"]: var kk = [o[0], o[1], o[2], false] + (o.slice(3) if o.size() > 3 else []); _put("k", kk, o[2] + 2)      # x z r hit [species, instance]
	for name in d["roads"]:
		if not road_pts.has(name): continue
		var r = d["roads"][name]; var p = PackedFloat32Array(road_pts[name]); var n = p.size() / 3
		var ri = roads.size(); roads.append({ p = p, n = n, hw = float(r["hw"]), wall = r["wall"], lim = r["lim"] })
		for i in n - 1:
			var cx = (p[i * 3] + p[i * 3 + 3]) / 2; var cz = (p[i * 3 + 2] + p[i * 3 + 5]) / 2; var k = Vector2i(floor(cx / SG), floor(cz / SG))
			if not seg.has(k): seg[k] = []
			seg[k].append(ri); seg[k].append(i)

# nearest road segment: {ok, r, i, d (signed, + = left), y, tx, tz}
func road_query(x: float, z: float, yref: float) -> Dictionary:
	var out = { ok = false }; var best = 1e9; var gx = int(floor(x / SG)); var gz = int(floor(z / SG))
	for ax in range(gx - 1, gx + 2):
		for az in range(gz - 1, gz + 2):
			var a = seg.get(Vector2i(ax, az))
			if a == null: continue
			for q in range(0, a.size(), 2):
				var r = roads[a[q]]; var i: int = a[q + 1]; var p: PackedFloat32Array = r.p
				var x0 = p[i * 3]; var z0 = p[i * 3 + 2]; var dx = p[i * 3 + 3] - x0; var dz = p[i * 3 + 5] - z0; var L2 = dx * dx + dz * dz
				if L2 < 1e-6: continue
				var t = clampf(((x - x0) * dx + (z - z0) * dz) / L2, 0, 1); var px = x0 + dx * t; var pz = z0 + dz * t; var dist = Vector2(x - px, z - pz).length()
				if dist > r.hw + 4: continue
				var y = p[i * 3 + 1] + (p[i * 3 + 4] - p[i * 3 + 1]) * t; var sc = dist + 4 * maxf(0, abs(yref - y) - 2.5)
				if sc < best:
					best = sc; var L = sqrt(L2)
					out = { ok = true, r = r, i = i, t = t, y = y, tx = dx / L, tz = dz / L, d = ((x - px) * (dz / L) - (z - pz) * (dx / L)) }
	return out

# walls of bridges and tunnels, guard rails and retaining walls: keeps the car inside; returns the corrected position and velocity
func walls(nx: float, nz: float, car) -> Array:
	var q = road_query(nx, nz, car.py)
	if not q.ok or abs(car.py - q.y) > 4: return [nx, nz]
	var r = q.r; var n: int = r.n; var i: int = q.i; var j = mini(i + 1, n - 1)
	var px: float = q.tz; var pz: float = -q.tx
	if r.wall[i] or r.wall[j]:
		var lim: float = r.hw - 1.1
		if abs(q.d) > lim and abs(car.py - q.y) < 3:
			var over: float = q.d - sign(q.d) * lim; nx -= px * over; nz -= pz * over
			var vn: float = car.vx * px + car.vz * pz; car.vx -= px * vn * 1.15; car.vz -= pz * vn * 1.15; car.vx *= 0.985; car.vz *= 0.985
			if abs(vn) > 2.5: car.bump(abs(vn), "rail")
	elif r.lim != null:
		var si = 0 if q.d > 0 else 1; var lim: float = maxf(r.lim[si][i], r.lim[si][j])
		if lim > 0 and abs(q.d) > lim and abs(q.d) < lim + 3:
			var sg: float = sign(q.d); var over: float = q.d - sg * lim; nx -= px * over; nz -= pz * over
			var vn: float = (car.vx * px + car.vz * pz) * sg
			if vn > 0: car.vx -= px * sg * vn * 1.15; car.vz -= pz * sg * vn * 1.15; if vn > 2.5: car.bump(vn, "rail")
			car.vx *= 0.99; car.vz *= 0.99
	return [nx, nz]

# buildings, props and trees: three circles along the car so the bodywork does not sink into things
var traffic_vel: Callable          # traffic index -> its velocity (x, z), so a car hit at the same speed is not a wall
func obstacles(nx: float, nz: float, car) -> Array:
	var done := {}
	var R = 1.0; var hl = 1.75; var cfx = sin(car.hd); var cfz = cos(car.hd)
	for off in [hl, 0.0, -hl]:
		var sx = nx + cfx * off; var sz = nz + cfz * off
		var cell = grid.get(Vector2i(floor(sx / OG), floor(sz / OG)))
		var pushes = []
		var boxes = (dyn + dyn2) if cell == null else cell.o + dyn + dyn2
		var me = car.get_instance_id()
		for o in boxes:
			if o.size() > 5 and o[5] == me: continue
			var dx: float = sx - o[0]; var dz: float = sz - o[1]; var c = cos(o[4]); var s = sin(o[4])
			var lx = dx * c - dz * s; var ly = -dx * s - dz * c
			var ppx: float = o[2] + R - abs(lx); var ppy: float = o[3] + R - abs(ly)
			if ppx > 0 and ppy > 0:
				var who = o[5] if o.size() > 5 else null          # a moving car (traffic or racer) rather than a building
				if ppx < ppy: pushes.append([c * sign(lx), -s * sign(lx), ppx, who])
				else: pushes.append([-s * sign(ly), -c * sign(ly), ppy, who])
		if cell != null:
			for o in cell.c:
				var dx: float = sx - o[0]; var dz: float = sz - o[1]; var d = Vector2(dx, dz).length(); var pen: float = o[2] + R - d
				if pen > 0 and d > 0.01: pushes.append([dx / d, dz / d, pen, null])
			for o in cell.k:
				if not o[3] and Vector2(sx - o[0], sz - o[1]).length() < o[2] + R:
					o[3] = true; var f = 0.99 if o[2] < 0.35 else 0.95; car.vx *= f; car.vz *= f; car.knocked.emit(o)          # a plastic post barely slows the car
		for p in pushes:
			var ax: float = p[0]; var az: float = p[1]; var pen: float = p[2]
			if p[3] != null and p[3] < 0: pen = minf(pen, 0.08)          # a traffic car overlapping us: separate over a few frames, never a pop
			if p[3] != null and done.has(p[3]): nx += p[0] * pen; nz += p[1] * pen; continue          # one blow per car per frame
			nx += ax * pen; nz += az * pen; sx += ax * pen; sz += az * pen
			var vn: float = car.vx * ax + car.vz * az
			var who = p[3]
			if who != null:
				# another car of about the same weight: they share the blow (nearly inelastic), nobody bounces off a wall
				var other = instance_from_id(who) if who > 0 else null
				var ovn = 0.0
				if other: ovn = other.vx * ax + other.vz * az
				elif who < 0 and traffic_vel.is_valid(): var tv: Vector2 = traffic_vel.call(-1 - who); ovn = tv.x * ax + tv.y * az
				done[who] = true
				var rel = vn - ovn
				if rel < 0:
					var J = -rel * 0.58; car.vx += ax * J; car.vz += az * J
					var ox = cfx * off; var oz = cfz * off; var tq = (oz * ax - ox * az) * J * car.V.m
					car.yr = clampf(car.yr + tq / car.V.Iz * 0.15, -1.6, 1.6)
					if other: other.vx -= ax * J; other.vz -= az * J
					elif who < 0: hits.append([-1 - who, -ax * J, -az * J])
					if rel < -4: car.bump(-rel, "car")
			elif vn < 0:
				var J = -vn * 1.15; car.vx += ax * J; car.vz += az * J          # little bounce: crumpling bodywork takes the energy
				var ox = cfx * off; var oz = cfz * off; var tq = (oz * ax - ox * az) * J * car.V.m
				car.yr = clampf(car.yr + tq / car.V.Iz * 0.15, -1.6, 1.6)
				if vn < -6:          # a real hit: most of the speed goes, sliding along the wall is scrubbed off too
					var tx = car.vx - ax * (car.vx * ax + car.vz * az); var tz = car.vz - az * (car.vx * ax + car.vz * az)
					car.vx -= tx * 0.35; car.vz -= tz * 0.35; car.vx *= 0.65; car.vz *= 0.65
				if vn < -2.5: car.bump(-vn, "solid")          # light knocks get a light sound too
	return [nx, nz]

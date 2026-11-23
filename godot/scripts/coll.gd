extends RefCounted
class_name Coll
# obstacles and road-side walls exported from the web game; same push-out rules as its physics()
const OG = 40.0; const SG = 48.0
var grid = {}            # Vector2i -> { o = [], c = [], k = [] }
var roads = []           # { p = PackedFloat32Array, n, hw, wall, lim }
var seg = {}             # Vector2i -> [road index, segment index, ...]
var dyn = []             # moving boxes (traffic), same layout as the static boxes

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
	for o in d["knock"]: var kk = [o[0], o[1], o[2], false]; _put("k", kk, o[2] + 2)
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
			var vn: float = car.vx * px + car.vz * pz; car.vx -= px * vn * 1.2; car.vz -= pz * vn * 1.2; car.vx *= 0.985; car.vz *= 0.985
	elif r.lim != null:
		var si = 0 if q.d > 0 else 1; var lim: float = maxf(r.lim[si][i], r.lim[si][j])
		if lim > 0 and abs(q.d) > lim and abs(q.d) < lim + 3:
			var sg: float = sign(q.d); var over: float = q.d - sg * lim; nx -= px * over; nz -= pz * over
			var vn: float = (car.vx * px + car.vz * pz) * sg
			if vn > 0: car.vx -= px * sg * vn * 1.25; car.vz -= pz * sg * vn * 1.25; if vn > 6: car.bump()
			car.vx *= 0.99; car.vz *= 0.99
	return [nx, nz]

# buildings, props and trees: three circles along the car so the bodywork does not sink into things
func obstacles(nx: float, nz: float, car) -> Array:
	var R = 1.0; var hl = 1.75; var cfx = sin(car.hd); var cfz = cos(car.hd)
	for off in [hl, 0.0, -hl]:
		var sx = nx + cfx * off; var sz = nz + cfz * off
		var cell = grid.get(Vector2i(floor(sx / OG), floor(sz / OG)))
		var pushes = []
		var boxes = dyn if cell == null else cell.o + dyn
		for o in boxes:
			var dx: float = sx - o[0]; var dz: float = sz - o[1]; var c = cos(o[4]); var s = sin(o[4])
			var lx = dx * c - dz * s; var ly = -dx * s - dz * c
			var ppx: float = o[2] + R - abs(lx); var ppy: float = o[3] + R - abs(ly)
			if ppx > 0 and ppy > 0:
				if ppx < ppy: pushes.append([c * sign(lx), -s * sign(lx), ppx])
				else: pushes.append([-s * sign(ly), -c * sign(ly), ppy])
		if cell != null:
			for o in cell.c:
				var dx: float = sx - o[0]; var dz: float = sz - o[1]; var d = Vector2(dx, dz).length(); var pen: float = o[2] + R - d
				if pen > 0 and d > 0.01: pushes.append([dx / d, dz / d, pen])
			for o in cell.k:
				if not o[3] and Vector2(sx - o[0], sz - o[1]).length() < o[2] + R: o[3] = true; car.vx *= 0.94; car.vz *= 0.94; car.knocked.emit(o)
		for p in pushes:
			var ax: float = p[0]; var az: float = p[1]; var pen: float = p[2]
			nx += ax * pen; nz += az * pen; sx += ax * pen; sz += az * pen
			var vn: float = car.vx * ax + car.vz * az
			if vn < 0:
				var J = -vn * 1.3; car.vx += ax * J; car.vz += az * J
				var ox = cfx * off; var oz = cfz * off; var tq = (oz * ax - ox * az) * J * car.V.m
				car.yr = clampf(car.yr + tq / car.V.Iz * 0.3, -2.5, 2.5)
				if vn < -6: car.vx *= 0.6; car.vz *= 0.6; car.bump()
	return [nx, nz]

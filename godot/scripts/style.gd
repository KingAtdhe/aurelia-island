extends RefCounted
class_name CarStyle
# Garage styling for the player's car (Progress.U(id): rim, rimcol, wing, ride, camber, livery), applied by Car.setup:
#  - rims: five designs built here (spokes, barrel, polished lip, centre cap) over the factory tyre; the factory rim surfaces
#    are hidden. Colours from RIMCOL. 0 keeps the factory wheels.
#  - wing: 0 factory, 1 none, 2 GT wing (carbon plane, end plates, swan-neck uprights) on the rear deck
#  - ride height and camber: how the car sits (looks only; the physics stays the tuned car)
#  - livery: a second pass over the paint (shaders/livery.gdshader)
const RIMS = ["Factory", "Mono 5", "Mesh 10", "Split 6", "Turbine", "Deep dish"]
const RIMCOL = [["Silver", Color(0.78, 0.79, 0.8)], ["Gunmetal", Color(0.22, 0.23, 0.25)], ["Gloss black", Color(0.03, 0.03, 0.035)],
	["Gold", Color(0.75, 0.56, 0.2)], ["Bronze", Color(0.42, 0.28, 0.16)], ["White", Color(0.92, 0.92, 0.9)]]
const WINGS = ["Factory", "None", "GT wing"]
const RIDE = [["Stock", 0.0], ["Low", -0.02], ["Lower", -0.04], ["Slammed", -0.065]]
const CAMBER = [["Stock", 0.0], ["Street", 2.0], ["Track", 4.5], ["Stance", 8.0]]
const LIVERIES = ["None", "Twin stripes", "Side arrow", "Two-tone", "Race"]
const NUMBER = { vortex = 7, calder = 22 }
const RIM_COST = 2500; const WING_COST = 3500; const LIVERY_COST = 2000

static var _hide: ShaderMaterial
static func hidden_mat() -> ShaderMaterial:
	if _hide == null:
		_hide = ShaderMaterial.new(); var sh = Shader.new(); sh.code = "shader_type spatial;\nrender_mode unshaded, depth_draw_never;\nvoid fragment() { discard; }"; _hide.shader = sh
	return _hide

static func apply(car: Car, s: Node3D, u: Dictionary):
	var C = Car.CARS[car.car_id]
	car.ride_off = RIDE[clampi(int(u.get("ride", 0)), 0, 3)][1]
	_camber(car, CAMBER[clampi(int(u.get("camber", 0)), 0, 3)][1])
	var rim = clampi(int(u.get("rim", 0)), 0, RIMS.size() - 1)
	if rim > 0: _rims(car, rim, RIMCOL[clampi(int(u.get("rimcol", 0)), 0, RIMCOL.size() - 1)][1])
	var wing = clampi(int(u.get("wing", 0)), 0, 2)
	if wing > 0: _wing(car, s, wing)
	var lv = clampi(int(u.get("livery", 0)), 0, LIVERIES.size() - 1)
	if lv > 0: _livery(car, s, lv, C)

# ---------------------------------------------------------------- camber: a pivot above each wheel, tilting the top in
static func _camber(car: Car, deg: float):
	for w in car.wheels:
		var n: Node3D = w.n; var par: Node3D = n.get_parent()
		var piv: Node3D = par if par.name.begins_with("Camber") else null
		if piv == null:
			piv = Node3D.new(); piv.name = "Camber_" + n.name; par.add_child(piv); piv.transform = Transform3D(Basis(), n.position)
			n.reparent(piv, true)
		var side = signf(car.to_local(piv.global_position).x)          # +1 on the car's left
		var fwd: Vector3 = (piv.get_parent().global_transform.basis.inverse() * car.global_transform.basis * Vector3(0, 0, 1)).normalized()          # the car's nose, in the pivot's parent space
		piv.basis = Basis(fwd, deg_to_rad(deg) * -side) if fwd.length() > 0.5 else Basis()

# ---------------------------------------------------------------- rims
static func _rims(car: Car, design: int, col: Color):
	var R = car.V.r * 0.74; var W = 0.2
	var mat := StandardMaterial3D.new(); mat.albedo_color = col; mat.metallic = 0.85; mat.roughness = 0.24
	var lip := StandardMaterial3D.new(); lip.albedo_color = Color(0.86, 0.87, 0.88); lip.metallic = 1.0; lip.roughness = 0.1
	var cap := StandardMaterial3D.new(); cap.albedo_color = Color(0.05, 0.05, 0.055); cap.metallic = 0.6; cap.roughness = 0.3
	for w in car.wheels:
		var n: Node3D = w.n
		for mi in ([n] if n is MeshInstance3D else []) + n.find_children("*", "MeshInstance3D", true, false):
			if mi.name.begins_with("Disc") or mi.name.begins_with("Rim16"): continue
			for i in mi.mesh.get_surface_count():
				var m = mi.mesh.surface_get_material(i); var nm = m.resource_name.to_lower() if m else ""
				if nm in ["rim", "rimlip", "chrome"]: mi.set_surface_override_material(i, hidden_mat())
		var axis = Vector3.RIGHT if car.spin_axis == "x" else Vector3.BACK
		var d = car.to_local(n.global_position); var a_car = car.global_transform.basis.inverse() * (n.global_transform.basis * axis)
		var out = axis * (1.0 if signf(a_car.x) == signf(d.x) else -1.0)          # wheel-local axle direction pointing away from the car
		var mesh = _rim_mesh(design, R, W, out, mat, lip, cap)
		var r := MeshInstance3D.new(); r.name = "Rim16"; r.mesh = mesh; r.layers = 2
		var sc = n.global_transform.basis.get_scale(); r.scale = Vector3(1.0 / sc.x, 1.0 / sc.y, 1.0 / sc.z)
		n.add_child(r)

# a rim in wheel space: axle along `out`, the face toward `out`
static func _rim_mesh(design: int, R: float, W: float, out: Vector3, mat, lip, cap) -> ArrayMesh:
	var b = _basis(out)          # x, y span the wheel face, z = out
	var st := { m = SurfaceTool.new(), l = SurfaceTool.new(), c = SurfaceTool.new() }
	for k in st: st[k].begin(Mesh.PRIMITIVE_TRIANGLES)
	var face = W * 0.45; var dish = 0.07 if design == 5 else 0.0
	_ring(st.m, b, R * 0.96, R * 0.96, face - W, face - 0.02, 32, false)            # barrel
	_ring(st.l, b, R, R * (0.86 if design == 5 else 0.93), face, face, 32, true)       # polished lip face
	_ring(st.l, b, R, R, face - 0.02, face, 32, false)
	var spokes = { 1: [5, 0.32, 0.0, 1], 2: [10, 0.1, 0.25, 2], 3: [6, 0.1, 0.0, 2], 4: [12, 0.07, 0.6, 1], 5: [8, 0.14, 0.0, 1] }[design]
	var hub = R * 0.27
	for k in spokes[0]:
		var ang = TAU * k / spokes[0]
		for t in spokes[3]:
			var off = 0.0 if spokes[3] == 1 else (t - 0.5) * 0.16
			_spoke(st.m, b, ang + off, hub, R * 0.9, R * spokes[1] * (1.0 if spokes[3] == 1 else 0.8), face - 0.025 - dish, face - 0.025, spokes[2], design == 2 and t == 1)
	_disc(st.c, b, hub * 1.05, face - 0.01 - dish, 20)          # centre cap
	_disc(st.m, b, hub * 1.25, face - 0.03 - dish, 20)
	var am := ArrayMesh.new()
	for k in [["m", mat], ["l", lip], ["c", cap]]:
		st[k[0]].generate_normals(); am = st[k[0]].commit(am); am.surface_set_material(am.get_surface_count() - 1, k[1])
	return am

static func _basis(out: Vector3) -> Basis:
	var z = out.normalized(); var x = (Vector3.UP if abs(z.y) < 0.9 else Vector3.RIGHT).cross(z).normalized(); return Basis(x, z.cross(x), z)
static func _p(b: Basis, r: float, a: float, z: float) -> Vector3: return b.x * (cos(a) * r) + b.y * (sin(a) * r) + b.z * z
static func _quad(s: SurfaceTool, a: Vector3, b2: Vector3, c: Vector3, d: Vector3):
	for v in [a, b2, c, a, c, d]: s.add_vertex(v)
	for v in [a, c, b2, a, d, c]: s.add_vertex(v)          # both sides: rims are seen from any angle
static func _ring(s: SurfaceTool, b: Basis, r0: float, r1: float, z0: float, z1: float, n: int, flat: bool):
	for k in n:
		var a0 = TAU * k / n; var a1 = TAU * (k + 1) / n
		_quad(s, _p(b, r0, a0, z0), _p(b, r0, a1, z0), _p(b, r1, a1, z1), _p(b, r1, a0, z1))
static func _disc(s: SurfaceTool, b: Basis, r: float, z: float, n: int):
	for k in n:
		var a0 = TAU * k / n; var a1 = TAU * (k + 1) / n
		for v in [b.z * z, _p(b, r, a0, z), _p(b, r, a1, z), b.z * z, _p(b, r, a1, z), _p(b, r, a0, z)]: s.add_vertex(v)
static func _spoke(s: SurfaceTool, b: Basis, ang: float, r0: float, r1: float, wdt: float, z0: float, z1: float, twist: float, cross: bool):
	var a_in = ang; var a_out = ang + twist * 0.5 + (0.32 if cross else 0.0)
	var w0 = wdt * 0.8 / max(r0, 0.01); var w1 = wdt * 0.55 / max(r1, 0.01)
	var A = _p(b, r0, a_in - w0, z1); var B2 = _p(b, r0, a_in + w0, z1); var Cc = _p(b, r1, a_out + w1, z1 - 0.01); var D = _p(b, r1, a_out - w1, z1 - 0.01)
	var dz = b.z * (z0 - z1)
	_quad(s, A, B2, Cc, D); _quad(s, A + dz, D + dz, Cc + dz, B2 + dz)
	_quad(s, A, D, D + dz, A + dz); _quad(s, B2, B2 + dz, Cc + dz, Cc)

# ---------------------------------------------------------------- wing
static func _wing(car: Car, s: Node3D, mode: int):
	var sp: Node3D = s.find_child("Spoiler", true, false); var mount: Node3D = s.find_child("Spoiler_Mount", true, false)
	var top := Vector3(0, 1.05, -car.V.b - 0.85)
	if sp:
		var bb = _aabb_in(car, sp); top = Vector3(0, bb.end.y, bb.get_center().z)
		sp.visible = false
	if mount: mount.visible = false
	if mode != 2: return
	var C = Car.CARS[car.car_id]; var hw = C.half.y * 0.86
	var carbon := StandardMaterial3D.new(); carbon.albedo_color = Color(0.035, 0.035, 0.04); carbon.metallic = 0.3; carbon.roughness = 0.28; carbon.clearcoat_enabled = true; carbon.clearcoat = 1.0
	var root := Node3D.new(); root.name = "GTWing"; car.body.add_child(root); root.position = car.body.to_local(car.to_global(top + Vector3(0, 0.26, 0.05)))
	var parts = [[Vector3(0, 0, 0), Vector3(hw * 2.0, 0.035, 0.34), -0.14], [Vector3(0, 0.07, -0.16), Vector3(hw * 2.0, 0.02, 0.1), -0.45]]
	for sx in [-1.0, 1.0]:
		parts.append([Vector3(sx * hw, 0.02, -0.02), Vector3(0.02, 0.24, 0.42), 0.0])          # end plates
		parts.append([Vector3(sx * hw * 0.45, -0.14, 0.06), Vector3(0.025, 0.3, 0.07), 0.3])   # uprights
	for p in parts:
		var mi := MeshInstance3D.new(); var bm := BoxMesh.new(); bm.size = p[1]; mi.mesh = bm; mi.material_override = carbon; mi.layers = 2
		mi.position = p[0]; mi.rotation.x = p[2]; root.add_child(mi)

static func _aabb_in(car: Car, n: Node3D) -> AABB:          # a node's box in the car's space
	var out := AABB(); var first = true
	for mi in ([n] if n is MeshInstance3D else []) + n.find_children("*", "MeshInstance3D", true, false):
		var xf = car.global_transform.affine_inverse() * mi.global_transform; var bb: AABB = xf * mi.get_aabb()
		out = bb if first else out.merge(bb); first = false
	return out

# ---------------------------------------------------------------- livery
static var _digits: Texture2D
static func _livery(car: Car, s: Node3D, design: int, C: Dictionary):
	if _digits == null: _digits = load("res://assets/livery_digits.png")
	var paint_col := Color(0.6, 0.1, 0.1)
	var u = Progress.U(car.car_id)
	if int(u.get("paint", 0)) > 0: paint_col = Progress.PAINTS[u.paint][1]
	var light = paint_col.get_luminance() > 0.45
	for mi in s.find_children("*", "MeshInstance3D", true, false):
		var xf: Transform3D = car.global_transform.affine_inverse() * mi.global_transform
		for i in mi.mesh.get_surface_count():
			var m = mi.get_surface_override_material(i)
			if m == null: m = mi.mesh.surface_get_material(i)
			if not (m is BaseMaterial3D and m.resource_name in C.paint): continue
			var d: BaseMaterial3D = m.duplicate()
			var lv := ShaderMaterial.new(); lv.shader = load("res://shaders/livery.gdshader"); lv.render_priority = 1
			lv.set_shader_parameter("to_car", Projection(xf)); lv.set_shader_parameter("design", design); lv.set_shader_parameter("digits", _digits)
			lv.set_shader_parameter("col_a", Color(0.05, 0.05, 0.06) if light else Color(0.95, 0.95, 0.93))
			lv.set_shader_parameter("col_b", Color(0.95, 0.95, 0.93) if light else Color(0.04, 0.04, 0.05))
			lv.set_shader_parameter("half_size", Vector3(C.half.y, 1.15, C.half.x)); lv.set_shader_parameter("number", NUMBER.get(car.car_id, 27))
			d.next_pass = lv; mi.set_surface_override_material(i, d)

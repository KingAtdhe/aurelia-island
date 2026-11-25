extends Node3D
class_name Island
# The whole of Aurelia Island, cut from the web game's map into 400 m chunks (source/godot_tools/export_chunks.py).
# Base chunks (ground, roads, water edge, far buildings, landmarks) are always loaded and carry the drive colliders;
# detail chunks (close-up buildings, street kit) stream in on a background thread around the car and go again behind it.
const DIR = "res://assets/island/"
const LOAD_R = 950.0          # detail chunks closer than this (to their box) are loaded
const DROP_R = 1250.0         # and dropped again past this
# drawing distance per map group: [begin, end] in metres (0 = from the camera / no limit)
const RANGE = {
	"Markings": [0, 320], "RoadDecals": [0, 220], "RoadDecalsStreet": [0, 220], "Skids": [0, 160], "Puddles": [0, 160], "ContactAO": [0, 260],
	"Props": [0, 330], "Shapes": [0, 420], "KitTrim": [0, 520], "ArchTrim": [0, 620], "Kerbs": [0, 500],
	"BuildingsHDModel": [0, 1150], "BuildingsLOD": [1100, 0], "Glazing": [0, 1400], "Shops": [0, 280],
}

var chunks := {}               # name -> { kind, lo: Vector2, hi: Vector2, node, state (0 none, 1 loading, 3 loaded and queued, 2 in) }
var focus := Vector3.ZERO
var _t := 0.0
var _queue := []               # loaded detail scenes waiting to be put in, one per frame
var _coll_queue := []          # [chunk node, collider scene] to add a frame later
var loaded_tris := 0
var attach_ms := []          # [chunk, ms on the main thread] for the streaming test

func load_base(spawn: Vector3):
	var idx = JSON.parse_string(FileAccess.get_file_as_string(DIR + "index.json"))
	for nm in idx["chunks"]:
		var c = idx["chunks"][nm]
		chunks[nm] = { kind = c["kind"], lo = Vector2(c["min"][0], c["min"][2]), hi = Vector2(c["max"][0], c["max"][2]), node = null, state = 0, tris = int(c["tris"]) }
	focus = spawn
	for nm in chunks:
		if chunks[nm].kind == "b" or _dist(chunks[nm]) < LOAD_R: _attach(nm, load(_path(nm)))

func _path(nm: String) -> String: return DIR + "chunks/%s.glb" % nm

func _dist(c: Dictionary) -> float:
	var p = Vector2(focus.x, focus.z); var q = p.clamp(c.lo, c.hi)
	return p.distance_to(q)

# turning parts (wind turbines, Ferris wheel, windmill sails, heliport rotor): each turns about its hub on a pivot
var spinners = []
func setup_spinners(world: Dictionary):
	for sp in world["spinners"]:
		var n: Node3D = find_child(sp["name"], true, false)
		if n == null: continue
		var pv = Node3D.new(); pv.name = "Pivot_" + sp["name"]; add_child(pv); pv.global_position = Vector3(sp["pos"][0], sp["pos"][1], sp["pos"][2])
		var gt = n.global_transform; n.get_parent().remove_child(n); pv.add_child(n); n.global_transform = gt
		var ax = { x = Vector3.RIGHT, y = Vector3.UP, z = Vector3.BACK }[sp["axis"]]
		spinners.append([pv, ax, float(sp["speed"])])
		if String(sp["name"]).begins_with("Spin_Turbine"):          # the tower is in the streamed detail (drawn to 420 m): past that a plain
			var tw := MeshInstance3D.new(); var cm := CylinderMesh.new()   # mast stands in, so the rotor never hangs in the sky on its own
			cm.top_radius = 1.25; cm.bottom_radius = 2.3; cm.height = 130.0; cm.radial_segments = 10; cm.rings = 1; cm.cap_top = false; cm.cap_bottom = false
			var tm := StandardMaterial3D.new(); tm.albedo_color = Color(0.86, 0.87, 0.86); tm.roughness = 0.6; cm.material = tm
			tw.mesh = cm; tw.name = "Mast_" + sp["name"]; add_child(tw); tw.global_position = pv.global_position + Vector3(0.0, -65.0 - 1.5, 0.0)
			tw.visibility_range_begin = 400.0; tw.visibility_range_begin_margin = 20.0; tw.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_DISABLED
			tw.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF

func _coll_path(nm: String) -> String: return DIR + "coll/%s.scn" % nm

func _attach(nm: String, scene: PackedScene, cs: PackedScene = null, deferred := false):
	var c = chunks[nm]
	if scene == null: c.state = 0; return
	var t0 = Time.get_ticks_usec()
	var n = scene.instantiate(); add_child(n); c.node = n; c.state = 2; loaded_tris += c.tris
	Look.apply(n); ranges(n)
	if c.kind == "d" and cs == null and ResourceLoader.exists(_coll_path(nm)): cs = load(_coll_path(nm))
	if cs and deferred: _coll_queue.append([n, cs])          # drive colliders prebuilt by scripts/_bake_coll.gd (shapes made on the loading thread), put in next frame
	elif cs: n.add_child(cs.instantiate())
	else: colliders(n)
	if c.kind == "d" and deferred: attach_ms.append([nm, (Time.get_ticks_usec() - t0) / 1000.0])

# detail streaming: a look round every quarter second, at most one chunk put in per frame
func _process(dt):
	for sp in spinners: sp[0].rotate(sp[1], sp[2] * dt)
	if not _coll_queue.is_empty():          # one piece of work per frame: a chunk's colliders, or the next chunk
		var q = _coll_queue.pop_front()
		if is_instance_valid(q[0]): q[0].add_child(q[1].instantiate())
	elif not _queue.is_empty():
		var q = _queue.pop_front(); var c = chunks[q[0]]
		if c.state == 3: _attach(q[0], q[1], q[2], true)
	_t -= dt
	if _t > 0: return
	_t = 0.25
	for nm in chunks:
		var c = chunks[nm]
		if c.kind != "d": continue
		var d = _dist(c)
		if c.state == 0 and d < LOAD_R:
			c.state = 1; ResourceLoader.load_threaded_request(_path(nm), "PackedScene", true)
			c.has_coll = ResourceLoader.exists(_coll_path(nm))
			if c.has_coll: ResourceLoader.load_threaded_request(_coll_path(nm), "PackedScene", true)
		elif c.state == 1:
			var st = ResourceLoader.load_threaded_get_status(_path(nm))
			var st2 = ResourceLoader.load_threaded_get_status(_coll_path(nm)) if c.has_coll else ResourceLoader.THREAD_LOAD_LOADED
			if st == ResourceLoader.THREAD_LOAD_LOADED and st2 == ResourceLoader.THREAD_LOAD_LOADED:
				var s = ResourceLoader.load_threaded_get(_path(nm)); var cs = ResourceLoader.load_threaded_get(_coll_path(nm)) if c.has_coll else null
				if d < DROP_R: _queue.append([nm, s, cs]); c.state = 3          # waiting its turn to be put in
				else: c.state = 0
			elif st == ResourceLoader.THREAD_LOAD_FAILED or st == ResourceLoader.THREAD_LOAD_INVALID_RESOURCE: c.state = 0
		elif c.state == 3 and d > DROP_R: c.state = 0
		elif c.state == 2 and d > DROP_R:
			c.node.queue_free(); c.node = null; c.state = 0; loaded_tris -= c.tris

func prime():          # load everything near the focus now (after a jump across the island)
	for nm in chunks:
		var c = chunks[nm]
		if c.kind != "d": continue
		var d = _dist(c)
		if d > DROP_R and c.state == 2: c.node.queue_free(); c.node = null; c.state = 0; loaded_tris -= c.tris
		elif d < LOAD_R and c.state != 2:
			if c.state == 1:
				ResourceLoader.load_threaded_get(_path(nm))
				if c.get("has_coll", false): ResourceLoader.load_threaded_get(_coll_path(nm))
			_attach(nm, load(_path(nm)))
	_queue.clear()

func ready_around() -> bool:          # every detail chunk near the car is in
	for nm in chunks:
		var c = chunks[nm]
		if c.kind == "d" and c.state != 2 and _dist(c) < LOAD_R * 0.6: return false
	return true

static func group_of(nm: String) -> String:
	var g = nm.get_slice("__", 0)
	return g

static func ranges(root: Node):
	for n in root.find_children("*", "GeometryInstance3D", true, false):
		var g = group_of(String(n.name))
		if g.begins_with("TerrainBlend"): (n as GeometryInstance3D).visibility_range_end = 900.0
		if OS.get_environment("HIDEGRP") != "" and g in OS.get_environment("HIDEGRP").split(","): n.visible = false   # test: look behind a group
		if not RANGE.has(g): continue
		var r = RANGE[g]; var gi := n as GeometryInstance3D
		gi.visibility_range_begin = r[0]; gi.visibility_range_end = r[1]
		gi.visibility_range_begin_margin = 20.0 if r[0] > 0 else 0.0; gi.visibility_range_end_margin = 20.0 if r[1] > 0 else 0.0
		gi.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_DISABLED

# map pieces the car drives on get a collider; its surface type rides along as metadata
static func surf_of(nm: String) -> String:
	if nm.begins_with("Road") or nm.begins_with("Bridges") or nm.begins_with("Pavement") or nm.begins_with("TerrainPave") or nm.begins_with("TunnelPortal") or nm.begins_with("StartLine"): return "road"
	if nm.begins_with("Verge"): return "dirt"
	if nm.begins_with("TerrainSand"): return "sand"
	if nm.begins_with("TerrainSnow"): return "snow"
	if nm.begins_with("Terrain__") or nm.begins_with("TerrainRock") or nm.begins_with("TerrainField") or nm.begins_with("TerrainForest") or nm.begins_with("Rocks") or nm.begins_with("Houses") or nm.begins_with("Structures") or nm.begins_with("Landmark") or nm.begins_with("TougeTerrace"): return "grass"
	return ""

static func colliders(root: Node):
	for n in root.find_children("*", "MeshInstance3D", true, false):
		var surf = surf_of(String(n.name))
		if surf == "": continue
		var sb = StaticBody3D.new(); sb.set_meta("surf", surf); var cs = CollisionShape3D.new(); cs.shape = n.mesh.create_trimesh_shape()
		sb.add_child(cs); n.add_child(sb)

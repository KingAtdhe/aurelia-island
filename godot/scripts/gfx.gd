extends RefCounted
class_name Gfx
# Graphics level, picked on the start screen and kept between runs (user://settings.cfg).
#   LOW    for older phones: 70 % render scale, no sun shadows, no bloom, no modelled grass, 60 % draw distances, 8 traffic cars
#   MEDIUM the phone default: 85 % render scale, one shadow split to 45 m, grass to 30 m, 80 % draw distances, 11 cars
#   HIGH   everything: full resolution, two shadow splits to 60 m, grass to 40 m, full draw distances, 14 cars
const NAMES = ["LOW", "MEDIUM", "HIGH"]
const SCALE = [0.7, 0.85, 1.0]
const DIST = [0.55, 0.72, 1.0]
const LOD = [8.0, 6.0, 4.0]
const GRASS = [0.0, 34.0, 52.0]          # modelled grass radius (Nov 26: further and denser on HIGH)
const CARS = [8, 11, 14]
const FAR = [1500.0, 2200.0, 3000.0]          # camera reach; thicker haze on the lower levels hides where the island ends
const FOG = [0.0011, 0.0007, 0.0005]
const CFG = "user://settings.cfg"
static var level := -1

static func get_level() -> int:
	if level < 0:
		var c = ConfigFile.new(); var d = 1 if OS.has_feature("mobile") else 2
		level = int(c.get_value("gfx", "level", d)) if c.load(CFG) == OK else d
		if OS.get_environment("GFX") != "": level = NAMES.find(OS.get_environment("GFX"))
		level = clampi(level, 0, 2)
	return level

static func set_level(l: int):
	level = clampi(l, 0, 2)
	var c = ConfigFile.new(); c.load(CFG); c.set_value("gfx", "level", level); c.save(CFG)

static func dist() -> float: return DIST[get_level()]
static func grass_r() -> float: return GRASS[get_level()]
static func cars() -> int: return CARS[get_level()]

# everything that can change while driving
static func apply(m: Node):
	var l = get_level(); var vp: Viewport = m.get_viewport()
	vp.scaling_3d_mode = Viewport.SCALING_3D_MODE_BILINEAR; vp.scaling_3d_scale = SCALE[l]
	vp.msaa_3d = [Viewport.MSAA_DISABLED, Viewport.MSAA_2X, Viewport.MSAA_4X][l]          # HIGH: cleaner edges on wires, rails and trees
	vp.mesh_lod_threshold = float(OS.get_environment("LODT")) if OS.get_environment("LODT") != "" else LOD[l]
	RenderingServer.global_shader_parameter_set("gfx_detail", 0.0 if l == 0 else 1.0)
	m.sun.shadow_enabled = l > 0
	m.sun.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_2_SPLITS if l == 2 else DirectionalLight3D.SHADOW_ORTHOGONAL
	m.sun.directional_shadow_max_distance = 60.0 if l == 2 else 45.0
	if m.environment: m.environment.glow_enabled = l > 0; m.environment.fog_density = FOG[l] * Weather.FOG_K[Weather.get_level()]
	if m.cam and not (m.get("showroom") and m.showroom.active): m.cam.far = FAR[l]
	if m.island: Island.ranges(m.island)
	if m.flora: m.flora.refresh()
	if m.grass: m.grass.set_radius(grass_r())

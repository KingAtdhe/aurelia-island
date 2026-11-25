extends RefCounted
class_name Tod
# Time of day: DAY, SUNSET, NIGHT (start screen button, kept in user://settings.cfg next to the graphics level).
# Swaps the sky (assets/sky*.png), moves and colours the sun (the moon at night), sets ambient light, haze and exposure,
# fades the baked sun shadows (global shader value tod_sunbake), and lights the city (tod_night): windows, shop rooms,
# signs, neon, street lamps, car head and tail lights.
const NAMES = ["DAY", "SUNSET", "NIGHT"]
const SKY = ["res://assets/sky.png", "res://assets/sky_sunset.png", "res://assets/sky_night.png"]
const SUN_DIR = [Vector3(-0.452, 0.616, 0.646), Vector3(-0.735, 0.075, 0.674), Vector3(0.55, 0.70, -0.45)]   # towards the sun / moon (sky.py, sky_tod.py)
const SUN_COL = [Color(1.0, 0.95, 0.86), Color(1.0, 0.6, 0.34), Color(0.6, 0.7, 0.95)]
const SUN_E = [1.35, 1.25, 0.6]
const AMB_E = [0.75, 0.62, 1.5]
const AMB_SKY = [1.0, 1.0, 0.0]          # at night the dark sky gives no fill: moonlit blue instead
const AMB_COL = [Color(1, 1, 1), Color(1, 1, 1), Color(0.24, 0.3, 0.46)]
const SKY_E = [1.0, 1.0, 1.0]
const EXPO = [1.0, 1.08, 1.7]
const FOG = [Color(0.72, 0.8, 0.88), Color(0.86, 0.64, 0.52), Color(0.05, 0.07, 0.11)]
const SUNBAKE = [1.0, 0.3, 0.0]
const NIGHT = [0.0, 0.35, 1.0]
const CFG = "user://settings.cfg"
# materials that glow: name -> [energy by day, energy at night]
const EMIT = { "KitShopInterior": [0.35, 1.0], "KitShopSign": [0.0, 0.9], "HeroSigns": [0.0, 0.8], "KitNeon": [0.25, 2.2], "KitAds": [0.0, 0.8], "KitLens": [0.0, 2.5] }
const HEAD = ["head", "Light_White", "Lamp", "LED", "LampLens"]
const TAIL = ["tail", "Light_Red", "Tail", "TailLED", "redlens"]
static var level := -1
static var mats := []          # [material, day energy, night energy]
static var _car_mats := {}     # original material -> lit copy

static func get_level() -> int:
	if level < 0:
		var c = ConfigFile.new(); level = int(c.get_value("tod", "level", 0)) if c.load(CFG) == OK else 0
		if OS.get_environment("TOD") != "": level = NAMES.find(OS.get_environment("TOD"))
		level = clampi(level, 0, 2)
	return level

static func set_level(l: int):
	level = clampi(l, 0, 2)
	var c = ConfigFile.new(); c.load(CFG); c.set_value("tod", "level", level); c.save(CFG)

const SKY_RAIN = ["res://assets/sky_rain.png", "res://assets/sky_rain.png", "res://assets/sky_rain_night.png"]
const SKY_RAIN_E = [1.0, 0.62, 1.0]
const FOG_RAIN = [Color(0.62, 0.65, 0.68), Color(0.5, 0.46, 0.45), Color(0.04, 0.045, 0.055)]
static func night() -> float: return NIGHT[get_level()]
static func sun_e() -> float: return SUN_E[get_level()] * Weather.SUN_K[Weather.get_level()]
static func amb_e() -> float: return AMB_E[get_level()] * Weather.AMB_K[Weather.get_level()]
static func sky_e() -> float: return SKY_RAIN_E[get_level()] if Weather.get_level() > 0 else SKY_E[get_level()]
static func expo() -> float: return EXPO[get_level()]

static func _energy(e: Array) -> float: return lerpf(e[0], e[1], night())

# a map material that glows (shop rooms, signs, neon, ads, lamp lenses): set up once, its strength follows the time of day
static func emissive(d: BaseMaterial3D, nm: String):
	var e = EMIT[nm]; d.emission_enabled = true
	if d.albedo_texture: d.emission_texture = d.albedo_texture; d.emission = Color(1, 1, 1)
	else: d.emission = d.albedo_color
	d.emission_energy_multiplier = _energy(e); mats.append([d, e])

# head and tail lights of a car model: lit copies of its lamp materials (shared by every car using the same material)
static func light_car(root: Node):
	for mi in root.find_children("*", "MeshInstance3D", true, false):
		for i in mi.mesh.get_surface_count():
			var m = mi.get_surface_override_material(i)
			if m == null: m = mi.mesh.surface_get_material(i)
			if not (m is BaseMaterial3D): continue
			var nm: String = m.resource_name; var head = nm in HEAD; var tail = nm in TAIL
			if not (head or tail): continue
			if not _car_mats.has(m):
				var d := (m as BaseMaterial3D).duplicate() as BaseMaterial3D; d.emission_enabled = true
				d.emission = Color(1.0, 0.95, 0.85) if head else Color(1.0, 0.08, 0.05)
				var e = [0.0, 3.0] if head else [0.0, 2.2]
				d.emission_energy_multiplier = _energy(e); mats.append([d, e]); _car_mats[m] = d
			mi.set_surface_override_material(i, _car_mats[m])

static func apply(m: Node):
	var l = get_level(); var e: Environment = m.environment
	var wx = Weather.get_level()
	var sm := e.sky.sky_material as PanoramaSkyMaterial; sm.panorama = load(SKY_RAIN[l] if wx > 0 else SKY[l]); sm.energy_multiplier = sky_e()
	e.fog_light_color = FOG_RAIN[l] if wx > 0 else FOG[l]; e.ambient_light_sky_contribution = AMB_SKY[l]; e.ambient_light_color = AMB_COL[l]
	e.fog_density = Gfx.FOG[Gfx.get_level()] * Weather.FOG_K[wx]
	m.sun.shadow_opacity = 0.35 if wx > 0 else 1.0          # overcast: soft, faint shadows
	if m.weather: m.weather.apply()
	for s in [m.sun, m.car_sun]:
		s.light_color = SUN_COL[l]
		s.global_transform = Transform3D(Basis.looking_at(-SUN_DIR[l].normalized(), Vector3.UP), Vector3.ZERO)
	RenderingServer.global_shader_parameter_set("tod_night", NIGHT[l])
	RenderingServer.global_shader_parameter_set("tod_sunbake", SUNBAKE[l])
	for a in mats:
		if is_instance_valid(a[0]): a[0].emission_energy_multiplier = _energy(a[1])
	if m.lamps: m.lamps.set_on(NIGHT[l])
	if m.head: m.head.visible = l == 2; m.head.light_energy = 60.0

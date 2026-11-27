extends RefCounted
class_name Controls
# Control options (CONTROLS page on the start screen), kept in user://settings.cfg next to graphics and time of day.
#   steering     BUTTONS, TILT or TILT (REVERSED): tilt turns the phone like a wheel, zeroed when you start driving
#   sensitivity  how quickly and how far the wheels turn for an input: 60 % .. 140 %
#   assist       steering assist: catches slides, counter-steers in drifts (off: all yours)
#   traction     traction control in grip driving (off: wheelspin and power oversteer on the throttle)
#   gearbox      AUTO or MANUAL (shift buttons on the screen)
const STEER = ["BUTTONS", "TILT", "TILT (REVERSED)"]
const SENS = [0.6, 0.8, 1.0, 1.2, 1.4]
const GEARBOX = ["AUTO", "MANUAL"]
const TILT_FULL = 24.0          # degrees of tilt for full lock
const TILT_DEAD = 2.0
const CFG = "user://settings.cfg"
static var _v := {}
static var tilt_zero := 0.0

static func _rd(k: String, d):
	if not _v.has(k):
		var c = ConfigFile.new(); _v[k] = c.get_value("ctl", k, d) if c.load(CFG) == OK else d
	return _v[k]
static func _wr(k: String, v):
	_v[k] = v; var c = ConfigFile.new(); c.load(CFG); c.set_value("ctl", k, v); c.save(CFG)

static func steer() -> int: return int(_rd("steer", 0))
static func set_steer(v: int): _wr("steer", v % STEER.size())
static func sens_i() -> int: return clampi(int(_rd("sens", 2)), 0, SENS.size() - 1)
static func set_sens(i: int): _wr("sens", clampi(i, 0, SENS.size() - 1))
static func sens() -> float: return SENS[sens_i()]
static func assist() -> bool: return bool(_rd("assist", true))
static func set_assist(v: bool): _wr("assist", v)
static func traction() -> bool: return bool(_rd("tc", true))
static func set_traction(v: bool): _wr("tc", v)
static func manual() -> bool: return int(_rd("gearbox", 0)) == 1
static func set_manual(v: bool): _wr("gearbox", 1 if v else 0)

# the phone's roll in degrees from the accelerometer (screen x against gravity); Godot turns the axes with the screen
static func roll_deg() -> float:
	var a = Input.get_accelerometer()
	if a.length() < 1.0: return 0.0
	return rad_to_deg(asin(clampf(a.x / a.length(), -1.0, 1.0)))

static func zero_tilt(): tilt_zero = roll_deg()

static func tilt_steer() -> float:          # -1 (left) .. 1 (right)
	var d = roll_deg() - tilt_zero
	if steer() == 2: d = -d
	if abs(d) < TILT_DEAD: return 0.0
	return clampf((d - signf(d) * TILT_DEAD) / (TILT_FULL - TILT_DEAD), -1.0, 1.0)

# the player's car takes the driving options
static func apply(car: Car):
	car.assist = assist(); car.tc = traction(); car.sens = sens(); car.manual = manual()

const BTN = ["SMALL", "MEDIUM", "LARGE"]
const BTN_K = [0.85, 1.0, 1.2]
static func btn_i() -> int: return clampi(int(_rd("btn", 1)), 0, 2)
static func btn_scale() -> float: return BTN_K[btn_i()]
static func set_btn(i: int): _wr("btn", i % 3)
static func swap() -> bool: return bool(_rd("swap", false))          # steering buttons on the right, pedals on the left
static func set_swap(v: bool): _wr("swap", v)

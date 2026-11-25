extends RefCounted
class_name Prof
# test: time spent per system (PROF=1 prints it with the race test lines)
static var t := {}
static var on := OS.get_environment("PROF") != ""
static func add(k: String, us: int): if on: t[k] = t.get(k, 0) + us
static func report() -> String:
	var s = ""
	for k in t: s += " %s %.1f" % [k, t[k] / 1000.0]
	t = {}; return s

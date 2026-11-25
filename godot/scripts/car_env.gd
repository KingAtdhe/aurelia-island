extends Node3D
class_name CarEnv
# What the car paint reflects. The sky pictures are bright all the way down, so a car reflected light grey under the
# horizon and looked as if it floated. A reflection probe that rides with the player's car sees the sky plus a dome
# with the ground below the horizon and a hazy line of hills and trees on it: the bodywork gets the dark lower half and
# the bright horizon line real cars have. The dome is on its own render layer (only the probe sees it), so the probe
# costs a few draws once (again when the time of day or weather changes) and is then just carried along.
const LAYER = 1 << 19
const GROUND = [Color(0.075, 0.08, 0.068), Color(0.07, 0.052, 0.045), Color(0.006, 0.007, 0.01)]
const HILLS = [Color(0.17, 0.2, 0.17), Color(0.22, 0.15, 0.12), Color(0.012, 0.014, 0.02)]
var probe: ReflectionProbe
var dome: MeshInstance3D
var mat: ShaderMaterial
var car: Node3D

func _init(): name = "CarEnv"; physics_interpolation_mode = Node.PHYSICS_INTERPOLATION_MODE_OFF

func build(c: Node3D):
	car = c
	dome = MeshInstance3D.new(); var sm := SphereMesh.new(); sm.radius = 20.0; sm.height = 40.0; sm.radial_segments = 48; sm.rings = 24; dome.mesh = sm
	mat = ShaderMaterial.new(); mat.shader = load("res://shaders/car_env_dome.gdshader"); dome.material_override = mat
	dome.layers = LAYER; dome.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF; add_child(dome)
	probe = ReflectionProbe.new(); probe.size = Vector3(26.0, 14.0, 26.0); probe.max_distance = 40.0; probe.cull_mask = LAYER; probe.reflection_mask = 2          # sees only the dome (and sky); only cars (layer 2) take its reflections
	probe.update_mode = ReflectionProbe.UPDATE_ONCE; probe.ambient_mode = ReflectionProbe.AMBIENT_ENVIRONMENT; probe.blend_distance = 4.0
	probe.intensity = 1.0; add_child(probe)
	refresh()

func refresh():          # time of day or weather changed: new ground colours, the probe looks again
	var l = Tod.get_level(); var wet = Weather.get_level() > 0
	mat.set_shader_parameter("ground", GROUND[l] * (0.75 if wet else 1.0))
	mat.set_shader_parameter("hills", HILLS[l].lerp(Color(0.2, 0.21, 0.22) * (1.0 if l < 2 else 0.06), 0.45 if wet else 0.0))
	if probe: probe.update_mode = ReflectionProbe.UPDATE_ALWAYS; await get_tree().process_frame; await get_tree().process_frame; probe.update_mode = ReflectionProbe.UPDATE_ONCE

func _process(_dt):
	if car: global_position = (car as Car).vis_pos() if car is Car else car.global_position

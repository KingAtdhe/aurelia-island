shader_type spatial;
render_mode unshaded, blend_mix, depth_draw_never, cull_disabled, fog_disabled, shadows_disabled;
// rain: thin streaks in a box that travels with the camera; each instance falls and wraps round, so one MultiMesh
// (one draw) fills the air round the car. The streaks lean with the wind and stretch with the car's speed.
uniform vec3 cam = vec3(0.0);
uniform vec3 box = vec3(36.0, 22.0, 36.0);
uniform float speed = 14.0;
uniform float amount = 1.0;          // share of the instances shown (rain / storm)
uniform vec3 wind = vec3(1.2, 0.0, 0.6);
uniform vec3 col : source_color = vec3(0.75, 0.8, 0.88);
uniform float bright = 0.35;
varying float a;
float h(float n) { return fract(sin(n * 12.9898) * 43758.5453); }
void vertex() {
	float id = float(INSTANCE_ID);
	vec3 r = vec3(h(id), h(id + 17.0), h(id + 41.0));
	vec3 lo = cam - box * 0.5;
	vec3 p = lo + mod(r * box - lo, box);                                       // wraps round the camera in x and z
	p.y = lo.y + mod(r.y * box.y - TIME * speed * (0.9 + 0.2 * h(id + 5.0)) - lo.y, box.y);   // and falls through the box
	a = step(h(id + 9.0), amount);
	// streak: a thin quad along the fall direction, facing the camera sideways
	vec3 fall = normalize(vec3(-wind.x, -speed, -wind.z));
	vec3 tocam = normalize(cam - p);
	vec3 side = normalize(cross(fall, tocam)) * (0.016 + 0.0025 * length(cam - p));          // wider further out: never thinner than a pixel
	vec3 v = p + side * VERTEX.x * 2.0 + fall * (VERTEX.y + 0.5) * 0.85;
	VERTEX = (inverse(MODEL_MATRIX) * vec4(v, 1.0)).xyz;
}
void fragment() {
	if (a < 0.5) discard;
	ALBEDO = col * bright;
	ALPHA = 0.38 * (1.0 - abs(UV.x - 0.5) * 2.0) * smoothstep(0.0, 0.3, UV.y) * smoothstep(1.0, 0.7, UV.y);
}

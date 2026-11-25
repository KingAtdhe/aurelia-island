shader_type spatial;
render_mode blend_mix, depth_draw_never, cull_disabled, unshaded, shadows_disabled;
// Tyre smoke and dust puffs (scripts/tyre_fx.gd): camera-facing soft clouds, turned and stretched by per-puff data,
// a billowing edge from a noise texture, lit by a colour that follows the time of day.
uniform sampler2D noise : repeat_enable, filter_linear_mipmap;
uniform vec3 light = vec3(1.0);
varying float rot;
varying float age;
void vertex() {
	float s = length(MODEL_MATRIX[0].xyz);
	MODELVIEW_MATRIX = VIEW_MATRIX * mat4(INV_VIEW_MATRIX[0] * s, INV_VIEW_MATRIX[1] * s, INV_VIEW_MATRIX[2] * s, MODEL_MATRIX[3]);
	rot = INSTANCE_CUSTOM.r; age = INSTANCE_CUSTOM.g;
}
void fragment() {
	vec2 p = UV - 0.5;
	float c = cos(rot), sn = sin(rot);
	vec2 q = vec2(c * p.x - sn * p.y, sn * p.x + c * p.y);
	float n = texture(noise, q * 0.8 + vec2(age * 0.3, rot * 0.1)).r;
	float n2 = texture(noise, q * 1.7 - vec2(rot * 0.2, age * 0.5)).r;
	float r = length(p) * 2.0 + (n * 0.55 + n2 * 0.3 - 0.42);
	float a = smoothstep(1.0, 0.25, r);
	ALBEDO = COLOR.rgb * light * (0.82 + 0.25 * n2);
	ALPHA = COLOR.a * a;
}

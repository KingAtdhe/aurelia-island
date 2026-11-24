shader_type spatial;
render_mode cull_disabled;
// modelled grass blades: wind sway growing towards the tips, clumps grow out of the ground at the edge of the ring
// (no popping), the island light bake shades them like the ground they stand on, a little light through the blades
uniform sampler2D bake : filter_linear, repeat_disable;
uniform vec4 bake_rect = vec4(-2400.0, -1680.0, 4800.0, 3360.0);
uniform float fade_far = 40.0;
varying float shade;
varying float far_k;
void vertex() {
	vec3 org = MODEL_MATRIX[3].xyz;
	float h = clamp(VERTEX.y / 0.5, 0.0, 1.6);          // height up the blade
	float ph = dot(org.xz, vec2(0.37, 0.23));
	float gust = 0.6 + 0.4 * sin(TIME * 0.45 + org.x * 0.02);
	vec2 sway = vec2(sin(TIME * 1.9 + ph) + 0.35 * sin(TIME * 3.7 + ph * 1.9), 0.5 * cos(TIME * 1.4 + ph * 0.7)) * 0.07 * gust;
	VERTEX.xz += sway * h * h;
	float d = distance(org.xz, CAMERA_POSITION_WORLD.xz);
	VERTEX.y *= 1.0 - smoothstep(fade_far - 9.0, fade_far, d);
	far_k = smoothstep(12.0, fade_far, d);          // further out the clumps take on the ground's own green, so the ring has no edge
	vec2 uv = (org.xz - bake_rect.xy) / bake_rect.zw;
	vec2 b = texture(bake, uv).rg;
	shade = (0.34 + 0.66 * b.r) * (0.72 + 0.28 * b.g);
}
void fragment() {
	ALBEDO = mix(COLOR.rgb, vec3(0.16, 0.22, 0.09), far_k * 0.55) * shade * 1.05;
	NORMAL = normalize(mix(NORMAL, (VIEW_MATRIX * vec4(0.0, 1.0, 0.0, 0.0)).xyz, 0.65));
	ROUGHNESS = 0.85; SPECULAR = 0.2;
	BACKLIGHT = vec3(0.25, 0.3, 0.12);
}

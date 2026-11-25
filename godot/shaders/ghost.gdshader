shader_type spatial;
render_mode unshaded, depth_prepass_alpha, cull_back, shadows_disabled, fog_disabled;
// The ghost car (race.gd): a pale blue see-through copy of the best run, brighter at the edges like glass.
// depth_prepass_alpha: only the nearest surface shows, so it reads as one clean shape.
uniform float fade = 1.0;
void fragment() {
	float rim = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 2.0);
	ALBEDO = mix(vec3(0.32, 0.6, 0.95), vec3(0.75, 0.9, 1.0), rim);
	ALPHA = (0.16 + 0.5 * rim) * fade;
}

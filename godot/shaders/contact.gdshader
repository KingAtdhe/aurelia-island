shader_type spatial;
render_mode unshaded, blend_mix, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;
// the dark patch right under a car where sky light can't reach (contact shadow): without it cars looked as if they hovered
// over the road. A soft rounded rectangle, darkest under the middle and at the four tyres; multiplies what is beneath.
uniform float strength = 0.72;
uniform vec2 half = vec2(2.3, 1.0);          // car half length, half width (m); the quad is a little bigger
float rrect(vec2 p, vec2 b, float r) { vec2 q = abs(p) - b + r; return length(max(q, 0.0)) + min(max(q.x, q.y), 0.0) - r; }
void fragment() {
	vec2 p = vec2((UV.y - 0.5) * 2.0 * (half.x + 0.55), (UV.x - 0.5) * 2.0 * (half.y + 0.45));          // metres from the centre: along, across (the quad's UV.x runs across)
	float d = rrect(p, half * vec2(0.92, 0.86), 0.45);
	float a = 1.0 - smoothstep(-0.5, 0.45, d);          // soft edge
	float core = 1.0 - smoothstep(-1.4, 0.0, d);          // darker towards the middle
	vec2 w = vec2(half.x * 0.68, half.y * 0.82);          // tyre patches
	float t = 0.0;
	for (int i = 0; i < 4; i++) { vec2 c = vec2(i < 2 ? w.x : -w.x, (i % 2 == 0) ? w.y : -w.y); t = max(t, 1.0 - smoothstep(0.0, 0.55, length(p - c))); }
	float k = clamp(a * (0.55 + 0.45 * core) + 0.35 * t, 0.0, 1.0) * strength;
	ALBEDO = vec3(0.0); ALPHA = k;          // plain alpha: multiply blending went through tone mapping and greyed the whole quad
}

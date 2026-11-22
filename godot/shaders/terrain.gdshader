shader_type spatial;
// Aurelia ground: map colour (vertex colour) x photo detail, large-scale variation, side projection on steep slopes
uniform sampler2D detail : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D detail_n : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform float tscale = 0.22;      // detail repeats per metre
uniform float grassy = 1.0;       // 1 = grass/field (lush and dry patches), 0 = rock/sand
uniform float blend_layer = 0.0;  // 1 = blend fringe drawn over the base ground, alpha from UV2.x
uniform float rough = 0.92;
varying vec3 wpos; varying vec3 wnrm;
float h(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float n2(vec2 p) { vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f); return mix(mix(h(i), h(i + vec2(1, 0)), f.x), mix(h(i + vec2(0, 1)), h(i + vec2(1, 1)), f.x), f.y); }
float fbm(vec2 p) { return n2(p) * 0.55 + n2(p * 2.3 + 7.1) * 0.3 + n2(p * 5.7 + 3.3) * 0.15; }
void vertex() { wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz; wnrm = normalize(mat3(MODEL_MATRIX) * NORMAL); }
vec4 tri(sampler2D t, float s) {
	vec3 w = pow(abs(wnrm) + 0.001, vec3(4.0)); w /= (w.x + w.y + w.z);
	return texture(t, wpos.zy * s) * w.x + texture(t, wpos.xz * s) * w.y + texture(t, wpos.xy * s + 0.37) * w.z; }
void fragment() {
	float steep = 1.0 - smoothstep(0.5, 0.78, abs(wnrm.y));
	vec2 q = wpos.xz;
	vec3 d = texture(detail, q * tscale).rgb;
	vec3 d2 = texture(detail, q * tscale * 0.27 + 0.5).rgb;                 // second, larger sample hides the repeat
	d = mix(d, d * d2 * 2.0, 0.35);
	if (steep > 0.01) d = mix(d, tri(detail, tscale).rgb, steep);
	float big = fbm(q * 0.021), mid = fbm(q * 0.29), fine = n2(q * 2.3);
	vec3 base = COLOR.rgb;
	if (grassy > 0.5) {
		vec3 tint = mix(vec3(0.82, 0.9, 0.7), vec3(1.15, 1.02, 0.7), smoothstep(0.38, 0.72, big));
		tint = mix(tint, vec3(1.1, 0.95, 0.78), smoothstep(0.66, 0.88, mid) * 0.6);
		base *= tint;
	}
	ALBEDO = base * d * 1.75 * (0.9 + 0.2 * fine);
	NORMAL_MAP = texture(detail_n, q * tscale).rgb;
	NORMAL_MAP_DEPTH = 0.8;
	ROUGHNESS = rough; METALLIC = 0.0; SPECULAR = 0.3;
	if (blend_layer > 0.5) ALPHA = clamp(UV2.x, 0.0, 1.0);
}

shader_type spatial;
// asphalt and gravel shoulders: photo texture x map colour, faded stretches, tar repairs, cracks, dust
uniform sampler2D tex : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D tex_n : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform float asphalt = 1.0;
varying vec3 wpos;
uniform sampler2D bake : filter_linear_mipmap, repeat_disable;
uniform vec4 bake_rect = vec4(-1950.0, 280.0, 1300.0, 1060.0);   // x0, z0, width, depth of the baked light map
vec3 baked(vec3 c) { vec2 uv = (wpos.xz - bake_rect.xy) / bake_rect.zw; if (uv.x < 0.0 || uv.y < 0.0 || uv.x > 1.0 || uv.y > 1.0) return c;
	vec2 b = texture(bake, uv).rg; return c * (0.34 + 0.66 * b.r) * (0.72 + 0.28 * b.g); }
float h(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float n2(vec2 p) { vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f); return mix(mix(h(i), h(i + vec2(1, 0)), f.x), mix(h(i + vec2(0, 1)), h(i + vec2(1, 1)), f.x), f.y); }
float fbm(vec2 p) { return n2(p) * 0.55 + n2(p * 2.3 + 7.1) * 0.3 + n2(p * 5.7 + 3.3) * 0.15; }
void vertex() { wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz; }
void fragment() {
	vec2 q = wpos.xz; vec3 c = texture(tex, UV).rgb * COLOR.rgb * 1.9;
	float big = fbm(q * 0.02), mid = fbm(q * 0.11), fine = n2(q * 2.3), r = 0.88;
	if (asphalt > 0.5) {
		c *= mix(0.7, 1.15, big);
		float tar = smoothstep(0.58, 0.6, fbm(q * 0.09 + 13.0)) * smoothstep(0.35, 0.55, n2(q * 0.03 + 5.0));
		c = mix(c, vec3(0.05, 0.05, 0.06), tar * 0.9);
		float crack = smoothstep(0.012, 0.0, abs(n2(q * 1.3) - 0.5)) * smoothstep(0.55, 0.75, mid);
		c *= 1.0 - 0.5 * crack;
		c = mix(c, vec3(0.5, 0.47, 0.41), smoothstep(0.45, 0.8, mid) * 0.16);
		r = 0.86 + 0.08 * (big - 0.5) - 0.25 * tar;
		float l = dot(c, vec3(0.3, 0.5, 0.2)); c = mix(vec3(l), c, 0.65);           // grey, not green-tinted, and never paler than old worn asphalt
		c *= min(1.0, 0.17 / max(l, 0.001));
	} else { c *= 0.75 + 0.5 * big; }
	ALBEDO = baked(c * (0.88 + 0.24 * fine)); NORMAL_MAP = texture(tex_n, UV).rgb; NORMAL_MAP_DEPTH = 0.7; ROUGHNESS = r; SPECULAR = 0.35;
}

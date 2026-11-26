shader_type spatial;
global uniform float tod_sunbake;
global uniform float wx_wet;
global uniform float gfx_detail;          // close-up detail layers: off on LOW          // weather: rain makes the ground darker and glossy          // time of day: the baked sun shadows fade out at sunset and night
// asphalt and gravel shoulders: photo texture x map colour, faded stretches, tar repairs, cracks, dust
uniform sampler2D tex : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D tex_n : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform float asphalt = 1.0;
varying vec3 wpos;
uniform sampler2D bake : filter_linear_mipmap, repeat_disable;
uniform vec4 bake_rect = vec4(-1950.0, 280.0, 1300.0, 1060.0);   // x0, z0, width, depth of the baked light map
vec3 baked(vec3 c) { vec2 uv = (wpos.xz - bake_rect.xy) / bake_rect.zw; if (uv.x < 0.0 || uv.y < 0.0 || uv.x > 1.0 || uv.y > 1.0) return c;
	vec2 b = texture(bake, uv).rg; return c * (0.34 + 0.66 * mix(0.75, b.r, tod_sunbake)) * (0.58 + 0.42 * b.g); }          
float h(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float n2(vec2 p) { vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f); return mix(mix(h(i), h(i + vec2(1, 0)), f.x), mix(h(i + vec2(0, 1)), h(i + vec2(1, 1)), f.x), f.y); }
float fbm(vec2 p) { return n2(p) * 0.55 + n2(p * 2.3 + 7.1) * 0.3 + n2(p * 5.7 + 3.3) * 0.15; }
void vertex() { wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz; }
void fragment() {
	vec2 q = wpos.xz; vec3 c = texture(tex, UV).rgb * COLOR.rgb * 1.9;
	float near = (1.0 - smoothstep(5.0, 24.0, length(VERTEX))) * gfx_detail;          // close to the camera: the stones in the asphalt
	vec3 micro = vec3(1.0);
	if (near > 0.01) micro = mix(vec3(1.0), clamp(texture(tex, q * 0.62 + 0.17).rgb / max(vec3(0.03), textureLod(tex, q * 0.62 + 0.17, 9.0).rgb), 0.55, 1.6), near * 0.55);
	c *= micro;
	float big = fbm(q * 0.02), mid = fbm(q * 0.11), fine = n2(q * 2.3), r = 0.88;
	if (asphalt > 0.5) {
		c *= mix(0.84, 1.08, big);
		float tar = smoothstep(0.58, 0.6, fbm(q * 0.09 + 13.0)) * smoothstep(0.35, 0.55, n2(q * 0.03 + 5.0));
		c = mix(c, vec3(0.05, 0.05, 0.06), tar * 0.9);
		float crack = smoothstep(0.012, 0.0, abs(n2(q * 1.3) - 0.5)) * smoothstep(0.55, 0.75, mid);
		c *= 1.0 - 0.5 * crack;
		c = mix(c, vec3(0.5, 0.47, 0.41), smoothstep(0.45, 0.8, mid) * 0.16);
		r = 0.78 + 0.1 * (big - 0.5) - 0.2 * tar - 0.06 * (1.0 - fine);          // worn asphalt has a faint sheen at low angles
		float l = dot(c, vec3(0.3, 0.5, 0.2)); c = mix(vec3(l), c, 0.65);           // grey, not green-tinted, and never paler than old worn asphalt
		c *= min(1.0, 0.17 / max(l, 0.001));
	} else { c *= 0.75 + 0.5 * big; }
	float pool = smoothstep(0.52, 0.7, fbm(q * 0.06 + 3.1)) * wx_wet;          // wet: standing water in the low spots
	c *= mix(1.0, 0.6, wx_wet) * mix(1.0, 0.75, pool);
	ALBEDO = baked(c * (0.88 + 0.24 * fine)); vec3 nm = texture(tex_n, UV).rgb; if (near > 0.01) nm.xy = clamp(nm.xy + (texture(tex_n, q * 0.62 + 0.17).xy - 0.5) * near * 0.9, 0.0, 1.0); NORMAL_MAP = nm; NORMAL_MAP_DEPTH = mix(0.7, 0.25, wx_wet);
	ROUGHNESS = mix(mix(r, 0.22, wx_wet), 0.04, pool); SPECULAR = mix(asphalt > 0.5 ? 0.42 : 0.35, 0.7, wx_wet);
}

shader_type spatial;
render_mode blend_mix, depth_draw_opaque, cull_disabled;
// sea: deep blue to turquoise, moving ripples, sky reflection via low roughness
uniform vec3 deep : source_color = vec3(0.03, 0.2, 0.32);
uniform vec3 shallow : source_color = vec3(0.1, 0.48, 0.52);
varying vec3 wpos;
float h(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float n2(vec2 p) { vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f); return mix(mix(h(i), h(i + vec2(1, 0)), f.x), mix(h(i + vec2(0, 1)), h(i + vec2(1, 1)), f.x), f.y); }
void vertex() { wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz; }
void fragment() {
	vec2 q = wpos.xz * 0.08; float t = TIME * 0.35;
	float a = n2(q + vec2(t, t * 0.6)), b = n2(q * 2.1 - vec2(t * 0.8, t * 0.3)), c = n2(q * 5.3 + vec2(t * 1.3, -t));
	vec3 n = normalize(vec3((a - b) * 0.6 + (c - 0.5) * 0.3, 1.0, (b - c) * 0.6 + (a - 0.5) * 0.3));
	NORMAL = normalize((VIEW_MATRIX * vec4(n, 0.0)).xyz);
	ALBEDO = mix(deep, shallow, smoothstep(0.3, 0.8, a * 0.6 + b * 0.4) * 0.35);
	ROUGHNESS = 0.06; METALLIC = 0.0; SPECULAR = 0.6; ALPHA = 0.9;
}

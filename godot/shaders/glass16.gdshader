shader_type spatial;
global uniform float tod_night;
global uniform float wx_wet;
// Concept 16 curtain walls: dark tinted glass that mirrors the sky by day (stronger at grazing angles), and at night a
// scatter of lit offices behind it, one cell per bay and floor, a few of them left on late.
varying vec3 wp;
varying vec3 wn;
void vertex() { wp = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz; wn = normalize(mat3(MODEL_MATRIX) * NORMAL); }
float h(vec3 p) { return fract(sin(dot(p, vec3(12.9898, 78.233, 37.719))) * 43758.5453); }
void fragment() {
	vec3 t = normalize(cross(vec3(0.0, 1.0, 0.0), wn + vec3(1e-4)));
	float u = dot(wp, t), v = wp.y;
	vec3 cell = vec3(floor(u / 3.0), floor(v / 3.6), floor(dot(wp, wn) * 0.25));
	float r = h(cell), r2 = h(cell + 5.3);
	vec3 tint = mix(vec3(0.035, 0.045, 0.055), vec3(0.05, 0.065, 0.07), r2);          // panes differ a little
	ALBEDO = tint;
	// the reflection is drawn here, not taken from the sky picture: that one is bright below the horizon too, which turned
	// whole towers grey-white seen from the street. Up: sky blue; level and down: the street and the buildings opposite.
	vec3 V = normalize((INV_VIEW_MATRIX * vec4(VIEW, 0.0)).xyz); vec3 R = reflect(-V, wn);
	float fres = 0.12 + 0.6 * pow(1.0 - clamp(dot(V, wn), 0.0, 1.0), 4.0);
	vec3 refl = mix(vec3(0.045, 0.05, 0.055), mix(vec3(0.3, 0.42, 0.55), vec3(0.55, 0.66, 0.78), smoothstep(0.3, 0.9, R.y)), smoothstep(-0.02, 0.25, R.y));
	refl *= mix(0.85, 1.15, r2) * (1.0 - 0.9 * tod_night) * mix(1.0, 0.7, wx_wet);
	METALLIC = 0.0; ROUGHNESS = 0.08; SPECULAR = 0.12;          // a little sun glint stays
	float on = step(0.58, r) * tod_night;
	float fv = fract(v / 3.6);
	float ceiling = smoothstep(0.62, 0.95, fv);          // the office's own ceiling light, brighter near the top of the pane
	EMISSION = refl * fres + on * mix(vec3(1.0, 0.86, 0.62), vec3(0.85, 0.92, 1.0), step(0.8, r2)) * (0.6 + 1.4 * ceiling) * (0.7 + 0.6 * r2);
}

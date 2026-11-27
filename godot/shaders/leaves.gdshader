shader_type spatial;
render_mode cull_disabled;
global uniform float wx_wet;
// Concept 15 trees (twig-spray leaf cards on real branches, flora_trees15.glb + the concept 04 species already in the
// game): cut-out leaves from the foliage atlas x the tree's own tint (vertex colour x instance colour), with
//  - sun through the leaves when the light is behind them (backlight)
//  - shade inside and under the crown: cards that face down or sit low are darker
//  - a gentle sway in the wind, more at the top and the outside of the crown
uniform sampler2D tex : source_color, filter_linear_mipmap_anisotropic, repeat_disable;
uniform float lift = 1.0;          // the atlas is painted dark: brightened like the web game's LEAF_LIFT
varying float hk;
varying float vary;
void vertex() {
	vec3 org = MODEL_MATRIX[3].xyz;
	hk = clamp(VERTEX.y / 12.0, 0.0, 1.3);
	vary = fract(sin(dot(org.xz, vec2(12.9898, 78.233))) * 43758.5453);
	float s = length(MODEL_MATRIX[1].xyz);
	float sway = (0.04 + 0.05 * hk) * hk / max(s, 0.3);
	float ph = TIME * 1.3 + org.x * 0.07 + org.z * 0.05 + VERTEX.x * 0.4;
	VERTEX.x += sin(ph) * sway; VERTEX.z += cos(ph * 0.8 + VERTEX.z * 0.3) * sway * 0.7; VERTEX.y += sin(ph * 1.7) * sway * 0.25;
}
void fragment() {
	vec4 t = texture(tex, UV);
	if (t.a < 0.45) discard;
	vec3 c = t.rgb * COLOR.rgb * lift;
	c *= mix(vec3(1.0), vec3(0.94 + 0.12 * vary, 1.0, 0.92 + 0.1 * vary), 0.8);
	float down = clamp(-NORMAL.y, 0.0, 1.0);          // view space: cards turned away from the sky sit in the crown's shade
	float shade = mix(0.74, 1.0, smoothstep(0.0, 0.7, hk)) * (1.0 - 0.22 * down);
	ALBEDO = c * shade * mix(1.0, 0.82, wx_wet);
	BACKLIGHT = c * vec3(0.9, 1.0, 0.6) * 0.4;
	EMISSION = c * 0.05;          // a little sky light inside the crown (as the old leaf material)
	AO = shade; AO_LIGHT_AFFECT = 0.4;
	ROUGHNESS = 1.0; SPECULAR = mix(0.0, 0.2, wx_wet);          // no sheen: thousands of cards would turn grey-white against the sun
}

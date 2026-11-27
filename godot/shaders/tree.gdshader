shader_type spatial;
render_mode cull_disabled;
global uniform float wx_wet;
// Saba's Tripo trees (pine, oak, olive, cypress): the baked picture with depth added in the shader.
//  - inside and low down is darker: the trunk and the underside of the crown sit in the tree's own shade
//  - colour pulled from bright yellow-green towards real foliage, a little different from tree to tree
//  - light through the leaves from behind, and a slow sway in the wind (more at the top)
uniform sampler2D tex : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D tex_n : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform float has_n = 1.0;
uniform float height = 9.0;          // rough model height, for the shade from bottom to top
varying float hk;
varying float vary;
void vertex() {
	vec3 org = MODEL_MATRIX[3].xyz;
	float s = length(MODEL_MATRIX[1].xyz);
	hk = clamp(VERTEX.y / height, 0.0, 1.2);
	vary = fract(sin(dot(org.xz, vec2(12.9898, 78.233))) * 43758.5453);
	float sway = hk * hk * 0.06 / max(s, 0.3);
	VERTEX.x += sin(TIME * 1.1 + org.x * 0.07 + org.z * 0.05) * sway;
	VERTEX.z += cos(TIME * 0.9 + org.z * 0.06) * sway * 0.7;
}
void fragment() {
	vec3 c = texture(tex, UV).rgb * COLOR.rgb;
	float l = dot(c, vec3(0.3, 0.55, 0.15));
	float leaf = smoothstep(0.02, 0.12, c.g - c.r);          // green parts: foliage
	vec3 deep = c * vec3(0.78, 0.86, 0.72);                    // richer, less yellow
	c = mix(c, mix(vec3(l), deep, 1.12), leaf * 0.55);
	c *= mix(vec3(1.0), vec3(0.92 + 0.16 * vary, 1.0, 0.9 + 0.12 * vary), leaf);
	float shade = mix(0.45, 1.0, smoothstep(0.0, 0.75, hk));         // trunk and lower crown in the tree's shade
	ALBEDO = c * shade * mix(1.0, 0.8, wx_wet);
	AO = mix(0.5, 1.0, smoothstep(0.05, 0.8, hk)); AO_LIGHT_AFFECT = 0.5;
	ROUGHNESS = 0.9; SPECULAR = 0.12;
	BACKLIGHT = vec3(0.32, 0.38, 0.16) * leaf;
	if (has_n > 0.5) { NORMAL_MAP = texture(tex_n, UV).rgb; NORMAL_MAP_DEPTH = 0.8; }
}

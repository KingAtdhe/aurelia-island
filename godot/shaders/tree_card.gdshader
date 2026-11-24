shader_type spatial;
render_mode cull_disabled;
// distant trees: two crossed cards and a top card per tree from the web game's tree atlas; they fade in where the modelled trees end
uniform sampler2D atlas : source_color, filter_linear_mipmap, repeat_disable;
uniform float near_d = 390.0;
varying vec2 base;
void vertex() { base = UV2; }
void fragment() {
	if (distance(base, CAMERA_POSITION_WORLD.xz) < near_d) discard;
	vec4 t = texture(atlas, UV);
	if (t.a < 0.5) discard;
	ALBEDO = t.rgb * COLOR.rgb * vec3(1.18, 1.15, 1.05);
	ROUGHNESS = 1.0; SPECULAR = 0.15;
	BACKLIGHT = vec3(0.12, 0.16, 0.06);
}

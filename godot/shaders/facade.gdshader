shader_type spatial;
// tower and block facades (FacadeWindows / FacadeGlass): the photo texture as by day; at sunset and night the dark panes of
// the texture glow warm, each bay-and-floor cell lit or dark on its own so buildings never glow evenly (web game litWindows)
global uniform float tod_night;
uniform sampler2D tex : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D orm : filter_linear_mipmap, repeat_enable;
uniform sampler2D tex_n : hint_normal, filter_linear_mipmap, repeat_enable;
uniform float has_orm = 1.0;
uniform float has_n = 1.0;
uniform float glass = 0.0;
uniform float use_col = 1.0;
void fragment() {
	vec4 t = texture(tex, UV);
	vec3 c = t.rgb * mix(vec3(1.0), COLOR.rgb, use_col);
	ALBEDO = c;
	vec3 o = has_orm > 0.5 ? texture(orm, UV).rgb : vec3(1.0, 0.8, 0.0);
	ROUGHNESS = o.g; METALLIC = o.b;
	if (has_n > 0.5) { NORMAL_MAP = texture(tex_n, UV).rgb; }
	if (tod_night > 0.01) {
		float l = dot(t.rgb, vec3(0.333));
		float pane = glass > 0.5 ? step(l, 0.72) : step(l, 0.45);
		vec2 cl = floor(UV * (glass > 0.5 ? vec2(2.0) : vec2(8.0, 4.0)));          // finer cells than the web game: single windows, not whole bays
		float rn = fract(sin(dot(cl, vec2(12.9898, 78.233))) * 43758.5453);
		float lit = step(0.6 + 0.25 * (1.0 - tod_night), rn) * (0.45 + 0.55 * fract(rn * 7.0));
		EMISSION = pane * lit * tod_night * (glass > 0.5 ? vec3(1.0, 0.91, 0.78) * 0.45 : vec3(1.0, 0.8, 0.5) * 0.7);
	}
}

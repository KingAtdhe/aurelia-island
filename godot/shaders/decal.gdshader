shader_type spatial;
render_mode skip_vertex_transform, cull_disabled;
global uniform float tod_sunbake;
global uniform bool look3;
global uniform float wx_wet;          // weather: rain makes the ground darker and glossy          // time of day: the baked sun shadows fade out at sunset and night
// paint and decals lying on the road and ground (markings, tyre marks, puddles, contact shade, shore foam): drawn a hair
// towards the camera so they never flicker against the surface under them, and shaded by the island bake like that surface
uniform sampler2D tex : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform vec4 col : source_color = vec4(1.0);
uniform float has_tex = 1.0;
uniform float rough = 0.8;
uniform float skid = 0.0;          // 1: the map's tyre marks (white alpha mask x vertex colour)
uniform sampler2D bake : filter_linear_mipmap, repeat_disable;
uniform vec4 bake_rect = vec4(-2400.0, -1680.0, 4800.0, 3360.0);
varying vec3 wpos;
void vertex() {
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	VERTEX = (MODELVIEW_MATRIX * vec4(VERTEX, 1.0)).xyz;
	NORMAL = normalize((MODELVIEW_MATRIX * vec4(NORMAL, 0.0)).xyz);
	VERTEX = VERTEX * 0.9994 + normalize(-VERTEX) * 0.008;
}
void fragment() {
	vec4 t = has_tex > 0.5 ? texture(tex, UV) : vec4(1.0);
	vec4 c = t * col * COLOR;
	if (look3 && skid > 0.5) c.rgb = vec3(0.035, 0.034, 0.033);          // Nov 27: some marks carry pale vertex colours and read as chalk circles; rubber is near black
	vec2 uv = (wpos.xz - bake_rect.xy) / bake_rect.zw;
	vec2 b = texture(bake, uv).rg;
	ALBEDO = c.rgb * (0.34 + 0.66 * mix(0.75, b.r, tod_sunbake)) * (0.72 + 0.28 * b.g);
	//ALPHA
	ALBEDO *= mix(1.0, 0.75, wx_wet); ROUGHNESS = mix(rough, 0.2, wx_wet); SPECULAR = mix(0.3, 0.6, wx_wet);
	if (look3 && dot(c.rgb, vec3(0.33)) < 0.12) { ROUGHNESS = mix(0.92, 0.3, wx_wet); SPECULAR = mix(0.12, 0.5, wx_wet); }          // Nov 27: dry tyre rubber is matt; the sky's sheen turned black skids into pale arcs
}

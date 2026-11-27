shader_type spatial;
render_mode skip_vertex_transform, cull_disabled;
global uniform float tod_sunbake;
global uniform bool look3;
global uniform float tod_night;
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
// the player's low beam drawn in the road's own shader: the spot light never reached the asphalt in the full scene
// (Compatibility renderer), so the road ahead stayed black at night. Same cone as the headlights, falling off with distance.
global uniform vec3 head_pos;
global uniform vec3 head_dir;
global uniform float head_on;
float head_light(vec3 p) {
	if (head_on < 0.01) return 0.0;
	vec3 L = p - head_pos; float d = length(L);
	float cone = smoothstep(0.8, 0.97, dot(L / max(d, 0.01), head_dir));
	return head_on * cone * clamp(1.0 - d / 70.0, 0.0, 1.0) / (1.0 + 0.004 * d * d);
}
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
	if (look3 && dot(c.rgb, vec3(0.33)) > 0.3) { float l = dot(ALBEDO, vec3(0.3, 0.5, 0.2)); ALBEDO = mix(ALBEDO, vec3(l) * vec3(1.0, 0.98, 0.94), 0.6 * tod_night) * mix(1.0, 0.42, tod_night); }          // Nov 27: white paint glowed blue in the moonlight against black asphalt
	//ALPHA
	ALBEDO *= mix(1.0, 0.75, wx_wet); ROUGHNESS = mix(rough, 0.2, wx_wet); SPECULAR = mix(0.3, 0.6, wx_wet);
	if (look3 && dot(c.rgb, vec3(0.33)) < 0.12) { ROUGHNESS = mix(0.92, 0.3, wx_wet); SPECULAR = mix(0.12, 0.5, wx_wet); }          // Nov 27: dry tyre rubber is matt; the sky's sheen turned black skids into pale arcs
	EMISSION = ALBEDO * head_light(wpos) * 3.2;          // markings shine back in the beam
}

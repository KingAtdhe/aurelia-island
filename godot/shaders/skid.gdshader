shader_type spatial;
render_mode skip_vertex_transform, blend_mix, depth_draw_never, cull_disabled, unshaded, fog_disabled;
// Skid marks (scripts/tyre_fx.gd): rubber on the road, soft at the edges, a little uneven along the length.
// Pulled a few mm towards the camera so they never flicker against the road.
varying float w;
void vertex() {
	vec3 wp = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	w = wp.x + wp.z;
	VERTEX = (MODELVIEW_MATRIX * vec4(VERTEX, 1.0)).xyz;
	VERTEX = VERTEX * 0.9994 + normalize(-VERTEX) * 0.01;
}
float h(float x) { return fract(sin(x * 12.9898) * 43758.5453); }
void fragment() {
	float edge = smoothstep(0.0, 0.22, UV.y) * smoothstep(1.0, 0.78, UV.y);
	float grain = 0.8 + 0.2 * h(floor(w * 9.0)) * h(floor(UV.y * 6.0) + 3.0);
	ALBEDO = COLOR.rgb;
	ALPHA = COLOR.a * edge * grain;
}

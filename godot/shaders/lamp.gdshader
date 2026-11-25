shader_type spatial;
render_mode unshaded, blend_add, depth_draw_never, cull_disabled, fog_disabled;
// street lamps at night: a soft glow round each lamp head (camera-facing) and a warm pool of light on the ground under it
uniform float pool = 0.0;
uniform float on = 0.0;
uniform vec3 col : source_color = vec3(1.0, 0.78, 0.45);
void vertex() {
	if (pool < 0.5) {          // glow: the quad turns to face the camera
		MODELVIEW_MATRIX = VIEW_MATRIX * mat4(INV_VIEW_MATRIX[0], INV_VIEW_MATRIX[1], INV_VIEW_MATRIX[2], MODEL_MATRIX[3]);
		MODELVIEW_MATRIX = MODELVIEW_MATRIX * mat4(vec4(length(MODEL_MATRIX[0].xyz), 0.0, 0.0, 0.0), vec4(0.0, length(MODEL_MATRIX[1].xyz), 0.0, 0.0), vec4(0.0, 0.0, 1.0, 0.0), vec4(0.0, 0.0, 0.0, 1.0));
	}
}
void fragment() {
	float r = length(UV - 0.5) * 2.0;
	float a = pool > 0.5 ? pow(clamp(1.0 - r, 0.0, 1.0), 1.8) * 0.32 : (pow(clamp(1.0 - r, 0.0, 1.0), 3.0) * 0.9 + smoothstep(0.12, 0.0, r) * 1.5);
	float d = length(VERTEX);
	if (pool < 0.5) a *= clamp(1.0 - (d - 600.0) / 600.0, 0.0, 1.0); else a *= clamp(1.0 - (d - 150.0) / 80.0, 0.0, 1.0);
	ALBEDO = col * a * on;
}

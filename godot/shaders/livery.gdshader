shader_type spatial;
render_mode skip_vertex_transform, blend_mix, depth_draw_never, cull_back;
// Liveries (scripts/style.gd): drawn as a second pass over the paint, in the car's own space (nose +Z, left +X, up +Y),
// so the paint underneath keeps its flakes and clear coat. 1 twin stripes, 2 side arrow, 3 two-tone, 4 race (stripes,
// a side band and a numbered roundel on each door).
uniform mat4 to_car;          // mesh space -> car space
uniform int design = 0;
uniform vec3 col_a : source_color = vec3(1.0);          // stripes, band, roundel
uniform vec3 col_b : source_color = vec3(0.05);         // two-tone lower body, number
uniform vec3 half_size = vec3(1.0, 1.15, 2.3);           // half width, height, half length
uniform sampler2D digits : source_color, filter_linear_mipmap;
uniform int number = 27;
varying vec3 cp;
varying vec3 cn;
void vertex() {
	cp = (to_car * vec4(VERTEX, 1.0)).xyz; cn = normalize(mat3(to_car) * NORMAL);
	VERTEX = (MODELVIEW_MATRIX * vec4(VERTEX, 1.0)).xyz; NORMAL = normalize((MODELVIEW_MATRIX * vec4(NORMAL, 0.0)).xyz);
	VERTEX = VERTEX * 0.9996 + normalize(-VERTEX) * 0.002;
}
float digit(vec2 uv, int d) {          // uv 0..1 inside one digit cell
	if (uv.x < 0.0 || uv.x > 1.0 || uv.y < 0.0 || uv.y > 1.0) return 0.0;
	return texture(digits, vec2((float(d) + uv.x) / 10.0, uv.y)).a;
}
void fragment() {
	float v = cp.x / half_size.x, h = cp.y / half_size.y, u = cp.z / half_size.z;
	float top = smoothstep(0.25, 0.45, cn.y), side = smoothstep(0.45, 0.7, abs(cn.x));
	float a = 0.0; vec3 c = col_a;
	if (design == 1 || design == 4) {
		float s = smoothstep(0.065, 0.075, abs(v)) * smoothstep(0.185, 0.175, abs(v));
		a = max(a, s * top * step(abs(u), 0.995));
	}
	if (design == 2) {
		float mid = mix(0.62, 0.5, (u + 1.0) * 0.5); float wdt = mix(0.05, 0.11, smoothstep(-0.9, 0.6, u)) * step(u, 0.72);
		a = max(a, side * smoothstep(wdt, wdt - 0.01, abs(h - mid)) * step(-0.95, u));
	}
	if (design == 4) a = max(a, side * smoothstep(0.035, 0.03, abs(h - 0.42)));
	if (design == 3) { a = side * smoothstep(0.43, 0.41, h); c = col_b; }
	if (design == 4) {          // roundel with the number, on both doors
		vec2 q = vec2(u * half_size.z - 0.1, cp.y - half_size.y * 0.55) / 0.3;
		if (cp.x < 0.0) q.x = -q.x;
		float r = length(q);
		float disc = side * smoothstep(1.0, 0.96, r);
		if (disc > 0.0) {
			int d1 = number / 10, d0 = number - d1 * 10;
			vec2 g = q * vec2(0.62, -0.62) + vec2(0.5, 0.5);
			float n = digit(vec2((g.x - 0.12) * 2.6, g.y * 1.25 - 0.12), d1) + digit(vec2((g.x - 0.5) * 2.6, g.y * 1.25 - 0.12), d0);
			c = mix(col_a, col_b, clamp(n, 0.0, 1.0)); c = mix(c, col_b, smoothstep(0.84, 0.88, r) * smoothstep(0.96, 0.92, r));
			a = max(a, disc);
		}
	}
	if (a < 0.01) discard;
	ALBEDO = c; ALPHA = a; METALLIC = 0.0; ROUGHNESS = 0.22; SPECULAR = 0.6; CLEARCOAT = 1.0; CLEARCOAT_ROUGHNESS = 0.05;
}

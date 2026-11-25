shader_type sky;
// The showroom: a dark studio with soft boxes overhead, light strips round the walls and a fine horizon line.
// It is the background and, more importantly, what the car paint, glass and chrome reflect.
uniform float turn = 0.0;          // the room turns with the camera's orbit so the highlights stay framed

float sector(float az, float c, float w) { return smoothstep(w, w * 0.7, abs(mod(az - c + PI, TAU) - PI)); }

void sky() {
	vec3 d = EYEDIR;
	float y = d.y;
	float az = atan(d.x, d.z) + turn;
	float el = asin(clamp(y, -1.0, 1.0));
	vec3 col = mix(vec3(0.018, 0.02, 0.024), vec3(0.05, 0.055, 0.064), clamp(y * 0.8 + 0.3, 0.0, 1.0));
	vec3 base = col;
	if (y < 0.0) col = mix(vec3(0.03, 0.032, 0.036), vec3(0.012, 0.013, 0.015), clamp(-y * 4.0, 0.0, 1.0));      // the floor
	if (y > 0.25) {          // two big soft boxes above the turntable
		vec2 p = vec2(sin(az), cos(az)) * sqrt(1.0 - y * y) / y;
		float a = smoothstep(0.62, 0.48, abs(p.x - 0.55)) * smoothstep(1.05, 0.9, abs(p.y));
		float b = smoothstep(0.62, 0.48, abs(p.x + 0.55)) * smoothstep(1.05, 0.9, abs(p.y));
		col += vec3(2.3, 2.25, 2.2) * (a + b);
	}
	// light strips on the walls: long lines that run along the bodywork as the car turns
	float band = smoothstep(0.05, 0.08, el) * smoothstep(0.24, 0.21, el);
	col += vec3(1.5, 1.47, 1.42) * band * (sector(az, 1.15, 0.55) + sector(az, -1.15, 0.55) + 0.55 * sector(az, PI, 0.4));
	float band2 = smoothstep(0.34, 0.36, el) * smoothstep(0.42, 0.40, el);
	col += vec3(0.7) * band2 * sector(az, 0.0, 0.9);
	col += vec3(0.32) * smoothstep(0.014, 0.0, abs(el - 0.012));          // the horizon line round the room
	col += vec3(1.0, 0.62, 0.08) * 0.6 * smoothstep(0.01, 0.0, abs(el + 0.004)) * sector(az, PI * 0.5, 0.5);   // an orange accent strip, low on one side
	// seen directly the lights are dim shapes on the walls; the full brightness is only in what the car reflects
	COLOR = AT_CUBEMAP_PASS ? col : base + (col - base) * 0.07;
}

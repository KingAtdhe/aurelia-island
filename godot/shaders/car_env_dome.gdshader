shader_type spatial;
render_mode unshaded, cull_disabled, fog_disabled;
// The reflection dome round the player's car (scripts/car_env.gd): ground below the horizon, a soft band of hills and
// trees on it, nothing above (the sky shows through there).
uniform vec3 ground : source_color = vec3(0.075, 0.08, 0.068);
uniform vec3 hills : source_color = vec3(0.17, 0.2, 0.17);
varying vec3 dir;

void vertex() { dir = normalize(VERTEX); }

void fragment() {
	vec3 d = normalize(dir);
	float az = atan(d.x, d.z);
	float h = 0.035 + 0.025 * sin(az * 3.0 + 1.3) + 0.015 * sin(az * 7.0 + 0.4) + 0.008 * sin(az * 17.0);   // hill and tree line, a few degrees high
	if (d.y > h) discard;
	float band = smoothstep(h, h - 0.02, d.y);
	vec3 c = mix(hills, ground, smoothstep(0.0, -0.12, d.y));
	ALBEDO = c;
	ALPHA = band;
}

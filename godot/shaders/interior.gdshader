shader_type spatial;
render_mode cull_disabled;
// shop and office windows: a furnished room is traced behind each pane per pixel, so glass reads as glass with rooms
// behind it, not as a flat grey slab (same rooms as the browser game's interior())
global uniform float tod_night;
global uniform bool look3;
global uniform float wx_wet;
varying vec3 wp;
void vertex() { wp = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz; }
float rh(vec3 p) { return fract(sin(dot(p, vec3(12.9898, 78.233, 37.719))) * 43758.5453); }
vec3 room(vec3 P, vec3 V, vec3 N, out float lit) {
	lit = 0.0;
	if (abs(N.y) > 0.6) return vec3(0.05);
	vec3 T = normalize(cross(vec3(0.0, 1.0, 0.0), N));
	float u = dot(P, T), v = P.y, Wu = 3.7, Hv = 3.4, D = 5.5;
	vec3 d = vec3(dot(V, T), V.y, -dot(V, N)); d.z = max(d.z, 0.02);
	float cu = floor(u / Wu), cv = floor(v / Hv); vec3 id = vec3(cu, cv, floor(dot(P, N) * 0.5 + 0.5));
	float fu = u - cu * Wu, fv = v - cv * Hv;
	float tu = abs((d.x > 0.0 ? (Wu - fu) : -fu) / (abs(d.x) < 1e-4 ? 1e-4 : d.x));
	float tv = abs((d.y > 0.0 ? (Hv - fv) : -fv) / (abs(d.y) < 1e-4 ? 1e-4 : d.y));
	float tw = D / d.z;
	float t = min(tw, min(tu, tv)); vec3 h = vec3(fu, fv, 0.0) + d * t;
	float r = rh(id), r2 = rh(id + 7.1), r3 = rh(id + 3.7);
	vec3 wallC = mix(vec3(0.78, 0.74, 0.66), mix(vec3(0.62, 0.68, 0.72), vec3(0.8, 0.66, 0.55), r2), step(0.5, r));
	vec3 c;
	if (t == tv) {
		c = d.y < 0.0 ? mix(vec3(0.32, 0.22, 0.14), vec3(0.42, 0.42, 0.44), step(0.6, r3)) * (0.8 + 0.2 * step(0.5, fract(h.x * 1.6)))
			: vec3(0.85) * (0.75 + 0.6 * exp(-dot(h.xz - vec2(Wu * 0.5, D * 0.45), h.xz - vec2(Wu * 0.5, D * 0.45)) * 0.9));
	} else if (t == tw) {
		c = wallC; float sh = step(h.y, 0.9 + 0.5 * r3) * step(Wu * (0.15 + 0.3 * r), h.x) * step(h.x, Wu * (0.55 + 0.35 * r));
		c = mix(c, mix(vec3(0.18, 0.16, 0.15), vec3(0.35, 0.2, 0.14), r2), sh);
		c = mix(c, vec3(0.25, 0.3, 0.35) * (0.6 + r), step(abs(h.x - Wu * 0.5), 0.55) * step(abs(h.y - 2.0), 0.4) * step(0.5, r2));
		c *= 0.75;
	} else c = wallC * 0.88;
	c *= mix(1.0, 0.5, clamp(h.z / D, 0.0, 1.0));
	float bl = step(r3, 0.32) * step(Hv - (0.6 + 2.2 * r), fv);
	c = mix(c, vec3(0.72, 0.7, 0.64) * (0.8 + 0.2 * step(0.5, fract(fv * 9.0))), bl);
	lit = step(0.5, r) * (0.65 + 0.35 * r2);
	return c;
}
void fragment() {
	vec3 cam = (INV_VIEW_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
	vec3 V = normalize(wp - cam);
	vec3 N = normalize(cross(dFdx(wp), dFdy(wp))); if (dot(N, V) > 0.0) N = -N;
	float lt; vec3 rc = room(wp, V, N, lt);
	float cs = abs(dot(N, V)); float fr = 0.04 + 0.96 * pow(1.0 - cs, 5.0);
	vec3 day = rc * 0.5, nt = rc * lt * vec3(1.25, 1.0, 0.72) * 1.35 + rc * 0.01;
	ALBEDO = vec3(0.02, 0.025, 0.03);
	EMISSION = mix(day, nt, tod_night) * (1.0 - fr);
	if (look3) {          // Nov 27: a drawn reflection like glass16 (the sky picture is bright below the horizon): sky up high, the
		// skyline opposite as a band of darker blocks near the horizon, the street below; each pane tilted a hair differently
		vec3 T = normalize(cross(vec3(0.0, 1.0, 0.0), N + vec3(1e-4)));
		vec3 pid = vec3(floor(dot(wp, T) / 1.85), floor(wp.y / 3.4), 0.0); float pr = rh(pid), pr2 = rh(pid + 9.1);
		vec3 R = reflect(V, N); R.y += (pr - 0.5) * 0.05; R.x += (pr2 - 0.5) * 0.04;
		float az = atan(R.z, R.x) * 9.0; float bi = floor(az);
		float top = 0.04 + 0.32 * rh(vec3(bi, 1.0, 0.0)) * rh(vec3(bi, 2.0, 0.0) + 0.3);
		vec3 sky = mix(vec3(0.34, 0.45, 0.58), vec3(0.58, 0.68, 0.8), smoothstep(0.3, 0.9, R.y));
		vec3 bld = mix(vec3(0.12, 0.13, 0.14), vec3(0.24, 0.25, 0.26), rh(vec3(bi, 3.0, 0.0))) * (0.85 + 0.3 * step(0.5, fract(R.y * 40.0 + fract(az) * 3.0)));
		vec3 refl = mix(bld, sky, smoothstep(top - 0.015, top + 0.015, R.y));
		refl = mix(vec3(0.05, 0.05, 0.055), refl, smoothstep(-0.06, 0.0, R.y));
		refl *= (0.85 + 0.3 * pr2) * (1.0 - 0.92 * tod_night) * mix(1.0, 0.75, wx_wet);
		float fw = mix(0.22, 0.5, step(0.72, pr)) + 0.6 * pow(1.0 - cs, 4.0);          // some panes mirror more (tinted or blinds behind)
		fw = clamp(fw, 0.0, 0.92);
		EMISSION = mix(day, nt, tod_night) * (1.0 - fw) + refl * fw;
	}
	ROUGHNESS = 0.08; METALLIC = 0.0; SPECULAR = 0.32;
}

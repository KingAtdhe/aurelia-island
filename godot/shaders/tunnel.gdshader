shader_type spatial;
render_mode unshaded, cull_disabled;
// tunnel bores (port of the web game's tunnels): pale tiled lower walls, dark sprayed-concrete vault, warm light from the rows
// of ceiling lamps with a pulse every lamp spacing, daylight reaching in from the portals
uniform sampler2D conc : source_color, filter_linear_mipmap, repeat_enable;
uniform vec4 portals[8];
uniform int n_portals = 0;
varying vec3 w;
void vertex() { w = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz; }
void fragment() {
	vec3 wn = normalize(cross(dFdx(w), dFdy(w)));          // face normal (the bore mesh has none of its own)
	float wall = 1.0 - smoothstep(0.22, 0.42, abs(wn.y));
	vec2 uw = vec2(w.x + w.z, w.y);
	vec3 cc = texture(conc, (wall > 0.5 ? uw : w.xz) * 0.22).rgb;
	vec2 tg = fract(uw / vec2(1.2, 0.6)); float grout = step(0.965, max(tg.x, tg.y));
	vec3 tile = mix(vec3(0.80, 0.80, 0.76), vec3(0.42, 0.42, 0.40), grout) * (0.75 + 0.35 * cc.g);
	vec3 vault = cc * vec3(0.34, 0.33, 0.32);
	vec3 base = mix(vault, tile, wall);
	float pulse = 0.6 + 0.4 * pow(abs(sin((w.x + w.z) * 0.2221)), 6.0);
	float day = 0.0;
	for (int i = 0; i < n_portals; i++) day = max(day, 1.0 - smoothstep(3.0, 28.0, distance(w, portals[i].xyz)));
	vec3 light = vec3(1.0, 0.88, 0.70) * mix(0.16, 0.52, wall) * pulse + vec3(0.92, 0.96, 1.0) * day * 1.0 + vec3(0.08);
	ALBEDO = base * light;
}

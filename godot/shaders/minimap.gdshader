shader_type canvas_item;
// round minimap: the island picture turned so the car always points up, a soft rim and a dark edge
uniform sampler2D map : filter_linear_mipmap, repeat_disable;
uniform vec2 center = vec2(0.5);        // car position in map UV
uniform vec2 fwd = vec2(0.0, 1.0);      // car heading in world x/z
uniform vec2 span = vec2(0.1, 0.1);     // map UV per unit of the circle radius (x and z)
void fragment() {
	vec2 p = UV * 2.0 - 1.0; float r = length(p);
	if (r > 1.0) discard;
	vec2 right = vec2(-fwd.y, fwd.x);
	vec2 w = right * p.x + fwd * (-p.y);
	vec2 uv = center + w * span;
	vec3 c = texture(map, uv).rgb;
	if (uv.x < 0.0 || uv.y < 0.0 || uv.x > 1.0 || uv.y > 1.0) c = vec3(0.06, 0.13, 0.19);
	c *= 1.0 - 0.35 * smoothstep(0.55, 0.95, r);
	float rim = smoothstep(0.9, 0.93, r);
	c = mix(c, vec3(0.92, 0.94, 0.96), rim * 0.85);
	COLOR = vec4(c, 0.92 * (1.0 - smoothstep(0.985, 1.0, r)));
}

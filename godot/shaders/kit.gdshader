shader_type spatial;
global uniform float tod_sunbake;
global uniform float wx_wet;
global uniform float gfx_detail;          // close-up detail layers: off on LOW
// Building and street-kit surfaces (brick, plaster, concrete, stone, wood, metal, roofs): the map's photo material
// (colour x map tint, normal, roughness/metal/occlusion) plus what makes it hold up close and sit in the world:
//  - fine detail: the same pictures again at 3.7x near the camera, so a wall right next to the car stays crisp
//  - weathering: large soft stains, rain streaks down the walls, darker towards the ground
//  - occlusion: the island's baked sky light at this spot (narrow streets and courtyards are darker)
uniform sampler2D tex : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D tex_n : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D tex_orm : hint_default_white, filter_linear_mipmap_anisotropic, repeat_enable;
uniform vec4 col : source_color = vec4(1.0);
uniform float use_col = 1.0;
uniform float has_n = 1.0;
uniform float has_orm = 1.0;
uniform float rough = 1.0;
uniform float metal = 0.0;
uniform vec3 uv_scale = vec3(1.0);
uniform vec3 uv_offset = vec3(0.0);
uniform float detail_k = 1.0;          // 0 for materials that should stay clean (paint, plastic)
uniform sampler2D bake : filter_linear_mipmap, repeat_disable;
uniform vec4 bake_rect = vec4(-2400.0, -1680.0, 4800.0, 3360.0);
varying vec3 wpos;
varying vec3 wnrm;
float h(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float n2(vec2 p) { vec2 i = floor(p), f = fract(p); f = f * f * (3.0 - 2.0 * f); return mix(mix(h(i), h(i + vec2(1, 0)), f.x), mix(h(i + vec2(0, 1)), h(i + vec2(1, 1)), f.x), f.y); }
float fbm(vec2 p) { return n2(p) * 0.55 + n2(p * 2.3 + 7.1) * 0.3 + n2(p * 5.7 + 3.3) * 0.15; }
void vertex() {
	UV = UV * uv_scale.xy + uv_offset.xy;
	wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz; wnrm = normalize(mat3(MODEL_MATRIX) * NORMAL);
}
void fragment() {
	float dist = length(VERTEX);
	float near = (1.0 - smoothstep(6.0, 28.0, dist)) * detail_k * gfx_detail;
	vec3 c = texture(tex, UV).rgb;
	if (near > 0.01) {          // fine detail: the picture's own grain at a smaller scale, mean-preserving
		vec3 f = texture(tex, UV * 3.7 + 0.31).rgb;
		c *= mix(vec3(1.0), clamp(f / max(vec3(0.05), textureLod(tex, UV * 3.7 + 0.31, 8.0).rgb), 0.6, 1.5), near * 0.45);
	}
	c *= col.rgb * mix(vec3(1.0), COLOR.rgb, use_col);
	// weathering
	float wall = 1.0 - abs(wnrm.y);
	float stain = fbm(wpos.xz * 0.11 + wpos.y * 0.07);
	float streak = fbm(vec2((wpos.x + wpos.z) * 1.7, wpos.y * 0.12)) * wall;
	c *= 1.0 - 0.14 * smoothstep(0.45, 0.85, stain) * detail_k - 0.12 * smoothstep(0.55, 0.85, streak) * detail_k;
	// occlusion from the island light bake (sky seen from above this spot) and from the material's own map
	vec2 buv = (wpos.xz - bake_rect.xy) / bake_rect.zw;
	float sky = texture(bake, buv).g;
	float occ = mix(0.62, 1.0, sky);
	vec3 orm = has_orm > 0.5 ? texture(tex_orm, UV).rgb : vec3(1.0, 1.0, 1.0);
	c *= mix(1.0, 0.82, wx_wet * (0.4 + 0.6 * wall));
	ALBEDO = c * occ;
	AO = orm.r; AO_LIGHT_AFFECT = 0.6;
	ROUGHNESS = clamp((has_orm > 0.5 ? orm.g : 1.0) * rough * mix(1.0, 0.6, wx_wet), 0.04, 1.0);
	METALLIC = (has_orm > 0.5 ? orm.b : 1.0) * metal;
	SPECULAR = 0.5;
	if (has_n > 0.5) {
		vec3 nm = texture(tex_n, UV).rgb;
		if (near > 0.01) { vec3 nf = texture(tex_n, UV * 3.7 + 0.31).rgb; nm.xy = clamp(nm.xy + (nf.xy - 0.5) * near * 0.8, 0.0, 1.0); }
		NORMAL_MAP = nm; NORMAL_MAP_DEPTH = 1.15;
	}
}

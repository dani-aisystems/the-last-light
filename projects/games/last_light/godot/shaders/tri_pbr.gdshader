shader_type spatial;
// World-space triplanar PBR for CC0 scans, graded into THE LAST LIGHT's palette.
// desat/tint re-colour the scan (e.g. green painted concrete -> weathered grey), wetness darkens
// albedo and lowers roughness (rain-soaked rock / condensation), grime adds a height-based dirt band.

uniform sampler2D albedo_tex : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D normal_tex : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D rough_tex : hint_roughness_r, filter_linear_mipmap_anisotropic, repeat_enable;
uniform float scale = 0.5;            // texture repeats per metre
uniform vec3 tint : source_color = vec3(1.0);
uniform float desat : hint_range(0.0, 1.0) = 0.0;
uniform float brightness = 1.0;
uniform float contrast = 1.0;
uniform float rough_mul = 1.0;
uniform float rough_add = 0.0;
uniform float metallic_v : hint_range(0.0, 1.0) = 0.0;
uniform float normal_strength = 1.0;
uniform float wetness : hint_range(0.0, 1.0) = 0.0;
uniform float grime_base_y = 20.0;    // world-space floor height for the dirt band
uniform float grime_height = 0.6;     // band height above grime_base_y
uniform float grime_amount : hint_range(0.0, 1.0) = 0.0;
uniform float blend_sharpness = 4.0;
// G6d weathering for the tower (0 = off, the default for every other material). Coordinates are round the
// tower axis (world origin): u = arc length round the wall, y = height.
uniform float streaks : hint_range(0.0, 1.0) = 0.0;   // vertical rain streaks (darker, glossier)
uniform float streak_density = 1.7;                   // streak columns per metre of wall
uniform float salt : hint_range(0.0, 1.0) = 0.0;      // salt bloom, strongest at the foot
uniform float salt_top_y = 7.5;                       // fades out by this height
uniform float rust_runs : hint_range(0.0, 1.0) = 0.0; // brown runs from the iron gallery down
uniform float rust_top_y = 20.0;                      // the gallery's underside

varying vec3 w_pos;

float hash21(vec2 p) {
	p = fract(p * vec2(123.34, 456.21));
	p += dot(p, p + 45.32);
	return fract(p.x * p.y);
}

float vnoise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash21(i), hash21(i + vec2(1.0, 0.0)), f.x), mix(hash21(i + vec2(0.0, 1.0)), hash21(i + vec2(1.0, 1.0)), f.x), f.y);
}
varying vec3 w_nrm;

void vertex() {
	w_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	w_nrm = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
}

vec3 grade(vec3 c) {
	float l = dot(c, vec3(0.299, 0.587, 0.114));
	c = mix(c, vec3(l), desat);
	c = (c - 0.5) * contrast + 0.5;
	return clamp(c, 0.0, 1.0) * tint * brightness;
}

void fragment() {
	vec3 n = normalize(w_nrm);
	vec3 bw = pow(abs(n), vec3(blend_sharpness));
	bw /= (bw.x + bw.y + bw.z);
	vec2 uvx = w_pos.zy * scale;
	vec2 uvy = w_pos.xz * scale;
	vec2 uvz = w_pos.xy * scale;
	vec3 c = texture(albedo_tex, uvx).rgb * bw.x + texture(albedo_tex, uvy).rgb * bw.y + texture(albedo_tex, uvz).rgb * bw.z;
	float r = texture(rough_tex, uvx).r * bw.x + texture(rough_tex, uvy).r * bw.y + texture(rough_tex, uvz).r * bw.z;
	// whiteout-blended triplanar normal (world space)
	vec3 tx = texture(normal_tex, uvx).xyz * 2.0 - 1.0;
	vec3 ty = texture(normal_tex, uvy).xyz * 2.0 - 1.0;
	vec3 tz = texture(normal_tex, uvz).xyz * 2.0 - 1.0;
	tx.xy *= normal_strength; ty.xy *= normal_strength; tz.xy *= normal_strength;
	vec3 nx = vec3(tx.xy + n.zy, abs(tx.z) * n.x).zyx;
	vec3 ny = vec3(ty.xy + n.xz, abs(ty.z) * n.y).xzy;
	vec3 nz = vec3(tz.xy + n.xy, abs(tz.z) * n.z);
	vec3 wn = normalize(nx * bw.x + ny * bw.y + nz * bw.z);
	vec3 col = grade(c);
	float rough = clamp(r * rough_mul + rough_add, 0.04, 1.0);
	if (grime_amount > 0.0) {
		float g = 1.0 - smoothstep(grime_base_y, grime_base_y + grime_height, w_pos.y);
		col *= 1.0 - grime_amount * g * 0.5;
	}
	if (streaks > 0.0 || salt > 0.0 || rust_runs > 0.0) {
		float rr = max(length(w_pos.xz), 0.001);
		float u = atan(w_pos.x, w_pos.z) * rr;               // metres round the wall
		// streaks: narrow columns, broken along their length, a few heavy ones under ledges
		float col_n = vnoise(vec2(u * streak_density, 0.5)) * 0.65 + vnoise(vec2(u * streak_density * 3.1, 7.0)) * 0.35;
		float run = vnoise(vec2(u * streak_density * 1.3, w_pos.y * 0.18));
		float sm = smoothstep(0.52, 0.8, col_n) * smoothstep(0.25, 0.7, run);
		col = mix(col, col * vec3(0.62, 0.6, 0.57), streaks * sm);
		rough = mix(rough, rough * 0.55, streaks * sm);
		// rust runs: brown, from the gallery iron down a couple of metres
		float rband = smoothstep(rust_top_y - 2.8, rust_top_y - 0.2, w_pos.y) * (1.0 - smoothstep(rust_top_y, rust_top_y + 0.05, w_pos.y));
		float rm = smoothstep(0.6, 0.85, vnoise(vec2(u * 2.3, 3.0))) * rband;
		col = mix(col, vec3(0.32, 0.2, 0.12), rust_runs * rm * 0.75);
		// salt bloom: patchy pale crust near the foot
		float sb = (1.0 - smoothstep(salt_top_y - 4.0, salt_top_y, w_pos.y)) * smoothstep(0.45, 0.75, vnoise(vec2(u * 2.0, w_pos.y * 2.2)));
		col = mix(col, vec3(0.86, 0.86, 0.82), salt * sb * 0.55);
		rough = mix(rough, 0.95, salt * sb * 0.5);
	}
	col *= 1.0 - wetness * 0.45;
	rough = mix(rough, rough * 0.35, wetness);
	ALBEDO = col;
	ROUGHNESS = rough;
	METALLIC = metallic_v;
	NORMAL = normalize((VIEW_MATRIX * vec4(wn, 0.0)).xyz);
}

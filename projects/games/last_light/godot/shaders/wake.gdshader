shader_type spatial;
render_mode blend_mix, cull_disabled, depth_draw_never, shadows_disabled;   // lit: it must not glow at night
// Audit Stage E2: a vessel's wake. The ribbon is built at rest (y = 0) on the CPU from the stern's track and
// displaced here with the ocean's own Gerstner set (shaders/ocean.gdshader, same waves / storm / time_s and the
// same lagoon calming), so it lies on the drawn sea wherever the waves are. UV.x runs across the ribbon
// (0..1), UV.y is the sample's age (0 new .. 1 gone).

uniform float storm = 0.5;
uniform float time_s = 0.0;
uniform vec4 waves[6];
// Stage M (M1): wave i at full height inside wave_fade[i].x metres from the tower, gone beyond .y (as ocean.gdshader;
// ship_view2 passes OceanWaves.shader_fade_array(), which is no fade under --sea=legacy)
uniform vec2 wave_fade[6];
uniform vec3 foam_color : source_color = vec3(0.62, 0.66, 0.68);
uniform float intensity = 1.0;      // speed and fade-in from the ship
uniform float glow = 0.05;          // daylight on white water (outside.gd dawn): lit foam alone reads no brighter
                                    // than the sky-reflecting sea at the tower's grazing angle (E2 captures)
uniform float lift = 0.25;          // metres above the analytic surface: the ocean mesh (3.33 m cells) interpolates
                                    // between vertices and buried a 5 cm ribbon (E2 capture); invisible offset at the tower's angle

varying vec3 w_pos;

vec3 gerstner(vec4 w, vec3 p, float amp_mul) {
	float steep = w.z * amp_mul;
	float k = 6.2831853 / w.w;
	float c = sqrt(9.8 / k);
	vec2 d = normalize(w.xy);
	float f = k * (dot(d, p.xz) - c * time_s);
	float a = steep / k;
	return vec3(d.x * a * cos(f), a * sin(f), d.y * a * cos(f));
}

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float vnoise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	vec2 u = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1.0, 0.0)), u.x), mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), u.x), u.y);
}

void vertex() {
	vec3 p = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	float amp = mix(0.35, 1.0, storm);
	vec3 disp = vec3(0.0);
	float r = length(p.xz);         // the rest position's distance from the tower
	for (int i = 0; i < 6; i++) {
		float gain = 1.0 - smoothstep(wave_fade[i].x, wave_fade[i].y, r);
		if (gain > 0.0) {
			disp += gerstner(waves[i], p, amp * gain);
		}
	}
	disp *= mix(0.35, 1.0, smoothstep(15.0, 45.0, r));
	w_pos = p + disp;
	VERTEX = (inverse(MODEL_MATRIX) * vec4(p + disp + vec3(0.0, lift, 0.0), 1.0)).xyz;
}

void fragment() {
	float age = UV.y;
	float across = abs(UV.x * 2.0 - 1.0);
	// a turbulent centre that spreads, two brighter edges (the Kelvin arms) further back
	float n = vnoise(w_pos.xz * 0.9 + vec2(time_s * 0.3, 0.0)) * 0.6 + vnoise(w_pos.xz * 2.7 - time_s * 0.2) * 0.4;
	float core = (1.0 - smoothstep(0.45, 1.0, across)) * (1.0 - smoothstep(0.0, 0.6, age));
	float arms = smoothstep(0.55, 0.92, across) * (1.0 - smoothstep(0.92, 1.0, across)) * smoothstep(0.05, 0.3, age);
	float a = max(core, arms * 0.7) * (0.6 + 0.4 * smoothstep(0.25, 0.75, n + 0.25 * (1.0 - age)));
	a *= (1.0 - age) * (1.0 - age) * intensity;
	ALBEDO = foam_color;
	ROUGHNESS = 0.9;
	EMISSION = foam_color * glow;
	ALPHA = clamp(a, 0.0, 0.85);
}

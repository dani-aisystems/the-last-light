shader_type spatial;
render_mode cull_back, specular_schlick_ggx;
// Storm ocean: 6 Gerstner waves (amplitude follows the storm) + two scrolling detail normal maps,
// crest foam from wave steepness, shore/reef foam from a distance-field texture built from layout.json.
// OceanWaves.height_at() on the CPU uses the same wave set so ships ride the same surface.

uniform float storm = 0.5;
uniform float time_s = 0.0;
uniform vec4 waves[6];          // dir.x, dir.y, steepness, wavelength
// Stage M (M1): wave i is at full height inside wave_fade[i].x metres from the tower and gone beyond .y
// (OceanWaves.FADE; scripts/fp/sea_mesh.gd's cells get too coarse for it out there). Every CPU mirror of
// this surface applies the same gain: OceanWaves.height_at, ship_view2, wake.gdshader.
uniform vec2 wave_fade[6];
uniform vec3 deep_color : source_color = vec3(0.012, 0.03, 0.045);
uniform vec3 shallow_color : source_color = vec3(0.03, 0.075, 0.085);
uniform vec3 foam_color : source_color = vec3(0.62, 0.66, 0.68);
uniform sampler2D detail_a : hint_normal, filter_linear_mipmap, repeat_enable;
uniform sampler2D detail_b : hint_normal, filter_linear_mipmap, repeat_enable;
uniform sampler2D foam_noise : filter_linear_mipmap, repeat_enable;
uniform sampler2D shore_field : filter_linear;     // R = foam proximity (1 at rocks, 0 at 11 m), G = the same
                                                   // over outside.SHELF_M (48 m, E3); mapped over field_rect
uniform vec4 field_rect = vec4(-260.0, -260.0, 520.0, 520.0);
uniform float flash = 0.0;
// Stage E (E3): the sea's look, one level per feature so each can be captured and benched on its own
// (--seafx=<n>, outside.gd). 0 is the pre-E3 fragment unchanged; each level adds to the one below it:
// 1 storm whitecaps, 2 shore and reef foam (field G), 3 shelf depth tint, 4 night palette, 5 far-sea floor.
uniform int seafx = 5;
uniform float whitecap_gain = 1.0;            // E3 level 1: whitecap coverage scale (0 turns them off)
uniform vec3 shelf_color : source_color = vec3(0.075, 0.17, 0.145);   // E3 level 3: water over the rock shelf
uniform float night = 0.0;                    // E3 level 4: 1 at full night, 0 at dawn (outside.gd, every frame)
uniform float night_depth = 1.0;              // E3 level 4: how far the night palette goes (0 = none)
uniform float far_rough = 0.5;                // E3 level 5: roughness floor reached beyond ~700 m
uniform float far_normal = 1.2;               // E3 level 5: strength of the broad far-sea detail normal

varying vec3 w_pos;
varying float crest;

vec3 gerstner(vec4 w, vec3 p, float amp_mul, inout vec3 tangent, inout vec3 binormal) {
	float steep = w.z * amp_mul;
	float k = 6.2831853 / w.w;
	float c = sqrt(9.8 / k);
	vec2 d = normalize(w.xy);
	float f = k * (dot(d, p.xz) - c * time_s);
	float a = steep / k;
	tangent += vec3(-d.x * d.x * steep * sin(f), d.x * steep * cos(f), -d.x * d.y * steep * sin(f));
	binormal += vec3(-d.x * d.y * steep * sin(f), d.y * steep * cos(f), -d.y * d.y * steep * sin(f));
	return vec3(d.x * a * cos(f), a * sin(f), d.y * a * cos(f));
}

void vertex() {
	vec3 p = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	vec3 tangent = vec3(1.0, 0.0, 0.0);
	vec3 binormal = vec3(0.0, 0.0, 1.0);
	float amp = mix(0.35, 1.0, storm);
	vec3 disp = vec3(0.0);
	float r = length(p.xz);         // the rest position's distance from the tower
	for (int i = 0; i < 6; i++) {
		float gain = 1.0 - smoothstep(wave_fade[i].x, wave_fade[i].y, r);
		if (gain > 0.0) {
			disp += gerstner(waves[i], p, amp * gain, tangent, binormal);
		}
	}
	// calm the water inside the lagoon / near the island so it doesn't swallow the shore
	float calm = smoothstep(15.0, 45.0, r);
	disp *= mix(0.35, 1.0, calm);
	VERTEX += disp;
	w_pos = p + disp;
	NORMAL = normalize(cross(binormal, tangent));
	crest = clamp(disp.y / (1.2 * amp + 0.01), 0.0, 1.0);
}

void fragment() {
	vec2 uv = w_pos.xz;
	vec3 na = texture(detail_a, uv * 0.045 + vec2(time_s * 0.012, time_s * 0.007)).xyz * 2.0 - 1.0;
	vec3 nb = texture(detail_b, uv * 0.11 - vec2(time_s * 0.02, -time_s * 0.015)).xyz * 2.0 - 1.0;
	float r_t = length(w_pos.xz);               // metres from the tower
	vec2 dxy = (na.xy + nb.xy) * (0.35 + 0.45 * storm);
	if (seafx >= 5) {
		// E3 level 5 (Stage M's H7 item): beyond the short waves' fade the surface went flat and mirrored the
		// dawn sky between the swell's crests in pale, sharp-edged patches. A broad detail normal (~10 m
		// features, still resolved at a kilometre through the binoculars) keeps some slope out there.
		vec3 nf = texture(detail_a, uv * 0.006 + vec2(time_s * 0.002, time_s * 0.0013)).xyz * 2.0 - 1.0;
		dxy += nf.xy * far_normal * (0.6 + 0.4 * storm) * smoothstep(300.0, 700.0, r_t);
	}
	vec3 dn = normalize(vec3(dxy, 1.0));
	NORMAL_MAP = dn * 0.5 + 0.5;
	NORMAL_MAP_DEPTH = 1.0;
	vec2 fuv = (w_pos.xz - field_rect.xy) / field_rect.zw;
	float shore = texture(shore_field, fuv).r;
	float n1 = texture(foam_noise, uv * 0.06 + vec2(time_s * 0.03, 0.0)).r;
	float n2 = texture(foam_noise, uv * 0.17 - vec2(0.0, time_s * 0.05)).r;
	float crest_foam = smoothstep(0.55 - 0.25 * storm, 0.95, crest + (n1 - 0.5) * 0.5) * (0.35 + 0.65 * storm);
	// G6d stage D: surf breaking on rock, not an even halo. The field is a distance (1 at the coast, 0 at
	// 11 m out, 4 cm steps); the white water reaches 1-4 m, surging in with the swell, heavier on some
	// ledges than others (n1, ~16 m patches), torn into lace (n3), with thin old foam drifting off.
	float dist = (1.0 - shore) * 11.0;
	float n3 = texture(foam_noise, uv * 0.33 + vec2(time_s * 0.05, -time_s * 0.07)).r;
	float surge = 0.5 + 0.5 * sin(time_s * 0.85 - dist * 1.3 + n1 * 7.0);
	float reach = (0.9 + 2.6 * surge * (0.45 + 0.55 * storm)) * (0.35 + 1.3 * n1) * (0.7 + 0.6 * crest);
	// E3 level 2: the swell breaks harder on the side of a rock it runs onto. The G channel (48 m) is sampled
	// 3 m up and down the dominant swell; where the field rises downstream the water is on the exposed face.
	float shelf = 0.0;          // G: 1 at the rock, 0 at 48 m (level 2 and up)
	float exposed = 0.0;
	float lee = 0.0;
	if (seafx >= 2) {
		vec2 sd = normalize(waves[0].xy) * (3.0 / field_rect.z);
		vec2 g3 = vec2(texture(shore_field, fuv + sd).g, texture(shore_field, fuv - sd).g);
		shelf = texture(shore_field, fuv).g;
		exposed = smoothstep(0.0, 0.05, g3.x - g3.y);
		lee = smoothstep(0.0, 0.05, g3.y - g3.x);
		reach *= 1.0 + 0.6 * storm + 1.2 * exposed * storm;
	}
	float edge = exp(-dist / max(reach, 0.2));
	float surf = smoothstep(0.32, 0.72, edge * (0.45 + 0.85 * n3) + 0.25 * edge * n2);
	float lace = smoothstep(0.64, 0.8, n3 * (0.6 + 0.8 * n2)) * exp(-dist / 3.5) * 0.55;
	surf = max(surf, lace);
	if (seafx >= 2) {
		// the breaker: white water thrown up the exposed face as each crest arrives
		float burst = exposed * smoothstep(0.45, 0.85, crest + (n3 - 0.5) * 0.3) * exp(-dist / (1.5 + 5.0 * storm))
			* (0.4 + 0.6 * storm);
		// old foam drifting off to the lee, out to the 48 m reach, in torn lines
		float trail = smoothstep(0.62, 0.8, n2 * (0.6 + 0.8 * n1)) * shelf * shelf * (0.3 + 0.7 * lee)
			* (0.15 + 0.85 * storm) * 0.55;
		surf = max(surf, max(smoothstep(0.25, 0.6, burst), trail));
	}
	float foam = clamp(max(crest_foam * n2 * 1.6, surf), 0.0, 1.0);
	if (seafx >= 1) {
		// E3 level 1: open-sea whitecaps. Nothing below a moderate sea; from a fresh breeze up, breaking
		// patches on the crests (big drifting noise thresholded by a storm-driven coverage) and, in a gale,
		// long foam streaks laid along the wind (the dominant swell's direction). Calmed in the lagoon,
		// thinned with range so the far sea doesn't turn to an even grey sheet once the noise mips average.
		float ws = smoothstep(0.32, 1.0, storm) * whitecap_gain;
		if (ws > 0.0) {
			vec2 wd = normalize(waves[0].xy);
			vec2 wa = vec2(dot(uv, wd), dot(uv, vec2(-wd.y, wd.x)));     // along / across the wind
			// foam_noise is fBm centred on 0.5 with a spread of about 0.12, so thresholds are set as
			// 0.5 + z * 0.12 for a target coverage: about 4 % of the sea at storm 0.55, 18 % in a full storm.
			float big = texture(foam_noise, uv * 0.011 + wd * time_s * 0.004).r;
			float brk = texture(foam_noise, uv * 0.047 - wd * time_s * 0.02).r;
			float pat = big * 0.6 + brk * 0.4 + (crest - 0.45) * 0.3;
			float thr = 0.5 + 0.12 * mix(2.3, 0.55, sqrt(ws));
			float capm = smoothstep(thr, thr + 0.035, pat) * (0.75 + 0.25 * smoothstep(0.35, 0.65, n3));
			// gale streaks: soft lanes about 1.3 m wide and 13 m long, gathered where the big patches are and
			// broken into lengths by a rounder noise (a stretched blob alone gives a straight-edged bar)
			float streak = texture(foam_noise, vec2(wa.x * 0.006, wa.y * 0.06) + vec2(time_s * 0.004, 0.0)).r;
			float lane = smoothstep(0.45, 0.6, big);
			float sthr = 0.5 + 0.12 * mix(2.2, 1.1, smoothstep(0.55, 1.0, storm));
			float streaks = smoothstep(sthr, sthr + 0.09, streak) * lane * smoothstep(0.55, 1.0, storm)
				* smoothstep(0.42, 0.62, n1) * (0.6 + 0.4 * n3);
			float wc = max(capm, streaks * 0.45);
			wc *= smoothstep(15.0, 45.0, r_t) * (1.0 - smoothstep(700.0, 1600.0, r_t) * 0.7);
			foam = max(foam, clamp(wc, 0.0, 1.0));
		}
	}
	float fres = pow(1.0 - clamp(dot(NORMAL, VIEW), 0.0, 1.0), 4.0);
	vec3 water = mix(deep_color, shallow_color, crest * 0.6 + exp(-dist / 4.0) * 0.4);
	if (seafx >= 3) {
		// E3 level 3: depth tint. No seabed exists, so the 48 m field stands in for the shelf round the island
		// and the reefs: cold green-grey over the rock, hidden by stirred-up water as the storm builds.
		water = mix(water, shelf_color, shelf * shelf * (0.85 - 0.45 * storm));
	}
	vec3 fcol = foam_color;
	float spec = 0.6;
	if (seafx >= 4) {
		// E3 level 4: the night palette. The water darkens and cools, the foam dims a little (it is what
		// shows the sea at night, so it keeps most of its light), the sheen drops. The fresnel glow below is
		// untouched, so the far sea still meets the Stage M fog at the horizon.
		float nk = clamp(night * night_depth, 0.0, 1.0);
		water *= mix(vec3(1.0), vec3(0.45, 0.5, 0.62), nk);
		fcol *= mix(1.0, 0.8, nk);
		spec = mix(0.6, 0.42, nk);
	}
	ALBEDO = mix(water, fcol, foam);
	ROUGHNESS = mix(0.06 + 0.1 * storm, 0.85, foam);
	if (seafx >= 5) {
		// and a roughness floor with range, so what reflection is left blurs instead of edging
		ROUGHNESS = max(ROUGHNESS, far_rough * smoothstep(250.0, 700.0, r_t));
	}
	SPECULAR = spec;
	METALLIC = 0.0;
	EMISSION = vec3(0.08, 0.1, 0.14) * fres * (0.25 + 3.0 * flash) * (1.0 - foam);
}

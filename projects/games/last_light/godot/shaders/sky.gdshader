shader_type sky;
// Night storm sky: layered scrolling cloud noise, darker overhead, a faint horizon glow,
// lightning flashes lighting the cloud bellies, and a dawn blend for the ending.

uniform sampler2D clouds : filter_linear_mipmap, repeat_enable;
uniform float storm = 0.5;
uniform float flash = 0.0;
uniform float dawn = 0.0;
uniform float time_s = 0.0;
uniform vec2 flash_dir = vec2(0.0, -1.0);
// Stage M (M2): the fog bank. The lowest few degrees fade into `murk`, the same colour the depth fog gives the
// farthest sea (scripts/fp/atmosphere.gd sets both), with an uneven top edge that drifts with the wind; below
// the horizon the sky is exactly the murk, so a pixel past the sea's rim still reads as fogged sea.
// bank = 0 is the legacy sky (--sea=legacy): no bank, the old darkening below the horizon.
uniform vec3 murk : source_color = vec3(0.15, 0.17, 0.2);
uniform float bank = 1.0;
// The volumetric fog now covers the sky as fully as the far sea (sky_affect 1.0, so they match at the horizon);
// its light is near black at night, so it darkens the cloud deck. sky_gain (Atmosphere.sky_gain) gives the sky
// above the bank back the brightness and contrast it had under the old 0.4 share; the bank and the horizon are
// not scaled, so the match holds (Daniel, 2026-11-18: "A + bring the clouds back").
uniform float sky_gain = 1.0;

void sky() {
	vec3 d = EYEDIR;
	float h = clamp(d.y, -0.2, 1.0);
	vec3 night_top = vec3(0.012, 0.016, 0.024);
	vec3 night_hor = vec3(0.05, 0.062, 0.078);
	vec3 dawn_top = vec3(0.16, 0.18, 0.22);
	vec3 dawn_hor = vec3(0.62, 0.5, 0.44);
	vec3 col = mix(mix(night_hor, night_top, smoothstep(0.0, 0.5, h)), mix(dawn_hor, dawn_top, smoothstep(0.0, 0.6, h)), dawn);
	vec2 uv = d.xz / max(d.y + 0.12, 0.05);
	float c1 = texture(clouds, uv * 0.05 + vec2(time_s * 0.004, time_s * 0.0015)).r;
	float c2 = texture(clouds, uv * 0.13 - vec2(time_s * 0.009, 0.0)).r;
	float cover = smoothstep(0.35 - 0.25 * storm, 0.85, c1 * 0.7 + c2 * 0.45);
	vec3 cloud_col = mix(vec3(0.03, 0.035, 0.045), vec3(0.4, 0.38, 0.38), dawn);
	float belly = c2 * cover;
	col = mix(col, cloud_col * (0.6 + 0.6 * c2), cover * smoothstep(-0.05, 0.15, h));
	// lightning: bright from the flash direction, through the cloud bellies
	float fd = pow(max(dot(normalize(d.xz + 0.0001), normalize(flash_dir)), 0.0), 3.0);
	col += vec3(0.55, 0.6, 0.75) * flash * (0.25 + 1.6 * belly * fd) * smoothstep(-0.05, 0.2, h);
	if (bank > 0.0) {
		// azimuth 0..1 (the texture repeats and is seamless, so whole multiples of it close the circle); lod 0,
		// because atan's jump at the back would otherwise pick a coarse mip along one line
		float az = atan(d.x, -d.z) / 6.2831853;
		float n1 = textureLod(clouds, vec2(az * 3.0 + time_s * 0.0011, 0.31), 0.0).r;
		float n2 = textureLod(clouds, vec2(az * 11.0 - time_s * 0.0023, 0.73), 0.0).r;
		// the top edge undulates slowly (1.6 to 4 degrees), never jagged: a high-frequency edge read as a
		// skyline of trees or roofs in the first captures
		float top = (0.028 + 0.03 * n1 + 0.01 * n2) * mix(1.0, 1.35, storm);    // radians: the bank's top edge
		float t = clamp(d.y / top, 0.0, 1.0);
		float n3 = textureLod(clouds, vec2(az * 7.0 + time_s * 0.003, 0.5 + t * 0.3), 0.0).r;
		float b = 1.0 - smoothstep(0.2, 1.0, t);                                 // solid at the sea, thinning up
		vec3 bank_col = murk * mix(1.0, 0.9 + 0.2 * n3, smoothstep(0.1, 0.7, t)); // slow mottling in its body
		col = mix(col * sky_gain, bank_col, b * bank);
		if (d.y < 0.0) {
			col = mix(col, murk, bank);
		}
	} else if (d.y < 0.0) {
		col = mix(col, vec3(0.02, 0.03, 0.04), clamp(-d.y * 6.0, 0.0, 1.0));
	}
	COLOR = col;
}

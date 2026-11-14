shader_type spatial;
render_mode unshaded, blend_mix, depth_draw_never, cull_disabled, shadows_disabled, skip_vertex_transform;
// G6d stage D (title only): a falling drop drawn as a motion streak. The particle's Y axis is aligned to
// its velocity (ParticleProcessMaterial align_y); the quad is turned round that axis to face the camera,
// so a slanted streak keeps its width at any angle. Far streaks never thin below about px_per_m * depth,
// so the distant layer still reads, with alpha lowered to keep the same coverage.

uniform vec4 tint : source_color = vec4(0.72, 0.78, 0.86, 0.22);
uniform float length_m = 0.7;      // streak length (about speed x a 1/24 s exposure)
uniform float width_m = 0.007;
uniform float px_per_m = 0.0016;   // minimum width per metre of depth
uniform float flash = 0.0;         // lightning lights the rain
uniform float max_len_per_m = 0.05; // a drop right by the lens never draws a streak across the frame
uniform vec2 mask_x = vec2(-2.0, -1.0);   // screen fade over the menu column (x0 -> x1 of the width) ...
uniform float mask_floor = 1.0;           // ... down to this much of the alpha

varying float v_alpha;

void vertex() {
	vec3 c = (MODELVIEW_MATRIX * vec4(0.0, 0.0, 0.0, 1.0)).xyz;
	vec3 ax = (MODELVIEW_MATRIX * vec4(0.0, 1.0, 0.0, 0.0)).xyz;
	float al = length(ax);
	ax = al > 1e-5 ? ax / al : vec3(0.0, 1.0, 0.0);
	vec3 side = cross(ax, normalize(c));
	float sl = length(side);
	side = sl > 1e-4 ? side / sl : vec3(1.0, 0.0, 0.0);
	float h = fract(sin(float(INSTANCE_ID) * 12.9898 + 4.1) * 43758.5453);
	float len = min(length_m * (0.6 + 0.8 * h) * al, max_len_per_m * -c.z);
	float w = max(width_m, px_per_m * -c.z);
	VERTEX = c + ax * VERTEX.y * len + side * VERTEX.x * w;
	NORMAL = vec3(0.0, 0.0, 1.0);
	float life = INSTANCE_CUSTOM.y;
	v_alpha = smoothstep(0.0, 0.15, life) * (1.0 - smoothstep(0.75, 1.0, life)) * (0.5 + 0.5 * h)
		* sqrt(width_m / w);
}

void fragment() {
	float across = 1.0 - abs(UV.x * 2.0 - 1.0);
	float along = sin(UV.y * 3.14159);
	ALBEDO = tint.rgb * (1.0 + 3.0 * flash);
	float m = mix(mask_floor, 1.0, smoothstep(mask_x.x, mask_x.y, SCREEN_UV.x));
	ALPHA = clamp(tint.a * v_alpha * across * along * m * (1.0 + 1.5 * flash), 0.0, 1.0);
}

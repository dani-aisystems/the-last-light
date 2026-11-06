shader_type spatial;
// G5 / finding 29: a distant lightning bolt. Camera-facing quad strips built by outside.gd.
// Unshaded and additive, and not fogged, because at 400-900 m the storm fog would erase it
// completely. UV.x runs across the strip (0..1); COLOR.a is the branch weight (main channel 1).
render_mode unshaded, blend_add, depth_draw_never, cull_disabled, fog_disabled, shadows_disabled;

uniform float intensity = 0.0;
uniform vec3 tint : source_color = vec3(0.80, 0.86, 1.0);

void fragment() {
	float x = abs(UV.x * 2.0 - 1.0);
	float core = pow(max(1.0 - x, 0.0), 6.0);       // white-hot centre line
	float halo = pow(max(1.0 - x, 0.0), 1.6) * 0.35;
	float a = (core + halo) * COLOR.a * intensity;
	ALBEDO = mix(tint, vec3(1.0), core) * 3.0;       // > 1 so the existing glow picks it up
	ALPHA = clamp(a, 0.0, 1.0);
}

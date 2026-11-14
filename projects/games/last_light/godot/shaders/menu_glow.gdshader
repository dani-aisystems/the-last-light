shader_type canvas_item;
// G6d stage E: the title menu's focus glow, a soft lamp-like bloom behind the focused item's text. An
// elongated ellipse (the rect is about 1.6x the text width) with a gaussian core that reaches exactly 0
// before the rect's edge, so it has no edges anywhere. Low alpha, warm white.

uniform vec4 tint : source_color = vec4(1.0, 0.85, 0.62, 1.0);
uniform float strength = 0.0;

void fragment() {
	vec2 p = UV * 2.0 - 1.0;
	float d = dot(p, p);
	float a = exp(-3.2 * d) * (1.0 - smoothstep(0.5, 1.0, d));
	COLOR = vec4(tint.rgb, tint.a * a * strength);
}

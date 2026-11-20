shader_type canvas_item;
// G6a (item 34): one shared grade for the ending panels, so images from different sources read as a set
// beside the warm-black ending card. Applied on the TextureRect only; the source PNGs stay untouched.
//   palette map  : luminance onto a period duotone (ink shadows, warm paper highlights), part of the
//                  original colour kept (`keep_color`)
//   ink edge     : a light luminance-edge darkening, like a printed key line
//   halftone     : a fine 45-degree dot screen in the shadows only (screen space, `dot_px` per cell)
//   grain + vignette
// `strength` 0 shows the image as supplied; 1 is the full grade.

uniform float strength : hint_range(0.0, 1.0) = 0.75;
uniform vec3 shadow_ink : source_color = vec3(0.10, 0.075, 0.06);
uniform vec3 paper : source_color = vec3(0.93, 0.86, 0.72);
uniform float keep_color : hint_range(0.0, 1.0) = 0.38;
uniform float edge_ink : hint_range(0.0, 1.0) = 0.35;
uniform float halftone : hint_range(0.0, 1.0) = 0.22;
uniform float dot_px = 4.0;
uniform float grain : hint_range(0.0, 0.2) = 0.035;
uniform float vignette : hint_range(0.0, 1.0) = 0.35;

// R3: COLOR on entry to fragment() is already texture * vertex colour, so multiplying the result by it again
// squared the image (a photo's mean luminance fell from 30 to about 5). The vertex colour, which carries
// the panel's modulate (its crossfade), is passed through here instead.
varying vec4 v_color;

void vertex() { v_color = COLOR; }

float luma(vec3 c) { return dot(c, vec3(0.299, 0.587, 0.114)); }

float hash(vec2 p) { return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453); }

void fragment() {
	vec4 src = texture(TEXTURE, UV);
	vec3 c = src.rgb;
	float l = luma(c);
	// palette map
	vec3 duo = mix(shadow_ink, paper, smoothstep(0.02, 0.98, l));
	vec3 g = mix(duo, c * mix(vec3(1.0), paper, 0.35), keep_color);
	// ink edge (luminance Sobel over the source texels)
	vec2 px = TEXTURE_PIXEL_SIZE * 1.5;
	float tl = luma(texture(TEXTURE, UV + px * vec2(-1.0, -1.0)).rgb);
	float tr = luma(texture(TEXTURE, UV + px * vec2(1.0, -1.0)).rgb);
	float bl = luma(texture(TEXTURE, UV + px * vec2(-1.0, 1.0)).rgb);
	float br = luma(texture(TEXTURE, UV + px * vec2(1.0, 1.0)).rgb);
	float gx = (tr + br) - (tl + bl);
	float gy = (bl + br) - (tl + tr);
	float edge = smoothstep(0.08, 0.45, length(vec2(gx, gy)));
	g = mix(g, shadow_ink, edge * edge_ink);
	// halftone: dots grow with darkness, only below mid grey
	vec2 sp = FRAGCOORD.xy / max(dot_px, 1.0);
	vec2 rot = vec2(sp.x + sp.y, sp.y - sp.x) * 0.70710678;
	float d = length(fract(rot) - 0.5);
	float dark = clamp((0.55 - l) / 0.55, 0.0, 1.0);
	float dotm = 1.0 - smoothstep(dark * 0.5 - 0.06, dark * 0.5 + 0.06, d);
	g = mix(g, shadow_ink, dotm * halftone * dark);
	// grain and vignette
	g += (hash(floor(FRAGCOORD.xy)) - 0.5) * grain;
	vec2 v = UV - 0.5;
	g *= 1.0 - vignette * smoothstep(0.25, 0.75, length(v) * 1.2);
	COLOR = vec4(mix(c, clamp(g, 0.0, 1.0), strength), src.a) * v_color;
}

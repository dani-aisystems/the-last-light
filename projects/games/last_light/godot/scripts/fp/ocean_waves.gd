class_name OceanWaves
extends RefCounted
## The Gerstner wave set shared by shaders/ocean.gdshader (GPU) and ship motion (CPU).
## Swells run roughly from the open sea (north) toward the island (+z).
##
## Audit Stage M (M1): each wave fades out with distance r from the tower (FADE: full height inside x metres,
## gone beyond y, smoothstep between), where scripts/fp/sea_mesh.gd's radial mesh gets too coarse to carry it.
## On Medium every wave keeps at least 2.5 vertices per wavelength wherever it is not zero. The 5.3 m chop goes
## first (110 to 145 m), the 60 m swell last (800 to 980 m). r is measured at the rest position (before the
## horizontal Gerstner shift), as the shader's vertex() does. ANY OTHER MIRROR OF THE SURFACE (ship_view2's
## surface sampler, shaders/wake.gdshader) must scale wave i by wave_gain(i, r) as well, inside the calming.

const WAVES := [
	Vector4(0.25, 1.0, 0.13, 60.0),
	Vector4(-0.4, 1.0, 0.11, 34.0),
	Vector4(0.6, 0.9, 0.09, 21.0),
	Vector4(-0.1, 1.0, 0.08, 13.0),
	Vector4(0.9, 0.5, 0.06, 8.0),
	Vector4(-0.7, 0.8, 0.05, 5.3),
]
const FADE := [
	Vector2(800.0, 980.0),
	Vector2(460.0, 550.0),
	Vector2(300.0, 380.0),
	Vector2(210.0, 265.0),
	Vector2(150.0, 185.0),
	Vector2(110.0, 145.0),
]
const NO_FADE := Vector2(1.0e7, 2.0e7)

## --sea=legacy (outside.gd sets it): no distance fade, as the old square sea.
static var legacy := false


static func amp_mul(storm: float) -> float:
	return lerpf(0.35, 1.0, storm)


## Wave i's share of its height at distance r (m) from the tower: 1 near, 0 beyond FADE[i].y.
static func wave_gain(i: int, r: float) -> float:
	if legacy:
		return 1.0
	var f: Vector2 = FADE[i]
	return 1.0 - smoothstep(f.x, f.y, r)


## The lagoon calming: waves at 35 % close to the island, full from 45 m out.
static func calm(r: float) -> float:
	return lerpf(0.35, 1.0, smoothstep(15.0, 45.0, r))


## Surface height at world (x, z) (vertical Gerstner component, evaluated at the rest position).
static func height_at(p: Vector2, t: float, storm: float) -> float:
	var h := 0.0
	var amp := amp_mul(storm)
	var r := p.length()
	for i in WAVES.size():
		var g := wave_gain(i, r)
		if g <= 0.0:
			continue
		var w: Vector4 = WAVES[i]
		var k := TAU / w.w
		var c := sqrt(9.8 / k)
		var d := Vector2(w.x, w.y).normalized()
		var f := k * (d.dot(p) - c * t)
		h += (w.z * amp * g / k) * sin(f)
	return h * calm(r)


## Approximate surface normal by central differences.
static func normal_at(p: Vector2, t: float, storm: float, e := 1.5) -> Vector3:
	var hx := height_at(p + Vector2(e, 0), t, storm) - height_at(p - Vector2(e, 0), t, storm)
	var hz := height_at(p + Vector2(0, e), t, storm) - height_at(p - Vector2(0, e), t, storm)
	return Vector3(-hx, 2.0 * e, -hz).normalized()


static func shader_array() -> Array:
	var out: Array = []
	for w in WAVES:
		out.append(Vector4(w.x, w.y, w.z, w.w))
	return out


## The fade table for ocean.gdshader's wave_fade uniform (legacy: no fade).
static func shader_fade_array() -> PackedVector2Array:
	var out := PackedVector2Array()
	for f in FADE:
		out.append(NO_FADE if legacy else f)
	return out

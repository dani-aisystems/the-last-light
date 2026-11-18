extends RefCounted
## Audit Stage M (M2): one atmosphere. Every layer that pulls a distant pixel toward a colour takes it from
## here: the depth fog's colour (outside.gd), the fog bank and the below-horizon fill of shaders/sky.gdshader
## (its `murk` uniform), so the farthest sea and the sky at the horizon are the same colour by construction,
## lightning included (docs/last_light/audit-2026-11/14_stageM_ocean_boundary_fog.md, D.1 and J.3).
## Static and stateless; loaded with preload (no class_name), so headless -s tests see it without an import.
##
## Density keeps today's figures (Daniel, decision 2: visibility 0.6 to 1.3 km at night, 2.8 km at dawn).
## Colours are sRGB Colors, as Environment.fog_light_color and a source_color uniform both take them.

const NIGHT_MURK := Color(0.12, 0.135, 0.16)   # dark, desaturated: between today's fog (0.05) and sky (0.25)
const DAWN_MURK := Color(0.55, 0.5, 0.48)
const FLASH_TINT := Color(0.55, 0.6, 0.75)     # the sky shader's lightning colour
const FLASH_MURK := 0.12                         # how much a flash lights the murk (fog and bank alike)


## Exponential depth-fog density (1/m): storm thickens it, the dawn thins it.
static func fog_density(storm: float, dawn: float) -> float:
	return lerpf(0.0025, 0.0065, storm) * (1.0 - 0.6 * dawn)


## Meteorological visibility (m): where 2 % of the contrast is left.
static func visibility_m(storm: float, dawn: float) -> float:
	return 3.912 / fog_density(storm, dawn)


## Share of an object's own light that survives d metres of fog.
static func transmittance(d: float, storm: float, dawn: float) -> float:
	return exp(-fog_density(storm, dawn) * d)


## Volumetric cover of a pixel beyond the froxel volume (its last slice), from the volumetric density (1/m).
## VOL_K is the effective path length, calibrated on captures against M0's sky (record J.3).
const VOL_K := 120.0


static func volumetric_cover(vol_density: float) -> float:
	return 1.0 - exp(-VOL_K * maxf(vol_density, 0.0))


## The sky above the bank under a sky_affect of 1.0 gets (1 - a) of its light; under the old 0.4 it got
## (1 - 0.4 a). This gain gives it the old brightness and contrast back (the fog's own light is near black at
## night, so no pivot is needed). 1.0 without volumetric fog (Low). Capped against noise in a full gale.
static func sky_gain(vol_density: float, volumetric_on: bool) -> float:
	if not volumetric_on:
		return 1.0
	var a := volumetric_cover(vol_density)
	return minf((1.0 - 0.4 * a) / maxf(1.0 - a, 0.05), 6.0)


## The murk: the colour the farthest sea and the sky at the horizon both converge to. sky_dawn is the sky
## shader's own dawn blend (outside.gd: max(dawn, dusk * 0.55)); flash is the flicker-shaped flash now.
static func horizon_color(sky_dawn: float, flash: float) -> Color:
	var c := NIGHT_MURK.lerp(DAWN_MURK, clampf(sky_dawn, 0.0, 1.0))
	return Color(c.r + FLASH_TINT.r * flash * FLASH_MURK, c.g + FLASH_TINT.g * flash * FLASH_MURK,
		c.b + FLASH_TINT.b * flash * FLASH_MURK)

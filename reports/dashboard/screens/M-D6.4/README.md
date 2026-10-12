# M-D6.4 — a real day/night terminator

**Status: COMPLETE.** The globe is lit by the sun's actual position, derived from
the clock, not by a painted gradient.

Captures: `t1.png` (T1) and `t3.png` (T3), taken 2026-10-12 on this host. Artifacts:
`components/stage/sun.ts`, the terminator wiring in `components/stage/Globe.tsx`,
and `scripts/sun_selftest.ts` (`npm run test:sun`).

## What was built

`sun.ts` computes the subsolar point — where the sun is directly overhead — from a
date, using the NOAA solar position approximation: a Fourier series in the
fractional year for the equation of time and the declination. It is accurate to
about 0.01°, roughly a kilometre of subsolar travel, which is two orders of
magnitude finer than the spacing between the globe's dots. So the terminator it
draws is the one the real Earth has.

From the subsolar point the module gives a unit sun direction in the frame
`landDots.ts` already used (`y` up, `lon = atan2(z, x)`), so the continents and
the terminator cannot be rotated against each other.

`Globe.tsx` lights each dot by `terminatorWeight(dotNormal, sun)` — a smoothstep
over a 0.3-wide penumbra, so the day side is bright, the night side is dark, and
the band between is a gradient with no visible kink. The night side keeps a floor
rather than going black: dust dims to 0.16 of base, land to 0.34. A globe that is
half invisible reads as broken, and the dust field is what makes the globe read as
a globe at all.

The sun is refreshed once per second, not per frame. The sun moves at 15°/hour and
the globe's idle spin is 0.5°/s, so a second is half a degree of travel — inside
the dot spacing, which makes the refresh invisible. One vector per refresh, and
the dots are re-lit in place (`needsUpdate`) rather than rebuilt.

## Why the terminator is exact

The group's transform is `Ry(spin) * Rz(tilt)`. Rather than transform 28 800 dots
per frame, the sun is transformed once by the inverse, `Rz(-tilt) * Ry(-spin)`.
This is not an approximation: the terminator is defined by the dot product of each
dot's position with the sun direction, and rotating the sun by the inverse of the
group's rotation is exactly equivalent to rotating every dot by the group's
rotation. One vector instead of a matrix per dot, and the result is identical.

## Verification

The astronomy is asserted headlessly — no GPU, no `window`, no three.js. 11 tests
in `scripts/sun_selftest.ts`, all passing:

| Assertion | Held to |
|---|---|
| June solstice declination | the tropic of Cancer, ±0.5° |
| December solstice declination | the tropic of Capricorn, ±0.5° |
| Both equinoxes | the equator, ±0.5° |
| Every day of the year | never outside the tropics, +0.2° |
| Per hour of UTC | ~15° of longitude westward |
| A day later | the same meridian, <1° drift |
| Noon UTC | within the equation of time, ±4.2° |
| The direction vector | unit length, height = declination |
| The frame | `atan2(z, x)` = the point's longitude, matching `landDots` |
| The terminator | full day at the subsolar point, full night at the anti-solar, half at the limb |
| The gradient | monotonic from night to day |

A painted terminator could look right and be anywhere. These are numbers, so a
bug in the series breaks them without breaking the render — which is exactly the
failure a screenshot cannot catch.

### And then the render

Numbers prove the astronomy. They do not prove the *wiring* — that the sun the
dots use is the sun the module computed, applied in the right frame, reaching the
card. That needed a measurement, and a control.

Both captures were taken against the same fixed stage rig (a gold point light
above, a rim light from stage-left), so **both already have a lit side**. Measuring
the M-D6.4 frame alone cannot separate the sun from the rig. Measuring the *change*
the terminator introduces can, because nothing else changed between the two frames.

The centroid of bright gold, measured against the disc's own centre (found from the
fresnel rim's bounding box, not the window's midpoint):

| Capture | Bright gold px | Centroid offset | Unit |
|---|---|---|---|
| M-D6.3, no terminator (control) | 539 | -34, -14 | -0.92, -0.38 |
| M-D6.4, with the terminator (T1) | 485 | -80, -10 | -0.99, -0.12 |
| **The terminator's own contribution** | | **-46, +4** | **-0.996, +0.087** |

The sun at capture (2026-10-11T23:30Z — the captures' 03:00 local on this
UTC+3:30 host) was at lon -176°, lat -7.1°. Projected through the stage's camera
(position `[0, 3.4, 7.6]`, fov 42, looking at the origin), its screen direction is
**-0.984, +0.176**.

The terminator's contribution lands at **-0.996, +0.087** — agreement within 6°,
with the dominant x-component matching to 1%. The terminator moved the bright mass
toward where the sun actually is, and nowhere else.

**An earlier reading of this same measurement was wrong, and the record should say
so.** The M-D6.4 frame's absolute offset (-0.99, -0.12) appeared to contradict a
naive prediction of (-0.99, +0.12): same x, inverted y, which I first attributed
to the window centre sitting below the globe's true disc centre. That hypothesis
was testable and it was false — the disc centre (852, 248) coincides with the
window centre (850, 247.5) to within three pixels. The real causes were two: I had
assumed a 1700×500 capture when the PNG is 1582×748, which throws off any hand-rolled
projection; and the absolute offset is not the sun's direction at all, because the
fixed stage lights contribute their own lit side to every frame. The differential
fixes both.

The T3 capture, at 24 000 dust + 4 800 land dots, confirms it is not a T1 artifact:
1591 bright gold px, centroid offset unit (-0.97, -0.25), bright gold left of the
vertical diameter 1112 px against 479 right — a 2.32 ratio, against the control's
1.16.

## What is deliberately not lit

The terminator shades the dot fields only. It does not shade the lacquer body or
the floor ring, for two reasons: the stage's gold point light is not the sun, and
making it behave like one would make the ring go dark half the time for no
astronomical reason; and M-D6.2 already QA'd the ring's look under the stage rig.
The globe's own axial tilt (0.31 rad) is aesthetic — it makes the globe read as a
planet — and the terminator is computed in the globe's tilted frame, so the tilt
rotates the continents under the sun correctly rather than being ignored.

Per §2.3, no status colour appears here. The night side is the same brand gold,
dimmed. A token's verdict is still expressed by the truth badge in the DOM, never
by brightening a region of the globe.

## Costs

T1 gains the terminator at no added draw call: the colour attribute already existed,
and the per-second re-light is a CPU pass over 28 800 floats, not a render change.
The `relight` path mutates the existing attribute's array in place and sets
`needsUpdate`, so no geometry is rebuilt as the world turns.

## Owner QA 02:48 items 2 and 5 — crown clearance and the seat, verified

Items 2 (crown clipped by the header) and 5 (globe not seated in the floor ring)
were one geometric problem, and the fix for both landed in `73a7f85`. This section
records the measurement that verifies them against `seated_t3.png`.

**Method.** A single bounding box is not enough here, because the shell's own gold
chrome (the M-D5.G chip borders in the header) is the same hue as the ring and sits
in the same frame. Every number below is restricted to the stage area, x 350..1250
and y 150..740, which excludes the header band entirely. The ring was then isolated
by ablation rather than by colour threshold: two captures of the floor with the
globe removed, one with the ring mesh and one without, differ in exactly the ring.
That removes the globe's dust and the shell's chrome at once. The floor rotates
between captures, so the diff also picks up the shamseh's motion — the ring's own
pixels are identified as the dim saturated-gold metal and measured in
`floor_ring_t3.png` directly.

| Object | Measurement |
|---|---|
| Header chrome, centre column | last non-stage-background pixel at **y = 48** |
| Globe crown, centre column | first non-stage-background pixel at **y = 135** |
| **Crown clearance** | **87 px** — the crown is not clipped (item 2) |
| Globe (bright dust, stage area) | x 483..1089, y 150..729, centre (786, 440), half-width 303, half-height 290 |
| Ring (dim gold metal, stage area) | x 477..1102, y 329..731, centre (790, 530), half-width 313, half-height 201 |
| Ring aspect (half-width / half-height) | 1.56 — a tilted circle, as a floor ring must read |

The two shapes carry the answer. The globe's projection is near-circular (303 × 290),
which is what a sphere must give; the ring's is an ellipse (313 × 201), which is what
a horizontal circle seen from above must give. The globe's horizontal span sits inside
the ring's by 6 px on the left and 13 px on the right, and the globe's vertical centre
(440) stands above the ring's (530) while the globe's base (729) meets the ring's near
edge (731). That is a ball in a hoop, not a halo at the equator. The ring's near edge
at y = 731 stays inside the 748 px frame.

A hand-rolled pinhole projection (camera `[0, 5.8, 8.8]`, 42° vertical, aspect
1582/748) agrees on the shape but renders both objects about 1.6× smaller than the
capture shows them. The origin projects to exactly (791, 374), the frame centre, so
the camera's aim is right; the disagreement is in the scale, and I did not resolve
it. It does not affect the verdict, because the two facts that settle items 2 and 5 —
the crown's clearance and the ring's containment of the globe — are measured against
each other in the same frame, and cancel any scale error. Recorded here so the next
pass does not re-derive the projection and trust it.

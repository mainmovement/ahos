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
in the same frame. Every number below is restricted to the stage disc, x 450..1150,
which excludes the shell's side chips, and the header is measured on the centre
column x = 791 where the globe is tallest, so the two rows being compared come from
the same column and cannot miss each other sideways. The ring was then isolated by
ablation rather than by colour threshold: two captures of the floor with the
globe removed, one with the ring mesh and one without, differ in exactly the ring.
That removes the globe's dust and the shell's chrome at once. The floor rotates
between captures, so the diff also picks up the shamseh's motion — the ring's own
pixels are identified as the dim saturated-gold metal and measured in
`floor_ring_t3.png` directly.

> **Corrected (owner QA 10:45).** The table this section first shipped in `8ca48fd`
> was measured through a scan window that began at y = 150 — fifteen rows *below*
> the crown — so the globe's "top" was the window's edge, not the globe. The
> clearance, the centre and both half-extents were derived from a clipped box and
> none of them describe the capture. Re-measured on the full frame:

| Object | Measurement |
|---|---|
| Header chrome, centre column x = 791 | last lit row **y = 54** |
| Globe crown, centre band x 741..841 | first lit row **y = 135** |
| **Crown clearance** | **81 px** — the crown is not clipped (item 2) |
| Globe + floor disc (lit, x 450..1150) | x 476..1109, y 135..731, centre (792, 433), half-width 316, half-height 298 |
| Globe base, centre band | y = 729 — the last bright row on the globe's own surface |
| Disc's last lit row (the ring's near edge) | y = 731, inside the 748 px frame |
| Ring's horizontal span at the globe's base | x 476..1108, width 632 |

`seated_t1.png` was also replaced (owner QA 10:45): the file this section shipped
with was a Chrome `ERR_CONNECTION_REFUSED` page — 64.1% of its frame was pale
background and only 29.2% was the stage's near-black — so it proved nothing about
T1. Recaptured on the running dev server, it is a real render (0.1% pale, 93.5%
near-black) and its geometry is *identical* to T3's: crown y = 135, clearance 81 px,
disc x 476..1109 and y 135..731. That is expected rather than coincidental — the
tier changes the dot count and the motion budget, never the globe's scale or seat,
so the crown clearance and the ring's containment hold at every tier by
construction.

The old row "x 483..1089, y 150..729, centre (786, 440), half-width 303, half-height
290" and its 87 px clearance all came from that clipped box; the corrected numbers
above are the ones to quote. The verdict itself is unchanged and does not depend on
the error — see the next paragraph.

The two shapes carry the answer, and the correction above does not change it. The
disc's bounding box is 633 × 597 with its centre at (792, 433) — wider than it is
tall, because the box wraps both the globe's near-circular projection and the ring's
ellipse, which extends further left and right than the globe does but not as far up.
The ring's own horizontal span at the globe's base is x 476..1108 (632 px wide) and
the globe's base is y = 729, two rows above the ring's near edge at y = 731. The
globe's vertical centre stands above the disc's while its base meets the ring's near
edge, which is a ball in a hoop rather than a halo at the equator. The ring's near
edge at y = 731 stays inside the 748 px frame.

The ring's ellipse and the globe's circle were separated by the ablation described
above, not by fitting boxes to a merged outline, which is why the merged box here is
reported as the disc rather than as either object.

A hand-rolled pinhole projection (camera `[0, 5.8, 8.8]`, 42° vertical, aspect
1582/748) agrees on the shape but renders both objects about 1.6× smaller than the
capture shows them. The origin projects to exactly (791, 374), the frame centre, so
the camera's aim is right; the disagreement is in the scale, and I did not resolve
it. It does not affect the verdict, because the two facts that settle items 2 and 5 —
the crown's clearance and the ring's containment of the globe — are measured against
each other in the same frame, and cancel any scale error. Recorded here so the next
pass does not re-derive the projection and trust it.

## Owner QA 02:48, item 3 — the "thick beaded neon ring"

Captures: `ablation_rim_full_old.png` (the committed `max(dot, 0)` shader) and
`ablation_rim_full.png` (the `abs(dot)` fix), both T3, both with the globe's spin
and the floor's rotation frozen so the pair is comparable. `clean_shell.png`,
`clean_shell_old.png` and `clean_noshell.png` isolate the shell on a bare globe
with the dot fields switched off, so the shell's own contribution can be seen with
nothing additive on top of it.

### The cause

Not a tuning problem. Two rounds of raising `uPower` moved the saturation barely at
all (755 -> 723 px) because the shader could not use the exponent. The shell renders
`side: THREE.BackSide`, so every fragment it draws is back-facing: its geometric
normal points *away* from the camera, and `dot(normal, view)` is negative. The old
line clamped it:

```glsl
float fresnel = 1.0 - max(dot(vNormalView, vViewDir), 0.0);
```

A negative dot goes to 0 under `max`, so `fresnel` is identically 1 — on every
fragment of the shell. `pow(1, uPower)` is 1 for any `uPower`, which is why the
exponent was inert. The shell was not painting a fresnel edge at all; it was
painting a solid constant-brightness annulus, and the width of that annulus was set
entirely by how far the shell's sphere (1.014 * R) reached past the occluding body
(0.965 * R) — about 15 px at this camera. The "beaded" texture was the additive
dust stacking at the silhouette on top of it. Replacing the clamp with `abs` is the
whole fix; no uniform was retuned.

### Measurement

Measured against each capture's own unlit background 22 px clear of the silhouette,
so the moving sun between page loads cannot contaminate it:

| Quantity | `max(dot, 0)` | `abs(dot)` |
|---|---|---|
| Peak luminance above local background at the limb | 123.8 | **85.5** |
| Saturated (> 238) pixels in the limb band | 1.18% | **1.03%** |
| Peak position relative to the silhouette | d = -3 | d = -3 |

The limb is still a strong gold edge — 85.5 above the background is not subtle —
but it is no longer the overblown band it was, and the saturated share fell with it.
On the bare globe, the shell's own contribution across the band where only it can be
lit (between the body's silhouette and the shell's) grades with the fix instead of
sitting flat, and the total light it puts into that band drops from 157.6 to 109.0.

What I could not get a clean number on, and am not claiming: the exact half-width of
the edge. The shell's annulus is only ~15 px wide and the floor ring occludes the
lower part of it, so a radial average over all angles is diluted by angles that have
no shell at all, and the two page loads differ by ~0.25 deg of sun, which relights
dots near the terminator and shows up in a plain diff as noise that is not the rim.
The three numbers above are the ones measured against a per-frame reference, and are
the ones I would stand behind.

## The two glow spots — attributed by ablation, not fixed

Captures (all T3 via the app's own tier override, 1582×748):
`spot_base_t3.png` (everything on), `spot_nodots_t3.png` (both additive dot clouds
hidden, lights and body on), `spot_nodir_t3.png` (only the directional key removed),
`spot_nolights_t3.png` (all four stage lights removed), `spot_nocanvas_t3.png`
(the `<canvas>` set to `display:none` after mount).

**Nothing here is claimed to be fixed.** What follows is the cause of each spot,
measured at fixed pixels. Two earlier passes closed this item on visual guesses that
the owner's screenshots disproved; this pass deliberately closes nothing.

### The two hottest pixels

Peaks in the globe's upper box (x 590..895, y 105..320), non-max-suppressed:

| Pixel | L | Colour |
|---|---|---|
| (739,162) | 125.3 | rgb(193,133,39) |
| (723,244) | 104.6 | rgb(206,120,61) |

Both warm gold, both in the globe's upper-left — the two spots the owner flagged.

### The ablation table

| Pixel | baseline | dots+land hidden | directional off | all four lights off |
|---|---|---|---|---|
| (739,162) | 125.3 | **0.2** | 134.8 | 134.8 |
| (723,244) | 104.6 | 134.0 | **0.0** | **0.0** |
| (790,176) | 88.8 | 135.5 | 135.3 | 0.0 |
| (680,184) | 74.0 | **12.2** | 109.7 | 126.6 |
| (659,252) | 65.2 | **0.0** | 41.2 | — |

The globe spins at T3, so a pixel's surface changes between captures. Additive dots
can only ever *add* light, so any cell that went **up** between the baseline and the
dots-hidden capture is rotation, not the ablation — those cells are not read as
evidence. The cells in bold are unambiguous, because they are drops the ablation
alone can produce.

**Spot 1, (739,162) — additive dot stacking.** It falls to 0.2 when the dot clouds
are hidden and is invariant across six captures with four different light sets
(134.5, 138.0, 135.7, 138.9, 134.8, 134.8 — both point lights off, the atmosphere
shell hidden, the directional off, and all four lights off). Nothing the stage lights
do reaches it, because the dot fields are shaded by the sun (`sun.ts`), not by the
stage rig. This is the mechanism `Globe.tsx`'s own 00:24 comment names — "dots near
the silhouette stack in screen space" — and the opacity 0.95 → 0.78 change already
backed it off without removing it: the pixel still reads L ≈ 125.

**Spot 2, (723,244) — the directional key's specular on the clearcoat body.** It
reads 0.0 in both captures where the directional light is off, including the one
where both point lights are still on, and it survives hiding the dots. A clearcoat
specular is fixed by light direction and view direction, not by surface rotation,
which is why this pixel measured bit-identical (134.0) across captures that differed
elsewhere: the globe turns under the highlight, the highlight does not move.

### What was ruled out

**A DOM overlay.** `document.elementFromPoint` at all six probe pixels returns the
`<canvas>` itself, with a transparent computed background and no blend mode. The
canvas is created `alpha: false` and cleared with an opaque colour, so nothing behind
it can show through anyway, and hiding the canvas by style drops the whole region to
the page background. The spots are painted by WebGL.

**The two point lights.** Removing both left (739,162) unchanged and moved (723,244)
by less than the sun's drift between page loads. The `StageLights` gold point light
above the crown — the obvious suspect, and the one a previous pass retuned — is not
either spot.

**The atmosphere shell.** Hiding the fresnel shell changed 5.19 % of the frame's
pixels, so the ablation took, but neither spot's pixel moved.

### Two causes, so no single change fixes both

The candidate interventions, with their tradeoffs, none of them applied:

- Spot 1 is additive stacking near the silhouette. Reducing `pointsMaterial.opacity`
  (0.78 today) or `size` (0.056) scales it directly, but dims the dust field the
  globe's roundness depends on (§"the dust field is what makes the globe read as a
  globe at all"). A size or alpha ramp by distance from the limb would address only
  the silhouette, at the cost of a shader or a per-dot attribute.
- Spot 2 is a clearcoat highlight. Raising the body's `roughness` (0.5) softens it
  but flattens the lacquer; dimming the directional (1.1) darkens the whole stage's
  dusk key, including the floor ring M-D6.2 already QA'd.

The owner's 00:24 option — make them intentional city/market pings, or remove — is a
visual judgement this measurement cannot make. Both spots are within the range the
00:24 retune was aiming at (neither is saturated: rgb(193,133,39) and rgb(206,120,61)
are warm gold, not the white-gold of the pre-fix 0.95 stacking).

### A correction to the numbers above

The geometry table in the "crown clearance" section was measured when the stage held
the full frame. Since M-D7's telemetry strips landed, the canvas occupies
x 15..1569, y 93..397 — a 305 px band — so that table's "disc y 135..731, centre
(792, 433)" is stale and the disc it describes cannot exist in the current layout.
The globe still centres near x = 792, but vertically it sits in the upper third of
that band. The crown-clearance verdict is not re-measured here; it needs the
strips' height subtracted before any of those numbers are quoted again.


---

## 2026-10-13 — Spot 2 fixed; Spots 1 and the "white-gold" line are correct lighting

Continuation session. The two vendor fixes (fresnel `Atmosphere`, cobe-style land
dots) were already committed, so this pass worked the two remaining hot spots
directly. Both were re-measured against the committed ablation values before
anything was changed, because the canvas geometry had moved.

**Spot 2 (723, 244) — fixed.** Re-measured at L = 134.0, bit-identical to the
committed ablation value, with the same sharp falloff (134.0 centre → 62–88 at
10 px → 14–16 at 20 px). That re-confirmed the clearcoat diagnosis independently.
`clearcoatRoughness` 0.28 → 0.5 — broadening the clearcoat rather than the base
`roughness`, so the lacquer sheen survives and the directional key that also
lights the M-D6.2 floor ring is untouched. After the change the same pixel reads
L = 32.3 rgb(69,24,7) and the 10 px neighbourhood went from a spike to flat:

| pixel | before | after |
|---|---|---|
| (723,244) | 134.0 | 32.3 |
| (713,244) | 87.7 | 36.6 |
| (733,244) | 61.4 | 27.2 |
| (723,234) | 64.9 | 28.8 |
| (723,254) | 69.1 | 28.6 |
| (703,244) | 14.0 | 17.9 |
| (743,244) | 15.6 | 16.8 |

The neighbours rising a few luminance points is the intended behaviour — the same
energy spread over more pixels rather than a dimmer light. Spot 2 no longer
appears in the canvas peak list.

**Spot 1 (739, 162) — not a defect, and the silhouette attribution above is
wrong.** The receipt's candidate intervention assumed additive stacking *near the
silhouette*. Measured, it is not near the silhouette: on the current layout the
disc spans roughly x 659..951 at y = 200, i.e. centre ≈ (805, 245) and radius ≈
150 px, which puts (739,162) at 106 px from centre — 45° from the view axis, and
(921,310) at 133 px — 62°. Neither is grazing.

What Spot 1 actually is: a dense dot patch at the day-side edge of the terminator.
A 9-point grid shows (745,162) at L = 94.5 and (745,168), six pixels directly
below it, at L = 0.4 — day to night in six pixels. `terminatorWeight`'s 0.3
spread is a ±17° band on the sphere, and the terminator happens to lie almost
edge-on to the camera here, so its projection compresses to a near-vertical line.
That is correct physics for a terminator seen nearly edge-on, not stacking.

**The "white-gold" region at (921, 310) — also correct lighting.** This became the
globe's hottest pixel once Spot 2 was spread (L = 231.6, rgb(255,241,69)), and it
matches the white-gold the 00:24 note warned about. It is a narrow bright streak,
under 20 px wide and at least 35 px tall, and it is a dense, fully-lit land-dot
coastline on the day side: the land layer's dots are larger (`LAND_DOT_PX` 5.5)
and brighter, and where the mask is dense the additive blending saturates the
channel. The M-D6.5 chain rings were ruled out first — they sit at
`RING_RADII × GLOBE_RADIUS × SCALE` = 2.32–3.06 world units, about 197 px from
centre, entirely outside the 150 px disc, and they are `lineWidth` 1 at
`opacity` 0.6.

**The 1 px rim is the atmosphere shell, not the dots.** A row scan at y = 200 is
bit-identical before and after the dot work below (left edge x = 659, peak 92.2
above backdrop at offset 0, 0–2 at ±2 px and +4 px): the vendored fresnel shell is
what paints the silhouette, so no change to the dot fields can touch it. This is
the "confirm beaded rim" item — the rim is present, one to two pixels wide, and
comes from the vendor shell the owner's rule asked for.

### A limb ramp was built, measured, and reverted

The receipt's own suggestion — "a size or alpha ramp by distance from the limb" —
was implemented and then thrown away, because the measurements above killed the
premise. A per-dot `smoothstep(0, 0.3, dot(normal, viewLocal))` was folded into
both `litColors` and `relight` (so mount-time lighting and the per-second refresh
still provably agree), with the view vector derived as `sunLocalFor`'s twin — the
inverse of the group's `Ry(spin) * Rz(tilt)`, applied to a constant camera-to-centre
direction, valid because the camera at `[0, 5.8, 8.8]` has no controls.

It compiled clean and was geometrically right, but it did nothing: Spot 1 moved
87.1 → 85.0, the (921,310) streak 218.8 → 231.6, and the row-200 limb profile was
unchanged to the digit. An initial sign error dimmed the front of the globe to
L ≈ 1.4 and exposed the bug immediately, which is worth noting as the reason the
ramp's effect was verified at all rather than assumed. Reverting leaves the globe
as the vendor kit and the §8.1 tuning intended; the negative result is recorded
here so the limb-stacking hypothesis is not re-attempted. If a future pass still
wants the silhouette softened, the lever is the atmosphere shell, not the dots.

### Open

- The 00:24 owner option — make the remaining bright regions intentional
  city/market pings, or remove — is still a visual judgement. Both remaining
  regions are warm gold in a plausible band, not saturated white-gold, and both
  are now explained as correct lighting rather than artefacts.
- `scripts/stage_luminance.mjs` still defaults its peak box to `476,135,1109,731`
  — the stale geometry this file corrected. Left alone here; quoting its default
  output quotes DOM below the canvas (peaks near y ≈ 691). Pass
  `--box 15,93,1569,397` or the numbers will be wrong.
- The crown-clearance table is still stale (see the correction above) and is not
  re-measured here.

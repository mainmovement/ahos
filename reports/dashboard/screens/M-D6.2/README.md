# M-D6.2 — the 00:24 visual QA pass on the globe

- Date (Tehran): 2026-10-12 · Step: M-D6.2, Soltan's 00:24 QA on the M-D6.1 globe
  (`t1.png` at `d6a8ca2`).
- The owner's four fixes, and what became of each.

## What changed

| Fix (00:24 QA) | Change |
|---|---|
| Rim is a thick flat neon-yellow ring | Fresnel `uPower` 3.0 → 6.0, `uIntensity` 1.35 → 0.72, shell radius 1.035R → 1.014R. The floor ring tube 0.045 → 0.02 units, its env intensity 1.2 → 0.7 and emissive 0.18 → 0.1. |
| Warm gold, not lemon | The globe's dots and rim, and the floor ring, take the token `gold` (#D4AF5A) instead of `goldHi` (#F1D58E). `goldHi` is the pale gold for things that must glow; on the globe it read as lemon. Still brand gold, still from the token table — no hex invented, §2.3 intact. |
| Globe too small, floating above the ring | Group scale 1.6; the seat is `ringY + 1.6 * GLOBE_RADIUS`, so the globe's lowest point rests on the ring surface at y = -0.498. |
| Add slow rotation | The globe now turns at §8.1's idle rate, 0.5°/s (one turn in twelve minutes), at every tier that allows motion. The budget's multiplier still scales the loose particles and the drift, and still gates rotation to zero under reduced motion. At T1's 0.5 the turn was 0.25°/s, which is not perceptible as motion. |
| Two hot spots look like glitches | Removed. See below — they were additive overexposure, and the diagnosis is what chose the fix. |

## The two hot spots were diagnosed, not guessed

The capture cannot be looked at from a script, and the PNG is not an image a
terminal can read, so the 00:24 capture was decoded directly and measured.

The hot spots sampled as pure saturated gold — (255, 236, 102) — which rules out
specular highlight immediately: the lacquer body's base token is `panel`
`#160E12`, near-black, and a dark metal lit by a gold bulb cannot reach 255 by
diffuse. So the crescent was the **dot field**, additively stacked: dots near the
silhouette are seen at a grazing angle and pile up in screen space, and at
`opacity 0.95` three overlapping dots saturate to white-gold. It sat at the crown
because that is where the grazing band is compressed into a narrow arc.

That diagnosis chose the fix. Culling the polar caps was rejected —
`globe_selftest.ts:53` pins pole reach as an invariant ("a whole sphere, not a
band"), and the caps were not the mechanism anyway. Instead the field is spread
and backed off: the 1.6× scale puts the same dot count over ~2.56× the screen
area, and dot opacity comes down 0.95 → 0.78 with the size 0.062 → 0.056. The
overhead point light moved up to y = 5.6 and softened 9 → 3.6, so the crown is lit
lacquer rather than a hot patch.

## Verification — measured, not eyeballed

Blown-out pixels (lum > 250) in the crown band (y 60–170, x 520–1180 — the floor
ring never enters it, so whatever is bright there is the globe):

| Capture | blown px | gold-field avg RGB | R/G | hue |
|---|---|---|---|---|
| M-D6.1 `t1.png` (before) | 305 | 229 209 98 | 1.10 | lemon — `#F1D58E` is R/G 1.10 |
| M-D6.2 `t1.png` (after) | **23** | 171 125 55 | **1.37** | warm gold — `#D4AF5A` is R/G 1.17 |
| M-D6.2 `t3.png` (after) | **22** | 193 154 72 | **1.25** | warm gold |

A 13× reduction in blown area, and the hue moves past the warm token, not toward
it by half measures. The clusters that remain above lum 248 are the floor ring at
the foot of the image, where a gold ring belongs.

| Capture | chip | gold px | bright gold px | scene fps |
|---|---|---|---|---|
| `t1.png` (measured) | `dashi-tier--t1` | 18 938 | 1 830 | 60 |
| `t3.png` (forced) | `dashi-tier--t3` | 18 836 | 8 232 | 55 |

Gold-pixel counts are lower than M-D6.1's (15 664 / 31 500) for the same reason
the hue is warmer: the deep token reflects less than the pale one, so fewer pixels
cross the capture's brightness-weighted gold test. Bright-gold pixels rising from
1 830 (T1) to 8 232 (T3) is the tier doing its job — four times the dots, one draw
call, still 55 fps on this machine's Intel HD Graphics under headless Chrome.

The globe now spans roughly x 550–1090, y 55–470 in the 1582×748 capture, centred
on x ≈ 820 against the image's 791 midline — the same centring M-D6.1 reported for
the RTL shell. Its lowest point meets the ring's far edge, which is what "seated
inside the floor ring" looks like from this camera.

Selftests: `test:globe` **8/8**, `test:stage-quality` **48/48**,
`test:truth-badge` **47/47**, `test:idea-shelf` **26/26**, `tsc` 0 errors,
`eslint` clean. No console errors in either capture.

## Not done, and why

- **Natural Earth land dots** (the 00:20 next steps) are not here; this pass was
  the QA list, and the globe's contract still says no geography. Land dots are a
  map, so when they arrive they must come from `world-atlas` / `topojson-client`
  and stay ornamental — or carry labelled data through `/api/command`.
- **The bloom chain** (M-D5.6) still stands in for the fresnel shell at all tiers.
- **`npx next build`** still not run; the 3199 dev server holds
  `data/e01_discovery.sqlite-shm`, as in M-D6.1.

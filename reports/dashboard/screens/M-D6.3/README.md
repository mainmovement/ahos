# M-D6.3 — Natural Earth land dots on the globe

- Date (Tehran): 2026-10-12 · Step: M-D6.3, the 00:20 next step on the M-D6.2 globe.
- The owner pre-approved exactly the packages this needs: `world-atlas` (ISC) and
  `topojson-client` (ISC); `three-globe` was not needed and was not added.

## What changed

The globe now traces the continents over its dust field — a second point layer,
sourced from Natural Earth polygons instead of arithmetic.

| Layer | Source | Count (T1 → T3) | Size | Shade |
|---|---|---|---|---|
| Dust (M-D6.1) | Fibonacci lattice, `globeGeometry.ts` | 6 000 → 24 000 | 0.056 | 0.72–1.0 |
| **Land (M-D6.3)** | `world-atlas/land-110m` via `topojson-client` | 1 200 → 4 800 | 0.088 | 0.88–1.0 |

Land is 20% of the dust budget, kept proportional so every tier shows the same
globe at a different resolution rather than three different objects. T3 totals
28 800 points, under the owner's 30k cap.

The atlas is **bundled, not fetched** — 55 KB of TopoJSON in the client chunk —
so §0.5's "zero external requests at runtime" still holds and §1's "no copied
art" holds with it. `land-110m` is the coarsest cut; as a *mask* for dots at this
scale its coastlines are finer than the dots themselves, so the 50m/10m cuts
would cost 10×–60× the bytes for nothing an eye can see.

## A bug the selftest caught, not me

Two assertions failed on the first run, and both were real.

**The sampler kept only the northern hemisphere.** The inside-land candidates
were subsampled with an integer stride, and land yields more candidates than any
tier asks for, so the stride rounded down to 1 and the sampler kept the
northernmost dots — leaving the whole southern globe empty. The fix is a
*fractional* stride with rounding, which spreads picks across the area-ordered
candidate list so each continent gets dots in proportion to the land it has. The
assertion stays: it still pins "reaches the polar land".

**I had assumed the Caspian and Lake Superior behave the same.** They do not:
Natural Earth at 110m carves the Caspian and the Black Sea out of the land but
leaves the Great Lakes in, so a dot or two lands on Lake Superior. My assumption
was wrong, not the decoder — the test now asserts what the atlas actually encodes
and names the imprecision, rather than burying it. If land ever has to be
geographically accurate the atlas must move to `land-50m` and that test be
rewritten against it.

## Verification

The geometry is proven without a GPU — `landDots.ts` is pure and headless, so
`test:land` can assert geography directly. 12/12: Paris/Tehran/Cape Town are
land, the mid-Atlantic and mid-Pacific are not, the Caspian and Hudson Bay are
water, every emitted dot is at the land radius **and** over land, the dots spread
across more than 60 longitude bands, and the sampler does not mutate the dust
field it samples from.

The rendering is proven by the capture's own metrics, same method as M-D6.2:

| Capture | chip | gold px | bright gold px | scene fps |
|---|---|---|---|---|
| M-D6.2 `t1.png` (no land) | `dashi-tier--t1` | 18 938 | 1 830 | 60 |
| M-D6.3 `t1.png` (land) | `dashi-tier--t1` | 21 507 | 3 376 | 60 |
| M-D6.2 `t3.png` (no land) | `dashi-tier--t3` | 18 836 | 8 232 | 55 |
| M-D6.3 `t3.png` (land) | `dashi-tier--t3` | 30 674 | 7 338 | 48 |

The layer is visible in the deltas: +2 569 gold px at T1 (+14%), +1 546 bright
gold px (+84%), which matches the arithmetic — land is 20% of the count at 2.5×
the dot area, so it should contribute about half again the dust's bright area.
The fps cost at T3 (55 → 48) is the second draw call and 4 800 more points on
this machine's Intel HD Graphics; 48 fps for an ornament that is not an
interaction surface.

Crown band (y 60–170, x 520–1180), same window M-D6.2 used:

| Capture | blown px | gold-field avg RGB | R/G | hue |
|---|---|---|---|---|
| M-D6.1 `t1.png` | 305 | 229 209 98 | 1.10 | lemon |
| M-D6.2 `t1.png` | 11 | 165 126 55 | 1.32 | warm gold |
| M-D6.3 `t1.png` | 52 | 168 129 67 | 1.30 | warm gold |
| M-D6.3 `t3.png` | 54 | 178 141 79 | 1.26 | warm gold |

The land layer is deliberately brighter, so blown pixels rise from 11 back to 52
— still 6× under M-D6.1's 305, and the hue stays on the warm side of the token.
0.07% of the band. The QA fix M-D6.2 made is intact.

Selftests: `test:globe` **8/8**, `test:land` **12/12**,
`test:stage-quality` **48/48**, `test:truth-badge` **47/47**,
`test:idea-shelf` **26/26**, `tsc` 0 errors, `eslint` clean. No console errors in
either capture.

## What the land still is not

- **It carries no data.** Brighter dots mean "this is land", nothing more. A
  token's verdict is never expressed by lighting a region — spec §2.3 forbids
  status colours as decoration, and the truth badge in the DOM says what the
  evidence said. If land has to mean something, the values must arrive through
  `/api/command` as labelled data, never as a colour change here.
- **The 110m imprecision stands** (Great Lakes; see above).
- **`npx next build`** still not run; the 3199 dev server holds
  `data/e01_discovery.sqlite-shm`, as in M-D6.1 and M-D6.2.
- **The bloom chain** (M-D5.6) still stands in for the fresnel shell at all tiers.

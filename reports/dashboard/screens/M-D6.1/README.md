# M-D6.1 — the point globe

- Date (Tehran): 2026-10-11 · Step: M-D6.1, pulled forward per the 19:42 QA list
  item 4: *"Pull M-D6 (the globe) forward right after these fixes. The owner must
  see the globe next."*
- Also serves item 3's form: *"a dotted or hex-point globe (instanced points,
  under 30k)"*, and the *"gold rim light … done in a shader or CSS"* with
  *"no heavy postprocessing on T1"*.

## What shipped

| Piece | File |
|---|---|
| The pure layout | `components/stage/globeGeometry.ts` |
| The globe itself | `components/stage/Globe.tsx` |
| The tier's dot budget | `motionBudget` in `components/stage/store.ts` |
| On the stage | `components/stage/Stage.tsx` |
| The layout selftest | `scripts/globe_selftest.ts` (8/8) |

A field of gold dots on a Fibonacci lattice, wrapped around a dark lacquer body,
hanging above the shamseh floor, with a fresnel rim along the silhouette.

The layout is the golden-angle spiral rather than random placement or a
latitude/longiture grid: random clumps, a lat/long grid piles points at the poles
and visibly rows at the equator, and the spiral is even at *any* count — so the
three tier densities read as one globe at three resolutions, not three objects.

## The globe carries no data, and that is a rule

The globe is the observatory's ornament. It renders **no geography, no continents,
no coastlines, no token markers**, because it holds no data. Its only permitted
glow is the brand gold (`themeColors.goldEmissive`) — spec §2.3 forbids status
colours as decoration, so the scene may not light a region in VERIFIED's turquoise
or a danger rim in REJECTED's red. A token's verdict is spoken by the truth badge
in the DOM, never by the stage's lighting. If the globe ever shows a marker, that
marker has to come from `/api/command` and be labelled; nothing here is wired for
it, by design.

## Tiers: density is the lever

`motionBudget` gains a `globePoints` field. Nothing else in the budget moved:

| Tier | Dots | Notes |
|---|---|---|
| T1 | 6 000 | one draw call, no postprocessing — the point globe is geometry, not the particles §11 takes away from T1 |
| T2 | 14 000 | |
| T3 | 24 000 | under the 30k the owner capped a point globe at |
| reduced motion | 6 000, static | a still globe is still a globe; only the rotation is taken away |
| T0 | 0 | the stage is never mounted (§11), so this is unreachable |

The fresnel rim is one overdrawn shell, not a bloom pass — which is why T1 may
have it too. The real bloom chain is M-D5.6's pipeline and may replace the shell
at T2/T3.

## Verification — the capture is measured, not eyeballed

The capture harness cannot be looked at from a script, so `screenshot_dashi.mjs`
now reads its own PNG back through Chrome and reports the brand-gold field: its
pixel count, its bright-gixel count, and its centroid. A globe that silently
rendered nothing would show a near-empty gold field and a centroid up in the
topbar.

| Capture | chip | canvas | gold px | bright gold px | gold centroid | scene fps |
|---|---|---|---|---|---|---|
| `t1.png` (measured) | `dashi-tier--t1` | 1 | 15 664 | 6 711 | (775, 381) | 56 |
| `t3.png` (forced) | `dashi-tier--t3` | 1 | 31 500 | 6 615 | (775, 309) | 60 |

Readings and what they prove:

- **The globe rendered.** 15.6k gold pixels at T1 against 137 k non-background
  pixels overall; before the globe the same capture carried 138 KB of PNG, after
  it 246 KB.
- **The budget did something.** Gold pixels roughly double at T3 (31.5k vs 15.6k)
  while bright-gold pixels stay flat (~6.7k) — consistent with four times the dots
  adding dim perimeter fill while the hot core saturates, which is what an
  additive dot field does as it densifies.
- **The centroid is where the globe hangs.** Horizontally centred (775 of 1582,
  within the RTL shell's centred stage), and above the image's vertical middle
  (381 and 309 of 748) as a globe hanging above the floor must be. T1's centroid
  sits lower than T3's because the floor's gold ring contributes a larger share
  of a sparser field.
- **The frame rate holds.** The harness now counts the page's own
  `requestAnimationFrame` ticks for 1.5 s — R3F drives rAF when its frameloop is
  "always", so this is the rate the owner sees, not a synthetic fill-rate figure.
  56 fps at T1 and 60 fps at T3 on this machine's Intel HD Graphics, inside
  headless Chrome, which typically caps below a real window. The 30k cap and the
  single draw call are safe here; headless numbers are a floor, not a ceiling
  claim, and a real window's rate is M-D5.6's overlay to measure.
- No console errors in either capture.

Selftests: `test:globe` **8/8** (on-sphere placement, pole reach, centroid, dot
spacing, no latitude rowing, determinism), `test:stage-quality` **48/48**,
`test:truth-badge` **47/47**, `test:idea-shelf` **26/26**, `tsc` 0 errors,
`eslint` clean.

## Not done, and why

- **The bloom chain** is not here — the fresnel shell stands in for it at all
  tiers. Item 3 allows "soft bloom done in a shader or CSS", and the shell is the
  CSS/shader answer; a real postprocessing pass at T2/T3 is M-D5.6.
- **The rings and beads** (M-D6 proper) are not here; the globe is the piece the
  owner asked to see next.
- **No data is bound to the globe**, so nothing on it can be stale or wrong — but
  it also cannot show a market state until M-D6's data rings arrive, and those
  must read `/api/command` and stay presentation-only.
- **`npx next build`** still not run; the 3199 dev server holds
  `data/e01_discovery.sqlite-shm`, as in M-D5.5 and M-D5.F.

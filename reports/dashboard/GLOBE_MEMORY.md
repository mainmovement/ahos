# GLOBE_MEMORY — the center globe's floor and its history

Read this **first**, every session, before touching anything under
`components/stage/` or `components/ahos/overview/globe-stage.tsx`. It exists so
the globe never regresses below the best state it has reached, and so a session
that has never seen the globe can still know what "good" looks like.

This agent cannot view images. Every floor below is therefore stated as
something measurable — a pixel statistic, a probe reading, a selftest — not as a
look. The reference capture is the ground truth a future session should diff
against.

## The reference capture

`reports/dashboard/screens/M-D6.6/tehran_t3.png` — 1582×748, **12 787 distinct
sampled colours**, the last stage capture before the template-first overview port
(`a5e9f8a`, 2026-10-14). It carries everything the M-D6 line built: the Tehran
mark, the matte body, the chain rings, the terminator.

Its T1 sibling `tehran_t1.png` (8 570 distinct colours, dominated by
`#0b0709`/`#140d11` — the deep stage shadow the dusk key falls out of) is the
**low-tier** floor: what the globe must still look like when this machine's
measured hardware tier drops it to T1 and the dot field thins.

The M-D5.G capture set established the gold baseline that still applies:
**15 685 gold pixels at T1, 31 412 at T3**, centroid `(775, 381)` at T1 and
`(775, 309)` at T3 — i.e. on the globe's vertical centre, not drifting.

## The floor — never go below any of these

1. **The launcher owns the stage's URL.** The globe is only proof if it is
   reachable at the address the app window opens. M-D1.1 (window never appeared)
   and M-D2.1 (window pointed at a dead port) are the two ways this breaks. If a
   capture looks empty, check `data/launcher/gateway_selected.json` and the pid
   record **before** blaming the stage.
2. **No blow-out hot patch at the crown.** The gold `pointLight` at `[0, 5.6, 0]`
   was intensity 9 on the old, smaller globe and flattened the crown to flat gold;
   M-D6.1 lowered it to 3.6 on a larger, higher globe; SOLTAN 2026-10-14 dimmed it
   to **2.2 with `distance` 12** (`8fa6f52`) after the owner reported a glow blob
   plus dots stacking at the tilted pole (the bulb sits above the pole, so the
   pole dots are the most-lit points of the body). If a capture shows a saturated
   gold disc at the top of the globe, the key light has crept back up.
   **Measurement caveat (2026-10-14):** the pixel-statistic floors below were
   written against the M-D5.G stage and are *not* comparable to the M-D6 stage —
   the CDP harness's gold count is invariant to this light (732 px on
   `/command_center` under 3.6 and 2.2 alike, because those pixels are emissive
   dots and UI accents, not point-lit lacquer). A *saturated-disc* detector, not a
   gold-count, is what floor #2 needs; `scripts/probe_crown.mjs` is the stub of
   one and still cannot tell a crown disc from warm text.
3. **No additive stacking on the land layer.** Two glow spots were traced to the
   land dots stacking additively (`4f51c21`); the fix clamps the fresnel rim's
   dot term to zero on every back-facing fragment (`4e0ff9b`). A T3 capture must
   not show dots brightening *through* the globe's far side.
4. **A matte body, not a hot one.** The body is a basic matte material since
   `4e94597`; before that, clearcoat gave an orange-red blob upper-left
   (`04da79f`). The dusk key must read as a gradient.
5. **Land legible at T1, no stacking at T3.** The T1 size/alpha ramp is
   measured on the canvas band (`7619b65`); lowering the night floors (`bfab049`)
   keeps the night side reading as night.
6. **The globe seats inside the floor ring, crown clear** (`73a7f85`).
7. **The atmosphere uses the vendor kit's own defaults** (`36c289f`), not
   hand-tuned values; the land dots are Natural Earth via the vendor pipeline
   (`4b1b0da`), cobe-style.
8. **The Tehran mark sits where the atlas says** (`4e94597`): on the
   northern/eastern half, never on a land dot and never outside the atmosphere.
   `scripts/tehran_selftest.ts` pins this.
9. **A lost WebGL context degrades, never crashes** (M-D5.4): the shell's panels
   are DOM and survive, and the stage offers recovery in one click.

## History — the M-D6 line, newest first

| Commit | Date (Tehran) | What it established |
|---|---|---|
| `8fa6f52` | 2026-10-14 08:36 | SOLTAN crown dim: pointLight 3.6/16 → 2.2/12; the CDP gold-count baseline proven invariant to this light, so the M-D5.G pixel floors are retired as a crown proxy |
| `ae75ca5` | 2026-10-14 07:44 | `next build` passes (tsconfig excludes vendor_assets; unreachable template components removed); the gateway now runs `next start` |
| `a5e9f8a` | 2026-10-14 05:17 | template-first overview; the stage now lives in `components/ahos/overview/globe-stage.tsx` behind `StageLazy`, gated on a measured quality verdict (T0 with no verdict shows the 2D fallback, not a broken canvas) |
| `4e94597` | 2026-10-13 21:28 | M-D6.6 Tehran mark + matte body |
| `b08c724` / `b740a6d` | 2026-10-13 17:07–17:12 | M-D6.4 the mask's v axis — the continents were upside down |
| `04da79f` | 2026-10-13 13:44 | matte body removes the orange-red blob |
| `7619b65` | 2026-10-13 11:40 | T1 land size/alpha ramp, measured |
| `c44668e` | 2026-10-13 09:38 | clearcoat hot spot attributed correctly to lighting |
| `90a3d4a` | 2026-10-13 00:58 | M-D6.5 chain rings from the vendor reference |
| `36c289f` | 2026-10-13 00:03 | atmosphere at vendor defaults |
| `a0ca3f3` | 2026-10-12 22:39 | vendor fresnel atmosphere + cobe land dots |
| `5408f4f` | 2026-10-12 17:49 | the glow-spot ablation harness (eight T3 shots) |
| `bfab049` | 2026-10-12 14:47 | night floors lowered |
| `2550aae` | 2026-10-12 14:13 | T1 legible without a T3 stacking reason |
| `4f51c21` | 2026-10-12 13:55 | the two glow spots were additive stacking |
| `4e0ff9b` | 2026-10-12 12:51 | fresnel rim clamps dot to zero back-face |
| `73a7f85` | 2026-10-12 08:56 | globe seats in the floor ring |
| `eb5ec75` | 2026-10-12 03:48 | M-D6.4 real day/night terminator |
| `4b1b0da` | 2026-10-12 02:35 | M-D6.3 Natural Earth land dots |
| `1a2f4bb` | 2026-10-12 01:13 | M-D6.2 the 00:24 owner QA pass |
| `d6a8ca2` | 2026-10-11 23:51 | M-D6.1 the point globe — gold dots on a Fibonacci lattice |
| `54dcd3c` | 2026-10-11 14:28 | M-D5.2/M-D5.3 the stage renders, probe honest |

## How to capture the globe faithfully

`CopyFromScreen` full-screen captures (the `windows_screenshot.ps1` path) include
everything on the desktop and cannot wait on the stage's own readiness —
M-D2.1's capture carried 9.3% unexplained near-white from exactly that. The
faithful path is Chrome over the DevTools protocol, waiting for the tier chip to
leave "pending" and a `<canvas>` to appear (`scripts/screenshot_dashi.mjs`); that
harness reports the gold pixel count and centroid, the scene fps, and any console
errors, which are the numbers this file's floors are written against. **A capture
without those numbers is not evidence of a globe.**

## Open debt against the floor

- ~~`next build` fails on this checkout and the launcher degrades to `dev`.~~
  **Closed 2026-10-14 (`ae75ca5`)**: the build passes and the gateway runs
  `next start`. Consequence for stage work: a `Stage.tsx` edit is **not served**
  until you rebuild — `launcher stop`, `npm run build`, `launcher start`. Two
  captures taken mid-edit will silently show the pre-edit bundle.
- The faithful CDP capture has been run against the overview at `/`
  (`8fa6f52`, goldPx 5508 / brightGoldPx 2033 / fps 41–45 / no console errors),
  but the pixel statistics that back floors #2 and the M-D5.G baselines are
  stale for the M-D6 stage (see floor #2's caveat). A saturated-disc detector
  that actually discriminates the crown blow-out is still owed.

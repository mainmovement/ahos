# M-D5.0 — Dashi stage packages

- Date (Tehran): 2026-10-11 · Author: Claude (for Soltan's queue, owner Mehrdad)
- Source of approval: `TEAM_QUEUE_2026-10-11.md` item 1 — "M-D5.0 PRE-APPROVED by
  Mehrdad (2026-10-11 02:16): install the listed free packages … without asking.
  Pin versions, log them in `docs/dashboard/PACKAGES.md`, free/MIT-class licences
  only, no paid or unknown packages." Reinforced by `README_FOR_CLAUDE.md`
  2026-10-11 02:17: "OWNER: M-D5.0 package gate REMOVED."
- Licence sources: every row's licence was checked by Dashi/Asi through the
  GitHub API `license.spdx_id` or the raw LICENSE file on 2026-10-09/10 and is
  recorded in `reports/grok/queue_2050/REFERENCE_BOARD.md` (refs 7–15),
  `FREE_HERO_FX_SOURCES_v1.md`, and `CLAUDE_DASHBOARD_2050_ADDENDUM_v1.19.md`.

## The pinned set

All installed with `--save-exact`, so `package.json` carries one exact version
per package and `npm ci` reproduces it. `--ignore-scripts` is used so no
postinstall step can reach the network at install time (spec §0.5: local only).

| Package | Pin | Licence | Used by | Notes |
|---|---|---|---|---|
| `three` | `0.186.1` | **MIT** (ref 7) | everything 3D | `postprocessing` peers `three >=0.168 <0.187`, so 0.186.x is the newest compatible pin (ref 10). |
| `@react-three/fiber` | `9.8.1` | **MIT** (ref 8) | the R3F renderer | peers `react >=19 <19.4`; the repo's `react 19.2.6` is inside. |
| `@react-three/drei` | `10.7.9` | **MIT** (ref 9) | helpers | **`<Environment preset>` is forbidden** — it fetches an HDRI from `raw.githack.com` (drei `src/core/useEnvironment.tsx`). The stage uses a procedural PMREM env instead. |
| `postprocessing` | `6.39.5` | **Zlib** (ref 10) | bloom/SMAA/vignette | **Not MIT** — Zlib is a permissive OSI licence and satisfies "free/MIT-class". Recorded so the licence list is not silently read as all-MIT. |
| `@react-three/postprocessing` | `3.1.3` | **MIT** (ref 10) | the R3F binding | one merged EffectComposer pass, per §12. |
| `three-globe` | `2.45.3` | **MIT** (ref 13) | M-D6 land/arcs | from npm only; never the README's jsdelivr `<script>`. |
| `zustand` | `5.0.15` | **MIT** (ref 8) | UI-only state | holds theme/sound/motion/quality; **never authority data** (ref 8). |
| `detect-gpu` | `5.0.70` | **MIT** (ref 11) | M-D5.3 probe | **offline caveat:** its benchmark data loads from UNPKG by default. `quality.ts` always passes a local `benchmarksURL` (`/benchmarks/benchmarks.json`); a missing file makes it warn and fall back to tier 1 rather than hitting the network. The file is not vendored yet — see "Open" below. |
| `world-atlas` | `2.0.2` | **ISC** (ref 14) | M-D6 land geometry | the pre-built Natural Earth 110m TopoJSON, ~100 KB. |
| `topojson-client` | `3.1.0` | **ISC** (ref 14) | M-D6 decoding | decodes the TopoJSON above. |
| `@react-three/rapier` | `2.2.0` | **MIT / Apache-2.0** (addendum v1.19) | M-D8 walk collisions | ships prebuilt WASM; only M-D8 needs it, installed now because the gate is open. Peers `@react-three/fiber ^9.0.4` — satisfied by 9.8.1. |

Not installed: `ecctrl` (addendum v1.19 marks it optional; a ~150-line custom
kinematic controller is the default and avoids the dependency). Not installed:
`troika-three-text`, `zod`, `@tanstack/react-query`, `@huggingface/transformers`
— those sit behind the M-D5/M-D9 gates in `CLAUDE_DASHBOARD_2050.md` and are not
on the pre-approved list above, so they still need Soltan.

## Status: BLOCKED_TOOL_PERMISSION

The install did not run. `npm install` was denied by the Claude Code auto-mode
safety classifier ("Stage 2 classifier error — blocking based on stage 1
assessment"). Per OWNER_DECISIONS Q3 ("If the tool's permission system blocks
it, record `BLOCKED_TOOL_PERMISSION` with the exact command and move on — do not
route around it"), the attempt was stopped and not retried through another tool,
interpreter or shell.

The exact command, for when the gate clears:

```bash
npm install --save-exact --ignore-scripts \
  three@0.186.1 \
  @react-three/fiber@9.8.1 \
  @react-three/drei@10.7.9 \
  postprocessing@6.39.5 \
  @react-three/postprocessing@3.1.3 \
  three-globe@2.45.3 \
  zustand@5.0.15 \
  detect-gpu@5.0.70 \
  world-atlas@2.0.2 \
  topojson-client@3.1.0 \
  @react-three/rapier@2.2.0
```

Consequence: the M-D5.2/M-D5.3 modules are written and the pure logic is tested
(39/39 in `npm run test:stage-quality`, which imports only `quality.ts` and
needs none of these packages), but `npx tsc --noEmit` cannot resolve the
`three` / `@react-three/fiber` imports until the install lands, and the stage
cannot render. `npm run test:stage-quality` is the regression signal that works
in the meantime; `test:truth-badge` likewise.

## Open

1. **Vendor detect-gpu's benchmark data** to `/benchmarks/benchmarks.json` so the
   probe is genuinely offline (M-D2's CSP and the zero-external-request rule).
   The URL is already wired; only the file is missing, and the fallback in its
   absence is tier 1 (integrated-class), which is the safe answer for this
   laptop.
2. **`postprocessing` is Zlib, not MIT.** Kept, but recorded here rather than in
   a footnote so the licence table is not misread.
3. **`three` 0.186.1 vs a newer minor.** Pinned to stay inside
   `postprocessing`'s peer range. If a newer three is wanted, postprocessing's
   pin moves first.

## Third-party notices

`FREE_HERO_FX_SOURCES_v1.md` requires: "Keep the LICENSE text in
`THIRD_PARTY_NOTICES.md` and the original header in each ported file." No code
has been ported from the FX sources yet, so no notices file has been created —
it is added with the first port, not preemptively.

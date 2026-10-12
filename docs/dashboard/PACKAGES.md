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
| `detect-gpu` | `5.0.70` | **MIT** (ref 11) | M-D5.3 probe | **offline caveat:** its benchmark data loads from UNPKG by default, and `benchmarksURL` is a *directory* it fetches `${url}/${model}.json` from per GPU family. `quality.ts` always passes the local `public/benchmarks/` (all 16 files vendored, 713 KB). Only a `type: "BENCHMARK"` result counts as a measurement — `FALLBACK`/`SSR` are the library guessing and are read as null, never as a tier. |
| `world-atlas` | `2.0.2` | **ISC** (ref 14) | M-D6 land geometry | the pre-built Natural Earth 110m TopoJSON, ~100 KB. |
| `topojson-client` | `3.1.0` | **ISC** (ref 14) | M-D6 decoding | decodes the TopoJSON above. |
| `@react-three/rapier` | `2.2.0` | **MIT / Apache-2.0** (addendum v1.19) | M-D8 walk collisions | ships prebuilt WASM; only M-D8 needs it, installed now because the gate is open. Peers `@react-three/fiber ^9.0.4` — satisfied by 9.8.1. |
| `echarts` | `6.1.0` | **Apache-2.0** (owner's vendor kit, `vendor_assets/charts/echarts-6.1.0`) | M-D7 evidence graph | added 2026-10-12 for the force-layout graph, per the 18:00 rule (take the vendor kit's chart lib rather than hand-writing a force simulation). Only `GraphChart` + `TooltipComponent` + `CanvasRenderer` are imported from `echarts/core`, so the bundle carries those and not the whole library. The vendor copy in `vendor_assets` is the same version — the pin and the kit agree. |

Not installed: `ecctrl` (addendum v1.19 marks it optional; a ~150-line custom
kinematic controller is the default and avoids the dependency). Not installed:
`troika-three-text`, `zod`, `@tanstack/react-query`, `@huggingface/transformers`
— those sit behind the M-D5/M-D9 gates in `CLAUDE_DASHBOARD_2050.md` and are not
on the pre-approved list above, so they still need Soltan.

## Status: INSTALLED (2026-10-11 10:04)

The install was run by Soltan on the laptop with the exact command below
(`--save-exact --ignore-scripts`, 99 packages added). All 11 pins verified present
at their exact versions in `node_modules`:

```
three 0.186.1 · @react-three/fiber 9.8.1 · @react-three/drei 10.7.9
postprocessing 6.39.5 · @react-three/postprocessing 3.1.3 · three-globe 2.45.3
zustand 5.0.15 · detect-gpu 5.0.70 · world-atlas 2.0.2
topojson-client 3.1.0 · @react-three/rapier 2.2.0
```

`npx tsc --noEmit` is clean (0 errors; it was 46 while the packages were
missing). `npm run test:stage-quality` 39/39, `test:truth-badge` 44/44.

The earlier `BLOCKED_TOOL_PERMISSION` (the Claude Code auto-mode safety
classifier denied `npm install`; OWNER_DECISIONS Q3 — recorded, not routed
around) is cleared. It is kept here as the record of why the M-D5.2 stage spent
a night written-but-unrendered.

The exact command that was run:

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

## Open

1. ~~**Vendor detect-gpu's benchmark data**~~ — **DONE.** `public/benchmarks/`
   now holds all 16 JSONs (713 KB) copied from `detect-gpu/dist/benchmarks/`,
   and `BENCHMARKS_URL` points at the directory. Two details mattered: the URL
   is a *directory* (detect-gpu fetches `${url}/${model}.json` per GPU family),
   not the single `benchmarks.json` path the doc first assumed; and only a
   `type: "BENCHMARK"` result is treated as a measurement, because `FALLBACK`
   and `SSR` are detect-gpu guessing.
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

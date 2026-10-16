# AHOS Pulse Orb v2

Self-contained Next.js 16 / React 19 / strict TypeScript / Tailwind 4 app with the `<PulseOrb />` calm-technology visualization. All runtime assets, including Natural Earth-derived GeoJSON, are bundled locally; the app does not call an external service.

## Run and verify

Requires Node.js 22.6+ (for the script-based TypeScript tests).

```bash
npm ci
npm run dev                 # binds 0.0.0.0:3000
npm run typecheck           # strict TypeScript, no explicit any
npm test                    # Node script-based unit tests
npm run build
```

Demo and control panel: `/orb-demo`.

## Component API

```tsx
<PulseOrb
  health={{ bpm: 60, jitterMs: 0, stale: false }}
  departments={[{ id, nameFa, rate, queue, lastDataAt, confidence, status }]}
  signals={[{ id, deptId, at, outcome, reason }]}
  gate={{ absorbed: 12, dissipated: 3, strictness: 0.8 }}
  calm={true}                 // default true
  quality="medium"           // low / medium / high
  morphed={false}             // optional controlled map toggle
  onMorph={(isMap) => {}}     // optional
/>
```

Quality chooses a fixed GPGPU texture at mount: low 64×64 (4,096), medium 128×128 (16,384), high 256×256 (65,536). It is intentionally mount-time configuration: changing it requires remounting the component. Health, signals, gate, department and calm changes use refs/textures and do not recreate the renderer or GPGPU scene. The demo includes a 50-update check; a Playwright harness compares the renderer-creation counter.

## Implementation and verification

- Fixed-capacity particle texture. Unassigned slots are dim ambient dust; signals only set metadata for selected particles. Calm mode caps highlighted items across departments/signals at seven and shows an overflow count.
- Map targets are generated from bundled country polygons using d3-geo `geoPath`, `geoCentroid`, `geoBounds`, and `geoContains`; boundaries and polygon interiors are sampled. Iran target samples are gold. Morph interpolates continuously in both directions.
- Twelve distinctly spaced, tilted department rings. Queue controls thickness, rate controls individual rotation speed. Ring labels appear on hover/focus; status patterns and age fog are rendered in WebGL and SVG fallback.
- Gate arc uses `gate.strictness` when supplied, otherwise `dissipated / (absorbed + dissipated)` (0.5 if no counts).
- Fallback includes ring patterns/fog, signal dots, gate arc, DEMO badge, and equivalent accessible department/signal tables.
- Renderer creation is instrumented as `window.__pulseOrbRendererCreations` and on the scene container as `data-renderer-creations`.
- No eslint configuration/dependency is present, so the lint script is intentionally omitted rather than left broken.
- `sharp` is an optional transitive dependency of Next.js, not imported or used directly (this app does not use `next/image`). If a package manager blocks lifecycle scripts, allow Sharp's install/build script in its `allowScripts`/build allowlist; otherwise Next's optional image optimization may be unavailable. The visualizer does not depend on it.

## Browser screenshots and UNVERIFIED items

Capture the requested 1600×900 calm, breach, and map screenshots and run the 50-prop renderer check with:

```bash
# Terminal 1
npm run dev
# Terminal 2 (requires Playwright Chromium installed)
npm run screenshots
```

**UNVERIFIED in this workspace:** no Chromium/Chrome executable or GPU browser is available, so I could not run the browser script, generate genuine screenshots, inspect recognizable continents/Iran visually, or verify runtime WebGL/GPGPU behavior and FPS. `docs/screens/README.md` records this limitation; it intentionally contains no fabricated screenshot evidence. `npm test` passed 12 script-based tests covering fixed texture sizes/independence, geometry-derived map samples including Iran, gate strictness, calm attention budget, ring spacing/speeds, and the renderer initialization contract. The Playwright comparison of 50 live prop updates is implemented but not run without a browser. Typecheck, production build, and npm audit (0 vulnerabilities) passed.

# AHOS Intelligence Command Deck

**Evidence First. Intelligence in Motion.**
**هوش عملیاتی؛ مبتنی بر شواهد، نه حدس.**

A premium, cinematic, **evidence-first** intelligence command environment.
Persian-first (RTL), English-second. **PAPER-ONLY. Local-first. Free-first.**
No real-money execution, no live backend, no telemetry, no external runtime
dependencies.

This project is a **completely separate application**. It does not import,
modify, or contact any existing AHOS project (`ahos`, `ahos_arena`,
`AHOS_Launcher`), port `3200`, port `8787`, or any database.

---

## 1. What this is (and is not)

| It IS | It is NOT |
| --- | --- |
| A local, offline, paper-only display & research deck | A live trading terminal |
| A demonstration of an honest data-provenance system | A source of real market data |
| A UI/UX reference implementation for the AHOS design language | A connection to any AHOS backend |
| A readiness-*assessment* surface (verdict locked at NOT AUTHORIZED) | An authorization or execution mechanism |

Every number you see is either:

- `SAMPLE` — deterministic, frozen, seeded demo data (dataset
  `ahos-demo-2026-10`, anchored at `2026-10-31T14:30:00Z`), always visibly
  labeled, watermarked on charts; or
- `NOT MEASURED` / `NOT CONNECTED` / `STALE` / `QUARANTINED` / `UNVERIFIED` /
  `UNKNOWN` — honest absence states. **Missing values are never replaced by
  zero, a fabricated percentage, a fabricated price, or a fabricated health
  indicator.**

The only `MEASURED` facts in the app are facts about the app itself (e.g. how
many desks are configured).

---

## 2. Technology stack

- **Next.js 15** (App Router, static prerender, route-level `dynamicParams`)
- **TypeScript** strict mode
- **Tailwind CSS 3.4** + CSS-variable design tokens (dark/light themes)
- **shadcn/ui-style components** hand-built on Radix primitives (Dialog, Sheet,
  Select, Dropdown, Popover, Tabs, Switch, Tooltip) + `cmdk` command palette
- **Framer Motion** available; CSS animations preferred for ambient effects
- **Recharts** for line/area/bar charts
- **TradingView Lightweight Charts v4** for candlesticks (desk detail)
- **Three.js** (direct, no react-three-fiber) for the cinematic command-center
  globe — lazily loaded, `ssr: false`, error boundary + 2D fallback
- **Zod** runtime validation of the entire frozen dataset (unit-tested)
- **Vitest** unit tests
- Fonts: **Vazirmatn** (Persian) and **Inter variable** (Latin), bundled
  locally under `public/fonts` (OFL licenses, notices in `public/fonts/LICENSE.md`).
  No remote fonts, no CDNs.

---

## 3. Getting started

```bash
npm install          # install dependencies
npm run dev          # development server on http://localhost:3300
npm run build        # production build (also runs type checking)
npm run start        # serve the production build on :3300
npm run lint         # ESLint (next/core-web-vitals + strict TS rules)
npm run typecheck    # tsc --noEmit (strict)
npm test             # Vitest: RNG determinism, i18n parity, dataset contracts,
                     # adapter-disabled guarantees, readiness-gate logic
npm run gen:earth    # regenerate the procedural Earth land mask
                     # (build-time only; needs the world-atlas dev dependency)
npm run shots        # browser screenshots of every page (dev tool)
```

**Port: 3300.** The app never touches `3200` or `8787`. If 3300 is occupied,
`next` will fail to bind — free it or pass an explicit alternate port; the app
never terminates other processes.

Requires Node 20+. Runs comfortably on a 4-core / 8 GB laptop: the production
first-load JS is ~100 kB shared (Command Center route ~270 kB including the
chart libs), the 3D scene loads lazily and pauses when the tab is hidden.

---

## 4. Project structure

```
app/
  layout.tsx                 root not-found (bilingual-safe static page)
  globals.css                design tokens, fonts, panels, hatches, utilities
  icon.svg                   original AHOS emblem (favicon)
  [locale]/                  fa | en — all pages live under the locale segment
    layout.tsx               html dir/lang, providers, shell, static params
    page.tsx                 Command Center
    desks/page.tsx           Intelligence Desks
    desks/[deskId]/page.tsx  Desk Detail (7 static desks × 2 locales)
    positions/page.tsx       Positions & Trades
    intelligence/page.tsx    Market Drivers & Intelligence News
    readiness/page.tsx       Gold Readiness Gate
    health/page.tsx          System Health & Soak
    settings/page.tsx        Settings
components/
  ui/                        buttons, panels, dialogs, sheets, selects, …
  layout/                    app shell, sidebar rail, top bar + status strip,
                             command palette, page header
  status/                    StatusBadge, ProvenanceChip, ProvenancePanel,
                             SignalBadge, EmptyState
  brand/                     original Lion & Sun emblem (SVG)
  providers/                 locale, settings (localStorage), theme
  visualization/             chart frame (SAMPLE watermark), candle chart,
                             sparkline, globe/
                               globe-stage.tsx    cinematic chamber shell: city
                                                  skyline, operator silhouette,
                                                  Lion&Sun reticle, scanlines,
                                                  vignette, ambience dock
                               command-room-scene.tsx  3D operations room:
                                                  console ring + staff + curved
                                                  video wall + commander
                               earth-hologram.ts  shared photoreal Earth kit
                               scene-utils.ts     deterministic helpers + grade
                               globe-scene.tsx    the Three.js scene: photoreal
                                                  Earth (bundled NASA day/night
                                                  textures, day/night cycle, ocean
                                                  glint, cloud shell), volumetric
                                                  projector beam, embers, holo scan,
                                                  gyro rings, orbit gates, arcs,
                                                  dust, bloom + grade pass (grain,
                                                  vignette, aberration), anchored
                                                  asset chips
                               globe-fallback.tsx 2D SVG fallback
                               earth-mask.ts      generated land mask
features/
  command-center/            command stage (globe + HUD wings), KPI grid,
                             charts, dataset banner
    hud/                     floating HUD panels: System Overview, Live Feed,
                             Top Opportunities, Market Intelligence mini-chart,
                             AI Intelligence prompt (all envelope-driven)
  desks/                     desks grid, desk detail
  positions/                 positions table + drawer + CSV
  intelligence/              news feed + driver board
  readiness/                 readiness gate (verdict locked)
  health/                    services, checks, soak timeline, resources
  settings/                  settings form
lib/
  types/                     all domain contracts (DataEnvelope, provenance…)
  schemas/                   Zod schemas + honesty invariants
  provenance/                envelope constructors + tone mapping
  data/                      frozen deterministic dataset (seeded RNG)
  adapters/                  DISABLED backend adapter boundary (:8787)
  i18n/                      config + fa/en dictionaries (parity-tested)
  formatters/                deterministic numbers, dates, CSV
  visualization/             ambience presets
public/
  brand/                     brand SVGs
  fonts/                     Vazirmatn + Inter (local, OFL)
evidence/
  screenshots/               real-browser screenshots (generated)
  functional-report.json     functional check results (generated)
scripts/
  generate-earth-mask.mjs    builds the land mask from world-atlas (build-time)
  capture.mjs                playwright-core + npm-bundled Chromium screenshots
  functional-check.mjs       end-to-end functional verification
tests/                       Vitest suites
```

---

## 5. The provenance system (the core idea)

`DataEnvelope<T> = { value: T | null; provenance: DataProvenance }`

`DataProvenance = { status, source, observedAt, reason, confidence, note? }`

Statuses: `MEASURED · SAMPLE · NOT_MEASURED · NOT_CONNECTED · STALE ·
QUARANTINED · UNVERIFIED · UNAVAILABLE · EXCLUDED · UNKNOWN`.

Rules enforced in code and by tests:

- Every `SAMPLE`/`STALE`/`UNVERIFIED` envelope must carry the dataset
  timestamp — never `Date.now()`. The wall clock is never read for data.
- `value === null` renders an explicit absence (`—` + status label). Zeros are
  semantic values only where genuinely zero.
- Every mock-driven panel shows a persistent, visible `نمونه / SAMPLE` label;
  sample charts carry a watermark; sample tables carry status badges.
- Position accounting preserves `NET = GROSS − FEES + FUNDING` exactly; missing
  fees/funding ⇒ `NET` is `null` (not computed, not zero). Zod rejects any
  violation, and tests pin it.
- Model scores are raw and explicitly `calibrated: false`; the Brier score is
  `NOT MEASURED` everywhere because calibration evidence does not exist.
- Unknown security/health state never renders as PASS/HEALTHY.
- The soak timeline shades `EXCLUDED` and `QUARANTINED` windows and labels them.

To make a panel honest, route its data through
`lib/provenance/envelope.ts` constructors (`sample`, `notMeasured`,
`notConnected`, `stale`, `quarantined`, `unverified`, `measured`) and render it
via `ProvenanceChip` / `StatusBadge` / `EnvelopeValue`.

---

## 6. PAPER-ONLY safety

- There is no order entry, no close/edit-trade action, no wallet action, and no
  execution code path anywhere in the codebase (verified by a functional test
  that asserts no such buttons exist).
- The global top bar permanently shows `PAPER-ONLY` (فقط کاغذی) and
  `Execution Mode: DISABLED — DISPLAY ONLY`, `Kill Switch: NOT CONNECTED`.
- The Gold Readiness page verdict is a **constant**
  `NOT READY / NOT AUTHORIZED`. A demonstration toggle may paint checklist
  items as PASS, but the verdict cannot move — pinned by unit tests.
- CSV export works only on the local sample dataset, and its header row states
  that it is a PAPER-ONLY sample export.

---

## 7. Backend adapter boundary (future, disabled)

`lib/adapters/ahos-adapter.ts` defines the future-compatible interface for a
real AHOS backend at `http://127.0.0.1:8787`:

```ts
interface AhosBackendAdapter {
  fetchSystemSnapshot(req): Promise<unknown>;
  fetchDesk(deskId): Promise<unknown>;
}
```

In this build the adapter is `enabled: false`, `adapterRegistry.active` is
`null`, and both methods throw `AdapterDisabledError`. A unit test fails CI if
anything ever activates it. Nothing probes `localhost:3200/8787`; the app
merely *displays* those endpoints as `NOT MEASURED` / `NOT CONNECTED`.

To integrate later (separately authorized build only): implement the interface
against a real backend, set `adapterRegistry.active`, and replace envelope
constructors at the `lib/data/` layer. The UI components do not change.

---

## 8. Replacing mock data safely

1. All mock data lives in `lib/data/*` and is generated from fixed seeds
   (`mulberry32` + string-derived seeds). No `Math.random` anywhere — rebuilds
   are byte-identical.
2. Change or replace a dataset module, keep the `DataEnvelope` shape, keep the
   frozen `DATASET.asOf` anchor consistent with the data you provide.
3. Run `npm test` — the Zod contract suite validates every collection
   (positions keep the NET identity, SAMPLE values carry timestamps, etc.).
4. Never import wall-clock time into a dataset module.

---

## 8b. The cinematic command stage (Phase D)

**Three simulated 3D views** (toggle at the head of the stage dock, persisted as
`sceneView`):

- **اتاق عملیات / Ops Room** (default) — a full 3D operations floor in plain
  Three.js with a **rigged human cast** (unmodified MIT demo assets from the
  three.js repo — Soldier, Michelle, Kira and a Ready Player Me avatar; see
  `public/models/humans/LICENSE.md`): one animated person per role desk
  (12 roles — gold, crypto, memecoin, oil, Europe, US/NASDAQ, Asia, newsroom,
  white-hat security, red team, research, briefing officer), patrol walkers
  with real walk cycles, door guards, a field journalist with a camera rig,
  a commuter entering through the **sliding entrance doors**, and the
  commander's avatar at the holographic Earth podium. A **glass curtain wall**
  looks out on a procedural city (instanced night-lit towers, river, bridge,
  moving car lights, drifting clouds) whose sky, sun/moon, stars, rain and
  snow are driven by **real weather for دزفول / خوزستان (Open-Meteo)** and
  the **real Tehran clock** — clear/partly/cloudy/fog/rain/snow and night/
  dawn/day/dusk phases, exactly as outside. Every console screen, touch
  tablet and wall board is a live canvas texture.
- **نمای فضا / Space View** — the orbital chamber: the photoreal Earth
  (below) framed by city skyline, operator silhouette and platform sigil.
- **نمای فرمانده / Commander Cam (FPV)** — eye-level camera at the
  commander's position facing the hologram and the console ring; drag to
  look around.

### Live public-data layer (honest by construction)

Room screens subscribe to a client-side market bus (`lib/live/market-bus.ts`)
polling **public, key-less, CORS-open** endpoints — Binance → OKX → CoinGecko
(crypto + PAXG), gold-api.com (spot XAU), Yahoo Finance via the allorigins
mirror (WTI/Brent/DAX/FTSE/Nikkei/Shanghai/NASDAQ/S&P 500), Open-Meteo
(Dezful weather) and BBC Persian RSS (wire headlines). Wall boards show the
**demo holdings × live prices** (labeled as demo), a world-market grid, and a
4-zone world clock (تهران · نیویورک · پکن · برلین). Clicking any floating
role chip — or any desk tablet — opens that workstation's panel with its
assets, live tape and data status.

Honesty contract of the live layer: when a source answers, values are real
and tagged with the source name + update time; when it does not, screens
show blanks / «متصل نیست» — **no fabricated numbers ever**. Holdings are a
demo constant; the UI always says so. The frozen AHOS dataset still powers
every page outside the stage, and desks labelled security / red team /
research display the internal SAMPLE notice, never market data.

The space view renders a full-bleed "command chamber": a photoreal Earth
(plain Three.js — no React Three Fiber) built from bundled NASA imagery —
Blue Marble day texture, Black Marble night lights, a water mask for ocean sun
glint and a drifting cloud shell — lit by a single sun direction so the
day/night terminator is real. Around it: a volumetric projector beam rising
from a light-well platform, rising embers, a travelling holographic scan band,
gyro rings, orbit gates with comet trails, data packets on city-to-city arcs,
ambient dust, nebulae, bloom and a final grade pass (film grain, vignette,
chromatic aberration). DOM/SVG layers: city skyline, operator silhouette, the
Lion & Sun platform sigil, HUD corner brackets, scanlines. Floating HUD panels
overlay the stage on wide screens (System Overview, Live Feed, Top
Opportunities, System Health rings, Market Intelligence mini-chart, AI
Intelligence) and stack below it on narrow ones. A recent-events ticker runs
along the stage floor; the dock switches simulated day-phase ambience (شب /
سپیده‌دم / روز / غروب) and cycles a decorative season tint (بهار/تابستان/پاییز/
زمستان). Earth textures are static, bundled, and credited in
public/textures/LICENSE.txt — no network is used at runtime.

Honesty rules preserved in the stage:

- The scene is decorative only — the page remains fully usable with it off
  (eye toggle in the corner, `sceneEnabled` pref, reduced-motion → 2D fallback,
  WebGL failure → 2D fallback via error boundary).
- Chips pinned to the globe (XAU/BTC/ETH/SOL) are **asset labels**, not prices.
- "Live Feed" and "Top Opportunities" carry SAMPLE badges and read from the
  same frozen dataset; "System Overview" counts app configuration (MEASURED)
  and marks everything operational as NOT_CONNECTED / NOT_MEASURED.
- The bottom dock switches simulated ambience presets (شب/سپیده‌دم/روز/غروب);
  it changes lighting only, never data or timestamps.

---

## 9. Internationalization & accessibility

- Persian (`fa`) is the default locale and the dictionary source of truth;
  English (`en`) is type-checked (`Dictionary` type) and parity-tested.
- Middleware redirects `/` → `/fa`; every route is `/fa/...` or `/en/...`.
- `html[dir]` switches rtl/ltr; layouts use logical properties (`ms-`, `me-`,
  `start-`, `end-`); technical identifiers are `dir="ltr"` isolated.
- Numbers/dates are formatted by a deterministic, `Intl`-free formatter
  (Persian digits `۰-۹` and Persian month names in `fa`).
- WCAG 2.2 AA as the target: keyboard navigation, visible focus rings,
  semantic landmarks/tables, `aria-sort`, `aria-current`, accessible dialogs,
  non-color-only status glyphs, chart summaries and tabular alternatives,
  `prefers-reduced-motion` respected (plus an explicit motion setting).

---

## 10. Known limitations

- All data is sample or honestly-absent; there is no live source of any kind.
- The 3D scene is decorative; it degrades to a static 2D fallback without
  WebGL, under reduced motion, or when disabled in Settings.
- The readiness verdict is intentionally immutable in this build.
- i18n coverage is UI-complete, but RTL chart mirroring is deliberately not
  applied inside chart plot areas (axes remain LTR for numeric legibility).
- Screenshots in `evidence/` were captured with a headless bundled Chromium
  (SwiftShader GL); real hardware GPUs render the same scene faster.

---

## 11. Licenses

- Project code: part of the AHOS workspace (see repository policy).
- Vazirmatn & Inter fonts: SIL Open Font License 1.1 — see
  `public/fonts/LICENSE.md`.
- Earth land mask: generated at build time from Natural Earth data via the
  `world-atlas` npm package (public domain).

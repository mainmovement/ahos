# AHOS Dashboard — Merge Guide

Persian-first (RTL) AI market-intelligence **command center** for AHOS.
Desktop-app style, **paper-only**, every value carries an explicit data status.
All data in this build is **mock** (`src/mock`) and is labelled **DEMO** in the UI.

> This folder is a self-contained Next.js app inside the AHOS repository
> (`ahos-dashboard/`). It does not modify or import anything from the root app.
> The only root changes are two ignore entries (see §9).

---

## 1. Stack & versions

Versions are pinned to match the root AHOS app where they overlap, to make the merge painless.

| Package | Version | Role |
|---|---|---|
| next | 16.2.6 | App Router, server components, `next/font/local`, `next/dynamic` |
| react / react-dom | 19.2.6 | UI runtime |
| typescript | 5.9.3 | strict mode + `noUncheckedIndexedAccess` |
| tailwindcss / @tailwindcss/postcss | 4.1.17 | CSS-first tokens via `@theme`, container queries |
| eslint / eslint-config-next | 9.39.4 / 16.2.6 | core-web-vitals + typescript + React Compiler rules |
| radix-ui | 1.8.1 | shadcn-style primitives (Dialog, Popover, Dropdown, Tooltip, Tabs, Switch, Slider, ToggleGroup, Direction) |
| cmdk | 1.1.1 | Ctrl+K command palette |
| class-variance-authority / clsx / tailwind-merge | 0.7.1 / 2.1.1 / 3.7.0 | variant + class utilities (`cn()`) |
| lucide-react | 1.57.0 | icons |
| echarts / echarts-for-react | 6.1.0 / 3.0.6 | charts (tree-shaken `echarts/core`) |
| three / three-globe | 0.186.1 / 2.45.6 | 3D Earth (client-only, lazy) |
| d3-geo / topojson-client / world-atlas | 3.1.1 / 3.1.0 / 2.0.2 | projections, 2D fallback, procedural textures |
| vazirmatn / @fontsource-variable/inter | 33.0.3 / 5.3.0 | font sources (copied into `public/fonts`, dev-only) |

Node ≥ 20.9 (tested on Node 22.22).

## 2. How to run

```bash
cd ahos-dashboard
npm install
npm run dev            # http://localhost:3000  (add -- -H 0.0.0.0 to expose)
npm run build && npm run start
npm run lint           # ESLint (0 problems)
npm run typecheck      # tsc --noEmit
npm test               # node:test — solar position + market-session unit tests
npm run verify:routes  # smoke-tests all routes against a running server (BASE_URL=…)
npm run assets:sync    # re-copy fonts + geodata from node_modules → public/ (only after upgrades)
```

No environment variables, secrets, keys or network access are required at runtime.

## 3. Folder map

```
ahos-dashboard/
├─ README_MERGE.md · LICENSES.md · package.json · next.config.ts · tsconfig.json · eslint.config.mjs
├─ docs/brief/                   original build brief + reference images (provenance)
├─ public/
│  ├─ fonts/                     Vazirmatn (variable) + Inter (variable, latin) + OFL texts
│  └─ geo/                       Natural Earth TopoJSON (land 50m/110m, countries 110m) + Iran 50m GeoJSON
├─ scripts/
│  ├─ sync-assets.mjs            copies fonts/geodata, extracts Iran outline
│  ├─ verify-routes.mjs          route smoke test
│  └─ licenses.mjs               production dependency license table
├─ tests/                        solar.test.ts · sessions.test.ts (node --test)
└─ src/
   ├─ app/                       one folder per route (server components: fetch via lib/api → render a client view)
   │  ├─ layout.tsx              <html lang dir data-*>, fonts, providers, AppShell
   │  ├─ globals.css             Tailwind import + base + component classes (glass, gold-border, data-table…)
   │  ├─ fonts.ts                next/font/local (no external font requests)
   │  ├─ page.tsx                Command Center
   │  └─ digital-world · earth · markets · opportunities · oil · gold · equities/[region] · crypto · tokens
   │     news · security · workshop · university · research · chat · agents · paper-trading · portfolio
   │     memory · errors · reports · system · governance · settings · not-found · error
   ├─ components/
   │  ├─ layout/                 AppShell, Sidebar, Topbar, AssistantColumn, CommandPalette, PageHeader, logo, providers
   │  ├─ cards/                  DataCard, KpiCard, MarketWatch, MarketChart, summary cards, shared blocks, AlertsList
   │  ├─ charts/                 EChart wrapper + domain charts, SVG Sparkline, RingGauge
   │  ├─ globe/                  three.js scene, shader, procedural textures, HUD, 2D fallback
   │  ├─ agents/                 ActivityFeed, AgentInspector (drawer), AgentGlyph
   │  ├─ chat/                   KianPanel, KianOrb
   │  ├─ ui/                     shadcn-style primitives + status chips
   │  └─ views/                  one client view per page
   ├─ lib/
   │  ├─ api/                    typed data functions (the ONLY data entry point) + types.ts contracts
   │  ├─ i18n/                   fa.ts (primary) · en.ts (type-checked against fa) · useI18n()
   │  ├─ settings/               settings store (localStorage + cookie mirror), quality budgets
   │  ├─ astro/solar.ts          NOAA/Meeus solar position, sunrise/sunset
   │  ├─ time/                   shared 1 Hz clock, market-session estimator
   │  ├─ audio/                  WebAudio tone engine (muted by default)
   │  ├─ format.ts               locale/digit-aware number, %, currency, date, relative time
   │  ├─ tokens.ts               runtime bridge: CSS variables → ECharts / WebGL colours
   │  └─ utils.ts                cn(), helpers
   ├─ mock/                      deterministic mock datasets (seeded PRNG) — never imported by components
   └─ styles/tokens/tokens.css   ★ the single design-token file
```

## 4. Design tokens

**File:** `src/styles/tokens/tokens.css` — every colour, radius, shadow, glow, blur and motion timing.

* `@theme { … }` — Tailwind tokens. The default Tailwind palette is **reset** (`--color-*: initial`) so only AHOS colours exist:
  `ink-*` (navy surfaces), `gold-*` (brand accent), `data-*` (cyan, data lines only), `fg-*` (text), semantic `up/down/warn/info/violet/slate`,
  `status-*` (LIVE/STALE/UNKNOWN/UNAVAILABLE/DEMO), `sev-*`, radii `--radius-*`, shadows/glows `--shadow-*`, blur, easing, animations.
* `:root { … }` — runtime tokens (motion durations, glass surfaces, gradients, hairlines, layout sizes).
* Profiles: `:root[data-quality="balanced|low"]`, `:root[data-theme="contrast"]`, `:root[data-motion="reduced"]` override tokens.
* JS consumers (ECharts, three.js) read the same variables through `src/lib/tokens.ts` (`readChartPalette()`), so the token file stays the single source of truth.

## 5. Architecture

**Data flow.** `app/<route>/page.tsx` (server) → `await get…()` from `src/lib/api/*` → passes a `DataEnvelope<T>` to a client view.
Client-only interactions call the same typed functions (e.g. `getCandles`, `askKian`, `getSearchIndex`).

```ts
interface DataEnvelope<T> { data: T; meta: DataMeta }
interface DataMeta { source: string; sourceLabel: Localized; retrievedAt: string | null; status: DataStatus; isMock: boolean; ttlSec?: number }
type DataStatus = "LIVE" | "STALE" | "UNKNOWN" | "UNAVAILABLE" | "DEMO";
```

**Truthfulness rules (enforced in code).**
* Mock payloads are always `status: "DEMO"`, `isMock: true`; every card shows a DEMO chip.
* `resolveStatus()` downgrades a LIVE payload older than `ttlSec` to **STALE**, and a LIVE payload without a timestamp to **UNKNOWN** — the UI cannot fake live.
* Missing values are `null` and render as “—” with an accessible “Unknown” label (never 0).
* Agents: runtime state, implementation status, maturity and verification are separate fields with separate chips; the hexagon glyph never animates.
* Decisions are rendered as canonical-backend output only (no BUY, no “hot opportunity”, no target-return %), mirroring `types.ts` / `canonical_read_model.ts` in the root repo.
* The only LIVE chips in the build belong to values computed locally from the device clock (sun position, clocks, sessions).

**RTL / i18n.** Root `<html lang="fa" dir="rtl">` (switches to `en/ltr`). Layout uses logical properties (`ms-/me-/ps-/pe-/start-/end-`, `border-s/e`).
Numbers render through `<Num>` (direction-isolated, tabular). Mixed strings (symbols, addresses, sources) use `<bdi>`/`dir="auto"`.
Charts keep chronological time left→right (financial convention) while legends/tooltips follow the UI direction. Persian digits are a setting (default Latin for dense tables).

**Settings.** `SettingsProvider` (`useSyncExternalStore`) — localStorage key `ahos.settings.v1` is the client source of truth; an SSR-relevant subset is mirrored to the `ahos_prefs` cookie so the server renders the correct `lang/dir/data-quality/data-theme/data-motion` (no flash, no hydration drift). First run auto-selects a quality profile from CPU cores / device memory / reduced-motion.

**Quality profiles** (`QUALITY_BUDGETS` in `src/lib/settings/types.ts`):

| | HIGH | BALANCED | LOW |
|---|---|---|---|
| Globe DPR cap × render scale | 2 × 100% | 1.5 × 85% | 1 × 70% |
| Bloom (UnrealBloomPass) | on | off | off |
| Globe textures / geodata | 4K / 50m | 2K / 110m | 1K / 110m |
| Stars / ambient gold dust | 3200 / 70 | 1500 / 30 | 500 / 0 |
| Frosted-glass blur | 16px | 8px | off (opaque) |
| FPS cap | 60 | 60 | 30 |

**3D Earth** (`src/components/globe`): `globe-hero.tsx` (HUD, WebGL detection, `next/dynamic({ssr:false})`) → `globe-canvas.tsx` (React wrapper) → `scene.ts` (framework-free three.js).
* Day/night: custom `ShaderMaterial` (`material.ts`); `sunDir` from `sunPosition(new Date())` (NOAA algorithm, unit-tested), refreshed every 60 s; soft terminator, warm twilight band, ocean glint, Fresnel rim, city lights on the night side.
* Textures are generated **procedurally** on a canvas from local Natural Earth data (`textures.ts`): navy ocean, gold coastlines, graticule, warm city clusters from a static metro list (`city-lights.ts`). No image files, no network.
* Iran: 50m outline as a gold cap + glowing border path + animated comet along the border, Tehran pulse rings, label, click/hover → camera fly-to + info panel, “back to global”.
* Controls: OrbitControls drag/zoom, auto-rotate with pause/resume (auto-pauses during interaction), zoom ±, reset, layer toggles (labels / atmosphere / markers / monitoring links), screen-space label collision culling.
* Robustness: 2D SVG fallback (`globe-fallback.tsx`, d3-geo night hemisphere) when WebGL is missing, the context is lost, or the user selects 2D; rendering pauses off-screen (IntersectionObserver) and when the tab is hidden; reduced motion → no auto-rotate/rings/dash animation, render-on-demand; full disposal of geometries, materials, textures, composer and renderer on unmount.

**Audio** (`src/lib/audio/engine.ts`): generated WebAudio tones only (tick, open/close, send/receive, notify chime, alert, success, whoosh, optional ambient pad). Muted by default; master mute in the top bar; volume / UI sounds / ambient in Settings. AudioContext is created lazily on first user gesture.

## 6. Key components & props

| Component | Path | Props |
|---|---|---|
| `AppShell` | layout/app-shell.tsx | `data: ShellData { badges, notifications, assistant }`, `children` |
| `Sidebar` | layout/sidebar.tsx | `badges: Partial<Record<NavItemKey, number>>` (nav config in `nav-config.ts`) |
| `Topbar` | layout/topbar.tsx | `notifications: AppNotification[]` |
| `AssistantColumn` | layout/assistant-column.tsx | `data: AssistantData { chatSeed, activity, activityMeta, agentIndex, alerts, alertsMeta }` |
| `CommandPalette` | layout/command-palette.tsx | — (opened via `usePalette()` / Ctrl+K) |
| `PageHeader` / `PageBody` | layout/page-header.tsx | `title, subtitle?, icon?, actions?, demo?` / `children, className?` |
| `DataCard` | cards/data-card.tsx | `title, subtitle?, icon?, meta?: DataMeta, actions?, footerExtra?, bare?, highlight?, as?, id?, className?, bodyClassName?` |
| `CardFooter` | cards/data-card.tsx | `meta?, extra?, compact?` — source · retrieved-at · status chip |
| `KpiCard` | cards/kpi-card.tsx | `kpi: Kpi, meta: DataMeta` |
| `MarketWatchCard` | cards/market-watch.tsx | `instruments: Instrument[], meta, title?, limit?` |
| `MarketChartCard` | cards/market-chart-card.tsx | `instruments, candles: Record<id, Candle[]>, meta, ids: string[], height?` |
| `PaperSummaryCard` · `NewsFeedCard` · `UniversityStatusCard` · `SystemHealthCard` | cards/summary-cards.tsx | `{account,intraday,meta}` · `{news,meta,limit?}` · `{uni,meta}` · `{system,meta}` |
| `InstrumentTile` · `StatTile` · `DriversCard` · `SectorHeatmapCard` · `MoversCard` · `ProviderHealthCard` · `Notice` | cards/blocks.tsx | see file (typed) |
| `EChart` / `useChartContext` | charts/echart.tsx | `option, label (ARIA), height?, onEvents?` |
| `CandlesChart` · `LinesChart` · `AreaSeriesChart` · `BarsChart` · `DonutChart` · `NetworkGraph` · `SectorTreemap` | charts/charts.tsx | typed series props + `label` |
| `Sparkline` | charts/sparkline.tsx | `data: number[], color?, area?, baseline?, height?, label?` |
| `RingGauge` | charts/ring-gauge.tsx | `value: number \| null, size?, stroke?, label, caption?, tone?, display?` |
| `GlobeHero` | globe/globe-hero.tsx | `earth: EarthOverview, meta, variant?: "hero" \| "full", initialFocus?: "global" \| "iran"` |
| `GlobeFallback2D` | globe/globe-fallback.tsx | `centers, focusIran, nowMs, onIranClick, showLabels, showMarkers` |
| `createGlobeScene` | globe/scene.ts | `(host, SceneOptions) → GlobeScene { flyTo, zoom, setLayers, setAutoRotate, setReducedMotion, dispose }` |
| `KianPanel` | chat/kian-panel.tsx | `seed: Record<"fa"\|"en", ChatMessage[]>, variant?: "rail" \| "full"` |
| `ActivityFeed` | agents/activity-feed.tsx | `events: AgentEvent[], index: Record<id, {name, runtime, code}>, limit?, dense?` |
| `AgentInspector` | agents/agent-inspector.tsx | `agent: Agent \| null, departments, onClose` |
| `StatusChip` / `MetaStatusChip` | ui/status.tsx | `status: DataStatus` / `meta: DataMeta` (auto-STALE) |
| `RuntimeChip` · `ImplementationChip` · `VerificationChip` · `OutcomeChip` · `IdentityChip` · `GateChip` · `SeverityChip` · `ConfidenceChip` · `ProviderChip` · `NewsStateChip` · `TriChip` · `AlertTierChip` | ui/status.tsx | one enum prop each (+ `size?`) — icon shape + text, never colour-only |
| `Chip` · `Num` · `Delta` · `TimeAgo` · `Meter` · `CopyButton` · `Kbd` | ui/chip.tsx · ui/primitives.tsx | typed |
| `Button` · `Tip` · `Segmented` · `Switch` · `Slider` · `Dialog`/`SheetContent` · `DropdownMenu*` · `Popover*` · `Tabs*` | ui/* | shadcn-style, Radix-based |

## 7. Mock function → real data source

Every function lives in `src/lib/api/*.ts` and returns `Promise<DataEnvelope<T>>`. Replace the body (`fromMock(...)`) with a real fetch; components do not change.

| Function | Mock | Real source to wire later |
|---|---|---|
| `getKpis()` | mock/kpis | Python canonical read model aggregates (`/api/decisions`, pipeline counters) |
| `getNavBadges()` | inline | same aggregates (counts per section) |
| `getMarketBoard()` / `getInstrument(id)` | mock/markets | Binance public (crypto), CoinGecko, exchange/vendor feeds for FX, indices, commodities; Iranian quotes from an approved domestic source |
| `getCandles(id, tf)` | mock/markets | Binance klines / vendor OHLC (client-callable via a Next route) |
| `getEquities(region)` | mock/equities | licensed index & quote vendor (TBD); TSETMC for Tehran |
| `getOil()` | mock/commodities | EIA open data (inventories), exchange settlements (Brent/WTI), OPEC MOMR |
| `getGold()` | mock/commodities | LBMA/COMEX settlement; domestic coin/gold quotes; WGC central-bank & ETF data |
| `getCrypto()` | mock/crypto | CoinGecko `/global`, Binance public futures (funding/OI), DefiLlama stablecoins, Alternative.me F&G |
| `getTokenDossiers()` | mock/tokens | Python canonical read model + DexScreener / GeckoTerminal / GoPlus / RugCheck evidence |
| `getOpportunities()` | mock/tokens | `canonical_read_model.ts` → Python `DecisionAdvisor` output (display only) |
| `getNewsroom()` | mock/news | AHOS `news.ts` pipeline (RSS + MyMemory translation + provenance) |
| `getSecurity()` / `getProviderHealth()` | mock/security | Python security overlay (`architecture/security`), GoPlus/RugCheck, `providers.ts` health probes |
| `getAgents()` / `getAgentActivity()` | mock/agents | agent registry (`AGENT_REGISTRY_MODEL.md`), runtime heartbeats, audit/event log |
| `getUniversity()` | mock/university | evaluation harness results + verification records (INDEPENDENT vs SELF_CHECK) |
| `getResearch()` | mock/research | `research_worker` missions + epistemic core (`tests2b` domain) |
| `getPaperAccount()` / `getPaperIntraday()` / `getPortfolio()` | mock/paper | `paper_trading/` ledger (Lane A, read-only) + valuation |
| `getSystem()` / `getErrors()` | mock/system | `/api/runtime`, process heartbeats, Lane A integrity check, recovery orchestrator log |
| `getNotifications()` / `getAlerts()` | mock/system | alert service (`AlertEvent` in root `types.ts`, tiers INFO/WATCH/HIGH_ATTENTION) |
| `askKian()` / `getChatSeed()` | mock/chat (rule-based) | `POST /api/chat` (`ConversationResponse` in root `types.ts`) |
| `getGovernance()` · `getMemory()` · `getReports()` · `getWorkshop()` | mock/org | governance ledger & approvals · memory store · report jobs · CI/pytest reports |
| `getDigitalWorld()` | mock/org | DefiLlama chains / stablecoins / DEX volumes |
| `getEarth()` | mock/org | static reference data (financial hubs) + index feeds; Iran indicators from approved sources |
| `getSearchIndex()` | composed | `/api/search` |

## 8. Accessibility checklist

Skip link, landmarks (`nav`, `header`, `main`, `aside`), `aria-current` in nav, `aria-expanded` on collapsibles, `aria-pressed` on toggles,
Radix focus management for dialogs/menus/drawers, visible gold focus ring, keyboard palette (Ctrl/⌘+K, ↑↓, Enter, Esc),
ARIA labels on icon buttons, charts (`role="img"` + summary label) and the WebGL canvas, `role="log"`/`aria-live` for chat,
status never colour-only (icon shape + text), unknown values announced as “Unknown”, high-contrast theme, reduced-motion support
(OS preference or explicit setting).

## 9. Merging into the root AHOS app

Root changes made in this branch (both are ignore entries only):
* `tsconfig.json` → `"exclude": [..., "ahos-dashboard"]` (keeps the root type-check scope unchanged)
* `eslint.config.mjs` → `globalIgnores([..., "ahos-dashboard/**"])`

Two options:
1. **Keep as a sibling app (recommended first step).** Run it on its own port; point `src/lib/api/*` to the root app's existing API routes (`/api/decisions`, `/api/runtime`, `/api/chat` …) via `fetch`. Zero coupling.
2. **Fold into the root `app/`.** Move `src/app/*` routes under a route group (e.g. `app/(command)/…`), copy `src/{components,lib,styles}` and `src/mock`, then:
   * the root alias is `@/* → ./*`; this app uses `@/* → ./src/*` — either keep a `src/` folder in the root or rewrite imports (`@/components/…` paths stay the same if you copy into `./components` etc.);
   * import `src/styles/tokens/tokens.css` from the root `globals.css` (it resets Tailwind's palette — check existing root classes first, or remove the `--color-*: initial` line);
   * copy `public/fonts` and `public/geo`; keep `next/font/local` declarations from `src/app/fonts.ts`;
   * `next.config.ts` here pins `turbopack.root`/`outputFileTracingRoot` to this folder — drop those two keys when merged.

## 10. Known limitations (honest)

* **All market, agent, news, security and account data is mock** (deterministic, seeded). Only clocks, market-session estimates and the sun position are computed live from the device clock.
* Market sessions use official regular hours in each exchange's time zone; **holidays, half-days and auctions are not modelled** (labelled “estimated”). The Tehran SE schedule (Sat–Wed 09:00–12:30) is an assumption.
* Night lights are procedural (static metro list + clustering), not satellite imagery; coastline detail is Natural Earth 1:50m (HIGH) / 1:110m.
* Kian is a rule-based mock responder (keyword intents); it never claims live data and answers UNKNOWN otherwise.
* `/equities/[region]`, `/markets?symbol=`, `/tokens?token=`, `/agents?agent=` deep links work; other list pages do not deep-link yet.
* Report PDF download is intentionally disabled in the demo build.
* Visual QA was done with headless Chromium + SwiftShader (software WebGL); real GPUs render faster/smoother. Safari/Firefox were not tested in this environment.
* No automated visual-regression or e2e test suite yet (unit tests cover the solar and session math; `verify:routes` covers all routes).

## 11. Verification (this build)

* `npm run build` ✔ — 27 page routes (+ 404 / error boundary)
* `npm run lint` ✔ — 0 problems (incl. React Compiler rules)
* `npm run typecheck` ✔ — strict
* `npm test` ✔ — 15/15 (solar declination at solstices/equinox, equation of time, subsolar point, Tehran sunrise/sunset, polar night; exchange sessions incl. DST, lunch breaks, weekends, Tehran week)
* `npm run verify:routes` ✔ — 30/30 checks: every route 200 with RTL markup + marker text (incl. deep links), unknown equities region → 404

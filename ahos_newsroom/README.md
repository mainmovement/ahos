# AHOS Newsroom — «دیده‌بان · خبرنگاران»

A **read-only, paper-only** intelligence desk that gathers market news for **oil (نفت)** and
**gold (طلا)** and hands verified evidence to the White Hats / Judge queue.

This folder is a **complete, self-contained** app: `npm install && npm run dev`, no network, no
backend, no secrets. Everything you see is produced by typed fixtures behind a mock adapter.

```
npm install
npm run dev      # http://localhost:3000
```

| Script | What it does |
| --- | --- |
| `npm run dev` | Next 16 dev server (Turbopack) on `0.0.0.0:3000` |
| `npm run build` | Production build (all routes prerendered statically) |
| `npm start` | Serve the production build |
| `npm run typecheck` | `tsc --noEmit`, `strict: true` |
| `npm run lint` | `eslint .` (flat config, `eslint-config-next`) |
| `npm test` | `vitest run` — 83 tests |
| `npm run verify` | typecheck → lint → test → build |

## What this screen is (and is not)

* It **is** an intelligence inbox: stories, sources, verification pipeline, conflicts, reporters.
* It **is not** a trading terminal. There is **no** buy / sell / size / approve / override /
  enable-trading / place-order control anywhere in the tree. A source-level test
  (`tests/forbidden-controls.test.ts`) fails the build if one ever appears.
* Allowed verbs, and only these: **view · filter · open evidence · copy ID · export read-only**.
* Headlines are information, **not** signals. No live price is ever derived from them, and the UI
  never colours a story as good or bad trade advice.

## Layout

```
Topbar          «دیده‌بان · خبرنگاران» · page TruthChip · PAPER_ONLY pill · mute · T0/T1/T2 · Tehran clock
[VIOLATION]     full-width red bar — only when the snapshot is not paper-only
[DEMO banner]   diagonal-striped gold banner — the adapter is a mock
Market pills    نفت ✔ · طلا ✔ · رمزارز «متصل نیست/PLANNED» · سهام «متصل نیست/PLANNED»

┌─────────────────────────────┬────────────────────────────┬──────────────────────────┐
│ RIGHT · story inbox         │ CENTRE · dossier           │ LEFT · conflict board    │
│ 7 highlighted cards         │ + source strip             │ + reporter roster        │
│ (dense table behind         │ + verification pipeline    │ + White Hats handoff     │
│  «جزئیات»)                  │                            │                          │
└─────────────────────────────┴────────────────────────────┴──────────────────────────┘
capsule dock    far-right rail: «جهان AHOS» slot (PLANNED)
TelemetryStrip  source id · last read · story count · demo · conflict · adapter · tier · Reality Map
```

RTL throughout (`<html dir="rtl">`), Vazirmatn + Inter bundled locally as `woff2`.

## URL switches

| Query | Effect |
| --- | --- |
| `?demo=1` | Forces the DEMO banner **and** marks every row DEMO → verified totals drop to 0 |
| `?violation=1` | Forces the VIOLATION bar even on a compliant snapshot |
| `?tier=0\|1\|2` | T0 flat 2-D · T1 solid panels (default) · T2 glass |
| `?state=calm\|empty\|unavailable\|error` | Adapter scenario |
| `?story=nws-oil-0143` | Deep-links a selected story |
| `?details=1` | Opens the dense story table |

Examples: `http://localhost:3000/?violation=1`, `http://localhost:3000/?story=nws-oil-0143`,
`http://localhost:3000/?state=empty`, `http://localhost:3000/?tier=0`.

## Truth rules (non-negotiable, all unit-tested)

1. **Status vocabulary.** Data may only be `LIVE · STALE · UNKNOWN · DEMO · CONFLICT · REJECTED`.
   `UNAVAILABLE / PARTIAL / PLANNED / MISSING / ERROR / LOADING / EMPTY / SIMULATED` are component
   states and can never upgrade data.
2. **UNKNOWN is grey**, never green — asserted on the tone map *and* on the rendered DOM.
3. **VERIFIED needs two independent, live, tiered sources.** One source ⇒ `PARTIAL`. Two sources
   from the same wire ⇒ still `PARTIAL` (they share an `independenceGroup`).
4. **DEMO is excluded from every total** and wears a diagonal-striped ribbon. Adding DEMO rows never
   moves the verified counter.
5. **Missing values show «—» / «ناموجود»**, never a fabricated `0`.
6. **STALE shows its last-update time**; a source with no timestamp is `UNKNOWN`.
7. **Pipeline stages that have not run are `PLANNED` / `UNKNOWN`** — never a fake COMPLETE.
   `JUDGE_HANDOFF` is always `PLANNED`: handoff is a manual, read-only act.
8. **CONFLICT never auto-clears.** Claim A vs claim B are both kept; the judge decides.
9. **Only oil & gold are connected.** Crypto / equities render as grey «متصل نیست · PLANNED»
   outlines with `storyCount: null` — zero invented headlines.
10. **Paper-only guard.** `executionMode !== 'PAPER_ONLY' || realTrading === true` ⇒ full-width red
    VIOLATION bar. The «فقط کاغذی · PAPER_ONLY» pill is permanent and not dismissible.

## Project layout

```
src/
  app/                     Next app router shell (layout · page · globals.css)
  components/truth/        shared chips (TruthChip, MissingValue) — lift as-is
  features/newsroom/
    NewsroomPage.tsx       the screen
    components/            StoryInbox · StoryDossier · SourceStrip · VerificationPipeline ·
                           ConflictBoard · ReporterRoster · JudgeHandoffTile ·
                           PaperOnlyGuard · ViolationBar · Topbar · TelemetryStrip · CapsuleDock
    lib/                   types · truth · pipeline · selectors · format · labels · tier
    __tests__/
  mock/newsroom/           fixtures.ts · adapters.ts (typed NewsroomAdapter)
public/fonts/              Vazirmatn + Inter woff2 (SIL OFL 1.1)
screenshots/               ten 1600×900 PNGs
tests/                     source-level guard rails
```

Dependencies: **next 16.4.2 · react 19.3.1 · typescript 5.9.3 · tailwindcss 4.3.3 · vitest 5.0.5**.
Tailwind is imported **without** its preflight (`tailwindcss/theme.css` + `tailwindcss/utilities.css`)
so nothing global can collide with a host app; every reset rule is scoped under `.ahos-root`.

## Screenshots

| File | URL |
| --- | --- |
| `01-calm-demo-oil-gold.png` | `/` |
| `02-conflict-board.png` | `/?story=nws-oil-0143` |
| `03-violation-bar.png` | `/?violation=1` |
| `04-empty.png` | `/?state=empty` |
| `05-unavailable.png` | `/?state=unavailable` |
| `06-tier0.png` | `/?tier=0` |
| `07-details-table.png` | `/?details=1` |
| `08-error.png` | `/?state=error` |
| `09-forced-demo-all.png` | `/?demo=1` |
| `10-tier2-glass.png` | `/?tier=2` |

Next steps for merging into the main AHOS app: see **`README_MERGE.md`**.
Command transcripts: see **`VERIFY.md`**. Third-party notices: see **`LICENSES.md`**.

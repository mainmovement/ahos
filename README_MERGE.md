# AHOS dashboard (Arena AI build) - Stages 1-3

> **Integration note (2026-10-16):** Stages 1-3 are implemented (shell, overview dashboard, charts/3D Earth/agents/chat UI with typed mock data - every mock card is labelled DEMO). The text below was written for Stage 1 and is kept for reference.
> On this branch the Arena UI lives at the route **`/arena`** (`app/arena/`), the old operator UI at `/operator`; `/` and the API routes are untouched.
> Fonts are bundled locally in `public/fonts` (copied from the `@fontsource/inter` and `@fontsource/vazirmatn` packages). Extra deps: `@types/three`, `@fontsource/*`, `echarts-for-react`.
> The "Run" section below is outdated for ports/hostnames: use `npm run dev -- --port 3100`.

## Scope and status

Stage 1 interface foundation is implemented. This is **not** the complete dashboard or a production-readiness claim. Market data, charts, 3D Earth, agents, chat, and dedicated domain routes are intentionally **NOT_STARTED** pending the next brief. Selecting navigation items currently changes the selected shell section and shows an explicit PLANNED notice; it does not pretend to load an implemented page.

The existing repository, API routes, canonical authority, and frozen Lane A have been preserved. Existing `CommandCenter.tsx` remains available at `/operator`. The new `/` is a local UI with no backend or external runtime requests. Market sessions say UNKNOWN, not LIVE. There are no simulated financial values or fake notifications in this stage.

## Run

```sh
npm install
npm run build
npm run start -- --hostname 0.0.0.0 --port 3000
# Development:
npm run dev -- --hostname 0.0.0.0 --port 3000
```

Preview origins under `*.e2b.app` are allowed in development. All browser URLs are relative. No environment variables, accounts, or secrets are required for the new shell.

## Versions

Next.js 16.2.6; React/React DOM 19.2.6; TypeScript 5.9.3; Tailwind CSS 4.1.17; lucide-react 1.57.0; Inter/Vazirmatn fontsource packages 5.3.0. See the lockfile for exact transitive dependencies. ECharts and Three.js are not installed yet: they belong to subsequent stages.

## Folder map

- `app/layout.tsx`: root metadata, default Persian RTL, new global stylesheet.
- `app/page.tsx`: shell entry point.
- `app/operator/`: preserved prior operator interface, with its legacy stylesheet.
- `src/components/layout/DashboardShell.tsx`: shell composition, selected section, local preferences, optional WebAudio confirmation tone.
- `src/components/layout/Sidebar.tsx`: right-hand navigation, collapsible groups, mobile drawer.
- `src/components/layout/Topbar.tsx`: command trigger, clocks, source status, language/quality/audio controls, notification and profile popovers.
- `src/components/layout/CommandPalette.tsx`: native modal dialog, bilingual filtering, arrows/Enter/Escape, focus containment.
- `src/components/ui/Brand.tsx`: original inline star symbol.
- `src/lib/navigation.ts`: typed bilingual navigation and planned module metadata (not market mock data).
- `src/styles/tokens/theme.css`: shared colors, gradients, typography, radii, shadows, blur, motion and quality tokens; Tailwind mappings.
- `src/styles/shell.css`: locally bundled fonts, global foundation, responsive shell styles.
- `public/fonts/`: self-hosted Inter and Vazirmatn WOFF2 files and upstream licenses.

The existing `app/` router is intentionally retained rather than moved to `src/app/`, avoiding changes to existing API imports. Mock data and typed API adapters will be introduced with actual data modules, not empty placeholders.

## Component interfaces

| Component | Props |
|---|---|
| DashboardShell | None; owns preferences and selection |
| Sidebar | language, active, onNavigate, open, onClose |
| Topbar | language/setLanguage, quality/setQuality, muted/toggleMute, onSearch, onMenu, onSettings |
| CommandPalette | open, onClose, onNavigate, language |
| StarMark | optional className |

## Controls and accessibility

- Ctrl/Cmd+K opens or closes search. Arrow keys move through results, Enter selects, Escape dismisses. Native dialog traps focus.
- Sidebar groups expand/collapse; all sections are reachable by scrolling or search. Mobile overlay closes with Escape or its backdrop.
- FA/EN updates labels and root language/direction. Sidebar stays on the right by design.
- Tehran, UTC and local clocks use browser time and IANA time zones. These are not market-feed timestamps.
- Language, quality and mute persist under `ahos.shell.preferences.v1`. Corrupt/unavailable storage is handled. Sound is muted by default; enabling it plays one generated, short, low-volume tone.
- Low quality removes the decorative grid and rotation, blur and glow. High/Balanced adjust blur; render-scale/particle tokens are reserved for the future globe.
- Reduced-motion disables decorative animation regardless of quality profile.
- Skip link, visible focus, accessible labels, non-color status text, local fonts, and narrow-screen layout are included.

## Verification — 2026-10-16

- `npm install`: passed. An interrupted earlier install left a truncated SWC binary; reinstalling only the generated SWC package repaired it.
- `npm run build`: passed, including strict TypeScript.
- `npm run lint`: passed for the whole repository.
- `python scripts/freeze_lane_a.py`: passed, 36 pinned files intact.
- `npm run test:web-api-auth`: 9 passed.
- `npm run test:canonical-read-model`: 13 passed.
- HTTP checks: `/` and `/operator` returned 200.
- Chromium/Playwright checks at 1440×1000 and 390×844: command search, selection, FA/EN, persisted quality/language, notification dropdown, mobile navigation, and no mobile horizontal overflow passed; no browser page errors. Browser tooling was installed outside the repository solely for verification.

## Known limitations / deployment blockers

- Only Stage 1 is delivered. There are no actual market sessions, data fetches, Earth rendering, domain pages, or account authentication in the new shell. The profile is explicitly a local display profile.
- `npm audit` reports 14 dependency findings (4 moderate, 9 high, 1 critical), including the existing pinned Next.js version. These require a separate dependency/security upgrade and regression pass **before production deployment**. No forced framework downgrades/upgrades were performed in this presentation task.
- Next build emits an existing broad filesystem tracing warning from `canonical_read_model.ts` through `/api/command`; build still passes. This backend tracing behavior is outside Stage 1 scope.
- Sidebar selection is local UI state, not routing. Real navigable section pages are a later-stage task.
- Stage 1 includes a clearly labeled foundation view rather than fabricated dashboard metrics. Replace its main content with the requested command center in the next stage; keep the reusable shell components.

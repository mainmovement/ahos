# AHOS DASHBOARD BUILD BRIEF (paste this whole message into Arena Agent Mode)

You are a senior principal front-end engineer and product designer. You have NO access to my repository, so build a complete, standalone, production-quality dashboard project from scratch inside your sandbox. Another engineer will later merge it into my real codebase, so structure matters as much as looks.

## Product
AHOS is a Persian-language (RTL) AI market-intelligence command center. It is a DESKTOP APP-STYLE dashboard (no website look, no marketing pages). Paper-trading only; never show any button that executes real trades. Use mock data ONLY, clearly isolated in one folder (`/src/mock`) and each card labelled with a small "DEMO" chip, so real APIs can replace it later.

## Stack (fixed, do not change)
Next.js (App Router) + TypeScript + Tailwind CSS + shadcn/ui-style components + lucide-react + Apache ECharts (echarts-for-react) + three.js with three-globe (lazy-loaded, client-only). No paid services, no external fonts or images needed at runtime: bundle fonts locally (Vazirmatn for Persian, Inter for Latin) and generate any textures procedurally or from local files.

## Visual identity (strict)
Near-black navy background, glassy gold as the main accent (gold gradient borders, soft gold glow, frosted glass cards with subtle blur), thin gold hairlines, restrained cyan only for data lines. Premium financial-terminal feel, dense but clean, high contrast, tabular numerals. Define ALL colours, radii, shadows, glow, blur, motion timings as CSS variables / Tailwind tokens in one file. No generic admin-template look. Small glowing gold star logo (SVG) on the sidebar top.

## Layout (match exactly)
1. Right-side sidebar (RTL): logo, collapsible groups, icons, active-item gold glow, badge counts. Items: Command Center, Digital World, Earth, Market Prices, Opportunities, Oil, Gold, US/EU/Asia Equities, Crypto Market, Token Intelligence, Newsroom, Security, Tech Workshop, University, Research, Kian Chat, Agents, Paper Trading, Portfolio, Memory & Learning, Errors, Reports, System, Governance, Settings.
2. Top bar: global search (Ctrl+K command palette), clocks (Tehran, UTC, local), market-session pills, notification bell with dropdown, language switch FA/EN, quality profile (High/Balanced/Low), mute toggle, user menu.
3. Main area: row of 6 KPI cards with sparklines; centre hero = 3D Earth; below it a wide chart + table row.
4. Left column: Kian chat panel (always visible, collapsible), agent activity feed, alerts.
5. Bottom row: 4 full cards (paper-trading summary, news feed, university status, system health).
Every card needs real-looking structure: title, value, delta, sparkline or table, footer with source + "retrieved at" time + status chip (LIVE / STALE / UNKNOWN / DEMO).

## 3D Earth (important)
three-globe in a client-only dynamic import. Day/night terminator computed from real current time with a correct solar-position formula (no random line). City lights on night side, atmosphere rim, slow auto-rotate with pause/resume, drag to rotate, zoom, reset. Iran gets a refined gold outline, soft glow, pulsing marker and label; click flies the camera there and opens an info panel; "back to global" button. Layer toggles (labels, atmosphere, markers). Works fully offline with locally generated/bundled textures. If WebGL is unavailable, show a graceful 2D fallback. Pause rendering when tab/view is hidden; dispose geometries/textures on unmount.

## Pages to build as real, navigable routes (not placeholders)
Command Center (full, as above), Earth & Global, Market Prices (table + ECharts candlestick/line, staleness chips), Oil, Gold, three Equities pages (shared template component), Crypto Market, Token Intelligence (dossier card with contract/chain/identity-confidence fields), Newsroom (pipeline stages + verified/unverified/conflicting states), Security Center, University (agents, exams, pass/fail, retraining queue), Research Institute, Agent Center (agent inspector drawer: role, department, implementation status, current task, last activity), Paper Trading (positions, PnL, risk limits), Portfolio, Errors & Recovery (lifecycle stages), System & Runtime, Settings (language, theme, motion, sound, quality). Build shared components so pages stay consistent.

## Truthfulness rules (apply to the UI design)
Never fake "live". Every value carries a status: LIVE, STALE, UNKNOWN, UNAVAILABLE, DEMO. A decorated avatar never implies a running task: show explicit state chips (registered / running / blocked / failed / planned). Unknown ≠ safe.

## Persian / RTL
`dir="rtl"` at root with `lang="fa"`; test each component for mirroring (icons, charts, tables, drawers). Mixed Persian/English/numbers/addresses must render correctly (use `dir="auto"` / bdi for identifiers). Persian digits optional via a setting. No overlapping labels in narrow sidebar.

## Quality profiles and accessibility
HIGH / BALANCED / LOW profile stored in localStorage, controlling particles, blur, bloom, render scale. Respect prefers-reduced-motion. Keyboard navigation, visible focus, ARIA labels, non-colour-only status. Audio is optional, muted by default, with a master mute and generated WebAudio tones only (no copyrighted assets).

## Engineering requirements
- Strict TypeScript, ESLint clean, `npm run build` must pass. Run `npm install` and `npm run build` in your sandbox and fix every error until it passes. Then run it and verify routes render.
- Clean folders: `src/app`, `src/components/{layout,cards,charts,globe,agents,ui}`, `src/lib`, `src/mock`, `src/styles/tokens`, `public/fonts`.
- Data access only through typed functions in `src/lib/api/*.ts` that currently read from `src/mock`, so a backend can replace them without touching components.
- Include `README_MERGE.md`: stack versions, folder map, how to run, token file location, list of components with props, a table mapping each mock data function to the real data it should later be wired to, and known limitations. Include `LICENSES.md` for every dependency/asset.
- No secrets, no external network calls at runtime, no paid APIs.

## Working method
Do not reply with a plan and stop. Work in your sandbox, creating real files. Order: tokens + layout shell + sidebar/topbar -> Command Center with KPI cards and charts -> Earth module -> remaining pages -> polish, a11y, quality profiles -> build + fix + README. After each stage, run the build. If you run out of room in one reply, say exactly which files remain and continue when I send "continue". At the end, state honestly what is finished, what is placeholder, and what failed. Give me the downloadable workspace.

Begin now with stage 1.

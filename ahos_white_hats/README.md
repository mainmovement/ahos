# AHOS · White Hats & Judge — «کلاه‌سفیدها و ناظر»

Read-only, paper-only audit screen for AHOS: the independent inspection group
that challenges every decision before it can become a paper trade.

Self-contained **Next.js 16 + React 19 + TypeScript (strict) + Tailwind 4** app.
No backend, no network at runtime: all data comes from typed mock adapters and
every mock-backed surface carries a visible **DEMO** chip.

## Run

```bash
npm install
npm run dev      # http://localhost:3000
```

Other scripts:

| command               | what it does                                   |
| --------------------- | ---------------------------------------------- |
| `npm run type-check`  | `tsc --noEmit` (strict)                        |
| `npm run lint`        | eslint 9 (flat config, typescript-eslint)      |
| `npm run test`        | vitest (truth rules, violation logic, controls)|
| `npm run build`       | production build                               |
| `npm run verify`      | type-check → lint → test → build               |

## Demo views (URL params — view/filter only)

| URL                                                        | shows                                  |
| ---------------------------------------------------------- | -------------------------------------- |
| `/?scenario=calm`                                          | calm healthy page (default), DEMO-labelled |
| `/?scenario=calm&open=finding:WH-F-1404-011`               | finding detail drawer                  |
| `/?scenario=violation`                                     | red VIOLATION bar + TRIPPED breaker    |
| `/?scenario=empty`                                         | honest EMPTY states                    |
| `/?scenario=unavailable`                                   | source down → UNAVAILABLE everywhere   |
| `/?scenario=calm&tier=t0`                                  | quality tier T0 — tables only          |

## Structure (lift-friendly)

```
src/
  app/                    layout (RTL, local fonts) + page + globals.css
  components/truth/       shared truth chips: StatusChip, DemoBadge, PaperPill, status tones
  features/white-hats/    the whole screen: components/, hooks/, lib/, types, predicates
  mock/white_hats/        typed fixtures + MockWhiteHatsAdapter (adapter seam)
tests/                    vitest — the non-negotiable truth rules
```

Only the path alias `@/` → `src/` is used. Design tokens are the `--ah-*`
CSS variables at the top of `src/app/globals.css` — lift them with the folder.

## Truth rules (enforced by tests)

- Statuses only: `LIVE, STALE, UNKNOWN, DEMO, CONFLICT, REJECTED`
  (+ component states `LOADING, EMPTY, ERROR, UNAVAILABLE, PARTIAL, SIMULATED`).
- UNKNOWN is grey, never green. Missing values show «—» / «ناموجود», never fake 0.
- Decisions with no judge result are UNKNOWN — never CLEAN.
- DEMO is diagonal-striped and excluded from every total.
- STALE always shows its last-update time; no timestamp ⇒ UNKNOWN.
- No green/red PnL colouring; outcomes are never ranked good/bad.
- Permanent «فقط کاغذی · PAPER_ONLY» pill; VIOLATION bar when
  `executionMode ≠ PAPER_ONLY` or `realTrading = true`.
- Forbidden forever: buy, sell, size, approve, place-order, enable-real-trading.
- Copy on positions: «موقعیت کاغذی؛ پول واقعی در کار نیست».
- `paperAllowed=false` rows show «غیرمجاز».

## Quality tiers

- **T0** `?tier=t0` — 2D tables/SVG only, no shadows/decor.
- **T1** (default) — solid panels, no blur.
- **T2** — optional glass (`ah-panel-glass`) — decorative, never required for data.

## Screenshots

Real 1600×900 browser captures live in `screenshots/` (see `VERIFY.md` for the
exact commands that produced them).

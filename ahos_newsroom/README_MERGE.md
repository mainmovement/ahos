# README_MERGE.md — lifting the Newsroom into another Next app

This folder was built to be **copied, not rewritten**. It touches nothing outside itself:

* one path alias: `@/*` → `src/*`;
* no global CSS reset (Tailwind preflight is deliberately **not** imported; every reset rule lives
  under `.ahos-root`);
* no API route, no server action, no env var, no outbound fetch;
* fonts are local files under `public/fonts/`.

## 1. Copy

```bash
# from the host repo root
cp -r ahos_newsroom/src/features/newsroom   src/features/newsroom
cp -r ahos_newsroom/src/components/truth    src/components/truth
cp -r ahos_newsroom/src/mock/newsroom       src/mock/newsroom     # delete once the API lands
cp -r ahos_newsroom/public/fonts            public/fonts
```

## 2. CSS — three blocks, all optional

`src/app/globals.css` contains, in this order:

1. `@layer theme, base, components, utilities;`
   `@import 'tailwindcss/theme.css' layer(theme);`
   `@import 'tailwindcss/utilities.css' layer(utilities);`
   → the Tailwind v4 import **without** preflight. If the host app already imports
   `"tailwindcss"`, delete this block entirely — nothing else depends on it.
2. The `@font-face` block (Vazirmatn + Inter) and the `@theme` bridge. If the host already ships
   these fonts, keep only the `@theme` colour/token bridge.
3. `:root { --ah-*: … }` plus the `.ahos-*` helper classes, all inside `@layer base` so Tailwind
   utilities always win. This block is safe to append to an existing stylesheet.

> Gotcha: keep the custom CSS **inside** `@layer base`. Unlayered rules outrank every Tailwind
> utility in the cascade and will silently kill `p-3`, `text-ah-*`, `border-*` …

| Token | Value | Token | Value |
| --- | --- | --- | --- |
| `--ah-bg` | `#080b10` | `--ah-gold` | `#d9b977` |
| `--ah-surface` | `#0d121a` | `--ah-cyan` | `#78cbd1` |
| `--ah-surface-2` | `#111926` | `--ah-live` | `#8bbfa6` |
| `--ah-text` | `#ecece7` | `--ah-danger` | `#e39494` |
| `--ah-text-dim` | `#a8b1bf` | `--ah-stale` | `#a08a5c` |
| `--ah-text-faint` | `#6f7885` | `--ah-unknown` | `#6b7480` |
| `--ah-line` | `#1b2432` | `--ah-radius(-sm/-lg)` | `12px (6px / 18px)` |

## 3. Route

```ts
// src/app/(ahos)/newsroom/page.tsx
import { Suspense } from 'react';
import { NewsroomPage } from '@/features/newsroom/NewsroomPage';

export default function Page() {
  return (
    <Suspense fallback={null}>
      <NewsroomPage />
    </Suspense>
  );
}
```

`NewsroomPage` is a client component (it uses `useSearchParams`), hence the Suspense boundary.
The host layout must be RTL: `<html lang="fa" dir="rtl">`, `<body class="m-0 …">`.

## 4. Swap the mock adapter for real endpoints

The UI only ever talks to one interface (`src/mock/newsroom/adapters.ts`):

```ts
export interface NewsroomAdapter {
  readonly id: string;
  readonly kind: 'mock' | 'http';
  load(request?: NewsroomRequest): Promise<NewsroomSnapshot>;
}
```

Rebind it in `src/mock/newsroom/adapters.ts` (or better: move the interface to
`src/features/newsroom/lib/adapter.ts` and inject it):

```ts
export const newsroomAdapter: NewsroomAdapter = httpNewsroomAdapter;
```

### Suggested endpoint → `NewsroomSnapshot` mapping

| Snapshot field | Suggested endpoint | Notes |
| --- | --- | --- |
| `executionMode`, `realTrading` | `GET /api/v1/system/mode` | **Server truth.** Never inferred by the client. `executionMode` must be the literal `PAPER_ONLY` and `realTrading` must be `false`; anything else renders the VIOLATION bar. |
| `generatedAt` | response header / envelope | Reference clock for every freshness calculation on the page. `null` ⇒ everything UNKNOWN. |
| `stories[]` | `GET /api/v1/newsroom/stories?market=OIL,GOLD` | Server must refuse any other market while disconnected. `publishedAt: null` ⇒ freshness UNKNOWN (never `Date.now()` on the client). |
| `sources[]` | `GET /api/v1/newsroom/sources?ids=…` | `lastReadAt: null` ⇒ UNKNOWN; `independenceGroup` is set **server-side** (same wire / syndicated copy share a group). |
| `conflicts[]` | `GET /api/v1/newsroom/conflicts?status=OPEN` | Never auto-resolve; the API must not return a "winner". |
| `reporters[]` | `GET /api/v1/newsroom/reporters` | `attempts/pass/fail: null` when not measured — the UI prints «—». |
| `pipeline[]` | derived (`derivePipeline`) or `GET /api/v1/newsroom/stories/:id/pipeline` | If the server returns stages, map unknown/missing → `PLANNED`/`UNKNOWN`; **never** `DONE`. |
| `freshness.*` | envelope timestamps | `null` ⇒ TelemetryStrip shows «ناموجود». |
| `telemetry.*` | `GET /api/v1/newsroom/telemetry` | `adapter` id is printed in the bottom strip so an operator always knows which layer they are looking at. |
| `markets[]` | `GET /api/v1/newsroom/markets` | `connected: false` ⇒ `storyCount` must be `null`. |

### Invariants the adapter must preserve

1. `computeTotals()` is the only place that produces counters. Do not add a server-supplied
   "verified count" — recompute from evidence.
2. A story is `VERIFIED` only when `deriveStoryVerification()` says so (≥ 2 independent, live,
   tiered sources, no open conflict, not DEMO).
3. `?demo=1` exists so an operator can prove the DEMO exclusion rule on live data: it forces the
   banner and marks every row DEMO, which must drop the verified counter to 0.
4. `?violation=1` exists so the VIOLATION bar can be rehearsed without a dangerous config.
5. Any future adapter must keep `kind` truthful: `kind: 'mock'` drives the page-level DEMO chip and
   the `SIMULATED` chip in the handoff tile. Flipping `kind` to `'http'` removes them.

## 5. Tests to keep green

`npm test` covers the truth rules; `tests/forbidden-controls.test.ts` walks the source tree and
fails on trading verbs, broker clients, `'use server'`, API routes and outbound `fetch`.
Add new Newsroom files under `src/features/newsroom/**` and they are covered automatically.

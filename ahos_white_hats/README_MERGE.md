# README_MERGE — mapping the mocks to real endpoints

How to lift `ahos_white_hats/` into the main AHOS Next app and replace the
mock adapters with real sources — without touching a single component.

## 1. Lifting the folder

Copy into the host app:

- `src/features/white-hats/**` — the screen (only depends on `@/components/truth` and `@/mock/white_hats`)
- `src/components/truth/**` — shared truth chips (StatusChip, DemoBadge, PaperPill, tones)
- `src/mock/white_hats/**` — keep during migration; delete after cutover
- `src/app/globals.css` → merge the `:root { --ah-* }` block and the
  `@layer components` classes into the host's global CSS
- fonts: `npm i @fontsource/inter @fontsource/vazirmatn` and keep the
  `@fontsource/*` imports in the host layout (fully offline after install)
- `postcss.config.mjs` → use `@tailwindcss/postcss` (Tailwind 4)

The feature imports nothing outside `@/features/white-hats`,
`@/components/truth`, `@/mock/white_hats` — no other globals.

## 2. The adapter seam

`src/mock/white_hats/adapter.ts` defines the only contract components know:

```ts
export interface WhiteHatsAdapter {
  readonly sourceId: string;
  fetchSnapshot(signal?: AbortSignal): Promise<WhiteHatsSnapshot>;
}
```

Implementation for production:

```ts
export class HttpWhiteHatsAdapter implements WhiteHatsAdapter {
  readonly sourceId = "https://ahos.internal/api/white-hats/snapshot@v1";
  async fetchSnapshot(signal?: AbortSignal): Promise<WhiteHatsSnapshot> {
    const res = await fetch("/api/white-hats/snapshot", {
      signal,
      headers: { accept: "application/json" },
      cache: "no-store",
    });
    if (res.status === 503 || res.status === 404) throw new WhiteHatsUnavailableError("منبع در دسترس نیست");
    if (!res.ok) throw new Error(`white-hats snapshot ${res.status}`);
    return WhiteHatsSnapshotSchema.parse(await res.json()); // zod recommended
  }
}
```

Then change only the default factory in
`src/features/white-hats/hooks/useWhiteHatsSnapshot.ts`.

## 3. Endpoint mapping (target)

| Snapshot field                       | Future endpoint (GET-only, read-only)                     | notes |
| ------------------------------------ | --------------------------------------------------------- | ----- |
| whole `WhiteHatsSnapshot`            | `/api/ahos/white-hats/snapshot`                            | single poll, ETag/`If-None-Match`; 30 s refresh is enough |
| `decisions[]`                        | `/api/ahos/white-hats/decisions?since=<iso>`               | incremental delta allowed |
| `timelines[decisionId]`              | `/api/ahos/white-hats/decisions/:id/timeline`              | lazy-load on selection, then hydrate |
| `findings[]`                         | `/api/ahos/white-hats/findings?status=&severity=&inspector=` | server-side filtering mirrors the UI filters |
| `inspectors[]`                       | `/api/ahos/white-hats/inspectors`                          | |
| `breaker`                            | `/api/ahos/white-hats/breaker`                             | must include `updatedAt`; missing ⇒ UNKNOWN |
| `canary`                             | `/api/ahos/white-hats/canary/latest`                       | latest deliberate-cheat run; `null` ⇒ UNKNOWN tile |
| `evidence[id]`                       | `/api/ahos/white-hats/evidence/:id`                        | lazy-load inside drawer |
| `executionMode`, `realTrading`       | `/api/ahos/system/execution-mode` (mirrored into snapshot) | the VIOLATION bar reads only these two fields |

All endpoints must be **GET-only**. The page has no mutating verb by design;
do not add POST/PUT/PATCH routes for this surface.

## 4. Field semantics the backend must honor

- Timestamps: ISO-8601 UTC. A missing timestamp must be `null` — never an
  epoch 0, never a fabricated value. The UI renders `null` as «—» + UNKNOWN.
- `freshness`: `LIVE | STALE | UNKNOWN | DEMO | CONFLICT | REJECTED` only.
  No reading time ⇒ `UNKNOWN`.
- Verdict `UNKNOWN` (no judge result yet) must be sent as `"UNKNOWN"` — the
  server must never coerce it to `CLEAN`.
- `demo: true` rows are excluded from all totals server-side as well; the UI
  recomputes totals defensively.
- Units: percentages as plain numbers (`2.4` = ۲٫۴٪). Money never appears on
  this screen.
- `executionMode` is `PAPER_ONLY | LIVE | SIMULATION`; the only acceptable
  production value is `PAPER_ONLY`. If it ever reads otherwise, the red
  VIOLATION bar renders automatically.

## 5. Non-negotiables after merge

- Keep `tests/` green in CI — they pin the truth rules (UNKNOWN never green,
  DEMO excluded from totals, VIOLATION logic, no forbidden controls).
- Never add an approve/override/size/buy/sell control to this screen.
- Keep the permanent PAPER_ONLY pill; it is not dismissible.

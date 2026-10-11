# M-D5.5 — the Hardware Tier Panel

- Date (Tehran): 2026-10-11 · Mission: M-D5.5
- Acceptance from `TEAM_QUEUE_2026-10-11.md:15`: *"Hardware Tier Panel
  (`components/shell/TierPanel.tsx`): hardware tier T8/T16/T32/GPU as main label,
  render tier beside it (T8->T0/T1, T16->T2, T32/GPU->T3), measured reason,
  override, RAM-guard state, list of ideas 'منتظر ارتقا' from
  `config/idea_shelf.json`. Missing file -> grey UNKNOWN. No hard-coded idea
  names."*

## What shipped

| Piece | File |
|---|---|
| The panel | `components/shelf/TierPanel.tsx` |
| The pure registry parse + upgrade rule | `components/shelf/ideaShelf.ts` |
| The one server-side reader of the registry | `app/api/idea_shelf/route.ts` |
| The selftest of the rule | `scripts/idea_shelf_selftest.ts` (22/22) |
| The capture harness | `scripts/screenshot_tierpanel.mjs` |
| Wiring + toggle in the topbar | `components/shell/DashiShell.tsx` |
| Styles | `app/globals.css` |

The panel opens from the topbar's «سخت‌افزار» button and renders, from the
measured verdict:

1. **hardware tier** as the main label — the tier id `T8` plus its band,
   «کمتر از ۱۲ هسته», and its reach `T0 / T1`;
2. **the render tier** beside it — «کم‌مصرف (Low-power)»;
3. **the measured reason** — «گرافیک یکپارچه یا هسته کم — سطح کم‌مصرف»;
4. **the RAM-guard state** — «دقیقاً روی کفِ ۸ گیگابایت», this machine's own case;
5. **the override** — «اندازه‌گیری — انتخاب دستی ثبت نشده», with a clear button
   that re-probes so the panel and the chip can never disagree;
6. **the ideas awaiting upgrade** — «منتظر ارتقا».

## The registry is not there yet, and that is the point

`config/idea_shelf.json` is Aji's M59.S deliverable and **does not exist** —
confirmed again at capture time. Every requirement the queue puts on that case is
handled by construction rather than by a fallback list:

- The registry lives under `config/`, not `public/`, so the browser cannot fetch
  it — and it is deliberately **not** copied into `public/`, because then the
  dashboard would serve a second copy that could drift from the one M59.S reads
  as its single source. `screenshot_tierpanel.mjs` records `/idea_shelf.json` →
  **404** alongside its `/api/idea_shelf` result, which is that decision showing
  up in the browser.
- `parseShelf(null)` → `{ status: "UNAVAILABLE", reason: "missing" }`. An
  unparseable or misshapen file is also UNAVAILABLE, never an empty list — a
  corrupted registry must not present itself as "everything fits".
- The panel renders a grey `TruthBadge` UNKNOWN for the shelf in either case.
  **There is no fallback list of idea names anywhere in the panel.** Inventing one
  would fabricate a roadmap the registry never issued, which is the failure mode
  `UNKNOWN > fabricated` exists to prevent.
- `awaitingUpgrade` returns `[]` for an unknown machine tier and excludes ideas
  with an unrecognised tier tag — because listing such an idea as *awaiting* would
  claim a requirement the registry never recorded, and listing it as *runnable*
  would claim the opposite.

## What the capture actually shows, and the branch it took

The headless browser holds no dashboard session, so `/api/idea_shelf` returned
**401 WEB_API_UNAUTHORIZED** — the same gate `/api/command` sits behind, and the
same reason the topbar pill reads UNKNOWN in these captures. The panel therefore
rendered its *error* branch («خواندن قفسهٔ ایده‌ها ناموفق بود»), not its
missing-file branch («config/idea_shelf.json هنوز ساخته نشده — M59.S»).

Both branches render the same grey UNKNOWN badge, so the captured presentation is
the required one; the distinction is in the Persian line, and the script records
the raw 401 body so the capture is not mistaken for the missing-file branch. In
the owner's window the launcher establishes a session, so the route is reachable
and the missing-file branch is the one that renders — its shape is asserted
directly by the selftest (`parseShelf(null)` → UNAVAILABLE "missing"), and the
route maps that to a 200 with `{ status: "UNAVAILABLE" }`, matching
`/api/command`'s contract that a missing registry is a fact about the system
rather than a server error.

The two are kept distinct rather than merged into a single "could not read" line,
because one means "M59.S has not shipped" and the other means something is wrong.

## Not verified, and why

- **`npx next build` did not complete in this session.** Turbopack failed reading
  `data/e01_discovery.sqlite-shm`, which a running process has locked (os error
  33). That process is the 3199 dev server, which is not this session's to stop
  (AGENTS.md: isolate runtime processes), so the build was not retried by killing
  it. `npx tsc --noEmit` is 0 errors and covers the new route and panel; the same
  pipeline built clean in the M-D5.2 session, and the live dev capture exercises
  the new route and panel directly.
- The **override-clear button's** re-probe path is exercised logically by the
  chip's identical mechanism (verified in M-D5.4) but not re-captured here; it
  shares `probeQuality` and the store with that path.

## Captures

| File | What it proves |
|---|---|
| `tier-panel.png` (151 KB) | The panel open beside the stage: `T8` main label, band, reach, measured render tier, reason, RAM at the floor, no override, and one grey UNKNOWN badge where the idea list will live |

## Evidence

- `npm run test:idea-shelf` — **22/22** (4 suites: missing-registry, ladder
  order, the upgrade rule, the RAM-guard line).
- `npm run test:stage-quality` — 48/48.
- `npm run test:truth-badge` — 44/44.
- `npx tsc --noEmit` — 0 errors.
- `npx eslint` on all touched files — clean.
- `node scripts/screenshot_tierpanel.mjs` — panel DOM captured with all five rows
  populated from the measured verdict; `/api/idea_shelf` → 401 (auth, as
  designed); `/idea_shelf.json` → 404 (not in `public/`, as designed); no console
  errors.
- `config/idea_shelf.json` — confirmed absent; the route provably takes its
  ENOENT branch today.

## Not done, and why

- **M-D5.6 perf overlay** is next, within the M-D12 budgets.
- **M-D6 globe** — after M-D5.6.
- **Full suite** — not run. Per the owner's rule it runs at the end of a mission,
  and M-D5 is not finished. Nothing committed here touches Python.

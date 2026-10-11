# M-D5.4 — context-loss fallback, and no data loss on a live tier switch

- Date (Tehran): 2026-10-11 · Mission: M-D5.4
- Acceptance from `TEAM_QUEUE_2026-10-11.md:14`: *"context-loss fallback to M-D4
  2D layout with Persian notice; no data loss on live tier switch."*
- The fallback machinery (`StageLifecycle`, `FallbackNotice`, `retryStage`) was
  written in M-D5.2 but had **never been exercised** — no test had ever forced a
  context loss, so the listener was unverified code that happened to be wired up.
  This step provokes a real loss and proves both criteria.

## How the loss is provoked

`WEBGL_lose_context.loseContext()` on the stage's own context. That extension
exists for this purpose: it makes the driver raise a **real** `webglcontextlost`,
the exact event `StageLifecycle`'s listener has to survive. Dispatching
`new Event("webglcontextlost")` instead would only prove the `addEventListener`
call — the recovery would be untested.

`scripts/screenshot_contextloss.mjs` drives this over CDP and records the DOM
state at each phase. It reads DOM only; it never touches `.env`, tokens, or any
authority surface.

## What the run shows

| Phase | Result |
|---|---|
| Before | `<canvas>` present, chip `dashi-tier--t1`, no fallback notice |
| `loseContext()` | canvas → **0**, notice appears with `role="alert"` |
| Notice text | «صحنهٔ سه‌بعدی از دسترس خارج شد» / «گرافیک پاسخ نداد؛ نمایش دو‌بعدی جایگزین شد. داده‌ها از بین نرفته‌اند.» |
| Click «اندازه‌گیریِ دوباره» | canvas → **1**, chip back to `dashi-tier--t1`, notice gone |
| Switch down (chip click) | `dashi-tier--t1` → `dashi-tier--t0`; stage unmounts; the 2D notice shows «این ماشین WebGL ندارد یا طبقهٔ نمایش آن T0 است (T0)» |
| Switch up (click at the floor) | `dashi-tier--t0` → `dashi-tier--t1`; `overrideAfter: null`; stage returns (`canvas: 1`) |
| Shell data across the switch | pill identical, scope caption's base sentence identical |
| Console errors | **none** in any phase |

The retry is a *re-probe*, not a blind re-mount (`DashiShell.tsx:108-113`): a
context lost once may be gone for the session, so the machine is measured again
and the stage returns only if the measurement still allows it.

## Two traps the first version of the test fell into

Both would have produced a green run for behaviour that had not happened. They
are recorded because they say something about the shell, not just the script.

**1. The chip never goes `pending` during a re-probe.** The first poll waited
for the chip to leave `pending` after a click — but the old verdict stays
displayed until the new probe lands, so the loop read the *pre-click* class and
reported success for a switch that had not taken effect. Fixed by waiting for
the tier class to actually move off the class it had before the click.

**2. A second consecutive switch needs its own reference class.** Comparing
against the class from the *start of the run* made the up-switch return
instantly (t0 already differs from the initial t1), sampling a verdict whose
probe was still in flight — the title read «انتخاب دستی شما» ("your manual
choice") while `localStorage` already showed the override cleared. That
combination looked like `writeOverride(null)` failing to clear the key. It did
not: the probe simply had not landed. `overrideAfter: null` plus the measured
reason in the title is what distinguishes a cleared override from a stuck one.

Also corrected: the scope caption's low-power line («حالت کم‌مصرف: حرکت و ذرات
خاموش است» — "low-power mode: motion and particles are off") is tier *description*, not data — it appears exactly when the motion
budget is zero, so it *should* change on a switch to T0. Judging data survival on
the raw caption would have read an honest description change as data loss; the
comparison now strips that suffix.

## Captures

| File | What it proves |
|---|---|
| `context-lost.png` (32 KB) | The 2D fallback notice, captured while showing — DOM-only, hence the placeholder-class byte size |
| `context-lost-recovered.png` (140 KB) | The stage that came back after the retry |
| `context-lost.json` | The full phase trace: before / after loss / after retry / both switch directions |

## Evidence

- `node scripts/screenshot_contextloss.mjs` — exit 0, run twice, identical
  verdicts both times.
- `npm run test:stage-quality` — 48/48.
- `npm run test:truth-badge` — 44/44.
- `npx tsc --noEmit` — 0 errors.
- `npx eslint` on touched files — clean (this step adds one script, no component
  change: the fallback already existed).

## Not done, and why

- **M-D5.5 TierPanel** is next. It reads `config/idea_shelf.json`, Aji's M59.S
  deliverable, which does not exist yet; it is specified to render grey UNKNOWN
  for the missing file rather than hard-code idea names.
- **M-D5.6 perf overlay** — after M-D5.5.
- **Full suite** — not run. Per the owner's rule it runs at the end of a mission,
  and M-D5 is not finished. Nothing committed here touches Python.

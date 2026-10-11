# M-D5.2/M-D5.3 — the Dashi stage renders

- Date (Tehran): 2026-10-11 · Mission: M-D5.2 (stage + shell), M-D5.3 (quality probe)
- The owner's M-D5.0 install landed at 10:04; this is the step that unblocked.
- Screenshots below. tsc 0 errors, `test:stage-quality` 44/44, `test:truth-badge`
  44/44, eslint clean.

## What this step shipped

The new main screen (`app/page.tsx` → `DashiShell`) renders for the first time:
the 56px RTL top bar, the PAPER ONLY pill bound to `/api/command`, the measured
tier chip, and the gold-lit observatory floor with its procedural shamseh
engraving and procedural PMREM environment. The old Command Center is untouched
and reachable at `/command_center`.

| Capture | What it proves |
|---|---|
| `01-placeholder-at-load.png` | The honest pre-probe state. The stage is `ssr:false`, so the shell shows the Persian loading line and the chip says "measuring", never a tier. |
| `02-t0-fallback-pre-fix.png` | **The bug.** The probe had run alongside the bundle parse, measured bundle-load contention as a frame rate, and demoted the machine to T0 it does not have — so the stage never mounted and the fallback notice rendered. |
| `03-stage-live-t1.png` | **The same machine after the fix.** Real `<canvas>` mounted, verdict T1 "کم‌مصرف" on 8 cores, no fallback. |
| `04-command-center-route-intact.png` | The old surface still serves at its stable URL after the main route flipped. |
| `05-prod-build-t1.png` | The committed code, built and served by `next build` + `next start` — not just `next dev`. Same honest T1 verdict, stage mounted (see `05-prod-build-t1.json`). |
| `06-core-count-honest.png` | The chip states the *measured* count, «۴ هستهٔ منطقی», not the band it was clamped into. The title names the band as a band: «دستهٔ کمتر از ۱۲ هسته». |

## Three defects the screenshots exposed

All three were fabrications of a hardware fact, and all three were invisible from
inside the code — `resolveTier` is pure and correct; the wrong verdicts came
entirely from *when* and *what* was measured, and from presenting a
classification as a measurement.

**1. The probe raced the bundle it was measuring.** `StageLazy` mounted on the
store's T1 *default*, so three.js/R3F parsed on the main thread while
`frameProbe` counted `requestAnimationFrame` ticks. A fill-rate test that
measures bundle-load contention reports < 24 fps; `resolveTier` then honestly
demoted to T0 from a dishonest number; the stage never mounted, so the defect
was self-confirming. `DashiShell` now waits for `verdict !== null` before loading
the stage, with a third render state for the measuring period — the T0 fallback
would have been a false claim, since nothing had failed while the probe was in
flight.

**2. An Intel HD integrated part was labelled "گرافیک مجزا" (discrete GPU).**
`probeQuality` had read detect-gpu's `tier >= 2` as a dedicated-class flag, but
that ladder is **framerate** (1 ≥ 15, 2 ≥ 30, 3 ≥ 60 fps), not card class — an
integrated part clearing 30 fps introduced itself as discrete, and the chip
stated it as a hardware fact. New `dedicatedClass(renderer)` reads the renderer
string and only *excludes* known-integrated families, returning `null` for
anything unreadable or unrecognised, so the absence of a match is never read as
evidence of integration. Five new selftest cases cover it, including this
laptop's literal renderer string and an Intel-Arc-substring ordering trap.

**3. The chip claimed «۸ هسته» (8 cores) on a 4-core machine.** The chip rendered
`HARDWARE_LABELS[verdict.hardware]`, but `hardwareTierSync` clamps *every* count
below 12 into the T8 band — a band name stated as a point measurement. The
T8/T16/T32 ladder is M-D5.3's own addition; CLAUDE_DASHBOARD_2050 rule 3 defines
only a two-valued hardware axis (discrete vs integrated). The verdict now carries
the measured count as `verdict.cores`, the chip states that (with "logical",
because `hardwareConcurrency` counts hyperthreads), and the band labels name
their edges, appearing only in the title as a band.

## Not done, and why

- **M-D5.5 TierPanel** and **M-D5.6 perf overlay** are next. The panel reads
  `config/idea_shelf.json`, which is Aji's M59.S deliverable and does not exist
  yet; it is specified to render grey UNKNOWN for the missing file rather than
  hard-code idea names.
- **M-D6 globe** — after M-D5.5.
- **Full suite** — not run. Per the owner's rule the full suite runs at the end
  of a mission, and M-D5 is not finished. Nothing committed here touches Python.
- **The M10 .env flip** — still owner-gated, untouched.

## Evidence

- `npm run test:stage-quality` — 48/48 (was 39/39; +5 for the `dedicatedClass`
  suite, +4 for the band-vs-measurement suite).
- `npm run test:truth-badge` — 44/44.
- `npx tsc --noEmit` — 0 errors (was 46 before the M-D5.0 install, 1 after it).
- `npx eslint` on every touched file — clean.
- `npx next build` — exit 0; `/` and `/command_center` both route.
- `next start` on 127.0.0.1:3000 — both routes HTTP 200, no console errors, and
  the probe's own replicated fill-rate test held 59 fps while the scene ran.
- Live probe of this machine: WebGL2 present, 60 fps sustained with a competing
  scene, 4 logical cores, 8 GB — the ladder's honest answer is T1.

# Night run report — 2026-10-11

Branch `ahos`, local commits only, nothing pushed. Started from
`NIGHT_RUN_CHECKPOINT.md` step 8b (M-D3 done).

## Shipped (committed)

| Commit | What |
|---|---|
| `e73ff7b` | **M-D4** — the shared snapshot vocabulary extracted from `CommandCenter.tsx` into `dashboard_snapshot.ts`. −207/+15 in CommandCenter, `tsc` clean. The owner's "commit M-D4 as-is" instruction, executed. |
| `37977a2` | **An M-D1 regression fixed.** The full suite after M-D3 returned `2 failed, 3350 passed, 4 skipped`. One failure is the known pre-existing `test_execution_state` isolation defect; the other was `launcher/appwindow.py:291`, whose POSIX branch had no console-suppressing flag. `windowsHide=True`. |
| `73a03e4` | **M-D5.1 prototype review + M-D5.0 package manifest**, plus `/command_center` so the existing real-data surface has a stable URL while the new shell becomes the main screen. |

## Written, tested, held in the working tree

The owner's pivot: build the new Dashi main screen from scratch; the old UI is
rejected. Following `TEAM_QUEUE_2026-10-11.md` M-D5.1..M-D5.6.

- **M-D5.3 quality probe** — `components/stage/quality.ts`.
  `npm run test:stage-quality` **39/39**. `resolveTier` is a pure function of a
  plain record, so the whole T0..T3 ladder is provable on a machine with no GPU.
  Judgement calls are in `DECISIONS_LOG.md`; the load-bearing ones are that an
  unavailable measurement is never read as a low one (null fps / null RAM do not
  demote), and that `prefers-reduced-motion` is deliberately not an input because
  §11 makes it combinable with any tier.
- **M-D5.2 stage + shell** — the empty gold-lit observatory floor with a
  procedurally generated 10-fold shamseh engraving, a procedural PMREM
  environment (the direct replacement for the prototype's banned
  `<Environment preset>` fetch), a 56px RTL top bar with the PAPER ONLY pill
  bound to real `executionMode`, the measured tier chip, and the M-D5.4
  context-loss fallback to a Persian notice.

## BLOCKED_TOOL_PERMISSION — the M-D5.0 install

This is the one thing I could not do, and it gates everything above from
rendering.

`npm install` for the owner-pre-approved set was **denied by the Claude Code
auto-mode safety classifier** ("Stage 2 classifier error — blocking based on
stage 1 assessment"), after several classifier timeouts on the same command. Per
OWNER_DECISIONS Q3 ("If the tool's permission system blocks it, record
`BLOCKED_TOOL_PERMISSION` … do not route around it") I stopped and did not retry
it through another tool, shell or interpreter.

The exact command, the pinned versions and the licence table are in
`docs/dashboard/PACKAGES.md`. Consequences, stated plainly:

- `npx tsc --noEmit` reports **46 errors**, every one of them missing-module
  resolution for `three`, `@react-three/fiber`, `zustand` and `detect-gpu`, plus
  the JSX intrinsic elements R3F's types provide. None is a logic error in the
  new code; `quality.ts` has exactly one, the `detect-gpu` import.
- **The stage has never rendered. No M-D5.2 screenshot exists.**
- I committed only what compiles and held the stage, shell, store, probe and the
  modified `app/page.tsx` / `package.json` / `globals.css` in the working tree,
  so the committed main route still renders the old Command Center. No
  half-built main screen ships while the gate is closed.

Working regression signals while blocked: `npm run test:stage-quality` 39/39,
`npm run test:truth-badge` 44/44.

## What the owner can do

Either re-run the install command from `docs/dashboard/PACKAGES.md` (it is
pre-approved and pinned), or add a Bash permission rule for `npm install`. Once
it lands, the remaining work is mechanical and already written: one commit lands
M-D5.2/M-D5.3 and flips `app/page.tsx` to the Dashi shell, then `next dev` on a
loopback port SSR-verifies the shell and the
`reports/dashboard/screens/M-D5.2/` screenshot is taken, then M-D5.5's TierPanel
and M-D6's globe.

## Not done, and why

- **M-D5.2/M-D5.4/M-D5.5/M-D5.6** — written or designed, all gated on the
  install. M-D5.5's TierPanel reads `config/idea_shelf.json`, which does not
  exist yet (it is Aji's M59.S deliverable); the panel is specified to render a
  grey UNKNOWN for the missing file rather than to hard-code idea names.
- **Screenshots** — no capability exists in the repo and the stage cannot render.
- **Full suite** — last run is the 62-minute one above (2 failed → now 1 known).
  Not re-run: nothing committed since touches Python, and the owner's rule is a
  full suite at the end of each mission, which M-D5 is not.
- **The M10 .env flip** — still owner-gated, untouched, as instructed.

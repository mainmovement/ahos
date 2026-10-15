# OWNER APPROVAL RECORD — M11.1 and M11.2

**Date:** 2026-10-06
**Event:** Owner (human) granted explicit approval for the owner-gated items M11.1 and M11.2.
**Effect:** `NEEDS_REVIEW` -> `DONE` on both rows (STATUS column only).
**Prior state:** both rows held the queue at `OWNER_GATE_HOLD` for ~5h (autopilot log lines
2026-10-05T19:34:14 .. 2026-10-06T01:04:15), correctly refusing to advance M11.3.

## What this approval IS

Owner acceptance of the *technical deliverables* of both missions, at the evidence level the
OWNER_DECISION_BRIEF described. Concretely:

- **M11.1** — single `AHOS` shortcut, zero visible consoles, in-dashboard Status/Stop/Restart,
  gateway port from non-secret candidate config. Proven by
  `reports/launcher/smoke_dashboard-api_20261005T021119Z.json` (`verdict.passed: true`,
  `components_owning_windows: []`, every control predicate true) and measured test counts in
  `docs/ONE_CLICK.md`.
- **M11.2** — the UTF-8 BOM fix in `launcher/ahos.ps1`. Proven by the BOM present at HEAD
  (`ef bb bf`), the mojibake reproduced and fixed on the real PS 5.1 binary, and the owner-run
  receipt `reports/launcher/m11_2_owner_run_20261005T043519Z.json` (exit 0, one start action,
  +903 valid UTF-8 bytes, `starts_with_utf8_bom: true`).

## What this approval is NOT (anti-fabrication pins)

This is **owner approval**, given in the owner's own message. It is *not* approval inferred from
an agent sign-off, a passing test, an `AUTOPILOT_RESULT: DONE` marker, or a git commit — the
source is the owner's explicit instruction.

It does **not**:
- raise either delivery above `TESTED` on the reality ladder (`VERIFIED` would still require an
  owner-read receipt, which this is not);
- authorise live trading, real funds, broker keys, or any departure from `PAPER_ONLY`;
- change Lane A (`discovery/**`, `paper_trading/**`), which stays frozen;
- approve the M11.2 spec's *literal* mechanism text (`[IO.File]::AppendAllText` /
  `Out-File -Encoding utf8`) — the implementation deliberately uses the R6
  `AHOS_LAUNCHER_LOG` + Python-side `_Tee` design instead, and that deviation was reported as
  CONFLICT DETECTED in the brief. The owner approved the working mechanism, not the superseded
  spec wording;
- resolve the two open `UNKNOWN`s (M11.1 idle-shell residue; M11.2 PowerShell 7 unverified).

## Runtime consequence

With both rows `DONE`, `Select-NextMission` finds M11.3 as the first launchable row with no
`NEEDS_REVIEW` row above it, so the hold releases and the runner launches M11.3 on its next loop
iteration. This was proven in an isolated sandbox against the real production selection function
before any queue edit was made; the production queue was byte-verified unchanged afterwards.

## Files changed by this approval

- `reports/grok/CLAUDE_AUTOPILOT_QUEUE.md` — STATUS column only, rows 8 and 9.
- This record.

No code, tests, or gates were modified to produce this approval.

# Open items after the intelligence loop (2026-10-30)

There is no file named `FULL_GAP_REGISTER`. The production register is `AHOS_GAP_REGISTER.md`. Statuses below are copied from that register and from `SPEC_TRACE.md`. This mission did not close any of them. Edge remains `UNPROVEN_EDGE`. Product classification stays `INTEGRATION_READY`.

## Gap register

| ID | Status | Plan |
|---|---|---|
| M-GAP-003 | OPEN | Keep the laptop soak running. Do not mark 7 days from a shorter window. |
| M-GAP-004 | OPEN | CI stays a template until the GitHub App has `workflows` permission. Do not push a workflow to force it. |
| M-GAP-005 | OPEN | Keep watching SQLite integrity. Do not switch to WAL in the middle of a soak. |
| M-GAP-006 | MITIGATED | Leave OS time sync on. The probe still does not measure an NTP offset. |
| M-GAP-007 | MITIGATED | Agent-host success is already recorded. The operator Windows re-probe is still a user action. |
| M-GAP-008 | OPEN | The calibration harness exists. `INSUFFICIENT_DATA` is not a validation. Wait for real labeled observations. |
| M-GAP-009 | OPEN | Telegram stays blocked until the owner rotates the token. Do not invent a live transcript. |
| M-GAP-010 | MITIGATED | Backup tooling exists. Seven distinct nights and a second-machine restore are still user actions. |
| M-GAP-011 | OPEN in the table; a later row says the adapters are implemented and the live probe remains a user action | Do not call the live probe closed. CoinMarketCap still needs a key. |
| M-GAP-012 | OPTIONAL | Off-box alerting is not an acceptance item. |

Closed in the register and left closed: M-GAP-001, 002, 013, 014, 015, 016, 017, 018, 019, 020. This mission did not re-open them and did not add a new closed id.

## SPEC_TRACE wall-clock rows

| ID | Status | Plan |
|---|---|---|
| M13 | PARTIAL | The paper book is running. Acceptance still wants a calendar month of soak. Do not count the current book as that month. |
| M31 | PARTIAL | Nightly digest code exists. The 30-night send streak is not claimed. Digest send stays BLOCKED until that streak is real. |
| M36 | PARTIAL | `reports/grok/M36/soak_72h_receipt.json` was `NOT_MET` at the last trace. Do not write COMPLETE over it. |
| Edge | UNPROVEN | Promotion still needs 30 out-of-sample closes, DSR above 0.95, and PBO under 0.5. The learning loop now refuses to move a weight without those numbers. |

## Left open by this mission

- 32 agent seats remain unfilled, including AG-01 MISSING. Only AG-18 and AG-19 were filled, because those two received a module and a test.
- SSRN is `ABSENT_NO_FEED`. No paper was invented.
- The three weekly research ideas have a null predicted score on every desk. They stay shadow.
- The 2026-10-30 diagnosis (bad timing, shadow difference 0.0132 USD) was not applied.
- `SPEC_TRACE.md` recorded pip-audit, gitleaks, and bandit as `TOOL_ABSENT`. This mission did not re-run those scanners.
- The six-hour gate window is a separate receipt. It is not closed by this file.

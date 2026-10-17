# CRITIQUE — M47 fault injection + M39 monthly paper halt (2026-10-18)

## What was required
- M47: READ / DOWNGRADE / HALT, four faults warn or halt within 60s, cannot delete logs, unHALT only with the owner.
- M39: stale data, provider error, ledger mismatch, USDT depeg > 0.5%, broker API anomaly halt the paper path. AI cannot promote.
- Soak wiring: a HALT latches and the next paper cycle is refused.

## What this pass actually does
- `architecture/health/faults.py` classifies nine synthetic faults as HALT in-process.
- `latch_halt` sticks HALT for the soak process. `scripts/m13_gold_soak.py` writes `health` and `entries_allowed` and skips later cycles while latched.
- `owner_unhalt` refuses every non-owner actor. It does not clear `HOLD.flag` and it is not called by the soak loop.
- `refuse_log_deletion` leaves the file bytes unchanged.

## Adversarial critique
| Gap | Status |
|-----|--------|
| Killing a live daemon, filling the disk, locking PGlite, or breaking the live hash chain | Not done. Those would damage the running paper soak. The suite injects the observation and checks the decision. |
| Flatten in ≤ 60s on a real broker | No broker and no live order path. The decision itself is timed; there is nothing real to flatten. |
| Owner signature cryptography | A length-checked owner token in tests, not a key ceremony. |
| Already-running soak PID | This process keeps the previous code until it is restarted by the operator. This pass does not kill it. |
| AI promotion | Rejected in the fault responder. The tier gate still cannot promote by itself (existing M13 rule). |

## Verdict
**M47 fault suite + soak latch: PASS** for paper decisions. **M39 monthly suite: PASS** for the five paper triggers. Live destructive injection and a real flatten remain out of scope while HOLD and PAPER_ONLY stand.

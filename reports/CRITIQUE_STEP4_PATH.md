# CRITIQUE — gold paper path wiring (2026-10-18)

## What changed
`GoldPaperTrack.run_cycle` asks the paper OMS before a new entry. A rejected venue, a paper drawdown above 10%, or a gateway rejection is an extra block. The breaker and the ledger halt still bind. Kelly does not raise the pre-registered notional. The model slot is requested for council, not for an order. A proposal is recorded with merge false. A settled loss can file an unverified lesson in a sidecar sqlite, not in the mission ledger.

## Evidence
`pytest tests/test_paper_path_wire.py` plus the existing gold/judge/soak safety tests run after the edit.

## Not proven
- The already-running soak process still has the previous code. `start_soak.ps1` no-ops while that process is alive, so this commit does not create a second writer.
- No live order path was added.
- Oil is not on this cycle.
- The sidecar lesson is not read back by the soak before the next entry.

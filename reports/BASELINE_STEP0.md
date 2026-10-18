# Step 0 baseline (read only)

Recorded 2026-10-18 after the path-wiring commit. The live ledger file was not rewritten by this note.

- Ledger: `data/mission_ledger/mission_ledger.jsonl`
- Head: `1bd33bf132367fa782b9decfc30ee1042c92de7687d902911d67d80930befe1e`
- Gold checkpoint cycle: 582
- `paper_only`: true
- Soak process: PID 10564 started 2026-10-17 23:48:48, child PID 7124 (venv launcher and interpreter, one soak)
- Safety pytest after the path edit: `test_gold_judge.py`, `test_m13_gold_soak.py`, `test_zero_money_invariant.py`, `test_tier_gate.py`, `test_m42_single_ledger.py` → 157 passed
- Path tests: `test_paper_path_wire.py` and `test_gold_paper_cycle.py` and `test_m38_gateway.py` → 43 passed

The running soak still executes the code it loaded at start. `start_soak.ps1` is a no-op while PID 10564 is alive, so the new OMS path is not inside that process yet.

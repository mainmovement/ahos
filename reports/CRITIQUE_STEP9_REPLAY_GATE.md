# Critique — Step 9 replay → tier gate inputs

Date: 2026-10-18 (Tehran).

## Change
- Canonical replay feed: `reports/grok/M13_REPLAY/tier_gate_replay_inputs.json` (gold + oil blocks, REPLAY_NOT_LIVE).
- `gate_inputs.tier_gate_kwargs(market=...)`; cost model strings include **2x slippage** phrase for measurability.
- `export_tier_gate_replay_evidence.py` writes `M13_REPLAY/tier_gate_exports/*.md` + `summary.json`.

## Proof
```
pytest tests/test_gate_inputs.py -q  → 2 passed
python scripts/export_tier_gate_replay_evidence.py --gold-ledger <TEMP copy>
```
Gold/oil: `cost_model` and `walk_forward` measurable; many live criteria still UNMEASURABLE (honest). Replay verdict: NO_PROVEN_EDGE.

## Gaps
- Live soak tier gate day files under M13_SOAK still reflect pre-restart process.
- Regime coverage still unmeasurable (M-REGIME-4 owner).

## Verdict
Step 9 **PARTIAL**: replay numbers feed the gate machinery; promotion still blocked.

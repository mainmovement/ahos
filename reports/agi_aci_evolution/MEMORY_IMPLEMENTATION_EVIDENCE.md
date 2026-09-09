# MEMORY_IMPLEMENTATION_EVIDENCE

**Implementation commit:** `1b6b4c0`  
**Base SHA:** `1f4febb9b373e01271654515db58dfe72371a0c0`

## Commands

```text
python3 -B scripts/freeze_lane_a.py
# Lane-A integrity OK (36 files pinned)  PASS

/tmp/ahos-test-venv/bin/python -m pytest -q -p no:cacheprovider \
  tests/test_cognitive_memory.py \
  tests/test_cognitive_core.py \
  tests/test_self_evolution_engine.py \
  tests/test_multi_mind_council_anti_echo.py
# 37 passed in 0.48s  PASS

/tmp/ahos-test-venv/bin/python scripts/validate_imports.py
# VALIDATION PASSED  203 modules; 37 evidence-surface files; Lane-A OK
# orphan WARN 12 modules: PRE-EXISTING
```

System `python3 -m pytest` remains ENVIRONMENT_FAILURE without a venv (PEP 668) if invoked that way; tests above used `/tmp/ahos-test-venv`.

## What the tests prove

- Isolated DB; soak/Lane-A/knowledge filenames refused
- Restart persistence + MEM-###### ids
- UNKNOWN provenance allowed; empty provenance rejected
- AI_MODEL cannot be OBSERVED_FACT; PREDICTION stays PREDICTION
- Contradiction keeps both rows; supersede keeps history
- Decay STALE ≠ delete; event time ≠ revision ingestion time
- HYP + ExperimentLedger linkage without replacing those stores
- Failure recurrence fingerprint
- Agent namespace isolation
- Integrity hash detects in-place tamper
- Memory cannot authorize execution/trading/autonomy
- Consolidation cannot write OBSERVED_FACT

## Soak / Lane A

Soak DB not opened. Lane A freeze unchanged. `.env` untouched.

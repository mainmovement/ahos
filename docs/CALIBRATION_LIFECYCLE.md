# AHOS — Calibration / Prediction Lifecycle

**Status:** CANONICAL (Lane-B bridge + frozen Lane-A labeler)  
**Date:** 2026-08-27  
**Related:** `architecture/learning/prediction_lifecycle.py`, `discovery/lifecycle.py`, `discovery/outcomes.py`, `architecture/learning/calibration.py`

---

## What a prediction is

A prediction is one append-only row in `opportunity_score_ledger` written by
`ScoreLedger.record` / `record_many` at scoring time:

| Field | Meaning |
|-------|---------|
| `token_id` | `sha256(chain:normalized_address)[:32]` — join key |
| `chain` / `token_address` | Asset identity |
| `scored_ts` | When the score was produced |
| `opportunity_score` / risk / confidence | Deterministic engine output |
| `source` | Only `local` is calibration-eligible |
| `source_provider` | Discovery provider provenance |
| `evidence_sha256` | Evidence fingerprint |

Horizon is **not** stored on the prediction. Calibration chooses horizon at report time (default `24h`, event class `+50%`).

---

## Lifecycle (deterministic)

```
Collect candidates (CollectorEngine)
        │
        ├─ persist production_observations (Lane-B side table)
        │
        └─ register_for_observation  ← prediction_lifecycle bridge (Lane B)
                │
                ├─ tokens / pairs upsert
                ├─ observation_state DISCOVERED
                └─ discovery_observations (real metrics; NULL for missing)
        │
Score → ScoreLedger prediction (source=local when configured)
        │
--observation-cycle (optional, recommended)
        │
        ├─ observe_active polls due tokens (frozen Lane A)
        ├─ lifecycle.sweep → RESOLVED at T+72h
        └─ materialize_outcomes → outcome_label
        │
CalibrationHarness.join
        │
        └─ token_id + horizon + event_class
           AND resolved_ts > scored_ts   (no peeking)
           AND source IN {local}
```

---

## Closure / censoring / failures

| Situation | Behavior |
|-----------|----------|
| Asset disappears / provider down | Poller records failures; gaps registered; DEAD after 24h without obs; still RESOLVED at T+72h |
| Liquidity collapses | Later observations record low liquidity (or NULL); outcomes use price path when present |
| Horizon not closed | `compute_outcomes` skips (no peeking) |
| No Lane-A registration | `no_matching_label` exclusion — this was the 348→0 bug |
| Incomplete metrics | NULL fields; never fabricated zeros |
| Test/sandbox ledger rows | Excluded from calibration (source filter) |

---

## Operator commands

```powershell
# After scoring cycles have run:
python scripts/backfill_lane_a_from_production.py
python scripts/prediction_lifecycle_status.py

# Daemon with observation + local evidence:
python -m architecture.runtime --daemon --interval-sec 60 --observation-cycle --evidence-source local

# After ≥72h of RESOLVED tokens with observations:
python scripts/calibration_report.py
```

Until genuine outcome pairs exist, status remains:

**`CALIBRATION_READY_BUT_DATA_REQUIRED`**

Do not lower calibration guards to force a green verdict.

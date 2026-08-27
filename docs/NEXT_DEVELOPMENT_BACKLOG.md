# AHOS — Next Development Backlog

**Date:** 2026-08-27  
**Branch:** `cursor/ahos-cleanup-alignment-4bde`  
**Classification:** `INTEGRATION_READY` (agent-host)

## Completed this pass

| ID | Result |
|----|--------|
| P0-2b | Lane-B bridge registers scored candidates into Lane-A; backfill from production_observations; status CLI; lifecycle doc; clock-injected join test |
| P0-3 / P1 intel | Already on branch from prior commits |

## Remaining (ordered)

| ID | Goal | Blocker |
|----|------|---------|
| P0-2c | Wait T+72h + observation-cycle → first real outcome_label rows → calibration pairs | Wall clock / daemon uptime |
| P0-1b | Operator Windows `--probe-providers` | OWNER |
| P3-1 | Telegram live E2E | OWNER token |
| P4-1 | 168h soak | OWNER |
| P1-4 | Deeper holder/RPC | Partial; free RPC limits |
| P1-6 / P5 | Dev-activity / AG-25 | Explicit approval — not started this pass |
| P2-1 | Calibration guards met | Needs pairs from P0-2c |

## Next smallest high-value step

Keep daemon with `--observation-cycle --evidence-source local` for ≥72h, then run `python scripts/calibration_report.py` and confirm `joined_pairs > 0` (still expect `INSUFFICIENT_DATA` until guards).

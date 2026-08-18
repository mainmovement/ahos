# AHOS Phase Progress Snapshot

**Date:** 2026-08-18 · **Branch:** `arena/01a015c9-ahos`
**Classification:** `READY_FOR_REAL_LOCAL_DATA` *(infrastructure — see §4 for what that does and does not mean)*

Evidence rule for this document: a row may claim PASS only if it names a committed
artifact or a reproducible command. Prose is not evidence.

---

## 1. Phase status (1–12)

| Phase | Subject | Status | Evidence |
|---|---|---|---|
| 1–3 | Architecture, data infrastructure, scientific backtesting | **D Verified** | `reports/PHASE_STATE.md` P1–P3; 3.6y real datasets + MANIFEST; verdict **0/13 strategies accepted** |
| 4 | n8n automation (6 workflows) | **D (import) / C (execution)** | live import 6/6 on n8n 2.8.4; activation credential-gated |
| 5 | Telegram Persian interface | **C Tested** | 9-intent NLU + Section-X cards; **0 live runs** (token blocker) |
| 6–9 | Discovery core, PAL, feature store, paper trading | **C/D** | Lane-A frozen, 36 files hash-pinned |
| 10 | Runtime, collector, pipeline, Windows portability | **D Verified** | tests grew 411 → 516; `python -m architecture.runtime` proven |
| XX–46 | Historical waves (knowledge, council, observability) | **C/D** | `reports/PHASE_STATE.md` P36–P46 |
| **Phase 7** | Reality audit v2 + scheduler hardening + provider registry | **PASS** | clock-drift stub replaced; watchdog; CoinGecko + ChainExplorer + `collect()` facade |
| **Phase 8–9** | Month-1 operational gate, controlled failure matrix | **PASS** | `reports/month1_failure_matrix.json` (28/28), `reports/reliability_matrix.json` (7/7) |
| **Phase 10** | **Prediction ledger + calibration harness** | **PASS** | `architecture/learning/`; closed M-GAP-013 — scores were computed then discarded, making calibration structurally impossible |
| **Phase 11** | **Adversarial integrity audit of the prediction chain** | **PASS** | 44 adversarial tests; closed M-GAP-014/015/016 |
| **Phase 12** | **Local activation preparation** | **PASS** | `AHOS_LOCAL_ACTIVATION_CHECKLIST.md`, `scripts/local_activation_report.py`, `reports/local_activation_report.json` |
| **Phase 13** | **Laptop operation gate** | **BLOCKED — awaiting laptop** | `AHOS_LAPTOP_OPERATION_REPORT.md`, `scripts/soak_t0_snapshot.py`, `reports/local_laptop_baseline.json` (`official_168h_eligible=false`, failed `windows_host`) |

### Phase 13 outcome — the transition was correctly NOT made

The directive permits `READY_FOR_REAL_LOCAL_DATA → LOCAL_SOAK_RUNNING` **only if**
four conditions hold. None can hold in the agent sandbox:

| Condition | Required | Actual (sandbox) |
|---|---|---|
| Windows laptop | yes | **Linux** |
| `source=local` | yes | **`sandbox`** (default; opt-in by design) |
| watchdog OK | yes | **`NO_HEARTBEATS`** (daemon not started) |
| t0 snapshot exists | valid | **`t0_valid=false`** |

`scripts/record_local_laptop_baseline.py` exited `2` with
`STOP: baseline is not eligible; do not start the official 168h clock.`
Task 4 gates the daemon on a baseline PASS, so **the daemon was not started**,
no t0 was certified, and no prediction was fabricated.

**Classification therefore remains `READY_FOR_REAL_LOCAL_DATA`.**

### What Phases 10–12 actually changed

Phase 10 found that the scorer produced a complete `OpportunityScoreReport` every
cycle and **threw it away** — no table anywhere held a score, so outcome labels
could never be joined to what the system predicted.

Phase 11 attacked that repair adversarially and found three more defects:

| Gap | Defect | Status |
|---|---|---|
| M-GAP-013 | predictions never persisted | **CLOSED** |
| M-GAP-014 | Lane-A outcome labeler never called by the runtime — labels would never exist, so the join would return 0 pairs regardless of uptime | **CLOSED** |
| M-GAP-015 | no synthetic/real boundary — a test fixture or sandbox run could silently become calibration evidence | **CLOSED** |
| M-GAP-016 | `--probe-providers` was documented but did not exist | **CLOSED** |

Phase 12 verified the whole chain executes and packaged the laptop activation path.

---

## 2. Chain verification (Phase 12, Task 1)

Executed end-to-end this session, not inferred from code reading:

| Transition | Result | How it was shown |
|---|---|---|
| Provider → `collect()` | **REAL** | 1 candidate collected through `CollectorEngine` |
| collect → Normalization | **REAL** | `NormalizedTokenCandidate` + `identify_unknowns()` |
| Normalization → Observation | **REAL** | 1 row persisted to `production_observations` |
| Observation → Feature Store | **REAL** | frozen `feature_store` via `discovery/materialize.py` |
| Feature Store → Scoring | **REAL** | evidence-only bundle → score 100.0 |
| Scoring → **Prediction Ledger** | **REAL** | 1 row, `source=local`, engine `AHOS-SCORE-v1`, weight fp `686f0cb3`, evidence sha `f0ca7a70` |
| Observation → **Outcome Label** | **REAL** | frozen labeler wrote 24 label rows for a closed-horizon token |
| Prediction + Label → **Calibration** | **REAL** | **1 eligible pair joined**; verdict correctly `INSUFFICIENT_DATA` |

The join enforces `label.resolved_ts > prediction.scored_ts` in SQL, so a prediction
can never be graded by an outcome that closed before it existed.

---

## 3. Remaining blockers

### USER-ACTION-REQUIRED (cannot be solved by an agent)

| # | Blocker | Gap | Why it needs you |
|---|---|---|---|
| 1 | **168-hour local soak** on the Windows laptop | M-GAP-003 | Arena/sandbox hours never count |
| 2 | **Live provider success** | M-GAP-007 | This host: 2 × `TLS_ERROR`, 0 × `SUCCESS` — egress is blocked and was **not** worked around |
| 3 | **7 consecutive nightly backups** + fresh-host restore | M-GAP-010 | Series counts distinct UTC dates; needs 7 real days and a second machine |
| 4 | **Telegram token rotation** + admin chat id | M-GAP-009 | Old token is exposed and must be revoked |

### Blocked by data accrual (not by code)

| # | Item | Gap |
|---|---|---|
| 5 | Real scoring calibration | M-GAP-008 — harness exists; needs ≥ 200 real pairs per band |
| 6 | Multi-chain E2E + CoinMarketCap/Launchpad adapters | M-GAP-011 — Month 2 |

### Optional (not local-production blockers)

GitHub Actions CI (M-GAP-004), off-box watchdog alerting (M-GAP-012).

---

## 4. What `READY_FOR_REAL_LOCAL_DATA` means

**It means:** the code path from provider to calibration is wired, executes
end-to-end, is adversarially tested, and is honestly instrumented. The laptop
activation path is documented and every referenced script exists.

**It does not mean:** the soak ran, the providers work, the scoring is calibrated,
the backups happened, or the system is production-ready. On this host the
activation report classifies as `INSTALLED_AWAITING_REAL_DATA_PRECONDITIONS`
because two real-data preconditions are unmet (no provider egress; evidence
namespace is `sandbox`, not `local`).

Current honest measurements on this host:

```
predictions in ledger : 0
outcome labels        : 0
calibration status    : INSUFFICIENT_DATA (0 eligible pairs)
provider probe        : {'UNSUPPORTED': 4, 'TLS_ERROR': 2}, any_success=False
```

---

## 5. Next operational milestone

**Run AHOS on the Windows laptop and begin real data accumulation.**

1. Work through `AHOS_LOCAL_ACTIVATION_CHECKLIST.md` (all boxes).
2. `python -m architecture.runtime --probe-providers` → commit the artifact.
   A single `SUCCESS` closes M-GAP-007 and is the gate for everything downstream.
3. `python scripts/record_local_laptop_baseline.py` → require
   `official_168h_eligible=true` (exits `2` and refuses otherwise).
4. `python scripts/local_activation_report.py` → require `READY_FOR_REAL_LOCAL_DATA`.
5. Start the daemon with **`AHOS_EVIDENCE_SOURCE=local`** (default is `sandbox`;
   without this, predictions are recorded but never calibration-eligible).
6. `python scripts/soak_t0_snapshot.py` → require `t0_valid=true`.
   **That timestamp is hour 0 of 168**, and only then does this document's
   classification advance to `LOCAL_SOAK_RUNNING`.
7. Fill in `AHOS_LAPTOP_OPERATION_REPORT.md` from the artifacts.
8. Nightly: `python scripts/sqlite_backup_restore.py nightly`.

Then, and only then:

```
Real Predictions → Real Outcomes → Real Calibration → Real Learning
```

The first meaningful calibration report is weeks away by construction — the
pre-registered guards (n ≥ 200 per band, ≥ 20 positives) are inherited from
`research/baseline_stats.py` and **must not be lowered** to produce a greener word.

---

## 6. Standing gates

| Gate | State |
|---|---|
| Lane-A freeze | **36 files pinned, unchanged** |
| Test suite | **1096 passed / 0 failed** (`reports/pytest_run.json`) |
| Import + architecture gate | **PASS** (`reports/validate_imports_run.json`) |
| Execution surface | **NO_EXECUTION_SURFACE** — no ccxt/web3/order/wallet/signing |
| TLS verification | never bypassed (scan-enforced by test) |
| Paper-only invariant | ENFORCED |

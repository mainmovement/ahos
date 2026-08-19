# AHOS Canonicalization Inventory and Source Comparison

**Audit date:** 2026-08-19
**Baseline commit:** `b46720c02f9ea4bdb69c51208299de2c0d52d248`
**Rule:** this inventory was completed before canonical source integration or cleanup. No
source or historical artifact was deleted during the inventory.

## 1. Source evidence audited

The checkout contains one Git commit (an uploaded aggregate), 639 tracked files and
19,982,209 tracked bytes. Because the Git history does not preserve the development
sequence, the following artifacts are independent source evidence rather than clutter:

| Evidence | What it contains | Canonicalization treatment |
|---|---|---|
| Current checkout | 258 Python files, 93 test files, schemas, workflows, research datasets and reports | Runtime baseline, not an automatic winner |
| `01a00f79-… (1).md` | A valid 90-file Git patch; includes later intelligence/council, calibration, position-monitor and Telegram work omitted from the uploaded tree | Semantically inspected; valuable changes will be ported, not blindly applied |
| `01a01560-….md` | A valid 41-file Git patch containing reliability/soak evidence and tooling | Existing stronger implementations retained; unique evidence preserved historically |
| `01a015c9-….md` | A valid 45-file Git patch containing the current learning ledger, provider probe and Windows release work | Most new files match the checkout byte-for-byte and form the strongest learning/runtime baseline |
| `ahos_snap_w*_after.txt` | Phase-by-phase file-list snapshots | Historical evidence; not runtime source |
| Git commit | Aggregate upload with no parent history available in this checkout | Provenance anchor only |

The three patch artifacts are the recoverable representation of the accumulated
`ahos` / `ahos-01` / `ahos-main` work available in this repository. Their file-level
contents were compared with the checkout. In particular, 19 paths from the first patch
and 17 paths from the second patch were absent from the checkout; these were inspected
before any cleanup decision.

## 2. Baseline validation (before integration)

| Check actually executed | Result |
|---|---|
| Python | CPython 3.11.2 |
| Python compile | PASS |
| n8n structural validator | 6/6 PASS |
| Lane-A hash freeze | PASS, 36 pinned files |
| Import/architecture/secrets validator | PASS, 146 modules imported; 17 evidence-boundary files and 2,065 source files scanned |
| Full pytest | **1 failed, 1,158 passed** in 155.26 s |

The one baseline failure is real, not suppressed:
`tests/test_phase13_laptop_operation.py::test_operation_report_dependency_hashes_are_real`.
`AHOS_LAPTOP_OPERATION_REPORT.md` contains the old `requirements.txt` SHA-256
`9a5ef0…`; the actual file hash is `af3e77…`. The Lane-A hash in that document is
correct. The committed `reports/pytest_run.json` is also stale (it reports an earlier
1,140-test run). These facts are corrected during documentation/QA consolidation.

## 3. Canonical capability map

| Responsibility | Implementations found | Evidence/test status | Canonical decision |
|---|---|---|---|
| Discovery / observation | Frozen `discovery/` E-01 PAL, identity, observation, lifecycle, feature store, security gate, outcomes and ranker | Broadly tested; 36-file Lane-A freeze passes; runtime observation hook exists | Keep as the scientific Lane-A source of truth; do not rewrite during unification |
| Provider abstraction | Frozen `discovery/pal.py`; production `architecture/providers/*`; older AI `architecture/provider_router.py`; Telegram AI PAL | Unit/failure tests exist. Six configured runtime adapters are registered. Provider probe honestly reports unsupported/TLS states | Keep domain-specific PALs deliberately; document their distinct boundaries. Do not claim CoinMarketCap support merely because a docstring names it |
| Evidence normalization | `architecture/intelligence/evidence.py` plus adapters | Tested and wired into scoring pipeline | Canonical evidence boundary |
| Features / risk / score | `architecture/features`, `architecture/risk`, `architecture/scoring` | Tested; scoring facade consumes materialized Evidence | Canonical deterministic decision floor |
| Ranking | Frozen `discovery/ranker.py`, plus runtime sorting in orchestrator | Tested; runtime currently ranks paired candidate/report objects | Retain Lane-A ranker for experiment data and runtime rank ordering for current candidates; document scope to avoid calling them competitors |
| Decision / response | `architecture/decision/advisor.py`; response formatter; patch-only specialist vetting work | Advisor tested but not wired into autonomous pipeline in checkout | Integrate advisor/panel/exitability into canonical orchestrator without bypassing Evidence scoring |
| Intelligence | `architecture/intel/*` raw-domain analyzers and `architecture/intelligence/*` Evidence-only engine | Both tested. The former supplies narrative/exitability/whale context; the latter is the canonical score path | Preserve as complementary layers; document that `intel` is context collection and `intelligence` is the Evidence contract/engine |
| Cognitive council | 10-lens `panel.py` in checkout; 39-lens/team implementation in patch; advisory live AI council | Checkout panel tested but patch implementation is materially more complete and has 100-member coverage/team governance tests | Integrate expanded deterministic panel and team registry; AI council remains optional/advisory |
| Learning / calibration | Strong current `architecture/learning/{score_ledger,calibration}.py`; older patch `architecture/evolution/{score_ledger,calibration}.py` | Current code has stronger no-peeking, source isolation, append-only guards and runtime wiring. Older code has useful Brier/Murphy/probability utilities but an obsolete store schema/path | `architecture/learning` is canonical. Port useful statistics/probability API; do not restore a competing production ledger |
| Evolution | Hindsight and controlled proposal engine | Tested; advisory/governed | Keep separate from empirical learning; no autonomous code mutation |
| Positions | Canonical paper position manager; frozen paper lab; patch-only active-position monitor | Tested components, but checkout manager cannot enumerate open positions and runtime does not monitor them | Integrate read-only enumeration and monitor; preserve paper-only boundary |
| Paper trading | `paper_trading/engine.py`, `engine_v2.py`, `engine_v3.py` and versioned schemas | Extensively tested and frozen as Lane A | Keep all three intentionally versioned experiment engines; they are not duplicate production runtimes |
| Telegram | Production adapter, security gate, Persian intent/service/response, polling launcher | Extensively tested. Patch exposes missing announcement-follow-up and HTML escaping | Integrate patch capability and persist only non-secret local conversational pointers |
| Runtime / scheduling | `architecture/runtime`, scheduler/watchdog, observation loop | Tested and connected. Root Windows launchers use observation cycle and local evidence source | Canonical runtime; harden installer and Docker commands |
| Research / strategy lab | Causal backtest/lab, registries and real CSV datasets | Tests and SHA manifests exist | Retain as isolated research lane; replace machine-specific paths |
| n8n | Six structurally valid JSON workflows | Structural validation only; `active` absent and Telegram/Postgres credentials required | Optional automation edge, explicitly inactive until imported/configured; never the decision brain |
| Docker / services | Root laptop compose plus multiple deployment/target designs | Some config tests; several files describe different scopes | Root compose becomes canonical optional laptop profile; deployment variants classified as operational or design-only |
| Databases | Four runtime SQLite stores generated from versioned SQL/code; PostgreSQL target schema | No tracked SQLite file existed at audit start. Bootstrap and synthetic backup/restore are tested | Runtime DBs remain ignored; schemas and integrity tooling remain tracked |
| Windows | PowerShell installer and PS1/BAT launchers; path resolver | Launchers structurally tested, but installer did not initialize DBs and did not enforce Python >=3.11; generated `config/paths.yaml` was machine-specific and tracked | Fix installer, make generated path snapshot local-only, preserve CRLF, add static launcher tests |

## 4. Duplicate and conflict findings

1. **Learning conflict:** the patch-only evolution ledger/calibrator is not restored as a
   second production stack. Current `architecture/learning` wins on integrity and runtime
   integration; unique statistical behavior is ported there.
2. **Panel conflict:** the patch version is the verified superset (team structure,
   evidence-independent convergence, more executable lenses). It becomes canonical after
   running both old and recovered tests.
3. **Paper engine versions:** `engine.py`, `engine_v2.py`, and `engine_v3.py` are preserved
   because their schemas and pre-registered experiments are intentionally versioned.
4. **Provider layers:** the discovery PAL, market-provider adapters and AI-provider routers
   remain separate because they serve different contracts. Their names and boundaries are
   documented instead of collapsing unlike responsibilities.
5. **Generated path file:** `config/paths.yaml` contains `/home/user/ahos` and is generated by
   `config/paths.py`; it is local state, not canonical configuration.
6. **Historical “final” reports:** several dated files make superseded readiness claims.
   Their evidentiary content is preserved, but canonical docs must not present those claims
   as current status.

## 5. Safety decision

No exchange SDK, wallet SDK, signing call or order-placement surface is present. Live
execution remains prohibited. Recovered decision and sizing work is advisory and paper-only;
it must not create a live execution path. Provider/AI failure remains UNKNOWN or degraded,
never a fabricated success.

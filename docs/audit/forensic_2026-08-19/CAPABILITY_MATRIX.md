# Capability and readiness matrix

## Legend

- **G (GREEN):** meaningful implementation and evidence support this dimension.
- **Y (YELLOW):** useful partial implementation, isolation test, or static evidence; end-to-end proof is incomplete.
- **R (RED):** absent, broken, unsafe as delivered, or no evidence for the claimed operational dimension.
- **N/A:** dimension is not applicable to the artifact itself.

The dimensions are: correctness (**C**), integration (**I**), coverage (**T**), reliability (**Rly**), maintainability (**M**), documentation (**D**), security (**S**), native Windows compatibility (**W**), and operational readiness (**O**). GREEN means “green for its bounded contract,” not “production-ready overall.”

## 1. Subsystem scorecard

| Subsystem | Reality status | C | I | T | Rly | M | D | S | W | O | Principal evidence / blocker |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|---|
| Safety / zero-money invariant | `IMPLEMENTED` | G | G | G | G | G | G | G | Y | G | no order/wallet path; safety and forbidden-pattern tests |
| Evidence boundary | `IMPLEMENTED` | G | G | G | G | G | G | G | G | G | EvidenceBundle APIs plus static forbidden-import gate |
| Deterministic features/risk/scoring | `IMPLEMENTED` | G | G | G | G | G | G | G | G | Y | broad matrices and integrations; no empirical calibration yet |
| Security intelligence | `IMPLEMENTED`, externally constrained | G | G | G | Y | G | G | G | Y | Y | UNKNOWN discipline is strong; source reachability not proven |
| Runtime provider abstraction | `IMPLEMENTED`, `REQUIRES_EXTERNAL_SERVICE` | G | G | G | Y | Y | Y | G | Y | Y | 83 focused tests; live providers not called; configs fragmented |
| Frozen discovery/PAL | `IMPLEMENTED`, `EXPERIMENTAL` | G | G | G | Y | Y | G | G | Y | Y | hash-pinned and tested; generated store has no current rows |
| Production collector | `IMPLEMENTED` | G | G | G | Y | Y | Y | G | Y | Y | failure events/circuit tests; shared DB schema ownership |
| Canonical pipeline | `IMPLEMENTED` | G | G | G | Y | G | G | G | Y | Y | identity pairing, veto chain, alert suppression tested |
| Exitability/virality/whale specialist chain | `IMPLEMENTED` | G | G | G | Y | Y | G | G | Y | Y | wired before entry alerts; external holder/news data often UNKNOWN |
| Cognitive panel/advisor/sizing | `IMPLEMENTED` | G | G | G | Y | Y | G | G | Y | Y | 42 executable lenses; sizing abstains without calibration |
| Alerts | `IMPLEMENTED` | G | G | G | Y | G | G | G | Y | Y | deterministic and gated; live delivery not proven |
| Telegram domain/NLU | `IMPLEMENTED` | G | G | G | Y | G | G | Y | Y | Y | extensive Persian tests; empty allowlist permits public access |
| Telegram live transport | `BROKEN`, externally/user constrained | Y | R | Y | R | G | G | R | Y | R | default-open authorization; embedded poller has no offset; competing pollers; no live run |
| AI LiveCouncil chat | `PARTIALLY_IMPLEMENTED` | G | Y | G | Y | Y | Y | Y | Y | R | injected transport tests; no Ollama/cloud execution evidence |
| Local AI / Ollama | `REQUIRES_EXTERNAL_SERVICE`, `REQUIRES_USER_ACTION` | Y | Y | Y | R | Y | Y | Y | R | R | OpenAI-compatible HTTP path only; host/model not proven |
| Embeddings/RAG/vector memory/tools | `DOCUMENTED_ONLY`/absent | R | R | R | R | N/A | R | R | R | R | no implementation or contracts |
| Prediction score ledger | `IMPLEMENTED` | G | G | G | G | G | G | G | G | Y | append-only/source-isolated tests; generated ledger empty |
| Outcome join/calibration | code `IMPLEMENTED`, evidence insufficient | G | G | G | Y | G | G | G | G | R | fresh report: 0 predictions, 0 labels, `INSUFFICIENT_DATA` |
| Canonical paper positions | `IMPLEMENTED` | G | G | G | Y | G | G | G | Y | Y | runtime monitoring wired; empty local store |
| Versioned paper research | `EXPERIMENTAL` | G | Y | G | Y | Y | G | G | Y | Y | v1/v2/v3/v3.2 intentionally retained, not live runtime |
| Research CSV/baselines | `IMPLEMENTED`, `EXPERIMENTAL` | G | Y | G | Y | Y | Y | Y | G | Y | hashes/rows/times match; external replay/licensing gaps |
| Scheduler/watchdog | `IMPLEMENTED` | G | G | G | Y | G | G | G | Y | Y | deterministic fault tests; no real sleep/reboot/service proof |
| Runtime lifecycle/metrics | `IMPLEMENTED` | G | G | G | Y | G | G | G | Y | Y | tested state/health; generated evidence tables empty |
| Knowledge claim store | `IMPLEMENTED`, empty | G | Y | G | Y | G | G | G | G | Y | schema/append-only tests; no current claims |
| Agent registry | `PARTIALLY_IMPLEMENTED` | Y | R | G | Y | Y | Y | G | Y | R | internally validated, but current status/evidence is stale |
| Control plane | `ORPHAN`, `SCAFFOLD` | G | R | G | Y | Y | Y | G | Y | R | injected-probe tests only; no canonical runtime entry |
| Self-evolution | `SCAFFOLD` | Y | R | Y | R | Y | Y | G | Y | R | in-memory stage machine only; rollback from monitoring impossible |
| Update manager | `SCAFFOLD` | Y | R | Y | R | Y | Y | G | Y | R | “apply” approves a plan but performs no update |
| Health/self-repair manager | `PARTIALLY_IMPLEMENTED` | Y | Y | Y | R | Y | Y | Y | Y | R | diagnostics useful; “repair” can only create empty DB files |
| SQLite bootstrap/migrations | `PARTIALLY_IMPLEMENTED` | G | G | G | Y | Y | G | G | Y | Y | 4 stores bootstrapped; `user_version=0`, distributed DDL ownership |
| Data integrity/runtime state | `BROKEN` isolation | Y | Y | Y | R | Y | Y | Y | G | R | all DBs integral, but tests/imports write real ignored stores |
| n8n workflows | `ORPHAN`, `REQUIRES_USER_ACTION` | Y | R | Y | R | Y | Y | Y | Y | R | JSON 6/6 only; DB/mount/import/credential mismatch |
| Docker image/root compose | `BROKEN` packaging surface | Y | Y | Y | R | Y | Y | R | Y | R | no `.dockerignore`; `.env` and machine data can enter image |
| Target/deployment compose profiles | `SCAFFOLD` | Y | R | Y | R | R | Y | Y | Y | R | five profiles, mutable tags, disconnected target services |
| Windows native installer/launchers | `PARTIALLY_IMPLEMENTED` | Y | G | Y | Y | G | G | Y | Y | R | CRLF/path/UTF-8 good; no native execution or restart proof |
| Dependency reproducibility | `PARTIALLY_IMPLEMENTED` | Y | Y | R | R | Y | Y | Y | Y | R | 8 core + 3 optional lower bounds; no lock, hashes, package metadata |
| Import/architecture validation | validator `IMPLEMENTED`; scope unsafe | Y | G | G | R | G | G | Y | G | R | imports 153 modules but executes `telegram_live_test` side effects |
| Test suite | `IMPLEMENTED` | G | G | G | Y | G | G | G | Y | Y | 1,414 pass; no coverage metric/live E2E; local DB coupling |
| Documentation governance | `PARTIALLY_IMPLEMENTED` | G | G | Y | Y | Y | Y | G | G | Y | precedence now explicit; highly visible stale reports remain |
| Evidence/report tooling | `IMPLEMENTED` | G | Y | G | Y | G | G | G | Y | Y | command artifacts/snapshots exist; most operation still manual |
| OSS capability intelligence | `SCAFFOLD` | Y | R | Y | R | Y | G | G | G | R | metadata audit only; no dependency/security/benchmark stages |
| Autonomous engineering agent | absent | R | R | R | R | N/A | Y | Y | R | R | no repo inspection, tools, edit/test/repair/Git/rollback loop |

## 2. Capability reality by requested concern

| Concern | Reality | Evidence-based conclusion |
|---|---|---|
| Discovery | `PARTIALLY_IMPLEMENTED` operationally | two implemented paths; provider/network results absent from current stores |
| Provider provenance | `IMPLEMENTED` in contracts; incomplete operationally | response/raw hashes and field sources exist; current live trace is absent |
| Intelligence/risk wiring | `IMPLEMENTED` | security and composed whale findings enter risk/score; specialist context enters panel/advisor |
| Security/whale intelligence | `IMPLEMENTED` with overlap | two whale abstractions are semantically different but insufficiently reconciled |
| Reproducible scoring | `IMPLEMENTED` at code level | deterministic/fingerprint tests pass; empirical ranking value is unproven |
| Prediction-to-outcome calibration | `PARTIALLY_IMPLEMENTED` | correct guards and joins, no usable rows |
| Learning | `PARTIALLY_IMPLEMENTED` | hindsight and post-trade lessons exist; no autonomous model/rule promotion |
| Scheduling | `IMPLEMENTED` locally | leases/drift/heartbeats tested; host restart and sleep behavior unproven |
| Telegram | domain `IMPLEMENTED`; deployment RED | no live run and authorization defaults open |
| AI council | `PARTIALLY_IMPLEMENTED` | advisory chat transport works under injected responses; not used in canonical automatic vetting |
| Local AI | minimal transport only | Ollama endpoint/model configured; no host/model/latency/resource evidence |
| n8n | `ORPHAN` | structurally valid workflows not executable from delivered canonical profile |
| Docker | `BROKEN` for safe build | context can include `.env`, `.git`, `.venv`, data, reports; Docker unavailable for proof |
| Windows | `PARTIALLY_IMPLEMENTED` | thoughtful scripts, no native execution proof or supervised restart |
| Autonomous engineering | `DOCUMENTED_ONLY`/absent | proposal stages are not a tool-using repair agent |

## 3. Overall rating

- **GREEN:** deterministic safety/evidence/scoring contracts and bounded test behavior.
- **YELLOW:** integrated Python runtime architecture, paper-only analysis, Windows scripts, research assets.
- **RED:** safe Docker packaging, private Telegram authorization default, import isolation, real calibration evidence, n8n delivery, Local AI beyond chat, and autonomous engineering.

**Overall: YELLOW, not ready for an unattended operational/readiness claim.**

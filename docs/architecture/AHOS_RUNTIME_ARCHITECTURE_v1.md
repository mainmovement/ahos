# AHOS RUNTIME ARCHITECTURE v1 (W12 PART C/D/L deliverable)
Status legend used per component: **IMPLEMENTED / TESTED / DESIGNED / BLOCKED / UNVERIFIED**.
Master law (W12 PART O): Temporal deploy, production PostgreSQL migration, Redis, NATS/Kafka,
Kubernetes, live AI provider keys, and production GitHub integration stay **DESIGN-ONLY** until
ALL of: (1) a real VPS/Docker host exists, (2) F1 convergence stage authorized, (3) E-01
materialization evidence, (4) the experimental gate report (Track A/B) is delivered. Nothing in
this document is claimed to run beyond the evidence column of its own table row.

## 1. Production topology (TARGET — per owner diagram, W12)
Owner-canonical topology (PART C directive, verbatim):
```
                 AHOS SINGLE START
                        │
                 CONTROL PLANE
                        │
              ┌─────────┴─────────┐
              │                   │
          PostgreSQL           Temporal
              │                   │
              └─────────┬─────────┘
                        │
                 Python Runtime
                        │
        ┌───────────────┼────────────────┐
        │               │                │
      Agents          Router           Council
        │               │                │
        │          AI Providers          │
        │               │                │
        └───────────────┼────────────────┘
                        │
                     Red Team
                        │
                  Decision Support
                        │
                Memory / Learning
                        │
                  Observability
```
Annotated variant (adds the OPTIONAL layers and the deterministic Lane-A floor that the
laws require in view — optional layers never affect system status, test-pinned):
                         ┌──────────────────────┐
                         │   OPERATOR (human)   │  PROMOTE-only authority; AHOS_START one verb
                         └──────────┬───────────┘
                                    │
                    ┌───────────────┴────────────────┐
                    │  MASTER RUNTIME CONTROLLER     │  today: architecture/control_plane.py
                    │  (single-start contract §3)    │  target slot: Temporal (DEFER-INSTALL)
                    └───────────────┬────────────────┘
        ┌───────────────┬───────────┼───────────────┬────────────────┬──────────────┐
   PostgreSQL*      Temporal*     Redis*        NATS*/Kafka*     n8n*           Observability*
   canonical        durable       cache/bus     event bus        external edge  OTel/Prometheus/
   state/evidence   workflows     (OPTIONAL     (OPTIONAL        (Telegram/     Grafana
   (CRITICAL)       (NON_CRIT)     NOT_JUST.)    NOT_JUST.)       webhooks)     (NON_CRITICAL)
        └───────────────┴───────────┴───────────────┴────────────────┴──────┬──────┘
                                                                            │
                          AGENT WORKERS (25 registered; boot_class ordered; orchestrated=0 today)
                          ┌───────────────┬───────────────┬───────────────┐
                     MODEL ROUTER      AI COUNCIL      RED TEAM        OSS CAPABILITY
                     (ADVISORY,        (ADVISORY,      (NON_CRITICAL,  INTEL AG-25
                      free-first,      verdicts not    fail-closed     (PLANNED;
                      probe-gated,     votes; no       for promotions) DISCOVERY→
                      breaker)         averaging)                      PROPOSAL only)
                          └───────────────┴───────────────┴───────────────┘
                                            │
              DETERMINISTIC LANE-A CORE (CRITICAL floor — NEVER depends on any AI/network target):
              collector → security gate → feature store → outcome labeler → paper engine →
              evidence stores (SQLite, append-only trigger-guarded post-F1-S1) → reports
```
\* = target/optional components: never fabricated as running; measured availability declared in
`config/control_plane.yaml` `infrastructure:` block (single source of truth, CI-pinned).

Lane separation (two-lane law, W12-added law: Lane A never stops for architecture): Lane A
(discovery.collect → paper_trading.cycle → probes → evidence) runs on the deterministic floor
by standing schedule, untouched by anything in this document. Isolation is CI-pinned
(static scan in tests/test_architecture_p1.py).

## 2. Component status table (measured 2026-08-13)
| Component | Status | Evidence / probe | Fallback & rollback |
|---|---|---|---|
| Deterministic Lane-A core (collector, gates, decide_v1, paper engine, outcomes) | IMPLEMENTED+TESTED; LIVE by schedule | t1–t12 cycle reports; 198/198 suite; probe PRB-* batteries | none needed — frozen experiment; any change = versioned card only |
| Evidence stores (3× SQLite) | IMPLEMENTED+TESTED; append-only guards LIVE post-F1-S1 | reports/f1_s1_{drill,apply}_20260813T025708Z.json (data_identical=true); test_f1_s1.py (7) | rollback = `engine/f1_s1_migration.py rollback` (drops 12 f1s1_* triggers), drill-proven |
| Master Runtime Controller (single-start surface) | IMPLEMENTED+TESTED (Python, in-repo) | tests/test_runtime_w11.py: one-start/idempotency/SAFE_HALT/resume/locks tests; single_start_runtime.md §5 | orchestrated=0 ⇒ rollback = do nothing; surface only REPORTS standing Lane-A liveness |
| PostgreSQL (canonical layer) | DESIGNED (DDL target); BLOCKED_NO_HOST | pg_parity_audit_w9.md (33/33 drift measured); control_plane.yaml BLOCKED_NO_HOST | SQLite stays source of truth; F1 plan S2–S5 gated |
| Temporal (durable workflows) | DESIGNED as TARGET; install DEFERRED | orchestration_comparison.md verdict RECOMMEND-AS-TARGET/DEFER-INSTALL; OSS audit W12A-OSS-1 (temporalio/sdk-python MIT, active ⇒ NO_INTEGRATION now, host-gated) | Python control plane keeps lifecycle semantics; adoption replay-gated |
| Redis | DESIGNED-OPTIONAL only (NOT_JUSTIFIED by evidence) | control_plane.yaml availability NOT_JUSTIFIED | excluded from compose target; never affects status (test-pinned) |
| NATS/Kafka | DESIGNED-OPTIONAL only (NOT_JUSTIFIED) | same | same |
| n8n | IMPLEMENTED workflows exist; LIVE execution BLOCKED_NO_HOST/NO_TELEGRAM_TOKENS | wave-6 live import smoke 6/6 (historical); W11 law: external edge ONLY (Telegram/webhooks/admin) — never in decision path | stays edge; token revocation user-open (R-28) |
| Observability stack (OTel/Prometheus/Grafana) | DESIGNED (§4); interim = run-ledger + probe reports IMPLEMENTED | control_plane run-ledger append-only + tamper test; reports/* cycle JSONs | interim stack is sufficient for experiment; target adopt at host |
| AI Provider Router | IMPLEMENTED+TESTED (free-first, probe-gated, breaker) | provider_router.py + contract; floor DETERMINISTIC_ONLY live-verified PRB-20260811-AI-001; 9 providers NEEDS_USER_KEY/NO_HOST/REFUTED | all-AI-failure ⇒ DETERMINISTIC_ONLY (PART G law, enforced) |
| AI Council (advisory) | IMPLEMENTED+TESTED | council.py + ai_council_contract_v1; no-vote/no-averaging/numeric-provenance lints (PART H laws) | deterministic engines AG-15/AG-16 remain only DECIDE authority |
| AG-25 OSS Capability Intelligence | SPECIFIED (PLANNED); first manual read-only audit EXECUTED | docs/architecture/OSS_CAPABILITY_DISCOVERY.md; reports/oss_capability_audit_1.json (W12A-OSS-1) | DISCOVERY→PROPOSAL only; integration requires ImprovementProposal → human gate |
| Kubernetes | NOT ADOPTED (UNJUSTIFIED at this scale) | this doc | revisit only if multi-node ever evidenced |

## 3. Single-start contract (PART D) — summary of single_start_runtime.md (unchanged)
Owner-mandated boot chain (PART D directive, verbatim), each step ledgered and each failure
mapped to SAFE_HALT (CRITICAL path) or SYSTEM_DEGRADED (NON_CRITICAL/ADVISORY):
```
Preflight → PostgreSQL → Temporal → Agent Registry → Contracts → Health → Event/Queue →
Agent Runtime → Router → Council → Red Team → Observability → Telegram/External Edge →
SYSTEM ONLINE
```
This chain maps 1:1 onto the engine's 16 phases below (Event/Queue and External Edge are the
OPTIONAL/edge slots; their absence never blocks the core verdict — test-pinned).
Verbs: AHOS_START / AHOS_STOP / AHOS_STATUS / AHOS_SAFE_HALT / AHOS_RESUME over one control
surface with 16 ledgered phases (env → infra discovery → health chain → config/state → registry
validation → DAG cycle-check → locks → orchestrated startup → health verify → verdict).
Contract invariants, all TESTED: idempotent re-start (same run, 0 duplicate activations) ·
crash-resume skips completed phases · SAFE_HALT never replays as success · append-only ledger
with tamper test. Boots honestly today: with this sandbox config it reports SAFE_HALT/DEGRADED
rather than fabricating ONLINE (test_real_config_boot_never_fabricates_online).
Target: identical surface wraps docker compose + Temporal on a host; operator never sees the
difference. Adding systemd/K8s supervision = DESIGNED only (PART O).
Soak + fault-injection evidence (W13, tests/test_control_plane_soak.py — 8 tests, green):
exhaustive single-fault property on the REAL config (8 components × boot-class semantics:
CRITICAL⇒SAFE_HALT / NON_CRITICAL⇒DEGRADED / OPTIONAL⇒never affects status); seed-pinned
64-combination fuzz (no spurious halt, never blind-online); 150-op interleaved soak (monotonic
append-only ledger; every opened run closed exactly once; ledger tamper aborts); crash-injection
at state_verify + resume (zero duplicated phases, ≥1 genuinely skipped); ledger-unavailable ⇒
fail-fast with ZERO partial state file; 25-attempt lock flood (exactly one holder; exactly one
recorded stale-steal); recovery as NEW run with old-run history byte-frozen; prober crash ⇒
UNHEALTHY evidence, never an engine crash. Documented design boundary found by the battery:
run-id derives from (idempotency-key, timestamp) — a frozen clock makes consecutive post-HALT
attempts collide into one run stream (append-only still holds; production time.time advances).

## 4. Observability stack (PART L)
PART L mandates: OpenTelemetry · Prometheus · Grafana · structured logs · heartbeat ·
agent health · provider health · circuit state · run ledger · evidence lineage · failure registry.
Interim (IMPLEMENTED, sufficient for the frozen experiment):
- run ledger — append-only control-plane run-ledger (run/phase rows; tamper test-pinned);
- agent health + circuit state — registry ops blocks + router breaker state, persisted;
- provider health — probe battery reports (PRB-* ids on every claim);
- evidence lineage — sha-join census (W11A-01 lineage verified) + probe ids attached to
  reports; failure registry — register F-series (F1–F16) + per-wave transparency log;
- structured logs — cycle/evidence JSONs under reports/ + research/experiments/ (every cycle emits);
- heartbeat — control-plane health phases re-measured on every boot (never assumed).
Target (DESIGNED, adopt at host): OpenTelemetry traces on controller + agent workers →
Prometheus metrics (cycle counts, guard aborts, router breaker state, council evidence counts,
drift counters) → Grafana dashboards; alert channels via n8n edge → Telegram (after token fix).
Log law (both stacks): append-only, no history mutation, redaction of secrets by construction
(env-only reads); DISPLAYED vs REALIZABLE style dual-reporting applies to any runtime metric
that has a cost figure attached.

## 5. Rollback paths (per change class — each versioned, replayable, rollbackable: W12 law)
- F1-S1 triggers: `engine/f1_s1_migration.py rollback` (12 named drops; drill-proven on copies).
- Registry/config change: git-less ⇒ snapshot-manifest + file-level restore; every registry
  change is additive-versioned (matrix_version) and CI-pinned; AG-17 promotion rollback =
  revert status letter + evidence text (single block).
- Compose target: never built ⇒ nothing to roll back; the file itself is the design artifact.
- This document: descriptive only; zero runtime coupling (Lane-A integrity proof: no Lane-A
  file touched in W12; see R-34 for the manifest diff).

## 6. Open dependencies / blockers (unchanged unless evidenced otherwise)
VPS+Docker host (USER) · Telegram token revoke+re-inject (USER, R-28) · AI provider keys (USER)
· E-01 materialization gate ≥2026-08-14 18:00Z (CLOCK) · Track A ≥200 resolved + ≥20 positives
+ 2 windows / Track B ≥30 closed + ≥1 cost reconciliation (EXPERIMENT). Until then: everything
above marked DESIGNED/BLOCKED stays exactly that.

## 7. Master self-improvement loop (PART N target architecture — REGISTERED, not live)
Owner-mandated loop (PART N directive), registered here as the governed target:
```
                 WORLD / GITHUB / RESEARCH
                          │
                          ▼
                 Capability Discovery   ── AG-25 (spec; 1st read-only audit done, W12A-OSS-1)
                          │
                          ▼
                    Benchmarking        ── baseline_stats + pre-registered gates (implemented)
                          │
                          ▼
                     AI Router          ── provider_router.py (implemented+tested; free-first,
                 ┌────────┼────────┐      probe-gated, breaker, DETERMINISTIC_ONLY floor)
                 ▼        ▼        ▼
              Model A  Model B  Model C   ── all NEEDS_USER_KEY today (registry, honest)
                 └────────┼────────┘
                          ▼
                       Council          ── architecture/council.py (advisory; no votes/averages)
                          │
                          ▼
                       Red Team         ── AG-14 + proposal redteam stage (fail-closed)
                          │
                          ▼
                    Improvement Proposal ── contracts/improvement_proposal_v1.json (no-skip law)
                          │
                          ▼
                    Human Gate          ── never software; AI never approver (contract-pinned)
                          │
                          ▼
                  Versioned System      ── registry matrix_version + versioned cards only
                          │
                          ▼
                    AHOS Runtime        ── this document, §1–§4
                          │
              ┌───────────┼───────────┐
              ▼           ▼           ▼
            Data        Agents      Memory     ── e01/paper stores · 25-agent registry · AG-17/18
              │           │           │
              └───────────┼───────────┘
                          ▼
                    Evidence / PG     ── SQLite today (F1-S1 guarded); PG target host-gated
                          │
                          ▼
                    Learning Loop     ── AG-18 (PARTIAL); lessons machinery implemented
                          │
                          └──────→ back to Discovery
```
Governing property (the entire safety statement): the loop may be self-reinforcing in
OBSERVATION only; every reinforcing WRITE passes the PART K gate
(docs/architecture/SELF_EVOLUTION_LOOP.md). No stage may be skipped (contract law); every
stage carries evidence or the loop halts at the first missing link (no-evidence law).

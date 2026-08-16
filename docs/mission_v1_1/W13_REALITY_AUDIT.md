# W13 — REALITY AUDIT & GAP ANALYSIS (MASTER ROADMAP §32/§37 — AUDIT FIRST)
Date: 2026-08-13T03:5xZ · Method: everything below measured from the live workspace (RO queries,
file census, CI run, probe batteries) — the road-map text itself was treated as DOCTRINE, never
as fact (REALITY > DOCUMENTATION). Lane A frozen/untouched. Lane B read-only + this document.

## 0. Reality-vs-report reconciliation (CONTINUATION rules 2/10)
W12-reference numbers vs live measurement — every discrepancy RESOLVED as temporal advance,
not error (the report froze counters at its own apply-time; cycles t13/t14 advanced them):
| Metric | W12 report | Measured now | Verdict |
|---|---|---|---|
| e01 tokens | 569 (at F1-S1 apply) / 638 (t12) / 722 expected later | **722** | consistent (t13 +48, t14 +36 new; ingested≠new because identity dedup) |
| observations | 716 (apply) / 791 (t12) | **924** | consistent (t13 +68, t14 +65) |
| outcome_label (resolved) | 0 | **0** | match — NOT YET VALIDATED holds |
| paper v2 open / v3 exits | 11 / 0 | **11 / 0** | match |
| v1 legacy open / exits | 15 / 0 (monitored) | **15 / 0** | match |
| cash | $1.8984375 | **$1.8984375** | match (ledger coherent: ΣALLOCATE ⇒ cash 20→1.8984, 18.10 deployed) |
| triggers | paper 34 / e01 10 / local 2 | **34 / 10 / 2** | match (F1-S1 state live) |
| tests | 203 (after re-issue closure) | **203/203 green (17.8s)** | match |
| host | no Docker | **docker absent (which(1) empty); Python 3.13.14; git binary present** | match |
| secrets | none | **TELEGRAM/OPENAI/ANTHROPIC/GEMINI all UNSET; no .env files** | match — AI = OFFLINE/UNVERIFIED floor state |

## §32 items — the 20 required answers
**1. Current architecture.** Two-lane. Lane A (FROZEN): discovery/ (collect, identity, observations,
lifecycle, feature_store, security_gate, outcomes, ranker, holders, materialize, pal) →
paper_trading/ (engine v1 legacy monitor, engine_v2, engine_v3/decision_v3, realizable, risk,
ledger, cost_model, lessons) → research/ (baseline_stats, experiments, reports) →
evidence stores (3× SQLite, append-only trigger-guarded post-F1-S1). Lane B (evolution):
architecture/ (contracts, registry, control_plane, provider_router, council), contracts/
(5 JSON-schema contracts incl. ops-extension), config/ (control_plane, agent_registry 25,
cognitive_principles v2-63, ai_provider_registry 9-lane, ai_providers), engine/ tooling
(f1_s1_migration, agent_matrix_v2, pal_probe, doc_hygiene, ahos_backtest), deployment/
(design-only compose). Standing cadence: cycles fire per user trigger (NO autonomous scheduler
in this sandbox — measured gap G-SCHED).
**2. Current agents.** 25 = EXISTS 9 (AG-02,03,07,08,09,15,16,17,21) · PARTIAL 12 · PLANNED 3
(11,20,25) · MISSING 1 (AG-01). Operability (machine-truthful): implemented 21 / contracted 6 /
orchestrated 0 / live 15. Boot classes 10 CRITICAL / 9 NON_CRITICAL / 6 ADVISORY / 0 OPTIONAL.
DAG acyclic (CI-pinned). Only AG-15/16 hold DECIDE; AG-23 = human gateway (never software);
AG-25 = DISCOVERY→PROPOSAL only.
**3. Current files.** 281 non-cache files: docs 84 · reports 46 · research 39 · paper_trading 22 ·
tests 15 · discovery 14 · engine 13 · telegram_ai 6 · config 6 · contracts 5 · architecture 6 ·
strategy_lab 6 · n8n 6 · data 5 (3 sqlite + manifests) · database 3 · deployment 2. Versioning:
NO git repository (host has git binary but .git/config is outside snapshot persistence —
local-VCS value here is UNVERIFIED ⇒ manifest-snapshot discipline instead:
/home/user/ahos_snap_w1{1,2,2r}_after.txt kept).
**4. Current tests.** 203 collected / 186 test functions across 15 files; full suite ~18s green;
runner: python3 -m pytest tests/ -q --ignore=tests/validate_n8n.py. Distribution: discovery/
paper/research cores, runtime_w11 (44), f1_s1 (7), agent_matrix_v2 (5), architecture_p1 (14),
wave7/telegram/strategy batteries.
**5. Current experiment.** Track A: 722 tokens / 924 obs / **0 resolved** (first 72h closures
≥2026-08-14 18:00Z — CLOCK). Track B: 11 open v2 (PT-X3-v2; all NO_DATA by stale-law — proof
the guard fires), 15 legacy v1 monitored, 0 exits anywhere, cash $1.8984375, entry gate
QUALIFIED_SKIPPED_NO_CASH by design. Verdict: **NOT YET VALIDATED**. B2 scan gated ≥200 resolved
(~2026-08-17 by cadence). §O 24h report clock-gated ≥2026-08-13 08:05Z (now 03:5xZ ⇒ PENDING).
**6. Current blockers.** USER: VPS/Docker host · Telegram token revoke+re-inject (R-28,
tokens compromised) · AI provider keys. CLOCK: E-01 materialization 08-14 18:00Z; §O report.
OWNER-OPEN: F12 tracked-token freshness (collector refreshes discovery universe, not the 11
tracked tokens — stale-law then converts to NO_DATA; inert-but-safe; any change to Lane A
collector is governance-touching ⇒ owner decision ONLY).
**7. Host limitations.** No Docker/containers; no systemd; /tmp not persistent across sessions
(manifests moved under /home/user — fix applied W12); network egress OK for free endpoints;
git binary present (persistence semantics UNVERIFIED for .git/config).
**8. Current dependencies.** Python stdlib + pandas (+yaml, pytest in CI env). Runtime deps:
free HTTP endpoints only (GeckoTerminal, DexScreener, RugCheck, GoPlus, DefiLlama, 3×publicnode
RPCs, 2×Solana RPCs, 3×RSS) — latest probe: OK. Refuted/down endpoints kept as evidence:
LlamaRPC 521, Helius-public 401, CryptoPanic 404, cloudflare/ankr DEGRADED, pollinations 402.
Zero paid dependency; allow_paid=false.
**9. GitHub opportunities.** 8 Tier-1 candidates registered (read-only audits W12A-OSS-1/2):
temporalio/sdk-python ⇒ NO_INTEGRATION (host-gated, aligned with target verdict) ·
promptfoo (MIT) · crewAI (MIT; persona-conflict with PART I law) · apscheduler (MIT — maps to
G-SCHED) · prometheus/client_python (Apache-2.0, slow cadence) · opentelemetry-python
(Apache-2.0) · tenacity (Apache-2.0) · prefect (Apache-2.0 — orchestration alt; must refute
Temporal verdict by Tier-3 benchmark before any change) ⇒ all CANDIDATE_HELD_UNVERIFIED.
None integrated; GitHub=CANDIDATE law held.
**10. AI-provider opportunities.** 9 capability lanes defined; all providers NEEDS_USER_KEY /
NO_HOST / REFUTED; keyless pollinations REFUTED (402). Floor DETERMINISTIC_ONLY live-verified
(PRB-20260811-AI-001). Opportunity = user keys (cost $0 blocked by sanctions ⇒ likely local/
self-hosted path first when host exists — aligns with §11 priorities).
**11. Missing components.** AG-01 Master Orchestrator (MISSING — build only via PART K loop).
Typed payload-level agent IO (contract v2, F3 queue). Autonomous scheduler (G-SCHED).
OTel/Prometheus live stack. PG canonical layer (S2–S5). Temporal runtime. Live self-healing
repair loop (detection/breaker exist; classify→repair chain designed not live). Failure-registry
consolidation (F-series scattered across register docs — works, but not yet a queryable table).
**12. Duplicate components.** None un-manifested. Versioned generations (paper engine v1/v2/v3,
decision modules v1/v3, exit v1/v2/v3) coexist BY DESIGN (frozen experiment evidence vs active
code) — wave-7 hygiene manifest (D_CLEANUP_MANIFEST) covers byte-dupes (archived, not deleted).
**13. Deprecated components.** pollinations provider (REFUTED, kept). paper engine v1 =
PT-BASELINE-v1 legacy monitor (active by design for 15 legacy positions). n8n workflows
shipped but unactivated (edge-only law + token blocker).
**14. Security risks.** R-28 compromised Telegram tokens (USER). F1 residual: upsert-by-design
tables unguarded (documented, deliberate). No secrets in repo (no .env; env-unset verified).
Supply-chain: external code enters only via PART E tiers (Tier-2/3 host/owner-gated). AI
prompt-injection: envelopes validate; DETERMINISTIC_ONLY = floor.
**15. Self-healing gaps.** Present: health probes, circuit breakers (control plane + router),
SAFE_HALT/DEGRADED semantics, resume-from-ledger, idempotent restart (all TESTED). Absent:
live classify→diagnose→repair→verify chain (no live AI, no sandbox-executor on this host),
restart-policy/watchdog (no init system), automatic rollback executor (rollback plans exist
as contract artifacts — f1_s1 rollback is the proven exemplar).
**16. Self-learning gaps.** Lessons machinery live but 0 lessons (0 closed trades — honest).
Outcome labeling pipeline ready, 0 resolved. B2 hypothesis cells pre-registered (H14–H20),
blocked at ≥200 resolved. No cross-regime/feature-predictivity claims permitted before gates
(§26/§27 laws = current behavior).
**17. Single-start gaps.** Surface complete in-repo (START/STOP/STATUS/SAFE_HALT/RESUME; 16
phases; honest verdict). Gaps: container/Temporal boot = BLOCKED_NO_HOST; orchestrated=0 by
design; no watchdog across process death (needs host scheduler); AG-01 MISSING means
n8n-form orchestration slot unfilled — the Python control plane currently IS the interim
authority (documented).
**18. Observability gaps.** Interim (implemented): run-ledger (tamper-pinned), beacon probes,
cycle JSONs, sha-lineage census, breaker state, register F-series. Target (DESIGN only):
OTel traces, Prometheus metrics, Grafana dashboards, alert channel (Telegram blocked) —
all host-gated per PART O.
**19. Iran-access / cost risks.** Documented (W7_E_IRAN_RESILIENCE_MATRIX): sanctions block
paid APIs + cards ⇒ allow_paid=false stays; free-first enforced; offline-capable core (RO
stores + local sqlite + deterministic engines); GitHub API reachable (verified this wave);
residual: if GitHub/network drops, last snapshots remain usable (no automated offline-knowledge
mirror of candidates yet — note as P2 gap, NOT a blocker).
**20. Highest-value next actions (§33 priority order).**
- P0 (safety/integrity/evidence — all currently GREEN): hold the freeze; on-clock items:
  §O report ≥08:05Z · E-01 materialization ≥08-14 18:00Z THEN cohort report → baseline
  comparison → outcome-sufficiency audit → Experimental Validation Report. Maintain
  manifest diff each wave (done).
- P1: control-plane SOAK/FAULT-INJECTION battery in-repo (PART P #13 is partially executable
  NOW: repeated START/RESUME/HALT loops + injected provider/DB failures on the Python engine —
  no host needed); typed-IO contract v2 design (F3) — Lane-B doc/test only.
- P2: F12 owner decision memo (freshness-of-tracked-tokens: options + consequences, NO
  execution without approval); AG-25 stage-1 implementation as versioned tool
  (engine/oss_audit.py codifying the Tier-1 probe used twice ad-hoc — WHY: repeatability;
  PART-35 answered below); GitHub knowledge-mirror design (offline snapshot of candidate
  metadata — §11 resilience).
- P3: PG schema generation rehearsal (DDL translation dry-run from pg_parity_audit — pure
  design artifact, no DB); Temporal worker topology design doc.
- P4: host-gated — unchanged.
PART-35 answers for the single near-term BUILD candidate (engine/oss_audit.py): WHY — two
ad-hoc audits already run (drift risk of unversioned probes); WHAT PROBLEM — repeatability/
evidence-comparability; EVIDENCE — W12A-OSS-1/2 reports; ALTERNATIVE — keep ad-hoc (rejected:
violates reproducibility law); COST — ~120 LOC stdlib-only; RISK — GitHub rate-limit (60/h
unauth) ⇒ cadence cap + cache manifest; FAILURE MODE — API down ⇒ UNVERIFIED entries (honest,
no fabrication); TEST — fixture-replay test (recorded JSON) + schema lint; ROLLBACK — file
removal (additive, no consumer); VALUE — AG-25 duty #1/#10 get a deterministic executor.

## Lane-A integrity (this wave)
Zero Lane-A logic changes (hash-verified at wave end vs ahos_snap_w12r_after.txt — appended to
R-36); cycles t13/t14 ran standing-law only; guards non-interfering; 0 resolved unchanged ⇒
NOT YET VALIDATED unchanged. No post-result tuning, no threshold edits, no doc-rewrites of
contradictions (rule 10: none found — drift reconciled in §0 table with evidence).

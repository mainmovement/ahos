# AHOS CANONICAL — ROADMAP (single queue)
Full phase exits: docs/DEVELOPMENT_ROADMAP.md · wave ledger: docs/mission_v1_1/J · state: canonical/PROJECT_STATE.md.

> **W57 RECONCILED (documentation-only, per `docs/canonical/RECONCILIATION_R1.md`).** The Wave-6/7 queue
> below is retained as historical planning. The current **dependency-ordered** queue supersedes it for
> sequencing. This PR implements **only item 1** (canonical reconciliation); no P0/P1/P2… engineering work
> is performed here.

## W57 dependency-ordered queue (current)
1. **Canonical reconciliation** — align PROJECT_STATE/ARCHITECTURE/ROADMAP/README with W57 + resolve the
   W43↔registry ambiguity (R1). *← this PR (documentation-only).*
2. **One-Brain architecture decision** — choose the single production scoring engine (Python vs TypeScript)
   or define a binding sync contract. Prerequisite for de-duplicating downstream work.
3. **Security-VETO / WATCH-cap in Lane-B (P0)** — bring the Lane-B pipeline into line with MISSION law #2
   (Lane-A already compliant). Safety-critical.
4. **Rank-first reconciliation** — gate Lane-B numeric scoring until the research gate, per doctrine.
5. **Telegram stale-test decision** — align the W57 gateway-only expectations (deliberate decision, not a
   silent "green-fix"; test changes are out of scope for the reconciliation PR).
6. **Provider / narrative integration** — connect implemented-but-disabled providers and wire narrative/news
   into the pipeline.
7. **Scoring dimensions / observability / runtime tests** — catalyst/tokenomics/dev-activity scoring, web
   observability on PostgreSQL, runtime tests for the TypeScript engine.
8. **Gated future capabilities** — GitHub auto-issue, human-gated self-evolution activation, live AI council.

Each future item requires its own PR with: objective · why-now · prerequisites · files · canonical
requirement · acceptance · tests · runtime validation · safety gate · rollback · Lane (A/B) · human-approval
need. All items must preserve: Lane-A evidence integrity · paper-only boundary · One-Brain governance ·
canonical contracts · zero-money policy.

---

## Wave-6/7 historical queue (retained as evidence — NOT current sequencing)

## Position NOW
P1 arch ✅ · P2 discovery: pipeline C/RUNNING; exit needs 72h continuous log (≥2026-08-14) ·
P3 on-chain+security depth: next (RPC holders live-probe passed wave-6; GoPlus re-probe) ·
P4 scoring+validation: gated by E-01 ≥8 weeks (≈2026-10-06) · P5 n8n 20/21/22 (after PAL stable ≥1w) ·
P6 Persian TG (needs blocker①) · P7 paper monitoring · P8 evolution.

## Wave-6 engineering targets (directive Part XXV)
1. E-01 passes continue (in-session) 2. 72h cohorts accumulate 3. holder-growth feature where feasible
   (getTokenLargestAccounts; holder *count* = NOT feasible on free RPC → UNKNOWN, documented)
4. whale/wallet-cluster architecture (doc I) 5. social ingestion interfaces (doc J; no paid social APIs)
6. baseline/event statistics (research/baseline_stats.py) 7. H14+ generation design (doc H)
8. rank-first maintained 9. $0/month maintained.

## User blockers (unchanged, top of queue)
① Telegram token rotation + admin chat id ② Production VPS (24/7 + Iran probes + Postgres boot).

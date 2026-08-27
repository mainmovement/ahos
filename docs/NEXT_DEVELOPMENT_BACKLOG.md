# AHOS — Next Development Backlog

**Date:** 2026-08-27  
**Branch baseline:** `cursor/ahos-cleanup-alignment-4bde` @ `59818e4`  
**Prerequisite:** Owner review/merge of PR #19, then approve a phase below.  
**Law:** Documentation describes reality. After this backlog is accepted, implement — do not spawn more status docs.

Honest completeness (harsh, evidence-based):

| Metric | Estimate |
|--------|---------:|
| Core engineering (code/tests/docs coherence) | ~62% |
| Mission-complete (live integrations + soak + calibration data) | ~27% |

---

## P0 — Blocking product gaps (mission cannot succeed without these)

| ID | Goal | Why | Dependencies | Modules | Acceptance | Tests | Evidence | Risk | Priority |
|----|------|-----|--------------|---------|------------|-------|----------|------|----------|
| P0-1 | Live discovery SUCCESS on operator host | Empty local stores ⇒ no real candidates | OA-3 egress | `architecture/runtime --probe-providers`, providers | ≥1 provider SUCCESS + tokens>0 artifact | existing probe tests | committed probe JSON | Network/filter | P0 |
| P0-2 | Accrue `local` observations + outcomes | Without evidence, scores cannot be calibrated | P0-1, OA-4 | daemon `--observation-cycle`, `discovery/outcomes.py` | Non-zero `local` ledger rows | ledger tests | sqlite row counts + report | Disk/time | P0 |
| P0-3 | Wire narrative intel into collector path | Narrative module tested but feed-through not wired (R-69) | P0-1 | `architecture/intel/news.py`, collector/orchestrator | News evidence appears on scored candidates when feeds up | integration test | cycle snapshot with narrative fields or honest UNKNOWN | Scope creep | P0 |

## P1 — Core intelligence

| ID | Goal | Why | Dependencies | Modules | Acceptance | Tests | Evidence | Risk | Priority |
|----|------|-----|--------------|---------|------------|-------|----------|------|----------|
| P1-1 | Deepen market-structure beyond liq/vol floors | Current structure analysis is thin | P0-1 | `architecture/risk`, scoring | Documented features + tests; UNKNOWN when absent | unit | feature schema | Overfit | P1 |
| P1-2 | Tokenomics analyzer (unlock/vesting where evidence exists) | Only FDV/supply fields today | providers | new `architecture/intel/tokenomics` or extend contracts | Explicit UNKNOWN without fabrication | unit | report samples | Data scarcity | P1 |
| P1-3 | Catalyst detector (events/listings) beyond news keywords | Currently NOT_IMPLEMENTED | narrative wiring | intel/catalyst | Catalogued catalysts with provenance | unit | fixtures | False positives | P1 |
| P1-4 | Holder/smart-money live path where free RPC allows | Whale suite offline; free SOL holders blocked | egress | `discovery/holders.py`, whales | Honest BLOCKED vs SUCCESS | provider tests | probe artifact | RPC limits | P1 |
| P1-5 | Unify dual-stack scoring contracts (TS↔Python) without moving One-Brain roots | Two brains documented; drift risk | careful design | `scoring.ts`, `architecture/scoring` | Shared field dictionary + parity tests | contract tests | parity report | Large refactor | P1 |

## P2 — Learning / calibration

| ID | Goal | Why | Dependencies | Modules | Acceptance | Tests | Evidence | Risk | Priority |
|----|------|-----|--------------|---------|------------|-------|----------|------|----------|
| P2-1 | First real calibration report on `local` pairs | Harness ready, 0 pairs | P0-2 | `architecture/learning/calibration.py` | Report not only INSUFFICIENT_DATA | existing | `reports/calibration_*.json` | Bad data | P2 |
| P2-2 | Governed weight-change proposals only | Evolution must not silent-edit Lane A | P2-1 | `architecture/evolution/`, improvement_proposal | Proposal→review→human gate | evolution tests | proposal artifact | Autonomy abuse | P2 |

## P3 — UX / Telegram / Web

| ID | Goal | Why | Dependencies | Modules | Acceptance | Tests | Evidence | Risk | Priority |
|----|------|-----|--------------|---------|------------|-------|----------|------|----------|
| P3-1 | Live Telegram via gateway | Unit≠live | OA-1/OA-2 | `telegram_ai/`, `/api/chat` | `source=conversation_gateway` transcript | live checklist | archived chat log | Token leak | P3 |
| P3-2 | Persian UX polish on gateway replies | Intent grammar exists; gateway path is product UX | P3-1 | `chat.ts`, persian helpers | Operator script pass | UI/manual | screenshots/log | Scope | P3 |
| P3-3 | Command Center honesty pass | No fake live cards when providers down | providers | `CommandCenter.tsx`, engine | UNKNOWN/BLOCKED visible | typecheck + manual | UI notes | Cosmetic | P3 |

## P4 — Operations

| ID | Goal | Why | Dependencies | Modules | Acceptance | Tests | Evidence | Risk | Priority |
|----|------|-----|--------------|---------|------------|-------|----------|------|----------|
| P4-1 | Execute 168h soak | Reliability unproven | OA-5 | soak protocol/scripts | 7 days snapshots | soak tests | snapshot series | Laptop sleep | P4 |
| P4-2 | 7-night backups | M-GAP-010 | OA-6 | `sqlite_backup_restore.py` | series_complete | backup tests | nightly JSON | Ops discipline | P4 |
| P4-3 | Optional CI workflow | PR gates | OA-7 workflows permission | template→`.github/workflows` | green CI | CI | Actions run | App perms | P4 |

## P5 — Advanced intelligence

| ID | Goal | Why | Dependencies | Modules | Acceptance | Tests | Evidence | Risk | Priority |
|----|------|-----|--------------|---------|------------|-------|----------|------|----------|
| P5-1 | AG-25 GitHub intelligence (if still wanted) | Registry PLANNED / NOT_IMPLEMENTED | design approval | agent_registry, oss_pipeline | implemented flags true + tests | unit | harvest fixture | Rate limits | P5 |
| P5-2 | Development-activity collector | Mission lists it; absent | P5-1 or separate | new collector | UNKNOWN without fake stars | unit | samples | Noise | P5 |
| P5-3 | AHOS runtime AI role orchestration (≠ Cursor routing) | Free-first router exists; not multi-role product orchestration | council | `architecture/ai/` | Role contracts + advisory-only | council tests | envelopes | Hallucination | P5 |

---

## Explicitly out of next-phase scope unless doctrine changes

- Real-money trading / wallet signing  
- Cursor automatic multi-model routing as AHOS feature  
- Claiming PRODUCTION_READY without OA-3…OA-5 artifacts  
- Social scrape of X/IG/TikTok (OUT_OF_POLICY)

## Recommended sequence after PR #19 merge

1. Owner OA-3 + OA-4 (live evidence)  
2. Engineering P0-3 (narrative wiring)  
3. P1 intelligence depth  
4. P2 calibration on real pairs  
5. P3 Telegram live  
6. P4 soak/backups/CI  
7. P5 only with explicit approval

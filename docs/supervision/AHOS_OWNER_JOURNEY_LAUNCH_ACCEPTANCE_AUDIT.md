# AHOS Owner Journey + Launch Acceptance Audit

**Council:** Independent AHOS Oversight Council  
**Date:** 2026-09-12  
**Type:** Audit / Governance / Acceptance Design only — **no product implementation**  
**Authority sources:** `OWNER_VISION_REGISTRY.md`, `AHOS_VISION_ALIGNMENT_AUDIT.md`, `AHOS_PROJECT_TRUTH_MODEL.md`, `docs/FINAL_TRUTH_AUDIT.md`, `AHOS_GAP_REGISTER.md`, `docs/CANONICAL_IMPLEMENTATION_MATRIX.md`, `docs/OPERATOR_VALIDATION_PROTOCOL.md`, `reports/PRE_SOAK_STATUS.txt`, `reports/calibration_20260827T202725Z.json`, runtime code review (read-only)

---

## GOVERNANCE LOCKS (ACTIVE — recorded at audit start)

| Lock | Status |
|------|--------|
| Lane A | **FROZEN** |
| PR #103 | **BLOCKED** |
| Slice 8 | **BLOCKED** |
| New W4 slice | **NOT AUTHORIZED** |
| New merge | **NOT AUTHORIZED** |
| New identity authority | **FORBIDDEN** |
| Historical mapping | **FORBIDDEN** |
| Readiness inflation | **FORBIDDEN** (no PASS from code/test alone) |
| IMPLEMENTED ≠ VALIDATED | **ENFORCED** |
| INTEGRATION_READY ≠ LAUNCH_READY | **ENFORCED** |
| Build agent new implementation | **NOT AUTHORIZED** during this audit |
| Council STATUS | **MONITOR** |
| Build agent STATUS | **FIX_BEFORE_CONTINUE** (unchanged; no new execution directive) |

---

## 1. EXECUTIVE VERDICT

### Primary question

> If AHOS were placed in the Owner's hands today, can the Owner complete a real mission from Opportunity discovery through decision, alert, paper position, and learning/calibration **end-to-end**?

### Answer: **NO**

**Classification:** `NOT READY` (journey operational) · `INTEGRATION_READY` (agent-host engineering only) · **`LAUNCH_READY` = FORBIDDEN CLAIM**

### Why NO (evidence-backed)

| Breakpoint | Journey | Evidence |
|------------|---------|----------|
| Operator machine not proven | J0 | No `reports/operator_validation_report_windows_*.json`; `PRE_SOAK_STATUS.txt`: G2/G3/G5/G10 FAIL/NOT_VERIFIED |
| Discovery→decision loop not operational on owner host | J1→J6 | G5 `local_predictions > 0` FAIL on current host |
| Identity knowledge split | J2 | W2 (#95) not on `main`; W4 stack unmerged; candidate ≠ trusted identity law enforced in tests only |
| Evidence dossier not operator-visible | J4 | `architecture/knowledge/dossier.py` on main; W2 graph on branch; Command Center not wired to dossier |
| Chat/Telegram not live | J7 | M-GAP-009 OPEN; `telegram_test_log.json` SIMULATED; gateway requires `AHOS_GATEWAY_URL` + dev server |
| Alerts not operationally proven | J8 | Unit tests PASS; no live Telegram E2E artifact; web banner depends on engine cycle + canonical BUY |
| Paper E2E not owner-validated | J9 | Three ledger surfaces; canonical gate tested; Windows soak not run |
| Learning loop empty | J12 | `calibration_20260827T202725Z.json`: 352 predictions, **0 eligible pairs**, `INSUFFICIENT_DATA` |
| 168h soak not executed | J10/J12 | M-GAP-003 OPEN |

### Smallest honest path to YES

Owner Windows G1–G10 → daemon accrual → W2 on main + W1.3 → P1 live (chat/TG/alerts) with E2E artifacts → T+72h labels → calibration ≥ minimal N → 168h soak → Mission A/B/C re-run on owner laptop without engineering intervention.

**No new build directive issued by this audit.** Gaps registered as REQUIRED CHANGE only.

---

## 2. CANONICAL OWNER JOURNEY J0–J12

### J0 — START / SYSTEM STATE

Owner enters AHOS and must understand: system status, data freshness, provider health, security state, market state, unknown/stale conditions, paper-only mode, last intelligence update.

**Canonical surfaces:** Command Center dashboard tab (`CommandCenter.tsx`), `/api/metrics`, Python `HealthSnapshotEngine` (`architecture/runtime/observability_snapshot.py`), provider census, canonical read model staleness banner.

**Law:** If canonical read model is `UNAVAILABLE` or `STALE`, web must not mint independent BUY/WATCH.

---

### J1 — DISCOVER

AHOS finds opportunity candidates from multi-source discovery.

**Canonical path:** Lane A frozen `discovery/collect.py` + Lane B `architecture/collector/engine.py`, `architecture/providers/*`, `architecture/pipeline/orchestrator.py`.

**Signals:** DexScreener, Gecko, pump.fun, CMC, narrative intel (`architecture/intel/news.py`), market structure, on-chain observations.

---

### J2 — IDENTIFY

Token identity must become canonical before trust.

**Canonical path:** `architecture/identity/resolution.py`, `gates.py`, `validate.py`; knowledge `architecture/knowledge/dossier.py` (W1 main); `evidence_graph.py` (W2 branch #95).

**Law:** **Candidate identity ≠ trusted identity.** Downstream decision must not treat candidate-only identifiers as authoritative (`test_canonical_identity.py`, dossier tests).

---

### J3 — VERIFY SECURITY

Security overlay must veto before opportunity.

**Canonical path:** `architecture/security/gate.py` → frozen `discovery/security_gate.py`; GoPlus/RugCheck adapters; `overlay_query.py`.

**Law:** Attractive score cannot bypass critical security veto (`test_canonical_security_gate.py`).

---

### J4 — BUILD EVIDENCE

Evidence dossier with provenance, timestamps, polarity, uncertainty, contradictions, entity binding.

**Canonical path:** `architecture/knowledge/dossier.py`, `architecture/intelligence/evidence.py`, `discovery/observations.py` (sha256 provenance), W2 evidence graph (branch).

**Law:** Evidence must attach to correct canonical subject.

---

### J5 — SCORE

Opportunity score with bands, missing-evidence handling, security veto, identity gate, explainability.

**Canonical path:** `architecture/scoring/engine.py` (authoritative). Display: `scoring.ts` (non-authoritative unless `canonicalBackend` injected).

**Law:** Score ≠ decision. High score with `INSUFFICIENT_EVIDENCE` is valid (`canonical_decision_read_model.json` pattern).

---

### J6 — DECIDE

Deterministic, auditable outcome: Opportunity / Watch / Weak / Blocked / Unknown / Insufficient Evidence.

**Canonical path:** `architecture/decision/authority.py` (`CanonicalDecisionAuthority`) → `reports/canonical_decision_read_model.json` → `canonical_read_model.ts` → UI/API.

**Chain:** Score → Decision → Evidence → Reason (reasonsFa/risksFa/unknownsFa in read model).

---

### J7 — CHAT

Owner asks about opportunities in Persian (and eventually English). Must be evidence-grounded, honest about unknown/stale, **not a second brain**.

**Canonical path:** `conversation_gateway.ts` → `app/api/chat/route.ts`; Telegram `telegram_ai/service.py` → same gateway URL (W57).

**Law:** Without `AHOS_GATEWAY_URL` → `EMERGENCY_FALLBACK_ONLY` (no independent scoring).

---

### J8 — ALERT

When canonical gates pass: web loud alert + Telegram Sun Sniper must show same opportunity.

**Gates:** `canonicalOutcome === BUY` + overlay `securityStatus === PASS` + score floor + cooldown + freshness re-check.

**Paths:** `architecture/alerts/engine.py`, `telegram_ai/pump_alert.py`, `alerts.ts`, `alert_banner.ts`, shared `reports/pump_alert_state.json`.

---

### J9 — PAPER POSITION

Owner tracks opportunity in paper mode — not live execution.

**Paths:** Lane A `paper_trading/engine_v3.py` (frozen); Lane B `architecture/positions/manager.py`; web `app/api/paper/route.ts`; Telegram `telegram_ai/positions.py`.

**Law:** `paperAllowedFromCanonical` must be true (Python BUY gate).

---

### J10 — MONITOR

Post-decision monitoring: price/state, evidence changes, security changes, thesis invalidation, alerts, stale state.

**Paths:** `paper_trading/position_monitor.py`, `discovery/observe_active.py`, `architecture/runtime/observation_loop.py`, Command Center watchlist tab.

---

### J11 — OUTCOME

Record success / failure / invalidated / expired / unresolved — no fabricated outcomes.

**Paths:** `discovery/outcomes.py`, `discovery/materialize.py`, `architecture/learning/prediction_lifecycle.py`.

---

### J12 — LEARN / CALIBRATE

Prediction → canonical outcome → calibration with no-peeking, valid identity join, minimum N.

**Paths:** `architecture/learning/calibration.py`, `score_ledger.py`; W4 identity join (branch, blocked).

**Law:** Learning without valid identity join is forbidden.

---

## 3. OWNER JOURNEY READINESS MATRIX

Legend: ✅ = evidenced · ⚠️ = partial/qualified · ❌ = not evidenced · **?** = UNKNOWN

| Journey | Designed | Implemented | Tested | Validated | Integrated | Operational | Launch Ready | Evidence |
|---------|:--------:|:-----------:|:------:|:---------:|:----------:|:-----------:|:------------:|----------|
| **J0** System State | ✅ | ✅ | ✅ E2 | ❌ | ⚠️ | ❌ | ❌ | `PRE_SOAK_STATUS.txt` G2/G3/G10 not verified; agent-host only |
| **J1** Discover | ✅ | ✅ | ✅ E2 | ⚠️ | ⚠️ | ❌ | ❌ | Agent-host LIVE 2026-08-27; Windows re-probe UNKNOWN (M-GAP-007) |
| **J2** Identify | ✅ | ✅ | ✅ E2 | ❌ | ❌ | ❌ | ❌ | W2 off main; W4 unmerged; unit tests only |
| **J3** Security | ✅ | ✅ | ✅ E2 | ⚠️ | ⚠️ | ❌ | ❌ | Overlay tests; live probe not owner-verified |
| **J4** Evidence | ✅ | ✅ | ✅ E2 | ❌ | ❌ | ❌ | ❌ | Dossier not UI-wired; W2 branch split |
| **J5** Score | ✅ | ✅ | ✅ E2 | ❌ | ⚠️ | ❌ | ❌ | Dual-stack; no live calibration validation |
| **J6** Decide | ✅ | ✅ | ✅ E2 | ⚠️ | ⚠️ | ❌ | ❌ | Read model fixture exists; G5 FAIL |
| **J7** Chat | ✅ | ✅ | ✅ E2 | ❌ | ⚠️ | ❌ | ❌ | M-GAP-009; simulated telegram log |
| **J8** Alert | ✅ | ✅ | ✅ E2 | ❌ | ⚠️ | ❌ | ❌ | No live TG E2E; banner unit-tested |
| **J9** Paper | ✅ | ✅ | ✅ E2 | ❌ | ⚠️ | ❌ | ❌ | Three ledgers; dryrun simulated |
| **J10** Monitor | ✅ | ✅ | ✅ E2 | ❌ | ⚠️ | ❌ | ❌ | M-GAP-003 soak not run |
| **J11** Outcome | ✅ | ✅ | ✅ E2 | ❌ | ⚠️ | ❌ | ❌ | No production outcome accrual evidence |
| **J12** Learn/Calibrate | ✅ | ✅ | ✅ E2 | ❌ | ❌ | ❌ | ❌ | 0 eligible pairs M-GAP-008 |

**Rule applied:** Code + unit tests = max **Implemented + Tested (E2)**. None of J0–J12 reach **Operational (E4+)** on owner Windows today.

---

## 4. MISSION ACCEPTANCE MATRIX

| Mission | Description | Expected | Actual | Manual Intervention | Verdict |
|---------|-------------|----------|--------|---------------------|---------|
| **A — Clean Opportunity** | Discovery → Identity → Security → Evidence → Score → Decision → Chat → Alert → Paper | Full E2E without dev help | Infrastructure exists; owner path not proven | **ENGINEERING + OPERATOR** (G1–G10, dev server, env, Postgres) | **NOT ACCEPTED** |
| **B — Dangerous Token** | Security veto blocks positive alert; chat explains veto | NO positive opportunity alert | Veto logic **tested** (E2); live path unproven | **CONFIG + OPERATOR** | **NOT VALIDATED** (E2 only) |
| **C — Identity Attack** | No unauthorized fusion; UNKNOWN/UNMATCHED/REJECTED | Fail-closed identity | `test_canonical_identity.py`, dossier spoof tests (E2); W1.3 hardening open | **ENGINEERING** for W1.3 | **NOT VALIDATED** operationally |
| **D — Insufficient Evidence** | No fake confidence | INSUFFICIENT_EVIDENCE / UNKNOWN | Authority tests + read model pattern (E2) | **NONE** for logic | **TESTED not VALIDATED** live |
| **E — Full Learning Loop** | Prediction → outcome → calibration, no peeking | Measurable calibration | Harness COMPLETE; **0 pairs** (`calibration_20260827T202725Z.json`) | **OPERATOR** (T+72h accrual) | **NOT VALIDATED** |

### Mission detail — what would be required for ACCEPTED

**Mission A minimum evidence:** Windows `operator_validation_report_windows_*.json` G1–G10 PASS + archived chat transcript + archived alert (web screenshot + TG message) + paper position JSON with canonical identity + decision snapshot — **none exist in repo**.

---

## 5. ONE-BRAIN AUDIT

### Intended chain

```
Discovery → Identity → Evidence → Security → Scoring → Decision
    → Chat → Alert → Paper Trading → Outcome → Calibration
```

### Authoritative implementation (per `AGENTS.md`, `PHASE3_CANONICAL_DECISION.md`)

| Stage | Authoritative | Edge (presentation/advisory) |
|-------|---------------|------------------------------|
| Discovery (Lane B) | Python collector + frozen Lane A | TS `engine.ts` display cycle |
| Identity | Python `architecture/identity/` | TS `tokenKey` (Phase 1 binding gap) |
| Evidence | Python dossier + observations | TS opportunity cards (overlay) |
| Security | Python overlay + frozen gate | TS `canonical_security.ts` (display) |
| Scoring | Python `architecture/scoring/` | **`scoring.ts` — ONE-BRAIN RISK** |
| Decision | Python `CanonicalDecisionAuthority` | TS blocked without `canonicalBackend` |
| Chat | `conversation_gateway.ts` | LLM advisory inside gateway only |
| Alert | Python `AlertEngine` + TS gated `alerts.ts` | Shared `pump_alert_state.json` |
| Paper | Lane A frozen + Lane B manager | TS `addPaper`, TG `positions.py` — **THREE-LEDGER RISK** |
| Outcome | Frozen `discovery/outcomes.py` | — |
| Calibration | Python `score_ledger` + `calibration.py` | — |

### ONE-BRAIN RISK register

| ID | Risk | Severity | Evidence | Mitigation in repo |
|----|------|----------|----------|-------------------|
| OBR-1 | Python vs TS scoring numeric dual-stack | **HIGH** | `scoring.ts` vs `architecture/scoring/engine.py` | Phase 3: no positive TS decision without `canonicalBackend` |
| OBR-2 | Three paper ledgers | **MEDIUM** | `paper_trading/`, `engine.ts`, `telegram_ai/positions.py` | `paperAllowedFromCanonical`; API 403 `CANONICAL_PAPER_DENIED` |
| OBR-3 | W2 evidence graph off main | **HIGH** | PR #95 not merged | Knowledge layer split-brain |
| OBR-4 | TS display rankScore labeled non-canonical | **LOW** | `CommandCenter.tsx` "غیرکانونیکال" | Honest labeling — UX gap if owner ignores label |
| OBR-5 | Council parallel heuristics | **LOW** | `council.ts` vs `architecture/council.py` | Advisory only |
| OBR-6 | Demo 3D trees with seed engines | **LOW** (confusion) | `advanced-3d-*`, `سایت درخت*` | Excluded from canonical compile |
| OBR-7 | Provider health dual writers | **MEDIUM** | Python snapshot vs TS `provider_health.ts` | Both shown; not single writer |

**Verdict:** One Brain **architecturally intended and partially enforced** — not **operationally proven** end-to-end on owner machine.

---

## 6. OPERATOR EXPERIENCE AUDIT

| Owner question | Visible in product? | Evidence | Gap |
|----------------|--------------------|---------|----|
| Why this opportunity? | ⚠️ Partial | First `reasonsFa` on card; modal "چرا؟" | Full dossier not linked — **OPERATOR UX GAP** |
| What is the evidence? | ⚠️ Partial | reasons/risks lines | No evidence graph UI — **OPERATOR UX GAP** |
| What is the risk? | ⚠️ Partial | `risksFa`, `securityState` pill | Security veto reason not always expanded |
| What is unknown? | ✅ | `unknownsFa` joined (amber) | — |
| Where does score come from? | ⚠️ Honest | `rankScore` labeled **غیرکانونیکال** | Owner may confuse with canonical score |
| What triggered alert? | ❌ | Logic in code/tests only | No alert reason panel in CC — **OPERATOR UX GAP** |
| What caused block? | ⚠️ Partial | REJECT/HONEYPOT pills | No unified "blocked because" narrative |
| When to wait? | ⚠️ Partial | STALE/UNAVAILABLE banners | No explicit "wait for X" guidance |
| What changed? | ❌ | Diff not in CC | **OPERATOR UX GAP** |

**Persian-first:** Command Center RTL/FA ✅. Telegram intent FA ✅. Alert Python path FA ✅; TS alert template EN header — **minor consistency gap**.

---

## 7. SUN SNIPER EXPERIENCE AUDIT

### Owner expectation

> "یک فرصت مهم پیدا شد" — one-glance: token, chain, contract, score, security, confidence, why now, why this token, risks, unknowns, timestamp, evidence, actions (Open Dossier / Ask AI / Paper Track).

### Reality today

| Element | Web | Telegram | Status |
|---------|-----|----------|--------|
| Token / chain / contract | ⚠️ CC card | ✅ `format_pump_alert` | PARTIAL |
| Opportunity score | ⚠️ display rank (non-canonical label) | ✅ score field | SPLIT presentation |
| Security state | ✅ pill | ⚠️ in TS alert only | PARTIAL |
| Confidence / evidence quality | ⚠️ confidence pill | ⚠️ TS path only | PARTIAL |
| Why now / why this token | ⚠️ first reason line | ✅ evidence section | PARTIAL |
| Main risks | ⚠️ first risk line | ✅ risks section | PARTIAL |
| Unknowns | ✅ on card | ❌ Python alert omits unknowns | **P1 PRODUCT GAP** |
| Timestamp | ⚠️ implicit | ✅ in alert | PARTIAL |
| Open Dossier | ❌ | ❌ | **P1 PRODUCT GAP** |
| Ask AI | ✅ chat column | ✅ gateway chat | NOT LIVE (M-GAP-009) |
| Paper Track | ✅ button (gated) | ⚠️ positions flow | NOT LIVE E2E |

**Verdict:** Sun Sniper is **backend-designed + unit-tested**, not **product-shaped** for owner one-glance mission. **P1 PRODUCT GAP** confirmed.

---

## 8. WEB ↔ TELEGRAM CONSISTENCY AUDIT

| Field | Shared authoritative source? | Split-brain? |
|-------|---------------------------|--------------|
| Canonical identity | Python read model | ⚠️ W2 off main increases drift risk |
| Score | Python canonical; display may differ | **YES** — display `rankScore` vs canonical score |
| Decision | `canonical_decision_read_model.json` | **NO** — same file for web/TG/chat |
| Security state | Python overlay | **NO** — gates aligned in tests |
| Evidence (reasons/risks) | Read model | ⚠️ TG Python alert omits unknowns vs web card |
| Alert firing | `pump_alert_state.json` + live re-check | **NO** — shared state |
| Chat answers | `conversation_gateway.ts` | **NO** — single gateway |

**SPLIT-BRAIN GAP (confirmed):** Display scoring (`scoring.ts` / `rankScore`) can diverge from canonical Python score — mitigated by labeling, not by elimination.

**SPLIT-BRAIN GAP (minor):** Telegram Python vs TS alert templates differ (FA vs EN header; unknowns section).

---

## 9. MANUAL INTERVENTION MATRIX

| Mission / Journey | Intervention level | Details |
|-------------------|-------------------|---------|
| J0 Start | **ENGINEERING + OPERATOR** | Clone, venv, npm, Postgres, `.env`, start dev server |
| J1 Discover | **OPERATOR** | Run daemon/single-cycle; provider egress on Windows |
| J2 Identify | **ENGINEERING** (W2 merge) | Branch split today |
| J3 Security | **CONFIG** | API keys; live probe |
| J4 Evidence | **ENGINEERING** | UI wiring not done |
| J5–J6 Score/Decide | **OPERATOR** | Daemon must produce predictions (G5) |
| J7 Chat | **CONFIG + OPERATOR** | `AHOS_GATEWAY_URL`, token, G2 |
| J8 Alert | **CONFIG + OPERATOR** | Telegram token rotation S-01, allowlist |
| J9 Paper | **OPERATOR** | Requires canonical BUY from running system |
| J10 Monitor | **OPERATOR** | 168h soak — cannot skip |
| J11 Outcome | **OPERATOR** | Wait T+72h+ real time |
| J12 Calibrate | **OPERATOR** | Accrual + run `calibration_report.py` |
| Mission A full | **ENGINEERING INTERVENTION** | Cannot run without dev setup today |
| Mission B–D logic | **NONE** (in tests) | Live validation missing |
| Mission E | **IMPOSSIBLE** today | 0 pairs |

**Launch rule violated:** Owner cannot complete Mission A **without developer intervention** → **NOT OPERATIONAL**.

---

## 10. EVIDENCE QUALITY MATRIX

| Launch claim | Level | Reality |
|--------------|-------|---------|
| "AHOS discovers tokens" | E2 | Unit tests + agent-host LIVE; Windows UNKNOWN |
| "Security veto works" | E2 | 41+ gate tests; no live E2E artifact |
| "One Brain enforced" | E2–E3 | Architecture tests + API gates; not soak-proven |
| "Telegram Sun Sniper works" | E1–E2 | Code + mocks; M-GAP-009 OPEN |
| "Web alerts work" | E2 | `test_alerts_web_banner.py`; no owner screenshot artifact |
| "Chat is evidence-grounded" | E2 | Gateway tests; no live transcript |
| "Paper trading works" | E2 | Simulated dryrun; not owner Windows |
| "Calibration validated" | E1 | Harness exists; **0 pairs** — claim FORBIDDEN |
| "168h soak passed" | E0 | **FORBIDDEN** — M-GAP-003 |
| "OPERATOR_READY" | E0 | **FORBIDDEN** — no Windows report |
| "LAUNCH_READY" | E0 | **FORBIDDEN** |

**Rule:** No launch claim accepted at E0–E2 alone.

---

## 11. FALSE GREEN FINDINGS

| ID | CLAIM → EVIDENCE → REALITY | Severity |
|----|---------------------------|----------|
| FG-1 | "2128 tests pass" → pytest agent-host → Windows G5 FAIL, no soak | **HIGH** |
| FG-2 | "Calibration report exists" → `calibration_*.json` → `eligible_pairs: 0`, `INSUFFICIENT_DATA` | **HIGH** |
| FG-3 | "Telegram tested" → `telegram_test_log.json` → **SIMULATED** environment | **HIGH** |
| FG-4 | "INTEGRATION_READY" → matrix → interpreted as launch-ready | **HIGH** (classification drift) |
| FG-5 | "Green dashboard" → CC health dims → canonical `UNAVAILABLE` fails closed but provider census may look populated from fixtures | **MEDIUM** |
| FG-6 | "Display rankScore" → opportunity card → labeled non-canonical but visually prominent | **MEDIUM** |
| FG-7 | "W1 dossier complete" → main branch → not UI-wired; W2 graph off main | **MEDIUM** |
| FG-8 | "Agent-host gates PASS" → `operator_validation_report_agent_host.json` → **not** Windows evidence | **HIGH** |
| FG-9 | "Score 100 + INSUFFICIENT_EVIDENCE" → read model sample → correct law but confusing UX if shown wrong | **LOW** |
| FG-10 | "Demo 3D site" → orphan trees → could be mistaken for product | **LOW** |

---

## 12. LAUNCH BLOCKERS L0–L3

### L0 — Absolute Blocker (launch forbidden)

| ID | Domain | Gap | Evidence |
|----|--------|-----|----------|
| L0-1 | Windows | No owner G1–G10 PASS artifact | `FINAL_TRUTH_AUDIT.md`, `PRE_SOAK_STATUS.txt` |
| L0-2 | Soak | M-GAP-003 — no 168h evidence | Gap register |
| L0-3 | One Brain (operational) | Journey not E2E on owner machine | Mission A NOT ACCEPTED |
| L0-4 | Security | S-01 exposed token — rotate before live | Gap register |
| L0-5 | Identity | Trusted canonical identity not on main path (W2) | PR #95 open |

### L1 — Critical (must resolve before launch)

| ID | Domain | Gap |
|----|--------|-----|
| L1-1 | Telegram | M-GAP-009 live E2E |
| L1-2 | Chat | Gateway live + quality artifact |
| L1-3 | Alerts | Web + TG E2E with canonical gates |
| L1-4 | Calibration | M-GAP-008 ≥ minimal real pairs |
| L1-5 | Identity | W1.3 spoof hardening |
| L1-6 | UX | Sun Sniper one-glance + dossier link |
| L1-7 | Provider | Windows live probe M-GAP-007 residual |

### L2 — Important (ideal pre-launch; can follow shortly after)

| ID | Domain | Gap |
|----|--------|-----|
| L2-1 | UX | Daily report, performance charts |
| L2-2 | Evidence | Evidence graph in UI (post-W2) |
| L2-3 | English | Full EN mode |
| L2-4 | Backup | M-GAP-010 seven nights |
| L2-5 | Selective W4 | Human-approved slices for contract display |

### L3 — Enhancement

Environment Engine, 3D/audio, council personas, tree viz, n8n runtime, CT signals, AG-25

### R — Research / Future

Domain-AGI/ACI world model, agent creation, multi-market, HFT, live execution L6+

---

## 13. SYSTEM READY vs INTEGRATION READY vs OPERATOR READY vs LAUNCH READY

| Classification | Definition | AHOS today | Evidence |
|----------------|------------|------------|----------|
| **System Ready** | Core modules import, tests pass | ⚠️ **YES on agent-host** | pytest; not re-verified at HEAD in this audit |
| **Integration Ready** | Components wired in dev/integration host | ✅ **YES** | `FINAL_TRUTH_AUDIT.md` |
| **Operator Ready** | Owner can run G1–G11 on Windows without dev | ❌ **NO** | No Windows artifact |
| **Launch Ready** | Missions A/B/C + soak + calibration + no L0 | ❌ **NO** | This audit |

**Forbidden equivalences:**
- INTEGRATION_READY ≠ OPERATOR_READY
- OPERATOR_READY ≠ LAUNCH_READY
- TESTED ≠ VALIDATED
- IMPLEMENTED ≠ OPERATIONAL

**Gate-based readiness label for this audit:** `NOT READY`

---

## 14. VISION → JOURNEY COVERAGE

| Vision area (owner) | Journey stages | Covered? |
|---------------------|------------------|----------|
| Evidence-first intelligence | J4, J5, J6 | ⚠️ Backend yes; UX partial |
| Security veto | J3 | ⚠️ Tested not live-proven |
| Persian-first product | J7, J8, UX | ⚠️ UI FA; live TG no |
| Sun Sniper experience | J8, §7 | ❌ P1 PRODUCT GAP |
| Paper-only trading | J9, J10 | ⚠️ Gated; not owner E2E |
| Learning/calibration | J11, J12 | ❌ 0 pairs |
| Contract truth P0 | J2 | ⚠️ In progress (W2/W4) |
| Windows/local/$0 | J0, ops | ❌ Not owner-verified |
| Domain-AGI/ACI | Future | ✅ Correctly separated (R) |
| Environment Engine | — | ❌ Not in journey yet (L3) |

---

## 15. MISSING / LOST JOURNEYS

| Journey / experience | Status | Notes |
|---------------------|--------|-------|
| **Open Dossier** from alert/card | **MISSING** | No UI route to sealed dossier |
| **Daily Intelligence Report** | **LOST** (Master Vision) | Not in CC |
| **"What changed since last visit"** | **MISSING** | No diff journey |
| **Alert → explain why loud** | **PARTIAL** | Gates in code; not owner-visible |
| **Position → outcome → lesson** | **PARTIAL** | Backend only; CC "تکامل و درس" empty until horizons |
| **English full journey** | **NOT STARTED** | Owner P2 |
| **Immersive / Environment journey** | **NOT STARTED** | Owner P2 — correctly out of launch |

---

## 16. OVER-BUILD / UNDER-BUILD

### UNDER-BUILD (vision/journey > product)

- End-to-end owner mission (Mission A) — **critical**
- Sun Sniper one-glance UX — **P1**
- Live Telegram + chat — **P1**
- Operational calibration — **P1**
- Windows operator proof — **P0**
- Dossier/evidence in operator UI — **P1**

### OVER-BUILD (implementation > journey need now)

- 7-slice W4 PR stack before W2 merge + P1 live
- P2–P5 cognitive research packs while journey not operational
- 5 orphan 3D demo trees (confusion risk)
- Dual TS scoring display layer (documented but still present)
- Volume of phase reports vs owner E2E artifacts

---

## 17. CRITICAL RISKS

| Risk | Trigger | Action |
|------|---------|--------|
| **Wrong contract in alert** | Identity not trusted on main | BLOCK launch; W2 + selective W4 |
| **Split-brain positive decision** | TS without canonicalBackend | Monitored; tests exist — re-verify at P1 |
| **Fake confidence** | Score without evidence | Law exists; UX may mislead on rankScore |
| **Secret leak** | S-01 token in history | ESCALATE_TO_HUMAN rotate |
| **Readiness inflation** | Agent claims LAUNCH_READY | Council BLOCK |
| **Soak interference** | Runtime changes during soak | Charter §39 BLOCK |
| **Calibration without identity join** | W4 merge without review | §20 BLOCK #103 |

**STOP / ESCALATE_TO_HUMAN conditions met:** Identity trust insufficient on main; operational evidence insufficient; S-01 open. **No new execution directive issued.**

---

## 18. AUDIT SELF-CRITIQUE

| Question | Assessment |
|----------|------------|
| Did journey miss vision? | ⚠️ Added "what changed" and dossier-open — owner P2 immersive correctly deferred |
| Too engineering-centric? | ⚠️ Yes — mitigated by §6–§7 UX audits; still backend-weighted |
| Launch criteria too harsh? | **NO** — Mission A/B/C bar is minimum for "owner can use it" |
| Prematurely deferred? | ⚠️ W4 slice 3 (Gecko boundary) may be L1 not L2 — human gate still required |
| Over-blocked? | ⚠️ Chat/alerts could reach OPERATOR_READY before full W4 — audit allows P1 after W2 |
| UX vs backend balance? | Improved vs prior audit; Sun Sniper gap now explicit P1 |
| Persian-first in acceptance? | ✅ FA surfaces checked; EN alert header gap noted |
| $0/Windows/local/Iran? | ✅ G1–G10 + provider probe in blockers |
| Future automation separated? | ✅ Paper-only + L6+ forbidden |

**Honesty gap:** pytest not re-run at HEAD in this audit; `AHOS_ISSUE_REGISTER.md` not fully read (~13k lines). Findings marked UNKNOWN where applicable.

---

## 19. FINAL LAUNCH ACCEPTANCE CONTRACT

AHOS is **`LAUNCH_READY`** only when **all** are evidenced at E4+ on owner Windows:

| # | Criterion | Today |
|---|-----------|-------|
| 1 | Identity trusted and canonical | ❌ W2 not main |
| 2 | Security veto operationally proven | ❌ E2 only |
| 3 | Evidence chain auditable end-to-end | ❌ UI gap |
| 4 | Score explainable to owner | ⚠️ Partial |
| 5 | Decision deterministic/traceable | ⚠️ E2; G5 FAIL |
| 6 | Chat same source of truth | ⚠️ Designed; not live |
| 7 | Web alert → authoritative decision | ⚠️ Tested not live |
| 8 | Telegram same decision | ❌ M-GAP-009 |
| 9 | Paper position E2E | ❌ |
| 10 | Outcome recordable | ⚠️ Infra only |
| 11 | Calibration valid measurement path | ❌ 0 pairs |
| 12 | Windows G1–G10 PASS | ❌ |
| 13 | 168h soak PASS | ❌ M-GAP-003 |
| 14 | No critical S/I issue | ❌ S-01 |
| 15 | Missions A, B, C without dev intervention | ❌ |

**Current contract status:** `NOT READY` — **0/15 operational proofs**

---

## 20. FINAL BEST PATH

**Format:** GATE → EVIDENCE → AUTHORIZATION → BUILD → VALIDATION

No PR-chain sequencing. Human authorization required between gates.

---

### GATE G-HUMAN-0 — Owner environment unlock

| Field | Value |
|-------|-------|
| **Prove** | Owner Windows laptop can run AHOS stack |
| **Evidence** | `reports/operator_validation_report_windows_*.json` G1–G10 PASS; S-01 token rotated |
| **Authorization** | **OWNER** (parallel, not build agent) |
| **Build** | None |
| **Validation** | Gate runner exit 0; no `NOT_VERIFIED` |
| **Unlocks** | G-OPS-1 |

---

### GATE G-OPS-1 — Operational accrual

| Field | Value |
|-------|-------|
| **Prove** | Discovery + predictions accrue locally |
| **Evidence** | G5 `local_predictions > 0`; G3 provider probe SUCCESS on Windows |
| **Authorization** | **OWNER** runs daemon |
| **Build** | None |
| **Validation** | `PRE_SOAK_STATUS.txt` pre_soak_entry_ok=True |
| **Unlocks** | G-BUILD-1 |

---

### GATE G-BUILD-1 — Identity trust foundation

| Field | Value |
|-------|-------|
| **Prove** | Candidate ≠ trusted identity; spoof resisted; W2 on main |
| **Evidence** | W1.3 test artifact; W2 (#95) merged; POST-FLIGHT report |
| **Authorization** | **COUNCIL** (existing Phase 1 directive — not expanded by this audit) |
| **Build** | W1.3 + W2 merge only — **NOT #103, NOT Slice 8** |
| **Validation** | pytest + freeze_lane_a at HEAD |
| **Unlocks** | G-BUILD-2 |

---

### GATE G-BUILD-2 — P1 owner product (Sun Sniper)

| Field | Value |
|-------|-------|
| **Prove** | Owner can chat, receive alert, see consistent decision |
| **Evidence** | E4 artifacts: chat transcript FA, web screenshot, TG message archive, alert payload JSON |
| **Authorization** | **COUNCIL** after G-BUILD-1 |
| **Build** | Gateway wiring, TG .env, loud alerts, contract display (no new authority) |
| **Validation** | Mission B + D on live system; no mock transport |
| **Unlocks** | G-BUILD-3 (selective W4) |

---

### GATE G-BUILD-3 — Selective identity/display hardening

| Field | Value |
|-------|-------|
| **Prove** | Contract shown in UI/TG matches canonical identity |
| **Evidence** | Per-slice POST-FLIGHT; human review per slice |
| **Authorization** | **OWNER + COUNCIL** per slice |
| **Build** | Approved W4 slices only (e.g. Gecko boundary) — **#103 remains BLOCKED until explicit unlock** |
| **Validation** | Mission C live |
| **Unlocks** | G-VALID-1 |

---

### GATE G-VALID-1 — Learning measurement

| Field | Value |
|-------|-------|
| **Prove** | Calibration joins real pairs with identity safety |
| **Evidence** | `calibration_report` with eligible_pairs ≥ minimum N; no peeking violations |
| **Authorization** | **OWNER** accrual T+72h+ |
| **Build** | None (harness exists) |
| **Validation** | Mission E ACCEPTED |
| **Unlocks** | G-VALID-2 |

---

### GATE G-VALID-2 — Reliability soak

| Field | Value |
|-------|-------|
| **Prove** | 168h continuous operation |
| **Evidence** | Committed soak snapshots per `AHOS_LOCAL_SOAK_PROTOCOL.md` |
| **Authorization** | **OWNER** |
| **Build** | None during soak (Charter §39) |
| **Validation** | M-GAP-003 CLOSED |
| **Unlocks** | G-LAUNCH-1 |

---

### GATE G-LAUNCH-1 — Launch acceptance

| Field | Value |
|-------|-------|
| **Prove** | Missions A, B, C without engineering intervention |
| **Evidence** | §19 contract 15/15 at E4+ |
| **Authorization** | **COUNCIL + OWNER** |
| **Build** | None |
| **Validation** | Re-run this audit; verdict YES |
| **Unlocks** | `LAUNCH_READY` classification (human declaration only) |

---

### Path summary (single line)

```
G-HUMAN-0 → G-OPS-1 → G-BUILD-1 → G-BUILD-2 → G-BUILD-3 → G-VALID-1 → G-VALID-2 → G-LAUNCH-1
```

**Not:** PR #97 → #98 → … → #103 → merge → hope.

---

## Council disposition after this audit

| Item | Status |
|------|--------|
| Council | **MONITOR** |
| Build agent | **FIX_BEFORE_CONTINUE** (unchanged) |
| New merge/slice | **NOT AUTHORIZED** |
| New build directive | **NOT ISSUED** — await human authorization |
| Required changes | Registered as GAPs in §12 — implementation deferred |

---

*Next: Human authorization to proceed with gated path. L2 operational delta. No Slice 8. No #103.*

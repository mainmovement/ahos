# AHOS Project Truth Model

**Maintained by:** Independent AHOS Oversight Council  
**Version:** 1.0 (initial master understanding)  
**Date:** 2026-09-12  
**Status:** Living document — updated each supervision cycle  
**Authority:** Supervisory model only. Does **not** override `docs/DOC_TRUTH_MAP.md`, `MASTER_DIRECTIVE_v1`, or `AGENTS.md`. Conflicts are reported, not silently resolved.

---

## Coverage ledger (honesty)

What this council has **systematically reviewed** vs **not yet fully reviewed**:

| Area | Review depth | Evidence |
|------|--------------|----------|
| Authority docs (`DOC_TRUTH_MAP`, `AGENTS.md`, `MISSION`, `MASTER_DIRECTIVE_v1`) | **READ** | Direct read + subagent |
| Gap/issue registers | **SAMPLED** | `AHOS_GAP_REGISTER.md` open gaps; `AHOS_ISSUE_REGISTER.md` **NOT fully read** (~13k lines) |
| `docs/` (146 md files) | **PARTIAL** | Truth map, final audit, charter, phase state, owner vision |
| `reports/` | **PARTIAL** | PHASE_STATE, agi_aci_evolution index, gap register |
| `architecture/` (169 py) | **STRUCTURAL** | Package map, key authority chain; ~90% module bodies unread |
| `tests/` (157 modules, ~2128 tests) | **CATEGORICAL** | Boundary test inventory; not every test body read |
| `app/` + CommandCenter | **PARTIAL** | Routes, auth gate, canonical read model; full UI unread |
| `telegram_ai/` | **PARTIAL** | service.py gateway-only pattern confirmed |
| Lane A (`discovery/`, `paper_trading/`) | **GOVERNANCE** | Freeze manifest, headers; bodies not fully read |
| PR history / branches | **CURRENT STATE** | Open PRs #95–#104; not full merge history |
| Duplicate web trees (5 dirs) | **INVENTORY** | Listed in tsconfig exclude; contents not audited |
| `n8n/workflows/` | **NOT READ** | Structural tests exist |
| `engine/`, `strategy_lab/` | **NOT READ** | Parallel research trees |
| Owner vision registry | **READ** | `OWNER_VISION_REGISTRY.md` |

**Council does not claim 100% line-by-line comprehension.** Claims below are evidence-backed from reviewed sources.

---

## 1. WHAT IS AHOS?

**Definition (operational):**  
Artificial Hybrid Opportunity Scoring System — a **paper-only**, evidence-first crypto **opportunity intelligence** platform. It discovers, verifies, scores, and explains early token opportunities using multi-source evidence. It is **not** a trading bot, pump oracle, or price predictor.

**Sources:** `docs/canonical/MISSION.md`, `AGENTS.md`, `ARCHITECTURE.md`

**Technical shape:**
- **Lane A (frozen):** `discovery/**`, `paper_trading/**` — scientific evidence surface (36-file SHA freeze)
- **Lane B (Python):** canonical identity, security overlay, decision authority, scoring, runtime daemon
- **Edges:** TypeScript Command Center (read model + gateway), Telegram (gateway client), n8n (automation)
- **Law:** `UNKNOWN > fabricated`; one Python decision brain; no second authority in TS/Telegram

**Classification today:** `INTEGRATION_READY` (agent-host) — `docs/FINAL_TRUTH_AUDIT.md`

---

## 2. WHY AHOS?

**Problem:** Crypto token discovery is noisy. Signals mix scams, honeypots, artificial pumps, rumors, and real opportunities. Humans cannot verify multi-source evidence fast enough.

**AHOS solves:** Systematic evidence collection → security veto → multi-dimensional scoring → explainable decision support → paper trade lifecycle → learning — in Persian-first UX.

**Core question AHOS answers:**  
*"Which early token has meaningful probability of a significant move — why, with what evidence, what invalidates it, what to watch next?"*  
(`docs/canonical/MISSION.md`)

---

## 3. WHO IS IT FOR?

| Actor | Role |
|-------|------|
| **Owner/operator** | Single-user; Windows laptop; $0-first; Iran-aware provider fallbacks |
| **End user (phase 1)** | Same person — no multi-tenant |
| **Cursor agents** | Engineering contractors — **not** runtime AI council |
| **AHOS runtime council** | In-product advisory routing (`architecture/ai/`) — evidence inputs only |

**Operating model:** Local Python daemon + local web UI + Telegram edge. No VPS required (owner constraint). Soak/calibration on operator laptop.

---

## 4. WHAT MUST IT BECOME? (Vision)

### Near-term product (owner P1)
- Conversational FA/EN chat (site + Telegram Sun Sniper)
- Loud opportunity alerts (canonical gates)
- Command Center as primary ops surface
- **Verified contract addresses** — never guessed
- Paper trading with explainable dossiers

### Medium-term
- Low-latency market data engine (not Wall-Street HFT)
- Environment Engine (geo/weather/time/theme/audio)
- Bilingual immersive 3D UX (incremental waves)
- 10-team AI council with meta-cognitive evaluation
- Calibration with real joined pairs

### Long-term (Charter north star)
Domain-General Cognitive Intelligence in mission domain:
```text
Perceive → Understand → Remember → Reason → Discover → Hypothesize
→ Experiment → Learn → Self-Critique → Controlled Improve
```
Multi-market adapters (crypto, gold, forex, equities) without rewriting cognitive core.

**Sources:** `OWNER_VISION_REGISTRY.md`, `AHOS_AGI_ACI_ARCHITECTURE_CHARTER_v1.0.md`

---

## 5. WHAT MUST IT NEVER BECOME? (Anti-goals)

| Anti-goal | Source |
|-----------|--------|
| Live trading without permission ladder L0–L7 + Risk Governor | Charter §25, AGENTS.md |
| General AGI claim | Charter §42 |
| Second brain in TS/Telegram | AGENTS.md, One Brain tests |
| Lane A casual modification | Charter §38, freeze |
| Readiness inflation (`PRODUCTION_READY`, etc.) | DOC_TRUTH_MAP §D |
| FOMO / guaranteed return language | AGENTS.md |
| Uncontrolled self-modification | Charter §41, PROJECT_STATE |
| Secrets in git | AGENTS.md, S-01 |
| Documentation as implementation proof | Charter §29 |
| Fabricated/stale data presented as live | STALE/UNAVAILABLE semantics |

---

## 6. CORE IDEAS (implemented + aspirational)

| Idea | State | Evidence |
|------|-------|----------|
| Evidence before decision | **IMPLEMENTED** | Pipeline, authority chain |
| One Brain | **IMPLEMENTED** | `test_one_brain_architecture.py` |
| Lane A freeze | **IMPLEMENTED** | 36-file SHA, tests |
| Security overlay veto | **IMPLEMENTED** | `architecture/security/gate.py` |
| AI council (advisory) | **IMPLEMENTED** | `architecture/council.py` — not majority vote |
| Paper trading lab | **IMPLEMENTED** | Lane A `paper_trading/` |
| Canonical read model (Py→TS) | **IMPLEMENTED** | `canonical_read_model.ts` |
| Token dossier (W1) | **IMPLEMENTED** | `architecture/knowledge/dossier.py` on main |
| Evidence graph (W2) | **IMPLEMENTED** branch-only | PR #95, not on main |
| Identity fusion (W4) | **DESIGNED→IMPLEMENTED** stacked PRs | #97–#103 |
| Human feedback signals (W3) | **IMPLEMENTED** branch | PR #96 |
| Cognitive memory P2 | **IMPLEMENTED** isolated | Not soak-wired |
| Cognitive loop P3 | **IMPLEMENTED** isolated | Not AGI |
| Benchmarks P4.1–4.3 | **TESTED** synthetic | Not intelligence score |
| Typed evidence P5 | **IMPLEMENTED** code on main; **governance MERGE=NO** in evolution index | PR #93 tension |
| World model | **DESIGNED only** | ACI-GAP-002 OPEN |
| Agent creation | **ASPIRATIONAL** | ACI-GAP-009 |
| Environment Engine | **DESIGNED** (owner) | Not in codebase |
| HFT / market making | **ASPIRATIONAL** phase 8 | Owner deferred |
| Tree growth UI / council personas | **ASPIRATIONAL** | Owner vision |
| Self-improvement loop | **PARTIAL** | `architecture/evolution/` human-gated |

---

## 7. ARCHITECTURE

### Target (Charter + ARCHITECTURE.md)
```text
MARKET DATA → DATA ENGINE → SIGNAL/ANALYTICS → RISK → PAPER → BACKTEST
                                                      ↓
INTELLIGENCE → DECISION → RISK GOVERNOR → PERMISSION → EXECUTION (future)
```

### Current (verified)
```text
Providers/Collector → Lane A discovery (frozen)
        ↓
Lane B: Identity → Security overlay → Intelligence → Scoring
        ↓
CanonicalDecisionAuthority → read_model.json
        ↓
TS Command Center / Telegram gateway (fail-closed)
```

**Dual-stack tension:** TS `scoring.ts`/`council.ts` still compute display ranks — bridged but not eliminated (`CANONICAL_IMPLEMENTATION_MATRIX.md`).

---

## 8. GOVERNANCE

| Rule | Mechanism |
|------|-----------|
| Master authority | `DOC_TRUTH_MAP.md` → canonical docs |
| Developer contract | `AGENTS.md` |
| Lane A integrity | `freeze_lane_a.py` + hash test |
| Import boundaries | `validate_imports.py` |
| Cursor hooks | Speed bump only — not security boundary |
| Phase honesty | NOT_STARTED / IN_PROGRESS / BLOCKED / PARTIAL / VERIFIED / COMPLETE |
| Human-only | Lane A `--write`, live trading, secret rotation, soak start |
| Supervision | `docs/supervision/` — council directives |

**Frozen:** `discovery/**`, `paper_trading/**`, immutable `MASTER_DIRECTIVE_v1`, soak T0 during active soak (Charter §39).

---

## 9. INTELLIGENCE MODEL

| Layer | Status | Notes |
|-------|--------|-------|
| Market intelligence | **IMPLEMENTED** | providers, intel, intelligence packages |
| Evidence fusion | **IMPLEMENTED** | PAL, observations, provenance |
| Identity | **IMPLEMENTED** | Lane B wraps frozen discovery |
| Security | **IMPLEMENTED** | Overlay + frozen evaluator |
| Scoring | **IMPLEMENTED** | Score-only, not decision |
| Decision | **IMPLEMENTED** | `CanonicalDecisionAuthority` |
| Risk | **IMPLEMENTED** | Part of authority pipeline |
| Calibration | **IMPLEMENTED infra** / **NOT VALIDATED** | 0 joined pairs (M-GAP-008) |
| Learning | **PARTIAL** | Ledger exists; measurement blocked |
| Self-improvement | **PARTIAL** | Evolution engine; autonomy OFF |

**Epistemic states (first-class):** STALE, UNAVAILABLE, UNKNOWN, INCOMPLETE, RUMOR ≠ FACT

---

## 10. AGI / ACI VISION

| Capability | DESIGNED | IMPLEMENTED | TESTED | VALIDATED | OPERATIONAL |
|------------|----------|-------------|--------|-----------|-------------|
| Charter cognitive loop | ✅ | ❌ | ❌ | ❌ | ❌ |
| P2 memory substrate | ✅ | ✅ isolated | ✅ | ❌ soak | ❌ |
| P3 cognitive loop | ✅ | ✅ isolated | ✅ | ❌ | ❌ |
| P4 benchmarks | ✅ | ✅ synthetic | ✅ | ❌ real market | ❌ |
| P5 typed evidence | ✅ | ✅ main code | ✅ | ⚠️ governance NO | ❌ |
| World model | ✅ | ❌ | ❌ | ❌ | ❌ |
| Agent creation | ✅ | ❌ | ❌ | ❌ | ❌ |
| Live execution L6–7 | ✅ | ❌ forbidden | — | — | ❌ |
| Domain-AGI (owner) | ✅ | ❌ | ❌ | ❌ | ❌ |

**Ceiling:** L1_ANALYZE, PAPER_ONLY. AGI/ACI is **NOT IMPLEMENTED** per charter header.

---

## 11. PRODUCT / UX VISION

| Feature | DESIGNED | IMPLEMENTED | TESTED | VALIDATED | OPERATIONAL |
|---------|----------|-------------|--------|-----------|-------------|
| Command Center dashboard | ✅ | ✅ | ✅ partial | ❌ operator | ❌ |
| FA RTL UI | ✅ | ✅ | ✅ | — | partial |
| EN full switch | ✅ owner | ⚠️ partial | — | — | ❌ |
| Conversational chat | ✅ owner P1 | ✅ gateway | ✅ | ❌ E2E live | ❌ |
| Telegram bot | ✅ | ✅ code | ✅ | ❌ live token | ❌ M-GAP-009 |
| Loud alerts | ✅ owner | ⚠️ banner code | ✅ | ❌ | ❌ |
| 3D / ambient audio | ✅ owner | ❌ duplicate trees only | — | — | ❌ |
| Environment Engine | ✅ owner | ❌ | — | — | ❌ |
| Tree growth viz | ✅ owner | ❌ | — | — | ❌ |
| Council personas | ✅ owner | ❌ | — | — | ❌ |
| Contract address accuracy | ✅ P0 | ⚠️ W4 in progress | ✅ unit | ❌ E2E | ❌ |

**Canonical web surface:** repo-root `app/` + `CommandCenter.tsx` only. Five duplicate Next trees are **orphans** (tsconfig exclude).

---

## 12. FUTURE AUTOMATION

| Level | Charter | Current |
|-------|---------|---------|
| L0 OBSERVE | ✅ | **OPERATIONAL** (daemon) |
| L1 ANALYZE | ✅ | **OPERATIONAL** |
| L2 RECOMMEND | ✅ | **PARTIAL** (alerts need live Telegram) |
| L3 AUTONOMOUS EXPERIMENT | ✅ | **PARTIAL** (evolution proposals) |
| L4 PAPER TRADING | ✅ | **OPERATIONAL** (Lane A) |
| L5 SIMULATED EXECUTION | ✅ | **PARTIAL** |
| L6 LIMITED LIVE | ✅ | **FORBIDDEN** |
| L7 CONTROLLED AUTONOMOUS | ✅ | **FORBIDDEN** |

**Trading capability ≠ permission.** Owner defers HFT to phase 8.

---

## Launch requirements (evidence-gated)

A capability is **OPERATIONAL** only with linked artifacts. Launch blockers:

| Requirement | Status | Gap |
|-------------|--------|-----|
| Lane A integrity | ✅ | — |
| pytest baseline (~2128) | ✅ | CI absent M-GAP-004 |
| Windows G1–G10 (pre-soak) | ❌ | Owner |
| 168h soak | ❌ | M-GAP-003 |
| Telegram E2E live | ❌ | M-GAP-009, S-01 |
| Calibration measurement | ❌ | M-GAP-008 (0 pairs) |
| OPERATOR_READY report | ❌ | `operator_validation_report_windows_*.json` missing |
| PRODUCTION_READY | ❌ | Forbidden claim |

**Launch audit rule:** No readiness upgrade without artifact in `AHOS_GAP_REGISTER.md`.

---

## Forbidden assumptions (council will reject)

- Test count = production ready
- Branch/PR existence = feature shipped
- Fixture tests = E2E proof
- Import success = runtime success
- AGI folder name = AGI capability
- Documentation = implementation
- STALE artifact = green CI
- Mock provider = live provider
- TS score = canonical BUY without Python injection

---

## Conflict register (supervisory)

| Conflict | Resolution |
|----------|------------|
| P5 code on main vs evolution index `MERGE=NO` | Report to human; do not treat as closed |
| W4 PR stack ahead of W2 merge | **BLOCK** until W2 on main |
| Duplicate 3D web trees vs One Brain | Orphan — do not wire to production |
| Owner wants "complete now" vs soak §39 | Soak and governance win |

---

## Review schedule

- **Next full truth model refresh:** after W2 merge + operator gate progress
- **Per-cycle delta:** `docs/supervision/cycles/CYCLE_NNN_*.md`
- **Build agent directive:** `LATEST_DIRECTIVE_FOR_AHOS_AGENT.md`

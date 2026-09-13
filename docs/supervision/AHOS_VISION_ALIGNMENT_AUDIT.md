# AHOS Vision Alignment Audit

**Council:** Independent AHOS Oversight Council  
**Date:** 2026-09-12  
**Type:** Pre-directive vision audit (no implementation)  
**Authority sources:** `OWNER_VISION_REGISTRY.md`, `AHOS_PROJECT_TRUTH_MODEL.md`, `MISSION.md`, `DOC_TRUTH_MAP.md`, `AGENTS.md`, `AHOS_GAP_REGISTER.md`, `CANONICAL_IMPLEMENTATION_MATRIX.md`, Charter v1.0, owner Master Vision messages, `BASELINE_AUDIT_2026-09-12.md`  
**Council STATUS after audit:** `MONITOR`  
**Build agent:** No new merge/slice authorized; existing §20 locks remain

---

## Executive summary

The council **does understand** what AHOS is supposed to become: an evidence-first, Persian-first, paper-only opportunity intelligence system evolving toward **Domain-AGI/ACI** in its mission domain — not a trading bot, not fake AGI, not a static scanner.

**Gap:** Vision is **much larger** than what is **operational** today. Implementation is strong on **governance, authority boundaries, and Lane B engineering**; weak on **owner-facing product (chat, Telegram live, alerts, immersive UX)** and **operational proof (soak, calibration, Windows gates)**.

**Council self-critique:** Prior BEST PATH (W1.3→W2→W4→P1) is **architecturally correct** for identity/trust foundation but **under-weighted owner P1** and **over-weighted W4 stack depth** relative to launch relevance. Revised path below.

---

## 1. AHOS Vision Alignment Matrix

Legend:
- **A** = Owner wants (VISION)
- **B** = Architecture supports
- **C** = Code claims / exists
- **D** = Evidence proves operational
- States: `IMPL` implemented · `PART` partial · `DES` designed only · `NO` missing · `DEF` deferred by design

| CAPABILITY | OWNER INTENT (A) | ARCH LOCATION (B) | CURRENT (C) | TESTED | VALIDATED | INTEGRATED | OPERATIONAL | EVIDENCE | GAP | PRIORITY | LAUNCH |
|------------|------------------|-------------------|-------------|--------|-----------|------------|-------------|----------|-----|----------|--------|
| **Core intelligence / One Brain** | Single evidence-first brain; no second authority | `architecture/decision/`, AGENTS.md | PART | ✅ | ✅ | PART | PART | one-brain tests | TS dual-stack remains | P0 | MUST |
| **Token discovery** | DexScreener, Gecko, pump.fun, multi-chain | `architecture/collector/`, providers | PART | ✅ | ⚠️ agent-host only | PART | NO | M-GAP-007 | Windows live probe | P0 | MUST |
| **Opportunity intelligence** | Rank explainably; NO OPPORTUNITY ok | scoring, intel, pipeline | PART | ✅ | NO | PART | NO | matrix PARTIAL | calibration data | P0 | MUST |
| **Evidence system** | Provenance, UNKNOWN, no fabrication | PAL, discovery, learning ledger | IMPL | ✅ | PART | PART | PART | freeze, ledger tests | live accrual | P0 | MUST |
| **Identity resolution** | Real verified contract addresses | `architecture/identity/`, W4 stack | PART | ✅ | NO | NO | NO | unit tests | W2 not main; W4 unmerged | P0 | MUST |
| **Security / scam / honeypot** | Veto before opportunity | `architecture/security/`, Lane A gate | IMPL | ✅ | PART | PART | PART | overlay tests | live E2E | P0 | MUST |
| **Market intelligence** | Volume, liquidity, momentum | `architecture/intel/`, providers | PART | ✅ | NO | PART | NO | unit tests | live data | P1 | MUST |
| **News intelligence** | Verify sources, Persian | intel, CommandCenter news | PART | ✅ | NO | PART | NO | UI exists | live feeds | P1 | SHOULD |
| **Social intelligence** | X/TG/IG as signals not facts | intel, providers (X blocked policy) | PART | ✅ | NO | PART | NO | tests | scraping policy | P2 | SHOULD |
| **On-chain intelligence** | Whales, holders, transfers | intel, discovery | PART | ✅ | NO | PART | NO | tests | — | P1 | MUST |
| **Narrative intelligence** | Meme/AI/DePIN narratives | intel | PART | ✅ | NO | PART | NO | tests | — | P2 | SHOULD |
| **Liquidity / whale / demand** | Signals for pump potential | intel, scoring | PART | ✅ | NO | PART | NO | tests | — | P1 | MUST |
| **Explainable scoring** | Why + risks + scenarios | scoring, explanations, dossier | PART | ✅ | NO | PART | NO | dossier W1 | W2 branch | P1 | MUST |
| **Calibration** | Measure score vs outcome | `architecture/learning/` | PART | ✅ | NO | PART | NO | 0 pairs M-GAP-008 | owner data | P1 | MUST |
| **Historical learning** | Win/loss post-mortem | learning, evolution | PART | ✅ | NO | NO | NO | harness only | — | P2 | SHOULD |
| **Backtesting / self-improvement** | Sandbox promote/reject | evolution, strategy_lab | PART | ✅ | NO | NO | NO | isolated | — | P3 | CAN FOLLOW |
| **Paper trading** | Virtual positions lifecycle | `paper_trading/` Lane A | IMPL | ✅ | PART | PART | PART | Lane A tests | — | P0 | MUST |
| **User position tracking** | "I bought X" monitor | positions, telegram flows | PART | ✅ | NO | PART | NO | tests | live UX | P1 | SHOULD |
| **Telegram (Sun Sniper)** | Natural FA chat, alerts | `telegram_ai/` gateway | PART | ✅ | NO | PART | NO | M-GAP-009 | token + gateway URL | P0 | MUST |
| **Alerts (loud)** | Opportunity + sound web+TG | alerts.ts, telegram alerts | PART | ✅ | NO | PART | NO | banner tests | live | P0 | MUST |
| **Web dashboard** | Command Center ops | `app/`, CommandCenter.tsx | PART | ✅ | NO | PART | PART | web tests | not operator-verified | P0 | MUST |
| **AI conversational UI** | ChatGPT-quality FA/EN | conversation_gateway, /api/chat | PART | ✅ | NO | PART | NO | auth tests | E2E quality | P0 | MUST |
| **Persian-first UX** | RTL, natural language | layout, telegram intent | PART | ✅ | PART | PART | PART | NLU matrix | full product copy | P0 | MUST |
| **English mode** | Full UI switch | owner P2 | DES | NO | — | — | — | — | not built | P2 | SHOULD |
| **System status / observability** | Health, watchdog, snapshots | runtime, observability, watchdog | PART | ✅ | PART | PART | PART | soak scripts | 168h M-GAP-003 | P1 | MUST |
| **Provider architecture** | Multi-provider fallback Iran | providers, router, PAL | PART | ✅ | PART | PART | NO | probe cmd | Windows probe | P0 | MUST |
| **Knowledge / memory** | Dossier, claims, cognitive P2 | `architecture/knowledge/`, cognitive | PART | ✅ | NO | NO | NO | W1 main, W2 branch | not UI-wired | P1 | SHOULD |
| **AI council / multi-agent** | 10 teams, debate, meta-layer | `architecture/council.py`, ai/ | PART | ✅ | NO | PART | NO | council tests | not 10-team UX | P2 | CAN FOLLOW |
| **AGI/ACI roadmap** | Domain cognitive evolution | cognitive/, charter | DES+PART | ✅ isolated | NO | NO | NO | P2-P5 tests | not AGI | P3 | FUTURE |
| **Future automation** | L0-L7 ladder, not now | Charter §25 | DES | DEF | — | — | — | CLOSED live | by design | — | FUTURE |
| **Security ops** | S-01 token, overlay | security, gaps | PART | ✅ | NO | PART | NO | S-01 OPEN | rotate token | P0 | MUST |
| **Reliability** | 168h soak, backups | soak protocol, backup script | PART | ✅ | NO | PART | NO | M-GAP-003/010 | owner run | P0 | MUST |
| **Windows / local-first** | Laptop, $0, no VPS | handoff docs, paths | PART | ✅ | NO | PART | NO | agent-host only | Windows G1-G10 | P0 | MUST |
| **Launch / deployment** | Operator then production | gates, gap register | DES | PART | NO | NO | NO | NOT_VERIFIED | all G3-G6 | P0 | MUST |
| **Environment Engine** | Geo/weather/time/audio UI | owner P2 | DES | NO | — | — | — | — | not started | P3 | CAN FOLLOW |
| **3D / Awwwards UX** | Immersive site | orphan Next trees | DES | NO | — | — | — | — | not canonical | P3 | CAN FOLLOW |
| **Tree growth / personas** | Visual council + tree | owner P2 | DES | NO | — | — | — | — | — | P3 | CAN FOLLOW |
| **Multi-market (gold/forex/equity)** | Domain adapters later | Charter placement law | DES | NO | — | — | — | — | future | P4 | FUTURE |
| **Low-latency / HFT path** | Phase 8 deferred | owner roadmap | DES | NO | — | — | — | — | deferred | P4 | FUTURE |
| **CT trading signals** | Evidence not authority | owner P3 | DES | PART | NO | NO | NO | — | integration | P2 | CAN FOLLOW |
| **GitHub OSS learning** | Learn adapt license | oss_pipeline, AG-25 | DES | PART | NO | NO | NO | NOT_IMPL live | AG-25 | P3 | CAN FOLLOW |
| **n8n automation** | Edge automation | n8n/workflows | PART | ✅ struct | NO | NO | NO | validate_n8n | runtime | P2 | CAN FOLLOW |
| **Human feedback signals** | W3 isolated | PR #96 branch | YES | ✅ | NO | NO | NO | unit tests | not merged | P2 | CAN FOLLOW |

---

## 2. AHOS Idea Coverage Matrix

| Owner idea | In Vision docs | In architecture | In roadmap/PRs | In code | In tests | Status |
|------------|----------------|-----------------|----------------|---------|----------|--------|
| Evidence before decision | ✅ | ✅ | ✅ | ✅ | ✅ | **COVERED** |
| Security veto | ✅ | ✅ | ✅ | ✅ | ✅ | **COVERED** |
| Persian-first Telegram | ✅ | ✅ | ✅ | ✅ | ✅ | **PARTIAL** (not live) |
| 10-team AI council | ✅ Master Vision | ⚠️ simplified council | ⚠️ | ✅ advisory | ✅ | **SIMPLIFIED** |
| Tree of knowledge metaphor | ✅ Master Vision | ❌ | ❌ | ❌ | ❌ | **IDEA_LOSS (UX)** |
| Environment Engine | ✅ owner | ❌ | ❌ | ❌ | ❌ | **NOT STARTED** |
| 3D immersive + ambient audio | ✅ owner | ❌ orphans only | ❌ | ❌ | ❌ | **NOT STARTED** |
| Sun Sniper Telegram bot | ✅ owner | ✅ gateway | ⚠️ | ✅ | ❌ live | **PARTIAL** |
| Loud alerts | ✅ owner | ⚠️ banner | ⚠️ | ⚠️ | ⚠️ | **PARTIAL** |
| Contract address truth | ✅ P0 | ✅ W4 | ✅ PR stack | ✅ | ✅ | **IN PROGRESS** |
| Domain-AGI/ACI | ✅ Charter | ✅ cognitive | ✅ P2-P5 | ✅ isolated | ✅ | **RESEARCH** |
| World model | ✅ Charter | ❌ ACI-GAP-002 | ❌ | ❌ | ❌ | **ASPIRATIONAL** |
| Multi-market trading | ✅ owner long-term | ✅ adapter law | ❌ | ❌ | ❌ | **FUTURE** |
| $0 / Iran / local / no VPS | ✅ | ✅ | ✅ | ✅ | ✅ | **COVERED** |
| Paper-only now | ✅ | ✅ | ✅ | ✅ | ✅ | **COVERED** |
| User position "I bought" | ✅ Master Vision | ⚠️ | ⚠️ | PART | PART | **PARTIAL** |
| Daily intelligence report | ✅ Master Vision | ⚠️ | ❌ | PART | ❌ | **IDEA_LOSS** |
| Performance charts PnL | ✅ Master Vision | ⚠️ | ❌ | PART | ❌ | **PARTIAL** |
| Self-debug / self-improvement | ✅ | ✅ evolution | ✅ | PART | PART | **PARTIAL** |
| Frontier research directorate | ✅ Charter | ⚠️ docs | ❌ | ❌ | ❌ | **ASPIRATIONAL** |
| Cognitive Society (memory-bearing agents) | ✅ owner | ⚠️ passports memory_bearing=false | ✅ P3 | PART | ✅ | **DESIGNED AHEAD OF IMPL** |

---

## 3. AHOS Launch Gap Map

| Tier | Capabilities | Evidence |
|------|--------------|----------|
| **MUST HAVE BEFORE LAUNCH** | One Brain authority; identity/contract verified; security veto; paper trading; Command Center; conversational chat (FA); Telegram live; canonical-gated alerts; provider probe on operator machine; Windows G1–G10; 168h soak; calibration ≥ minimal pairs; no S-01 | G3-G6 fail today; M-GAP-003/008/009 |
| **SHOULD HAVE BEFORE LAUNCH** | News/social intel live; user position tracking UX; explainable dossier in UI; EN language switch; nightly backups 7 nights; CI optional | Partial impl |
| **CAN FOLLOW AFTER LAUNCH** | Environment Engine; 3D/audio; council personas; tree viz; W3 human feedback; n8n runtime; CT signals integration; historical learning depth | Owner P2-P3 |
| **FUTURE / RESEARCH** | Domain-AGI/ACI world model; agent creation; multi-market adapters; HFT; live execution L6+; AG-25 live GitHub harvest | Charter + owner defer |
| **NOT REQUIRED** | Wall-Street HFT; multi-tenant; VPS; orphan 3D template sites in repo | Owner + design |

---

## 4. Vision Drift Findings

### UNDER-BUILD (Vision > Implementation)

| Drift | Severity | Evidence |
|-------|----------|----------|
| Product feels like "engineering platform" not "Sun Sniper experience" | HIGH | P1 chat/TG/alerts not live |
| Master Vision 10-team council → simplified advisory council | MED | `architecture/council.py` |
| Tree metaphor, daily report, performance charts | MED | Not in Command Center |
| Environment Engine / immersive UX | MED | Owner P2 not started |
| Explainable token dossier not in operator UI | MED | W1 not wired to CC |
| Calibration learning loop | HIGH | 0 pairs |

### OVER-BUILD (Implementation > Vision need now)

| Drift | Severity | Evidence |
|-------|----------|----------|
| 7-slice W4 PR stack before W2 merge | HIGH | #97–#103 vs #95 |
| 5 orphan 3D Next.js trees | LOW | tsconfig exclude |
| P2–P5 cognitive research on main while product idle | MED | not soak-wired but repo focus |
| 40+ cursor branches / phase reports volume | LOW | onboarding noise |
| Dual TS scoring stack | MED | matrix PARTIAL |

---

## 5. Under-Build Findings (detailed)

1. **Operator cannot use AHOS end-to-end today** — Telegram not live, soak not run, Windows gate missing.
2. **Owner P0 contract accuracy** — in progress (W4) but blocked on sequencing.
3. **Conversational product quality** — gateway exists; owner wants ChatGPT-level — **unvalidated**.
4. **Alerts with sound** — designed; not proven loud TG + web alarm path.
5. **Learning from outcomes** — infrastructure complete; measurement empty.

---

## 6. Over-Build Findings (detailed)

1. **W4 slices 1–7 PR chain** — architecturally aligned but **disproportionate** vs unmerged W2 and idle P1.
2. **Knowledge layer depth** (W1.1, W1.2, W2, graph) ahead of UI integration — research-heavy.
3. **AGI/ACI evolution pack** — well-governed but risks **perception drift** if not labeled aspirational.
4. **Council spent 3+ cycles on W1/W2/W4** — owner audit correctly flags product deprioritization risk.

---

## 7. Missing / Lost Ideas (IDEA_LOSS)

| Idea | Source | Status | Risk |
|------|--------|--------|------|
| Tree growth visualization | Owner P2, Master Vision | Not in roadmap PRs | Medium — UX identity |
| Council visual personas | Owner P2 | Not started | Low — P2 |
| Daily Intelligence Report | Master Vision §41 | Not surfaced in CC | Medium — operator habit |
| "1000→1 exceptional opportunity" funnel UX | Master Vision §29 | Logic exists; UX not | Low |
| Cognitive Society memory-bearing agents | Owner + Charter | Explicitly `memory_bearing=false` today | Intentional gap — not loss |
| Multi-provider AI debate UX | Owner P3 | Backend only | Medium |
| GitHub as learning source (AG-25 live) | Master Vision §22 | NOT_IMPLEMENTED | Low — deferred |

**Not IDEA_LOSS (correctly deferred):** HFT, live trading, world model, VPS, multi-user.

---

## 8. AGI / ACI Reality Map

| Capability | VISION | DESIGN | IMPLEMENTATION | TEST | VALIDATION | OPERATIONAL |
|------------|--------|--------|----------------|------|------------|-------------|
| Charter cognitive loop | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| P2 memory substrate | ✅ | ✅ | ✅ isolated | ✅ | ❌ | ❌ |
| P3 cognitive loop | ✅ | ✅ | ✅ isolated | ✅ | ❌ | ❌ |
| P4 benchmarks | ✅ | ✅ | ✅ synthetic | ✅ | ❌ | ❌ |
| P5 typed evidence | ✅ | ✅ | ✅ main code | ✅ | ⚠️ gov NO | ❌ |
| World model | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Agent creation | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Self-improvement governance | ✅ | ✅ | ✅ human-gated | ✅ | PART | ❌ |
| Domain-AGI (owner) | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Live execution L6-7 | ✅ future | ✅ | ❌ forbidden | — | — | ❌ |

**Verdict:** AGI/ACI is **correctly labeled aspirational** in charter. Risk is **packaging/naming drift**, not false code claims — if council/agents avoid "AGI delivered" language.

---

## 9. Critique of Current Best Path

### Current path
`W1.3 → W2 merge → W4 rebase → P1 chat/TG/alerts → owner ops`

### What is right
- **Identity/contract P0** must precede trustworthy alerts ("amazing token" with wrong address = catastrophic).
- **W2 on main** reduces split-brain in knowledge layer.
- **Charter §39** — not jumping to product while breaking soak is correct.
- **§20 locks** on #103 / Slice 8 — correct per owner.

### What is wrong / incomplete
- **P1 deprioritized too long** while build agent built 7 W4 slices — owner P0/P1 product lag.
- **W4 rebase may be premature** — owner blocked #103; full stack merge may need **human gate per slice**, not mechanical rebase.
- **"Foundation first" became "research first"** — dossier/graph/cognitive ahead of Telegram live.
- **No parallel track** for owner-only actions (token rotate, Windows gate) — council should ESCALATE_TO_HUMAN explicitly in every strategic cycle.

### Dependency check
| Before P1 | Required? |
|-----------|-------------|
| W2 on main | YES — reduces confusion |
| W1.3 spoof fix | YES — trust boundary |
| Full W4 merge | **NO** — only contract-display path needs identity; not all 7 slices |
| Soak complete | NO for P1 wiring — but Charter §39 blocks runtime *changes* during soak |

---

## 10. Meta-Critique of Council Findings

| Council claim | Valid? | Adjustment |
|---------------|--------|------------|
| "Council over-focused on W4" | **YES** | Evidence: 7 PRs, agent idle on P1 |
| "Skip W4 entirely" | **NO** | Owner P0 contract accuracy needs identity work |
| "P1 should come before W1.3" | **NO** | Spoof fix is small; identity trust precedes alerts |
| "Merge all W4 now" | **NO** | Owner BLOCK on #103; human per-slice |
| "3D UX is launch blocker" | **NO** | SHOULD/CAN FOLLOW per launch map |
| "Truth model complete" | **PARTIAL** | ISSUE_REGISTER unread; re-verify pytest at HEAD |
| "IDEA_LOSS tree viz" | **YES** but P3 | Don't elevate to MUST |

**Bias check:** Council may under-value W4 because of PR count fatigue — **W4 slice 3 (Gecko pool/token boundary) is launch-relevant**, not over-engineering.

---

## 11. FINAL BEST PATH (single)

### Problem
AHOS must reach trustworthy Launch without losing owner vision (product + intelligence + AGI path) while respecting safety locks and evidence discipline.

### Evidence
This audit matrices; baseline G3-G6 fail; owner P0/P1; §20 locks.

### Alternatives considered

| Alt | Rejected why |
|-----|----------------|
| A: P1 immediately, skip W2 | Split-brain knowledge; wrong contract risk |
| B: Continue W4 slices 8+ | Owner BLOCK |
| C: Merge entire W4 stack at once | Review debt; #103 blocked |
| D: Pause all engineering for UX only | Violates identity P0; soak safety |
| E: Current path unchanged | Under-serves P1 too long — **partially reject** |

### Chosen path

```
PHASE 0 (HUMAN — parallel, not build agent)
  → Rotate Telegram token (S-01)
  → Windows G1–G10 when ready
  → Authorize soak window if applicable

PHASE 1 (BUILD — small, evidence-gated)  [FIX_BEFORE_CONTINUE]
  → W1.3 spoof hardening
  → Merge W2 (#95) only
  → DOSSIER.md + DOC_TRUTH_MAP
  → STOP further W4 slices; HOLD #103 per §20

PHASE 2 (BUILD — owner P1 product)  [ALLOW after Phase 1]
  → Chat FA quality via gateway (E2E transcript artifact)
  → Telegram Sun Sniper .env wiring (no secrets in git)
  → Alerts: canonical gates + web sound + TG (E2E artifact)
  → Contract display: consume existing identity path; no new authority

PHASE 3 (BUILD — selective W4)  [ESCALATE_TO_HUMAN per slice]
  → Human reviews which W4 slices merge (likely 3–4 boundary fix first)
  → NOT automatic full stack rebase

PHASE 4 (OWNER + BUILD)
  → Soak + calibration pairs accrue
  → G3-G6 re-audit

PHASE 5+ (CAN FOLLOW)
  → Environment Engine spec → incremental UX
  → AGI/ACI research isolated
  → Multi-market / HFT future
```

### Why this is best
Balances **owner P0 trust** (identity), **owner P1 product** (chat/TG/alerts), **owner §20 safety**, and **launch gates** without architecture churn or fake readiness.

### Risks
- Build agent remains IDLE → ESCALATE_TO_HUMAN wake
- P1 attempted during soak → BLOCK runtime semantic changes
- W4 needed for contracts but blocked → monitor identity display bugs

### Mitigations
- PRE-FLIGHT/POST-FLIGHT per SUPERVISION_ARCHITECTURE v2
- L1 PR event on any W4 merge attempt
- Explicit HUMAN gate for slices beyond approved set

### Required tests
- pytest + freeze_lane_a at HEAD before any merge
- E2E artifacts for P1 (chat, alert, TG)

### Rollback
- Revert PR; truth model records state; no force-push

---

## Council STATUS

| Target | Status |
|--------|--------|
| **Council** | `MONITOR` |
| **Build agent** | `FIX_BEFORE_CONTINUE` (Phase 1 only when active) |
| **PR #103 / Slice 8** | `BLOCK` (unchanged §20) |
| **New directives** | Issued only after this audit — see `LATEST_DIRECTIVE` update |

---

## What AHOS is supposed to become (evidence statement)

AHOS should become a **trustworthy, Persian-first, evidence-backed opportunity intelligence operating system** on the owner's Windows laptop that:

1. Finds and explains early token opportunities with **verified** identities and **security veto**
2. Talks naturally via **web and Telegram** with **honest** UNKNOWN/STALE semantics
3. Alerts loudly only when **canonical gates** pass
4. Paper-trades and **learns** from outcomes with measurable calibration
5. Evolves toward **Domain-AGI/ACI** through **governed, isolated research** — never fake claims
6. Eventually supports broader markets and controlled execution — **only with permission ladder evidence**

That is what supervision will hold BUILD AGENT to — not merely green tests or more PRs.

---

*Next: L2 operational delta; L3 strategic alignment check; G1 gate after W2 merge.*

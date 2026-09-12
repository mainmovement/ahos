# Latest Directive for Ahos cursor configuration Agent

**Updated:** 2026-09-12 (Cycle 003 — owner vision integrated)  
**Status:** `PROCEED_AFTER_W2`  
**Owner vision:** `docs/supervision/OWNER_VISION_REGISTRY.md`  
**Charter:** `docs/architecture/AHOS_AGI_ACI_ARCHITECTURE_CHARTER_v1.0.md`

---

## READ FIRST (every session)

1. `docs/supervision/OWNER_VISION_REGISTRY.md`
2. `docs/supervision/LATEST_DIRECTIVE_FOR_AHOS_AGENT.md` (this file)
3. `.cursor/skills/ahos-governance-context/SKILL.md`
4. `docs/DOC_TRUTH_MAP.md` + `AGENTS.md`

---

## PHASE A — NOW (blocking everything else)

| # | Task | Skill | PR |
|---|------|-------|-----|
| A1 | W1.3: close dynamic class identity spoof | `ahos-token-identity` | on `cursor/token-dossier-composer-9500` |
| A2 | Add `test_w1_2_dynamic_class_spoof_is_not_canonical` | `ahos-change-verification` | same |
| A3 | Merge-ready W2 (#95) | `ahos-domain-backend` | #95 |
| A4 | `architecture/knowledge/DOSSIER.md` + DOC_TRUTH_MAP | `ahos-governance-context` | same |
| A5 | Rename `test_w12_*` → `test_w1_2_*` | — | same |
| A6 | Security overlay/decision conflict fail-closed | `ahos-security-analysis` | same |
| A7 | Rebase W4 (#97–#103) on post-W2 main; collapse to ≤3 PRs | `ahos-token-identity` | rebase |

**Do not start Phase B until W2 is on `main`.**

---

## PHASE B — Owner P1 (after W2 merged)

| # | Task | Skill | Notes |
|---|------|-------|-------|
| B1 | **Chat UX** — natural FA/EN conversation on site | `ahos-web-experience` | via Conversation Gateway, not second brain |
| B2 | **Telegram Sun Sniper** — wire bot, match app gateway | `ahos-domain-backend` | token **only** in `.env`; rotate S-01 |
| B3 | **Alerts** — opportunity + loud alarm (web + Telegram) | `ahos-web-experience` | requires Python `alerts_allowed` + overlay PASS |
| B4 | **Contract accuracy** — canonical address display | `ahos-token-identity` | UNKNOWN if unverified; never guess |
| B5 | E2E evidence: chat transcript + telegram + alert screenshot/video | `ahos-change-verification` | artifact required |

---

## PHASE C — Experience (small waves, not one PR)

| # | Task | Skill |
|---|------|-------|
| C1 | Write `docs/architecture/DYNAMIC_ENVIRONMENT_ENGINE.md` spec | `ahos-web-experience` |
| C2 | Bilingual FA/EN switch (full UI copy) | `ahos-web-experience` |
| C3 | Ambient audio + 3D increments on Command Center | `ahos-web-experience` |
| C4 | Tree growth visualization + council persona cards | `ahos-product-intelligence` |

Awwwards-level quality = **iterative waves** with critic review each wave.

---

## PHASE D — AGI/ACI evolution (research only, isolated)

- Continue P2–P5 cognitive modules per Charter — **not soak-wired**
- Frontier layer: discover → benchmark → adopt/reject
- No "world model" labeling until `ACI-GAP-002` closed
- Self-improvement proposals only via sandbox + governance

---

## MODEL SELECTION

| Work | Model |
|------|-------|
| Architecture, security, identity | Claude Opus 5 High / GPT-5.6 Sol High |
| Implementation | Claude Sonnet 5 High / Composer 2.5 |
| Mechanical tests/docs | Grok 4.6 High Fast / Gemini 3.8 Flash High |
| Council debate | Multi-model (advisory merge only) |

---

## DO NOT

1. Lane A (`discovery/**`, `paper_trading/**`) — Charter §38
2. Live trading / leverage execution — Charter §25 (L0–L1 + PAPER_ONLY)
3. Commit secrets (Telegram token was exposed in owner chat — **rotate**)
4. Merge W4 before W2 on main
5. One mega-PR for website + telegram + AGI + trading
6. Claim AGI/ACI/PRODUCTION_READY delivered — Charter §42
7. Interfere with soak — Charter §39
8. TS independent authority — AGENTS.md

---

## DEFINITION OF DONE (per wave)

- Relevant tests pass (pytest + web selftests if UI)
- `freeze_lane_a.py` pass
- Walkthrough artifact (screenshot/video) for UI/telegram
- No secrets in diff
- Phase status honest in PR body

---

## Rationale

`docs/supervision/cycles/CYCLE_003_2026-09-12.md`

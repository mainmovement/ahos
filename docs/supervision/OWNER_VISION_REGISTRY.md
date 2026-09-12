# Owner Vision Registry (Supervision Memory)

**Purpose:** Long-term supervision memory for owner intent.  
**Authority:** Complements `docs/architecture/AHOS_AGI_ACI_ARCHITECTURE_CHARTER_v1.0.md` and Master Vision.  
**Law:** This registry does **not** override `AGENTS.md`, Lane A freeze, PAPER_ONLY, or soak gates.

---

## 1. North Star (owner-confirmed)

AHOS evolves toward **Domain-General Cognitive Intelligence** in its mission domain:

```text
Perceive → Understand → Remember → Reason → Discover → Hypothesize
→ Experiment → Debate → Predict → Observe → Learn → Self-Critique → Improve
```

- **Not** general AGI for all human problems.
- **Yes** Domain-AGI-like: adapt to new chains, attacks, narratives, market structures.
- **ACI** = cognitive architecture (memory, metacognition, council, experimentation).
- **Self-improvement** = propose → sandbox → benchmark → governance → promote/reject.
- **Never** uncontrolled modification of Lane A, security gates, or live trading permission.

---

## 2. Trading & markets roadmap (owner)

| Stage | Target | Status |
|-------|--------|--------|
| 1 | Fast data collection (WebSocket, order book) | PARTIAL |
| 2 | Signal / analytics engine | PARTIAL |
| 3 | Opportunity discovery | IN_PROGRESS |
| 4 | Paper trading | IMPLEMENTED (Lane A) |
| 5 | Backtesting | PARTIAL |
| 6 | Latency optimization | NOT_STARTED |
| 7 | Limited live (tiny capital) | NOT_STARTED |
| 8 | Professional HFT / market making | DEFERRED |

**Stack preference:** Python (orchestration, AI, backtest) + Rust (critical latency path later).  
**Not goal #1:** Wall-Street-grade HFT / colocation.  
**Yes goal #1:** Low-latency crypto scanning + evidence-first intelligence.

**Future markets (architecture must not block):** crypto tokens, gold, forex, EU/Asia equities, commodities, bonds, derivatives — via Domain Adapters, not rewriting Cognitive Core.

**Leverage:** Decision variable, risk-adjusted; 1× can be optimal; never bypass venue limits.

---

## 3. Product priorities (owner, ranked)

### P0 — Correctness & trust
- **Contract addresses must be real and verified** (canonical identity pipeline).
- Evidence before decision; UNKNOWN > fabricated.
- No fake AGI/ACI claims.

### P1 — Core product (next execution waves)
1. **Web chat** — conversational, Persian/English, gateway-quality UX.
2. **Telegram** — `@sun_sniperbot` / Sun Sniper; natural chat; matched with app gateway.
3. **Alerts** — loud Telegram + on-site alarm for high-opportunity tokens (overlay PASS + canonical gates).
4. **Command Center dashboard** — primary operations surface on GitHub Pages path.

### P2 — Experience (incremental, not one giant PR)
- Bilingual FA/EN full switch (UI copy, not numbers).
- 3D / audio / ambient environment (Awwwards-level aspiration).
- **Dynamic Real-Time Environment Engine:** geolocation → weather API → timezone → season/day/night → lighting/sky/audio/UI.
- Visible **tree growth** metaphor; council teams as visual personas.
- Themes: farm, battlefield, office, galaxy, etc. with ambient soundscapes.

### P3 — Intelligence depth
- 10-team AI council (math, market, on-chain, security, OSINT, news, social, engineering, AI research, red-team).
- Multi-provider AI (GPT, Claude, Gemini, Grok) — advisory only.
- CT (Crypto Twitter) trading signals as **evidence**, not authority.
- Learning from paper trade wins/losses; post-mortem loops.
- GitHub OSS learn → compare → adapt (license-respecting).

### P4 — AGI/ACI evolution layer (isolated research)
- Cognitive memory, loop, benchmark (P2–P5 on main, not soak-wired).
- Frontier research directorate (discover → benchmark → adopt/reject).
- World model: **NOT IMPLEMENTED** — do not mislabel dossier/graph as world model.

---

## 4. Constraints (binding)

| Constraint | Value |
|------------|-------|
| Budget | $0-first; free APIs; local-first |
| Runtime | Windows laptop; **no VPS** (owner) |
| Users | Single-user |
| Iran | Sanctions/filtering; provider fallbacks required |
| Execution | PAPER_ONLY until explicit owner promotion |
| Soak | Charter §39 — no interference during active soak |
| Secrets | **Never commit tokens** — use `.env` only (S-01 OPEN) |

---

## 5. Cursor skills map (for Ahos agent)

| Task | Skill |
|------|-------|
| Always first | `ahos-governance-context` |
| Identity / contract accuracy | `ahos-token-identity` |
| Security / scam | `ahos-security-analysis` |
| Market / discovery | `ahos-opportunity-hunter`, `ahos-market-intelligence` |
| Web / 3D / chat UX | `ahos-web-experience` |
| AI council | `ahos-ai-council` |
| Backend Python | `ahos-domain-backend` |
| Tests / evidence | `ahos-change-verification` |
| Research / OSS | `ahos-research-intelligence` |

---

## 6. Model selection (owner pool)

| Work type | Suggested models |
|-----------|------------------|
| Architecture / governance / security final | Claude Opus 5 High, GPT-5.6 Sol High |
| Deep implementation | Claude Sonnet 5 High, Composer 2.5 |
| Fast mechanical / grep / tests | Grok 4.6 High Fast, Gemini 3.8 Flash High |
| Multi-model debate | Use Multiple Models on council tasks only |

---

## 7. What "success" means (owner + Charter §48)

Not: 50 new files, 100 agents, or "AGI module exists."

Yes: measurable improvement on discovery quality, scam detection, calibration, false positive/negative, reasoning consistency, self-error detection — with artifact proof.

---

## 8. Supervision note

Owner vision is **large**. Execution must stay **sequenced** per `AGENTS.md` phase gates.  
Supervision agent enforces: foundation first, no soak violation, no secret leaks, no readiness inflation.

**Last updated:** 2026-09-12 (owner message integration)

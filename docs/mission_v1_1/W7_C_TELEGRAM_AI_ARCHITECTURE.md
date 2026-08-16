# TELEGRAM AI ARCHITECTURE (Deliverable C) — 2026-08-11
# State letters per component. Persian-first. Free-first. Deterministic authority.

## 1. Layer diagram (directive §16, as-built)
TELEGRAM (bot API — token env-only, user blocker ①)
  ↓ webhook/poller (n8n 20/21/22 in Phase-5; engine/bot_skeleton today)
PERSIAN INTENT PARSER — telegram_ai/intent.py — **C Tested** (25 tests; all §16/Part-XVI examples pinned)
  ↓ ParseResult(intent, confidence, rule_id, slots, needs_context)
DETERMINISTIC COMMAND LAYER — routes ONLY on rule hits; UNKNOWN ⇒ clarify, never guess — **B Implemented**
  (routing law + INFO_ONLY/LEDGER_MUTATING gates in code; bot glue lands with token)
AI-PAL — telegram_ai/providers.py + ai_providers.yaml — **C Tested** (fallback chain LIVE VERIFIED in
  DETERMINISTIC_ONLY mode from sandbox, PRB-20260811-AI-001; keyed providers NEEDS_USER_KEY)
AHOS DATA / RESEARCH ENGINE — discovery/* + research/* — authoritative for ALL numbers — **C Tested**
RESPONSE GENERATOR — fact-templated Persian answers; AI may polish phrasing only — **B Implemented**
  (render contracts in alerts.py; bot templates land with token)
PERSIAN TELEGRAM RESPONSE — footer law enforced on decisional content — **B Implemented**

## 2. Authority law (test-pinned)
- Deterministic code owns: prices, amounts, timestamps, P/L, identity, security verdicts, research
  verdicts, ledger writes. AI NEVER mutates financial records (LEDGER_MUTATING_INTENTS={"BUY_LOG"},
  reachable only from the command layer; test-pinned).
- sell-advice/take-profit/PnL intents are INFO-ONLY (test-pinned) — answers state facts and risks,
  never directives.
- AI output frames carry ADVISORY_DISCLAIMER_FA; decisional messages end with «تصمیم نهایی با کاربر است.»

## 3. Degradation ladder (never stops answering — directive §14)
1. Local model (ollama) — auto-joins chain when VPS/laptop exists (blocker ②).
2. Free-tier keyed providers in chain order (GitHub Models → Groq → Gemini → OpenRouter free).
3. DETERMINISTIC_ONLY — parser + templates answer alone; AI assist absent is a MODE, not a failure.
Each hop is probe-evidenced; no capability claim without probe id.

## 4. What is NOT built yet (honest)
- Live Telegram glue (needs token rotation ① + VPS ②): webhook intake, session context store
  (for «این توکن» anaphora), rate limiting per user. DESIGN COMPLETE here; code B/C for core modules.
- Persian ASR/voice input — out of scope for Wave-7.
- LLM function-calling into AHOS tools — deliberately deferred until the deterministic command layer
  has more live mileage (security review concern: tool-call injection surface).

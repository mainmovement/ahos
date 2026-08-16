# K. TELEGRAM PERSIAN AI-INTERFACE IMPLEMENTATION PLAN — Wave-6 (Part XVI/XVII) — 2026-08-11

## Principle (binding)
AI interprets language; DETERMINISTIC CODE records TOKEN/AMOUNT/PRICE/TIME/POSITION/P&L.
An LLM output can never mutate a financial record without schema validation + user confirmation.

## 1. Layers
```
Persian free text
 → Layer-1 deterministic parser (regex/digit-parse: ۵≡5, تومان/تومن/تتر/دلار, order words)   [this wave's plan → code Phase-6]
 → Layer-2 AI-PAL intent arbitration (ONLY if L1 confidence < τ or ambiguity)                [advisory]
 → structured intent {intent, slots, confidence, source_layer}
 → CONFIRMATION CARD (✔ثبت/✎اصلاح/✖لغو)   [mandatory for position.open]
 → deterministic ledger (positions)
```

## 2. Intent set v1 (frozen in I-doc; implementation order)
position.open (qty or amount+currency) · position.status · portfolio.list · watchlist.add ·
partial_exit_query · full_exit_query · opportunities.list · help.
Parser fixtures: ≥14 golden utterances (incl. «سیو سود کنم؟»=partial_exit_query, «همه رو بفروشم؟»=
full_exit_query, «این توکن رو زیر نظر بگیر»=watchlist.add) — 100% pass required (Phase-6 CI).

## 3. AI-PAL (provider chain, free-first; advisory only)
Chain: [user-provided key (OpenRouter free models / Gemini free tier) → local OSS model (ollama on VPS,
e.g. small instruct fa/multilingual) → deterministic L1-only fallback (clarify loop)].
Contract: {model_id, prompt_hash, response, latency, cost(=$0 cap), confidence} logged to audit.
Schema-validated JSON intent; invalid/timeout ⇒ L1-only path + clarify question.
NO AI call is required for system operation (cost-zero + Iran-resilient by construction).

## 4. Safety bars
- Intent schema whitelist (unknown intent ⇒ clarify; never execute-side effects).
- Numeric slots: parsed value RE-CHECKED deterministically (digit table, currency map) — AI may tag, not invent.
- Financial records: two-step (proposal row PENDING → explicit user ✔ → COMMITTED) — Human Gate at UX layer.
- Every rendered decisional message carries footer «تصمیم نهایی با کاربر است.» (renderer asserts presence).

## 5. Phase-6 exit evidence
Fixture suite green + REAL harness A–J (needs blocker ①) + 1 live-session acceptance script.
Wave-6 state: contract FROZEN (EXISTS), parser code NOT yet (MISSING → Phase-6), AI-PAL DESIGNED (A).

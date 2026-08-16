# POSITION MONITORING SPEC (Deliverable I) — 2026-08-11
# Implementation: telegram_ai/positions.py (C Tested) + intent layer bindings. PAPER ledger only.

## 1. Capture (natural language → deterministic record)
User: «من ۵ میلیون تومان این توکن خریدم» → intent BUY_LOG (R-BUY-01), amount=5,000,000 IRT,
token = conversation context (anaphora resolver = session context store in the bot glue; the PARSER
never guesses — needs_context flag test-pinned).
Ledger row (append-only, sha-derived entry_id): chain, address, side=BUY, amount_value,
amount_currency (IRT canonical; ریال normalized تومان), entry ts (UTC + local rendered in messages),
raw_text provenance, intent_rule evidence.
Refusals (by construction): unresolved token ⇒ None; non-positive amount ⇒ None; currency absent ⇒
recorded ONLY after user clarification (UNKNOWN currency in a financial record is not allowed).

## 2. Continuous monitoring (state per position)
- Current value/P&L: from E-01 observations ONLY (latest price_usd, as_of shown honestly)
  — if the token is outside E-01 coverage: state UNKNOWN, never fabricated. Fiat conversion for
  crypto-denominated entries (ETH etc.) requires a free IRT/USDT reference source — **not yet
  sourced (recorded UNKNOWN); P&L for crypto-denominated entries reported in the entry unit only**.
- Drawdown/risk state: from observation series + security verdicts (gates apply to monitored tokens).
- Thesis status: driven by the alert classes (W7_J); every state change carries WHY + evidence.

## 3. Snapshots & reports (when bot is live — blockers ①②)
- On-demand «چند درصد سود دارم؟» → deterministic aggregate of ledger rows × latest observed price.
- Daily digest: positions summary + monitored-token state changes, footer law on decisional lines.

## 4. Maturity
BUY_LOG path: C Tested (unit level). Session context store: A Designed (bot glue). Valuation feed:
B Implemented (observation-backed), limited by collection coverage — honest limitation recorded.
SELL flow (partial exits, realized P&L): A Designed for wave-8 (ledger is append-only; sells will be
companion rows, never edits).

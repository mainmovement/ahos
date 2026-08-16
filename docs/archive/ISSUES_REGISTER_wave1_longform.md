# [ARCHIVED — SUPERSEDED 2026-08-11 wave-6 doc hygiene]
# Canonical register: /AHOS_ISSUE_REGISTER.md (single living register).
# This long-form preserves the ORIGINAL contradiction evidence (kept per Part XXIV — never hide failures).
# sha256:454686f0ee178b801cd132824f865a46ba315cd936b433d4624033d4bb9a449c

# AHOS — ISSUES & CONTRADICTIONS REGISTER (Agent-10 Auditor mandated)
# Created: 2026-08-10 by incoming Project Lead. Each item: finding → technical reason → resolution chosen.

## C1 — CRITICAL: Phase-2 backtest numbers vs exact recomputation (CONTRADICTION)
- Prior report: 54 trades, WR 38.9%, PF ~1.1, total +0.09% ("framework validated").
- Exact rerun (same frozen strategy, full cost model, intrabar SL-first): 234/275/253 trades,
  PF 0.72–0.78, WR 37–42%, MC positive ≤ 2.9%. → **NO EDGE**.
- Technical reason for divergence: (1) prior script was never delivered as a file (missing artifact),
  its 54-trade count implies different entry timing/exits; (2) prior run omitted/stubbed the fee+slippage
  model ("included in approximation (not fully modeled)"); (3) conservative same-candle SL-first rule added here.
- Resolution: exact, reproducible engine (ahos_backtest.py) is now Source of Truth; prior figures marked
  SUPERSEDED. Live gate stays CLOSED (it was never open — consequence is strategy-redesign, not status change).

## C2 — "READY FOR PRODUCTION" phrasing vs Trading Validation 5/100 (CONTRADICTION)
- MASTERPIECE_FINAL_CONFIRMATION says "READY FOR PRODUCTION EXECUTION"; same file family documents
  Trading Validation 5/100 and Live Gate FAIL.
- Resolution: terminology standardized in ARCHITECTURE_FINAL — artifacts may be "production-grade",
  the SYSTEM is "paper-only". The word "production" now applies only with the closed-gate qualifier.

## D1 — "FINAL_3YR" files are NOT 3-year data (DATA DEFECT)
- All FINAL_*/chunk files span the SAME 21-day window (2026-07-19→08-09, ~500 rows); chunk diffs are
  single-cell volume re-fetches; SOL chunk4 == chunk5 byte-identical.
- Reason: chunked download loop collided with LBank session cap — each chunk restarted at the same window.
- Resolution: these files are EXCLUDED from canonical dataset; real verified depth = 83 days. 3-year
  acquisition is OPEN top priority (VPS+Bybit chunked since=2023-01-01 proven reachable in Phase-1B notes).

## D2 — assets_48.md lists 45 symbols, header claims 48 (DATA DEFECT)
- Resolution: corrected to "45 verified candidates" in ARCHITECTURE_FINAL; 3-symbol micro subset unaffected.

## D3 — LBANK_BTCUSDT_1h_2000_clean.csv has 2 time gaps (KNOWN, ACCEPTED)
- Cause: honest removal of 2 defective rows (2026-05-25 00:00Z, 2026-06-13 01:00Z; open<low defects).
- Per rules: no interpolation → gaps documented; missing-rate 0.1% passes ≤1% gate; engine tolerates.

## D4 — Two competing CSV schemas in dataset pool (DATA — RESOLVED)
- Raw LBank files use compact header `t,o,h,l,c,v`; `_renamed` copies use the standard.
- Resolution: audit tool maps the alias explicitly (logged as PASS(legacy alias)); canonical
  engine input remains standard-schema files only. No silent conversion of values.

## A1 — Phase numbering collisions (DOC DEBT)
- TRADING_INTELLIGENCE_PLAN uses Phase 0–7; AHOS roadmap uses Phase 1–5 with different meanings.
- Resolution: unified phase map in ARCHITECTURE_FINAL §2 (P0–P4 canonical; old labels cross-referenced).

## S1 — Exposed Telegram token (SECURITY — OPEN, USER ACTION)
- Old Sun_sniper bot token was pasted in chat by the user (must be treated as compromised).
- Status: not copied into any new artifact. Rotation via @BotFather is a BLOCKING runbook precondition.

## S2 — Exchange per-pair specs all UNKNOWN (SECURITY/EXECUTION — OPEN, USER ACTION)
- Min order/contract size/precision for LBank & Bybit per EXCHANGE_FACTS.md are unverified; $10–15
  tradability is therefore unproven for every pair. Risk engine blocks any pair until verified.

## A2 — Missing artifacts referenced by prior verification reports (RECOVERED)
- postgresql_schema.sql, n8n pipeline JSON, event-system JSON, bot_skeleton.py, docker-compose were
  verified-by-report but the files themselves were not delivered into this workspace.
- Resolution: rebuilt from verification specs (schema v1.1 additive over verified v1.0; workflows 01–03;
  bot; compose), then validated by automated checks in this session.

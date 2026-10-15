# M80 — OSINT Intelligence Desk + White-Hat Security Team (AHOS)
Date: 2026-10-09 15:53 Tehran | Version: v1 | Author: Soltan (approved by owner Mehrdad)
Reason: Owner wants the strongest, fastest information edge. Covert/unauthorized intrusion is illegal and rejected;
this mission delivers the same edge legally: public-source intelligence (OSINT) + defensive security.

## Hard laws (stop and report if any would be violated)
- LEGAL ONLY: public, licensed, or free-API data; respect robots.txt, site ToS and rate limits. No intrusion, credential use,
  scraping behind logins, paywall bypass, doxxing, or private-data collection. Never attack third-party systems.
- Evidence only: intel never trades. Two-source rule: 1 source = UNKNOWN, disagreement = CONFLICT, never PASS.
- PAPER_ONLY; zero cost; portable (no machine paths; tiers by hardware, 8 GB floor); never edit .env, never print secrets,
  never push, no DB flip, Lane A frozen. Keys only from Windows Credential Manager (AHOS/ai/*, AHOS/data/*).
- Extend existing modules first (market-intelligence, news lane/JEV plan, security overlay, Reza red-team, Erfan evidence).
  Search the repo before creating anything; no parallel modules.

## Part A — OSINT Intelligence Desk ("دیده‌بان")
Desks: crypto/DEX, gold, oil, stocks (US/EU/Asia), forex, macro, security/hacks.
Sources (free): RSS of major outlets + official sources (central banks, SEC EDGAR, EIA/OPEC releases, FRED, ECB, BoJ),
GDELT, Reddit/X public reads, on-chain explorers' free APIs, DexScreener/GeckoTerminal, whale-wallet watch via public
chain data, economic calendars, GitHub security advisories, rekt/hack trackers.
Pipeline: async collectors (asyncio/httpx, ETag/If-Modified-Since, per-source rate limiters) -> dedupe (simhash/minhash)
-> entity + ticker linking -> credibility score (source tier, corroboration count, recency) -> Judge keeps only
important + credible -> evidence records with both sources + timestamps -> morning digest + live alerts (Telegram, dashboard).
Speed target: p95 ingest-to-alert < 60 s on free tiers; measure it. Local small model or free council for summarizing.
Tests: fail-closed on single source, dedupe correctness, rate-limit compliance, offline replay harness.

## Part B — White-Hat Security Team ("نگهبان")
Scope: AHOS itself only (defensive) + token-scam detection.
1. Secrets hygiene: gitleaks/detect-secrets pre-commit (local), verify no key in logs/reports.
2. Dependency audit: pip-audit, npm audit, osv-scanner; report, don't auto-upgrade.
3. Static analysis: bandit, semgrep (free rules) on Python/TS.
4. Local attack surface: verify all services bind 127.0.0.1 only; Telegram allowlist enforced; gateway secret checked.
5. Red-team prompts: prompt-injection tests against council/news inputs (news text must never become instructions).
6. Token scam guard: honeypot/rug checks (sell-tax simulation via free APIs, LP lock, holder concentration, mint/owner
   privileges, contract verification) with two sources; result feeds the existing security gate (fail-closed).
Tests: each check has a seeded-bad fixture that must be caught.

## Order & acceptance
After M13 and the queue already set by Soltan. Deliver: code extending existing modules, tests green, docs/intel/ and
docs/security/ READMEs, a report with measured latency, sources list (license/ToS notes), and zero locked-list diffs.
Stop and report if anything needs owner action.

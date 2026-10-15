# M80 v2 — OSINT Intelligence Desk + White-Hat Security Team (AHOS)
Date: 2026-10-09 16:08 Tehran | Version: v2 | Author: Asi (upgrade of Soltan's v1, owner-approved scope)
Reasons v2: cover all markets with precise scoring math, measurable SLAs, and institutional-grade defensive security, all still legal, free, and evidence-only.

## Hard laws (unchanged from v1; stop and report if any would be violated)
LEGAL ONLY: public/licensed/free-API data, robots.txt + ToS + rate limits. No intrusion, credential use, login scraping, paywall bypass,
doxxing, or private data. Never touch third-party systems. Evidence only, so intel never trades. Two-source rule: 1 source = UNKNOWN, disagreement = CONFLICT.
PAPER_ONLY; zero cost; portable; never edit .env or print secrets; never push; no DB flip; Lane A frozen. Keys only from Windows Credential Manager.
Extend existing modules (market-intelligence, news lane/JEV, security overlay, Reza red-team, Erfan evidence). Search before creating.

## Part A — دیده‌بان (OSINT desk)
**Desks & free sources**
- Crypto/DEX: exchange announcements RSS, DexScreener/GeckoTerminal, explorer free APIs, public whale-wallet watch, rekt/hack trackers.
- Gold/Oil: EIA weekly, OPEC press releases, FRED, CFTC Commitments of Traders (free), major outlet RSS.
- Stocks US/EU/Asia: SEC EDGAR (full-text + 8-K/13F/Form 4), ESMA/national regulators' RSS, exchange notices, earnings calendars.
- Forex/Macro: Fed, ECB, BoE, BoJ, PBoC releases; FRED; ECB SDW; economic calendar; GDELT for geopolitics.
- Social: Reddit/X public reads only (rate-limited); weighted low until corroborated.
**Pipeline:** async `httpx` collectors with ETag/If-Modified-Since and per-source token buckets. Dedupe via SimHash (Hamming ≤ 3) + MinHash LSH,
then entity/ticker linking with a local alias table, then scoring, then Judge, then evidence record (both sources, URLs, UTC timestamps, hash), then digest + alerts.
**Scoring math:**
Credibility C = 1 − Π_j (1 − r_j), where r_j is the source-tier reliability (official 0.9, major outlet 0.7, social 0.3).
Recency R = e^(−λΔt), with λ set per desk (macro slow, crypto fast). Impact I comes from a desk rule table (e.g. rate decision, hack > $X, 8-K item 1.03).
Priority = C · R · I. ALERT if Priority ≥ τ_alert AND ≥2 independent sources (different owners), else DIGEST/UNKNOWN.
**SLAs (measure, report):** p95 ingest→alert < 60 s, duplicate rate < 2%, false-alert rate tracked weekly, zero ToS/rate-limit violations.
**Tests:** single-source must be UNKNOWN, conflict must be CONFLICT, dedupe golden set, rate-limit compliance, offline replay harness, injection text treated as data.

## Part B — نگهبان (white-hat, AHOS only + scam detection)
1. Secrets: `gitleaks` + `detect-secrets` pre-commit, log/report redaction tests.
2. Supply chain: `pip-audit`, `npm audit`, `osv-scanner`; lockfiles pinned; generate SBOM (CycloneDX, free). Report, don't auto-upgrade.
3. SAST: `bandit`, `semgrep` community rules (Python/TS), and `ruff` security rules. CI gate fails on high severity.
4. Attack surface: services bind 127.0.0.1 only (test), Telegram allowlist, gateway secret, CSP/headers on the dashboard, no debug in prod.
5. LLM safety: prompt-injection corpus vs council/news inputs, tool-call allowlist, outputs never executed as commands. Reza red-team extends this.
6. Token scam guard: sell-tax sim, LP lock, owner privileges, holders, verification, age, with ≥2 sources and fail-closed into the existing security gate.
7. Integrity: hash-chained evidence log (each record stores prev hash) so tampering is detectable. Signed daily digest checksum.
8. Threat model: STRIDE table for AHOS components in docs/security/, reviewed each mission.
**Tests:** every check has a seeded-bad fixture that must be caught, plus a clean fixture that must pass.

## Order & acceptance
After M13 and Soltan's queue. Deliver: code extending existing modules, green tests, docs/intel/ + docs/security/ READMEs,
measured SLA report, source list with license/ToS notes, zero locked-list diffs. Stop and report if owner action is needed.

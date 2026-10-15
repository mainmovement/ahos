# M59: University (دانشگاه) — research department, source registry, Saturday exams, targeted retraining

## خلاصه فارسی
رئیس دانشگاه فرزانه است؛ ۹ دانشکده با اساتیدی از ایجنت‌های موجود (روشا، کیمیا، آریا، پروانه، بیژن، نیما، تینا/امنیت، مهندسی نرم‌افزار، حسابداری). دپارتمان تحقیق و تفحص (سرپرست شیدا) مقاله، روش، مخزن گیت‌هاب و منابع معتبر هر حوزه را جمع، امتیازدهی و حذف تکراری می‌کند و با رعایت مجوز/قوانین سایت‌ها، به صف آموزش و آزمون ایجنت‌ها می‌دهد. **هر شنبه (به وقت تهران)** همه ایجنت‌ها آزمون می‌دهند؛ حوزه‌های ضعیف آموزش هدفمند و آزمون مجدد می‌گیرند تا نمره به **≥۹۰٪** برسد. سنجش صادقانه: بانک سؤال کنارگذاشته (held-out)، تست کد، و وظایف معامله کاغذی. تاریخچه نمره هر ایجنت ثبت می‌شود. وضعیت: PLANNED تا تست‌ها پاس شوند.

Owner directive 2026-10-07 09:48/09:50 (Mehrdad), newest wins. Extends M15 (University) in OWNER_DIRECTIVE_MISSION_PLAN.md, UNIVERSITY_AND_AGENTS_DISCOVERY.md (University = PLANNED, zero code), M57 §2.10 v3 (structure + UN-1…UN-11 JDs), M58.4 (benchmark) and M58.2 (mistake ledger). PAPER_ONLY; no keys; no push.

## 1. Structure (detail in M57 §2.10)
President فرزانه (#35) · 9 faculties with existing-agent professors · Research & Investigation dept (head شیدا #29: UN-1, UN-7, UN-9) · faculty research staff (UN-2…UN-6) · teaching & exams office (UN-8, UN-10, UN-11) · Failure Analysis هومن (#34) feeds the mistake ledger.

## 2. Source registry (`config/university/sources.yaml`, one file, extensible)
Schema per source: `id, domain[], name, url, category, access: api|rss|manual|dataset, licence, tos_ok: bool, quality: {authority, recency, track_record, citations} 0-5, score, added_by, reviewed_by, status: active|disabled`.
Rules: official API/RSS/open datasets first; no scraping behind logins or against ToS/robots; paywalled = metadata only; licence recorded (MIT/Apache/CC/proprietary); de-dup by canonical URL + SHA-256 of normalised content + near-dup (MinHash ≥0.9); score = weighted quality, sources < 2.5 disabled; every item stores source id + hash (Erfan evidence).
Seed categories (examples; target "hundreds" over time, ≥20 vetted per active domain):
| Domain | Example reputable sources |
|---|---|
| Research (all) | arXiv (q-fin, cs.LG, stat.ML, cs.CR), SSRN, NBER working papers, Papers with Code, Google Scholar alerts (manual) |
| Programming / coding speed | official docs (Python, TypeScript, Node), PEPs, GitHub trending + release notes, Stack Overflow (CC BY-SA), benchmarks (SWE-bench) |
| Writing | style guides (Google developer style, Microsoft style), Plain Language guidelines |
| Banking / accounting | BIS, IMF, central banks (Fed, ECB, CBI), IFRS Foundation, Basel docs |
| Security / white-hat | OWASP (Top 10, ASVS, Cheat Sheets), MITRE ATT&CK/CWE/CVE, NIST, CISA KEV, PortSwigger Academy, HackTricks (lab-only) |
| Gold | World Gold Council, LBMA, COMEX/CME specs, Fed real-yield data (FRED) |
| Oil | EIA, IEA, OPEC MOMR, CFTC COT, CME WTI / ICE Brent specs |
| Stock exchanges / brokers | SEC EDGAR, exchange rulebooks (NYSE, Nasdaq, LSE, TSE, TSETMC), FINRA BrokerCheck, broker fee/margin docs |
| Futures, long/short, leverage | CME education, exchange margin docs, Binance/Bybit/OKX futures & funding docs, Investopedia (intro only), academic papers on leverage/position sizing (Kelly, vol targeting) |
| Profit-taking / risk | peer-reviewed papers, Kimia/Roosha internal protocols, backtest results from UN-6 |
| Crypto / tokens / on-chain | protocol docs, Ethereum/Solana docs, DeFiLlama, Dune (public), Etherscan/Solscan, CoinGecko API, rekt.news, Chainalysis/TRM public reports, M55 sources |
| AI/ML | arXiv, model cards, Hugging Face docs, official lab blogs |
Adding a domain = new `domain` tag + professor + ≥20 sources; no code change.

## 3. Weekly cycle (Asia/Tehran)
- **Thu–Fri:** research dept ingests, de-dups, scores; UN-8 builds training units; UN-10 refreshes banks.
- **Saturday 09:00 Asia/Tehran:** exam for every registered agent (19 + sub-agent templates). Off the trading critical path; budget-capped by Cost/Resource Manager; if Atria quota < 30% the exam runs deterministic sections only and is marked PARTIAL.
- **Grading:** per domain/skill. Pass = **≥ 90% excellent**; 75–89 = remediation; < 75 = remediation + professor review + agent flagged to Ramin/Qasem as "reduced trust" (proposals size-capped) until it passes.
- **Remediation loop:** UN-8 targeted unit for each weak skill → **retest on fresh held-out items** (never the same items) within 48 h → repeat, max 3 retests/week, then escalate to Farzaneh + professor (spec/prompt/data issue, goes to M58.5 pipeline).
- **Honest measurement:** held-out banks (≥30% never trained on, leak check), code tasks graded by pytest in sandbox, paper-trading tasks on replayed historical data graded by PnL/risk rules, free-text by rubric judge + 10% human/professor spot-check. Scores reported with item count and CI; no score without an evidence hash.

## 4. Question-bank format (`data/university/question_bank/<domain>/<skill>.jsonl`)
```json
{"id":"crypto.leverage.0042","domain":"crypto","skill":"leverage_liquidation","type":"mcq|short|code|paper_task","difficulty":1-5,
 "prompt":"...","choices":["..."],"answer":"...","rubric":null,"tests":"tests path for code items","replay":"dataset+window for paper_task",
 "sources":["src_id"],"heldout":true,"version":3,"author":"UN-10","approved_by":"Kimia","created":"2026-10-07"}
```

## 5. Code locations (extend; grep first — University has no code today)
| Piece | Extend | New (only if no home exists) |
|---|---|---|
| Exam runner + grading + score history | `architecture/cognitive/benchmark/` (cases, corpus, evaluator, metrics, thresholds, reproducibility, report) — exam = benchmark suite per agent (**M58.4**) | `architecture/cognitive/benchmark/university_exam.py` |
| Score history / calibration | `architecture/learning/score_ledger.py`, `calibration.py` | — |
| Weak-area → training + memory | `architecture/cognitive/memory/consolidation.py`, `store.py`; mistake ledger via `architecture/evolution/hindsight.py`, `findings.py` (**M58.2**: every mistake → new held-out item) | — |
| Source registry + ingestion | `architecture/knowledge/` (`store.py`, `trust_registry.py`, `oss_pipeline.py`), `engine/oss_audit.py` | `config/university/sources.yaml` |
| Saturday scheduler hook | `architecture/scheduling/engine.py` (`ProductionScheduler`, `ScheduleTask`): task `university_weekly_exam`, cron `0 9 * * SAT` tz `Asia/Tehran`; retest tasks scheduled dynamically; watchdog covers it | — |
| Agent list | `ahos_org/registry.py`, `config/agent_registry.yaml` (one registry) | — |
| Dashboard/Telegram | existing surfaces (part1 §33–36) show score history | — |

## 6. Tests
`tests/test_university_exam.py` (new): sampling only held-out items; leak check fails when an item appears in training; grading reproducible with seed; ≥90 pass / <90 remediation; retest uses fresh items; max-retest escalation; ABSENT ≠ pass.
`tests/test_university_sources.py` (new): schema validation; ToS-false source rejected; de-dup (exact + near-dup); low-score source disabled.
`tests/test_scheduling_university.py` (new) or extend scheduler tests: Saturday 09:00 Asia/Tehran fires once; DST-safe; quota-low → PARTIAL.
Extend `tests/test_cognitive_benchmark.py`, `tests/test_score_ledger_calibration.py`, `tests/test_hindsight_engine.py` (mistake → item).

## 7. Acceptance metrics
- 100% of registered agents examined each Saturday; per-agent score history persisted and queryable (≥ 4 weeks visible).
- Every weak skill gets a remediation unit + retest within 48 h; % of agents at ≥ 90% reported weekly (honest, can be low).
- Leak rate 0; grading reproducibility 100% on seeded rerun; every score has an evidence hash.
- Source registry ≥ 20 vetted sources for each of the first 6 domains (crypto, tokens, futures/leverage, gold, oil, security); 0 ToS violations; dup rate < 2%.
- Mistake ledger (M58.2) entries convert to held-out items; benchmark trend (M58.4) shows exam results.
- Status IMPLEMENTED only when all tests above pass in CI; PAPER_ONLY.

## 8. Mission rows
M59.1 source registry + ingestion · M59.2 question bank + leak guard · M59.3 exam runner/grader + score history · M59.4 Saturday scheduler hook · M59.5 remediation + retest loop (links M58.2/M58.4).

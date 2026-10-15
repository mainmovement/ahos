# M57: Agent sub-teams — organisational design (leads, specialists, load, latency, escalation)

## خلاصه فارسی
- هر ایجنت اصلی (lead) یک تیم کوچک و محدود از زیرایجنت‌ها دارد: اسکنر، تحلیل‌گر، پیشنهاددهنده. زیرایجنت‌ها **فقط پیشنهاد** می‌دهند (اختیار NONE)؛ اجرا فقط از مسیر Execution Gateway + ریسک رامین + کیل‌سوییچ. همه چیز PAPER_ONLY.
- تیم Token Hunter همان تیم M55 است و اینجا دوباره تعریف نمی‌شود.
- جمع پیشنهادی: ۱۰ تیم (۹ دامنه + دانشگاه)، ۴۳ زیرایجنت پایه (سقف ۶۸ با مقیاس‌پذیری خودکارِ محدود). سقف بار: هر lead حداکثر ۶ زیرایجنت، هر زیرایجنت حداکثر ۷۰٪ ظرفیت پایدار.
- «سرعت نور» یعنی پایپ‌لاین رویدادمحور و موازی با اهداف واقعی (مثلاً سیگنال تا پیشنهاد کمتر از ۲ ثانیه برای ممکوین)، نه ادعای غیرواقعی.
- هر زیرایجنت شرح شغل کامل دارد (مأموریت، وظایف، ورودی، خروجی، ابزار، KPI، تحویل، قواعد خطا).
- دانشگاه: رئیس فرزانه، ۹ دانشکده با اساتید (روشا، کیمیا، آریا، پروانه، ...)، دپارتمان تحقیق و تفحص به سرپرستی شیدا، ۱۱ زیرایجنت؛ آزمون هفتگی شنبه‌ها (M59).
- مسیر AGI/ACI/SI در M58 به سازوکارهای عملیاتی قابل ساخت تبدیل شده؛ هر کدام فقط پس از پاس شدن تست «پیاده‌شده» حساب می‌شود.

Owner directive 2026-10-07 (Mehrdad). Status: **SPEC / PLANNED**. Extends (does not replace): M55 (§3 sub-teams), docs/agents/PLANNED_19_AGENT_MAP.md, docs/agents/AGENT_ORGANIZATION_README.md, config/agent_registry.yaml (single registry), docs/architecture/AHOS_AGI_ACI_ARCHITECTURE_CHARTER_v1.0.md, ADR_ACI_001. Newest owner statement wins. Roster changes still go through the human gate ("new agents" = owner approval, OWN-AV-135); sub-agents are **templates under existing leads**, not new top-level agents.

## 1. Rules for every sub-team (IMPLEMENTED: none yet — all PLANNED)
- Authority: sub-agents = NONE (read + propose). Lead = PROPOSE. Execution only via deterministic Execution Gateway → Ramin risk → kill switch. PAPER_ONLY.
- Registered as templates in config/agent_registry.yaml under the lead (`subagent_templates:`), with `max_instances`, `token_budget_per_hour`, `queue_threshold`.
- Bounded autoscale (M55): spawn when lead queue > threshold for > 60 s; despawn after 10 min idle; hard max per lead; every spawn logged to the ledger.
- Every output carries: source ids, timestamp, confidence, evidence hash (Erfan schema).

## 2. Teams and full job descriptions (v2, owner feedback 2026-10-07 09:39)
Base: the 19 agents in docs/agents/PLANNED_19_AGENT_MAP.md + config/agent_registry.yaml (the "18 proposed" list is ignored per owner). Market desks (US, Asia/EU, commodities) are owner-directed desks (M55) under agent.org.08 market-intelligence scope until the owner approves a roster change. Token Hunter = M55 team (duties restated as JDs, not redefined). Sub-agents: authority NONE, PAPER_ONLY.
Name note: owner brief uses Qasem=QA, Reza=red team, Erfan=evidence; some repo docs describe Reza=evidence/reality ladder and Erfan=safety/authority. Roles below are written by function; owner to confirm names.

### 2.1 Token Hunter (M55, lead Kamyar w/ Nima+Tina) — 5 sub-agents
**TH-1 Source adapter worker**
- Mission: Ingest Axiom-class/DexScreener/GMGN/Birdeye public data read-only (M55 §1)
- Duties: normalise new pairs, migrations, volume spikes; attach source reliability (Dana); enforce ToS/rate limits
- Inputs: official public APIs/websockets
- Outputs: normalised `PairEvent` stream
- Tools: adapter interface, cache
- KPIs: p95 ingest<200 ms; uptime ≥99%; 0 ToS violations
- Handoffs: → TH-2, Dana (quality)
- Failure/escalation: source down → mark stale, fail-closed, alert Observability
**TH-2 Launch/pump scanner**
- Mission: Detect early pump candidates (M55 §2)
- Duties: first-minute liquidity, buyer velocity, migration events, social bursts; score 0-100
- Inputs: PairEvent, TH-3 wallet events, narrative tags
- Outputs: scored `Candidate`
- Tools: rules engine, small model
- KPIs: precision@top10 vs 1h outcome; recall of later pumps
- Handoffs: → Tina gate (TH-4)
- Failure/escalation: score model drift → fall back to rules, notify Aria
**TH-3 Smart-wallet tracker**
- Mission: Track profitable/whale wallets entering tokens
- Duties: maintain wallet watchlist with hit-rate; emit entries/exits; detect bundled buys
- Inputs: chain RPC/indexer (read-only)
- Outputs: `WalletEvent`
- Tools: indexer client
- KPIs: entry-signal lead time; watchlist hit rate
- Handoffs: → TH-2, Nima
- Failure/escalation: RPC lag >5 s → degrade flag
**TH-4 Scam gate worker (Tina template)**
- Mission: Run Tina's mandatory checks per candidate
- Duties: mint/freeze authority, LP lock/burn, honeypot sim, top-holder concentration, dev history
- Inputs: Candidate + contract data
- Outputs: PASS/FAIL/UNKNOWN + reasons
- Tools: static analyser, sim
- KPIs: rug-avoided rate; false-pass = 0 target; p95<3 s
- Handoffs: → TH-5 only on PASS
- Failure/escalation: UNKNOWN=FAIL; backlog>20 → autoscale (max 4)
**TH-5 Paper proposer**
- Mission: Turn PASSed candidates into typed paper proposals
- Duties: size within memecoin slice; SL/TP ladder; daily loss cap check; reason text
- Inputs: PASS candidate, Ramin limits
- Outputs: `Proposal` to lead queue
- Tools: proposal schema
- KPIs: proposal→decision latency; paper PnL; hit rate
- Handoffs: → Kamyar → Gateway/Ramin
- Failure/escalation: cap hit → stop proposing, log

### 2.2 Crypto Market Intelligence (Kamyar, agent.org.08) — 4 sub-agents
**CM-1 Majors scanner**
- Mission: Watch BTC/ETH/SOL + top-50 for anomalies
- Duties: price/funding/OI/basis anomaly detection; liquidation clusters
- Inputs: exchange public streams
- Outputs: scored `MarketEvent`
- Tools: stream client, z-score rules
- KPIs: p95<200 ms; false-alarm rate
- Handoffs: → CM-2, CM-4
- Failure/escalation: stream gap → stale flag
**CM-2 Regime analyst**
- Mission: Single source of truth for market regime
- Duties: classify trend/vol regime; correlation shifts; publish regime changes
- Inputs: MarketEvent, Kimia quant features
- Outputs: `Regime` label + confidence
- Tools: LLM + quant features
- KPIs: regime accuracy vs realised vol; stability (no flapping)
- Handoffs: → all crypto proposers, Ramin
- Failure/escalation: low confidence → 'UNCERTAIN' (proposers shrink size)
**CM-3 Narrative watcher**
- Mission: Detect news/social narrative bursts
- Duties: cluster headlines/posts; tag tokens/sectors; flag manipulation
- Inputs: public feeds via Narrative Intelligence
- Outputs: `NarrativeTag`
- Tools: embedding clustering
- KPIs: lead time vs price move; spam filtered %
- Handoffs: → CM-2, TH-2
- Failure/escalation: tainted content → no tool actions (prompt-injection rule)
**CM-4 Crypto proposer**
- Mission: Typed paper proposals for majors
- Duties: combine events+regime; entry/exit/size
- Inputs: CM-1..3
- Outputs: `Proposal`
- Tools: schema
- KPIs: paper Sharpe; proposal acceptance rate
- Handoffs: → Kamyar
- Failure/escalation: regime UNCERTAIN → reduced size only

### 2.3 On-Chain Intelligence (Nima, agent.org.09) — 4 sub-agents
**OC-1 New-pair/mempool watcher**
- Mission: Earliest on-chain view of launches and large txs
- Duties: decode pool creations, large swaps, LP adds/removes
- Inputs: RPC/indexer read-only
- Outputs: `ChainEvent`
- Tools: decoder
- KPIs: detect latency <2 blocks
- Handoffs: → TH-2, OC-4
- Failure/escalation: node lag → switch provider
**OC-2 Whale & smart-money tracker**
- Mission: Cluster and label wallets
- Duties: entity clustering, CEX flows, labels with confidence
- Inputs: ChainEvent, public labels
- Outputs: `WalletLabel`
- Tools: graph clustering
- KPIs: label precision (spot-checked)
- Handoffs: → TH-3, OC-4
- Failure/escalation: conflicting labels → mark unverified
**OC-3 Liquidity/exitability checker**
- Mission: Can we exit at size? (registry Liquidity/Exitability)
- Duties: depth, slippage at size, LP concentration
- Inputs: pool state
- Outputs: `ExitabilityScore`
- Tools: AMM math
- KPIs: slippage forecast error
- Handoffs: → Tina, proposers
- Failure/escalation: insufficient data → exitability=0
**OC-4 Flow analyst**
- Mission: Interpret flows into signals
- Duties: net flows, accumulation/distribution, bridge flows
- Inputs: OC-1..3
- Outputs: `FlowSignal`
- Tools: LLM summary
- KPIs: signal hit rate
- Handoffs: → Kamyar, CM-2
- Failure/escalation: —

### 2.4 Token Security / Scam (Tina, agent.org.10) — 3 sub-agents
**TS-1 Contract static checker**
- Mission: Find dangerous contract powers
- Duties: mint/freeze, proxy/upgradeable, owner privileges, blacklist, fee traps
- Inputs: verified source/bytecode
- Outputs: findings list
- Tools: static analysis
- KPIs: false-pass=0 on scam corpus; p95<1 s
- Handoffs: → TS gate verdict
- Failure/escalation: unverified source → UNKNOWN
**TS-2 Honeypot simulator**
- Mission: Prove sell is possible
- Duties: simulate buy+sell, tax measurement
- Inputs: forked state/sim API
- Outputs: sim result
- Tools: simulator
- KPIs: sim p95<3 s; corpus recall
- Handoffs: → verdict
- Failure/escalation: sim error → UNKNOWN(=FAIL)
**TS-3 Holder/dev & bundle detector**
- Mission: Detect insider concentration
- Duties: top-holder %, dev wallet history, bundled launch buys, LP owner
- Inputs: OC-2 labels, chain data
- Outputs: risk flags
- Tools: graph
- KPIs: rug-avoided rate
- Handoffs: → verdict, Reza corpus
- Failure/escalation: —

### 2.5 US Stocks desk (market desk under agent.org.08 scope, M55) — 4 sub-agents
**US-1 Opportunity scanner**
- Mission: Keep scanning while lead is busy (M55 example)
- Duties: screen gaps, volume, breakouts, unusual options (public)
- Inputs: market data API
- Outputs: scored queue
- Tools: screener
- KPIs: missed-opportunity count while lead busy = 0
- Handoffs: → US-4
- Failure/escalation: queue>50 → expire low scores with log
**US-2 Earnings/filings analyst**
- Mission: Fundamental events
- Duties: parse 8-K/10-Q/earnings, guidance deltas
- Inputs: SEC EDGAR, transcripts
- Outputs: `FundamentalNote`
- Tools: LLM + parser
- KPIs: surprise-direction accuracy
- Handoffs: → US-4
- Failure/escalation: parse failure → no signal
**US-3 Technical analyst**
- Mission: Price-structure view
- Duties: levels, trend, volatility, relative strength
- Inputs: OHLCV
- Outputs: `TechNote`
- Tools: indicators lib
- KPIs: setup hit rate
- Handoffs: → US-4
- Failure/escalation: —
**US-4 Equity proposer**
- Mission: Typed paper proposals
- Duties: merge notes, size, SL/TP, hours check
- Inputs: US-1..3, Ramin limits
- Outputs: `Proposal`
- Tools: schema
- KPIs: paper PnL, acceptance
- Handoffs: → lead
- Failure/escalation: market closed → queue only

### 2.6 Asian & European Stocks desk — 3 sub-agents
**AE-1 Asia session scanner**
- Mission: Screen Asia sessions (market hours only)
- Duties: gaps, sector moves, ADR divergence
- Inputs: public data
- Outputs: scored queue
- Tools: screener
- KPIs: coverage of top movers
- Handoffs: → lead
- Failure/escalation: off-hours → sleep
**AE-2 Europe session scanner**
- Mission: Same for EU sessions
- Duties: as AE-1
- Inputs: public data
- Outputs: scored queue
- Tools: screener
- KPIs: as AE-1
- Handoffs: → lead
- Failure/escalation: off-hours → sleep
**AE-3 Macro/FX analyst**
- Mission: Cross-region macro and FX context
- Duties: rates, FX, central-bank calendar
- Inputs: public macro feeds
- Outputs: `MacroNote`
- Tools: LLM
- KPIs: event-impact accuracy
- Handoffs: → desks, commodities
- Failure/escalation: —

### 2.7 Commodities desk (gold/oil) — 3 sub-agents
**CO-1 Price/curve scanner**
- Mission: Spot/futures curve anomalies
- Duties: contango/backwardation shifts, breakouts
- Inputs: public futures data
- Outputs: scored events
- Tools: rules
- KPIs: false-alarm rate
- Handoffs: → lead
- Failure/escalation: —
**CO-2 Macro & geopolitics analyst**
- Mission: Supply/demand shocks
- Duties: OPEC, conflicts, USD, real yields
- Inputs: news, AE-3
- Outputs: `MacroNote`
- Tools: LLM
- KPIs: lead time vs moves
- Handoffs: → lead
- Failure/escalation: tainted feed → no tools
**CO-3 Inventory/calendar watcher**
- Mission: Scheduled reports
- Duties: EIA/API inventories, CFTC COT, calendar alerts
- Inputs: public releases
- Outputs: `CalendarEvent`
- Tools: scheduler
- KPIs: 0 missed releases
- Handoffs: → lead, CO-2
- Failure/escalation: —

### 2.8 Risk (Ramin, agent.org.11) — 3 sub-agents
**RK-1 Exposure aggregator**
- Mission: Single portfolio exposure view
- Duties: aggregate by asset/sector/chain/correlation
- Inputs: ledger, positions
- Outputs: `Exposure`
- Tools: deterministic
- KPIs: freshness <1 s
- Handoffs: → Ramin, Gateway
- Failure/escalation: stale → Gateway rejects new proposals
**RK-2 Limit/stop monitor**
- Mission: Enforce stops and caps (deterministic, never LLM-only)
- Duties: per-trade/day/slice caps, stop triggers, kill-switch signal
- Inputs: Exposure, prices
- Outputs: breach events, HALT
- Tools: rules engine
- KPIs: breach→action <1 s; 0 missed breaches
- Handoffs: → kill switch, Ramin
- Failure/escalation: monitor dead → HALT (fail-closed)
**RK-3 Scenario/stress analyst**
- Mission: What-if losses
- Duties: stress tests, correlation spikes, liquidity shocks
- Inputs: Exposure, Kimia models
- Outputs: `StressReport`
- Tools: sim
- KPIs: daily report on time
- Handoffs: → Ramin
- Failure/escalation: —

### 2.9 Assurance triad (QA / red team / evidence) — 3 sub-agents
**AS-1 QA test-runner & acceptance checker**
- Mission: Verify every change against acceptance
- Duties: run tests, check acceptance criteria, regression
- Inputs: repo, mission specs
- Outputs: QA verdict + logs
- Tools: pytest, CI
- KPIs: escaped-defect rate
- Handoffs: → QA lead sign-off
- Failure/escalation: flaky → quarantine + ticket
**AS-2 Red-team attack generator**
- Mission: Attack proposals and code
- Duties: generate attack cases, scam corpus, prompt-injection tests
- Inputs: changes, proposals
- Outputs: attack report
- Tools: fuzzers, M56 arena (high-stakes)
- KPIs: findings per review; 0 critical escaped
- Handoffs: → red-team lead
- Failure/escalation: critical → block merge
**AS-3 Provenance verifier**
- Mission: Every claim has evidence
- Duties: check sources, hashes, evidence ledger entries
- Inputs: outputs, ledger
- Outputs: evidence verdict
- Tools: hash check
- KPIs: unsupported-claim rate
- Handoffs: → evidence lead
- Failure/escalation: missing evidence → claim downgraded to UNVERIFIED

### 2.10 University / دانشگاه — v3 (owner clarification 2026-10-07 09:48; supersedes v2 lead)
Extends reports/grok/UNIVERSITY_AND_AGENTS_DISCOVERY.md (University = PLANNED, mission plan M15) and the AHOS_AUTONOMOUS_VISION.md roster (#35 فرزانه, #29 شیدا, #34 هومن). Newest owner statement wins: **President (رئیس) = فرزانه / Farzaneh (#35)** (was "Dean"). Reports to the owner via the existing chain (آرش + عرفان). Professors are **existing agents wearing a faculty hat** — no new top-level agents (new agents = owner gate).

| Faculty | Professor (استاد) | Subjects (extensible list in source registry) |
|---|---|---|
| Methodology & Statistics | روشا Roosha (#6) | backtest protocol, walk-forward, CPCV, PBO, deflated Sharpe, causal inference |
| Quant & Trading | کیمیا Kimia (#12) | stock exchanges, brokers, futures, long/short, leverage types & sizing, profit-taking, risk/reward |
| AI / ML | آریا Aria (#13) | LLMs, time-series models, evaluation |
| Writing & Prompting | پروانه Parvaneh (#15) | writing quality, reports, prompt engineering, injection defence |
| Software Engineering & Coding Speed | Agent Runtime Engineering (agent.org.14) | programming, code speed, testing, Python/TS |
| Security & White-hat | Security Architect (agent.org.03) + تینا Tina (#10) | appsec, ethical hacking theory (lab-only, no live targets), token/scam security |
| Commodities | بیژن Bijan (#28) | gold, oil, charts, macro drivers |
| Crypto, Tokens & On-chain | نیما Nima (#9) | crypto, tokens, DEX/on-chain, memecoins (M55) |
| Banking & Accounting | Accounting Agent (part1 §29) | banking, accounting, FX, rates |
Failure Analysis (هومن Hooman #34) feeds every faculty from the mistake ledger (M58.2).

**Research & Investigation department** (head: شیدا Shida #29, GitHub Intelligence): sub-agents UN-1…UN-7 + UN-9 collect, score and de-dup material from the source registry (M59 §2), then UN-8/UN-10 turn it into training units and exam questions for every agent. University sub-agents below (11 base / 14 max).

**The 8 v2 specialists are kept (owner 09:50) and placed in the structure:** Research & Investigation dept (under Shida): UN-1 arXiv/q-fin miner, UN-7 GitHub SOTA scout, UN-9 source curator. Faculty research staff: UN-2 ML/time-series → Aria's faculty; UN-3 microstructure → Nima's faculty; UN-4 RL/strategy → Kimia's faculty; UN-5 causal/stats and UN-6 replication → Roosha's faculty. Teaching & exams office (reports to Farzaneh): UN-8 curriculum trainer (remediation), UN-10 question-bank builder, UN-11 proctor/grader.

**UN-1 arXiv/q-fin paper miner**
- Mission: Find relevant new research weekly
- Duties: query arXiv q-fin/cs.LG/stat.ML, SSRN abstracts; rank by relevance+rigor
- Inputs: arXiv API, SSRN public
- Outputs: ranked `PaperCard` (claim, data, method)
- Tools: arXiv API, embeddings
- KPIs: ≥20 cards/week; precision of 'relevant' ≥70% (Roosha spot-check)
- Handoffs: → UN-2..5 by topic
- Failure/escalation: —
**UN-2 ML/time-series research**
- Mission: Evaluate forecasting/ML methods for AHOS
- Duties: assess models (TS foundation models, GBMs), leakage risks
- Inputs: PaperCards, AHOS data
- Outputs: `MethodBrief` + experiment plan
- Tools: notebooks
- KPIs: briefs adopted into experiments
- Handoffs: → Aria, UN-6
- Failure/escalation: —
**UN-3 Market-microstructure research**
- Mission: Order flow, AMM/DEX mechanics, MEV
- Duties: study slippage, liquidity, MEV/sandwich risk
- Inputs: papers, chain data
- Outputs: `MethodBrief`
- Tools: sim
- KPIs: improvement in exitability forecast
- Handoffs: → Nima, OC-3
- Failure/escalation: —
**UN-4 RL/strategy research**
- Mission: Strategy design incl. RL/bandits
- Duties: design candidate strategies for tournament (M58.3)
- Inputs: papers, backtests
- Outputs: strategy specs
- Tools: backtest engine
- KPIs: strategies passing tournament gate
- Handoffs: → Kimia, M58.3
- Failure/escalation: no overfit checks → reject
**UN-5 Causal inference & statistics**
- Mission: Guard against false discoveries
- Duties: multiple-testing correction, deflated Sharpe, causal checks
- Inputs: experiment results
- Outputs: `StatsVerdict`
- Tools: statsmodels
- KPIs: false-discovery rate
- Handoffs: → Roosha, Kimia
- Failure/escalation: weak evidence → NOT_SUPPORTED
**UN-6 Replication / backtest-of-papers**
- Mission: Reproduce paper claims on our data
- Duties: replicate, out-of-sample, cost-inclusive
- Inputs: PaperCards, data
- Outputs: replication report (REPLICATED/FAILED)
- Tools: backtest engine
- KPIs: replication rate reported honestly
- Handoffs: → Kimia, Erfan evidence
- Failure/escalation: can't reproduce → FAILED, never adopted
**UN-7 GitHub SOTA repo scout**
- Mission: Find maintained open-source tools
- Duties: scan repos, licences, activity, security
- Inputs: GitHub search
- Outputs: `RepoCard` (licence, risk)
- Tools: GitHub API
- KPIs: adopted repos with licence OK=100%
- Handoffs: → Open-Source Capability Intelligence, Aria
- Failure/escalation: copyleft/unknown licence → flag
**UN-8 Curriculum / self-learning trainer**
- Mission: Turn mistakes and research into training material
- Duties: build eval sets from mistake ledger (M58.2), update prompts/playbooks (proposals)
- Inputs: mistake ledger, briefs
- Outputs: curriculum + prompt-change proposals
- Tools: eval harness
- KPIs: benchmark gain per cycle (M58.4)
- Handoffs: → M58.5 pipeline
- Failure/escalation: regression → reject

**UN-9 Source-registry curator**
- Mission: Maintain the per-domain source registry (M59 §2)
- Duties: add/retire sources; score quality (authority, recency, citations, track record); de-dup by URL+content hash; record licence/ToS and allowed access method (API/RSS/manual)
- Inputs: owner/professor nominations, UN-1/UN-7 discoveries
- Outputs: `config/university/sources.yaml` entries
- Tools: hashing, robots/ToS check, licence detector
- KPIs: ≥ 20 vetted sources per active domain; dup rate < 2%; 0 ToS violations
- Handoffs: → UN-1..UN-7 (crawl list), Erfan (evidence)
- Failure/escalation: unclear licence/ToS → source disabled until professor review

**UN-10 Question-bank builder**
- Mission: Build held-out exam banks per agent and domain
- Duties: write MCQ/short-answer/code/paper-task items with answer keys + source refs; keep ≥ 30% items held-out (never used in training); rotate items; tag difficulty & skill
- Inputs: training units, mistake ledger (M58.2), professor review
- Outputs: `data/university/question_bank/<domain>/*.jsonl` (M59 §4 format)
- Tools: generator + professor approval
- KPIs: bank size ≥ 200 items/domain; leak rate (held-out item seen in training) = 0
- Handoffs: → UN-11, professors
- Failure/escalation: item disputed → quarantined, not scored

**UN-11 Exam proctor & grader (deterministic)**
- Mission: Run the Saturday exam and grade honestly
- Duties: sample held-out items; run code tests in sandbox; run paper-trading tasks on replayed data; grade with keys/tests (LLM-judge only for free text, with rubric + spot-check); write score history
- Inputs: question bank, agent endpoints
- Outputs: `ExamResult` rows, weak-area list
- Tools: pytest sandbox, paper replay, rubric judge
- KPIs: 100% agents examined each Saturday; grading reproducible (same seed → same score)
- Handoffs: → UN-8 remediation, Farzaneh report, M58.4 benchmark
- Failure/escalation: agent unavailable → marked ABSENT (not passed); grader error → exam void + rerun

**Why 11 University sub-agents (v3):** UN-9/10/11 added for the owner's weekly-exam requirement (source curation, item writing and grading must be separate so no agent writes and grades its own exam). Original rationale for UN-1..8: one per distinct research discipline that feeds a different consumer (Aria ML, Nima microstructure, Kimia strategy/stats, Roosha method). Fewer would merge statistics with strategy (conflict of interest: the agent that proposes a strategy must not certify its significance); more would create overlap (e.g. separate DeFi vs CEX microstructure) with no evidence of load. Max 14 (UN-1, UN-6, UN-10, UN-11 may scale to 2 during paper backlog). Throughput is weekly, not real-time — University is never on the trading critical path.

### Totals
| | Teams | Base sub-agents | Max |
|---|---|---|---|
| Domain + assurance | 9 | 32 | 54 |
| University | 1 | 11 | 14 |
| **Total** | **10** | **43** | **68** |
Supporting agents (Data/Dana, Memory, Observability, Cost/Resource Manager, Governance) get **no** sub-teams initially — they serve all teams; add only with evidence of overload.

## 3. Load limits
- Per sub-agent: ≤ 70% sustained utilisation, ≤ 1 concurrent LLM call (scanners: N streams but bounded CPU), queue depth ≤ 50.
- Per lead: ≤ 6 sub-agents direct (span of control); lead handles ≤ 3 open decisions; overflow is queued with scores, never dropped silently (drop = logged).
- Global: Cost/Resource Manager enforces hourly token budget per team; when Atria quota < 30%, analysts degrade to deterministic scanners only; < 10% → HOLD (proposals only from deterministic rules).
- Backpressure: queues bounded; oldest low-score items expire with a log entry.

## 4. Latency targets ("speed of light" = engineering, realistic)
Event-driven (websockets/streams + in-process queue/pub-sub), parallel fan-out, deterministic checks before LLM calls, caching.
| Path | Target p95 |
|---|---|
| Stream event → scanner score | < 200 ms |
| Tina deterministic checks (static + cached) | < 1 s; honeypot sim < 3 s |
| Memecoin signal → paper proposal at lead | < 2 s without LLM; < 8 s with one analyst LLM call |
| Stocks/commodities opportunity → proposal | < 30 s |
| Proposal → Gateway + Ramin decision (deterministic) | < 100 ms |
| Kill switch propagation | < 1 s |
LLM calls are the dominant latency (seconds); they are kept off the critical path where a deterministic rule suffices. Targets are to be measured, not claimed.

## 5. Escalation & coordination
- Sub-agent → lead (typed proposal). Lead → Execution Gateway (paper) or → peer lead (cross-domain, e.g. Nima → Tina).
- Conflict between leads → Consensus/Disagreement Engine; unresolved high-stakes → Multi-Mind Council / M56 arena (proposal only) → Qasem/Reza/Erfan → human gate if rules/money/tiers/new agents.
- Any FAIL from Tina or Ramin is final for that proposal; no override by sub-agents or arena.
- Heartbeats to Observability every 10 s; missed 3 → lead marks sub-agent dead and respawns within the bound.

## 6. AGI / ACI / SI path
Now operational as buildable missions in **M58-operational-agi-aci-si-loops.md** (self-eval, mistake ledger, strategy tournament, capability benchmark, self-improvement pipeline, cross-domain transfer). The long-horizon AGI/ACI/SI goal itself remains a north-star VISION; each M58 mechanism counts as IMPLEMENTED only once its tests pass.

## 7. Acceptance (when implemented)
- Registry: sub-agent templates under existing leads with max_instances/budget/threshold; a test rejects unbounded spawn.
- Orchestrator test: lead busy → scanner still captures and queues a second opportunity (M55 test reused).
- Load test (mocked streams) shows backpressure + logged drops; latency table measured and reported honestly.
- Tina UNKNOWN = FAIL test; Ramin veto test; quota-degradation test.
- PAPER_ONLY, no keys, no push; 19-agent sign-off.

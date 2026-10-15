<!-- Tehran: 2026-10-09 16:20 (UTC+3:30) | Version: v1 | Author: Soltan-review | Reason: the owner asked to prevent duplicate and parallel conflicting work. -->
# DEDUP / MERGE MAP for the queue_2050 and 2026-10-09 docs (v1)
Status: PLAN ONLY. Read-only review; no queue, checkpoint, or code file was edited. Claude (PID 9580) is in night-run step 4 (M12); steps 1-3 are DONE (b5929a7, c0c145f, bd93360).
Method: read the queue (CLAUDE_AUTOPILOT_QUEUE.md), the mission specs, the vision mission table (§ M14-M52 rows, M15.6-11, M28-M34, M36), the Astra plan §2.3/§6, the Soltan 04:50 log, and every queue_2050 doc. I also ran a git grep over code (Lane A excluded).
Classes: DUPLICATE = drop the new item and use the existing one. OVERLAP = merge into the existing mission as an addendum. NEW = keep it under the next free id. SUPERSEDES = the newer version replaces the old.
Free ids: no M61-M69 exists anywhere in the repo. M60.x (Astra), M70.x (Aji), and M80 are already reserved by their docs, and those ids are kept.
Use: this file is an input for M34.1 (coherence audit). It is not a substitute for that audit.

## 0. Code facts found (git grep, read-only)
- LLM layer: architecture/ai/clients.py and router.py already reference ollama, groq, openrouter, and github_models. credential_store.py and wincred_reader.py exist, and so do council_live.py and debate_council.py (CC-3).
- News: architecture/intel/news.py, catalyst.py, regimes.py, market_structure.py, and exitability.py exist. There is no market-intelligence/ dir.
- Security: architecture/security/gate.py, hygiene.py, and contract_analysis.py exist. No gitleaks, bandit, semgrep, or osv-scanner was found.
- Quant: research/quant_metrics.py has Kelly. strategy_lab/validation_engine.py has walk-forward and purged k-fold. No DSR, PBO, or HRP code was found.
- Self-*: architecture/cognitive (benchmark, sandbox, evolution_gate), architecture/evolution (engine, findings, hindsight, selection, validate), and tests/test_health_manager.py exist. No dspy, textgrad, inspect_ai, or promptfoo was found.
- No runtime hardware probe was found (psutil.virtual_memory, VRAM). The existing CLAUDE.md and AGENTS.md mean `/init` must NOT be run.
- Telegram: telegram_ai/service.py emits EMERGENCY_FALLBACK_ONLY. The G11 tooling is scripts/windows_g11_telegram_e2e_helper.ps1 plus reports/grok/G11_LIVE_E2E_RUNBOOK.md.

## 1. Map: item -> existing match -> class -> action
| # | New item (source) | Existing match | Class | Action |
|---|---|---|---|---|
| 1 | Telegram bridge -> decision core fix + G11 E2E (Soltan log 15:00) | M11.4 (DONE, health only), M35.3 (BLOCKED_OWNER, token rotation), G11 runbook, telegram_ai/service.py | NEW | **M61**. Find why the bridge returns EMERGENCY_FALLBACK_ONLY and fix it in telegram_ai/gateway. No token change and no .env access. Prepare the G11 transcript at reports/telegram_e2e_<UTC>.md, where the owner sends one message. This does not unblock M35.3. |
| 2 | M-PORT portable package + post-move health check (Soltan log 04:58) | Launcher M11.x, M10 (DB flip forbidden), M-D12 portable note, M70.1 probe | NEW | **M62**. Build a portable Windows bundle (Python, Node, deps, shortcut, data-move guide, health script). Secrets go back into Credential Manager by the owner. It consumes the M70.1 probe and must not write a second probe. |
| 3 | CLAUDE_SKILLS_v1 (Claude Code tooling) | M52 = AHOS-internal marketplace (different scope); Soltan 15:31 vetting | NEW | **M63** (ops). Install only between Claude sessions, never during PID 9580 work. Claude Code Setup (local scope) is approved. Task Observer is optional and needs its source checked first. Context7, Playwright MCP, and Sequential Thinking need Soltan approval. Skip `/init` because CLAUDE.md exists; extend that file instead. |
| 4 | Free council wiring: Gemini + Groq + OpenRouter :free + GitHub Models (Soltan 14:02-14:19) | M35.1 (router + council), M15/M15.6-11, M37 (registry + $0 cap), clients.py/router.py/credential_store.py, vision rule "no parallel council" | OVERLAP | Make it an addendum to **M35.1**. Read keys from AHOS/ai/* in Credential Manager. Allow only :free models. Votes are advisory, and the Python brain decides. Do not create a new council module. |
| 5 | Market data keys Finnhub / TwelveData / FRED (Soltan 14:33-14:48) | M19 desks, two-source rule, identity resolver | OVERLAP | Make it an addendum to **M19** as source pairs inside the existing evidence path. |
| 6 | Two-source rule, all markets (حافظه_ادامه/*قانون_شاهد*) | multi_source resolver (373516e, b5929a7) | OVERLAP | This is a binding law, not a mission. Add it as an acceptance line in every mission. M34.2 records one verifier owner and M34.4 adds a CI lint against a second verifier. |
| 7 | JEV news desk idea (حافظه_ادامه/*JEV*) | M80 v2 Part A (same desks, judge, and digest), M18 news (Negar), architecture/intel/news.py | DUPLICATE | Drop it as a separate item; see row 8. The JEV-style bottom strip becomes part of the **M-D7** telemetry strips. |
| 8 | M80 v2 Part A, "Didehban" OSINT desk | M18 (news/Negar), M33.7 (legal OSINT for tokens), M44 (science radar), intel/news.py and catalyst.py, TS v2 §10/§11 | OVERLAP | Make this ONE news/intel desk as addendum **M18.N**, with M80-A v2 as its spec. M33.7 reuses the same collectors, and M44 stays science-only. Output is evidence only and never trades. |
| 9 | M80 v2 B1 secrets / B3 SAST / B4 attack surface / B5 LLM safety / B8 STRIDE | security/hygiene.py SECRET_RULES, M31.6, M35.1 injection defence, Reza red team | NEW (residual) | **M64**, "Negahban" defensive hardening. It extends hygiene.py, and B5 extends the M35.1 injection defence. The CI gate lives next to the M34.4 lint. |
| 10 | M80 v2 B2 supply chain (pip-audit, osv, SBOM) | M48 (OSV/pip-audit, hash-pin, rollback) | OVERLAP | Make it an addendum to **M48**; SBOM is the only new part. |
| 11 | M80 v2 B6 token scam guard + TS v2 §4 token safety | M33.4 security gate v2 (GoPlus, Honeypot.is, RugCheck), M33.5 fork sim, security/gate.py | DUPLICATE | Drop it and use **M33.4/M33.5**. |
| 12 | M80 v2 B7 hash-chained evidence log | M42 (hash-chained single ledger), mission/ledger.py | DUPLICATE | Drop it and use **M42**. Add the signed daily digest checksum to M42. |
| 13 | TS v2 §0 universe + free data pairs | M19 desks, row 5 | OVERLAP | Addendum to **M19**. yfinance is for research only and always gets a second source. |
| 14 | TS v2 §1 regime (HMM, PELT) | intel/regimes.py, M24 rotation layer, M33.22 M-REGIME | OVERLAP | Addendum to **M24**, extending regimes.py. Filtered states only, with no lookahead. |
| 15 | TS v2 §2 multi-timeframe confluence | features/extractor.py, M24 | OVERLAP | Addendum to **M24** (signal layer). |
| 16 | TS v2 §3 order flow / liquidity gate | intel/market_structure.py and exitability.py, M21, M38 | OVERLAP | Addendum to **M21** (risk gate). |
| 17 | TS v2 §5 vol sizing, §6 fractional Kelly, §12 ruin + kill switches | M21 (Kelly, vol targeting, DD ladder, kill), M39, research/quant_metrics.py, M60.5 risk cap | OVERLAP | Addendum to **M21**, with M39 owning the kill switch. Extend quant_metrics.py. |
| 18 | TS v2 §7 HRP/ERC allocation + paper double-entry transfers | M24 allocator, M28.6 HRP, M42 ledger, M40 treasury | OVERLAP | Allocation goes to **M24**/M28.6 and the paper double-entry goes to **M42**. Never make real transfers. |
| 19 | TS v2 §8 walk-forward + DSR/PBO, purged CV | M28.1 stats library (DSR, PBO/CSCV), M25 gate evaluator, strategy_lab/validation_engine.py | DUPLICATE | Drop it and use **M28.1 + M25**, extending validation_engine.py. zipline/bt are not needed. |
| 20 | TS v2 §9 calibrated ensemble | M15.10 log-odds aggregation, learning/calibration.py, M60.3 | OVERLAP | Addendum to **M15.10**. Calibration extends the same calibration.py file. |
| 21 | TS v2 §10 news sentiment, §11 price gaps | Row 8 (M18.N); two-source CONFLICT; Soltan 14:42 gaps-as-evidence | OVERLAP | §10 merges into **M18.N**. §11 becomes a CONFLICT/DATA_ERROR evidence check under the **M19** two-source path and never auto-trades. |
| 22 | TS v2 §13 performance evals + promotion gate | research/quant_metrics.py, M25 gate evaluator, M17 panel, vision §11.0 T1->T2 | OVERLAP | Addendum to **M25**. The gate needs at least 30 closed paper trades, which is consistent with M13. |
| 23 | AHOS_TRADING_SKILLS_v2 (whole doc) | AHOS_TRADING_SKILLS_v1 | SUPERSEDES | v2 replaces v1. Its build order 13>5>12>4>8>7>1>2>6>3>9>10>11 maps to M25>M21>M21>M33.4>M28.1>M24>M24>M24>M21>M21>M15.10>M18.N>M19. |
| 24 | CLAUDE_MISSION_M80_OSINT_WHITEHAT_v2 | M80 v1 | SUPERSEDES | v2 replaces v1. Split per rows 8-12. |
| 25 | CLAUDE_MISSION_AGI_v2 (M70 v2) | M70 v1 (CLAUDE_MISSION_AGI_RESEARCH_M70.md + 05-20 folder copy) | SUPERSEDES | v2 replaces v1. |
| 26 | M70 docs/agi/SOURCES.md + AGI_ROADMAP L0-L6 | M58 (AGI/ACI/SI loops), Astra §5.3 E0-E? phases, vision §10 | OVERLAP | Addendum to **M58**. L0-L6 must map onto the M58 and E-phase ladder, with no second ladder. |
| 27 | M70.1 hardware probe + tier selector | none in code; M-D5 browser probe; M-PORT | NEW | Keep the id **M70.1**. One Python probe serves M62 and the model tiers. The M-D5 GPU probe stays browser-side and reads the same tier names. |
| 28 | M70.2 llama.cpp/Ollama adapter + grammar output | clients.py/router.py (ollama present), config/offline_mode.py, M35.1, M37 | OVERLAP | Merge with row 4 into **M35.1**, as one LLM interface. |
| 29 | M70.3 eval harness + frozen evals | M58.4 benchmark (cognitive/benchmark), M59.3 exam runner, M50 | OVERLAP | M70.3 delivers the core of **M58.4**, extending cognitive/benchmark. M59.3/M50 then reuse it. |
| 30 | M70.4 worktree sandbox + limits + auto-revert | M45 Auto Lab (BLOCKED_OWNER, isolation), cognitive/sandbox.py | OVERLAP | Addendum to **M45**, extending sandbox.py. The worktree/Job-Object subset may run now. Full M45 isolation stays owner-gated. |
| 31 | M70.5 self-debug loop (N candidate patches) | M46 Self-Debug (patch on separate branch), M58.2 | DUPLICATE | Drop it as separate work. **M46** gains the N-candidate ranking and seeded-bug suite, extending health_manager. |
| 32 | M70.6 safety lock (hash check, read-only gates) | M51 "never touches gates", M58.5 evolution_gate, M34.4 CI lint | OVERLAP | Addendum to **M58.5/M51**. Run it FIRST among the self-* work. |
| 33 | CLAUDE_DASHBOARD_2050 (upgrade layer) | M-D1..M-D12 (CLAUDE_BUILD_MISSIONS), OWNER_DECISIONS_Q1-Q10, M17 panels, M35.2 chat | OVERLAP | Use it as an addendum per M-D mission. OWNER_DECISIONS wins on conflict. Its extra packages (zod, @tanstack/react-query, transformers.js, WebGPU three) go to the owner at the M-D5 npm gate. M17 and M35.2 mount into the M-D4 shell. |
| 34 | Astra plan M60.1-M60.8 | M60.3 vs M28.1 (DSR), learning/calibration; M60.5 vs M21 risk cap; M60.6 vs M15.6-11 + row 4 | NEW (ids already given) | Keep them. M60.3 imports the M28.1 library, M60.5 calls M21 limits, and M60.6 extends the M35.1 council. Nothing gets copied. |
| 35 | Astra M60.9 live Astra voice | Owner 04:54: no paid API | DUPLICATE (cancelled) | Drop it. The free council (row 4) replaces it. |
| 36 | Night order 04:20 steps 1-8 | Queue M12, M34, M13, M-D1..4 | (in progress) | Not re-queued. Steps 1-3 are DONE and step 4 (M12) is running. |

Superseded files (keep on disk, mark them historical, do not execute):
- queue_2050/AHOS_TRADING_SKILLS_v1.md, plus its copy in حافظه_ادامه/2026-10-09_15-53_*.
- queue_2050/CLAUDE_MISSION_M80_OSINT_WHITEHAT.md (v1), plus its copy in حافظه_ادامه/2026-10-09_15-53_*.
- reports/grok/CLAUDE_MISSION_AGI_RESEARCH_M70.md and حافظه_ادامه/2026-10-09_05-20_*/CLAUDE_MISSION_AGI_RESEARCH.md (M70 v1).

Counts: NEW 6 (M61, M62, M63, M64, M70.1, M60.1-8 family). OVERLAP 20. DUPLICATE 6 (JEV, M80-B6/TS§4, M80-B7, TS§8, M70.5, M60.9). SUPERSEDES 3 (TS v2, M80 v2, M70 v2). One row (36) is in progress.

## 2. Contradictions for the owner (not decided here)
1. M35.3, M31.5, and M33.13 say Telegram is "BLOCKED until AD-0128 token rotation", but the bot is live on the current token and the owner ordered M61 without a token change. The owner should confirm that M61 is allowed on the current token.
2. Dashboard 2050 adds packages beyond the Q3 list (zod, tanstack, transformers.js), so they need explicit approval at the M-D5 gate.
3. CLAUDE_SKILLS_v1 says to run `/init`, but CLAUDE.md exists, so the plan is to extend it instead. Context7, Playwright, and Sequential Thinking were not in Soltan's 15:31 approval.
4. Mission ids: "M15 GitHub research" in the brief corresponds to vision **M16** (University and GitHub). M15 is the council.
5. M70.4 lets a sandbox run while M45 isolation is BLOCKED_OWNER. Only the worktree, timeout, and auto-revert subset is proposed. Full isolation stays gated.

## 3. Final single ordered queue for Claude (after its current night-run work)
1. **M61**: Telegram bridge to the decision core, then the G11 live E2E with an archived transcript.
2. **M12**: agent organisation (in progress; DONE only with a receipt).
3. **M34**: coherence audit, taking this map as M34.1 input. It records one owner for verifier, council, LLM layer, ledger, and news desk.
4. **M13**: gold-first paper loop toward 30 closed paper trades (Lane B only).
5. **M63**: Claude dev tooling, between sessions only.
6. **M-D1..M-D4** with the Dashboard 2050 addenda (no new packages). The JEV strip waits for M-D7.
7. **M35.1+**: Kian core, carrying the free council (row 4) and the M70.2 local adapter in one LLM layer.
8. **M70.6** safety lock, then **M70.1** hardware probe.
9. **M70.3** (= M58.4 core), **M70.4** (M45 subset), and **M70.5** (= M46 core), then a stop for the M70 report. L3 and above need approval.
10. **M62 M-PORT**, which uses the M70.1 probe.
11. Trading-math core in TS v2 order: **M25** + **M28.1** (§13, §8), then **M21** (§5, §12, §6, §3), **M33.4/M33.5** (§4), **M24** (§7, §1, §2), and **M15.6-M15.11** (§9).
12. **M60.1-M60.6** (Astra ABB).
13. **M42** (+ paper double-entry, signed digest), then **M43**.
14. **M19** (+ data keys, source pairs, §11 gaps), then **M18.N** unified news desk (M80-A v2 + JEV + §10).
15. **M48** (+ SBOM), then **M64** Negahban hardening.
16. **M35.2, M35.4, M35.5, M47, M44, M49**.
17. **M52, M50, M51, M58.1-M58.6, M59-M59.5, M60.7, M60.8**.
18. **M-D5..M-D12** (owner npm gate), with M17 panels mounted.
19. **M37, M41, M39, M38, M40**, then the rest of **M14-M33** in plan order (incl. M16, M20, M22, M23, M26-M33), then **M55, M56, M57**, **M36**, and **M53**.

Blocked or held (skip): M10 and M35.3 (owner), full M45 isolation (owner), M60.9 (cancelled), M70 L3 and above (approval), and every HUMAN-GATE row (M26, M32.7, M33.15, M33.24).

## Soltan decisions on open questions (2026-10-09 16:14 Tehran, v1.1)
1. Telegram: M61 proceeds on the CURRENT token (owner created the bot and set it; rotation is never done by AI). M35.3/M31.5/M33.13 'blocked until rotation' no longer block M61.
2. Dashboard 2050 extra packages (zod, tanstack, transformers.js): allowed only at the M-D5 gate, exact pins, permissive licence, free, lockfile committed; not before.
3. CLAUDE_SKILLS: extend existing CLAUDE.md (no /init). Context7, Sequential Thinking and Playwright MCPs approved at project-local scope, keyless, no proxies; install only between Claude sessions (M63).
4. GitHub research uses M16 (vision id).
5. v1 files (trading skills v1, M80 v1, M70 v1) are HISTORICAL; use v2 only.

## v1.2 note (2026-10-09 16:30 Tehran, Soltan; owner request 16:21)
- New addendum: reports/grok/queue_2050/M57_M59_UNIVERSITY_TEAMS_MEMORY_ADDENDUM_v1.md (University as single trainer incl. Didehban/Negahban, research intake path, rosters DB-/NG-/MEM-, per-team memory + weekly University review, gated self-* loop, M34.6 end-to-end chain test).
- Class: OVERLAP (addendum only, no new mission ids except test row M34.6 inside M34).
- Slots: §3 step 3 (M34) gains M34.2 owners for trainer/memory/intake/registry + M34.6 skeleton; step 9 (M70.6/M70.5/M46) carries the self-* loop; steps 14/15 (M18.N, M64) get University examinee status + rosters; step 16/19 (M49, M30) and step 17 (M58.2 -> mistake AND success ledger, M59.5 weekly review) carry per-team memory; step 19 (M57) adds the new rosters to the M57/M58/M59 rows.

## v1.3 note (2026-10-09 16:41 Tehran, Soltan; owner approval 16:30)
- New addendum: reports/grok/queue_2050/OWNER_FEATURES_5_ADDENDUM_v1.md (results judge, circuit breaker, nightly Persian digest, outside-tree backups, owner teaching mode).
- Classes: F1 OVERLAP M42 (+ Accounting #36; Erfan evidence only; not Decision Judge #38). F2 OVERLAP M39 (+ daily/weekly paper loss -> HALT + Telegram). F3 OVERLAP M35.4/M31 (trades, reasons, Judge P&L, University lessons). F4 OVERLAP G10 + sqlite_backup_restore (memories+ledger, portable dest outside working tree; M62). F5 NEW **M65** (owner teaching mode, simple Persian).
- Slots into §3 order: F1 with step 13 (M42); F4 with G10 + step 10 (M62 portable dest) and step 13 (ledger in backup set); F3 with step 16 (M35.4); F5 **M65** after M35.4 in step 16 (depends on M61 Telegram bridge); F2 with step 19 (M39).
## v1.4 (2026-10-09 16:48 Tehran) Live agent tree map (owner approved)
- Addendum to M-D (agent office + live task graph, M-D7/M-D8 area), NOT a new mission: one clickable hierarchical tree of all AHOS teams -> agents -> sub-agents (from ahos_org/registry.py + M57 rosters), centred on the shared knowledge/memory core (company-brain pattern). Each node shows real status, current task, maturity, last University cert; UNKNOWN when no evidence. Real data only, no fake numbers. Inspired by public @alassafi.ai content (idea only, no code copied).

## v1.5 (2026-10-09 16:50 Tehran) Design reference: Textura agency (@textura.eu)
- Reference only for M-D hero/boot screens: animated website hero sections, cinematic first-impression intros. No code or assets copied (their GitHub repo is empty; prompts site getlayers.ai is a product, not used). Implement our own with three.js/WebGPU per CLAUDE_DASHBOARD_2050. No new mission.

## v1.6 (2026-10-09 17:00 Tehran) Reference: ajsahni/agents-office (3D isometric agent office, three.js)
- Matches owner reference image 5 (3D agent office). Addendum to M-D7/M-D8 (agent office + tree map): study its layout ideas (departments, desks, central Brain, task bar routing, live team status). Licence NOT verified: no code copied until licence confirmed permissive. Do NOT adopt its Chrome-session driving or claude -p fan-out (security + token cost). Our office shows only real AHOS agent state from ahos_org/registry.py; UNKNOWN when no evidence.

## v1.7 (2026-10-09 17:00 Tehran) University research dept: scout principle + free paper sources
- Addendum to M16/M58/M59.1 (no new mission). Principle (from @ai_in_research): AI is a SCOUT, not proof; every research claim needs replication + two sources before curriculum promotion (already law, restated).
- Free programmatic paper sources for the research intake: arXiv API, Semantic Scholar API (free key optional), OpenAlex, Crossref, SSRN/RePEc RSS for finance. Hosted tools (Elicit, NotebookLM, FutureHouse agents) are human-use references only, not wired into AHOS (accounts/ToS).

## v1.8 (2026-10-09 17:05 Tehran) Patterns from @reznikov_engineering (Apex assistant), ideas only
- M57 sub-agent template addendum: each specialist runs a planning loop (subgoals -> draft -> self-critique -> revise) with its own tools and goal; critique result logged to team memory (A4).
- M30/M49 addendum: a live editable Projects/Missions Log as part of persistent memory (what's active, paused, next) - already mostly covered; make it visible.
- M-D addendum (Kian assistant panel): an animated 'face'/avatar for the AHOS assistant, local, free assets only, muted by default. No new mission.

## v1.9 (2026-10-09 17:31 Tehran) Idea from @ross_rfx (Orion RFX), idea only
- Nebula/Protocol 7 are PAID products: REJECTED, nothing copied or bought.
- Idea kept: genetic strategy evolution (breed many strategy variants, keep survivors) as a University research addendum to M16/M58 + M70.x. Use free DEAP (LGPL) or own code; every survivor must pass walk-forward + out-of-sample + the overfitting guard and two-source rule; PAPER_ONLY. No new mission.

## v1.10 (2026-10-09 17:37 Tehran) Source: Entrelligence (@entrelligence, entrelligence.com)
- Independent tech/AI/business/markets news outlet with a stated two-source, primary-source policy. Addendum to M18.N (دیده‌بان) source list: add its public RSS/site feed if one exists (Claude verifies feed URL + ToS). It is ONE source only: never counts as two; AI/tech-stock news is evidence, not a trade signal. No new mission.

## v1.11 (2026-10-09 17:38 Tehran) Reviewed: @invista.ja (Flavio, Brazil algotrading)
- Sells ready-made robots/course: REJECTED (paid). Ideas (strategy creation+validation, robot portfolio, risk) are ALREADY covered by M19/M21/M24/M42, skfolio (approved), and v1.9 genetic evolution. Nothing new added; no new mission.

## v1.12 (2026-10-09 17:42 Tehran) Ideas from @nick_saraev (free AI-agents course, ideas only)
- M63 addendum (Claude tooling): 'self-updating rules' - when the owner corrects Claude, Claude appends the lesson as a dated rule to a LESSONS section of CLAUDE.md. Append-only; never edits laws, Lane A, .env or Master Directive; logged in DECISIONS_LOG.
- M57/v1.8 addendum: after the self-critique loop, a FRESH reviewer agent (no shared history) checks important outputs (code, strategies, University certs), because an agent is biased by its own history. Fits the M42 independent-judge principle.
- Multi-agent idea fan-out (many agents on one problem): University research only, capped at 3 parallel cheap/free-model agents (token budget). No new mission.
- Repo nickjwells/skills-workspace (Claude Code skills): candidate only; Asi vets licence/security before any use. Paid Maker School / Skool: REJECTED.

## v1.13 (2026-10-09 17:46 Tehran) Correction to v1.12 fan-out cap
- The cap is NOT a fixed 3. Parallel agents = min(hardware tier from RAM/CPU at runtime, remaining free-tier quota of online council providers). Local models have no token cost, only RAM/CPU limits. Online free APIs have daily/minute quotas: a quota-aware scheduler must keep a reserve so live decision paths never starve. 8 GB = floor; scales up on stronger PCs (M-PORT).

## v1.14 (2026-10-09 17:56 Tehran) LAW: Learn-from-correction at every level (owner order)
- Generalises v1.12 item 1. Every level keeps an append-only, dated LESSONS log: Soltan + Asi/Dashi/Aji (their folders), Claude (CLAUDE.md LESSONS), every AHOS team/agent (team memory, M30/M49/A4), University.
- University (M57/M58/M59) weekly harvests all LESSONS; only lessons proven by replication + two sources are promoted into curriculum and taught to all teams; unproven stay 'candidate'. Lessons never override laws/Lane A/.env/Master Directive. No new mission.

## v1.15 (2026-10-09 17:57 Tehran) LAW: Continuous idea scouting by everyone, led by the University research institute (owner order)
- Addendum to M16/M58/M59.1 + v1.7 (no new mission). Every team/agent may submit idea cards; the University research institute (پژوهشکده) scouts DAILY like the owner did today.
- Free legal public sources only: GitHub trending/search, arXiv, Semantic Scholar, OpenAlex, Crossref, SSRN/RePEc RSS, Hugging Face (no account), public RSS/blogs/YouTube metadata, public X via allowed APIs. No login-walled scraping, no paid tools.
- Pipeline per idea: idea card (source, date, what, which AHOS module) -> DEDUP check vs this map -> licence+security vet -> sandbox test -> replication + two sources -> owner/Soltan approval -> curriculum/integration. Rejected ideas logged with reason.
- Budget: scouting uses local models + free-quota scheduler (v1.13); weekly Persian digest of top ideas to owner via Telegram (M31).

## v1.16 (2026-10-09 17:58 Tehran) v1.15 source list extended
- Universities: MIT OCW, Stanford/Berkeley/Oxford/Cambridge open courses and papers, plus arXiv q-fin and cs.AI/cs.LG. GitHub: Trending + topic search (trading, agents, quant). X: public posts via allowed free API only. YouTube/Reddit: public metadata/RSS only. Instagram: owner-shared links/screenshots only (login-walled). Respect each site's ToS/robots; no login scraping.

## v1.17 (2026-10-09 18:00 Tehran) Creator watchlist (autonomous, no Instagram scraping)
- Owner should not have to send links. Research institute keeps config/creator_watchlist (editable) and daily resolves each creator to their PUBLIC open channels (X via allowed API, YouTube RSS, GitHub, blog/RSS, LinkedIn public posts via search) and scouts those through the v1.15 pipeline.
- NO Instagram bot account or Instagram scraping (ToS violation, ban + IP risk). Official Instagram API is own-account only.
- Seed list: alassafi.ai, textura.eu, marc.kaz, iclosegreen, ajsahni.ai, ai_in_research, drmirdehghan, zack.s.t.a, donimas, reznikov_engineering, jacobsskills, saziqo.ir, ross_rfx (Ross Hayes/Orion RFX), entrelligence, invista.ja, aianykey, gitfordesign, nick_saraev (Nick Saraev / nickjwells), goatengineerhq, praddeep.karki.

- 2026-10-09 19:05 v1.17 watchlist +germanyand1 (owner-shared).

- 2026-10-09 19:06 v1.17 watchlist +sahni.ai (likely same creator as ajsahni.ai / AJ Sahni, agents-office; merged under one entry).

- 2026-10-09 19:10 v1.17 watchlist +seb.ai (owner-shared).

## v1.18 (2026-10-09 19:32 Tehran) Ideas from owner video: KRYPT TRADER (Kalshi agent bot), ideas only
- Kalshi is US-regulated and blocks Iran: REJECTED as a venue. Its agents use paid models (opus/gpt): not used. Repo/licence unverified: Asi vets before any code is used.
- M-D7/M-D8 addendum: a first-person walk mode through the 3D agent office (click an agent to see its real task/status) plus a council room view. Reuses the existing office and tree map; no new mission.
- Council addendum (M19/M21 council): council members get distinct, documented personas and risk profiles (e.g. macro/Fed, smart-money/whales, weather/commodities, conservative) and vote. Disagreement is logged; the two-source rule still applies.
- Celebration animation only on REAL paper P&L from the M42 judge; never fake numbers, and always labelled PAPER.

## v1.19 (2026-10-09 19:36 Tehran) Idea from owner video: 'Zero' voice assistant recap (agency demo, ideas only)
- Addendum to the M-D Kian assistant panel (v1.8) + M31 digest + M65 teaching mode, no new mission: the owner speaks ('Kian, give me a recap') and Kian answers by VOICE in Persian, while a glowing node graph pulses with the speech and stat panels fill in one by one from REAL data (M42 paper P&L, open positions, دیده‌بان alerts, University progress). Unknown values show UNKNOWN.
- Free and local only: speech-to-text via whisper.cpp or Vosk, Persian text-to-speech via Piper (or another free local voice if Persian quality is poor; Claude tests). Hardware-tiered; muted by default; push-to-talk (no always-on mic).

## v1.20 (2026-10-10 01:32 Tehran) M13.x multi-market paper rollout (owner approved). Extends M13, no new mission
- Order: only after M13 gold passes its acceptance (two-source price witness, exit rules, risk, M42 judge, M39 breaker). Then one market at a time, each as an ADAPTER on the same gold pipeline (no parallel engine): M13.1 oil (WTI/Brent), M13.2 crypto majors (BTC/ETH), M13.3 US equities/indices, M13.4 EU, M13.5 Asia, M13.6 long-tail tokens (with the نگهبان scam/honeypot checks from M80 v2 mandatory).
- Per adapter: two independent free price sources (same 0.5-1% agreement rule), trading hours and holidays per exchange, tick size, contract or lot specs, fees, slippage model, FX conversion to USD; sizing and math from AHOS_TRADING_SKILLS_v2; per-market circuit breaker plus a global portfolio breaker; skfolio cross-market allocation and a correlation cap.
- Gate to the next adapter: unit tests, a 7-day paper soak without crashes, and M42 judge numbers recorded honestly (no promises). After all adapters pass, run them concurrently in PAPER_ONLY.
- Must not starve the free API quota (v1.13 scheduler); hardware-tiered.

## v1.21 (2026-10-10 08:26 Tehran) Token budget rule (owner approved)
- Run the FULL test suite only at the END of each mission (before the DONE flip). During work, run targeted tests only. Reason: the full suite (~57 min) burns a lot of the Atria quota (100M lifetime, 68% used).

## v1.22 (2026-10-11 01:28 Tehran) @seb.ai post (6 role bots, 'fund floor' pixel UI), ideas only
- Claim of \ -> \,698 is UNVERIFIED and treated as marketing. Setup guide is comment-gated: not used.
- Already covered: role split finder/sizer/executor (council + M21 sizing + execution), and a dedicated 'anti-pump guard' agent that can VETO chasing entries. Add the anti-pump veto explicitly to the M21 risk gate (late entry after an N% spike, volume-climax check). The pixel 'fund floor' style goes into M-D8 as an optional office theme. No new mission.

## v1.23 (2026-10-11 01:33 Tehran) @arwazaz_ 'JEV + Opus' 9-slide algo stack, ideas only (merges with the JEV note of 2026-10-09)
- Architecture already matches AHOS: research layer (University/M58), decision layer (council), deterministic risk in code (M21/M39), execution, monitoring, feedback loop. Paid models and broker APIs (Zerodha/Dhan, India-only) are NOT used. Blueprint is comment-gated: not used.
- New precise items, as addenda to M13.x/M19/M21: (1) a versioned JSON MarketState contract (regime, trend, volatility, momentum, options/news/macro bias, position_state) built from multi-source features, never raw data to the LLM; (2) a JSON Decision schema: signal, regime, confidence 0-1, entry, stop, target_1..3, position_size, valid_for (expiry in candles), short reasoning, review flag (true when uncertain); expired decisions are auto-discarded; (3) a risk config file (risk_per_trade, max_daily_loss, max_exposure, max_correlation, slippage, fees, kill_switch) validated before every trade, with a structured BLOCK reason logged; (4) a duplicate-order guard. No new mission.

## v1.24 (2026-10-11 01:36 Tehran) Source: wangzhe3224/awesome-systematic-trading (MIT, ~5.2k stars), via @wadoodai and @git.radar
- Curated index (97 libraries, 40+ strategies, 55 books, data sources, risk, optimisation, RL). Seed list for the v1.15 research-institute scouting pipeline and the M16/M58 University curriculum. Each listed tool still gets its OWN licence/security vet (Asi) before use; the list's MIT licence does not cover the linked projects.
- Priority reading for the University: pysystemtrade (Rob Carver), the alpha collections and the risk/optimisation sections. NautilusTrader (re-seen via @git.radar) is already approved for backtesting only. No new mission.

## v1.25 (2026-10-11 01:38 Tehran) Dashboard refs: @iamnastynash 'La Sala de Papel' isometric trading office + radix-ui/themes (via @gitfordesign)
- M-D8 addendum: isometric 3D office with named zones per department (Research & Resources, Backtesting & Evaluation, The Arena = live paper trades), agent name tags floating over desks, a central Director/Professor desk. Matches the agents-office reference. Idea only, nothing copied.
- radix-ui/themes (MIT, ~8.7k stars): candidate accessible component base for M-D panels and forms (RTL support required for Persian). Dashi or Asi vets RTL and licence before adoption; must not conflict with the M-D3 tokens (tokens win). No new mission.

## v1.26 (2026-10-11 01:47 Tehran) Owner screenshots batch (6), ideas and candidates
- PinchTab (pinchtab/pinchtab, Apache-2.0, 12 MB Go binary, token-efficient browser control for agents): CANDIDATE for research-institute scouting of PUBLIC pages only (v1.15/v1.17). Never with logged-in personal accounts. Asi vets security first.
- @duncanrogoff's 7 agent repos (Browser Use, an agent-memory repo, Scientific Agent Skills, Diagram Design for Claude Code, Anthropic Cybersecurity Skills, Awesome Harness Engineering, plus one unnamed): Asi resolves exact repos and licences. Mapping: memory -> M30/M49 ideas; cybersecurity skills -> نگهبان (M48/M64, defensive only); harness engineering -> M57/M70 orchestration; scientific skills -> University research methods.
- @jesserurka 'free model trained on 45 exchanges' = Kronos candle forecaster: ALREADY APPROVED (extra predictor). No change.
- Dify (158k stars): too heavy for an 8 GB laptop (Docker stack), and its licence has extra conditions: SKIP as a dependency; workflow-builder idea only for M-D (visual pipeline view).
- haelyra repo (multi-agent dotfolders .claude/.codex/.gemini): name unclear, PENDING. Owner can send the repo name.
- @prozavlly 10 floating navigation designs (liquid floating bar, magnetic dock, orbit nav, glass capsule, cyber neon dock): M-D addendum for the dashboard's main navigation dock (desktop), animated, accessible, RTL. Idea only. No new missions.

## v1.27 (2026-10-11 01:51 Tehran) Owner screenshots batch 2
- Floating nav (prozavlly): already in v1.26.
- @valeridoesai 4 repos: Graft (Claude Code cost/speed) -> Asi for M63; Codebase Memory MCP (repo as knowledge graph) -> Asi for M30/M49/Claude memory; Agency Agents (232 sub-agents, 16 domains) -> Asi for M57 roster ideas only; Open Montage (video) SKIP for AHOS.
- Databasement (David-Crt/databasement): self-hosted backup UI for Postgres/SQLite/etc. Candidate for G10 nightly backups. Asi vets licence/security/Windows fit.
- Agent Reach (Panniantong/Agent-Reach, via marc.kaz): CANDIDATE for research scouting of PUBLIC pages only (v1.15/v1.17). Asi vets ToS/security. No login-walled scraping.
- trycompai/crm (agentic CRM): SKIP as a product (not AHOS). Dashboard dark-theme layout ideas only for M-D.
- usestrix/strix (AI pentest with exploit PoCs): REJECTED. نگهبان stays defensive only (M80 v2 / M48/M64). No exploit tooling. No new missions.

## v1.28 (2026-10-11 01:55 Tehran) Owner screenshots batch 3
- @sebintel Grok survival bot on Polymarket with real money: REJECTED as a pattern. Real-money autonomous trading, survival framing and unverified P and L. Keep only ideas already covered: M39 kill switch, M42 judge, PAPER_ONLY, a clear ALIVE/DEAD status on the dashboard.
- nanobot (MIT, about 48k stars, Python self-hosted agent framework: memory, MCP, multi-agent, schedules, OpenAI-compatible API): CANDIDATE for Asi (M57/M70 local council patterns). Must fit 8 GB; no paid deps.
- Laya (nandhakishorv/laya, local 421M model, very low latency vs cloud): HIGH PRIORITY candidate for the free local council / decision path (M19 + v1.13 hardware tier), to cut Atria quota burn. Asi/Aji vet RAM fit on 8 GB Windows and licence.
- @charles.zhengg native browser use tip: idea only; overlaps PinchTab (v1.26). No new repo until named.
- jonaslejon/malicious-pdf: REJECTED. Offensive malware tooling. Never used, even for testing. No new missions.

## v1.29 (2026-10-11 01:56 Tehran) Owner screenshots batch 4
- PurpleDoubleD/locally-uncensored (AGPL v3, local AI studio chat/images/video): SKIP. AGPL copyleft (same rule as Midday) and off-core for PAPER trading. No mission.
- dimensionalOS/dimos (open-source robot OS / physical body for agents): SKIP. Robotics hardware, not AHOS laptop paper trading.
- MiroFish (claimed free AI fake-customer market simulator, ~70k stars in promo): CANDIDATE idea only for Asi — synthetic agents for paper launch / price reaction tests (M57). Must find real repo + licence; no paid API; no install until vetted.

### v1.29 follow-up (2026-10-11 01:57 Tehran)
- MiroFish (666ghj/MiroFish) confirmed AGPL-3.0 (~77k stars). MiroFish-Offline also AGPL. Same Midday rule: SKIP install/vendor. Patterns only (synthetic swarm for paper sentiment) may inspire M57 design notes; Asi records idea, no clone.

## v1.30 (2026-10-11 01:58 Tehran) Owner screenshots batch 5
- Browser games list (@wassimyounes_): SKIP. Off-topic entertainment; not AHOS.
- Copy4AI (VS Code extension, Leon Kohli): CANDIDATE for Asi as optional free developer tool — pack folder/tree + files (or git diff vs HEAD) for Claude/Gemini prompts. Not part of AHOS runtime. Must never copy secrets/keys; respect .gitignore. Optional for Mehrdad/Claude workflow only.

## v1.31 (2026-10-11 01:59 Tehran) Owner screenshot OpenSandbox
- opensandbox-group/OpenSandbox (Apache-2.0, ~15k stars): CANDIDATE for Asi. Isolated agent sandbox (code/commands/files/browser) via Docker locally or K8s. Licence OK (not AGPL). Hardware caution: Docker/K8s may exceed the 8 GB portable floor — defer install; evaluate only as optional isolation for future agent code execution / M-PORT stronger PC, not for tonight's gold/dashboard path.

## v1.32 (2026-10-11 02:03 Tehran) Owner shared gittrend.io profile grids
- Add gittrend.io to research-institute auto-follow (open channels only; no Instagram bot login). Daily: note new free, licence-OK tools relevant to AHOS.
- REJECT: invisible_playwright_mcp (anti-bot evasion / stealth browser). REA Reverse Engineer Anything (RE tooling). OmniGet (mass download of paid courses / copyright-adjacent).
- SKIP off-core: games/PS5/video editors (Drift, Null Motion, ffframes, SkyCraft, DroidDeck, universal-modder, ANYPS5), SEO/CMS/social (bisibility, Kaleta, CogSend), mac-only mac-ocr, K8s OpenFrame (heavy), Bright Data sponsored templates, FIBO joke, AirCard-iOS.
- CANDIDATES for Asi (vet licence + 8GB): OpenHarness (coding-agent harness), Oriveo Community (BYOK multi-model UI), nanoMuse / OpenWorkBuddy / OpenDots (local personal agents — overlap nanobot v1.28), light-ocr (offline OCR), DeepWatch/Watch Skill (agent observation with verifiable results), e2e AI test framework, pg-jev (NL→Postgres), clearai (ontology — Aji note).
- CANDIDATE for Dashi: oil-ui (AI-generated UI layouts patterns). Whiteboard canvas — optional design ref only.

## v1.33 (2026-10-11 02:04 Tehran) OWNER IDEA: Trend Hunter role in University/Research Institute (M57/M59)
- One dedicated institute member ("Trend Hunter") that does exactly what Mehrdad did tonight, automatically, every day:
  1. Scan open sources only: GitHub Trending, followed creators' X/YouTube/GitHub/blogs (gittrend.io, marc.kaz, seb.ai, etc. watchlist). NO Instagram bot login/scraping.
  2. For each find: real repo URL, licence (AGPL/GPL = SKIP vendor), cost (free only), 8 GB fit, relevance to AHOS (paper trading, agents, dashboard, local models).
  3. Safety gate: auto-REJECT real-money bots, stealth/anti-bot, exploits/malware, piracy.
  4. Dedup against DEDUP_MERGE_MAP, then write REJECT/SKIP/CANDIDATE entry and drop notes into Asi/Dashi/Aji inboxes.
  5. Daily short Persian digest to Soltan; Soltan surfaces only the best to Mehrdad.
- Runs on free models (Gemini free / local small model), low token budget; never installs anything itself (proposal only, Asi vets, Claude builds after approval).

## v1.34 (2026-10-11 02:07 Tehran) OWNER RULE: Idea Shelf + hardware tiers (never fall behind, never overload)
- Every approved idea gets a tier tag: T8 (8GB, default now), T16, T32+, GPU. Stored in an Idea Shelf registry (feature flags), code ready but disabled if above current tier.
- At each launch AHOS detects RAM/CPU/GPU and auto-enables only tiers that fit. On hardware upgrade, higher tiers auto-enable with no rewrite (fits M-PORT).
- RAM guard: under memory pressure, shed low-priority modules first (3D, extra agents, local models); PAPER_ONLY core + truth badge never shut down.
- Trend Hunter (v1.33) must assign a tier to every CANDIDATE.

## v1.35 (2026-10-11 02:14 Tehran) Owner screenshots batch 6
- GitBot (@gitbot-hq/gitbot, MIT, npm v0.0.10, ~58 stars): SKIP for now. Very early; runs Claude Code/Codex per repo = extra token burn. Pattern only: reusable agent job + thread per repo (already have Soltan watchdog + resume).
- fork.cast_ motion-design skill (before/after AI video ads): DASHI idea only. Motion polish pattern for M-D7/M-D8 transitions; repo not identified, no install.
- Hermes3D (iamlukethedev/hermes3d, MIT, v1.0.0, 3D virtual office for AI agents): CANDIDATE for Dashi as reference for M-D8 Agent Tower / walk mode / council room (ref 5 agents office). Patterns only; T16 likely; vet licence and RAM before any code reuse.
- REA (again): stays REJECTED (v1.32).
- seb.ai six-agent Grok trading (Scout/News/Sentiment/Charts/Risk/Decision, paper-first): no new mission; matches existing AHOS council + M39/M42 risk gates. Promo 'comment for guide' ignored.
- Madeira (Windows games on iPhone, GPL-3.0): IGNORE, off-scope.

## v1.36 (2026-10-11 06:48 Tehran) Owner screenshots batch 7 (college.guide.official, fork.cast_)
- open-slide (MIT, ~8.7k stars, React slide framework for agents): SKIP for runtime; optional later for AHOS reports/pitch decks (T8). No mission now.
- Perplexica / Vane (local AI search with citations, Ollama/Groq): CANDIDATE for Asi -> M18.N evidence search with cited sources (supports two-source rule). Check licence (README shows MIT? verify), Docker need, 8GB tier.
- LibreChat (MIT, multi-model chat UI, BYOK): SKIP. Chat client, overlaps Soltan/Telegram bridge; heavy (Mongo).
- AnythingLLM (MIT, private RAG desktop): CANDIDATE shelf T16 -> M30/M49 document memory; verify RAM on 8GB.
- ComfyUI (GPL-3.0, image/video gen): SKIP. GPU tier, off-core.
- Dify: already recorded earlier (v1.26-ish); stays SKIP/shelf (heavy, Docker, licence has extra conditions).

## v1.37 (2026-10-11 06:52 Tehran) Owner screenshots batch 8
- ani-cli (GPL-3.0, anime scraper CLI): IGNORE. Off-scope, and it scrapes a piracy-adjacent site.
- codingknowledge 'Learn AI for free' list (Kaggle Learn, HF courses incl. agents/LLM/deep-RL, fast.ai, CS229, CS50 AI, 3Blue1Brown, mlflow docs, learnprompting): ADD to M57/M59 University curriculum as free public course sources (read-only learning material for institute agents and Mehrdad). No install.
- sebastianhardy_ '350 Grok bots run one trading desk' (live trading visual, golden network map): REJECT as a trading pattern (live money, unverified). Dashi idea only: golden node-network world map + run log + ledger strip look -> M-D6/M-D7 visual reference.

## v1.38 (2026-10-11 06:55 Tehran) Owner screenshots batch 9
- ComfyUI-Ref2VA-VSA (character video gen, needs RTX 4090 24GB): SKIP. GPU tier far above laptop, off-core; ComfyUI is GPL.
- averygan/reclip (paste a link, download social video): SKIP. Downloading from TikTok/YouTube/Instagram breaks their ToS; not AHOS. Never used to pull owner reels automatically.
- ANYPS5 (GPL-2.0, PS5 executable porting): IGNORE, off-scope (already SKIP in v1.32).

## v1.39 (2026-10-11 14:41 Tehran) Owner screenshots batch 10 (12 images)
- Vicoa (AGPL-3.0, run a team of coding agents): SKIP (AGPL; overlaps Soltan + Claude flow).
- MegaMemory (MIT, MCP persistent knowledge graph for coding agents): CANDIDATE for Asi -> M30/M49, compare with Codebase Memory MCP (already APPROVE-SHELF); pick one, not both.
- OpenFlow (Apache-2.0, beta, visual workflow builder): SHELF. Beta, Docker; idea for M57 workflow visual only.
- Qwen 3.8 27B Uncensored (abliterated, needs 13.5-16.8GB/24GB GPU): REJECT. Too heavy (GPU tier) and safety-removed weights are against AHOS rules.
- Archify (MIT, ~75k stars, agent skill for architecture/flow diagrams as HTML): CANDIDATE for docs/Claude (overlaps Diagram Design APPROVE) -> Asi pick one.
- SwiftUI Pro / FaceGate: IGNORE (Apple-only).
- AI Brain (ai-brain.aisac.cloud, shared AI memory via MCP): REJECT for now. Hosted account service, not open-source/self-hosted; would send AHOS memory to a third party. Idea already covered by M30/M49 local memory.

## v1.40 (2026-10-11 15:01 Tehran)
- RankMeFast (AGPL-3.0, self-hosted SEO, needs paid data vendors like DataForSEO): SKIP. AGPL, paid APIs, off-core (SEO).
- Awesome Seedance (MIT code, CC BY 4.0 curation, AI video prompt library): SKIP for runtime. Optional later for AHOS marketing videos only; no mission.

## v1.41 (2026-10-11 16:42 Tehran)
- Taste Skill (anti-slop frontend skill): CANDIDATE Asi/Dashi for UI quality; licence TBD; skill only.
- Uptime Kuma (MIT): T8 shelf, AHOS service health monitor on 127.0.0.1.
- Grok Polymarket survival bot (50 -> 13.67, -71%): REJECT, confirms PAPER_ONLY. Dashi: agent-card-with-one-rule look for M-D8 council.

### v1.41 follow-up (2026-10-11 18:08)
- Taste Skill Leonxlnx/taste-skill MIT APPROVE (design-taste-frontend only). Codebase Memory MCP chosen over MegaMemory. Diagram Design chosen over Archify (shelf). Uptime Kuma T8 shelf. OpenFlow repo unidentified (UNVERIFIED).

## v1.42 (2026-10-11 19:18 Tehran)
- LittleBrother (OSINT people/phone/IP/email lookup, Lulz3xploit): REJECT. Doxxing/surveillance tool; never in AHOS.
- Kev (Apache-2.0, small JEV-like decision models on Qwen3.5 0.8B/4B/9B/27B, trainable): CANDIDATE HIGH for Asi/Aji -> M35.1 council pre-filter alongside Laya. Kev-0.8B likely T8, 4B T16. Verify repo, weights licence, Windows CPU fit, eval honesty. Never a sole voter.
- WordCraft (MIT/Apache-2.0, Rust Word clone): IGNORE, off-core.

## v1.43 (2026-10-11 20:12 Tehran)
- light-ocr (@arcships/light-ocr, Apache-2.0, offline PP-OCRv6): APPROVE T8 shelf; local OCR for PDF/image reports & chart screenshots (evidence intake). Add to config/idea_shelf.json.
- Laya: DUP of v1.28 candidate.
- OpenHarness (MIT, multi-agent coding harness): SKIP, pattern only (single Claude now).
- Web-Check (MIT, website OSINT): SKIP, off-mission.
- Sherlock / username-across-sites checkers: REJECT (people tracking / OSINT on individuals).
- v1.43b (20:17): termuxcommands OSINT pack (UserFinder, Blackbird, email footprint, PhoneIntel, IP tracers, IPDrone, SICAT toolkit): REJECT all, people/IP tracking. Auto-reject this category.
- v1.44 (20:20) OWNER IDEA: 'Pump Hunter' white-hat module (APPROVE concept, T8): early pump/dump alerts from PUBLIC market data only (volume/price anomalies, social mention spikes, public on-chain whale flows). PAPER_ONLY, alerts only. No personal OSINT tools. Slot with M13.x multi-market after gold.
- v1.45 (21:25): DeepGEMM (deepseek-ai, MIT): SKIP, needs NVIDIA SM90/SM100 datacenter GPU + CUDA 12.9. GPU-tier shelf note only.
- v1.46 (21:29): bitnet.cpp (microsoft/BitNet, MIT, CPU 1-bit inference): APPROVE shelf. T8 = BitNet b1.58 2B4T local helper (news summarize/tagging, quota relief, overlaps Laya role). 100B claims = T32+ only. Asi to verify RAM/speed on 8 GB.
- v1.47 (23:05) OWNER-APPROVED M58 AGI ideas -> Aji design: nightly self-critique+lesson efficacy, strategy tournament (DEAP), devil's-advocate council seat, event memory (news->gold reaction), calibrated probability forecasts (Brier). T8, PAPER_ONLY, after dashboard+gold.
- v1.48 (07:40) OWNER: identity = analyst + trader; paper first, real money later behind hard gate (months of verified paper profit + owner approval + tiny capped start). Supersedes 'NOT a trading bot' in MISSION.md 08-16 and the booklets.

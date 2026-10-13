# README_FOR_CLAUDE: read this first before any queued work
Date: 2026-10-09 16:56 Tehran | Version: v1 | Author: Soltan | Reason: owner order (16:55). Claude must use EVERY item that Soltan, Asi, Dashi and Aji found and approved.

## Rules
1. Before starting any mission, read this file, then DEDUP_MERGE_MAP.md (all notes up to the latest v1.x), then the files below that the map assigns to that mission.
2. Use the approved sources, techniques and libraries in these files. Don't reinvent them, and don't add parallel modules.
3. Use v2 where it exists. v1 files are HISTORICAL.
4. Items marked SKIP or REJECTED are never used (paid, illegal, unlicensed or unsafe).
5. Laws in every mission: PAPER_ONLY; the two-source rule (UNKNOWN/CONFLICT never PASS); zero cost; portable; never edit .env or print secrets; never push; no DB flip; Lane A frozen; no profit promises. API keys come only from Windows Credential Manager (AHOS/ai/gemini, groq, openrouter, github_models; AHOS/data/finnhub, twelvedata, fred).
6. Archive every decision with date, reason and version (reports/grok/DECISIONS_LOG.md). Soltan mirrors it into حافظه_ادامه.

## Files (by owner)
| File | Author | Use for |
|---|---|---|
| DEDUP_MERGE_MAP.md | Soltan | Single execution order + merges (authoritative) |
| CLAUDE_SKILLS_v1.md | Asi | M63 Claude tooling (local scope, between sessions) |
| AHOS_TRADING_SKILLS_v2.md | Asi | Trading math/skills -> M19/M21/M24/M25/M42/M15.x |
| CLAUDE_MISSION_M80_OSINT_WHITEHAT_v2.md | Soltan+Asi | دیده‌بان -> M18.N; نگهبان -> M48/M64 |
| MARCKAZ_TOOLS_VETTING_v1.md | Asi | Only the AgentConnect routing/allowlist pattern goes into M61; the rest SKIP |
| CLAUDE_DASHBOARD_2050.md | Dashi | M-D1..M-D12 addenda (OWNER_DECISIONS wins) |
| FREE_HERO_FX_SOURCES_v1.md | Dashi | 19 licence-checked free FX sources for M-D4/M-D5/M-D10 |
| CLAUDE_MISSION_AGI_v2.md | Aji | M70.x self-improvement under safety lock |
| M57_M59_UNIVERSITY_TEAMS_MEMORY_ADDENDUM_v1.md | Soltan | University trains every team, team memory, M34.6 e2e chain test |
| OWNER_FEATURES_5_ADDENDUM_v1.md | Soltan | P&L judge, circuit breaker, nightly digest, backups, M65 teaching mode |
| *_v1.md superseded | - | HISTORICAL |
| QUANT_DESK_REPOS_VETTING_v1.md | Asi | Kronos (MIT) extra forecaster M15.10/M24; skfolio (BSD-3) M24/M28.6; NautilusTrader (LGPL) backtest parity M28.1/M25, never live; Hummingbot ideas only; Freqtrade (GPL) separate dry-run process at most, no keys, no Telegram; RD-Agent UNVERIFIED; OpenBB (Apache) M19 candidate |
| (ref) github.com/ajsahni/agents-office | Soltan | Design reference only for M-D7/M-D8 3D agent office; check licence before reusing code; never adopt its Chrome-session driving |
| (note v1.7) University research intake | Soltan | arXiv, Semantic Scholar, OpenAlex, Crossref, SSRN/RePEc RSS into M16/M58/M59.1; AI = scout not proof |
| (note v1.8) Apex patterns | Soltan | M57: subgoal->draft->self-critique loop per sub-agent; M30: visible missions log; M-D: Kian animated avatar |

- 2026-10-09 17:33: DEDUP_MERGE_MAP v1.9 adds genetic strategy evolution (DEAP, free) to M16/M58/M70.x. Orion RFX paid tools REJECTED.

- 2026-10-09 17:37: DEDUP_MERGE_MAP v1.10 adds Entrelligence as a candidate news source for M18.N (دیده‌بان).

- 2026-10-09 17:38: v1.11 @invista.ja reviewed, already covered, nothing new.

- 2026-10-09 17:42: v1.12 adds self-updating LESSONS rules (M63), a fresh-agent reviewer (M57), and a capped idea fan-out (University).

- 2026-10-09 17:46: v1.13 the fan-out cap is computed from the hardware and free quota at runtime, not a fixed 3.

- 2026-10-09 17:56: v1.14 LAW: every level keeps a LESSONS log, and the University promotes only proven lessons each week.

- 2026-10-09 17:57: v1.15 LAW: daily idea scouting by the research institute and all teams, with idea cards, DEDUP and vetting before any use.

- 2026-10-09 17:58: v1.16 adds university, GitHub, X, YouTube and Reddit sources for the scouting pipeline.

- 2026-10-09 18:00: v1.17 creator watchlist, followed daily through their open channels. Instagram is never scraped.

- 2026-10-09 19:32: v1.18 KRYPT TRADER ideas: office walk mode, council personas with risk profiles, and real paper-P&L celebrations. Kalshi REJECTED.

- 2026-10-09 19:36: v1.19 Kian voice recap in Persian (local STT/TTS, pulsing graph, real stat panels).

| CLAUDE_DASHBOARD_2050_ADDENDUM_v1.19.md | Dashi | v1.18 walk mode + council room (M-D8), v1.19 Kian voice recap (M-D3/4/7/9/11). whisper.cpp + sherpa-onnx + Piper fa_IR CC0 voices; Piper GPL runtime excluded |

| ASI_VETTING_v1.19.md | Asi | KRYPT TRADER REJECTED (unsafe installer adds a Defender exclusion), ideas only for M21/M25/M28.1/M42. skills-workspace SKIP (no licence). Kian voice: Vosk small-fa + Piper fa_IR-amir as a separate process (APPROVE, M35.1+) |

- 2026-10-10 01:32: v1.20 M13.1-M13.6 rollout after gold: oil, crypto, US, EU, Asia, then tokens, one adapter at a time on the gold pipeline, then all run concurrently in PAPER_ONLY.

- 2026-10-10 08:26: v1.21 RULE: full test suite only at the end of each mission, targeted tests during work (token budget).

- 2026-10-11 01:28: v1.22 adds an anti-pump veto to the M21 risk gate and an optional pixel 'fund floor' theme for M-D8.

- 2026-10-11 01:33: v1.23 adds JSON MarketState + Decision schemas (with valid_for and a review flag), a risk config with structured BLOCK reasons, and a duplicate-order guard.

- 2026-10-11 01:36: v1.24 adds awesome-systematic-trading (MIT) as the seed index for research scouting and the University curriculum. Each tool is vetted separately.

- 2026-10-11 01:38: v1.25 adds isometric office zones and name tags (M-D8), and radix-ui/themes as a candidate component base (vet RTL first).

- 2026-10-11 01:42: RULE: after each M-D step, Soltan screenshots the dashboard and compares it with the Dashi docs. Work below that level is sent back, so build to the Dashi design, not to the old UI.

- 2026-10-11 01:47: v1.26 PinchTab (public pages only) and duncanrogoff's 7 repos go to Asi vetting. Kronos is already approved. Dify SKIP (idea only). Floating nav dock styles added to M-D.

- 2026-10-11 01:51: v1.27 Graft + Codebase Memory MCP + Agency Agents -> Asi. Databasement -> G10 candidate. Agent Reach public-only. Strix REJECTED (offensive). CRM SKIP.

- 2026-10-11 01:55: v1.28 nanobot + Laya -> Asi (local agents / local model). Survival Polymarket bot REJECTED. malicious-pdf REJECTED.

- 2026-10-11 01:56: v1.29 Locally Uncensored SKIP (AGPL). dimos SKIP (robotics). MiroFish idea -> Asi (find repo/licence).

- 2026-10-11 01:57: MiroFish also AGPL — SKIP install; idea patterns only.

- 2026-10-11 01:58: v1.30 browser games SKIP. Copy4AI optional free VS Code helper -> Asi (dev workflow only, no secrets).

- 2026-10-11 01:59: v1.31 OpenSandbox (Apache-2.0) -> Asi backlog; Docker-heavy, not for 8GB tonight.

- 2026-10-11 02:03: v1.32 gittrend.io on watchlist. Reject stealth Playwright + REA + OmniGet. Asi backlog: OpenHarness, Oriveo, local agents, light-ocr, DeepWatch. oil-ui -> Dashi.

- 2026-10-11 02:04: v1.33 OWNER IDEA Trend Hunter agent in Research Institute (M57/M59): daily open-source scouting + licence/cost/8GB/safety gate + dedup + inbox notes. Build after current dashboard/gold missions.

- 2026-10-11 02:07: v1.34 OWNER RULE Idea Shelf: tier tags T8/T16/T32/GPU + feature flags, runtime hardware detect auto-enable, RAM guard sheds non-core first; paper core never off.

- 2026-10-11 02:13: READ TEAM_QUEUE_2026-10-11.md next (Dashi M-D5..M-D8 order with owner gate at M-D5.0, Aji Idea Shelf + Trend Hunter, Asi verdicts).

- 2026-10-11 02:14: v1.35 Hermes3D (MIT) = Dashi reference for M-D8 agent office, patterns only. GitBot SKIP (early, token burn). REA still REJECT. seb.ai six-agent = already covered by council.

- 2026-10-11 02:17: OWNER: M-D5.0 package gate REMOVED. Install the free packages listed in TEAM_QUEUE without asking; pin and log versions. Anything not in the doc, paid, or non-free licence still needs Soltan.

- 2026-10-11 06:48: v1.36 Perplexica/Vane -> Asi (cited search for M18.N). AnythingLLM shelf T16. LibreChat/ComfyUI/open-slide SKIP. Dify unchanged.

- 2026-10-11 06:52: v1.37 free AI course list -> University curriculum sources. 350-Grok-bots desk REJECT as trading, Dashi visual ref only. ani-cli IGNORE.

- 2026-10-11 06:55: v1.38 Ref2VA (RTX 4090), reclip (ToS), ANYPS5: all SKIP/IGNORE.

- 2026-10-11 10:04: Soltan ran the M-D5.0 install on the laptop (exact PACKAGES.md command, --save-exact --ignore-scripts, 99 packages added). BLOCKED_TOOL_PERMISSION is cleared: verify package.json/lock, run tsc + stage tests, then render M-D5.2 and take screenshots.
  - tsc after install: 1 error only, components/stage/quality.ts(421): detect-gpu 5.0.70 has no getGpuDevice export (use getGPUTier result fields). Fix first.

- 2026-10-11 14:15: SOLTAN QA M-D5.2 (owner screenshot): palette/RTL/tier chip OK. Fix: top-left chip text is hatched/strikethrough and unreadable; make it legible. Stage is empty (expected until M-D6). Keep going M-D5.3..M-D6 globe fast; owner expects the modern Dashi look, so prioritise visible content (globe, side panels with real data/UNKNOWN) over more invisible plumbing.

- 2026-10-11 14:33: DASHI QUEUE v3 (overrides order in TEAM_QUEUE): (1) M-D5.F first: chip/label text solid, local Vazirmatn, contrast >= 4.5:1. (2) No step may end on an empty stage; M-D5.2 shows gold placeholder globe + grey 'T?' chip. (3) Order: stage -> M-D6 globe -> right tier panel + run-log/ledger strips (real data or grey UNKNOWN) -> plumbing -> pipeline graph -> M-D8. (4) Visual refs: golden node-network map (M-D7.1/7.3, look only), Hermes3D MIT patterns (M-D8), motion polish for transitions.
- 2026-10-11 14:33: AJI v1.1: Idea Shelf = config/idea_shelf.json. University tracks T-A..T-F (later). ASI addendum: Vane (ex-Perplexica, MIT) APPROVE-SHELF T16 for M18.N cited search, 127.0.0.1 only, counts as ONE source; AnythingLLM/Hermes3D/GitBot SKIP.

- 2026-10-11 14:41: v1.39 MegaMemory + Archify -> Asi (dedupe vs approved picks). Vicoa AGPL SKIP, uncensored Qwen REJECT, AI Brain hosted REJECT, Apple-only IGNORE.

- 2026-10-11 15:01: v1.40 RankMeFast SKIP (AGPL + paid vendors). Awesome Seedance SKIP (video prompts, off-core).

- 2026-10-11 16:42: v1.41 Taste Skill -> Asi/Dashi; Uptime Kuma T8 shelf; Polymarket survival bot REJECT.

- 2026-10-11 18:07: DASHI QUEUE v4: nav = glass capsule on right edge, crimson/gold (M-D5.2/5.4/6.4); T0/T1 solid bar, no blur; reduced motion disables magnetic effect. M-D8.5 seat cards show one hard rule from config or grey UNKNOWN. Hermes3D pattern ref for M-D8.3-8.5. Taste Skill pending licence.

- 2026-10-11 18:08: ASI PICKS (GitHub API, all MIT): (1) Taste Skill github.com/Leonxlnx/taste-skill APPROVED: copy ONLY design-taste-frontend + its LICENSE into .claude/skills by hand; run redesign-existing-projects once as a UI audit of the new Dashi dashboard (keep RTL, no new packages); skip gpt-taste. (2) Codebase Memory MCP = M30/M49 pick (MegaMemory SKIP). (3) Diagram Design = docs pick (Archify shelf). (4) Uptime Kuma = T8 shelf, later, 127.0.0.1:3001, notifications off. OpenFlow unidentified.

- 2026-10-11 19:18: v1.42 Kev (Apache-2.0 small decision models) -> Asi/Aji vet for M35.1 with Laya. LittleBrother OSINT REJECT. WordCraft IGNORE.

- 2026-10-11 19:26: SOLTAN QA M-D5.5 (owner screenshot) — OWNER SAYS NOT 'WOW' ENOUGH. Fix before moving on:
  1. Top-left chip text STILL hatched/unreadable. M-D5.F (solid text, Vazirmatn, contrast >= 4.5:1) was step one and is not done. Do it now.
  2. 'Waiting for upgrade' row shows a hatched error ('reading idea shelf failed'). Create a seed config/idea_shelf.json from real approved items (Laya, Kev, Vane, OpenSandbox, AnythingLLM, Uptime Kuma, Browser Use, with tiers from Asi's vetting) so the panel shows real content. If the file is missing, show clean grey UNKNOWN text, never a hatched box.
  3. WOW ON 8 GB: the T1 tier must still look premium. Use cheap effects: frosted-glass panels (CSS backdrop-filter on panels only), a gold rim light and soft bloom done in a shader or CSS, slow ambient motion, a dotted or hex-point globe (instanced points, under 30k), animated gradient glow on the stage edge, smooth number tickers. No heavy postprocessing on T1.
  4. Pull M-D6 (the globe) forward right after these fixes. The owner must see the globe next.
  5. Add a dev-only quality override (Settings: Force T3) so the owner can preview the full look on this laptop.
  6. After each fix, screenshot at T1 AND forced T3.

- 2026-10-11 20:12 SOLTAN: v1.43 add light-ocr (Apache-2.0, T8) as an idea_shelf.json entry only (no install now). Sherlock-type tools REJECTED. Dashboard fixes stay first.

- 2026-10-11 21:15 SOLTAN: PARALLEL TEAM. A second builder (Gemini CLI) now works in worktree G:\robat\ahos_gemini (branch ahos-gemini) on M59.S idea shelf, M57.T trend hunter, Pump Hunter doc. Claude: stay on dashboard M-D5/M-D6 only; do NOT build idea_shelf loader/RAM guard (Gemini owns it; you may keep the seed JSON for the panel). Soltan merges nightly.

- 2026-10-11 21:46 SOLTAN: CANCEL the 21:15 PARALLEL TEAM note. Gemini is NOT running (region blocked). Claude owns everything again, including the idea shelf. STOP re-reading context: the open work is the 19:42 QA list, item 1 first (solid chip text). Build, screenshot, commit. Read no more than 3 files before the first edit.

- 2026-10-11 23:03 SOLTAN QA (owner screenshot): chip text readable now, good. Still wrong: the 'حالت اجرا' chip has a dashed/hatched border, make it solid. Stage is still an empty gold ring. Commit item 1 NOW, then do items 2 (idea_shelf seed) and 4 (M-D6 dotted globe inside the ring) next. Owner must see the globe tonight. Keep each step small and commit after each.
- 2026-10-11 23:05 SOLTAN: v1.47 M58 AGI ideas sent to Aji for design. NOT in Claude's queue yet; stay on dashboard.

- 2026-10-12 00:00 SOLTAN (alignment audit, see حافظه_ادامه/2026-10-12_ALIGNMENT_AUDIT.md): AFTER M-D6.1 globe is committed, do a SMALL core step before M-D6.2: start the M13 gold 7-day paper soak (scheduled cycle + daily judge report, close G2/G3 in reports/PRE_SOAK_STATUS.txt). Then return to dashboard. M59.S core (registry/hardware/flags/RAM guard) comes right after M-D6. Owner will confirm order in the morning.

- 2026-10-12 00:01 OWNER DECISION: GOLD AND DASHBOARD IN PARALLEL, starting NOW. Supersedes the 00:00 'after M-D6.1' note. Commit the current M-D6.1 globe work-in-progress first, then immediately start the M13 7-day gold paper soak as a background scheduled job (paper cycles + daily judge report in reports/grok/M13_SOAK/, close G2/G3 in PRE_SOAK_STATUS.txt). Once the soak runs on its own, continue M-D6. Check the soak's daily report at each session start. Then M59.S core (registry/hardware/flags/RAM guard). Fix the hard-coded C:\Users\Sniper paths in claude_resume.ps1:59 and run_mission.ps1:30 with $env:USERPROFILE.

- 2026-10-12 00:08 SOLTAN QUEUE v2 (from FULL_HISTORY_AUDIT; binding order, small steps, commit each): A) gold 7-day soak + daily judge + M42 nightly single-ledger reconcile (parallel with dashboard M-D6). B) M59.S core/idea_shelf (registry, hardware detect, flags, RAM guard) + tests. C) M47 health monitor that can downgrade/halt the soak + M39 monthly fault test. D) M49 lessons ledger + M58.1 decision self-evaluation fed by soak trades. E) M13.3 crypto adapter on FREE sources already in adapters.py (DexScreener, GeckoTerminal, GoPlus, RugCheck); Pump Hunter = alert layer; DEXTools stays off. Do NOT build a parallel engine (M20): gold_paper must use the one ledger.

- 2026-10-12 00:20 SOLTAN QA d6a8ca2 (M-D6.1 point globe): accepted as step 1. PRE-APPROVED free packages (owner rule: free + listed = install without asking, pin versions, log in PACKAGES.md): three-globe (MIT), world-atlas (ISC), topojson-client (ISC). Next M-D6 steps: Natural Earth land dots, real day/night terminator (sun.ts), abstract chain rings. If you hit 'API Error: 400', commit WIP and tell the owner to start a fresh session; do not loop.
- 2026-10-12 00:24 SOLTAN visual QA M-D6.1 t1.png: globe visible, good. Fix: rim is a thick flat neon-yellow ring (cartoonish) -> thin soft fresnel falloff, warm gold not lemon; globe too small and floating above the ring -> scale up ~1.6x and seat it centred inside the floor ring; add slow rotation; the two hot spots look like glitches -> make them intentional city/market pings or remove. 'حالت اجرا' chip border still dashed (M-D5.G).

- 2026-10-12 00:35 SOLTAN INSTALLED (owner order: everything needed for a top-tier 3D + audio + visual-FX dashboard; all free/open licences, pinned): motion (MIT, UI animation), gsap + @gsap/react (free licence, timelines), howler (MIT, sound playback), tone (MIT, synthesized UI sounds, no asset files needed), maath (MIT, easing/random for R3F), @react-spring/three (MIT, physics motion), leva (MIT, DEV-only tuning panel), @types/howler. Already present: three, R3F, drei, postprocessing, rapier, three-globe, world-atlas, topojson-client, detect-gpu. Log them in docs/dashboard/PACKAGES.md. Sound rules: OFF by default, one mute toggle, quiet subtle UI ticks/whooshes, never on T0. Use within RAM tiers.
- 2026-10-12 00:38 SOLTAN QUEUE v2 additions (from old booklets, audit section 7): F) source-trust learning, a per-source reliability score that improves over time (extends the two-source rule; for gold + crypto). G) 0-100 composite score from 10 explainable sub-scores + 'why better than alternatives' for every recommendation. H) early new-token launch detection (Pump.fun / Moonshot / Raydium LaunchLab, free public data) + honeypot/liquidity-lock checks = Pump Hunter base, inside M13.3. Read the Universal Market Object Standard doc before M13.1. Paper-only, free sources only.
- 2026-10-12 01:17 SOLTAN QA 1a2f4bb (M-D6.2): better (warm gold, bigger, thinner rim). Still open: (1) the two glow spots (pale top, orange-red upper-left) are still visible, remove them or make them clear intentional market pings; (2) the globe crown is clipped by the header, lower it or scale it about 0.92; (3) T3 rim still reads as a thick beaded neon ring, soften the fresnel falloff. Also make the hardware-tier chip borders solid (same as 178c90e). Then the land dots, terminator and chain rings, and start the gold soak.
- 2026-10-12 02:48 SOLTAN QA 4b1b0da (M-D6.3 land): T3 continents readable, good. Before or with the terminator, close the repeat items, which are now overdue: (1) remove the two glow spots, or turn the Tehran one into a small intentional gold ping; (2) the globe crown is still clipped by the header; (3) T3 rim is still a thick beaded neon ring; (4) the caption still says M-D6.1; (5) seat the globe inside the floor ring; (6) make the T1 land brighter. Verify each against your own screenshot before committing.
- 2026-10-12 04:16 SOLTAN QA eb5ec75 (M-D6.4 terminator): math accepted, but visually too subtle, make the night side clearly darker (T1 too). HARD GATE: the six overdue items from 02:48 (glow spots, clipped crown, neon rim, caption M-D6.1, globe seated in floor ring, faint T1 land) were skipped twice. Do NOT start the chain rings until all six are fixed, one small commit each, each one checked against your own screenshot. A headless M13 autopilot job may be committing in parallel: stage and commit ONLY your own dashboard files (never git add -A), and run git pull/rebase-free checks (git status) before each commit.

- 2026-10-12 07:40 OWNER DECISION (identity): AHOS = analyst AND trader. PAPER_ONLY for now, until it debugs, improves and evolves itself. Real-money trading on all planned markets is a FUTURE phase behind a hard gate: several months of verified paper profit, explicit owner approval for every enable, start tiny with a capital cap, kill-switch (M39) and judge (M42) required. Until the owner opens that gate, no code path may place real orders or hold exchange keys.

## Soltan QA note 2026-10-12 10:45 Tehran (after 8ca48fd)
- 73a7f85 seating + crown: CLOSED (pixel-checked).
- After you finish the current beaded-rim step (do not interrupt it): (1) fix or remove the wrong measurement numbers you put in README in 8ca48fd; they don't match seated_t3. (2) seated_t1.png is a Chrome ERR_CONNECTION_REFUSED page, not a render; start the dev server and recapture a real T1 shot.
- Still open: glow spots, beaded rim, faint T1 land. Commit only your own files by path.
- Owner rule: technical tier promotions (T0->T1) are approved by Soltan+Claude on strict technical criteria; only the first real-money switch needs Mehrdad.
- Asi v1.49: PdfCraft SHELF T8 (wait, Windows CLI immature); gyotaku owner-only standalone, never linked into AHOS.


- 2026-10-12 14:10 SOLTAN QA 4f51c21 (glow spots = land opacity 0.95->0.62): FAIL, item NOT fixed. Your own after-shot land062_t3.png still shows BOTH spots (pale upper-centre, orange-red upper-left) clearly. ablation_noland.png (land layer removed) ALSO shows both spots at the same place, so the land layer is not the cause. The spots sit at the same SCREEN position in every shot while the globe rotates, so they are view- or light-dependent (hunch: a reflection/highlight of the two pointLights in Stage.tsx, or the shell/body material; verify by removing BOTH lights at once and by hiding the body and shell meshes one at a time, and measure luminance at the spot's screen pixel, not on a rotating land patch). Revert land opacity toward 0.95 unless a real reason remains, because cutting it makes the open item 'faint T1 land' worse. Recheck your luminance numbers against the PNG before writing them in a commit message. Still open: glow spots, faint T1 land, README measurement table, real T1 recapture. Commit only your own files by path.

- 2026-10-12 14:43 SOLTAN QA 2550aae (T1 land opacity/size ramp): PARTIAL. Item 6 (faint T1 land) improved: landbig_t1.png / landramp_t1.png show continents more readable than flat land062_t1 (T1 at 0.95 + larger dots). BUT glow spots are STILL OPEN and your commit message still wrongly claims the T3 0.62 back-off 'removes the glow spots'. Visual check: landbig_t1, landbig_t3, land062_t3 ALL still show both spots (pale upper + orange-red). That claim was already FAIL at 14:10 on 4f51c21 (ablation_noland retains spots at fixed screen position = view/light, not land stacking). Do NOT keep tying land opacity to glow spots. Next: kill both Stage pointLights together and hide body/shell meshes one at a time; measure spot luminance at fixed screen pixels. README measurement table still wrong. Working tree currently has ABLATION freezes (IDLE_RAD=0, FROZEN_SUN) — revert those before any non-ablation commit. Screens copied to C:\Users\Sniper\qa_2550aae_*.png. Commit only your own files by path.

- 2026-10-12 15:25 SOLTAN QA a40a53e/HEAD (commits since 2550aae: bfab049 night floors, ceed116 docs, 1fc7a33 README+seated_t1, a40a53e docs): PARTIAL.
  - 1fc7a33 PASS for the two 10:45 doc items: measurement table corrected (crown clearance 81 px, disc x 476..1109 / y 135..731); seated_t1.png is a real T1 render now (141696 B, 0.1% pale), not ERR_CONNECTION_REFUSED.
  - bfab049 PARTIAL on night darkness (DUST_NIGHT 0.16->0.07, LAND_NIGHT 0.34->0.16). Frozen before/after bands drop modestly (frz_old_t3 pct>32 8.50->7.75; p99 119->111). Night still dominated by the two glow spots.
  - REGRESSION: bfab049 removed the T1 land opacity/size ramp from 2550aae (back to fixed opacity 0.95, size 0.088). That undoes the PARTIAL win on faint T1 land. Restore the ramp (or equivalent) without tying it to glow spots.
  - Glow spots STILL OPEN and NOT fixed. nightfloor_t3 / frz_new_t3 / seated_t1 / landbig_t3 all still show pale upper + orange-red upper-left. Stage.tsx still has both pointLights ([0,5.6,0] and [0,-1.5,5]). Do the light/body/shell ablation from the 14:10 note; do not claim glow spots closed.
  - Claude's session note "All QA items closed" is FALSE. Still open: glow spots (hard), faint T1 land (regressed), confirm beaded rim after 4e0ff9b still holds visually.
  - Screens at C:\Users\Sniper\qa_a40a53e_*.png. Commit only your own files by path.
- 2026-10-12 16:24 SOLTAN QA ca203cc PASS (docs-only archive; chip border solid). Repeat items NOT touched by this commit and still open: (1) two glow spots, (2) faint T1 land, (3) rim confirm. Keep the current light ablation short; commit after each step.

- Soltan 2026-10-12 17:35 (Tehran): owner asks to use ready-made assets instead of building from scratch; see vendor_assets/globe/README.md; prefer these for glow-spot fix and chain rings; commit only your own files by path.

- Owner rule 2026-10-12 17:42: build nothing from scratch when vendor_assets has it; customize, unify style (one palette/typography), assemble, and match; commit only your own files by path. Index: vendor_assets/README.md (icons, tokens, characters, scenes/hdri, hud, charts, vfx, fonts incl. Vazirmatn, loaders, sounds, ui_reference, globe).

## Soltan 2026-10-12 18:00 Tehran: DOWNLOAD THE KIT YOURSELF (owner rule)
Copying from Soltan's box failed, so you fetch it. Download into G:\robat\ahos\vendor_assets\<category>\ (gitignore the vendor tree; never commit it). Keep each LICENSE. Small, free, permissive only. Then build nothing from scratch: customize, unify (one palette + typography), assemble, match.
- icons: npm pack lucide-static, @tabler/icons, @phosphor-icons/core (extract SVGs only)
- tokens: @radix-ui/colors (dark scales) + own AHOS dark sci-fi palette
- fonts (OFL): Vazirmatn (Persian RTL), Orbitron, Oxanium, Exo 2, Rajdhani, JetBrains Mono
- characters + office/university props: Kenney Mini Characters, Kenney Furniture Kit (CC0, kenney.nl, GLB only)
- HDRI: 3 indoor + 4 night skies from polyhaven.com at 1k (CC0)
- HUD: Arwes frames/backgrounds (MIT)
- charts: lightweight-charts 5.x (Apache-2.0, keep TradingView attribution) for candles; echarts 6 for the rest
- VFX: @react-three/postprocessing (MIT; its dependency postprocessing is Zlib, approved)
- loaders: SpinKit CSS (MIT)
- sounds: Kenney Interface Sounds + UI Audio (CC0); off by default, mute toggle, never on T1
- globe: already in vendor_assets\globe (use reference/AtmosphereR3F.tsx for rim/glow; cobe land-mask note for T1 land)
Write vendor_assets\README.md index. Commit only your app files by path.


## SOLTAN NOTE 2026-10-13 21:20 Tehran (binding, do these in order)
- Keep every turn short. NEVER Read reports/grok/M13_SOAK/* directly (file-change injection causes API 400); copy to TEMP first.
- 0. Do NOT git add -A. HOLD.flag stays.
- 1. Fix dashboard bootstrap URL port 3199 vs dev server 3000 so the browser opens the 3D dashboard.
- 2. Glow blobs: last lead = gold pointLight at [0,5.6,0] above the globe crown + dot stacking at tilted pole. Remove/dim that pointLight; no more long A/B measurement loops (2 tries max, then take the simplest fix). Commit + one T3 screenshot.
- 3. Wire bottom UNKNOWN cards (run, gates, ledger) to local soak data. Commit + screenshot.
- 4. Create reports/dashboard/GLOBE_MEMORY.md: globe history from git log, best earlier screenshot as reference, rules never to go below it. Read it first every session.

## STANDING ORDER (Soltan, 2026-10-13 21:36 Tehran) - applies to EVERY session, forever
Quality bar: top-tier, 2050-level, technically excellent. Assemble/customize vendor_assets; build nothing from scratch.
Work loop (never idle, never ask the owner for technical approval):
1. Read reports/dashboard/GLOBE_MEMORY.md (if present) and the last 60 lines of this README.
2. Pick the NEXT unfinished item in this binding order: (a) items in the latest SOLTAN NOTE; (b) remaining dashboard screens (office, university, evidence graph, ledger, sound) from vendor_assets; (c) QUEUE v2 items A-H; (d) the rest of reports/grok/CLAUDE_AUTOPILOT_QUEUE.md in order.
3. Do it in small steps; each turn under 20 minutes; commit by path after every step with one real screenshot path for visual work. No claims without proof.
4. Max 2 attempts per bug, then use the simplest ready-made solution and move on.
5. Append one line per commit to reports/grok/PROGRESS_LOG.md (time, commit, what, screenshot) so the next session knows where to continue.
6. Then go straight to the next item. Never stop just because one item is done.
Safety: never git add -A, never push, paper-only, HOLD.flag stays, never Read reports/grok/M13_SOAK/* directly (copy to TEMP), never print keys.
If API 400 or context near full: commit, write the next step in PROGRESS_LOG.md, and stop; the watchdog restarts a fresh session that continues from PROGRESS_LOG.md.

## OWNER NOTE 2026-10-13 21:43 Tehran (top priority, before other items)
- AHOS is a DESKTOP DASHBOARD APP, not a website. The owner must open it like an app (own window, no browser tabs/address bar). Make the desktop shortcut open it as an app window (e.g. Edge/Chrome --app=URL kiosk-style, or the planned packaged app) that also starts the dev/prod server itself if not running.
- BUG: clicking the desktop icon opens nothing. Fix the launcher end to end (server start + correct port + app window). Test by actually launching it; screenshot proof.
- The owner dislikes the current icon. Replace it with a premium 2050-style AHOS icon assembled from vendor_assets (icons/fonts/palette), gold-on-dark, crisp at 16-256 px, as .ico. Screenshot proof.

## TOP PRIORITY (Soltan 2026-10-13 23:00): read reports/dashboard/MASTER_SPEC.md first; it overrides older dashboard plans. Follow its build order and quality gate.


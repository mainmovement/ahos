# CLAUDE AUTOPILOT QUEUE (owner order 2026-10-04 00:01)
Owner rule: if Grok is disconnected or out of tokens, Claude continues these missions ONE BY ONE from the docs, automatically.
Driver: reports/grok/claude_autopilot.ps1 (hidden). Watchdog: claude_watchdog.ps1. Details of every mission: OWNER_DIRECTIVE_MISSION_PLAN.md + AHOS_AUTONOMOUS_VISION.md (newest version wins).
Statuses: PENDING, RUNNING, DONE, PARTIAL (retry), NEEDS_REVIEW, BLOCKED_OWNER (human gate; skipped). Edit only the STATUS column.

| ID | STATUS | MISSION (see plan/vision for full spec + acceptance criteria) |
|---|---|---|
| M11.1 | DONE | Launcher finish (single icon, zero consoles, Status/Stop/Restart in CommandCenter.tsx, gateway port) - run by run_mission.ps1 -n 11_1 |
| M11.2 | DONE | launcher/ahos.ps1 hidden path: Tee-Object -Encoding invalid in PS 5.1 (log never written) + no double-run on stderr (spec: reports/grok/autopilot/missions/M11.2-launcher-ps51-log.md) |
| M11.3 | DONE | Gateway process identity: marker never matches npm wrapper -> second start calls own gateway foreign (spec: reports/grok/autopilot/missions/M11.3-gateway-identity.md) |
| M11.4 | DONE | Telegram health = stable process/readiness, not pid alive at spawn (spec: reports/grok/autopilot/missions/M11.4-telegram-health.md) |
| M48.1 | DONE | Next 16.2.6 -> 16.3.8 security update (critical advisory), proposal + rollback (spec: reports/grok/autopilot/missions/M48.1-next-security-update.md) |
| M10.1 | RUNNING | Launcher initialises empty PGlite store (schema-only restore) + real table probe (spec: reports/grok/autopilot/missions/M10.1-pglite-init-in-launcher.md) |
| M10 | PENDING | Native portable PostgreSQL/PGlite switch, Docker/n8n retirement (plan "M10 decision") |
| BL | PENDING | Close open BL/MJ items and all QA (16) BLOCKERs listed in reports/grok (GROK_HANDOFF, ORCHESTRATION_LOG, remaining-work inventory) |
| M12 | PENDING | Agent organisation: 37+ agents in config/agent_registry.yaml using the owner charter template, authority NONE by default, no auto-creation |
| M34 | PENDING | Coherence audit M34.1-M34.2: one core, one ledger, one registry, one bus, one bot, one memory; map duplicates, merge plan, number mapping |
| M13 | PENDING | Paper trading, gold first (PAPER_ONLY), T0->T1 machinery per vision 11.0 |
| M42 | PENDING | Hash-chained single ledger + nightly reconcile |
| M43 | PENDING | Decision records + per-market tier state |
| M35.1 | PENDING | Kian core (gemini_chat + router + council + memory + hash-chained audit store under data/ + tools + gate code + injection defence) |
| M35.2 | PENDING | Kian chat inside CommandCenter.tsx dashboard |
| M35.3 | BLOCKED_OWNER | Kian on Telegram - blocked until owner rotates Telegram token (AD-0128) |
| M35.4 | PENDING | Nightly Persian report by Kian (extend M31, no second reporter) |
| M35.5 | PENDING | Command routing + human-gate inbox |
| M47 | PENDING | Health Monitor (READ/DOWNGRADE/HALT, fault-injection suite) |
| M44 | PENDING | Science Radar (legal APIs, on research_worker/ + research_report_bot.py) |
| M49 | PENDING | Lessons Ledger (hash-chained, UNVERIFIED until QA) |
| M46 | PENDING | Self-Debug (evidence_refs, patch on separate local branch only) |
| M48 | PENDING | Safe dependency/model updates (proposal + rollback, hash-pinned) |
| M45 | BLOCKED_OWNER | Auto Lab - needs owner one-time low-privilege user + firewall setup; fail-closed until then |
| M52 | PENDING | Skill & Plugin Marketplace (vetting V1-V4, registry fields, INV-41) |
| M50 | PENDING | Weekly Intelligence Exam, Saturdays 08:00 Tehran |
| M51 | PENDING | Self-Improvement Loop (one proposal/cycle, never touches gates) |
| M37 | PENDING | Frontier model slots locked (registry + budget cap + cost meter) |
| M41 | PENDING | Broker key-permission self-check (fail-closed, no real broker needed: mocked tests) |
| M39 | PENDING | Kill switch + monthly fault injection (paper) |
| M38 | PENDING | Execution Gateway (deterministic, no LLM) - paper/simulated only |
| M40 | PENDING | Treasury request flow + negative tests (no real transfers) |
| M14-M33 | PENDING | Remaining plan missions in plan order (markets, university, arena, crisis sim, debate, memory, wealth panel M17 dashboard, mother-fund simulation, Token Hunter M33 paper-only) - take the NEXT unfinished one each run |
| M36 | PENDING | Autonomous world orchestration (after all above) |
| M53 | PENDING | Quarantine dead scaffold trees, run_ahos.sh, tests2b, slills (spec: reports/grok/autopilot/missions/M53-cleanup-dead-trees.md) |

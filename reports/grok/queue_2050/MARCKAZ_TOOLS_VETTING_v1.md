<!-- Tehran: 2026-10-09 16:54 (UTC+3:30) | Version: v1 | Author: Asi | Reason: vet @marc.kaz tools for AHOS against hard laws -->
# @marc.kaz tools: AHOS vetting v1
Hard laws: Windows laptop, 8 GB RAM floor, zero cost, legal public data only, and addenda only (no new parallel modules).
Sources: GitHub public REST API (the cursor-github connector returned "not connected"), READMEs, threads.com/@marc.kaz, nstarlive.com and its /about page.
X: get_users_by_username("marc_kaz") returned not found and search_posts_all returned 0, so the posts were confirmed on Threads instead.
Times below are Tehran (UTC+3:30), converted from GitHub UTC values.

## Verdict table
| # | Project | Repo / license | Last commit, stars | Verdict / slot |
|---|---|---|---|---|
| 1 | North Star (nstarlive.com) | No public repo found; license UNVERIFIED (closed site, "public demonstrator") | n/a | SKIP |
| 2 | img2threejs | github.com/img2threejs/img2threejs, Apache-2.0 (not MIT) | 2026-10-08 07:24, ~17.8k | SKIP (optional design-time note for M-D8) |
| 3 | OpenDots | github.com/CopilotKit/OpenDots, MIT | 2026-10-07 02:16, ~4.6k | SKIP |
| 4 | AgentConnect | github.com/agentconnect-md/agentconnect, Apache-2.0 (not MIT) | 2026-10-09 13:00, ~1.5k | Pattern-only addendum to M61 |
| 5 | REA (Reverse Engineer Anything) | github.com/morluto/rea, MIT (mark-brt/rea is a fork) | 2026-10-09 16:50, ~36k | SKIP |
| 6 | Single-photo to 3DGS | Exact project UNVERIFIED (the Threads post shows no link) | n/a | SKIP |

## Details
1. North Star: 250,000+ camera globe plus 8 more sectors (username/breached-DB lookups, NetScan port scanning, crypto tracing, "Fisherman" link intel with "exact GPS-capable visitor telemetry").
   - Data: viewing happens on their hosted site; they say detection runs in the browser. Camera ToS per feed: UNVERIFIED.
   - Risks: breached databases, port scanning and GPS tracking links break the legal-public-data law. Closed source, so nothing to self-host.
   - M18.N note: if Didehban ever wants a camera layer, use only official open feeds (DOT/TfL-style) with per-source ToS checks. Repo leads found but not vetted (license/ToS UNVERIFIED): GoSlowPoke168/Argus, 011-sam-110/Provenance.
2. img2threejs: an agent skill (Claude Code / Codex / OpenCode via `npx img2threejs`) that rebuilds one image as procedural Three.js code.
   - Data: the image and prompts go to whatever LLM the host agent uses, so token cost depends on the agent.
   - Fit: Python + Node, light on RAM. Not needed for the globe/tree map.
   - Optional: one-off asset generation for M-D8 at design time, never a runtime dependency.
3. OpenDots: needs CopilotKit Intelligence (hosted service, local Docker "evaluation", or a licensed self-hosted deployment) plus an OpenAI-compatible key and a speech provider.
   - Data: conversations go to CopilotKit Intelligence; the CPK_TELEMETRY_ID is tied to your account.
   - Risks: breaks zero cost (licensed or hosted parts) and wants Docker on 8 GB. Slack-centric. Overlaps the existing dashboard (M-D1..M-D4).
4. AgentConnect: multi-agent routing across Slack, Telegram, Discord, GitHub and more. Self-host runs Docker Compose (Web console, Control Plane, Relay, PostgreSQL); a Cloud tier also exists.
   - Data: messages go to the platforms you connect, plus your chosen LLM providers.
   - Risks: 4 containers plus Docker Desktop/WSL2 is tight on 8 GB, and it adds another bot-token holder (conflicts with AD-0128 / M35.3).
   - M61 addendum: borrow only its routing and allowlist pattern for telegram_ai/gateway. Do not deploy it.
5. REA: local CLI + MCP that decompiles and traces binaries, Electron/JS, .NET and websites.
   - Windows: Ghidra on Windows x64 is "experimental"; IDA Windows is verified (paid). Static JS/.NET needs no engine. Ghidra + JDK21 is heavy on 8 GB.
   - Data: analysis runs locally; results go to your agent's LLM.
   - Risks: reverse engineering third-party apps can breach EULA/anti-circumvention law. No AHOS slot fits.
   - Legal use only: auditing AHOS's own builds (outside these slots; M64 owner decision).
6. Single-photo splat: post says "depth lift, camera orbit, then a trained splat". Repo not identified.
   - Candidates seen, not confirmed as the posted tool: zju3dv/InfiniSplat (Apache-2.0, ~286 stars, downloads a Hugging Face checkpoint) and apple ml-sharp forks.
   - Risk: GPU/RAM heavy. No AHOS slot.

## UNVERIFIED
- North Star repo, license and camera-feed ToS.
- The exact splat tool.
- Licenses of Argus and Provenance.
- AgentConnect RAM use on Windows.
- Whether OpenDots works fully free with local Docker Intelligence.

Dedup: checked /workspace/out/DEDUP_MERGE_MAP.md (M18.N row 8, M61 row 1, M-D7 row 7) and ahos-teams/ahos-asi (M80 v1/v2). Nothing here creates a new module; the only action is a pattern note added to M61.

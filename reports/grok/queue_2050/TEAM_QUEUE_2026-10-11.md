# TEAM QUEUE 2026-10-11 02:13 Tehran (Soltan) — read before next step
Full source docs live on Soltan's box; this is the authoritative summary for Claude.

## Order after quota returns
1. Dashboard M-D5..M-D8 (Dashi queue below). M-D5.0 PRE-APPROVED by Mehrdad (2026-10-11 02:16): install the listed free packages (three, @react-three/fiber, drei, postprocessing, detect-gpu, zustand, three-globe, world-atlas, @react-three/rapier; ecctrl optional) without asking. Pin versions, log them in docs/dashboard/PACKAGES.md, free/MIT-class licences only, no paid or unknown packages.
2. Finish gold cycle work already in progress.
3. M59.S Idea Shelf, then M57.T Trend Hunter (Aji, below).
4. Asi shelf approvals (below), each as an addendum to an existing mission, never a new module.

## Dashi M-D5..M-D8 (each step: screenshot to reports/dashboard/screens/<mission>/ + sidecar json; Soltan QA vs reference board before owner sees it)
- M-D5.1 docs/dashboard/PROTOTYPE_REVIEW.md (read 4 prototype dirs only).
- M-D5.2 components/stage/Stage.tsx lazy (next/dynamic ssr:false): gold-lit empty stage centred in RTL shell, where the globe sits in ref 3.
- M-D5.3 components/stage/quality.ts: measure WebGPU/WebGL2, detect-gpu (local), 2 s frame test, RAM -> render tier T0..T3, user override; tier chip in TopBar; never from machine name.
- M-D5.4 context-loss fallback to M-D4 2D layout with Persian notice; no data loss on live tier switch.
- M-D5.5 Hardware Tier Panel (components/shell/TierPanel.tsx): hardware tier T8/T16/T32/GPU as main label, render tier beside it (T8->T0/T1, T16->T2, T32/GPU->T3), measured reason, override, RAM-guard state, list of ideas "منتظر ارتقا" from config/idea_shelf.json. Missing file -> grey UNKNOWN. No hard-coded idea names.
- M-D5.6 dev perf overlay within M-D12 budgets.
- M-D6 Globe: sun.ts selftest (1 deg), Globe.tsx dotted land (world-atlas ISC), gold Tehran mark, real terminator; ChainRings.tsx beads only from real opportunities[], UNKNOWN/CONFLICT no bloom; reduced motion; T2>=60 / T1>=30 fps, draw calls <=120.
- M-D7 PipelineGraph.tsx (3D) + PipelineGraph2D.tsx (T0, same nodes); TelemetryStrips (run log, gates, spend 0, ledger; stale = UNKNOWN); speech pulse only with real audio.
- M-D8 agents: read real sources first; /api/agents only if real source exists (fail-closed); AgentTower + AgentGrid2D (ref 5); walk mode T3 (T2 scaled, T1 teleport, T0 hidden); council room seats lit only from fresh votes.
- oil-ui (MIT) = workflow inspiration only (side-by-side variant screenshots, refine loop). Copy no code by default.

## Aji M59.S Idea Shelf
- core/idea_shelf/{registry.py, hardware.py, flags.py, ram_guard.py}; registry file = config/idea_shelf.json (single source shared with dashboard; JSON chosen over YAML). Entry: {id, title, tier, core, flag, est_ram_mb, priority, depends_on}.
- psutil detection (RAM/VRAM/cores/OS), fail-safe no GPU, cached, override in config. Auto-enable if tier fits + deps; log every decision.
- RAM guard: soft 80% shed lowest priority non-core; hard 90% shed all non-core; re-enable below 70% for 60 s. Paper core NEVER shed.
- Tests: mocked 8/16/32/GPU sets, shed order, core-never-shed property test, hysteresis, override, missing GPU driver safe.

## Aji M57.T Trend Hunter (proposes only, never installs)
- institute/trend_hunter/{sources,dedup,gate,score,digest,runner}.py; config/trend_hunter.yaml; config/vet_checklist.yaml (read-only to loop).
- Open sources only: GitHub API/trending, HF, arXiv, PyPI/npm RSS, Ollama library. No Instagram login.
- Gate per Asi 12-point checklist: identity/typosquat, licence (MIT/Apache/BSD allow; GPL/AGPL/NC flag), maintenance, $0 cost, hardware tier tag, Windows, egress/telemetry, security red flags (stealth, curl|bash, 0.0.0.0, Defender exclusions, plaintext keys => REJECT), ToS/legal, dedup to existing mission, paper-only, output INBOX line + Persian digest.
- Budget ~8k tokens/day: rules first, local ~3B model, Gemini free fallback, abort on cap. Once a day on existing scheduler.
- Tests: dedup, gate fixtures, token cap abort, offline fixtures, UTF-8 Persian digest, AST test: no pip/install calls.

## Asi verdicts (2026-10-11)
- APPROVE-SHELF: Laya NandhaKishorM/laya Apache-2.0 (M35.1 pre-filter, never a sole voter; RAM unverified), light-ocr arcships/light-ocr Apache-2.0 T8 sidecar (M18.N), Scientific Agent Skills MIT (M16), Codebase Memory MCP MIT (M30/M49), Diagram Design MIT (docs).
- APPROVE patterns only: nanobot HKUDS/nanobot MIT (M57/M70; must not replace M61 Telegram).
- APPROVE tool only (not runtime): Copy4AI GPL-3.0 — never include .env/dotfiles.
- SHELF T16: OpenSandbox Apache-2.0, Browser Use MIT.
- SKIP: PinchTab (stealth injection), OpenHarness (overlaps nanobot), Oriveo/MiroFish/Locally Uncensored (AGPL), nanoMuse (GPL), OpenWorkBuddy/pg-jev (licence unclear), Agent-Reach (ToS unverified), DeepWatch (identity unverified).
- REJECT: strix, invisible_playwright_mcp, REA, OmniGet.
- IGNORE: dimos, browser-games.


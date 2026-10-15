# CLAUDE_DASHBOARD_2050: upgrade layer for M-D1..M-D12
- Date: 2026-10-09 15:45 Tehran (UTC+3:30)
- Version: v1
- Author: Dashi (design agent), for Soltan, owner Mehrdad
- Base docs: DASHBOARD_DESIGN_SPEC.md, CLAUDE_BUILD_MISSIONS.md, OWNER_DECISIONS_Q1-Q10.md (those still win where this file is silent)
- Reason: owner asked for a "2050-level" build: the most advanced, fastest options, free only, 8 GB RAM as the floor, hardware tiers chosen at runtime, no hard-coded machine paths.

## Global rules (apply to every mission)
1. Free and open-source only, all assets bundled, 127.0.0.1 only. Reason: owner has no budget; offline is safer.
2. Two-source truth rule: one source = UNKNOWN, disagreement = CONFLICT, neither styled as success (no gold, no green, no success sound). Reason: owner law.
3. Tiers are picked at runtime from measured capability, never from the machine name: T3 Ultra (WebGPU + discrete GPU), T2 High (WebGPU or WebGL2, integrated GPU), T1 Low-power (WebGL2, reduced effects), T0 2D (no 3D). 8 GB is the floor. Reason: portable to a stronger PC later (M-PORT).
4. Every new file starts with a header: Tehran date and time, version, author, reason. Every decision gets a one-line reason in the mission report.
5. Persian RTL first; numbers in Persian digits, with a toggle. Reason: owner's language.

## Stack upgrades (decision -> reason)
- Renderer: three.js WebGPURenderer with automatic WebGL2 fallback; shaders in TSL (three.js shading language). Reason: the newest free GPU path, compute shaders, one shader code base for both backends.
- Off main thread: render in a Web Worker via OffscreenCanvas where supported; data parsing in a separate worker. Reason: the UI never janks while 3D runs.
- GPU compute: particles, globe arcs and graph layout run as WebGPU compute on T3/T2, on the CPU in a worker on T1. Reason: thousands of nodes at 60 fps.
- Data transport: a single local Server-Sent Events stream (/api/stream) with typed deltas plus snapshot-on-reconnect; schema validated with zod. Reason: live without polling; simpler than WebSockets on Next.js.
- Client state: TanStack Query for snapshots plus a tiny signal store for live deltas. Reason: minimal re-renders.
- Rendering budget: React Server Components for the shell, lazy client island for 3D, dynamic import per view. Reason: first paint under 1.5 s.
- Assets: glTF + meshopt + KTX2 (Basis) textures, self-hosted decoders. Reason: smallest GPU memory; no CDN.
- Post FX: pmndrs postprocessing (bloom, tone mapping AgX, SMAA), selective per tier; no SSR/SSGI below T3. Reason: cinematic look within budget.
- Text: troika-three-text with self-hosted Vazirmatn (no fallback fetch). Reason: crisp RTL 3D text, offline.
- Sound: Web Audio API with HRTF PannerNode plus AudioWorklet synthesis; muted by default. Reason: spatial sound with no paid assets.
- Window: Chrome/Edge --app with its own profile (per OWNER_DECISIONS); a second click focuses the existing window; boot token single-use, expires in under 60 s. Tauri 2 stays the documented upgrade path. Reason: zero new runtime on 8 GB.
- Local AI hooks (optional, T3/T2 only): WebGPU in-browser small model via transformers.js for "explain this widget" summaries, off by default. Reason: free and offline, but never a source of truth (shows UNKNOWN).

## Mission upgrades
- M-D1 Window: add focus-existing-window, single-use token under 60 s, and a /api/health check before the window opens. Accept: second click focuses within 1 s; reusing the token returns 401; screenshot of the window.
- M-D2 Offline: CSP connect-src 'self'; self-host Draco, meshopt, KTX2 decoders and fonts. Accept: a network log during a 5-min session shows zero non-127.0.0.1 requests.
- M-D3 Tokens: design tokens as CSS variables plus a TSL uniform mirror so 2D and 3D share the same palette. Accept: a snapshot test proves UNKNOWN and CONFLICT never use success tokens.
- M-D4 2D layout: RSC shell, RTL grid, container queries; this is T0 forever. Accept: Lighthouse performance score of 90 or more locally; RTL screenshot.
- M-D5 3D stage: capability probe (WebGPU adapter limits, a 2-second frame-rate test) picks the tier; adaptive resolution scaling keeps the frame-time target. Review the 5 old prototypes first. Accept: tier is logged with its reason; switching tiers live causes no data loss.
- M-D6 Globe: WebGPU compute arcs, real day/night line from the sun position, Tehran mark; chains remain conceptual rings until a real geographic source exists (UNKNOWN). Accept: 60 fps on T2 and 30 fps or more on T1 on the laptop.
- M-D7 Evidence graph: force layout in GPU compute (T3/T2) or a worker (T1); SSE live deltas; bottom strips for run log, gates, spend (always 0 / free) and ledger. Accept: 2,000 nodes on T2 without dropping below 50 fps.
- M-D8 Agent Society: instanced isometric floors; maturity only from a real read-only endpoint, otherwise UNKNOWN. Accept: no hard-coded maturity values (grep test).
- M-D9 Sound: HRTF spatial cues tied to camera position, AudioWorklet tones, Kenney CC0 files only; no success cue for UNKNOWN or CONFLICT. Accept: starts muted; mute persists after restart.
- M-D10 Boot and emblem: "golden path" boot under 2.5 s, skippable; our own Faravahar/coin vector rendered with a TSL gold material. Accept: reduced motion skips the animation.
- M-D11 Proof: automated perf run per tier (frame-time p95, GPU memory, RAM under 1.2 GB for the app on the 8 GB floor), axe accessibility pass, reduced-motion and low-power checks. Accept: report with numbers measured on the laptop, no estimates.
- M-D12 Acceptance: owner pack with a screenshot per view per tier, a 30-second screen recording, a list of known UNKNOWN sources, and an install/portable note for M-PORT.

## Order and gates
M-D1 to M-D4 now (no new 3D packages). M-D5 onward needs the owner's install approval for: three (WebGPU build), @react-three/fiber, drei, postprocessing, three-globe, troika-three-text, zod, @tanstack/react-query, and optionally @huggingface/transformers. Stop at each gate and report.

# FREE_HERO_FX_SOURCES v1
- **Date (Tehran):** 2026-10-09 16:52 +0330 · **Version:** v1 · **Author:** Dashi
- **Why:** the owner liked Textura agency's animated cinematic hero sections and wants free equivalents for the AHOS dashboard (Persian RTL, React 19 / Next.js 16, react-three-fiber 9, three.js WebGPU/TSL, Web Audio, offline, 8 GB laptop floor, real data only).
- **Method:** every license below was checked through `api.github.com/repos/<repo>/license` and, where flagged, the raw LICENSE file. Every URL returned HTTP 200 on 2026-10-09.

## Overlaps with REFERENCE_BOARD.md (not repeated here)
drei (incl. AdaptiveDpr and PerformanceMonitor), postprocessing / react-postprocessing, r3f, three.js examples, theatre.js, r3f-perf, detect-gpu, zustand, globe.gl / three-globe, 3d-force-graph, xyflow, howler and the GSAP license note are already on the board. The codrops rows below use GSAP, so they inherit the board's GSAP licence note.

## Sources (copy ideas or code into our own components; never import from a CDN)
| # | Source | License | Mission | How to adapt |
|---|---|---|---|---|
| 1 | [Magic UI](https://github.com/magicuidesign/magicui) | MIT | M-D4, M-D10 | Port Border Beam, Number Ticker, Particles and Animated Grid into `components/fx/`. Mirror x-offsets for RTL. Bind tickers only to live snapshot values. |
| 2 | [Motion Primitives](https://github.com/ibelick/motion-primitives) | MIT | M-D4, M-D10 | Rewrite Text Effect, Spotlight and Glow cards. Use per-word splitting (never per-glyph, because that breaks Persian joining). Return static text when reduced motion is on. |
| 3 | [shadcn/ui](https://github.com/shadcn-ui/ui) | MIT | M-D3, M-D4 | Base primitives for the 2D shell. Copy them in, swap `left/right` for logical `start/end`, and theme them from M-D3 tokens. |
| 4 | [Cult UI](https://github.com/nolly-studio/cult-ui) | MIT | M-D4 | Port selected shadcn-style animated blocks (dynamic island, texture cards) as hero panels. Keep the MIT header in each ported file. |
| 5 | [Animata](https://github.com/codse/animata) | MIT | M-D4, M-D10 | Pick background and text animations for the boot screen. Audit each one for `dir="rtl"`. Gate them behind the quality tier and run nothing on the low tier. |
| 6 | [Motion](https://github.com/motiondivision/motion) | MIT | M-D4, M-D10 | Animation engine for the 2D hero and boot. Use `useReducedMotion()` everywhere and bundle it locally from npm (npm gate). |
| 7 | [paper-design/shaders](https://github.com/paper-design/shaders) | Apache-2.0 | M-D4, M-D10 | Zero-dependency WebGL hero backgrounds (mesh gradient, grain, dot orbit). Keep the Apache NOTICE. Freeze to one static frame for reduced motion or low power. |
| 8 | [tsParticles](https://github.com/tsparticles/tsparticles) | MIT | M-D10 (2D fallback) | Canvas particle intro for the 2D path when WebGL is off. Use the slim bundle only. Cap particles per tier. |
| 9 | [pmndrs/uikit](https://github.com/pmndrs/uikit) | MIT | M-D5, M-D8 | In-scene 3D UI panels for the tower floors and dossiers. Verify RTL and Vazirmatn shaping before adopting. If shaping fails, fall back to HTML overlays. |
| 10 | [pmndrs/examples](https://github.com/pmndrs/examples) | MIT | M-D5, M-D6, M-D10 | Reference R3F scenes (staging, lighting, transitions). Rewrite the patterns we need. Do not copy their remote HDRI or model URLs; ship local assets only. |
| 11 | [pmndrs/react-three-next](https://github.com/pmndrs/react-three-next) | MIT | M-D5 | Next.js + R3F starter for the persistent-canvas/view pattern. Port that pattern into our lazy stage boundary. |
| 12 | [react-spring](https://github.com/pmndrs/react-spring) | MIT | M-D5, M-D8 | `@react-spring/three` for physical camera and tower transitions. Use `immediate: true` when reduced motion is on. |
| 13 | [maath (pmndrs/math)](https://github.com/pmndrs/math) | MIT | M-D5, M-D6 | Damping, easing and random-in-sphere helpers for globe beads and camera dolly. Pure math with no assets. |
| 14 | [THREE-CustomShaderMaterial](https://github.com/FarazzShaikh/THREE-CustomShaderMaterial) | MIT | M-D6, M-D10 | Extend standard materials for the emblem coin sheen and globe atmosphere. On the WebGPU path, rewrite as TSL node materials instead. |
| 15 | [N8AO](https://github.com/N8python/n8ao) | CC0-1.0 | M-D5 (high tier) | Ambient occlusion for the tower and coin on the high tier only. Disable it on the 8 GB floor. |
| 16 | [codrops/IntroGridMotionTransition](https://github.com/codrops/IntroGridMotionTransition) | MIT | M-D10 | Grid intro choreography for the boot (the "golden path" reveal). Rewrite in Motion or GSAP inside React. |
| 17 | [codrops/IntroTrailEffect](https://github.com/codrops/IntroTrailEffect) | MIT | M-D10 | Layout-change intro for the boot-to-command hand-off. Re-time it under 2 s and make it skippable. |
| 18 | [codrops/WebGLBlobs](https://github.com/codrops/WebGLBlobs) | MIT | M-D10, M-D6 | Noise-deformed sphere shader for the boot "core" or emblem backdrop. Port the GLSL to TSL. |
| 19 | [realism-effects](https://github.com/0beqz/realism-effects) | MIT | M-D5 (optional) | SSGI and motion blur ideas for cinematic stills only. WebGL-only and heavy, so off by default. |

## Common adaptation rules
- Keep the LICENSE text in `THIRD_PARTY_NOTICES.md` and the original header in each ported file.
- RTL: use logical CSS properties, mirror directional motion, split text by word, and test with Vazirmatn.
- Wrap every effect in a `prefers-reduced-motion` check and gate it by quality tier (high/med/low/2D). Low tier gets a static frame.
- Offline: vendor everything through the npm gate. No CDN, remote fonts, HDRIs or analytics (M-D2 CSP).
- Real data only: any counter, graph or particle that suggests metrics must bind to live snapshot fields. Decorative motion carries no numbers.

## Excluded or flagged
- **React Bits** (DavidHDev/react-bits): MIT + Commons Clause, which forbids redistributing "a ported version". Use it for ideas only, or flag it for the owner.
- **Aceternity UI**: custom licence at ui.aceternity.com/licence, not OSI, with marketplace and redistribution limits. Pro blocks are paid. Excluded.
- **Magic UI Pro and Animata/Cult Pro tiers**: paid. Excluded.
- **codrops/CrossroadsSlideshow** and other codrops repos with no LICENSE file: excluded. Check each codrops repo individually before using it.
- **Spline community files**: excluded for now. Licensing is per file and runtime export uses a hosted viewer (conflicts with offline).

# CLAUDE_DASHBOARD_2050 ADDENDUM v1.19 (folds INBOX DEDUP v1.18 + v1.19)
- Date: 2026-10-09 19:40 Tehran (UTC+3:30) · Version: v1.19 · Author: Dashi, for Soltan, owner Mehrdad
- Reasons: INBOX 2026-10-09 19:38 asks to fold walk mode + council room (v1.18) and the Kian Persian voice recap (v1.19) into existing missions, with no new mission. Base: CLAUDE_DASHBOARD_2050.md v1 (global rules 1-5 still apply and are not repeated here).
- Licence method: GitHub API `repos/<repo>` license.spdx_id and Hugging Face `api/models` tags / per-voice MODEL_CARD, checked 2026-10-09 19:40. Nothing here is already in the M-D docs, REFERENCE_BOARD or FREE_HERO_FX_SOURCES_v1.

## Verified libraries (new to the M-D docs only)
| Library / model | Licence (verified) | Used in |
|---|---|---|
| pmndrs/drei PointerLockControls + KeyboardControls (drei already approved at the M-D5 gate) | MIT | M-D8 walk |
| pmndrs/react-three-rapier (@react-three/rapier) on dimforge/rapier.js | MIT / Apache-2.0 | M-D8 walk collisions |
| pmndrs/ecctrl (optional; a ~150-line custom kinematic controller is the default) | MIT | M-D8 walk |
| Web Audio AnalyserNode (browser built-in, already part of the M-D9 Web Audio stack) | n/a (platform API) | M-D7 pulse, M-D9 |
| k2-fsa/sherpa-onnx (local sidecar, runs Piper VITS voices offline) | Apache-2.0 | M-D9 TTS |
| Piper voices rhasspy/piper-voices fa_IR amir, ganji, reza_ibrahim (medium) | CC0 (MODEL_CARD) | M-D9 TTS |
| ggml-org/whisper.cpp + ggerganov/whisper.cpp ggml weights (base or small) | MIT (weights from openai/whisper-*: Apache-2.0) | M-D9 STT |
| huggingface/transformers.js + openai/whisper-base (T3/T2 in-browser alternative) | Apache-2.0 / Apache-2.0 | M-D9 STT |
- Excluded: rhasspy/piper runtime (MIT but archived; its successor OHF-Voice/piper1-gpl is GPL-3.0, so we use sherpa-onnx instead); fa_IR "gyro" voice (MODEL_CARD says only "See URL", so the licence is unverified); ganji_adabi (licence not checked).

## M-D8 Agent Society: first-person walk + council room (v1.18)
- Walk: PointerLockControls + KeyboardControls (WASD/arrows, Shift to run, Esc to exit), rapier capsule against static floor/desk colliders; on-screen buttons for keyboard-only and touch users. Reason: proven free pmndrs stack, no new renderer.
- Council room: one fixed camera preset (no walking needed) showing the 10 council.ts teams around a table; seats light only from fresh `council`/`votes` rows, otherwise UNKNOWN. Reason: reuses the existing M-D8 evidence rule.
- Tiers: T3 full walk + physics; T2 walk at 0.75 render scale; T1 council room preset + click-to-teleport (no rapier); T0 walk disabled, 2D council grid from M-D4.
- Accept: T0 shows no walk button (snapshot test); a collision test keeps the camera inside the walls after 60 s of scripted input; Esc always releases the pointer; grep test finds no hard-coded seat activity.

## M-D7 Evidence graph: speech-reactive pulse (v1.19)
- While the recap plays, an AnalyserNode (fftSize 256, RMS) drives a TSL uniform that pulses only the node currently being read (glow + scale ≤ 1.15). Reason: links speech to evidence without fake activity.
- UNKNOWN nodes pulse grey, CONFLICT nodes pulse amber; neither uses success tokens. T1 pulses colour only; T0 highlights the 2D row.
- Accept: pulse stops within 200 ms of audio end; a token test proves UNKNOWN/CONFLICT pulses never use gold/green.

## M-D3/M-D4 Stat panels (real data only)
- Recap panels bind only to `/api/command` snapshot fields shown with their `generatedAt`; a missing or single-source field renders the UNKNOWN TruthBadge (Persian label نامعلوم), disagreement renders CONFLICT.
- Accept: a fixture with deleted fields shows نامعلوم in every affected panel; grep test finds no numeric literals in panel components.

## M-D9 Sound: Kian Persian voice recap, push-to-talk (v1.19)
- Muted by default; voice needs a separate opt-in toggle that persists. Push-to-talk only (hold Space or the mic button); no always-on mic; mic permission is asked on first press.
- STT: whisper.cpp base (T1/T2) or small (T3) as a 127.0.0.1 sidecar; transformers.js Whisper in a worker is the T3/T2 alternative. TTS: sherpa-onnx + a CC0 fa_IR Piper voice. Both run on 8 GB; models bundled locally (M-D2 CSP unchanged).
- Honesty rule: the recap script is generated from snapshot fields by a template, never by a model; it reads real values only, says «نامعلوم» for UNKNOWN, says «تعارض» for CONFLICT and never phrases CONFLICT or UNKNOWN as success; no success cue plays for them.
- Tiers: T3/T2 STT + TTS; T1 TTS only with typed commands; T0 TTS only (no 3D) with text transcript always shown.
- Accept: app starts muted with mic off; a fixture recap with UNKNOWN and CONFLICT fields is transcribed and contains نامعلوم/تعارض and no success words; network log shows zero non-127.0.0.1 requests during a voice session.

## M-D11 Proof additions
- Measure on the 8 GB laptop: walk mode frame-time p95 per tier, STT latency for a 5 s utterance, TTS time-to-first-audio, and RAM of app + sidecars (target: sidecars ≤ 1 GB extra, measured not estimated).
- Accept: report numbers per tier; if the RAM target fails, T1 drops STT automatically and the report says so.

## Gates
New npm/binary installs need owner approval at the M-D5/M-D9 gates: @react-three/rapier, ecctrl (optional), whisper.cpp binary + model, sherpa-onnx binary + fa_IR voice. Stop and report at each gate.

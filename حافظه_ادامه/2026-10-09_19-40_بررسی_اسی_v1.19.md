<!-- Tehran: 2026-10-09 19:40 (UTC+3:30) | Version: v1.19 | Author: Asi | Reason: vet KRYPT TRADER, skills-workspace, Persian STT/TTS -->
# ASI_VETTING v1.19 (instruction for Claude Code)
Laws: zero cost, free local tools only, paper only, no exchange or Kalshi keys, addenda only.
Read INBOX.md (Soltan 19:38) and LESSONS.md first. UNVERIFIED means don't build on it until checked.
Sources: GitHub public API, a shallow source scan of the Oben24 mirror, Hugging Face API, alphacephei.com, and the whisper.cpp README. Times are Tehran.

## Verdicts
| # | Item | Verdict | Why |
|---|---|---|---|
| 1 | KRYPT TRADER (Kalshi bot) | REJECT (ideas only, paper) | Kalshi blocks Iran; the original repo is gone; the installer adds a Windows Defender exclusion; binaries come from off-GitHub |
| 2 | nickjwells/skills-workspace | SKIP (read for patterns only, copy nothing) | No licence file (LICENSE returns 404), so all rights are reserved; mostly lead-gen/marketing skills |
| 3 | Persian STT/TTS for Kian | APPROVE: STT Vosk small-fa-0.5 (whisper.cpp small as fallback); TTS Piper fa_IR medium | Free, local, fits 8 GB, permissive or separate-process licences |

## 1. KRYPT TRADER: REJECT
- Origin: krypt.cc/tools/trader ("V6.4, free, open-source, no telemetry"). The original repo github.com/scripflipped/Krypt-Trader now returns 404 (deleted or private).
- Releases (v3.3, 24 Jun) pointed users to a setup exe on krypt.cc rather than a GitHub build, so the binary can't be matched to the source.
- Copies still online, both MIT ("Copyright (c) 2026 Krypt"):
  - github.com/Oben24/Krypt-Trader: 0 stars, created 2026-08-10 04:06, the account's only repo.
  - github.com/legaldusty/krypt-trader-universal: a macOS port with .dmg releases that can't be verified.
- RED FLAG: build/installer.nsh runs `powershell Add-MpPreference -ExclusionPath $InstDir`, which silently excludes the install folder from Windows Defender. This is a classic malware-staging pattern. Never run a krypt installer.
- Key handling (source looks OK): it stores the Kalshi key + RSA private key, encrypted with DPAPI (python/kalshi_auth.py), in local SQLite under %APPDATA%. No wallet, so no on-chain drain path.
  - Real risk: the account API key can place real orders, and the exe's contents are unverified.
- Network: the source contacts kalshi.com/demo, api.coingecko.com, api.coinbase.com, min-api.cryptocompare.com, discord (optional webhook) and krypt.cc links. No obvious eval or obfuscation in the source.
- Telemetry in the shipped binary: UNVERIFIED.
- Scam signs: original repo deleted, low-star mirrors from single-repo accounts, unsigned builds ("click Run anyway"), and the Defender exclusion.
- Ideas to reuse (paper only, re-implement, never copy code):
  - Demo + dry-run as default, with separate live switches → M21 kill-switch pattern.
  - Daily stop-loss/take-profit, trading-hours window and master kill switch → M21.
  - Fee-aware backtest on our own resolved signals → M28.1/M25.
  - Restart reconciliation of the book → M42 ledger.
  - Whale/momentum scoring as evidence features → M18.N / M24 (crypto data only, never Kalshi).

## 2. skills-workspace: SKIP
- 29 stars; last commit 2026-02-02 00:51 Tehran; no licence, so treat it as all rights reserved.
- Its 25 skills are mostly lead-gen/outreach (gmaps-leads, instantly-*, upwork-apply, gmail-inbox, youtube-outliers, video-edit). modal-deploy is a paid cloud service and local-server uses Cloudflare tunnels.
- Pattern worth noting: a SKILL.md with frontmatter (name, description, allowed-tools) plus deterministic scripts/*.py.
  - Use that structure for AHOS's own skills; write them ourselves.
- Loosely relevant to look at: literature-research (PubMed) for M16, generate-report (Open-Meteo PDF) for report templates.

## 3. Persian STT/TTS for Kian
| Tool | Persian quality | Licence | RAM (8 GB) | Verdict |
|---|---|---|---|---|
| Vosk vosk-model-small-fa-0.5 (60 MB) | Site WER 31.2 / 26.2 (test sets UNVERIFIED) | Apache-2.0 | Small (exact RAM UNVERIFIED) | STT PICK |
| Vosk vosk-model-fa-0.5 (1 GB) | Site WER 29.7 / 25.1 | Apache-2.0 | Higher (UNVERIFIED) | Optional |
| whisper.cpp (MIT) + OpenAI weights | Zero-shot large-v3: CV WER 44.4, FLEURS 36.1; large-v2: 53.0 / 39.2 (navidved leaderboard). Small/medium are worse (exact WER UNVERIFIED) | MIT | small ~852 MB, medium ~2.1 GB, large ~3.9 GB | Fallback (small/medium) |
| Piper fa_IR voices: amir, ganji, ganji_adabi, gyro, reza_ibrahim (all medium, ~63 MB) | Natural-sounding quality UNVERIFIED (no listening test) | Engine: rhasspy/piper MIT (archived 2025); active fork OHF-Voice/piper1-gpl GPL-3.0 (v1.8.0). Voice datasets CC0 (amir, ganji, reza_ibrahim); gyro "See URL" (UNVERIFIED) | Small (UNVERIFIED) | TTS PICK: fa_IR-amir-medium |
| MMS-TTS facebook/mms-tts-fas | UNVERIFIED | CC-BY-NC-4.0 | UNVERIFIED | SKIP (non-commercial) |
| Coqui TTS | Persian model UNVERIFIED | MPL-2.0 | n/a | SKIP (last push 2024-08) |
- Better Persian STT exists: navidved/gooya-v1.4 has CV WER 19.5. Its licence and size are UNVERIFIED; check them before use (M16 note).
- Windows install steps:
  - Vosk: run `pip install vosk`, download and unzip vosk-model-small-fa-0.5.zip from alphacephei.com/vosk/models, then feed 16 kHz mono WAV to KaldiRecognizer.
  - whisper.cpp: get the Windows x64 zip from GitHub Releases, download ggml-small.bin, then run `whisper-cli -m ggml-small.bin -l fa -f in.wav`.
  - Piper: `pip install piper-tts`, download fa_IR-amir-medium.onnx plus its .onnx.json from huggingface.co/rhasspy/piper-voices, then render text to WAV.
- GPL rule: call piper1-gpl only as a separate CLI process, never import it into AHOS. Alternatively use the archived MIT build.
- Kian slot: addendum to **M35.1+** (Kian core, DEDUP map item 7). Live paid voice M60.9 was cancelled (row 35), so this stays local and free. All audio stays local and nothing is uploaded.

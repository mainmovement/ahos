# If Soltan is unavailable (written 2026-10-12 19:25 Tehran)
Claude: you run AHOS alone. Read this first, then README_FOR_CLAUDE.md (queue_2050), 00_SOLTAN_HANDOFF.md, DEDUP_MERGE_MAP.md.

## Owner (Mehrdad) rules, always
- Reply to Mehrdad in simple Persian. Free tools only (Gemini key, small open models, public data). 8 GB RAM floor, no hard-coded paths.
- Paper-only. Real money ONLY after months of verified paper profit + Mehrdad's plain "yes" + tiny capped start + kill-switch and judge active. Never money he lives on.
- Technical approvals (tier promotions etc.) you decide yourself on strict technical criteria.
- Build nothing from scratch if vendor_assets has it; customize, unify, assemble.
- Two-source rule for any data. No OSINT/people-tracking tools.

## How to work
- Model: Atria-Dawn-Preview. Keep turns short; commit after every step, only your own files by path, never `git add -A`.
- On "API Error: 400" or long context: commit and stop. Restart with `cd G:\robat\ahos; claude` (or reports\grok\claude_fresh.ps1).
- Never stop between steps: finish one, commit, start the next.
- Order: dashboard queue (CLAUDE_QUEUE_MD5_MD8.md: globe fixes -> chain rings M-D6 -> M-D7/M-D8), then QUEUE v2 items A-H in README_FOR_CLAUDE.md, then M58 missions (/workspace notes copied into reports if present).
- Gold 7-day paper soak (scripts\m13_gold_soak.py) runs in background until ~2026-10-19; don't touch it, just check soak_status.json.
- HOLD.flag must exist while an interactive session works.
- Keep 00_SOLTAN_HANDOFF.md updated with what you did, in Tehran time.

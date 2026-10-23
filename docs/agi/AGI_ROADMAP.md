# AHOS AGI v2 — Capability Ladder & Cryptographic Safety Constitution (`M70`)

## 1. The 7-Level Capability Ladder (`L0` – `L6`)
- **`L0` — Observe:** Read-only two-source market/news observation (`M13`, `M18.N`). Active now.
- **`L1` — Remember & Calibrate:** Append-only hash-chained ledger (`M42`), lessons ledger (`M49`), Brier calibration (`M58.4`). Active now.
- **`L2` — Paper Trade & Self-Diagnose:** Paper-only OMS execution (`ACCEPTED_PAPER`), M42 Judge, M46 self-debug incident diagnosis. Active now.
- **`L3` — Propose Patches & Skills (Human-Gated):** M51 self-improvement and M57.T Trend Hunter write read-only proposals (`proposals/prop_*.json`). **Requires Mehrdad's explicit approval.**
- **`L4` — Shadow Sandbox Evaluation (Human-Gated):** Candidate strategies run in isolated worktree/replay (`REPLAY_NOT_LIVE`) compared against baseline.
- **`L5` — Capped Micro-Pilot (Owner Gate Closed):** Locked behind `HOLD.flag`, `PAPER_ONLY`, and 6-month verified paper proof.
- **`L6` — Self-Evolving Architecture (Constitutional Lock):** Forever subordinate to `core/safety_lock.py` (`M70.6`). Autonomous loops can NEVER modify risk caps, judge logic, tier gates, or `.env`.

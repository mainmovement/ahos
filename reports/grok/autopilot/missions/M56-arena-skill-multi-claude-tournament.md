# M56: Arena skill (multi-Claude tournament) for high-stakes decisions — integration plan

Owner directive 2026-10-07 (Mehrdad). Status: **PLAN / VISION — nothing installed.** PAPER_ONLY, safety gates locked, no push. Extends existing registry entries "Multi-Mind Council" (PLANNED), "Consensus/Disagreement Engine" (PARTIAL) and "Red Team" (PARTIAL) in config/agent_registry.yaml — do NOT create a parallel agent.

## 1. What exists (verified 2026-10-07)
| Option | Link | License | How it works |
|---|---|---|---|
| **arena-skill** (closest match to "16 Claudes compete") | https://github.com/Jakeschincariol/arena-skill (listing: https://www.claudepluginhub.com/plugins/jakeschincariol-arena-skill) | MIT (~310★, pushed 2026-09-27) | `/arena`: N sub-agents (default 100, `--quick` = 16) get the identical task + a different strategy card; single-elimination bracket; each pair attacks/defends/revises; a separate judge scores on a rubric (correctness 30, completeness 25, robustness 20, specificity 15, clarity 10); `bracket.py` does the arithmetic; a verified fatal flaw can't win. |
| **pstack `arena`** (best-of-N + graft) | https://github.com/cursor/plugins/tree/main/pstack/skills/arena | not declared in repo metadata — check before vendoring | Fan out N candidates, cross-judge on a different model family, pick a base, graft the best ideas from losers, verify. Built for Cursor; pattern is portable. |
| **agent-arena** (heterogeneous debate) | https://github.com/zhjai/agent-arena | MIT (~26★) | Evidence-first debate: Claude Code × Codex (or others) analyse independently, critique, verify evidence, blind-judge, preserve dissent. Modes incl. `red_team`, `full_arena`. |

The listing claims were checked against the source; still read SKILL.md + bracket.py before any use (third-party code = untrusted).

## 2. Install (for later, NOT done) — Claude Code on Windows
```
/plugin marketplace add Jakeschincariol/arena-skill
/plugin install arena
```
Alternatively clone and copy `skills/arena` into `%USERPROFILE%\.claude\skills\` (user) or `G:\robat\ahos\.claude\skills\` (project). Requires Python on PATH for bracket.py. Pin a commit hash; review diff on update.

## 3. Cost / Atria quota (honest)
- Tokens ≈ N candidates × (task + output) + attack/defense rounds + (N−1) judge matches. 16-way bracket ≈ 15 matches ⇒ realistically **~30–50× a single answer**; default 100-way ≈ 200–300×. **Never use default 100.**
- AHOS policy: `--quick` (16) max; default N=4–8 for most arena calls; Cost/Resource Manager enforces a per-run token cap and a daily arena budget; abort if the quota is under 30%.
- Wall-clock: parallel sub-agents ⇒ ~3–6 single-answer latencies for 16-way (log₂16 = 4 rounds).

## 4. Where to use (only high stakes)
Use: architecture ADRs, security design / threat models, strategy changes (risk params, autonomy-tier proposals), irreversible migrations, post-incident root cause.
Do NOT use: routine code, docs, scanning, any trade-time path (latency + cost), anything a deterministic test can decide.
Arena output is a **proposal only** — authority NONE; it never bypasses the Execution Gateway, Ramin risk, kill switch or human gates.

## 5. Fit with the 19-agent sign-off
1. Lead agent frames the task + rubric (rubric must include AHOS invariants: PAPER_ONLY, no keys, fail-closed).
2. Arena runs (N≤16); judge = different model family where possible (pstack/agent-arena pattern) to cut self-preference bias.
3. **Erfan (evidence)** checks every factual claim in the winner and logs the bracket transcript hash in the evidence ledger.
4. **Reza (red team)** attacks the winner independently — the arena's internal attacks don't replace him.
5. **Qasem (QA)** verifies tests/acceptance; then normal 19-agent sign-off; human gate if the change touches rules/money/tiers.
6. Dissent (runner-up + its strongest attack) is preserved in the record.

## 6. Acceptance criteria
- Skill source reviewed, commit pinned, MIT license file recorded; installed only after owner OK.
- Wrapper/config enforces N≤16, token cap, daily budget, quota floor; tested with a mock.
- Trigger list = high-stakes only; a test shows routine tasks are refused.
- Each run produces: rubric, bracket scores, winner, runner-up dissent, token cost, evidence hash.
- One pilot on a real ADR, compared to the single-agent answer; Qasem/Reza/Erfan sign off; result documented honestly (incl. "no improvement" if so).

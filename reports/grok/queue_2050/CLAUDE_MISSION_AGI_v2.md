<!-- Date: 2026-10-09 15:43 Tehran (UTC+3:30) | Version: v2.0 | Author: Aji (for Soltan/Mehrdad) | Supersedes: CLAUDE_MISSION_AGI_RESEARCH.md
Reason: owner asked for the most advanced, fastest FREE open-source methods, under a strict token budget, with all hard laws kept. -->
# CLAUDE MISSION M70 v2: AHOS autonomy, self-debug, self-improvement, evals
Executor: Claude, on the laptop. You do the research, verification, downloads, and code yourself.
Rule for every file you create: it must start with the Tehran date and time, the version, the author, and the reason for each choice.

## 0. HARD LAWS (any violation means stop and report)
1. Zero cost. Only free tools, Mehrdad's free Gemini key, free local models, and public data. No paid APIs, subscriptions, or card trials.
2. Portable. No hard-coded paths. Windows first. Detect RAM, VRAM, and CPU at runtime and pick model and 3D tiers from them. 8 GB is the floor, not the ceiling.
3. PAPER_ONLY. No real money and no irreversible external actions.
4. Two-source rule. Back every license, version, and benchmark claim with two independent sources, and record both.
5. Forbidden: `.env` or secrets, `git push`, DB flips or migrations, Lane A.
6. No self-modifying safety. Loops may never edit safety rules, gates, University criteria, eval sets or thresholds, or this list. Enforce this with code (M70.6) and a hash check.
7. Licenses. Prefer MIT, Apache-2.0, or BSD. Flag GPL, AGPL, NC, and custom model licenses (Llama, Gemma) before adopting.
8. Reversible. Every change goes on a branch or worktree, comes with rollback steps, and never deletes user data.
"Future-grade" means current, verified, maintained open source. Never pin a version you haven't fetched.

## 1. First: read the repo
Read the README, the continuity and plan docs, the mission history, and the University pipeline. Extend existing modules and never build parallel ones. Number new missions M70.x.

## 2. Method stack: candidates to verify (reason per pick)
- Inference: llama.cpp (GGUF, speculative decoding, grammar-constrained JSON) and Ollama as the friendly runner. Reason: fastest free CPU path on 8 GB, and both run on Windows.
- Model tiers (pick at runtime): T0 8 GB uses about 1.5-4B at Q4_K_M (Qwen3/Qwen2.5-Coder small, Phi-4-mini). T1 16 GB uses about 7-8B coder Q4. T2 32 GB or a GPU uses about 14B+. Gemini free is the fallback for hard tasks. Reason: strongest open coder or reasoner per GB, with license noted.
- Structured output: grammar or JSON-schema decoding (llama.cpp GBNF, Outlines or XGrammar). Reason: removes parse failures and makes small models reliable tool users.
- Orchestration: a graph or state machine with checkpoints (LangGraph or smolagents, whichever fits AHOS). Reason: resumable runs, a human interrupt, and replayable traces.
- Self-debug: a localize, patch, test loop in the style of Agentless/SWE-agent, with Reflexion-style failure memory. Reason: the best published fix rates without needing a giant model.
- Search over fixes: generate N candidate patches, rank them by tests, then use a small model as judge. Reason: test-time compute instead of model size.
- Self-optimization: DSPy optimizers (MIPROv2/GEPA-style) and TextGrad on prompts and programs against FROZEN evals. Reason: measurable gains with no training cost.
- Evals: inspect_ai or promptfoo plus the repo's own tests, with seeded-bug suites and small HumanEval/MBPP/SWE-bench-Lite subsets. Reason: offline, scriptable, and CI-friendly.
- Sandbox: git worktree plus a subprocess with timeouts and resource limits (Windows Job Objects; firejail or bubblewrap on Linux). Reason: free, fast, and you can roll back instantly.
- Evolution (gated, later): archive-based open-ended search in the style of Darwin-Gödel-Machine and ADAS that proposes PR drafts only. Reason: the frontier method, kept safe by human merge.
Output: `docs/agi/SOURCES.md` with name, URL, license, pinned version, last release, two sources, an 8 GB/Windows check, and the reason.

## 3. Capability ladder: `docs/agi/AGI_ROADMAP.md`
Each level lists its definition, tests, numeric thresholds from a MEASURED baseline, a University gate, rollback, and a promote or demote rule.
L0 Observe: structured traces for every task. L1 Diagnose: at least 80% of labeled failures classified correctly.
L2 Self-debug: fixes seeded bugs in a sandbox with 0 regressions, and a human merges.
L3 Self-develop: builds a scoped feature from a mission file, and a human merges.
L4 Self-update: upgrades pinned deps or models, with auto-rollback if the eval score drops.
L5 Self-optimize: keeps a DSPy or TextGrad change only if it beats baseline on a held-out set.
L6 Self-evolve: architecture PR drafts only, never auto-merged, and safety files untouchable.

## 4. Implementation (one local branch each, no push)
- M70.1 Hardware probe and tier selector. Extend the existing config or model loader, with tests on mocked 8/16/32 GB machines on Windows and Linux.
- M70.2 llama.cpp/Ollama adapter behind the existing LLM interface, with grammar-constrained output and Gemini fallback. Add contract tests.
- M70.3 Eval harness wired into the University pipeline, with a frozen eval set, a baseline report, and an offline run on T0.
- M70.4 Sandbox runner with worktrees, limits, auto-revert, and trace capture. Add a test that a bad patch is reverted.
- M70.5 Self-debug loop (L1-L2) with N-candidate patches ranked by tests, producing a report and PR draft. Add a seeded-bug suite.
- M70.6 Safety lock: safety files are read-only to every loop, with a hash check at startup, and blocked attempts are logged. Add tests.
Stop after M70.6 and report. L3 and above need approval from Mehrdad or Soltan.

## 5. Acceptance
`SOURCES.md` and `AGI_ROADMAP.md` exist with headers. M70.1-6 are green and run on an 8 GB machine with the T0 model.
The run cost nothing. `.env`, push, DB, and Lane A were untouched, and `git diff` on the safety files is empty.
Report what was built, pins and licenses, baseline metrics, rollback steps, and risks.
If blocked, stop and report. Never work around a hard law.

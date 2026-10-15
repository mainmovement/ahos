# CLAUDE MISSION M70 — AGI Research, Roadmap & First Implementation (AHOS)

Owner: Mehrdad. Coordinator: Soltan. Author: Aji. Executor: Claude (on the laptop).
You do ALL research, license checks, downloads, roadmap writing and implementation yourself, locally.

## 0. HARD LAWS (non-negotiable; violating any = stop and report)
1. ZERO COST: free tools only. Allowed: Mehrdad's existing free Gemini key, free open-source models/libraries, public data. No paid APIs, subscriptions, trials needing a card, or purchases.
2. PORTABLE: never hard-code machine paths or usernames; use config + relative paths. Must work on Windows (installer/portable package M-PORT is planned). Detect hardware (RAM/VRAM/CPU) at runtime and pick model + 3D tiers from it. 8 GB RAM is the FLOOR, not the ceiling.
3. PAPER_ONLY: no real-money trades, payments, or irreversible external actions.
4. TWO-SOURCE RULE: any factual claim used for a decision (license, version, benchmark) needs two independent sources; record both.
5. FORBIDDEN: reading/editing/committing `.env` or secrets; `git push`; flipping/migrating the production DB; touching Lane A.
6. NO SELF-MODIFYING SAFETY: self-improvement code may never edit safety rules, safety gates, University pipeline criteria, eval thresholds, or this law list. Mark those files read-only to the loop; only a human changes them.
7. Licenses: prefer MIT / Apache-2.0 / BSD. Flag GPL/AGPL/non-commercial and custom model licenses (Llama, Gemma) — do not adopt without noting it.
8. Every change must be reversible (git branch/worktree + documented rollback). Never delete user data.

## 1. Before anything: read the repo
- Read the AHOS repo README, existing plan/continuity docs, mission history, and the University pipeline module.
- List existing modules for: agent loop/orchestration, evals, debugging, updates, model loading. EXTEND these. Do NOT create parallel modules. If something truly new is needed, justify it in the PR notes.
- Continue the repo's existing mission numbering as M70.x.

## 2. Research (time-box: ~2 hours total; keep notes short)
For each area, shortlist 1–3 candidates. Record: name, URL, license, latest stable version/tag, last release/commit date, fits-8GB?, Windows OK?, two sources.
a) Self-debug / self-repair loops (e.g. Aider, OpenHands, SWE-agent, Reflexion/Self-Debugging papers).
b) Agent orchestration (e.g. LangGraph, smolagents, AutoGen).
c) Eval harnesses (e.g. inspect_ai, promptfoo, lm-evaluation-harness; small task sets like HumanEval/MBPP/SWE-bench Lite subsets).
d) Prompt/program self-optimization (e.g. DSPy, TextGrad).
e) Sandboxed self-improvement with rollback (git worktrees, subprocess/container sandboxes that work on Windows; ideas from ADAS / Darwin-Gödel-Machine papers).
f) Local LLMs via Ollama or llama.cpp, tiered: T0 = 8 GB CPU (≈1.5–4B Q4), T1 = 16 GB, T2 = 32 GB+ or GPU. Note each model's license.
Prefer reusing what AHOS already depends on. Pin exact versions only after verifying them.
Output: `docs/agi/SOURCES.md` (table above).

## 3. Roadmap
Write `docs/agi/AGI_ROADMAP.md` — capability ladder, each level with: definition, acceptance tests, metrics with numeric thresholds, University-pipeline safety gate, rollback, promote/demote rule.
- L0 Observe: structured logs + error capture for every task.
- L1 Self-diagnose: classifies its own failures; ≥80% correct on a labeled failure set.
- L2 Self-debug: proposes + tests fixes in a sandbox branch; ≥X% of seeded bugs fixed, 0 regressions on full test suite; human merges.
- L3 Self-develop: implements small scoped features from a mission file in a sandbox; passes tests + University review; human merges.
- L4 Self-update: safely upgrades pinned deps/models; auto-rollback if eval score drops.
- L5 Self-optimize: DSPy-style prompt/program tuning against frozen evals; only keeps changes that beat baseline on held-out set.
- L6 Self-evolve (gated): proposes architectural changes as PR drafts only; never auto-merges; safety files untouchable.
Choose X and other thresholds from a measured baseline; write the baseline into the doc.

## 4. Implementation (do in order; one small PR-ready branch each, no push)
- M70.1 Hardware probe + tier selector: extend existing model-loading/config module. Detect RAM/VRAM/OS → choose model tier from a config table. Tests: mocked 8/16/32 GB machines. Windows + Linux.
- M70.2 Local LLM adapter: Ollama/llama.cpp backend behind the existing LLM interface, Gemini (free key) as fallback. Tests: adapter contract tests with a stub server.
- M70.3 Eval harness: wire the chosen harness to the University pipeline; frozen eval set + baseline report. Tests: harness runs offline on T0.
- M70.4 Sandbox + rollback: git worktree/branch sandbox runner with timeout, resource limits, auto-revert on failure. Tests: failing patch is reverted cleanly.
- M70.5 Self-debug loop (L1–L2): capture error → diagnose → patch in sandbox → run tests + evals → produce report/PR draft for human. Tests: seeded-bug suite.
- M70.6 Safety lock: enforce read-only on safety rules/gates/eval thresholds for all self-improvement code paths; test that attempts are blocked and logged.
Stop after M70.6 and report. L3+ needs Mehrdad's/Soltan's approval.

## 5. Acceptance for this mission
- `docs/agi/SOURCES.md`, `docs/agi/AGI_ROADMAP.md` exist and follow sections 2–3.
- M70.1–M70.6 on local branches, all tests green, runs on an 8 GB machine with T0 model.
- No cost incurred, no `.env` touched, no push, no DB change, no Lane A change, safety files unchanged (show `git diff` on them is empty).
- Short report: what was built, pinned versions + licenses, baseline metrics, rollback steps, open risks.

## 6. If blocked
Stop, write the blocker into the report, and wait. Do not work around a hard law.

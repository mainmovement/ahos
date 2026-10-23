# AHOS AGI v2 — Vetted Open-Source Foundations (`M70.1–M70.6`)

| Component | Open-Source Reference | License | Hardware Tier | AHOS Integration |
|---|---|---|---|---|
| `M70.1` Hardware Probe | `psutil` | BSD-3-Clause | `T8` | `core/idea_shelf/hardware.py` & `ram_guard.py` |
| `M70.2` Local LLM Adapter | `Ollama` / `llama.cpp` JSON grammar | MIT | `T8` / `T16` | `architecture/ai/kian_agent.py` & local bridge |
| `M70.3` Frozen Eval Harness | `scikit-learn` / `brier_score` | BSD-3-Clause | `T8` | `architecture/learning/calibration.py` & `benchmark.py` |
| `M70.4` Worktree Sandbox | `git worktree` + Windows Job Objects | GPL-2.0 (CLI tool) | `T8` | `architecture/health/lab_gate.py` (owner-gated) |
| `M70.5` Self-Debug Loop | SWE-agent / Aider diff-proposal pattern | MIT / Apache-2.0 | `T8` | `architecture/learning/self_debug.py` (proposals only) |
| `M70.6` Safety Lock | SHA-256 immutable manifest | Internal | `T8` | `core/safety_lock.py` & `architecture/health/safety_lock.py` |

---
name: ahos-domain-backend
description: AHOS Python backend — domain services, deterministic engines, persistence, APIs, async, tests. Use for architecture/*, engine/*, strategy_lab/*, config/*, contracts/*.
paths:
  - "architecture/**"
  - "engine/**"
  - "strategy_lab/**"
  - "contracts/**"
  - "config/**"
  - "telegram_ai/**"
---

# AHOS domain backend

Canonical packages: `architecture/` (Lane B), `engine/`, `strategy_lab/`,
`telegram_ai/` (gateway), `config/`, `contracts/`.

Do not edit frozen `discovery/` or `paper_trading/`. Compose their results.

Key entrypoints:

- Intelligence floor: `architecture/intelligence/engine.py`
- Decision advisor (AI downgrade only): `architecture/decision/advisor.py`
- Pipeline: `architecture/pipeline/orchestrator.py`
- Score ledger: `architecture/learning/score_ledger.py`
- Evidence: `architecture/intelligence/evidence.py`
- Security Lane B: `architecture/security/`
- Provider collect: `architecture/providers/collect.py`

Evidence Architecture law: intelligence / risk / features / scoring /
explanations must not import `discovery`, `paper_trading`, `telegram_ai`, or
`engine`.

Prefer extending tested modules over new parallel packages. Add pytest with
fail-closed cases. Keep `AHOS_PAPER_ONLY=1`.

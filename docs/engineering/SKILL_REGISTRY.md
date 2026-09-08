# AHOS Cursor Skill Registry

Progressive load only. Do not inject every skill into every prompt.

Inspected 2026-09-08 (Phase 3 re-check):

| Path | Result |
|------|--------|
| `G:\robat\ahos\cursor\slills` | Windows local path — **not a git directory** |
| `cursor/slills` | **Absent** |
| `slills/` at repo root | **Present** — 16 uploaded `SKILL*.md` files (Poteto-style / third-party). **Not** AHOS Cursor project skills. Do not load as `.cursor/skills`. Do not delete. |
| `.cursor/skills/` | **Canonical** — eleven `SKILL.md` files |

Do not rename `slills/` into `.cursor/skills`. Do not treat uploaded SKILL dumps as the AHOS registry.

| Skill | Purpose | When | Model preference | Risk |
|-------|---------|------|------------------|------|
| ahos-governance-context | One Brain, Lane A, phase gates | almost always | any | low token |
| ahos-domain-backend | Python architecture | backend | Sol / Sonnet | medium |
| ahos-change-verification | freeze, tests, phase record | before COMPLETE | fast then strong | medium |
| ahos-token-identity | chain/address/pool | discovery / identity | Sol + Opus if conflict | high |
| ahos-security-analysis | white-hat token security | token security / overlay | Opus for review | high |
| ahos-market-intelligence | market structure | opportunity tasks | Sol / fast | medium |
| ahos-research-intelligence | news → evidence | research | Sol / fast | medium |
| ahos-opportunity-hunter | candidate ranking only | hunt, not decide | Sol | medium |
| ahos-ai-council | 2–4 lenses, no upgrade | council work | Sol | medium |
| ahos-web-experience | Next/RTL/browser | web | Sonnet / fast | medium |
| ahos-product-intelligence | revenue without FOMO | product | medium | low |

Forbidden: Superpowers, ralph-loop, Continual Learning, uncontrolled loops.

---
name: ahos-ai-council
description: Advisory AI Council — select 2–4 lenses, independent responses, evidence packet, abstention, red-team, no authority upgrade.
paths:
  - "architecture/council.py"
  - "architecture/ai/**"
  - "architecture/knowledge/**"
  - "architecture/decision/**"
disable-model-invocation: true
---

# AHOS AI Council

Ten logical families exist as a design surface. Do not run all ten every time.
Select 2–4 relevant lenses. Produce independent responses before comparison.
Do not leak other agents' answers before submission. Do not average scores.

Existing: `architecture/council.py` (advisory_only),
`architecture/ai/council_live.py`, `architecture/knowledge/panel.py` (currently
runs all PANEL_LENSES — do not treat that as the target 2–4 router),
`architecture/decision/advisor.py` (downgrade-only ratchet).

Cache key: `evidence_packet_hash + policy_version`.
Missing evidence ⇒ ABSTAIN / INSUFFICIENT.
Material conflict ⇒ explicit CONTRARIAN / red-team.

AI cannot upgrade identity, security, confidence, or recommendation.
TS `council.ts` is a heuristic duplicate — do not extend it as authority.

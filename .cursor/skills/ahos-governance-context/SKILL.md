---
name: ahos-governance-context
description: AHOS project laws — One Brain, Lane A freeze, no second brain, phase gates, evidence discipline, Git/PR rules. Use at session start and for any architecture or governance question.
---

# AHOS governance context

Read, do not copy: `docs/DOC_TRUTH_MAP.md`, `docs/canonical/MASTER_DIRECTIVE_v1.md`,
`AGENTS.md`, `AHOS_GAP_REGISTER.md`.

## Laws

1. One Python decision brain. TypeScript/Telegram/n8n/AI are edges or advisors.
2. Lane A (`discovery/**`, `paper_trading/**`) is FROZEN.
3. Do not rebuild AHOS. Reuse existing modules. Remove duplication only when
   equivalence is proven.
4. PAPER_ONLY. No wallets, no live orders.
5. UNKNOWN / INCOMPLETE / CONFLICT never become PASS or a positive recommendation.
6. Do not rewrite historical evidence or fabricate operational SUCCESS.
7. Phase status is COMPLETE only when mandatory gates were actually executed.
8. No Superpowers, ralph-loop, Continual Learning, auto-merge, or force-push.

## Existing dual-stack (do not widen)

`scoring.ts`, `engine.ts`, `council.ts`, `alerts.ts` currently score and alert
independently of Python. Documented in `docs/CANONICAL_IMPLEMENTATION_MATRIX.md`.
New work must consume canonical Python state rather than grow this gap.

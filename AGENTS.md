# AHOS developer-agent contract

Start with `docs/DOC_TRUTH_MAP.md`. Current canonical authority and open gaps
override historical readiness prose. This file is the Cursor engineering
contract. It does not replace `docs/canonical/MASTER_DIRECTIVE_v1.md`.

AHOS is a PAPER_ONLY crypto opportunity-intelligence system, never a trading
bot. `UNKNOWN > fabricated`. No FOMO, urgency, guaranteed-return, or
positive-authority language may replace evidence.

## Authority

- Lane A (`discovery/**`, `paper_trading/**`) is FROZEN. Never edit it or
  regenerate `config/lane_a_freeze.sha256` without an explicit reviewed
  governance request. `python scripts/freeze_lane_a.py --write` is human-only.
- Python Lane B owns canonical identity (`architecture/identity/`, wrapping
  frozen `discovery/identity.py`), security, deterministic decisions,
  persistence, and provenance.
- TypeScript/Next.js is an authenticated API, read model, and presentation
  surface. It must not create an independent recommendation authority.
  Existing `scoring.ts` / `engine.ts` / `council.ts` / `alerts.ts` are a
  documented dual-stack gap — do not widen them.
- Telegram is an interaction edge; n8n is an automation edge.
- Providers and AI are evidence/advisory inputs only. They cannot override
  identity conflict, security rejection, insufficient evidence, or canonical
  deterministic authority. AI may downgrade or abstain; it cannot upgrade.

## Safety

Never enable live trading, wallets, or real funds; change credentials; use
paid services without explicit owner approval; destroy data; rewrite
historical evidence; weaken tests; force-push; auto-merge; or push to `main`.

Do not commit secrets. Do not put tokens in `NEXT_PUBLIC_*`. Do not copy
operator `.env` into worktrees. Do not present empty-VM databases as soak
evidence.

Hooks in `.cursor/hooks.json` are a speed bump, not a security boundary.
Enforcing controls are Lane A hashes, `scripts/validate_imports.py`,
CODEOWNERS, tests, and human PR review.

Do not install Superpowers, ralph-loop, or Continual Learning. Do not run
uncontrolled autonomous loops.

## Workflow

Use isolated worktrees for concurrent writers. Isolate databases, ports,
runtime processes, and evidence paths. Never share SQLite/Postgres between
worktrees.

Before editing: state scope, authority surface, and verification.
After editing: Lane A integrity, the narrowest relevant existing gates, and
honest phase status (`NOT_STARTED` / `IN_PROGRESS` / `BLOCKED` / `PARTIAL` /
`VERIFIED` / `COMPLETE`). Only `COMPLETE` unlocks dependent phases.

Load only the Skill that matches the task. Prefer:

- exploration / mechanical work: fast models
- implementation: strong models
- identity / security / architecture / final review: strongest models plus
  an independent security reviewer

Readiness vocabulary is limited to artifact-backed AHOS classifications.
Blocked external checks remain `BLOCKED` or `NOT_VERIFIED`.
Current product classification: `INTEGRATION_READY` (agent-host).
`OPERATOR_READY` and `PRODUCTION_READY` require real operator evidence.

## Definition of Done

Requested behavior is integrated; relevant tests pass; Lane A integrity
passes; security and authority boundaries remain intact; evidence receipts
are recorded without overwriting history; the diff is independently
reviewed; no unsupported readiness claim remains.

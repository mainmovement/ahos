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
  frozen `discovery/identity.py`), the security overlay (`architecture/security/gate.py`:
  projects `SecuritySignals` onto frozen CRITICAL keys and calls
  `discovery.security_gate.evaluate`; PASS/REJECT/INCOMPLETE/STALE; does not
  copy the evaluator), the canonical decision authority
  (`architecture/decision/authority.py` wrapping `DecisionAdvisor`; pipeline
  identity → evidence → security → liquidity → score → risk → confidence →
  optional AI downgrade → decision), persistence, and provenance.
  OpportunityScorer scores; it does not decide.
- TypeScript/Next.js is an authenticated API, read model, and presentation
  surface. It must not create an independent recommendation authority.
  `scoring.ts` / `council.ts` remain non-authoritative analysis. They may rank
  and fail-closed REJECT/ABSTAIN for display, but they must not emit
  WATCH/PAPER_CANDIDATE without an injected Python `canonicalBackend`.
  Automatic OPPORTUNITY Telegram (`alerts.ts`) requires Python `alerts_allowed`
  (BUY) **and** canonical overlay PASS. `POST /api/paper` OPEN requires Python
  `paper_allowed` **and** overlay PASS. Local OBSERVED/UNKNOWN is not security
  authority.
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

<!-- BEGIN:nextjs-agent-rules -->

# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->


## Unattended operation
- Never ask the owner questions or wait for approval (no plan-mode approval waits, no multiple-choice prompts).
- Choose the safest option consistent with PAPER_ONLY and the docs, record the decision in reports/grok/DECISIONS_LOG.md (date, question, choice, reason), and continue.
- Never push to GitHub; never print secrets/.env contents.


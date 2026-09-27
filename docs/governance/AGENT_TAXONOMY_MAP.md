# Agent Taxonomy Map — RECONCILED, NOT MERGED

Machine-readable authority: [`agent_taxonomy_map.json`](./agent_taxonomy_map.json)
Enforced by: [`tests/test_agent_taxonomy_map.py`](../../tests/test_agent_taxonomy_map.py)

Status: `RECONCILED_NOT_MERGED`

AHOS carries **four independent agent taxonomies** plus the A–H evaluation roles from the
M0 reality audit. They overlap heavily and disagree on what "agent 01" means. This artifact
maps them explicitly, records provenance on every relation, and refuses to collapse anything.

Per the master directive (§12): preserve both taxonomies, register provenance, build an
explicit mapping. **Silent merge is forbidden.**

## The four taxonomies

| Namespace | Source | Count | Honest class |
|---|---|---|---|
| `agent.*` | `ahos_org/registry.py` (`CANONICAL_AGENT_IDS`) | 19 | **[IMPLEMENTED]** policy model — no runtime, no external I/O |
| `AG-*` | `config/agent_registry.yaml` | 25 | machine-readable ops registry; `orchestrated: 0` for every agent |
| `AGENT-*` | `docs/AGENT_MAPPING.md` (Phase-1 frozen lock) | 10 (+15 expert roles) | frozen two-layer map; documentary |
| `agent.org.*` | `docs/agents/PLANNED_19_AGENT_MAP.md` | 19 | **[PLANNED]** documentary blueprint; not seeded in code |
| `A`–`H` | M0 reality matrix | 8 | evaluation roles, not repository ids |

These are **not** layers of one system. They are four separate attempts to name the same
organization, written at different times, none of which supersedes the others.

## The "agent 01" collision

This is the single most dangerous ambiguity in the repository. The same short id means four
unrelated things:

| Taxonomy | Id | Meaning |
|---|---|---|
| `agent.*` | `agent.chief-orchestrator` | Chief Orchestrator — logical coordinator, no unrestricted authority |
| `AG-*` | `AG-01` | Master Orchestrator — status **MISSING**, ABSENT BY DESIGN, form `n8n_workflow` |
| `AGENT-*` | `AGENT-01` | **DataFetch** — DATA group, CCXT/LBank ingest; **not an orchestrator** |
| `agent.org.*` | `agent.org.01-chief-architect` | Chief Architect — documentary organizational architecture leadership |

Anyone reading "agent 01" without the namespace prefix will reach the wrong conclusion. The
map records this as a **collision, not an alias**; the test refuses to let two members of a
collision come from one taxonomy (which would be a merge).

## The blocking finding

> All 19 Slice-1 canonical agents are seeded at `MaturityLevel.REGISTERED` (0).
> `MINIMUM_MATURITY_FOR_ALLOW = 2` (`IMPLEMENTED`).
> **Therefore no Slice-1 agent can currently be granted execution authority.**

This is the precise mechanical reason no control-plane orchestration exists. It is not a
documentation gap or a missing wiring task — the maturity floor is a deliberate gate, and
every canonical agent sits below it. Any real control-plane boot must raise documented
maturity **with evidence**, not edit the floor.

As of 2026-09-27 that ramp exists: `AgentRegistry.advance_maturity` is the only legal path
from `REGISTERED` to `IMPLEMENTED`. It is fail-closed and audit-logged, and nothing calls it
automatically — the decision to advance a specific anchor stays with human governance. This
removes the missing-mechanism half of the blocker; the missing-evidence half remains.

The ops matrix says the same thing differently: `operability_totals: orchestrated: 0`, and
`AGENTS.md` confirms Agent One "not implemented".

## Authority invariants (all verified against live code)

| Invariant | Claim |
|---|---|
| `INV-DECIDE-HOLDERS` | Only **AG-15** Decision Engine and **AG-16** Paper-Trading hold `allowed_authority: [DECIDE]`. No Slice-1 anchor holds DECIDE. |
| `INV-VETO-DETERMINISTIC` | AG-09 holds VETO as a **deterministic** safety veto — never an AI veto. |
| `INV-PROMOTE-HUMAN-ONLY` | AG-23 holds PROMOTE+VETO but **only as a documented human gateway** — never implementable as software. |
| `INV-NO-SLICE1-EXECUTION` | Maturity 0 < floor 2 ⇒ no Slice-1 execution. |
| `INV-MATURITY-ADVANCE-GOVERNED` | The only path from REGISTERED to IMPLEMENTED is `AgentRegistry.advance_maturity` — fail-closed, evidence-mandatory, audit-logged, and never called by any seed or production path. Levels above IMPLEMENTED are not reachable through it. |
| `INV-GLOBAL-DENY` | `GLOBAL_DENY_CAPABILITIES` (`trading.live`, `production.operate`, `credentials.access`, `ahos.lane_a`, `telegram.access`, `n8n.access`, …) are never ALLOW. |
| `INV-RESEARCH-FORBIDDEN` | A research context cannot receive `IDENTITY_MANAGE`, `APPROVAL_ISSUE`, `KNOWLEDGE_PROMOTE`, `AUTHORITY_DELEGATE`, `EXECUTION`, `POLICY_MODIFY`, `VERIFICATION_RECORD`, `TASK_MANAGE`. |
| `INV-AI-NO-UPGRADE` | An AI council challenge can only **downgrade** or abstain; `upgrade_blocked` is set for council ENTER when gates are closed. |
| `INV-PAPER-ONLY` | Real trading disabled: `hygiene.py` vetoes `AHOS_ALLOW_REAL_FUNDS`/`AHOS_EXECUTE_LIVE_TRADES`; `Resource.AHOS_LIVE_TRADING` protected; `Operation.EXECUTE` and `Capability.EXECUTION` are global denies. |

## M0 evaluation roles with no Slice-1 anchor

Three of the eight A–H roles have **no** Slice-1 logical anchor at all. These are the real
gaps; they are recorded, not smoothed over:

| Role | Finding |
|---|---|
| **C — Builder** | No Slice-1 anchor. Closest implemented substance is `research_worker/analyst.py` (Class A research analyst) and the `agent_org` research-host facade — neither is a builder agent. A builder would need capability grants inside the TCB. **Prerequisite: control-plane boot of at least one agent.** |
| **F — Research Intelligence** | Implemented as a research **worker + host**, not as a Slice-1 logical agent. Real code, real tests — but `PROCESS_ISOLATION_PROVIDED = false` and `SAME_PROCESS_RESIDUAL = true`, so isolation is claimed and not provided. |
| **H — GitHub / Open-Source Intelligence** | No Slice-1 anchor. `AG-25` is PLANNED and `engine/oss_audit` is an **orphaned dead module** (never imported). The entire Agent-H substrate is dead code behind one manual audit report. |

## What this map is not

- It does not create, promote, or activate any agent.
- It does not merge any taxonomy or role.
- It does not grant, imply, or escalate any capability or authority.
- Mapping a role is **not** evidence that the role is implemented, tested, or operational.
- All 19 Slice-1 anchors remain at maturity `REGISTERED` (0); none can execute.

## Maintenance

The map is pinned to live code by `tests/test_agent_taxonomy_map.py`. The test fails if:

- an anchor is added or removed relative to `CANONICAL_AGENT_IDS`;
- a relation loses its provenance;
- one of the four taxonomy sources stops being cited (a silent merge);
- any mapping gains `decision_authority` or cites a globally-denied capability;
- any capability token outside `INTERNAL_CAPABILITIES` is cited (it would be un-enforceable);
- the `REGISTERED` maturity or the paper-only protections are dropped;
- a positive readiness label appears in a claim-bearing field, or the disclaimer is deleted.

Edit `agent_taxonomy_map.json` and the test together. A change to the set of anchors is a
governance change and requires independent review.

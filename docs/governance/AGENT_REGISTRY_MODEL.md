# Agent Registry Model

```text
DOCUMENT_ID      = AGENT_REGISTRY_MODEL
VERSION          = 0.1.0
STATUS           = DESIGN_ONLY (this file) + IMPLEMENTED (Slice 1 AgentRegistry)
ENFORCEMENT      = Slice 1 registry code only
RUNTIME_VERIFIED = NO
```

## Do not rebuild the registry

`ahos_org/registry.py` already implements a canonical **19-role logical registry**.

This document describes **compatibility**. It does not replace `AgentRegistry`.

---

## Plane A — Slice 1 canonical registry `[IMPLEMENTED]` `[TESTED]`

Source: `ahos_org/registry.py` `CANONICAL_AGENT_IDS` (exactly 19).

Tests: `tests/test_registry.py` `test_all_19_roles_registered`.

Initial maturity: `MaturityLevel.REGISTERED` (0) — **below** `MINIMUM_MATURITY_FOR_ALLOW` (IMPLEMENTED=2), so canonical agents **cannot** receive `ALLOW` for execution-class actions without a later maturity change (`ahos_org/policy.py`).

Identity fields on `AgentRecord`: see Constitution §7. Missing charter fields are **not** in the dataclass.

`enabled=True` on seed does **not** mean operational specialists exist. It means the logical row is present.

---

## Plane B — Slice 2B identity store `[IMPLEMENTED]` `[TESTED]`

`agent_org` can `REGISTER_AGENT` via TCB with `AgentIdentity` (`principal.` ids, `IdentityType.AGENT`).

This is **not** the same table as Slice 1 `agent.*` ids.

`DEFERRED_IMPLEMENTATION`: identity federation between `ahos_org` and `agent_org`.

---

## Plane C — Research analyst `[IMPLEMENTED]` `[TESTED]` (bounded)

```text
AGENT_ID = RESEARCH_ANALYST_AGENT
```

Not in `CANONICAL_AGENT_IDS`. Not in the planned 01–19 map. Class A deterministic worker. No LLM. No Agent One.

---

## Plane D — Planned specialist blueprint `[PLANNED]` `[DESIGN_ONLY]`

Source: [PLANNED_19_AGENT_MAP.md](../agents/PLANNED_19_AGENT_MAP.md).

IDs: `agent.org.NN-<slug>`.

**Not seeded.** **Not immutable.** Human approval required to merge, split, or replace Plane A.

---

## Compatibility rules

1. Never copy Plane D into `CANONICAL_AGENT_IDS` in this documentation mission.
2. Never rename Plane A roles to match the blueprint without L2.
3. Reports must say which plane an `AGENT_ID` belongs to.
4. Communication envelope recipients in Plane D are documentary until registered in a runtime plane.
5. `orchestrate.plan` on `agent.chief-orchestrator` ≠ Agent One.

---

## ROLE_OVERLAP / ROLE_GAP (visible, not resolved)

See planned map. Summary:

| Blueprint (D) | Possible Slice 1 overlap (A) | Action taken |
| --- | --- | --- |
| 01 Chief Architect / 02 Systems Architect / 14 Runtime / 04 Governance | change-architect, chief-orchestrator, windows-runtime, release-governance-reviewer | `POSSIBLE_MERGE` recorded only |
| 03 Security Architect / 10 Token Security | agent.security | overlap of “security” word; domains differ |
| 16 QA / 19 Red Team | independent-verification, red-team | overlap |
| 17 Product UX / 18 Frontend | frontend-ux | overlap |
| 08–12 market/on-chain/quant | scoring-science, paper-trading, provider-data | partial thematic overlap |
| 05 Epistemic / 06 Research methodology | (weak) reality-forensics, evidence-transport, cognitive-agi-aci | `ROLE_GAP` if D is adopted without A mapping |
| RESEARCH_ANALYST_AGENT | none | extra agent outside both 19-lists |

`POSSIBLE_SPLIT` / `POSSIBLE_MERGE`: **not executed**.

---

## DEFERRED_IMPLEMENTATION

```text
- Single unified registry across Slice 1, Slice 2B, research host, and 01–19 charters
- Charter fields on AgentRecord
- Message bus bound to registry ids
- Supervisor service
- Mapping table approved by humans (A ↔ D)
- Agent One orchestrator using registry
- Enforcement of Constitution status taxonomy in code
- Intersect Slice 1 INTERNAL_CAPABILITIES with Constitution authority classes
```

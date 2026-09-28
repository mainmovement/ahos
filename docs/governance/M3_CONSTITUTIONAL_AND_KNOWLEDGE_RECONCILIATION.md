# AHOS — M3 PROJECT CONSTITUTIONAL AND KNOWLEDGE RECONCILIATION

```text
DOCUMENT_ID      = M3_CONSTITUTIONAL_AND_KNOWLEDGE_RECONCILIATION
MISSION          = M3 (PROJECT CONSTITUTIONAL AND KNOWLEDGE RECONCILIATION)
CREATED_UTC      = 2026-09-28
STATUS           = READ-ONLY RECONCILIATION — no code, no migration, no merge, no deletion
AUTHORITY        = NONE CREATED. This document classifies authority; it does not grant any.
RUNTIME_EFFECT   = NONE
LANE_A_EFFECT    = NONE
SUPERSEDES       = NOTHING. It amends M-GAP-035's framing with evidence (see Part C).
```

**Purpose.** Establish a durable, evidence-backed project memory and decision-precedence
structure so future sessions, agents, and context compactions can distinguish current
constitutional directives, active governance, active architecture, implementation reality,
verified runtime evidence, proposals, experiments, historical decisions, superseded decisions,
and deprecated decisions — without a human restating project history.

**Method.** Read-only. Repository evidence first, per the evidence doctrine in
`docs/architecture/AGENT_14_RUNTIME_FOUNDATION_RECONCILIATION_AND_MVOR_ARCHITECTURE.md` §3:

```text
L0 repository source > L1 executed tests > L2 adopted governance > L3 architecture docs > L5 chat
REALITY > DOCUMENTATION · TEST PASS ≠ OPERATIONAL · DOCUMENTED ≠ ENFORCED
```

**Non-goals (binding).** No historical document is erased. No conflicting taxonomy is silently
merged. No control-plane component is renamed, deleted, merged, or migrated. No maturity level
changes. No Lane-A change. No live trading. No self-evolution or self-promotion activation.
Provenance and supersession are preferred over deletion.

---

## PART A — Source inventory and classification

Classification vocabulary (this document): **CONSTITUTIONAL** (immutable doctrine) ·
**GOVERNANCE** (binding rules + enforcement) · **ARCHITECTURE** (design/decision record) ·
**IMPLEMENTATION** (code reality) · **EVIDENCE** (generated receipts) · **PROPOSAL** (not adopted) ·
**EXPERIMENT** (time-boxed study) · **HISTORICAL** (superseded, retained) ·
**DEPRECATED** (superseded + must not be cited).

### A.1 Constitutional and governance

| Source | Date | Class | Authority | Status | Enforcement |
|---|---|---|---|---|---|
| `docs/canonical/MASTER_DIRECTIVE_v1.md` | 2026-08-13 | **CONSTITUTIONAL** | OWNER-ratified, verbatim | **ACTIVE** — the only registry-ACTIVE doctrine | registry + `tests/test_master_directive.py` (5 tests) |
| `docs/canonical/master_directive_registry.json` | — | GOVERNANCE | mechanical authority pointer | ACTIVE, lists v1 only | CI: exactly one ACTIVE, no orphans, sha match, issue-register presence |
| `docs/canonical/MASTER_DIRECTIVE_W43.md` | W43 | **AMBIGUOUS — see C.1** | self-described directive, Persian | "living, not registry ACTIVE" per `DOC_TRUTH_MAP.md:11` | **NOT covered by the registry glob** (Part C.1) |
| `docs/canonical/GOVERNANCE.md` | — | GOVERNANCE | canonical | ACTIVE | tied to named enforcement |
| `docs/canonical/MISSION.md` | — | GOVERNANCE | canonical | ACTIVE | 7 absolute laws |
| `docs/canonical/PROJECT_STATE.md` | 2026-08-11 (Wave-7) | GOVERNANCE pointer | claims "always-current" | **STALE** — see C.2 | none (it is a pointer) |
| `AGENTS.md` | current | GOVERNANCE | Cursor engineering contract | ACTIVE | `.cursor` + human review; self-declared "does not replace MASTER_DIRECTIVE_v1" |
| `docs/governance/AGENT_ORGANIZATION_CONSTITUTION.md` | — | CONSTITUTIONAL (org layer) | Agent Organization, not AHOS | ACTIVE **for the org layer only** | see Part C.3 |
| `docs/architecture/SELF_EVOLUTION_LOOP.md` | W12 PART K | GOVERNANCE | contract law | ACTIVE | `contracts/improvement_proposal_v1.json` + CI lints |
| `docs/architecture/ADR_ACI_001_CHARTER_VS_DEFERRED_EVOLUTION.md` | 2026-09-09 | ARCHITECTURE decision | **ACCEPTED** | ACTIVE — dual-authority precedent | none mechanical |

### A.2 Architecture and reality

| Source | Date | Class | Status |
|---|---|---|---|
| `docs/DOC_TRUTH_MAP.md` | current | GOVERNANCE index | ACTIVE — the declared entry point |
| `docs/architecture/AHOS_RUNTIME_ARCHITECTURE_v1.md` | 2026-08-13 (W12) | ARCHITECTURE | ACTIVE; §1 names `control_plane.py` as MASTER RUNTIME CONTROLLER |
| `docs/architecture/unified_control_plane.md` | W10/W11 | ARCHITECTURE spec | ACTIVE; §9 honest SAFE_HALT admission |
| `docs/architecture/orchestration_comparison.md` | 2026-08-13 | ARCHITECTURE decision | ACTIVE verdict: Python-native ADOPT-NOW, Temporal DEFER-INSTALL, n8n edge-only |
| `docs/architecture/single_start_runtime.md` | W11 | ARCHITECTURE spec | ACTIVE; §5 `orchestrated=0 by design this wave` |
| `docs/architecture/AGENT_14_RUNTIME_FOUNDATION_RECONCILIATION_AND_MVOR_ARCHITECTURE.md` | 2026-09-14 | ARCHITECTURE reconciliation | ACTIVE — prior reconciliation; **the methodological precedent for this document** |
| `docs/architecture/SLICE_2A_EPISTEMIC_CORE_AND_TCB_SPEC.md` | 2A-RESTORED-2 | ARCHITECTURE contract | ACTIVE **for the org layer**; §0 explicitly "not an AHOS implementation or integration" |
| `docs/governance/AGENT_TAXONOMY_MAP.md` + `.json` | 2026-09-27 (M2) | GOVERNANCE record | ACTIVE, RECONCILED_NOT_MERGED; `tests/test_agent_taxonomy_map.py` (19) |
| `AHOS_GAP_REGISTER.md` | living | EVIDENCE/gap register | ACTIVE — M-GAP-001…037 |
| `AHOS_ISSUE_REGISTER.md` | living | EVIDENCE | ACTIVE — R-series append-only provenance |
| `architecture/runtime/`, `architecture/control_plane.py`, `ahos_org/`, `agent_org/` | — | **IMPLEMENTATION** | traced in Part C |

### A.3 Superseded / deprecated — must not be cited as current

| Source | Class | Note |
|---|---|---|
| `AHOS_FINAL_STATUS.md` | **DEPRECATED** | banned `READY_FOR_DEPLOYMENT` claim |
| `AHOS_PRODUCTION_READINESS_REPORT.md` | **DEPRECATED** | score/READY overclaim |
| `docs/SECURITY_CHECKLIST.md`, `docs/MISSING_COMPONENT_REGISTER.md`, `docs/STRATEGIC_GAP_ANALYSIS.md` | HISTORICAL | bannered stale design snapshots |
| `docs/archive/consolidation_2026-09-26/` | HISTORICAL | pre-canonical external copies; evidence only, not authority |
| Agent-14 v1 runtime architecture | HISTORICAL | superseded for organizational intent by the MVOR reconciliation; retained for substrate analysis |

---

## PART B — Decision provenance and supersession table

Each row: one decision or rule, with authority, supersession in both directions, and current
implementation state. **No row is silently merged with a conflicting row.**

| # | Decision | Source (date) | Authority | Supersedes | Superseded by | Implementation state |
|---|---|---|---|---|---|---|
| D1 | Permanent operating doctrine; 12-step wave protocol; immutability per version | `MASTER_DIRECTIVE_v1.md` (2026-08-13) | OWNER, verbatim | reinforces pre-existing Master Operating Contract (weakens nothing) | nothing (v2 does not exist) | Enforced: registry + 5 CI tests |
| D2 | Only ONE ACTIVE doctrine; ACTIVE = highest version; every version file listed + sha-registered | registry law | mechanical | — | — | **Holds for `v*` files only — see C.1** |
| D3 | UNKNOWN > fabricated; honest-token vocabulary | `MISSION.md` laws 1,7; W43 §اصل بنیادین | OWNER | — | — | Enforced in code (fail-closed gates) |
| D4 | PAPER_ONLY; live trading forbidden without separately-documented gates | `MISSION.md` law 5; W43 §معامله; `AGENTS.md` | OWNER | — | — | LIVE_TRADING_AUTHORIZED = NO (pinned) |
| D5 | Lane-A freeze; 36 sha-pinned files | `config/lane_a_freeze.sha256` | GOVERNANCE | — | — | OK, verified this session |
| D6 | Two-lane law: Lane A never stops for Lane-B architecture | W12-added law, `AHOS_RUNTIME_ARCHITECTURE_v1.md` | ARCHITECTURE | — | — | CI-pinned (`test_architecture_p1.py`) |
| D7 | Python-native control plane = ADOPT-NOW interim; Temporal = target, DEFER-INSTALL; n8n = edge only | `orchestration_comparison.md` (2026-08-13) | ARCHITECTURE verdict | resolves W10 tension | nothing (host-gated adoption later) | Engine implemented+tested; **not wired to daemon — Part C.4** |
| D8 | Agent startup gated on `orchestrated==true`; orchestrated=0 today is **by design** | `unified_control_plane.md` §2; `single_start_runtime.md` §5 | ARCHITECTURE | — | — | Pinned by totals test |
| D9 | AGI/ACI charter = strategic research only; autonomous evolution stays deferred | `ADR_ACI_001` (2026-09-09) | ARCHITECTURE (ACCEPTED) | would-have-superseded backlog — explicitly refused | nothing | Dual authority recorded; `evolution_gate.py` refuses non-B_ONLY |
| D10 | AI may never self-approve, never touch Lane A, never promote itself | `SELF_EVOLUTION_LOOP.md`; `improvement_proposal_v1.json` | CONTRACT LAW | — | — | CI lints + human gate (never software) |
| D11 | Four agent taxonomies mapped, collision recorded, **not merged** | `AGENT_TAXONOMY_MAP.md` (2026-09-27) | GOVERNANCE record | — | — | 19 tests; mapping ≠ capability grant |
| D12 | Maturity floor MINIMUM_MATURITY_FOR_ALLOW=2; all 19 anchors at REGISTERED(0) | `ahos_org/policy.py`, `registry.py` | GOVERNANCE | — | — | Pinned; legal ramp = `advance_maturity` |
| D13 | Deletion needs council sign-off; autonomous deletion prohibited — archive only | `GOVERNANCE.md` | GOVERNANCE | — | — | Honored this session (stray dirs flagged, not deleted) |
| D14 | Agent One is intended root but `FUTURE_NON_AUTHORITY_ROOT`; four statements stay simultaneously true | MVOR reconciliation §3 (2026-09-14) | ARCHITECTURE | Agent-14 v1 Phase-7 listing | — | Code marker unchanged |

---

## PART C — M-GAP-035 findings: reclassification with evidence

M-GAP-035 (recorded 2026-09-28) asserted **three control-plane surfaces, two test-only, and the
daemon consults none**. That framing is **directionally correct but materially imprecise**. The
read-only M3 trace reclassifies it. This is a correction to my own earlier finding, not a
confirmation.

### C.1 The three surfaces are not three competing planes for one system

| Surface | Non-test importers | Self-declared identity (verbatim) | Correct class |
|---|---|---|---|
| `architecture/runtime/` | LIVE: `deployment/healthcheck.py`, `scripts/init_databases.py`, `scripts/local_activation_report.py`, `scripts/month1_failure_matrix.py` | the AHOS observation daemon | **AHOS production daemon** |
| `architecture/control_plane.py` | none (tests only) | "AHOS W11 Lane-B — Control Plane engine"; named MASTER RUNTIME CONTROLLER by `AHOS_RUNTIME_ARCHITECTURE_v1.md:47` | **AHOS operator surface** — one system, deliberately not yet wired |
| `ahos_org/` | none outside itself | *"an independent organizational control plane. It is not an AHOS runtime, not a trading system, and not an AGI."* — `ahos_org/__init__.py` | **separate system: the Agent Organization (Slice 1)** |
| `agent_org/` | none outside itself | *"not an AHOS implementation or integration; not an agent runtime, Agent One, or a 19-agent council"* — Slice 2A §0 | **separate system: the epistemic core / TCB (Slice 2B)** |

So there is **one** AHOS control plane (`control_plane.py`), and `ahos_org`/`agent_org` are not
candidate planes for AHOS at all. M-GAP-035's phrase "the choice of which plane is canonical" was
based on a category error: the org layer and the AHOS opportunity-intelligence runtime are
different systems that coexist in one repository. The M2 taxonomy map already recorded the
namespace collision (`agent.*` / `AG-*` / `AGENT-*` / `agent.org.*`) without merging — this is the
same separation.

### C.2 The genuine AHOS gap is narrower and less severe than M-GAP-035 claimed

The daemon does not import `control_plane.py` — **but that is substantially by design, not
oversight**:

- `single_start_runtime.md` §5: "Start real agent services | **NO — orchestrated=0 by design this
  wave** | totals test pins orchestrated=0"
- `AHOS_RUNTIME_ARCHITECTURE_v1.md` §2 row 3: "orchestrated=0 ⇒ rollback = **do nothing**; surface
  only **REPORTS** standing Lane-A liveness"
- `unified_control_plane.md` §9: with real configs the engine returns SAFE_HALT and "the
  deterministic Lane-A core continues via its standing schedule — safe BY DESIGN"

**Verified live this session:** `ControlPlane().start()` boots honestly to `SAFE_HALT`
(`run-c4ccb36c02e23b0a`) over 8 components (postgresql, temporal, redis, event_bus, n8n,
observability, ahos_engine, evidence_stores) and reads agents in the **AG-\*** namespace. It
fabricates nothing. The surface works exactly as documented.

The real, narrower finding is a **composition-root ambiguity** (DECISION REQUIRED, not a defect):
there are two documented ways to "run AHOS" — `python -m architecture.runtime --daemon …` and
`ControlPlane().start()` — with no integration and no recorded precedence between them. Neither
document says which is the entrypoint when both exist.

### C.3 Contradictions detected (unresolved — recorded, not merged)

- **C.3.1 The doctrine registry glob does not cover `MASTER_DIRECTIVE_W43.md`.**
  `tests/test_master_directive.py:89` globs `MASTER_DIRECTIVE_v*.md`. W43 does not match `v*`, so
  the "no orphan doctrine files" and sha-registration laws never apply to it — despite it being
  named `MASTER_DIRECTIVE_*` and containing "فرمان اصلی" (main command) with operational doctrine
  ("do not ask the user for ordinary engineering changes; but do not break Governance and Safety").
  DOC_TRUTH_MAP:11 treats it as a wave directive ("living, not registry ACTIVE"). **Either the
  enforcement glob should match every `MASTER_DIRECTIVE_*.md`, or W43 should be renamed so it
  cannot be mistaken for unregistered doctrine.** This is a genuine loophole in a CI-enforced
  constitutional law and needs a human decision (Part F, item 7).
- **C.3.2 `docs/canonical/PROJECT_STATE.md` is stale despite claiming to be always-current.** It
  is pinned to "Wave-7 · 2026-08-11" while the register tracks 2026-09-28 and DOC_TRUTH_MAP
  references W43/W44. Its own header says "always-current pointer". The pointer is correct
  (→ `reports/PHASE_STATE.md`); the content is not.
- **C.3.3 Two "agent" namespaces remain live and unmapped at the runtime seam.** `control_plane.py`
  reads `config/agent_registry.yaml` (AG-01…AG-25); `ahos_org` defines 19 `CANONICAL_AGENT_IDS`.
  M2 mapped the taxonomies as a policy record, which does not connect them at the code seam.
- **C.3.4 (from M-GAP-037, carried)** `validate_imports.py` exits 1 on any warm host because its
  44 FAIL lines are gitignored `__pycache__`, making the soak pre-registration gate unpassable in
  the only context it exists for. Enforcing control; policy decision.

### C.4 Minimum composition-root path (AHOS system, not the org layer)

For the AHOS opportunity-intelligence runtime — the only system with a live daemon. Each step is
classified: **R** REALITY (exists and runs) · **E** EVIDENCE (receipt exists) · **D** DOCUMENTATION
(documented only) · **P** PROPOSAL · **?** DECISION REQUIRED.

```text
runtime command        R   `python -m architecture.runtime --daemon --observation-cycle`
                      (AHOS_LOCAL_SOAK_PROTOCOL.md §4; SIGINT/SIGTERM graceful stop)
   │
   ▼
operator surface       ?   architecture/control_plane.py  ← DECISION REQUIRED: integrate, or
                          keep as the parallel honest-reporting surface (C.2)
   │
   ▼
agent organization     D   config/agent_registry.yaml (AG-01..AG-25); orchestrated=0 by design
   │
   ▼
capability/policy      R   registry validation + dependency graph (cycle ⇒ SAFE_HALT) —
   validation              implemented+tested inside control_plane.py boot phases 11-12
   │
   ▼
governance/authority   R   policy floor MINIMUM_MATURITY_FOR_ALLOW=2 (ahos_org/policy.py is
                          the org layer; AHOS uses its own registry gating, D8)
   │
   ▼
agent execution        D   phase 14 starts only implemented && orchestrated agents; today 0
   │
   ▼
evidence/audit         R   append-only run ledger (tamper test-pinned) + reports/ receipts
   │
   ▼
independent            R   16 phase tests; 8-test single-fault soak battery; 64-combination
verification               fuzz; real-config boot never fabricates ONLINE
```

For the **Agent Organization layer** (a separate system), the corresponding minimum path is the
MVOR seven primitives in `AGENT_14_RUNTIME_FOUNDATION_RECONCILIATION_AND_MVOR_ARCHITECTURE.md`
§1.1, all still DESIGNED — none of the 8 launch blockers has closed. That path is out of scope for
AHOS composition and remains human-gated.

**The one sentence that matters:** the AHOS composition root already exists and is verified; the
open question is only whether the daemon and the control-plane surface become one entrypoint or
stay two deliberately-separated ones. That is a decision, not an implementation gap.

---

## PART D — Organizational memory model

This reconciliation establishes the following model for future compactions. It is a **model**;
writing it into mechanically-enforced artifacts is item 8 below.

```text
AUTHORITY          WHO said it, in what capacity. OWNER > CONTRACT LAW > GOVERNANCE >
                   ARCHITECTURE(ADR) > IMPLEMENTATION > DOCUMENTATION > CHAT.
                   "It is in a doc" is not authority; the doc's authority class is.
PROVENANCE         Source path + date + sha256 where the law requires it (registry, R-series).
TEMPORAL VERSIONING Every rule carries a date; newer is NOT more authoritative — authority class
                   decides, then date. ADR_ACI_001 is newer than the backlog and deliberately
                   does NOT supersede it.
SUPERSESSION       Explicit and bidirectional: what a rule supersedes, and what supersedes it.
                   Absent both = live. Silent change = governance violation (D1).
REALITY VERIFICATION  DOCUMENTED ≠ ENFORCED ≠ RUNNING. Each claim needs its evidence class:
                   L0 source > L1 tests > L2 adopted governance > L3 docs > L5 chat.
CONTRADICTION       Two true statements may coexist (D14: four Agent-One statements at once).
DETECTION          Contradictions are RECORDED, never collapsed. Resolution is a human decision.
DECISION HISTORY    Every decision in PART B carries authority + supersession + state, so a
                   future session can answer "is this still in force?" without asking a human.
```

---

## PART E — The nine required M3 report items

**1. Authoritative current rules.** `MASTER_DIRECTIVE_v1.md` (only registry-ACTIVE doctrine,
OWNER-ratified 2026-08-13, immutable per version) · `MISSION.md` 7 absolute laws · `GOVERNANCE.md`
hard rules · `AGENTS.md` engineering contract · the contract law in
`SELF_EVOLUTION_LOOP.md`/`improvement_proposal_v1.json` · the ADOPT-NOW verdict in
`orchestration_comparison.md` · `ADR_ACI_001` (charter = research, evolution = deferred).

**2. Superseded rules.** `AHOS_FINAL_STATUS.md` and `AHOS_PRODUCTION_READINESS_REPORT.md`
(DEPRECATED, banned readiness claims) · Agent-14 v1's Phase-7 Agent-One listing (superseded by the
MVOR reconciliation for organizational intent; retained for substrate analysis) · the stale design
snapshots bannered in DOC_TRUTH_MAP §E.

**3. Unresolved contradictions.** The four in C.3: the registry glob loophole over W43 (C.3.1);
`PROJECT_STATE.md` staleness vs its always-current claim (C.3.2); the live unmapped AG-\* /
`CANONICAL_AGENT_IDS` seam (C.3.3); and the warm-host validator gate (C.3.4, M-GAP-037). None is
merged or resolved here.

**4. Current architectural reality.** One live AHOS daemon (`architecture/runtime/`) running the
deterministic Lane-A floor by standing schedule. One implemented-and-tested operator surface
(`architecture/control_plane.py`) that boots honestly to SAFE_HALT and, by documented design at
orchestrated=0, starts no agents and only reports Lane-A liveness. A separate, explicitly
not-AHOS organizational layer (`ahos_org/` Slice 1, `agent_org/` Slice 2B) whose 8 MVOR launch
blockers are all still open. Evidence pipeline repaired this session (M-GAP-033/034/036) with
M-GAP-037 open. Lane A intact (36 files).

**5. M-GAP-035 findings.** Reclassified in Part C: not three competing planes, but one AHOS plane
plus a separate org layer, with a composition-root ambiguity between the daemon and the surface
that is a DECISION REQUIRED rather than a wiring defect. M-GAP-035 should be amended, not closed.

**6. Canonical-plane options.** (a) **Integrate** — the daemon's `--daemon` path calls
`ControlPlane().start()` as its boot prologue so there is one entrypoint and the honest SAFE_HALT
verdict becomes the daemon's startup gate. (b) **Keep separated** — record explicitly in
DOC_TRUTH_MAP and `single_start_runtime.md` that the daemon is the Lane-A evidence producer and
the control plane is the operator/reporting surface, with precedence stated. (c) **Defer** — leave
as-is and treat it as a host-era concern. Recommendation: **(b) now, (a) when orchestrated > 0** —
(b) costs a doc edit and removes the ambiguity; (a) is premature while agent startup is by-design
zero and would couple the daemon to a SAFE_HALT verdict it cannot yet act on.

**7. Decisions that genuinely require human authority.**
- Whether W43 is unregistered doctrine or a wave directive — and whether to close the registry-glob
  loophole or rename W43 (C.3.1). This touches a CI-enforced constitutional law; it is not mine.
- The canonical-plane option above (6).
- M-GAP-037's validator artifact-check semantics (enforcing control).
- Any maturity advance via `advance_maturity` — evidence-mandatory, human-governance by construction.
- Disposition of the 137 tracked files in four root directories unrelated to AHOS (flagged
  2026-09-28; deletion prohibited without council sign-off, D13).

**8. Changes autonomously implementable afterward.** All are documentation/annotation, none
changes runtime, governance, maturity, or Lane A: amend M-GAP-035's framing per Part C; record the
composition-root precedence if option (b) is chosen; refresh `PROJECT_STATE.md`'s stale Wave-7
content to a honest pointer-only state; add the contradiction rows to `AHOS_GAP_REGISTER.md`;
write this model into `DOC_TRUTH_MAP.md` as a section. Code changes (options 6a, C.3.1's glob)
require the human decisions above and must not precede them.

**9. Next highest-value mission-relevant gap.** M-GAP-037: the soak pre-registration gate is
unpassable on a warm host. It is the single remaining blocker in the local-evidence pipeline that
M-GAP-033/034/036 repaired, it gates every maturity-evidence claim the org layer would need, and
its fix is small and well-scoped once the artifact-check semantics are decided. Second: the
composition-root precedence (6b), which is a doc edit.

---

## PART F — Standing rules for any session using this document

1. Do not cite anything in A.3 as current readiness.
2. Do not treat W43 as registered doctrine, and do not treat its absence from the registry as
   permission either — C.3.1 is unresolved.
3. Do not merge the AG-\* and `CANONICAL_AGENT_IDS` namespaces, and do not treat the M2 map as
   having connected them.
4. Do not promote any maturity, approve any proposal, or enable any self-evolution.
5. When two statements in PART B conflict, record the contradiction; do not resolve it.
6. AGI/ACI is a continuing architectural objective and research requirement, not an achievement.
   Nothing in this document claims otherwise.

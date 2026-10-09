# M12 — Agent organisation: register the 18 owner-approved agents

Queue row (verbatim): *Agent organisation: 37+ agents in `config/agent_registry.yaml`
using the owner charter template, authority NONE by default, no auto-creation.*
Vision authority: `reports/grok/AHOS_AUTONOMOUS_VISION.md` §2.3 (owner approved
2026-10-03 20:43: "منشورهای ۲۰ تا ۳۷ مصوب‌اند. ثبت در رجیستری … در M12 انجام
می‌شود"), §2.3.1 the owner charter template, §2.3.2 the summary table, §2.3.3 the
18 full charters (lines 186–404).

This file holds the four PRE-CODING reviews (mission contract order), then the
three end sign-offs appended after the build.

## Pre-coding review — آرش (Chief Architect)

**Where the 18 go, and where they do not.** The queue row names one file:
`config/agent_registry.yaml`. That file is the declared "source of truth for
Master Orchestration" and already holds AG-01..AG-25. The 18 become
**AG-26..AG-43**, one per vision agent #20..#37, in vision order, so the
mapping is mechanical and auditable. No new module, no second registry file,
no parallel verifier — the two-source rule's "extend the existing path" applied
to organisation, not just markets.

**What is NOT touched:** `ahos_org/registry.py` and the Slice-1
`agent.org.*` store. The charter template forbids seeding it without human
approval, and the queue row says "no auto-creation". Registering 18 rows in the
AG matrix creates zero rows there. A test pins that the Slice-1 anchor count is
unchanged by this mission.

**Status choice: `PLANNED`, not the vision's `REGISTERED`.** The registry's own
status enum (`contracts/agent_contract_v1.json`) has no `REGISTERED` member:
`EXISTS / PARTIAL / PLANNED / MISSING / DUPLICATED / UNKNOWN`. The vision's
`REGISTERED` is the *lifecycle* state (P1§14), a different vocabulary from the
registry's build-status vocabulary. `PLANNED` is the honest member — "spec only;
enters runtime solely through the self-evolution loop" — and it keeps the
EXISTS-evidence lint untouched, because none of the 18 has an executable
artifact. Registering them as anything stronger would be exactly the
"agent exists by declaration alone" law the matrix generator exists to enforce.

**Form: `service`, not `n8n_workflow`.** M10 retired n8n (2026-10-07); every one
of the six shipped cadences now has a recorded Python home. Designing 18 new
agents on a retired runtime would re-introduce the coupling M10 removed.

**Accepted risk, stated:** 6 of the 18 carry `boot_class: CRITICAL` (the CIO,
Treasury, Execution, Compliance, Ledger, Guardian — the charter's own
segregation-of-duties posts). They are `implemented: false`, so no boot claim is
made; the totals block is computed, not asserted, and stays truthful.

## Pre-coding review — domain specialist (org design)

**Reporting lines become `dependencies`, agent ids only.** The registry header
law is explicit ("Dependencies are agent ids only"), so a charter line like
"بهرام reports to کوروش" becomes `dependencies: [AG-26]`. Lines that point at
one of the 19 Slice-1 anchors (رامین, گیتی, فرزانه-as-Dean-report-line, دانا,
کیمیا, سپهر, آرش, عرفان, قاسم, رضا, روشا) are **not** expressed as
`dependencies` — that would be a cross-taxonomy edge, which is the locked
OWN-AV-56 mapping. They are recorded in `ops.notes` as the charter reporting
line, cited, and left unlinked.

**مریم's veto is recorded, not granted.** Vision line 113 and her charter give
her a veto the CIO cannot override. The queue row simultaneously says "authority
NONE by default". Both are true at different layers: the charter describes
*designed* authority; the registry grants *runtime* authority. At registration
she gets `allowed_authority: []` like the other 17, her designed veto is written
in her `ops.notes` as not-yet-granted, and `VETO` is deliberately **not** in her
`forbidden_authority` — forbidding it would deny an owner-approved charter fact.
Granting it is a governance promotion act (PART K / improvement_proposal_v1),
not a registration act. This is the one place the two documents pull in
different directions and the resolution is: record both, decide neither.

**Partial teams are not registered.** §2.7 mandates seats the vision itself
leaves open: a second GitHub seat (`GH-2`), a second Guardian seat, three more
seats on سیاوش's four-person AGI/ACI team, plus the open §2.7 seats. Registering
one member of a mandated team without its seats would present a complete team
that does not exist. Those seats stay unregistered and are listed below as
owner/governance items.

**Non-duplication (§2.5):** the 19 Slice-1 names (§2.2) and the 18 new names
(§2.3) are disjoint — verified against the §2.2 table. The `@gold` profile
variants the vision attaches to several agents ("Gold Macro Agent is a `@gold`
profile of this same agent, not a duplicate agent") are profiles of one agent,
so they generate no extra rows; they are noted on the host agent.

## Pre-coding review — پروانه (Prompt / spec)

**How "authority NONE by default" is expressed so a machine can check it.**
The schema's required-field check rejects an omitted or null
`allowed_authority`; the only honest expression of "no authority granted" that
both validates and is testable is an empty list: `allowed_authority: []`.
`forbidden_authority: [DECIDE, PROMOTE]` on every one of the 18 keeps the
standing owner law (only AG-15/AG-16 DECIDE) machine-enforced for the new rows
too. A test asserts all three: empty allowed, DECIDE absent, PROMOTE absent.

**Evidence pointers must be resolvable, not prose.** Each entry's `evidence`
cites the vision file and the charter heading (e.g.
"`reports/grok/AHOS_AUTONOMOUS_VISION.md` §2.3.3 #20 (کوروش charter, lines
186-198)"). A test extracts the cited file and asserts it exists, so a renamed
or moved vision breaks the test rather than silently orphaning 18 charters.

**No invented probes.** `required_probes` for the 18 names what the charter's
own *Verification Requirements* line names (the human/agent verifier and the
statistical check), as probe tokens in the file's existing vocabulary style.
No probe is claimed to have run; the doc generator prints them as `required:`,
never as results.

**Charter text is cited, not re-authored.** The vision §2.3.3 is the
owner-authored, owner-approved charter text. M12 does not rewrite charters —
that would create a competing authority. The readable index
(`docs/agents/M12_REGISTERED_AGENTS.md`) carries the owner template's ten fields
per agent, condensed in English with the Persian source cited, so the template's
shape is honoured without a second source of truth.

## Pre-coding review — گیتی (Governance)

**The one real conflict, LISTED not decided.** OWN-AV-06 says agents register
via `ahos_org/registry.py`; the charter template (§2.3.1 / P1§14 lineage) says
the org registry is not seeded without human approval, and the queue row points
at `config/agent_registry.yaml`. I register in `config/agent_registry.yaml`
because the queue row names that file explicitly and because it is the declared
source of truth for the AG matrix, and I record the conflict here for the owner.
Resolving it (one registry, or a bridge) is a governance decision about the
composition root, and M34 is the coherence audit that should carry it.

**Locked human-gates this mission does NOT touch:**
- OWN-AV-56 — the two-taxonomy mapping (AG-* ↔ `agent.org.*`). Stays UNRESOLVED.
  No cross-taxonomy edge is created in either direction.
- OWN-AV-62 — ACTIVE requires a university certificate (L0–L4). Nothing in this
  mission activates anything; lifecycle transitions are not performed by a
  registration.
- §2.7 mandatory seats — listed above, left unregistered.
- OWN-AV-04 — the veto matrix is "not encoded". This registration does not
  encode it either; it records designed vetoes as notes. Encoding the matrix is
  a separate governance act.

**No gate is loosened to make a number move.** The count assertions being
changed (25 → 43) exist to pin "the doc matches the registry and the totals are
truthful". Raising them preserves exactly those invariants — the doc is still
byte-identical to a fresh generation, totals are still computed from the rows.
The assertions are not the safety boundary; the invariants they check are, and
those survive unchanged.

**PAPER_ONLY and Lane A:** no new agent touches Lane A. All 18 are `lane: B`.
No execution, order, wallet, or money-path capability is granted — the two
EXECUTION-plane agents (بابک, داریوش) carry `paper-only / testnet` boundaries
from their charters and `allowed_authority: []`.

---

## Build (after the four reviews above)

1. `config/agent_registry.yaml` — 18 entries AG-26..AG-43 inserted before
   `totals:`; `totals` recomputed (agents 25→43, PLANNED 3→21, boot_class
   CRITICAL 10→16 / ADVISORY 6→18; operability unchanged — all 18 false).
2. `docs/architecture/agent_matrix_v2.md` — regenerated with
   `engine/agent_matrix_v2.py` (never hand-edited; freshness pinned by test).
3. `docs/agents/M12_REGISTERED_AGENTS.md` — the charter-template index, new.
4. `tests/test_m12_agent_registration.py` — new, the M12 invariants.
5. `tests/test_agent_matrix_v2.py:37`, `tests/test_architecture_p1.py`
   lines 69/72/73/108/110 — count pins 25 → 43.

## End sign-offs (appended after the build)

### قاسم (QA)
Targeted: `pytest tests/test_m12_agent_registration.py tests/test_agent_matrix_v2.py
tests/test_architecture_p1.py tests/test_agent_taxonomy_map.py tests/test_runtime_w11.py`
→ **100 passed**. New file alone: `tests/test_m12_agent_registration.py` → 18 passed.
Full suite (2026-10-09, started 10:41 UTC, 57:22): **2971 passed, 4 skipped,
0 failed**, run with `tests/test_execution_state.py` excluded. That file's single
failure `test_missing_store_reads_no_data_never_ok` is the pre-existing
test-isolation defect already proven on a pristine checkout and left for the
owner; re-run in isolation this session it still fails identically (1 failed,
8 passed) and no new failure appeared there. Nothing was weakened to make a
number move: the count pins raised 25→43 preserve the doc-freshness, no-duplicate
and totals-truthfulness invariants, and the pre-existing failure is reported,
not hidden.

### رضا (Red team)
Attacks tried against my own diff:
1. **Empty authority read as unrestricted.** Searched every consumer of
   `allowed_authority` (`architecture/contracts.py:34,38,43`,
   `engine/agent_matrix_v2.py:78`) — all three use set algebra or `or []`, so an
   empty list evaluates to "no authority", never "any authority". No runtime
   path grants from this field at all. Negative result, reported as such.
2. **Registration as a readiness claim.** Tried to read
   `docs/architecture/agent_matrix_v2.md` as evidence the org exists: the
   generator's own header and the `evidence_requirements` line for every PLANNED
   row say "spec only; enters runtime solely through the self-evolution loop",
   and the census line prints PLANNED 21. The claim is not inflatable from the
   artifact.
3. **Stale supervision.** Found real drift the suite does not catch:
   `docs/governance/agent_taxonomy_map.json` still reported `count: 25` /
   PLANNED 3, and five docs stated the 25-agent census as present fact —
   `docs/supervision/AHOS_REALITY_MAP_v1.md` worst of all, since its job is to
   prevent census overclaims. All corrected to 43 / 21; the map bumped to 0.1.1
   with a dated delta note. Lesson: a registration changes every census quote,
   and the suite does not notice — grep is the only check.
4. **Charter traceability forgery.** Tried to claim a charter an agent does not
   have: the new test extracts the Persian charter name from each entry's
   `evidence` and asserts it is present in the vision, so a fabricated or
   mistranscribed citation fails the build.
5. **Cross-taxonomy smuggling.** Tried to express a reporting line to a Slice-1
   anchor as a dependency: the new test asserts every dependency is a known
   AG id, so no `agent.*` edge can enter the matrix through this mission.

### عفران (Evidence)
Every claim above points at a file, a test or a command:
- The 18 registrations: `config/agent_registry.yaml` (AG-26..AG-43, `git diff`);
  zero contract violations, asserted by `test_registry_agents_and_spec_conformance`
  and `test_registry_ops_blocks_validate` (both in the 2971).
- "authority NONE by default": `tests/test_m12_agent_registration.py::
  test_every_new_agent_grants_no_runtime_authority`, per agent.
- "no auto-creation": `test_no_slice1_agent_was_created` — asserts the registry
  holds no `agent.*` id and `CANONICAL_AGENT_IDS` is still 19.
- "37+": `test_registry_meets_the_queue_rows_floor`, 43 ≥ 37.
- Doc freshness: `engine/agent_matrix_v2.py --check` prints FRESH; pinned by
  `test_matrix_v2_doc_is_fresh`.
- Full-suite counts: the command and timings above, run this session.
- The pre-existing failure: proven pre-existing earlier in this night run by
  stashing every change of mine and parking the new files outside the tree — it
  failed identically on a pristine checkout; re-confirmed in isolation this
  session (1 failed, 8 passed).

**AUTOPILOT_RESULT: DONE**

# AHOS — M4 WAVE-DIRECTIVE DECLARATION (M-GAP-038 resolution)

```text
DOCUMENT_ID      = M4_WAVE_DIRECTIVE_DECLARATION
MISSION          = M4 (CONSTITUTIONAL ENFORCEMENT AND RUNTIME COMPOSITION RECONCILIATION)
CREATED_UTC      = 2026-09-28
STATUS           = DECLARED + MECHANICALLY PINNED (additive; no existing pin weakened)
AUTHORITY        = NONE CREATED. This document declares a classification already made in
                   adopted governance (docs/DOC_TRUTH_MAP.md section A) and pins it. It does
                   not create doctrine, does not ratify anything, and does not grant authority.
RUNTIME_EFFECT   = NONE
LANE_A_EFFECT    = NONE
SUPERSEDES       = NOTHING
REVERSIBLE       = YES — one commit (delete the pin + this doc) restores the prior state.
```

---

## 1. What M-GAP-038 actually is — corrected from M3

M3 recorded M-GAP-038 as "the doctrine-registry enforcement glob does not cover
`MASTER_DIRECTIVE_W43.md`", calling it a loophole in a CI-enforced constitutional law.
**That framing is too strong.** The complete M4 trace shows the glob's *substance* is correct and
the defect is elsewhere: the constitution has **two kinds of authority but declares and enforces
only one.**

### 1.1 Evidence

| # | Claim | Class | Basis |
|---|---|---|---|
| E1 | Exactly two `MASTER_DIRECTIVE_*` files exist on disk: `MASTER_DIRECTIVE_v1.md`, `MASTER_DIRECTIVE_W43.md` | **FACT** | `ls docs/canonical/MASTER_DIRECTIVE*`; `git ls-files \| grep -i master_directive` returns those two plus the registry and the test |
| E2 | The registry's `directives` array lists **only v1**, status ACTIVE | **FACT** | `docs/canonical/master_directive_registry.json` |
| E3 | Across the registry file's **entire git history, "W43" appears 0 times** | **FACT** | `git log -p -- master_directive_registry.json \| grep -c W43` → 0 |
| E4 | W43 was introduced in commit `5ccb0c0` (2026-08-21, owner `mainmovement`) whose message says "register Master Directive" — but **that commit touched only `README.md`, `MASTER_DIRECTIVE_W43.md`, `news.ts`, `page.tsx`. It did not touch the registry, the test, or the issue register.** | **FACT** | `git show --stat 5ccb0c0` |
| E5 | The only registry-like act in that commit is one README line: `- Master directive: docs/canonical/MASTER_DIRECTIVE_W43.md` | **FACT** | `git show 5ccb0c0 -- README.md` |
| E6 | W43 contains **0 of 5** required non-weakening invariants and **0 of 12** required protocol steps | **FACT** | simulation of `tests/test_master_directive.py:59-70` against W43 (see §1.2) |
| E7 | W43's sha256 appears **nowhere** as an integrity pin; the only hit across the repo is `"sha256_before_deletion"` in an archive deletion manifest | **FACT** | full-repo search for `87627c0a…` |
| E8 | v1's sha is pinned in three places (registry, `V1_PIN` in the test, R-42 in the register); W43's is pinned in zero | **FACT** | as above + `AHOS_ISSUE_REGISTER.md:780` |
| E9 | `docs/DOC_TRUTH_MAP.md` already classifies W43 as "Wave ops directive (**living, not registry ACTIVE**)" and states W44 has no directive of its own, so "W43 remains the governing one" | **EVIDENCE** (adopted governance, L2) | `docs/DOC_TRUTH_MAP.md` section A |
| E10 | W43's own text is **wave-scoped**, not permanent: "Web Command Center (**هدف این موج** — the goal of *this wave*)" and a 13-point "Definition of Done (خلاصه)" for that wave | **EVIDENCE** | `MASTER_DIRECTIVE_W43.md:51,96-110` |
| E11 | W43's substance is **consistent with**, not weakening of, v1: `UNKNOWN > fabricated`, `PAPER_ONLY`, `NO REAL TRADING`, `NO WALLET SIGNING`, and an explicit order not to break Governance/Safety boundaries | **EVIDENCE** | `MASTER_DIRECTIVE_W43.md:7,30,87-91,16` |

### 1.2 The decisive simulation

Had the enforcement glob simply been widened to `MASTER_DIRECTIVE_*.md` (the obvious-looking fix),
the constitutional test suite would have failed:

```text
MASTER_DIRECTIVE_v1.md:  missing invariants=0/5   missing protocol steps=0/12
MASTER_DIRECTIVE_W43.md: missing invariants=5/5   missing protocol steps=12/12
test_no_orphan_files_and_sha_match -> disk==listed: False
   only on disk: ['MASTER_DIRECTIVE_W43.md']   only in registry: []
```

**INTERPRETATION.** W43 is not an unregistered doctrine *version*. It is a **wave-scoped
operational directive**, a different class of authority. The `MASTER_DIRECTIVE_v*.md` glob
correctly excludes it — v1's change law (R-42) is written in terms of `MASTER_DIRECTIVE_v{n}`
("any future `MASTER_DIRECTIVE_v2` requires …"), and the registry's schema
(`version` numeric, `status` ∈ {ACTIVE, SUPERSEDED}, ACTIVE = max version) has **no slot** for a
wave directive. Registering W43 would either break `max()` (non-numeric version) or demote v1 to
SUPERSEDED (numeric version > 1) — which v1 forbids and which W43's content does not ask for.

### 1.3 The real defect

**The constitution operates two classes of directive but only names, pins, and enforces one.**
Consequences:

- W43 is reachable only by *filename prefix*; nothing in `docs/canonical/` says what class it is.
- It is the operationally governing directive (E9) yet has **no integrity pin** (E7/E8) — it could
  drift silently and nothing would notice. That is precisely the failure mode v1's registry was
  built to prevent, applied to the other class.
- The exclusion from the registry *looks accidental*, because the introducing commit announced
  "register Master Directive" (E4/E5) and never completed it.
- A future reader cannot tell "correctly excluded" from "registration was forgotten."

---

## 2. The declaration

```text
AHOS constitutional authority has TWO declared classes of master directive:

  CLASS A — PERMANENT DOCTRINE (constitutional)
    Files      : docs/canonical/MASTER_DIRECTIVE_v{n}.md
    Registry   : master_directive_registry.json, exactly one ACTIVE = highest {n}
    Enforced   : tests/test_master_directive.py
                 - sha256 immutability per version
                 - required non-weakening invariants in every version
                 - ordered 12-step wave-opening protocol in every version
                 - no orphan version files; every sha in AHOS_ISSUE_REGISTER.md
    Current    : v1, ACTIVE, ratified 2026-08-13T04:55:00Z
    Supersede  : only via MASTER_DIRECTIVE_v{n+1} + registry transition + R-series entry
                 carrying both hashes (R-42 change law)

  CLASS B — WAVE OPERATIONAL DIRECTIVE (governance, time-scoped)
    Files      : docs/canonical/MASTER_DIRECTIVE_<WAVE>.md
    Registry   : NOT in master_directive_registry.json — by declaration, not by omission.
                 These are wave-scoped and do not supersede Class A.
    Enforced   : tests/test_wave_directive_declaration.py (added by M4)
                 - the Class A / Class B partition on disk is pinned and exhaustive
                 - each Class B file's sha256 is pinned (drift detection — closes E7/E8)
                 - Class B files must not claim ACTIVE or supersession (no weakening)
                 - Class A invariants are re-asserted untouched
    Current    : MASTER_DIRECTIVE_W43.md
    Supersede  : a later wave directive supersedes an earlier one by explicit statement in the
                 newer file plus an AHOS_ISSUE_REGISTER.md R-series entry. It never supersedes
                 or demotes Class A.
```

This **does not merge the two classes**. It declares both, keeps the registry for Class A only,
and makes the separation exhaustive and test-pinned instead of convention-based.

**Scope note (binding):** a Class B directive governs *how a wave is executed* — operational
delegation and wave goals. It cannot amend Class A doctrine. Where the two could be read to
conflict, **Class A prevails**. W43's own text already obeys this: it explicitly forbids breaking
Governance and Safety boundaries (E11) rather than overriding them.

---

## 3. Disposition of W43

| Question | Answer | Class |
|---|---|---|
| Is W43 legitimate? | **Yes.** Owner-authored in `5ccb0c0`, operationally governing per DOC_TRUTH_MAP, substantively consistent with v1 | FACT + EVIDENCE |
| Is it a doctrine version? | **No.** Wave-scoped content, no invariants, no protocol, no version number | FACT (E6, E10) |
| Is it superseded? | **No.** No later wave directive exists; W44 has reports but no directive (E9). It remains the latest written directive | EVIDENCE |
| Is it historical/accidental? | **No.** Deliberately authored; the *registration* in `5ccb0c0` was incomplete, the file was not | FACT (E4, E5) |
| Should it be deleted or renamed? | **NO — not by me.** It is operationally governing. Renaming would break 9 referencing files and is a disposition decision requiring owner review (`docs/canonical/GOVERNANCE.md`: autonomous deletion prohibited) | DECISION REQUIRED |

---

## 4. Options considered

| Option | Verdict |
|---|---|
| **(1) Widen the glob to `MASTER_DIRECTIVE_*.md`** | **REJECTED.** Fails 5 invariants + 12 protocol steps + orphan check (§1.2). Would force W43 either to be rewritten to look like permanent doctrine (wrong — it is wave-scoped) or to be deleted. |
| **(2) Add W43 to the registry as a version** | **REJECTED.** Either breaks `max()` or demotes v1 to SUPERSEDED — a constitutional change v1's own law forbids and W43 never requested. |
| **(3) Add a `wave_directives` key to the registry** | **DEFERRED — DECISION REQUIRED.** Cleanest model, but it changes the registry schema (schema 1 → 2), which is constitutional enforcement. Requires owner ratification and an R-series entry. |
| **(4) Rename W43 so it cannot be mistaken for doctrine** | **DECISION REQUIRED.** Breaks 9 referencing files; disposition of an operationally governing document is owner review under GOVERNANCE.md. |
| **(5) Declare the two-class partition and pin it additively** | **ADOPTED (M4).** Strictly additive: one new test, one new doc. No existing pin weakened, no registry change, no rename, no deletion. Makes the existing DOC_TRUTH_MAP classification exhaustive, pinned, and drift-detecting. Fully reversible. |

---

## 5. What this does NOT do

- Does not create, ratify, supersede, or amend any doctrine.
- Does not change the registry, `tests/test_master_directive.py`, or any existing enforcement.
- Does not rename, delete, or move W43.
- Does not promote W43, grant it Class A authority, or make it supersede v1.
- Does not claim AGI/ACI achievement; that remains a continuing architectural objective and
  research requirement.
- Does not touch Lane A, maturity levels, governance boundaries, or enable live trading.

**Reversal path.** Delete `tests/test_wave_directive_declaration.py` and this document. The
repository returns to its pre-M4 classification state. The M3 description of M-GAP-038 stands as
the record of what the defect looked like before the partition was declared.

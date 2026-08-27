# AHOS CANONICAL — RECONCILIATION R1
**Type:** R-series governance documentation decision (documentation-only; no doctrine amendment).
**Scope:** Resolve the `MASTER_DIRECTIVE_W43.md` ↔ directive-registry ambiguity and record the W57
canonical-truth reconciliation. **This record changes no code, tests, configuration, runtime behavior,
Lane-A files, or the directive registry.** It only documents the verified repository relationship.

**Relationship to the R-series:** the canonical R-series lives in `AHOS_ISSUE_REGISTER.md`
(e.g. R-05, R-42). This file is a standalone canonical reconciliation note because no directive
*transition* occurs here (v1 stays ACTIVE), so the register's transition-entry law is not triggered.
A future governance action MAY cross-link this note from `AHOS_ISSUE_REGISTER.md`.

---

## A. Issue

`docs/canonical/MASTER_DIRECTIVE_W43.md` exists on disk and was referenced by `README.md` (and
`AHOS_WEB_COMMAND_CENTER.md`) under the heading "Master directive", which could be read as presenting
W43 as the active canonical directive. The status registry
(`docs/canonical/master_directive_registry.json`) does **not** list W43 as an active directive.

## B. Evidence (exact paths / references)

- `docs/canonical/master_directive_registry.json` — lists exactly one directive: `MASTER_DIRECTIVE_v1.md`,
  `status: ACTIVE`, `sha256: e2457c0d9dfbadba84ee666feb46f0a01f60663e749f1261f27988abfd837d79`.
- `docs/canonical/MASTER_DIRECTIVE_v1.md` — header: `status: ACTIVE`, `IMMUTABLE ONCE RATIFIED`,
  ratified 2026-08-13; registered as R-42 in `AHOS_ISSUE_REGISTER.md`.
- `docs/canonical/MASTER_DIRECTIVE_W43.md` — title `# AHOS — MASTER AUTONOMOUS EVOLUTION & COMPLETION
  DIRECTIVE (W43)`; filename is **not** in the `MASTER_DIRECTIVE_v{n}.md` version namespace.
- `tests/test_master_directive.py`:
  - `test_no_orphan_files_and_sha_match` compares the registry against `CANON.glob("MASTER_DIRECTIVE_v*.md")`
    — i.e. only files matching `MASTER_DIRECTIVE_v*.md`. `MASTER_DIRECTIVE_W43.md` does **not** match this
    glob, so the test does not treat it as a versioned doctrine file and passes with only `v1` listed.
  - `test_v1_immutable_and_present` pins the v1 sha256 (`V1_PIN`).
  - `test_registry_shape_single_active_highest` enforces exactly one ACTIVE = highest version.
- `README.md:57` — `- Master directive: \`docs/canonical/MASTER_DIRECTIVE_W43.md\`` (the ambiguous wording).
- `AHOS_WEB_COMMAND_CENTER.md:36` — `\`docs/canonical/MASTER_DIRECTIVE_W43.md\`` under "Master directive".
- `docs/canonical/KNOWLEDGE_MAP.md:156–157` — already correctly names `MASTER_DIRECTIVE_v1.md` as the
  immutable canonical directive with sha + registry + CI test (no ambiguity in the canonical index).

## C. Current canonical authority

**`docs/canonical/MASTER_DIRECTIVE_v1.md` is the ACTIVE canonical directive.** Authority is defined solely
by `docs/canonical/master_directive_registry.json` (the "exactly one ACTIVE; ACTIVE = highest version" law),
which is CI-enforced by `tests/test_master_directive.py`. Classification: **CONFIRMED** (registry + immutable
sha pin + passing test).

## D. Status of W43

`MASTER_DIRECTIVE_W43.md` is a **historical / legacy wave directive (reference-only)**. It is **not** a
registered versioned doctrine file (it is outside the `MASTER_DIRECTIVE_v{n}.md` namespace that the registry
and CI govern) and is **not** an independent active directive. Classification: **CONFIRMED** that it is not
registry-active; its content is retained as historical evidence and is **left byte-for-byte unchanged** by
this reconciliation.

## E. Immutability rule

`MASTER_DIRECTIVE_v1.md` remains **IMMUTABLE**. Any doctrinal change requires a **new** versioned file
(`MASTER_DIRECTIVE_v{n+1}.md`) **plus** a registry transition (`v{n}` → SUPERSEDED, `v{n+1}` → ACTIVE)
**plus** an `AHOS_ISSUE_REGISTER.md` entry in the same wave, with both sha256 values — exactly as the v1
change-law and `tests/test_master_directive.py` require. This reconciliation performs **no** such transition.

## F. Registry rule

Only the directive designated **ACTIVE** in `docs/canonical/master_directive_registry.json` is authoritative.
Presence of any other `MASTER_DIRECTIVE_*.md` file on disk (including W43) does **not** confer active
authority. The registry is **not** modified here; adding W43 to it would in fact break
`test_no_orphan_files_and_sha_match` (disk `v*` glob ≠ listed set), confirming W43 must remain unlisted.

## G. README correction

The "Master directive" pointer in `README.md` (and `AHOS_WEB_COMMAND_CENTER.md`) is corrected to name
`MASTER_DIRECTIVE_v1.md` as the ACTIVE, immutable directive and to label `MASTER_DIRECTIVE_W43.md` as a
historical wave directive (reference-only), linking to this record. No directive file content is edited.

## H. Test alignment

This documentation **agrees with** `tests/test_master_directive.py`: v1 is the single immutable ACTIVE
directive; the registry governs authority; the `MASTER_DIRECTIVE_v*.md` glob deliberately excludes W43.
The test is **not** modified and no conflict with it was found. (Per the task's stop-rule: had the test
contradicted this documentation, work would have stopped and reported the conflict instead of editing it.)

## I. Decision

> **`MASTER_DIRECTIVE_v1.md` is the active canonical directive; `MASTER_DIRECTIVE_W43.md` is not an
> independent active directive (historical/legacy, reference-only).**

This decision is supported by repository evidence (Section B) and is deterministic and non-authority-changing.

---

## Appendix — status legend used across the reconciled canonical docs
`CURRENT/IMPLEMENTED` · `PARTIAL` · `EXPERIMENTAL/OFF` · `MISSING` · `UNVERIFIED` · `CONTRADICTED`.
These reflect the completed AHOS audit (the authoritative observation set for this reconciliation) and
preserve uncertainty; `UNVERIFIED`/`LIKELY` findings are **not** promoted to `CONFIRMED`.

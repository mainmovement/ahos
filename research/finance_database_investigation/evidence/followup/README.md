# evidence/followup — Supplemental Findings Index

**Index only.** This file is a directory listing. It contains no analysis, no measurement, no
conclusion and no policy. Read the referenced JSON artifacts for content.

> ## Append-only, supplemental findings
>
> The two `E-*` artifacts listed below are **supplemental, append-only findings** added under
> separate written authorization from **Agent B — Engineering Governor**. They were **appended** to
> this directory. **Nothing pre-existing was modified, overwritten or deleted.**
>
> - **No historical document was corrected.** Documents 00–25 and `README.md` in the package root
>   remain **FROZEN** exactly as written. They still state the aggregate that `E-CORR-01` supersedes.
>   Where a supplemental artifact conflicts with a historical document, **the artifact governs** and
>   the conflict is recorded rather than edited away.
> - **No AHOS code or policy was changed.** No production file, test, requirement, package
>   configuration, workflow, provider, schema, fixture or decision-authority surface was created,
>   modified or deleted. `policy_status` on every artifact is **`CANDIDATE — NOT AHOS POLICY`** and
>   `implementation_authorized` is **`false`**.
> - **No archived JSON was overwritten.** Both target paths were verified absent before writing, and
>   the generator refuses to write to an existing path.

## Supplemental artifacts added by this pass

| File | Finding | Title | Status | Implementation authorized | Production impact | Policy status |
|---|---|---|---|---|---|---|
| `E-CORR-01_aggregate_row_count_reconciliation.json` | **E-CORR-01** | Aggregate row-count discrepancy: documented aggregate 304,495 versus reconciled aggregate 305,495 | VERIFIED | `NO` | `none` | `CANDIDATE — NOT AHOS POLICY` |
| `E-NEW-01_symbol_only_stub_rows.json` | **E-NEW-01** | 5,108 symbol-only stub rows across the corpus; in indices they are 5.32% of the table and are exactly the rows with an empty exchange | VERIFIED | `NO` | `none` | `CANDIDATE — NOT AHOS POLICY` |

## Pre-existing artifacts in this directory (unmodified)

| File | Finding | Note | Status | Implementation authorized | Production impact | Policy status |
|---|---|---|---|---|---|---|
| `d_gics_sequence.json` | — | *(pre-existing; unmodified by this pass)* | — | — | — | — |
| `f1_objective_a.json` | — | *(pre-existing; unmodified by this pass)* | — | — | — | — |
| `f2_a10_contract.json` | — | *(pre-existing; unmodified by this pass)* | — | — | — | — |
| `f3_na_regression.json` | — | *(pre-existing; unmodified by this pass)* | — | — | — | — |
| `f4_identity.json` | — | *(pre-existing; unmodified by this pass)* | — | — | — | — |
| `f5_gics_replication.json` | — | *(pre-existing; unmodified by this pass)* | — | — | — | — |

## Provenance of the supplemental artifacts

| Field | Value |
|---|---|
| Authorized by | **Agent B — Engineering Governor** (archive the two newly discovered measurements only) |
| Authored by | **Agent E — Evidence Authority** |
| Authorized output directory | `research/finance_database_investigation/evidence/followup/` |
| Files authorized | exactly three — the two JSON artifacts above and this index |
| Generation | Values were **computed by direct measurement at generation time**, not transcribed from prose. The generating script was scratch (`/tmp/e_gen.py`) and was **not committed**; each artifact carries a full `reproduction_recipe` so it can be regenerated without it |
| Research environment | `/tmp/fdb2_venv` (Python 3.11.2, pandas 3.0.5), clone `/tmp/fdb2_repo` @ `a174c97d3bba96fc1a82b2e1068fb3ec5e02e634` |
| AHOS tree state at generation | branch `arena/01a0a5c8-ahos`, HEAD `2728b230f16e256a4f017cb8377f42ddf42b6f8f` |
| Package documents | 00–30 + root `README.md` — **all frozen** |

## Relationship to the parent package

| Artifact | Registered in | Rule candidate | Knowledge item |
|---|---|---|---|
| `E-CORR-01` | 30 §30.3(v), 26 §26.5 | — | **KN-11** |
| `E-NEW-01` | 30 §30.3(v), 26 §26.3 | **DQR-05** | **KN-12** |

Both documents 26 and 28 recorded that these two measurements existed **only in prose**, because the
pass that produced them was authorized to create documents 26–30 and no evidence artifact. This
directory entry closes that gap. See document 30 §30.4 (*ENV-DUR-01 residual risk*).

**Related corrections not archived here** (recorded in document 30 §30.3, no new artifact required):
`E-CORR-02` (interpretation of the archived `rows_lost_under_release_semantics` field) and
`E-CORR-03` (verification-instrument defects found in the final check suite).

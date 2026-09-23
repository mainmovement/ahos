# AID_STATIC — M1 post-merge static review of PR #108 (NOT Agent-16 VERIFY)

> **AID_STATIC / AID_NOT_VERIFY / AID_NOT_PASS** — Chief of Staff static/remote aid only.  
> **≠ Agent-16 VERIFY packet. ≠ Agent-19 CHALLENGE absorb.**  
> **This file is NOT a substitute for independent Agent-16 IV (VERIFY) on merge SHA.**  
> Do not cite this file as post-land VERIFY, D1_ON_MAIN CLOSED, or readiness.  
> Stamp applied 2026-09-24 by Agent-01 after Agent-19 CHALLENGE on CoS pack.

**Date:** 2026-09-24 (Asia/Tehran, UTC+3:30)  
**Upstream:** `mainmovement/ahos`  
**Merge SHA:** `d721d92d08450b69a09d6ff1e626470ad8949edf` (also current `main` HEAD at verify time)  
**PR:** [#108](https://github.com/mainmovement/ahos/pull/108) — MERGED 2026-09-15T21:09:24Z  
**Title:** `fix(knowledge): W1.3 identity spoof harden (exact type + always-recompose)`  
**Method:** Remote static only (`gh api` + `raw.githubusercontent.com`). **No git clone. No local pytest.** Cloud coding agents unavailable.

---

## Verdict: **AID_STATIC_COHERENCE_WITH_GAPS** (static aid only — **≠** Agent-16 IV; ban bare `PASS` / `PASS_WITH_GAPS` as AID verdict)

| Dimension | Result |
|-----------|--------|
| Fix A present on main (`type is` / `_exact_type`) | **YES** |
| Fix B present on main (always-recompose; discard `dossier=`) | **YES** |
| Tests T1–T11 coherent with Fix A+B | **YES** (static) |
| Suite executed in this session | **NO** — limitation |
| Independent Agent-16 VERIFY / Agent-19 re-CHALLENGE on merge SHA | **NOT EVIDENCED** here |
| D1 “closed” claim | **NOT claimed** (PR body forbids it until post-land VERIFY) |

**Why not PASS:** residual OUT_OF_SCOPE (real-typed hand-built `IdentityResolution`/`TokenIdentity` with `VERIFIED`), no executable test run, no post-land VERIFY packet on this SHA.  
**Why not FAIL:** both hardens are on `main` at the stated SHA; regressions are present and match the intended threat model for string/module spoof and caller-supplied dossier forge.

---

## Files fetched (main @ merge SHA ≡ main HEAD)

| Path | Source | Lines (fetched) |
|------|--------|----------------:|
| `architecture/knowledge/dossier.py` | raw main | 781 |
| `architecture/knowledge/evidence_graph.py` | raw main | 677 |
| `tests/test_token_dossier.py` | raw main | 1118 |
| `tests/test_evidence_graph.py` | raw main | 728 |

Local copies under `/workspace/ahos-out/pr108_files/` (analysis aid only; not a checkout).

PR file stats: dossier +17/−5; evidence_graph +22/−12; `test_evidence_graph` +206/−1; `test_token_dossier` +180/−3.

---

## Fix A — exact class identity (`type is`)

**Location:** `architecture/knowledge/dossier.py`

```text
def _exact_type(obj: Any, module: str, name: str) -> bool:
    """Fail-closed exact class identity (not string name/module spoof)."""
    mod = sys.modules.get(module)
    if mod is None:
        return False  # fail-closed
    real = getattr(mod, name, None)
    return real is not None and type(obj) is real
```

`_is_supported_identity_resolution` / `_is_supported_token_identity` both call `_exact_type` against `architecture.identity.types::{IdentityResolution,TokenIdentity}` via split module name (no contiguous `architecture.identity` import token in dossier source — intentional boundary).

**Previous (pre-PR, from patch):** string compare on `__module__` + `__name__` — spoofable by `type("IdentityResolution", (), {"__module__": "architecture.identity.types", ...})`.

**Evidence quote (module docstring):**  
> Canonical identity is authorized only by a supported IdentityResolution plus TokenIdentity (exact class object identity via sys.modules; no import of that package). Arbitrary caller objects with `state=VERIFIED` are rejected.

---

## Fix B — always-recompose

**Location:** `architecture/knowledge/evidence_graph.py` → `compose_evidence_graph`

```text
_ = dossier  # discarded — not authority
dossier = compose_dossier(
    identity=identity,
    decision=decision,
    score=score,
    security=security,
    claims=claims,
    metadata=metadata,
)
```

Docstring:  
> The dossier= argument is accepted for API compatibility only and is discarded. Authority always comes from a fresh compose_dossier(...) over raw kwargs (always-recompose).

`_canonical_token_allowed` still checks `identity_state == "VERIFIED"` and non-empty `canonical_token_id`, but only against a **freshly composed** dossier.

---

## Test coherence (static)

| ID | File | Intent | Static coherence |
|----|------|--------|------------------|
| T1 | `test_token_dossier.py` | dynamic IR+TI spoof → no VERIFIED/canonical | Matches Fix A |
| T2 | same | forge IR-only or TI-only → reject | Matches Fix A |
| T3 | same | real VERIFIED still canonical | Positive path preserved |
| T4 | same | UNRESOLVED/CONFLICT non-canonical | Unchanged semantics |
| T5 | `test_evidence_graph.py` | hand-built `TokenDossier` via `dossier=` → no canonical | Matches Fix B |
| T6 | same | `identity=` real VERIFIED still works | Positive path via recompose |
| T7 | `test_token_dossier.py` | source lacks contiguous identity import / seal symbols; has `import sys` + `_exact_type` | Matches design |
| T8 | `test_evidence_graph.py` | A-alone insufficient; hand dossier fails B | Explicit A∧B necessity |
| T9 | both | spoof through W2 / compose_dossier path | Cross-surface |
| T10 | both | combined A+B closed; real path OK | Combined |
| T11 | `test_evidence_graph.py` | seal symbols absent; hand dossier discarded | Anti-seal-forge |

Also updated: prior `test_w1_dossier_can_be_projected_without_recompose_identity` now asserts `dossier=` alone yields `canonical_token_id is None` — **behavior change intentional**.

W1.2 tests updated so type-spoof hits `identity_input_invalid` (Fix A) before field-access paths; exact-type hostile-token path still covered via monkeypatch on real `IdentityResolution`.

**PR claimed test plan:** `pytest tests/test_token_dossier.py tests/test_evidence_graph.py -q` (108 passed on scratch VERIFY — **not re-run here**).

---

## Limitation (binding)

> **This agent cannot run the repository test suite without a checkout/clone.**  
> Cloud coding / on-demand agents are UNAVAILABLE (usage exhausted).  
> All conclusions above are **static remote review only**. Passing CI on GitHub for #108 was not independently re-confirmed in this session beyond merge metadata.

---

## Residual risks

1. **OUT_OF_SCOPE (PR body):** Upstream **real-typed** objects (`type(obj) is IdentityResolution` / `TokenIdentity`) hand-built with `state=VERIFIED` can still authorize canonical via `compose_dossier(identity=...)`. Fix A stops *name/module spoof*, not *legitimate-class forgery*.
2. **Fail-closed unload:** If `architecture.identity.types` is not in `sys.modules`, `_exact_type` returns False → no VERIFIED (safe but may surprise callers who expected soft degrade).
3. **Process-level attacks:** Replacing the class object in `sys.modules["architecture.identity.types"]` still beats `type is` (shared with most Python identity checks; not claimed closed).
4. **API footgun:** `dossier=` remains in the signature (discarded). Callers who relied on hand-built dossiers **break** (intended). Dead parameter may confuse future authors until deprecated/removed.
5. **Governance gap:** PR explicitly: *Does not claim D1 closed until post-land Agent-16 VERIFY + Agent-19 re-CHALLENGE on this SHA.* No such packet was located/verified in this static pass.
6. **No Lane-A / trading impact observed** in these four files (Lane B `architecture/knowledge/**` + tests only).

---

## What a cloud agent must re-run locally (when on-demand enabled)

```bash
# From a clean main checkout at d721d92d08450b69a09d6ff1e626470ad8949edf (or later main containing it)
python -m pytest tests/test_token_dossier.py tests/test_evidence_graph.py -q
# Optional broader identity/knowledge smoke (discoverable neighbors; not claimed by PR #108):
python -m pytest tests/test_canonical_identity.py tests/test_identity_fusion.py -q
# Lane-A integrity (must stay green; no edits expected):
python scripts/freeze_lane_a.py   # or project’s documented verify flag — do NOT --write
```

`pytest.ini` on main: `testpaths = tests`, `python_files = test_*.py`, `pythonpath = .`

Post-land governance (from PR body): Agent-16 VERIFY packet + Agent-19 re-CHALLENGE **on merge SHA** before any “D1 closed” language.

---

## Epistemic label for this document

`STATIC_REMOTE_REVIEW` · `AID_STATIC` · `IMPLEMENTED_ON_MAIN` (code+tests visible) · `EXECUTABLE_VERIFY = NOT_RUN` · `INDEPENDENT_CHALLENGE = NOT_EVIDENCED` · **NOT Agent-16 IV substitute**

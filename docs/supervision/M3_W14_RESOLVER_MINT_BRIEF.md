# M3 DESIGN BRIEF (AID) — W1.4 resolver-mint marker (NOT implementation; NOT VERIFY)

> **DESIGN_AID / AID_NOT_VERIFY / AID_NOT_PASS** — design brief only; not an implementation PR.
> **AID_NOT_VERIFY / AID_NOT_PASS** — Chief of Staff static/remote aid only.  
> **≠ Agent-16 VERIFY packet. ≠ Agent-19 CHALLENGE absorb.**  
> Do not cite this file as post-land VERIFY, D1_ON_MAIN CLOSED, or readiness.  
> Stamp applied 2026-09-24 by Agent-01 after Agent-19 CHALLENGE on CoS pack.


**Date:** 2026-09-24 (Asia/Tehran, UTC+3:30)  
**For:** next cloud / on-demand coding agent (when usage restored)  
**Base:** `mainmovement/ahos` main @ `d721d92d08450b69a09d6ff1e626470ad8949edf` (PR #108 merged)  
**Fork workflow:** `sunsniper98-ctrl/ahos` feature branch → PR into upstream main  
**Mode:** PAPER_ONLY · Lane A frozen · no trading execution · no soak interruption

---

## One narrow reversible follow-up

### Title (proposed)
`fix(knowledge): W1.4 resolver-mint marker for VERIFIED identity (dossier/graph refuse unminted VERIFIED)`

### Why this (not something else)
PR #108 closed **string/module spoof** (Fix A) and **caller `TokenDossier` trust** (Fix B).  
PR #108 explicitly left **OUT_OF_SCOPE:** hand-building a **real-typed** `IdentityResolution` + `TokenIdentity` with `state=VERIFIED` and passing it to `compose_dossier` / `compose_evidence_graph(identity=...)`.

That residual is the highest-value **Lane-B identity/security** follow-up that:
- does not touch `discovery/**` or `paper_trading/**`,
- does not change scoring semantics,
- does not enable live trading,
- is reversible via composer version bump (`token-dossier-composer-v1.3`) only (no env/feature-flag hatch),
- has clear acceptance tests.

### Non-goals (hard)
- No Lane A edits; no `config/lane_a_freeze.sha256 --write`.
- No live trading, wallets, credentials, paid providers.
- No AGI/ACI capability claims; no readiness upgrade language.
- No “D1 closed” / “C-FORGE-07 closed” / “identity unforgeable” in PR title/body (dossier/graph refuse-unminted only; Agent-16/19 on **new** SHA before any D1 talk).
- No seal cryptography theater; opaque mint marker only.
- No **ungated public** mint/forge API (`mint_verified_resolution` public or in `__all__`); test path must be `_`-private or real `resolve_identity`.
- No `AHOS_ALLOW_UNMINTED_VERIFIED` in v1.3 (prefer omit); if ever present: default OFF, CI must never enable.
- Cookie transfer / other VERIFIED consumers outside dossier/graph: OUT_OF_SCOPE unless gated in same PR.
- Do not remove `compose_dossier` positive path for real resolver output.

---

## Authority surface (Lane B only)

| Path | Change |
|------|--------|
| `architecture/identity/types.py` (and/or `resolution.py`) | Add private/opaque `_verified_mint` (or equivalent) set **only** by resolver/factory helpers that already produce VERIFIED after real checks |
| `architecture/knowledge/dossier.py` | In `_extract_identity` / verified gate: require mint marker (or equivalent) before accepting `identity_state == VERIFIED` → canonical |
| `tests/test_token_dossier.py` | New T12+: hand-built real-typed VERIFIED without mint → no canonical; resolver-minted VERIFIED still works |
| `tests/test_evidence_graph.py` | Mirror via `identity=` path |
| `tests/helpers_identity.py` | Fixtures via `_mint_verified_for_tests` (private, not in `__all__`) or real `resolve_identity` — **not** a public forge API |
| Optional docs | Short note in `architecture/knowledge/EVIDENCE_GRAPH.md` residual threat model — docs only |

**Out of surface:** `discovery/**`, `paper_trading/**`, Telegram/n8n, TS scoring, cognitive loop soak wiring.

---

## Design sketch (implementer choice — keep minimal)

Preferred minimal pattern:

1. Module-private object or `object()` cookie stored on `IdentityResolution` **only** (not on `TokenIdentity`) as `_ahos_verified_mint` / frozen field default `None`.
2. **Only** `architecture.identity.resolution.resolve_identity` attaches the cookie via module-private `_attach_verified_mint` / `_VERIFIED_MINT`. Test helper if needed: `_mint_verified_for_tests` (leading `_`, not in `__all__`); **VETO** ungated public `mint_verified_resolution`.
3. `compose_dossier` treats `state == VERIFIED` **without** cookie as **reject** with mandatory `reject_code="identity_verified_unminted"` (fail-closed, no canonical, **no silent demotion**).
4. Dataclass/`__init__` of types must not accept caller-supplied cookie from public kwargs (use `object.__setattr__` inside factory, or `InitVar` discarded, or `__post_init__` that clears cookie unless `factory_token` matches module secret).

Reversibility: composer version bump (`token-dossier-composer-v1.3`). **Omit** `AHOS_ALLOW_UNMINTED_VERIFIED` in v1.3 (Agent-19 / سپهر). No escape hatch preferred.

Alternative (narrower, if mint marker proves invasive): **deprecate `dossier=`** with `DeprecationWarning` + assert zero production call sites — *does not* close OUT_OF_SCOPE; only API hygiene. Prefer mint marker as primary; deprecation as optional drive-by **only if** zero call sites confirmed.

---

## Acceptance tests outline

```text
A1  Hand-built IdentityResolution(TokenIdentity(state=VERIFIED, ...)) exact types,
    no mint → compose_dossier: canonical_token_id is None; reject_code MUST be
    identity_verified_unminted (no silent demotion to UNRESOLVED/None-without-code).

A2  Same object into compose_evidence_graph(identity=...) → graph.canonical_token_id is None;
    token node metadata canonical is False.

A3  resolve_identity path (or _mint_verified_for_tests / resolve_identity used by helpers_identity)
    → VERIFIED + canonical still works (parity with W1.3 T3/T6). No public mint API.

A4  Dynamic type() spoof still fails (W1.3 T1/T9 regressions green).

A5  Hand-built TokenDossier via dossier= still discarded (W1.3 T5/T11 green).

A6  UNRESOLVED / CONFLICT real-typed paths unchanged (W1.3 T4).

A7  Source hygiene: dossier.py still has no contiguous "architecture.identity" import token
    if that invariant remains binding; if mint check needs types, use existing sys.modules exact-type path only.

A8  Lane A freeze verify unchanged (script check, no --write).

A9  No public mint / forge API: mint helpers absent from architecture/identity `__all__`;
    production attach = module-private `_attach_verified_mint` from `resolve_identity` only;
    tests via `tests/_mint_support.py` `_mint_verified_for_tests` (leading `_`).

A10 No `AHOS_ALLOW_UNMINTED_VERIFIED` in v1.3 tree (`rg` zero hits — omit preferred).
```

Commands for implementer:

```bash
pytest tests/test_token_dossier.py tests/test_evidence_graph.py tests/test_canonical_identity.py -q
python scripts/freeze_lane_a.py   # verify only
```

---

## PRE-FLIGHT table (paste into PR)

| Field | Content |
| --- | --- |
| Intended change | W1.4: VERIFIED identity requires resolver mint marker before dossier/graph authorize canonical |
| Authority surface | Lane-B identity types/resolution + knowledge dossier/graph + tests/helpers only |
| Reason | Dossier/graph refuse unminted real-typed VERIFIED (PR #108 residual scoped; not global C-FORGE-07 closed) |
| Expected behavior | Unminted real-typed VERIFIED → reject_code identity_verified_unminted, no canonical (dossier/graph only); resolver-minted → canonical; spoof paths stay closed; do not claim C-FORGE-07 globally closed |
| Risks | Test fixtures must mint; any production hand-built VERIFIED breaks (intended); fail-closed if factory mis-wired |
| Test plan | pytest commands above + freeze verify |
| Locks | PAPER_ONLY; no Lane A; no D1-closed claim until post-land VERIFY+CHALLENGE; no readiness upgrade |

---

## Post-land governance (required language)

After merge:

1. Agent-16 VERIFY packet on **new** merge SHA (pytest receipt + freeze OK).  
2. Agent-19 re-CHALLENGE (try unminted real-typed forge + spoof suite).  
3. Only then discuss D1 status — never in the implementation PR body as done.

---

## Explicitly deferred (do not sneak in)

- Independent kill-switch hardware/path (governance + design).  
- World model / AGI memory soak wiring.  
- Expanding agent_registry PARTIAL→EXISTS.  
- Removing `dossier=` in the same PR unless call-site census is zero and tests updated (can be W1.4b).

---

## Success criteria for the cloud agent

- [ ] Single focused PR, reversible via composer bump only (no feature-flag/env hatch), Lane-B only  
- [ ] Acceptance tests **A1–A10** green locally (A9 public-mint veto + A10 hatch omit)  
- [ ] No Lane A file changes  
- [ ] Honest PR body (no AGI, no PRODUCTION_READY, no D1 closed, no C-FORGE-07 closed, no unforgeable, no public mint API)  
- [ ] Does not push to `main`; opens PR for human merge  

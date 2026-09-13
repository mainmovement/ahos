# Claim / Evidence Graph View (W2)

Read-only projection of existing AHOS evidence, claims, provenance, and the
W1 token dossier. Isolated research/analytical component.

## Purpose

Make Evidence → Claim → Contradiction → Provenance → Token inspectable
without minting new factual or identity authority.

## Scope

Composition only. No runtime, pipeline, Lane A, P5, store writes, network,
or decision-engine wiring.

## Vocabularies

Nodes: `TOKEN`, `EVIDENCE`, `CLAIM`, `SOURCE`, `CONTRADICTION`, `PROVENANCE`, `DECISION`

Edges: `ATTACHED_TO`, `DERIVED_FROM`, `SUPPORTED_BY`, `CONTRADICTS`,
`SOURCED_FROM`, `HAS_PROVENANCE`, `RELATES_TO`

## Epistemic rules

Never upgrade INFERRED/UNKNOWN/UNRESOLVED/CONFLICT/REJECT.
Claims are `INFERRED`. `FACTUAL_PREMISE` is a copied label only.
Provider-`VERIFIED` evidence maps to `DERIVED`, never `OBSERVED`.

## Identity rules

Canonical TOKEN nodes require W1 `identity_state == VERIFIED` and
`canonical_token_id`. Symbol, operational token_id, and aliases stay
explicitly non-canonical.

## Contradictions

Both claims remain. A `CONTRADICTION` node plus `CONTRADICTS` edges record
the disagreement. No silent winner.

## Unknowns

Missing evidence/claims stay missing. The graph does not invent sources,
timestamps, confidence, or relationships.

## Deterministic IDs

Field-derived local IDs. No UUID, `hash()`, or composition clocks.
A graph ID is never a canonical token identity.

## Immutability

Frozen graph. `as_dict()` returns a detached copy.

## Consumer contract

`identity_state`, `canonical_token_id`, `security_state`, and
`decision_outcome` are not sufficient authority. Also read `conflicts`,
`unknowns`, `epistemic_map`, and `provenance`.

## Non-goals

Council, world model, calibration, runtime integration, W1 redesign,
automatic promotion, claim-store writes.

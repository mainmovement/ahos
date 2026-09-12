# Human Feedback Foundation (W3)

Read-only signal contract for human feedback about AHOS assessments.
Isolated research/analytical component.

## Purpose

Record human judgments about tokens, decisions, alerts, observations,
evidence quality, and system behavior so later governed evaluation can
compare them to outcomes. Feedback is evidence about a human judgment.

## Scope

Composition only. No persistence, training, calibration, runtime, pipeline,
Lane A, P5, scoring, security, identity resolution, or trading.

## Feedback vocabulary

`CONFIRMATION`, `CORRECTION`, `DISAGREEMENT`, `FALSE_POSITIVE`,
`FALSE_NEGATIVE`, `MISSED_SIGNAL`, `SECURITY_CONCERN`,
`IDENTITY_CORRECTION`, `EVIDENCE_QUALITY`, `DECISION_QUALITY`,
`ALERT_QUALITY`, `OBSERVATION_QUALITY`, `SYSTEM_BEHAVIOR`, `OTHER`

## Value vocabulary

`POSITIVE`, `NEGATIVE`, `UNCERTAIN`, `CORRECT`, `INCORRECT`, `UNKNOWN`

These are feedback values, not world truth.

## Epistemic semantics

Every signal has `epistemic_status = FEEDBACK_SIGNAL`.
W3 never assigns `OBSERVED`, `FACTUAL`, `FACTUAL_PREMISE`, or `VERIFIED`.

## Authority boundary

Copied `authoritative_state` (decision, security, identity) is never
overwritten. Feedback sits beside it. Disagreement is recorded, not resolved.

## Identity boundary

Canonical subject only when the caller supplies `subject_kind=CANONICAL_TOKEN`,
`identity_state=VERIFIED`, and a subject id. Symbol, alias, and operational
ids stay non-canonical. W3 does not resolve identity.

## Provenance

Preserved only when supplied. Missing provenance stays missing.
"Human said X" is never rewritten as market evidence.

## Temporal semantics

`timestamp` is preserved only if the caller supplies a numeric value.
W3 never calls `now()`. Feedback time is not event, prediction, observation,
or evaluation time.

## Conflict handling

Conflicting signals on the same subject remain visible in aggregation.
No automatic winner.

## Immutability

Frozen records. `as_dict()` returns a detached copy. Source objects are
not mutated.

## Deterministic IDs

Field-derived `feedback:...` ids. Not token identity. No UUID, `hash()`,
or hidden clocks.

## Consumer contract

Do not use `value` alone as authority. `CORRECT` is not `FACTUAL`.
`INCORRECT` is not `SYSTEM_INVALID`. Inspect type, value, subject,
epistemic status, provenance, conflicts, timestamp semantics, actor class,
and canonical-versus-operational identity.

## Non-goals

Learning, calibration, decision override, security override, identity
promotion, runtime wiring, persistence, UI, Council, trading, W4.

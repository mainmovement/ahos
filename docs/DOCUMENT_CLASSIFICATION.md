# AHOS documentation classification and precedence

**Canonicalization date:** 2026-08-19

When documents disagree, use this order:

1. code, versioned schemas, safety tests, and Lane-A freeze manifests;
2. `docs/canonical/CANONICAL_STATUS.md` for current capability status;
3. the canonical and operational documents listed below;
4. research/design documents as proposals or experimental records;
5. historical phase reports only as evidence of what was claimed or observed at that time.

A filename containing “FINAL”, “PRODUCTION”, or “READY” does **not** make an old
report current.

## Canonical

- `README.md` — entry point and safety/architecture summary.
- `docs/canonical/CANONICAL_STATUS.md` — current integrated architecture,
  capability, validation, Windows workflow, limitations, and next phase.
- `docs/canonical/{MASTER_DIRECTIVE_v1,MISSION,SECURITY,GOVERNANCE,ARCHITECTURE,
  DATA_MODEL,DISCOVERY,PROVIDERS,RESEARCH,TELEGRAM,ROADMAP}.md` — normative
  domain references. Where an older count/status appears, the status document
  above takes precedence.
- `SECURITY.md`, `CONTRIBUTING.md`, and `ARCHITECTURE.md` — repository-level
  policy/entry documents.

## Operational

- `QUICKSTART.md`, `INSTALLATION.md`.
- `AHOS_OPERATOR_QUICKSTART_WINDOWS.md`, `AHOS_WINDOWS_DEPLOYMENT_GUIDE.md`,
  `AHOS_WINDOWS_OPERATOR_RUNBOOK.md`.
- `AHOS_LOCAL_ACTIVATION_CHECKLIST.md`, `AHOS_LOCAL_SOAK_PROTOCOL.md`,
  `AHOS_MONTH1_SOAK_PROTOCOL.md`, and `docs/RUNBOOK_OPERATIONS.md`.
- `docs/n8n_setup_guide.md` and `docs/TELEGRAM_TEST_PROCEDURE.md`.

Operational documents describe procedures. A soak or readiness result is valid
only when its required artifacts and gates actually exist.

## Research and design

- `docs/mission_v1_1/`, `docs/architecture/`, score/security designs,
  `docs/STRATEGY_SPEC_v1.0.md`, and strategic gap/roadmap documents.
- `research/`, `research/reports/`, and `research/experiments/` evidence and
  manifests.
- Council, provider, target architecture, self-repair, and future-state designs.

These are deliberately retained. They may describe unimplemented targets and
must not be read as proof that a capability is live.

## Historical

- Root `AHOS_PHASE*.md`, `AHOS_*REPORT.md`, past readiness/gate/month
  recommendations, and progress snapshots are point-in-time records.
- `docs/archive/` is explicitly historical.
- `docs/history/source-patches/` preserves the three audited source-history
  patches byte-for-byte.
- `docs/history/snapshots/` preserves phase file-list snapshots byte-for-byte.
- Dated JSON under `reports/` is executed evidence from its stated host/time,
  not a current readiness certificate.

## Superseded/obsolete as current guidance

The old “final”, “production readiness”, and phase-completion claims are
superseded **as current status**, but retained for provenance. In particular,
`AHOS_FINAL_STATUS.md`, `AHOS_PRODUCTION_READINESS_REPORT.md`,
`AHOS_PHASE_XX_COMPLETION_REPORT.md`, and older reality audits must not override
`docs/canonical/CANONICAL_STATUS.md`.

No unique historical document was discarded merely because its title or topic
overlaps another file. Cleanup was limited to the predeclared manifest in
`docs/audit/DELETION_MANIFEST.md`.

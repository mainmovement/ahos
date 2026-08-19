# AHOS evidence-first forensic audit — index

**Audit date:** 2026-08-19
**Audited code/data snapshot:** `arena/01a01a99-ahos` at `c77597899dce60d192abe94cb017279089b065f7`
**Upstream state at audit close:** PR #9 was OPEN, non-draft, MERGEABLE, and not merged into `main`.
**Mode:** non-destructive. No product code, schema, runtime data, or historical artifact was deleted or rewritten during this audit.

## Verdict

AHOS has a substantial, safety-conscious deterministic implementation and a broad passing test suite, but it is **not yet operationally proven as a complete autonomous Windows/local-AI system**. Its strongest verified surfaces are deterministic intelligence/scoring, safety boundaries, schema bootstrap, provider contracts under injected transports, and static/runtime-component tests. Its weakest surfaces are real evidence accumulation, native Windows/Docker/n8n execution, dependency reproducibility, runtime-state isolation, import safety, Local AI beyond chat transport, and autonomous engineering/tool execution.

The audit therefore assigns an overall **YELLOW** capability verdict with several **RED deployment blockers**. “1,414 tests passed” is valid evidence for the tested checkout; it is not evidence that external providers, Telegram, Docker, n8n, Ollama, PostgreSQL, or a Windows laptop ran.

## Required artifacts

1. [CURRENT_ARCHITECTURE_MAP.md](CURRENT_ARCHITECTURE_MAP.md)
2. [CAPABILITY_MATRIX.md](CAPABILITY_MATRIX.md)
3. [DUPLICATE_REGISTER.md](DUPLICATE_REGISTER.md)
4. [DEAD_OR_ORPHAN_REGISTER.md](DEAD_OR_ORPHAN_REGISTER.md)
5. [DOCUMENTATION_DRIFT_REGISTER.md](DOCUMENTATION_DRIFT_REGISTER.md)
6. [TEST_REALITY_REPORT.md](TEST_REALITY_REPORT.md)
7. [DATA_INTEGRITY_REPORT.md](DATA_INTEGRITY_REPORT.md)
8. [WINDOWS_READINESS_REPORT.md](WINDOWS_READINESS_REPORT.md)
9. [LOCAL_AI_READINESS_REPORT.md](LOCAL_AI_READINESS_REPORT.md)
10. [AGENT_AUTONOMY_GAP_REGISTER.md](AGENT_AUTONOMY_GAP_REGISTER.md)
11. [OSS_CANDIDATE_REGISTRY.md](OSS_CANDIDATE_REGISTRY.md)
12. [PRIORITIZED_ROADMAP.md](PRIORITIZED_ROADMAP.md)

## Evidence summary

| Evidence | Result |
|---|---|
| Tracked inventory | 660 files; 274 Python; 160 Markdown; 124 JSON; 16 YAML; 7 SQL; 100 top-level test modules; 6 n8n workflows |
| Python parsing | 274 modules, 0 AST parse errors |
| Full pytest at audited snapshot | **1,414 passed in 171.47s**; audit-artifact regression **1,414 passed in 170.56s** |
| Focused provider tests | **83 passed in 6.80s** |
| Focused score/calibration tests | **58 passed in 5.52s** |
| Skip/xfail markers | none found |
| Import/architecture/secret gate | PASS; 153 modules imported; 17 evidence-boundary files and 2,073 source files scanned |
| Static n8n validation | 6/6 JSON workflows passed structural validator |
| SQLite | 4 ignored local stores; all `integrity_check=ok`; 47 tables total; only 20 rows, all in `control_flags` and attributable to the import-time test harness |
| Calibration | `INSUFFICIENT_DATA`; 0 predictions, 0 labels |
| Research datasets | 12 CSV output hashes, row counts, and first/last timestamps match their manifests |
| Docker/PowerShell execution | NOT RUN: neither Docker nor PowerShell was available on the audit host |
| External live operation | NOT RUN: no live provider, Telegram, n8n, PostgreSQL, Ollama, or native Windows session was started |
| Working tree before audit artifacts | clean |

## Status vocabulary

- `IMPLEMENTED` — executable code exists and has meaningful local evidence.
- `PARTIALLY_IMPLEMENTED` — useful implementation exists but the claimed end-to-end capability or integration is incomplete.
- `SCAFFOLD` — contracts/state machine/configuration exist without an operational loop.
- `DOCUMENTED_ONLY` — prose/design without executable implementation.
- `DEAD_CODE` — no current caller/entry path and no deliberate experimental role established.
- `DUPLICATE` — overlaps another capability; semantic comparison is required before removal.
- `BROKEN` — execution violates its contract, has a demonstrated harmful side effect, or cannot work as delivered.
- `ORPHAN` — executable/tested in isolation but not connected to a delivered runtime.
- `EXPERIMENTAL` — deliberately retained research/versioned implementation.
- `REQUIRES_EXTERNAL_SERVICE` — needs a network/server/provider not supplied by the process.
- `REQUIRES_USER_ACTION` — requires credentials, import, installation, approval, or a host action.

## Evidence precedence used in this audit

1. Immutable laws, versioned schemas, current code, and safety tests.
2. Re-executed evidence from this exact snapshot.
3. `docs/canonical/CANONICAL_STATUS.md` and current operational instructions.
4. Dated machine-readable artifacts, only for the host/time/commit they identify.
5. Research/design documents.
6. Historical phase reports and marketing-like readiness titles.

Historical reports were retained as history, not treated as current operational proof. No candidate deletion in the registers is approved by this audit; every recommendation is “preserve”, “reconcile”, “archive only after manifest”, or “fix after human approval.”

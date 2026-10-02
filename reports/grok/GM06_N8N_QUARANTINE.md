# GM-06: n8n governance validator rules and ahos_03 quarantine

| Field | Value |
|---|---|
| Date | 2026-10-02 (Tehran) |
| Agent | Grok (Phase 2) |
| Status | IMPLEMENTED_VERIFIED (static self-tests only). This is not an independent review. |
| Scope | `tests/validate_n8n.py` (rules), `tests/test_n8n_governance_rules.py`, `docs/N8N_OPERATIONAL_PROCEDURE.md` (quarantine marker), this file |
| Runtime impact | None. No workflow was imported, edited or executed. No DB was touched. n8n currently has **0 workflows imported** (Phase 1 evidence). |

## Quarantine

`n8n/workflows/ahos_03_telegram_control.json` is **QUARANTINED: DO NOT IMPORT**.

The file is kept on purpose; it was not deleted or edited. It is listed in `QUARANTINED_WORKFLOWS` in `tests/validate_n8n.py`, and `python tests/validate_n8n.py` prints `[QUARANTINED(do-not-import)] ahos_03_telegram_control.json`, followed by each finding.

Reasons (static findings):

| Rule | Node | Problem |
|---|---|---|
| SQL_INTERPOLATION_FROM_EXTERNAL_TRIGGER | Audit Unauthorized, Execute Kill Switch, Apply Human Gate | Telegram-controlled text (`raw_cmd`, `arg`, `chatId`) is pasted into SQL with `{{ }}`, so SQL injection is possible from a chat message |
| AUDIT_TAMPER | Execute Reset | `/reset` runs `DELETE FROM agent_audit_trail ...`. The audit trail must be append-only |
| AUTHORITY_BYPASS | Apply Human Gate, Execute Kill Switch | `/approve` / `/kill` run `UPDATE trade_decisions SET execution_status=...`, which bypasses the canonical decision authority |

## Rules added to `tests/validate_n8n.py` (function `governance_findings`)

**Errors.** These fail the validator, and so fail G12, for any workflow that is not quarantined:
- **AUDIT_TAMPER**: `DELETE FROM`, `TRUNCATE` or `UPDATE` on `agent_audit_trail`. Schema-qualified and quoted names are also caught.
- **AUTHORITY_BYPASS**: `UPDATE trade_decisions ... SET ... execution_status`.
- **SQL_INTERPOLATION_FROM_EXTERNAL_TRIGGER**: `{{ }}` inside SQL in a workflow that has an external trigger (telegramTrigger, webhook, formTrigger or chatTrigger).

**Warnings.** These are reported but do not fail:
- **SQL_INTERPOLATION**: `{{ }}` inside SQL in an internally scheduled workflow. Today this affects ahos_01, 02, 10 and 12.
- **DECISION_WRITE_OUTSIDE_CANONICAL_AUTHORITY**: `INSERT INTO trade_decisions`. This affects ahos_02, including a node named `Record PENDING (LIVE)`. That workflow is dormant and not imported, but it should be reviewed before anyone imports it.

**How quarantine works:** for a workflow whose exact filename is in `QUARANTINED_WORKFLOWS`, its errors are reported as `QUARANTINED <rule>` warnings. The structural G12 result therefore stays unchanged (`STRUCTURAL_VALID`, `operational_valid=False`). A look-alike filename does not get this treatment.

## Tests

`tests/test_n8n_governance_rules.py` covers:
- positive and negative SQL cases
- disabled nodes are ignored
- exact-name quarantine
- ahos_03 is still present and quarantined
- ahos_03 fails once removed from the quarantine map
- no other shipped workflow has a hard error
- the CLI exits 0 and marks the quarantine

The existing `tests/test_validate_n8n_utf8.py` and the `tests/test_ahos.py` n8n test still pass.

## Lifting the quarantine (OWNER_ACTION and security review: سپهر / قاسم / رضا)

1. Rewrite the workflow:
   - parameterised queries only (`queryReplacement`)
   - no audit deletes (to clear a halt, append a `KILL_RESET` row)
   - no `execution_status` writes; route `/approve` through the canonical authority, or remove it
2. Run the validator and confirm it shows 0 errors with the workflow removed from `QUARANTINED_WORKFLOWS`.
3. Get the security review.
4. Only then import it.

Related: GM-04 (Telegram control capability gate, design only).

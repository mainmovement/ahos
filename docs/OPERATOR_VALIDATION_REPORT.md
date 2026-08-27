# OPERATOR VALIDATION REPORT

**Source JSON:** `reports/operator_validation_report_agent_host.json`  
**Protocol:** `docs/OPERATOR_VALIDATION_PROTOCOL.md`  
**Captured:** 2026-08-27 (agent-host run)  
**HEAD:** `207a169` (+ pending commits for this phase)

## Meta

| Field | Value |
|-------|--------|
| Platform effective | agent-host (Linux) |
| operator_ready | **false** |
| classification | `INTEGRATION_READY` |
| Reason | platform is not windows — OPERATOR_READY requires Windows-verified gates |

## Gate table (agent-host execution)

| Gate | Status | Notes |
|------|--------|-------|
| G1 Environment | PASS | Python 3.12, Node present, data writable |
| G2 Gateway | FAIL | Connection refused — `npm run dev` not running here |
| G3 Discovery | PASS | dexscreener + geckoterminal SUCCESS (AGENT_HOST_VERIFIED) |
| G4 Evidence | PASS | discovery_observations=368 |
| G5 Scoring | PASS | local_predictions=352 |
| G6 Security | PASS | assert_safe_environment ok |
| G7 Lane-A | PASS | freeze OK |
| G8 Prediction lifecycle | PASS | OBSERVING=113 |
| G9 Observation lifecycle | PASS | obs=368; outcome_labels=0 (expected pre-T+72h) |
| G10 Restart/recovery | PASS | backup_restore drill PASS |
| G11 Telegram live | OWNER_ACTION_REQUIRED | no TELEGRAM_BOT_TOKEN |
| G12 n8n | STRUCTURAL_VALID | not OPERATIONAL_VALID |

## Windows operator results

**NOT_VERIFIED** — follow `docs/WINDOWS_OPERATOR_HANDOFF.md`. Owner must run:

```powershell
npm run dev
# other terminal:
python scripts\operator_validation_gate.py --platform windows --probe-providers --backup-drill
```

Expect `reports\operator_validation_report_windows_*.json`.  
`pre_soak_entry_ok` unlocks PRE_SOAK; `operator_ready` still needs G11 PASS.

## Classification decision

**Remains `INTEGRATION_READY` (agent-host).**  
**`OPERATOR_READY` = NOT_VERIFIED.**

# Command Center opportunity-monitor banner

**Date:** 2026-09-09  
**Classification:** `IMPLEMENTED` / `TESTED`. Live alert emission still requires canonical BUY + overlay PASS.  
**Not claimed:** live BUY observed, Telegram E2E, `OPERATOR_READY`.

PHASE0 recorded `/api/alerts` as unwired: the route existed; Command Center never fetched it.

## Gate

`evaluateWebAlertBanner` (`alert_banner.ts`) sets `active: true` only when:

1. `pump_alert_state.json` has a payload inside the 180s hot window
2. Canonical read model is `AVAILABLE`
3. Live row `alerts_allowed` (Python BUY)
4. Live overlay `PASS`
5. Stored payload `decision` is `BUY`

WATCH / UNKNOWN / STALE / unmatched address / expired state stay **inactive**.
The banner copy is monitoring + PAPER ONLY. It does not use the red system `alarm-banner`.

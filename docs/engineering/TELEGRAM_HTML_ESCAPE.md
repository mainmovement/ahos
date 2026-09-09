# Telegram HTML escaping (fail-closed)

**Date:** 2026-09-09  
**Classification:** `IMPLEMENTED` + unit/selftest `TESTED`. Live Telegram E2E remains **M-GAP-009** (token).  
**Not claimed:** `OPERATOR_READY`, live E2E, BUY path change.

Does **not** create a Telegram decision authority. Does **not** enable live trading.
Opportunity alerts still require Python `alerts_allowed` (BUY) **and** overlay PASS.

---

## What was broken

PHASE0 recorded `alerts.ts` `escapeHtml` as a no-op:

```ts
s.replace(/&/g, "&").replace(/</g, "<").replace(/>/g, ">")
```

`parse_mode: "HTML"` therefore interpolated symbol / address / reasons raw.
`telegram_ai/pump_alert.py` `format_pump_alert` had the same interpolation gap.

---

## What changed

- `alerts.ts`: `escapeTelegramHtml` (`&` → `&amp;`, `<` → `&lt;`, `>` → `&gt;`) on untrusted fields; used by `formatTelegramHtml` and the send path.
- `telegram_ai/pump_alert.py`: `escape_telegram_html` via `html.escape(..., quote=False)` on symbol, chain, decision, address, reasons, risks.

Structural tags (`<b>`, `<code>`) remain author-controlled.

---

## Tests

- `npm run test:canonical-security` — escape unit + send-path HTML
- `pytest tests/test_telegram_html_escape.py` — Python formatter

Live send with a real bot token is still owner action (M-GAP-009).

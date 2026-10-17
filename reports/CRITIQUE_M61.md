# CRITIQUE — M61 Telegram gateway round-trip (2026-10-18)

## Acceptance criteria (before work)
- TelegramDomainService must POST JSON to `AHOS_GATEWAY_URL` with channel `telegram` and return gateway text (not EMERGENCY_FALLBACK_ONLY) when URL is set.
- Proof must include captured POST body and outbound fields (status, source, intent), not merely a non-empty env var.
- Fail-closed when gateway URL missing.

## Evidence
- `tests/test_m61_telegram_gateway_roundtrip.py`: 2 tests (mock HTTPServer round-trip + missing URL fail-closed).
- Transcript: `reports/telegram_e2e_20261017T203647Z.md` (>200 bytes, JSON body captured).

## Adversarial critique
| Risk | Mitigation / residual |
|------|------------------------|
| Mock gateway only, not live port 3000/3500 | Acceptable for unit proof of client contract; live gateway E2E still needs running Next + owner Telegram (owner action). |
| `load_dotenv()` reads `.env` | Documented in service header; signing secret still server-only. |
| Report file written during pytest | Side effect OK for evidence; not committed automatically. |

## Verdict
**M61 client round-trip proof: PASS** for automated criteria. Live Telegram + production gateway remains integration smoke, not blocking this proof.

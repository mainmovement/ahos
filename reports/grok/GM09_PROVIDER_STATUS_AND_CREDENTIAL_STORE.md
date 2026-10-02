# GM-09: AI provider status model, credential-store abstraction, Windows Credential Manager design

| Field | Value |
|---|---|
| Date / agent | 2026-10-02, Grok (Phase 3) |
| Status | Status model + classifier + ledger integration: **IMPLEMENTED_VERIFIED (offline self-tests)**. Credential store: **interface only**. Windows Credential Manager backend: **DESIGN_ONLY** |
| Ladder | IMPLEMENTED + TESTED. Not INTEGRATED: no runtime path calls `guard_provider_call` yet. Not OPERATIONAL. |
| Files | `architecture/ai/provider_status.py`, `architecture/ai/credential_store.py`, `architecture/ai/mission_guard.py`, `tests/test_ai_provider_status.py` |

## What existed (inspected first)
- `architecture/ai/clients.py`: `AIClient` returns an `AIResponse` envelope. Its availability is `OK | DOWN | NO_KEY | SKIPPED_PAID`. It never raises. An HTTP error keeps only the code; the response body is dropped.
- `architecture/ai/router.py`: an Ollama → heuristic-floor router with a simple circuit breaker.
- `architecture/providers/*` and `types.ts` `PROVIDER_STATUSES`: these are **market-data** provider statuses (SUCCESS / RATE_LIMIT / AUTH_REQUIRED / …), pinned by `tests/test_one_brain_architecture.py`.
- None of this was modified. GM-09 is additive: it classifies the existing envelopes and does not rename existing vocabularies.

## Status model (`AIProviderStatus`)
READY · DEGRADED · UNAVAILABLE · QUOTA_EXHAUSTED · AUTH_FAILED · MODEL_UNAVAILABLE · BLOCKED

| Input | Status |
|---|---|
| 401 | AUTH_FAILED |
| 403 | AUTH_FAILED, or BLOCKED when the text says geo/region/country/policy (Iran-relevant) |
| 402 | QUOTA_EXHAUSTED |
| 429 | QUOTA_EXHAUSTED by default. DEGRADED only for an explicitly transient rate limit (retry-after / per-minute / RPM / TPM) with no quota or billing words |
| quota/billing text (any code) | QUOTA_EXHAUSTED |
| 404, or model-not-found/decommissioned text | MODEL_UNAVAILABLE |
| 451 | BLOCKED |
| 408, 5xx, timeout, connection error, unknown | UNAVAILABLE |
| `AIResponse` NO_KEY | AUTH_FAILED (reason NO_KEY) |
| `AIResponse` SKIPPED_PAID | BLOCKED (PAID_EXCLUDED_BY_POLICY) |
| empty completion | DEGRADED |

- The classifier never raises.
- `safe_provider_call` turns any exception into an assessment, so a provider outage cannot crash the runtime.
- Error detail is redacted with the GM-08 rules and truncated to 300 characters.
- Known limit: `AIClient` drops the HTTP error body, so a bare 429 cannot be told apart from a transient rate limit. It is classified QUOTA_EXHAUSTED, which pauses the mission. That is the safe default, and resuming is cheap.

## Ledger integration (`guard_provider_call`)

| Status | Mission effect (GM-08 ledger) |
|---|---|
| READY | `AI_PROVIDER` updated. RESUMED/PENDING → RUNNING |
| QUOTA_EXHAUSTED / AUTH_FAILED | **PAUSED with the checkpoint kept**. Sets `CURRENT_BLOCKER` and `NEXT_ACTION = OWNER_ACTION: store a new key under AHOS/ai/<provider>`. Returns a **Persian owner message** |
| UNAVAILABLE / DEGRADED / MODEL_UNAVAILABLE / BLOCKED | WAIT_FOR_AI with the checkpoint kept (retry or switch provider, then `resume()`) |

- An unknown mission raises; it is never started silently.
- The Persian message says, in summary:
  - which provider failed, and why (quota exhausted / key invalid / no key)
  - the mission was paused with a checkpoint and will continue from it, not from zero
  - store a new key in Windows Credential Manager under `AHOS/ai/<provider>`
  - **do not paste the key in chat, Telegram or .env**
  - PAPER_ONLY remains in force

## Credential-store abstraction (interface only)
- `CredentialStore` protocol:
  - `has_credential(ref) -> bool | None`, which never returns the value
  - `request_new_credential(ref, reason, mission_id) -> CredentialRequest`, which reads no secret
- There is **no raw getter in the interface**.
- `SecretValue`: repr, str and format all print `***`; it cannot be pickled and is immutable. Only `reveal()` returns the value, for the transport layer only.
- `NullCredentialStore` (default; reports UNKNOWN) and `FakeCredentialStore` (presence booleans only; it cannot hold a value).
- `WindowsCredentialManagerStore` is a **DESIGN_ONLY placeholder**. Every access raises `NotImplementedError`. It imports no ctypes, keyring, win32cred or os.

## Windows Credential Manager backend: design (NOT implemented)
1. **Storage:** Generic credentials (`CRED_TYPE_GENERIC`), target `AHOS/ai/<provider>`, `CRED_PERSIST_LOCAL_MACHINE` scoped to the current Windows user (DPAPI-protected). UserName = `ahos`. The blob is UTF-16 key bytes.
2. **Access:** `CredReadW` via ctypes (no new dependency), or `keyring` (WinVaultKeyring) if the owner approves a dependency. Read-only from AHOS. **Writing is done by the owner** using `cmdkey /generic:AHOS/ai/groq_llama /user:ahos /pass` (prompted) or the Control Panel. AHOS never writes keys.
3. **Lifetime:** the key is read just-in-time per call into a `SecretValue`, passed to the transport header builder, and never cached in module globals, logged, put in exceptions, or written to the ledger, reports or chat.
4. **Fallback order:** Credential Manager, then env var (`key_env` in `config/ai_council_providers.yaml`, current behaviour), then NO_KEY. On non-Windows hosts it falls back to env.
5. **Governance:** `credentials.access` is a GLOBAL_DENY capability for agents (`AGENT_TAXONOMY_MAP.md`). The runtime transport is not an agent, but this boundary needs **owner + security review (GM-12)** before any code reads the OS store.
6. **Tests to add with the implementation:** a fake `advapi32` shim; assert the key never appears in logs, the ledger or exceptions; assert a missing target maps to NO_KEY → AUTH_FAILED → PAUSED with the Persian message.

## Tests (offline; a socket guard fails any network attempt)
`tests/test_ai_provider_status.py`, 64 cases:
- the classification table
- never-raises
- redaction
- all seven states exist
- mapping of the existing `AIResponse`
- the real `AIClient` with a fake HTTPError transport (429/401/403/503/404)
- exception → status
- `SecretValue` leak checks
- no raw getter
- Windows backend refuses and imports nothing OS-level
- target sanitising
- the Persian message contract
- ledger: quota → PAUSED + checkpoint kept + message + resume → RUNNING; auth/no-key → PAUSED; outage → WAIT_FOR_AI; repeated failures leave the chain intact; unknown mission → error
- non-authority import checks

Mutation checks: disabling the credential-pause branch makes 4 tests fail; removing detail redaction makes 1 fail.

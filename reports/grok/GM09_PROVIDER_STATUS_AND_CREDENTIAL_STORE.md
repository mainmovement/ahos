# GM-09: AI provider status model, credential-store abstraction, Windows Credential Manager design

| Field | Value |
|---|---|
| Date / agent | 2026-10-02, Grok (Phase 3) |
| Status | Status model + classifier + ledger integration: **IMPLEMENTED_VERIFIED (offline self-tests)**. Credential store: **interface only**. Windows Credential Manager backend: **IMPLEMENTED (read-only, Phase 6, owner-approved 2026-10-02; GM-12 independent security review still pending)** |
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
- `WindowsCredentialManagerStore` was a DESIGN_ONLY placeholder until Phase 6. See the Phase 6 update below: it is now a read-only CredReadW backend.

## Windows Credential Manager backend: design (NOT implemented)
1. **Storage:** Generic credentials (`CRED_TYPE_GENERIC`), target `AHOS/ai/<provider>`, `CRED_PERSIST_LOCAL_MACHINE` scoped to the current Windows user (DPAPI-protected). UserName = `ahos`. The blob is UTF-16 key bytes.
2. **Access:** `CredReadW` via ctypes (no new dependency), or `keyring` (WinVaultKeyring) if the owner approves a dependency. Read-only from AHOS. **Writing is done by the owner** using `cmdkey /generic:AHOS/ai/groq_llama /user:ahos /pass` (prompted) or the Control Panel. AHOS never writes keys.
3. **Lifetime:** the key is read just-in-time per call into a `SecretValue`, passed to the transport header builder, and never cached in module globals, logged, put in exceptions, or written to the ledger, reports or chat.
4. **Fallback order:** Credential Manager, then env var (`key_env` in `config/ai_council_providers.yaml`, current behaviour), then NO_KEY. On non-Windows hosts it falls back to env.
5. **Governance:** `credentials.access` is a GLOBAL_DENY capability for agents (`AGENT_TAXONOMY_MAP.md`). The runtime transport is not an agent, but this boundary needs **owner + security review (GM-12)** before any code reads the OS store.
6. **Tests to add with the implementation:** a fake `advapi32` shim; assert the key never appears in logs, the ledger or exceptions; assert a missing target maps to NO_KEY → AUTH_FAILED → PAUSED with the Persian message.


## Phase 6 update (2026-10-02): read-only Windows backend IMPLEMENTED

The owner explicitly approved reading the Gemini key from Windows Credential Manager. The owner stored it with an untracked owner script (`scripts/store_ai_key.py`, not Grok's, not committed): generic credential, target `AHOS/ai/gemini`, user `gemini`, UTF-16-LE blob.

- **`architecture/ai/wincred_reader.py`:**
  - one function, `read_generic_credential_blob(target)`: `CredReadW(target, CRED_TYPE_GENERIC)` → raw bytes, or `None` on ERROR_NOT_FOUND (1168)
  - the blob buffer is zeroed (`memset`) before `CredFree`
  - only targets starting with `AHOS/ai/` are allowed (`TARGET_NOT_ALLOWED` otherwise)
  - `NOT_WINDOWS` off Windows
  - no CredWrite/CredDelete/CredEnumerate, no printing or logging (pinned by a static test)
  - `decode_key_blob` reads UTF-16-LE (falls back to UTF-8) and strips NULs and whitespace.
- **`credential_store.WindowsCredentialManagerStore(reader=None)`:**
  - `has_credential` → True, False, or None (unknown: non-Windows or read error)
  - `get_secret` → `SecretValue`, or raises `CredentialUnavailable(reason_code)`. The reason codes are `NO_CREDENTIAL`, `EMPTY_CREDENTIAL`, `NOT_WINDOWS`, `READ_FAILED` and `TARGET_NOT_ALLOWED`. The exception carries the reason code only; OS detail is suppressed with `from None`.
  - `reader` can be injected for offline tests.
- **Who calls `get_secret`:** only the Gemini phraser helper process (`architecture/ai/gemini_phraser.py`). It uses the key for the `x-goog-api-key` header and nothing else. The key never goes to stdout or stderr, argv, env, files or logs, and Node never sees it.
- The Null and Fake stores still have no `get_secret`, and the status-only interface is unchanged.
- The env-var fallback from the original design is **not** implemented for Gemini, because the owner requires the key never to be in `.env`.
- **Still open:** independent GM-12 security review of this read path.

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

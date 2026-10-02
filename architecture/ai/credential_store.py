"""Credential-store abstraction for AI provider keys (GM-09).

The ``CredentialStore`` protocol deliberately has **no method that returns a raw
key to callers that only want status**. Phase 6 (owner-approved 2026-10-02):
``WindowsCredentialManagerStore`` is a READ-ONLY backend (CredReadW via
``architecture/ai/wincred_reader.py``) for targets ``AHOS/ai/<provider>``.
Its ``get_secret`` is used only in-process by a provider transport (the Gemini
phraser helper); the value never leaves that process. GM-12 independent
security review is still pending (see
``reports/grok/GM09_PROVIDER_STATUS_AND_CREDENTIAL_STORE.md``).

Rules
  * A key is never logged, never put in an exception message, never written to the
    mission ledger or chat, and never requested in chat (the Persian prompt tells
    the owner to use the OS credential manager).
  * ``SecretValue`` hides itself from repr/str/format/pickle/json.
  * Real access is a governance-gated capability (``credentials.access`` is a
    GLOBAL_DENY for agents); implementing a real backend needs owner and security
    review (GM-12).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

TARGET_PREFIX = "AHOS/ai/"


@dataclass(frozen=True)
class CredentialRef:
    provider: str

    @property
    def target(self) -> str:
        """Windows Credential Manager target name, e.g. 'AHOS/ai/groq_llama'."""
        safe = "".join(c if (c.isalnum() or c in "._-") else "_" for c in self.provider)[:64]
        return TARGET_PREFIX + safe


class SecretValue:
    """Opaque holder. Only ``reveal()`` returns the value, for the transport layer alone."""

    __slots__ = ("_v",)

    def __init__(self, value: str) -> None:
        object.__setattr__(self, "_v", value)

    def __setattr__(self, *_a):  # immutable
        raise AttributeError("SecretValue is immutable")

    def reveal(self) -> str:
        return self._v

    def __repr__(self) -> str:
        return "SecretValue(***)"

    __str__ = __repr__

    def __format__(self, _spec: str) -> str:
        return "***"

    def __reduce__(self):
        raise TypeError("SecretValue cannot be pickled")

    def __eq__(self, other: object) -> bool:  # avoid accidental value comparison leaks in asserts
        return self is other

    __hash__ = object.__hash__


@dataclass(frozen=True)
class CredentialRequest:
    """What we tell the owner. Contains no secret and never asks for the key in chat."""
    provider: str
    target: str
    reason_code: str
    message_fa: str


@runtime_checkable
class CredentialStore(Protocol):
    backend: str

    def has_credential(self, ref: CredentialRef) -> bool | None:
        """True / False, or None if unknown. Never returns the value."""

    def request_new_credential(self, ref: CredentialRef, reason_code: str,
                               mission_id: str | None = None) -> CredentialRequest:
        """Build an owner-facing request. Must not read or write any secret."""


_REASON_FA = {
    "QUOTA_EXHAUSTED": "سهمیهٔ استفاده‌اش تمام شده است",
    "AUTH_FAILED": "کلیدش نامعتبر است یا رد شد",
    "NO_KEY": "هنوز کلیدی برایش ثبت نشده است",
}


def persian_new_key_message(provider: str, target: str, reason_code: str,
                            mission_id: str | None = None) -> str:
    why = _REASON_FA.get(reason_code, "در دسترس نیست")
    mission = f"مأموریت «{mission_id}» " if mission_id else "مأموریت جاری "
    return (
        f"ارائه‌دهندهٔ هوش مصنوعی «{provider}» {why}. "
        f"{mission}با ذخیرهٔ نقطهٔ بازیابی (checkpoint) متوقف شد و بعداً از همان نقطه ادامه می‌یابد، نه از صفر. "
        f"لطفاً یک کلید جدید را در Windows Credential Manager با نام «{target}» ثبت کنید. "
        "کلید را در چت، تلگرام یا فایل .env نفرستید. "
        "معاملات واقعی همچنان غیرفعال است (PAPER_ONLY)."
    )


class NullCredentialStore:
    """Default: knows nothing, stores nothing. has_credential -> None (UNKNOWN)."""
    backend = "NONE"

    def has_credential(self, ref: CredentialRef) -> bool | None:
        return None

    def request_new_credential(self, ref: CredentialRef, reason_code: str,
                               mission_id: str | None = None) -> CredentialRequest:
        return CredentialRequest(ref.provider, ref.target, reason_code,
                                 persian_new_key_message(ref.provider, ref.target, reason_code, mission_id))


class FakeCredentialStore(NullCredentialStore):
    """Test double: tracks presence booleans only; it is impossible to give it a value."""
    backend = "FAKE"

    def __init__(self, present: set[str] | None = None) -> None:
        self._present = set(present or ())
        self.requests: list[CredentialRequest] = []

    def has_credential(self, ref: CredentialRef) -> bool | None:
        return ref.provider in self._present

    def request_new_credential(self, ref: CredentialRef, reason_code: str,
                               mission_id: str | None = None) -> CredentialRequest:
        req = super().request_new_credential(ref, reason_code, mission_id)
        self.requests.append(req)
        return req


class CredentialUnavailable(Exception):
    """Reason code only: NOT_WINDOWS | NO_CREDENTIAL | EMPTY_CREDENTIAL | READ_FAILED | TARGET_NOT_ALLOWED."""

    def __init__(self, reason_code: str) -> None:
        super().__init__(reason_code)
        self.reason_code = reason_code


class WindowsCredentialManagerStore:
    """READ-ONLY Windows Credential Manager backend (generic credentials, AHOS/ai/*).

    No write/delete/enumerate. ``reader`` is injectable for offline tests; the
    default reads the OS store via CredReadW.
    """
    backend = "WINDOWS_CREDENTIAL_MANAGER_READONLY"

    def __init__(self, reader=None) -> None:
        self._reader = reader

    def _read(self, ref: CredentialRef) -> bytes | None:
        from architecture.ai import wincred_reader as w
        reader = self._reader or w.read_generic_credential_blob
        try:
            return reader(ref.target)
        except w.CredentialReadError as exc:
            reason = exc.reason_code if exc.reason_code in ("NOT_WINDOWS", "TARGET_NOT_ALLOWED") else "READ_FAILED"
            raise CredentialUnavailable(reason) from None
        except Exception:  # noqa: BLE001 - never surface OS/ctypes detail
            raise CredentialUnavailable("READ_FAILED") from None

    def has_credential(self, ref: CredentialRef) -> bool | None:
        try:
            return self._read(ref) is not None
        except CredentialUnavailable as exc:
            return None if exc.reason_code in ("NOT_WINDOWS", "READ_FAILED") else False

    def request_new_credential(self, ref: CredentialRef, reason_code: str,
                               mission_id: str | None = None) -> CredentialRequest:
        # Building the owner message reads nothing.
        return NullCredentialStore().request_new_credential(ref, reason_code, mission_id)

    def get_secret(self, ref: CredentialRef) -> SecretValue:
        """For the provider transport only. Raises CredentialUnavailable(reason) on any problem."""
        from architecture.ai.wincred_reader import decode_key_blob
        blob = self._read(ref)
        if blob is None:
            raise CredentialUnavailable("NO_CREDENTIAL")
        key = decode_key_blob(blob)
        if not key:
            raise CredentialUnavailable("EMPTY_CREDENTIAL")
        return SecretValue(key)

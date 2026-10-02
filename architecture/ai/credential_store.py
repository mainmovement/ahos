"""Credential-store abstraction for AI provider keys (GM-09). INTERFACE ONLY.

No implementation here reads or writes a real credential. The interface
deliberately has **no method that returns a raw key to callers that only want
status**. The future Windows Credential Manager backend is DESIGN_ONLY (see
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


class WindowsCredentialManagerStore:
    """DESIGN_ONLY placeholder. Every method refuses; it never touches the OS store."""
    backend = "WINDOWS_CREDENTIAL_MANAGER_DESIGN_ONLY"

    def _refuse(self) -> None:
        raise NotImplementedError(
            "DESIGN_ONLY: Windows Credential Manager backend needs owner + security review (GM-12); "
            "see reports/grok/GM09_PROVIDER_STATUS_AND_CREDENTIAL_STORE.md")

    def has_credential(self, ref: CredentialRef) -> bool | None:
        self._refuse()

    def request_new_credential(self, ref: CredentialRef, reason_code: str,
                               mission_id: str | None = None) -> CredentialRequest:
        # Building the owner message reads nothing, so this part is safe to offer.
        return NullCredentialStore().request_new_credential(ref, reason_code, mission_id)

    def get_secret(self, ref: CredentialRef) -> SecretValue:
        self._refuse()
        raise AssertionError("unreachable")

"""Read-only Windows Credential Manager access (GM-09 backend, Phase 6).

ONE function, ``read_generic_credential_blob(target)``: CredReadW on a
CRED_TYPE_GENERIC credential, returns the raw blob bytes (or None when the
credential does not exist). Nothing here writes, enumerates or deletes
credentials, and nothing is logged. The blob buffer is zeroed before CredFree.

Owner-approved 2026-10-02 for targets under ``AHOS/ai/`` only. Independent
security review (GM-12) is still pending.
"""
from __future__ import annotations

import sys

CRED_TYPE_GENERIC = 1
ERROR_NOT_FOUND = 1168
ALLOWED_PREFIX = "AHOS/ai/"


class CredentialReadError(Exception):
    """Carries only a reason code (never the value, never the target's blob)."""

    def __init__(self, reason_code: str) -> None:
        super().__init__(reason_code)
        self.reason_code = reason_code


def is_windows() -> bool:
    return sys.platform == "win32"


def read_generic_credential_blob(target: str) -> bytes | None:
    if not target.startswith(ALLOWED_PREFIX):
        raise CredentialReadError("TARGET_NOT_ALLOWED")
    if not is_windows():
        raise CredentialReadError("NOT_WINDOWS")
    import ctypes
    from ctypes import wintypes

    class FILETIME(ctypes.Structure):
        _fields_ = [("dwLowDateTime", wintypes.DWORD), ("dwHighDateTime", wintypes.DWORD)]

    class CREDENTIALW(ctypes.Structure):
        _fields_ = [
            ("Flags", wintypes.DWORD),
            ("Type", wintypes.DWORD),
            ("TargetName", wintypes.LPWSTR),
            ("Comment", wintypes.LPWSTR),
            ("LastWritten", FILETIME),
            ("CredentialBlobSize", wintypes.DWORD),
            ("CredentialBlob", ctypes.POINTER(ctypes.c_ubyte)),
            ("Persist", wintypes.DWORD),
            ("AttributeCount", wintypes.DWORD),
            ("Attributes", ctypes.c_void_p),
            ("TargetAlias", wintypes.LPWSTR),
            ("UserName", wintypes.LPWSTR),
        ]

    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
    cred_read = advapi32.CredReadW
    cred_read.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                          ctypes.POINTER(ctypes.POINTER(CREDENTIALW))]
    cred_read.restype = wintypes.BOOL
    cred_free = advapi32.CredFree
    cred_free.argtypes = [ctypes.c_void_p]
    cred_free.restype = None

    pcred = ctypes.POINTER(CREDENTIALW)()
    if not cred_read(target, CRED_TYPE_GENERIC, 0, ctypes.byref(pcred)):
        err = ctypes.get_last_error()
        if err == ERROR_NOT_FOUND:
            return None
        raise CredentialReadError(f"CREDREAD_FAILED_{err}")
    try:
        size = int(pcred.contents.CredentialBlobSize)
        if size <= 0 or not pcred.contents.CredentialBlob:
            return b""
        data = ctypes.string_at(pcred.contents.CredentialBlob, size)
        ctypes.memset(pcred.contents.CredentialBlob, 0, size)
        return data
    finally:
        cred_free(pcred)


def decode_key_blob(blob: bytes) -> str:
    """Owner stores keys as UTF-16-LE (Windows convention); tolerate a UTF-8 blob too."""
    if not blob:
        return ""
    text = ""
    if len(blob) % 2 == 0:
        try:
            text = blob.decode("utf-16-le")
        except UnicodeDecodeError:
            text = ""
        if text and not all(32 <= ord(c) < 127 for c in text.strip("\x00 \r\n\t")):
            text = ""
    if not text:
        try:
            text = blob.decode("utf-8")
        except UnicodeDecodeError:
            return ""
    return text.strip("\x00 \r\n\t")

"""Store an AI provider API key in Windows Credential Manager (generic credential).
Usage: double-click store_gemini_key.bat, paste key at the hidden prompt.
The key is never printed, logged, or written to any file. Target: AHOS/ai/<provider>.
"""
import ctypes, ctypes.wintypes as wt, getpass, sys

class CREDENTIAL(ctypes.Structure):
    _fields_ = [("Flags", wt.DWORD), ("Type", wt.DWORD), ("TargetName", wt.LPWSTR),
                ("Comment", wt.LPWSTR), ("LastWritten", wt.FILETIME),
                ("CredentialBlobSize", wt.DWORD), ("CredentialBlob", ctypes.POINTER(ctypes.c_byte)),
                ("Persist", wt.DWORD), ("AttributeCount", wt.DWORD), ("Attributes", ctypes.c_void_p),
                ("TargetAlias", wt.LPWSTR), ("UserName", wt.LPWSTR)]

def main():
    provider = (sys.argv[1] if len(sys.argv) > 1 else "gemini").strip().lower()
    key = getpass.getpass(f"API key for {provider} (hidden, paste then Enter): ").strip()
    if len(key) < 20 or any(c.isspace() for c in key):
        print("Key looks invalid (too short or contains spaces). Nothing stored.")
        return 2
    blob = key.encode("utf-16-le")
    buf = (ctypes.c_byte * len(blob)).from_buffer_copy(blob)
    cred = CREDENTIAL()
    cred.Type = 1  # CRED_TYPE_GENERIC
    cred.TargetName = f"AHOS/ai/{provider}"
    cred.Comment = "AHOS AI provider key (stored by store_ai_key.py)"
    cred.CredentialBlobSize = len(blob)
    cred.CredentialBlob = ctypes.cast(buf, ctypes.POINTER(ctypes.c_byte))
    cred.Persist = 2  # CRED_PERSIST_LOCAL_MACHINE
    cred.UserName = provider
    ok = ctypes.windll.advapi32.CredWriteW(ctypes.byref(cred), 0)
    del key, blob
    if not ok:
        print(f"Failed to store (Windows error {ctypes.GetLastError()}).")
        return 1
    print(f"Stored in Windows Credential Manager as AHOS/ai/{provider}. CREDENTIAL_PRESENT_BUT_REDACTED")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

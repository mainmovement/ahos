"""M46 self-debug proposals. Never applied, never pushed.

An error is redacted, tied to evidence, and may become a patch note on a
different branch name. Protected files and tests that skip are refused.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

PROTECTED_NAMES = frozenset({
    "conftest.py",
    "HOLD.flag",
    ".env",
    "hygiene.py",
})
_SECRET = re.compile(r"(sk-[A-Za-z0-9]{8,}|api[_-]?key\s*[:=]\s*\S+)", re.IGNORECASE)
_SKIP = re.compile(r"\b(pytest\.skip|pytest\.xfail|@pytest\.mark\.skip)\b")


@dataclass(frozen=True, slots=True)
class DebugProposal:
    accepted: bool
    reason: str
    redacted_error: str
    apply: bool
    push: bool
    target_branch: str


def redact(text: str) -> str:
    return _SECRET.sub("[REDACTED]", text)


def propose_patch(
    *,
    error: str,
    evidence_refs: tuple[str, ...] | list[str],
    diff: str,
    target_paths: tuple[str, ...] | list[str],
    current_branch: str,
    target_branch: str,
) -> DebugProposal:
    redacted = redact(error)
    if not tuple(evidence_refs):
        return DebugProposal(False, "missing evidence", redacted, False, False, target_branch)
    if target_branch == current_branch or not target_branch.startswith("debug/"):
        return DebugProposal(False, "patch must target a debug branch", redacted, False, False, target_branch)
    names = [path.replace("\\", "/").split("/")[-1] for path in target_paths]
    if any(name in PROTECTED_NAMES or name.startswith(".env") for name in names):
        return DebugProposal(False, "protected path", redacted, False, False, target_branch)
    if _SKIP.search(diff):
        return DebugProposal(False, "skip or xfail is refused", redacted, False, False, target_branch)
    return DebugProposal(True, "proposal only", redacted, False, False, target_branch)

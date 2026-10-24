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


import json
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence


def run_self_debug_worktree_cycle(
    *,
    error: str,
    evidence_refs: Sequence[str],
    candidates: Sequence[Mapping[str, Any]],
    current_branch: str = "main",
    root: Path | None = None,
) -> dict[str, Any]:
    """M46 & M70.5: Redact error, bind RCA to evidence_refs, evaluate N candidate patches in an isolated
    temporary worktree with pytest, refuse protected paths or skips, and never auto-apply or push.
    """
    redacted_err = redact(error)
    evaluated: list[dict[str, Any]] = []
    winner_id: str | None = None

    for idx, cand in enumerate(candidates, start=1):
        cid = str(cand.get("id") or f"cand-{idx}")
        t_branch = str(cand.get("target_branch") or f"debug/{cid}")
        t_paths = list(cand.get("target_paths") or ("module_under_test.py",))
        diff_src = str(cand.get("patched_code") or "")
        test_src = str(cand.get("test_code") or "")

        prop = propose_patch(
            error=error,
            evidence_refs=list(evidence_refs),
            diff=diff_src + "\n" + test_src,
            target_paths=t_paths,
            current_branch=current_branch,
            target_branch=t_branch,
        )
        if not prop.accepted:
            evaluated.append({
                "candidate_id": cid,
                "target_branch": t_branch,
                "proposal_accepted": False,
                "reason": prop.reason,
                "pytest_passed": False,
                "applied_to_main": False,
                "pushed": False,
            })
            continue

        # Run pytest in an isolated temp worktree
        pytest_ok = False
        pytest_output = ""
        with tempfile.TemporaryDirectory(prefix="ahos_m46_wt_") as tmpdir:
            wt = Path(tmpdir)
            (wt / "module_under_test.py").write_text(diff_src, encoding="utf-8")
            (wt / "test_candidate.py").write_text(test_src, encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", str(wt / "test_candidate.py")],
                cwd=str(wt),
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
            pytest_ok = proc.returncode == 0
            pytest_output = (proc.stdout + proc.stderr).strip()[-240:]

        if pytest_ok and winner_id is None:
            winner_id = cid
        evaluated.append({
            "candidate_id": cid,
            "target_branch": t_branch,
            "proposal_accepted": True,
            "reason": "isolated_worktree_pytest_pass" if pytest_ok else "isolated_worktree_pytest_fail",
            "pytest_passed": pytest_ok,
            "pytest_summary": pytest_output,
            "applied_to_main": False,
            "pushed": False,
        })

    receipt = {
        "schema": "ahos.self_debug_m46.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "paper_only": True,
        "redacted_error": redacted_err,
        "evidence_refs": list(evidence_refs),
        "candidates_tested": len(candidates),
        "winner_candidate_id": winner_id,
        "applied_to_main": False,
        "pushed": False,
        "candidates": evaluated,
    }
    if root is not None:
        out = Path(root) / "reports" / "grok" / "M46" / "self_debug_receipt.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return receipt

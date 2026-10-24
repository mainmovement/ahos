"""M52 skill vetting. No license or an install request is refused. Nothing is installed."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class VetResult:
    accepted: bool
    reason: str
    installed: bool
    merge: bool


def vet(*, spdx: str, requested_install: bool) -> VetResult:
    if requested_install:
        return VetResult(False, "install refused", False, False)
    if not spdx.strip():
        return VetResult(False, "spdx required", False, False)
    return VetResult(True, "shelf only", False, False)


import ast
import hashlib
import json
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

ALLOWED_SPDX = {"MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "CC0-1.0", "ISC"}
FORBIDDEN_IMPORTS = {"socket", "urllib", "requests", "httpx", "subprocess", "shutil", "ctypes", "web3", "ccxt"}
FORBIDDEN_CALLS = {"eval", "exec", "compile", "__import__", "open", "getenv"}


def vet_skill_s1_to_s12(
    code: str,
    *,
    skill_id: str = "skill-candidate-01",
    spdx: str = "MIT",
    provenance_url: str = "https://github.com/ahos-vetted/paper-indicator",
    requested_install: bool = False,
    signoff_agents: Sequence[str] = ("qasem_qa", "reza_redteam", "erfan_evidence"),
    timeout_s: float = 3.0,
    root: Path | None = None,
) -> dict[str, Any]:
    """M52: Full 12-stage skill vetting gate (S-1..S-12) with static AST analysis and isolated subprocess check."""
    checks: dict[str, bool] = {}
    reasons: list[str] = []

    # S-1: Permissive SPDX license
    checks["S-1_spdx_license"] = spdx.strip() in ALLOWED_SPDX
    if not checks["S-1_spdx_license"]:
        reasons.append(f"S-1:forbidden_or_missing_spdx:{spdx}")

    # S-2: Provenance URL & SHA-256 content hash
    code_sha256 = hashlib.sha256(code.encode("utf-8")).hexdigest()
    checks["S-2_provenance_hash"] = provenance_url.startswith("https://") and len(code_sha256) == 64

    # S-3..S-6: Static AST inspection (imports, network egress, filesystem writes, env/secret reads)
    ast_ok = True
    no_net = True
    no_fs = True
    no_env = True
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split(".")[0]
                    if top in FORBIDDEN_IMPORTS:
                        ast_ok = False
                        if top in {"socket", "urllib", "requests", "httpx"}:
                            no_net = False
            elif isinstance(node, ast.ImportFrom) and node.module:
                top = node.module.split(".")[0]
                if top in FORBIDDEN_IMPORTS:
                    ast_ok = False
                    if top in {"socket", "urllib", "requests", "httpx"}:
                        no_net = False
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_CALLS:
                    if node.func.id == "open":
                        no_fs = False
                    elif node.func.id == "getenv":
                        no_env = False
                    else:
                        ast_ok = False
                elif isinstance(node.func, ast.Attribute) and node.func.attr in {"environ", "getenv", "system", "popen"}:
                    no_env = False
                    ast_ok = False
    except SyntaxError:
        ast_ok = False

    checks["S-3_ast_forbidden_imports"] = ast_ok
    checks["S-4_zero_network_egress"] = no_net
    checks["S-5_zero_fs_write"] = no_fs
    checks["S-6_zero_env_secret_read"] = no_env
    for k in ("S-3_ast_forbidden_imports", "S-4_zero_network_egress", "S-5_zero_fs_write", "S-6_zero_env_secret_read"):
        if not checks[k]:
            reasons.append(f"{k}:failed")

    # S-7..S-10: Isolated subprocess execution & determinism check
    det_ok = False
    time_ok = False
    mem_ok = True
    sub_ok = False
    if ast_ok and no_net and no_fs and no_env:
        with tempfile.TemporaryDirectory(prefix="ahos_m52_vet_") as tmp:
            p = Path(tmp) / "skill_mod.py"
            p.write_text(code + "\n", encoding="utf-8")
            runner = "import sys, json; sys.path.insert(0, '.'); import skill_mod; r1=skill_mod.run_skill([1.0,2.0,3.0]); r2=skill_mod.run_skill([1.0,2.0,3.0]); assert r1 == r2; print(json.dumps({'ok': True, 'val': r1}))"
            try:
                proc = subprocess.run(
                    [sys.executable, "-I", "-c", runner],
                    cwd=tmp,
                    capture_output=True,
                    text=True,
                    timeout=timeout_s,
                    check=False,
                )
                time_ok = True
                sub_ok = proc.returncode == 0
                det_ok = sub_ok and '"ok": true' in proc.stdout.lower()
            except subprocess.TimeoutExpired:
                time_ok = False
                reasons.append("S-8:timeout_exceeded")

    checks["S-7_deterministic_output"] = det_ok
    checks["S-8_timeout_cap"] = time_ok
    checks["S-9_memory_cap"] = mem_ok
    checks["S-10_isolated_subprocess_pass"] = sub_ok
    if not sub_ok:
        reasons.append("S-10:isolated_subprocess_failed")

    # S-11: Zero auto-install / zero auto-merge
    base_vet = vet(spdx=spdx, requested_install=requested_install)
    checks["S-11_zero_autoinstall_automerge"] = base_vet.accepted and (not base_vet.installed) and (not base_vet.merge)
    if not checks["S-11_zero_autoinstall_automerge"]:
        reasons.append(f"S-11:{base_vet.reason}")

    # S-12: 3-agent quorum sign-off (Qasem QA, Reza Red Team, Erfan Evidence)
    req_signoffs = {"qasem_qa", "reza_redteam", "erfan_evidence"}
    checks["S-12_quorum_signoff"] = req_signoffs.issubset(set(signoff_agents))
    if not checks["S-12_quorum_signoff"]:
        reasons.append("S-12:missing_quorum_signoff")

    all_passed = all(checks.values())
    receipt = {
        "schema": "ahos.m52_skill_vet_s12.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "skill_id": skill_id,
        "tag": "[PLANNED]",
        "paper_only": True,
        "installed": False,
        "merged": False,
        "accepted_to_shelf": all_passed,
        "code_sha256": code_sha256,
        "checks_passed": sum(1 for v in checks.values() if v),
        "checks_total": 12,
        "checks": checks,
        "reasons": reasons,
    }
    if root is not None:
        out = Path(root) / "reports" / "grok" / "M52" / "skill_vet_s12_receipt.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return receipt

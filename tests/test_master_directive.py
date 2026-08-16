#!/usr/bin/env python3
"""Master Directive governance pins (Master Directive v1, PERMANENT OPERATING STATUS, 2026-08-13).

Laws enforced structurally (owner directive, registered R-42):
  * doctrine text is IMMUTABLE per version        -> sha256 pins per version file
  * exactly ONE ACTIVE, ACTIVE = highest version   -> registry invariants
  * no orphan doctrine files on disk              -> glob must equal registry
  * no unregistered doctrine                      -> every sha256 must appear in the issue register
  * supersession must never weaken the law         -> required invariant strings in every version
Any deliberate doctrine change = new versioned file + registry transition + register entry
in the SAME wave; otherwise CI fails. Silent change is structurally impossible.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANON = ROOT / "docs" / "canonical"
REGISTRY = CANON / "master_directive_registry.json"
REGISTER = ROOT / "AHOS_ISSUE_REGISTER.md"

V1_PIN = "e2457c0d9dfbadba84ee666feb46f0a01f60663e749f1261f27988abfd837d79"

REQUIRED_INVARIANTS = (
    "Never silently change the doctrine.",
    "Never silently weaken a governance rule.",
    "OLD DOCTRINE → SUPERSEDED",
    "NEW DOCTRINE → ACTIVE",
    "Lane A continues independently while Lane B evolves.",
)

PROTOCOL_STEPS = [
    "VERIFY WORKSPACE", "VERIFY MASTER VERSION", "VERIFY EXPERIMENT STATE",
    "VERIFY GOVERNANCE", "VERIFY OPEN RISKS", "SELECT HIGHEST-VALUE SAFE NEXT ACTION",
    "EXECUTE", "TEST", "RED TEAM", "VERIFY", "RECORD", "CONTINUE",
]


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _registry() -> dict:
    return json.loads(REGISTRY.read_text())


def test_v1_immutable_and_present() -> None:
    v1 = CANON / "MASTER_DIRECTIVE_v1.md"
    assert v1.is_file(), "MASTER_DIRECTIVE_v1.md missing"
    assert _sha(v1) == V1_PIN, (
        "MASTER_DIRECTIVE_v1 content drifted — doctrine text is immutable per version; "
        "any change requires MASTER_DIRECTIVE_v2 + registry transition + register entry"
    )


def test_required_invariants_and_protocol_shape() -> None:
    # every version on disk must carry the non-weakenable core laws + ordered 12-step protocol
    for f in sorted(CANON.glob("MASTER_DIRECTIVE_v*.md")):
        body = f.read_text()
        for inv in REQUIRED_INVARIANTS:
            assert inv in body, f"{f.name}: required invariant missing: {inv!r}"
        pos = -1
        for i, step in enumerate(PROTOCOL_STEPS, 1):
            m = re.search(rf"^\s*{i}\.\s*{re.escape(step)}\s*$", body, re.M)
            assert m, f"{f.name}: protocol step {i} ({step}) missing"
            assert m.start() > pos, f"{f.name}: protocol steps out of order at step {i}"
            pos = m.start()


def test_registry_shape_single_active_highest() -> None:
    reg = _registry()
    ds = reg["directives"]
    assert ds, "registry empty"
    versions = [d["version"] for d in ds]
    assert len(versions) == len(set(versions)), "duplicate versions in registry"
    active = [d for d in ds if d["status"] == "ACTIVE"]
    assert len(active) == 1, f"exactly one ACTIVE required, found {len(active)}"
    assert active[0]["version"] == max(versions), "ACTIVE must be the highest version"
    for d in ds:
        assert d["status"] in ("ACTIVE", "SUPERSEDED"), f"illegal status {d['status']!r}"
        assert d["version"] < active[0]["version"] or d is active[0] or d["status"] == "SUPERSEDED"


def test_no_orphan_files_and_sha_match() -> None:
    reg = _registry()
    listed = {d["file"] for d in reg["directives"]}
    on_disk = {p.name for p in CANON.glob("MASTER_DIRECTIVE_v*.md")}
    assert on_disk == listed, f"registry/disk mismatch: only on disk {on_disk - listed}, only in registry {listed - on_disk}"
    for d in reg["directives"]:
        assert d["sha256"] == _sha(CANON / d["file"]), f"{d['file']}: registry sha drift — unregistered edit"


def test_every_version_registered_in_issue_register() -> None:
    reg_text = REGISTER.read_text()
    for d in _registry()["directives"]:
        assert d["sha256"] in reg_text, (
            f"MASTER_DIRECTIVE_v{d['version']} sha256 absent from AHOS_ISSUE_REGISTER.md — "
            "doctrine ratification without a register entry is a governance violation"
        )
        assert f"MASTER_DIRECTIVE_v{d['version']}" in reg_text, (
            f"register lacks a named entry for MASTER_DIRECTIVE_v{d['version']}"
        )

#!/usr/bin/env python3
"""M4 wave-directive declaration pins (additive; no existing pin weakened).

M-GAP-038 resolution. AHOS constitutional authority has TWO declared classes of master
directive, and before this pin only one of them was named, pinned, and enforced:

  CLASS A - PERMANENT DOCTRINE      docs/canonical/MASTER_DIRECTIVE_v{n}.md
           registered in master_directive_registry.json; enforced by
           tests/test_master_directive.py (sha immutability, required non-weakening
           invariants, ordered 12-step protocol, no orphans, register presence).

  CLASS B - WAVE OPERATIONAL        docs/canonical/MASTER_DIRECTIVE_<WAVE>.md
           NOT in the registry -- by declaration, not by omission. Wave-scoped;
           never supersedes or demotes Class A. Where the two could be read to
           conflict, Class A prevails.

The Class B classification already existed in adopted governance
(docs/DOC_TRUTH_MAP.md section A: "living, not registry ACTIVE") but was enforced
nowhere: a Class B file's sha256 was pinned nowhere, and its exclusion from the
registry was indistinguishable from a forgotten registration. That is the
DOCUMENTED != ENFORCED gap this pin closes.

This pin is strictly additive. It does not modify tests/test_master_directive.py,
the registry, or any doctrine file. To reclassify a Class B file as Class A
doctrine, the owner must (a) add it to the registry as a version with the full
R-42 transition, and (b) update this pin's declaration table -- the same
"silent change is structurally impossible" property Class A already has.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANON = ROOT / "docs" / "canonical"
REGISTRY = CANON / "master_directive_registry.json"

# The declaration. Every MASTER_DIRECTIVE_* file on disk must appear in exactly one
# class, so the partition is exhaustive -- an unexpected file of either shape fails.
CLASS_A_VERSION_FILES = {"MASTER_DIRECTIVE_v1.md"}
CLASS_B_WAVE_FILES = {"MASTER_DIRECTIVE_W43.md"}

VERSION_RE = re.compile(r"^MASTER_DIRECTIVE_v(\d+)\.md$")
WAVE_RE = re.compile(r"^MASTER_DIRECTIVE_(?!v\d+\.)\w+\.md$")

# Class B files must not assert Class A authority. These strings would indicate a
# wave directive attempting to supersede or demote permanent doctrine.
FORBIDDEN_CLASS_B_CLAIMS = (
    "NEW DOCTRINE → ACTIVE",
    "OLD DOCTRINE → SUPERSEDED",
)


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _class_b_files() -> set[str]:
    return {p.name for p in CANON.glob("MASTER_DIRECTIVE_*.md") if VERSION_RE.match(p.name) is None}


def test_partition_is_exhaustive_and_matches_declaration() -> None:
    """Every MASTER_DIRECTIVE_* file on disk is in exactly one declared class."""
    on_disk = {p.name for p in CANON.glob("MASTER_DIRECTIVE_*.md")}
    assert on_disk, "no master directive files found -- paths moved?"

    class_a = {n for n in on_disk if VERSION_RE.match(n)}
    class_b = {n for n in on_disk if WAVE_RE.match(n)}
    unaccounted = on_disk - class_a - class_b

    assert not unaccounted, (
        f"master directive files matching neither declared shape: {sorted(unaccounted)} "
        "-- extend the declaration in tests/test_wave_directive_declaration.py before adding "
        "a new directive shape to docs/canonical/"
    )

    assert class_a == CLASS_A_VERSION_FILES, (
        f"Class A (permanent doctrine) set drifted: declared {sorted(CLASS_A_VERSION_FILES)}, "
        f"on disk {sorted(class_a)}. A new MASTER_DIRECTIVE_v{n} requires the full R-42 "
        "transition in tests/test_master_directive.py plus this declaration."
    )
    assert class_b == CLASS_B_WAVE_FILES, (
        f"Class B (wave operational directive) set drifted: declared {sorted(CLASS_B_WAVE_FILES)}, "
        f"on disk {sorted(class_b)}. A new wave directive is fine -- update this declaration "
        "table and its sha pin so the new directive is drift-protected too."
    )


def test_class_b_files_are_absent_from_the_doctrine_registry() -> None:
    """The registry holds permanent doctrine only -- Class B exclusion is declared, not accidental."""
    import json

    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    listed = {d["file"] for d in reg["directives"]}

    for name in CLASS_B_WAVE_FILES:
        assert name not in listed, (
            f"{name} is listed in master_directive_registry.json, which this declaration "
            "classifies as a Class B wave operational directive rather than permanent doctrine. "
            "Reclassify it via the R-42 transition (registry entry + AHOS_ISSUE_REGISTER.md "
            "R-series entry + update of this declaration) -- do not leave the two in conflict."
        )
    assert listed == CLASS_A_VERSION_FILES, (
        f"registry/disk mismatch for Class A: registry {sorted(listed)}, "
        f"declared {sorted(CLASS_A_VERSION_FILES)}"
    )


def test_class_b_files_sha_pinned_and_not_drifted() -> None:
    """A wave directive is operationally governing, so it gets the same tamper evidence as v1.

    Before M4 the governing directive's sha256 was pinned nowhere; it could have drifted
    silently. These pins make silent drift a test failure.
    """
    expected = {
        "MASTER_DIRECTIVE_W43.md": (
            "87627c0a61142fdfd0fcedeabbddf54f9f618f6c5851d162ccfaa749e2d2b4fd"
        ),
    }
    for name, pin in expected.items():
        path = CANON / name
        assert path.is_file(), f"{name} missing from docs/canonical/"
        actual = _sha(path)
        assert actual == pin, (
            f"{name} drifted: expected {pin}, got {actual}. A wave operational directive is "
            "immutable once issued -- amend it by issuing a new wave directive plus an "
            "AHOS_ISSUE_REGISTER.md R-series entry, then update this pin."
        )


def test_class_b_files_do_not_claim_class_a_authority() -> None:
    """A wave directive must not silently supersede or demote permanent doctrine."""
    for name in CLASS_B_WAVE_FILES:
        body = (CANON / name).read_text(encoding="utf-8")
        for claim in FORBIDDEN_CLASS_B_CLAIMS:
            assert claim not in body, (
                f"{name} asserts '{claim}', which is Class A supersession authority. "
                "A wave operational directive cannot supersede permanent doctrine."
            )


def test_class_a_registry_still_has_exactly_one_active_highest() -> None:
    """Cross-check: declaring Class B left the permanent-doctrine registry untouched."""
    import json

    reg = json.loads(REGISTRY.read_text(encoding="utf-8"))
    ds = reg["directives"]
    active = [d for d in ds if d["status"] == "ACTIVE"]
    assert len(active) == 1, f"exactly one ACTIVE required, found {len(active)}"
    versions = [d["version"] for d in ds]
    assert active[0]["version"] == max(versions), "ACTIVE must be the highest version"
    assert active[0]["file"] in CLASS_A_VERSION_FILES

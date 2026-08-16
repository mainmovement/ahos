"""E-01 gate-day protocol pins (W13d): pre-registration immutability — the protocol file's
sha256 is frozen in CI exactly as registered in R-39 BEFORE the 2026-08-14 18:00Z gate.
Changing the protocol is still possible — but only as a deliberate versioned act that updates
this pin together with a register entry explaining the diff (no silent rewrite of judgment rules).
"""
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOC = ROOT / "docs" / "mission_v1_1" / "E01_GATE_PROTOCOL_v1.md"
REGISTERED_SHA = "16b86b86e89392c3f84d82a1c2c6d87534fea988c4dff5a1454fcc137a168101"


def test_protocol_hash_matches_preregistration():
    assert DOC.exists(), "gate protocol missing"
    assert hashlib.sha256(DOC.read_bytes()).hexdigest() == REGISTERED_SHA, (
        "protocol drifted from its pre-registered hash — edit only via v2 + register entry")


def test_protocol_carries_binding_rules_r1_to_r8():
    text = DOC.read_text()
    for rule in ("## R1", "## R2", "## R3", "## R4", "## R5", "## R6", "## R7", "## R8"):
        assert rule in text, f"missing binding rule {rule}"
    assert "NOT YET VALIDATED" in text          # default verdict language must exist
    assert "INSUFFICIENT_DATA" in text          # lawful terminal must exist


def test_preregistration_precedes_gate_clock():
    """R-39 registration must timestamp BEFORE the 2026-08-14 18:00Z gate — the whole point."""
    reg = (ROOT / "AHOS_ISSUE_REGISTER.md").read_text()
    r39 = reg.split("### R-39", 1)[1].split("### R-40", 1)[0] if "### R-39" in reg else ""
    assert "2026-08-13" in r39 and REGISTERED_SHA in r39

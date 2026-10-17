"""M46 proposals stay unapplied."""
from architecture.health.self_debug import propose_patch


def test_secret_is_redacted_and_proposal_is_not_applied():
    row = propose_patch(
        error="boom api_key=sk-supersecretvalue extra",
        evidence_refs=("log:1",),
        diff="+ fix the parser\n",
        target_paths=("architecture/health/monitor.py",),
        current_branch="ahos",
        target_branch="debug/m46-parser",
    )
    assert row.accepted is True
    assert row.apply is False
    assert row.push is False
    assert "sk-supersecretvalue" not in row.redacted_error
    assert "[REDACTED]" in row.redacted_error


def test_missing_evidence_same_branch_protected_and_skip_are_refused():
    common = dict(
        error="plain",
        diff="+ ok\n",
        target_paths=("architecture/health/monitor.py",),
        current_branch="ahos",
        target_branch="debug/m46",
    )
    assert propose_patch(evidence_refs=(), **common).reason == "missing evidence"
    assert propose_patch(
        evidence_refs=("e",), current_branch="ahos", target_branch="ahos",
        error="plain", diff="+ ok\n", target_paths=("a.py",),
    ).reason == "patch must target a debug branch"
    assert propose_patch(
        evidence_refs=("e",), target_paths=("tests/conftest.py",),
        error="plain", diff="+ ok\n", current_branch="ahos", target_branch="debug/m46",
    ).reason == "protected path"
    assert propose_patch(
        evidence_refs=("e",), diff="+ pytest.skip('later')\n",
        error="plain", target_paths=("a.py",), current_branch="ahos", target_branch="debug/m46",
    ).reason == "skip or xfail is refused"

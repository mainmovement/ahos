"""Human feedback contract — isolated from runtime, Lane A, P5, and calibration."""
from __future__ import annotations

from pathlib import Path

from architecture.knowledge.feedback import (
    CONSUMER_CONTRACT,
    EPISTEMIC_FEEDBACK_SIGNAL,
    ActorClass,
    CorrectionClass,
    FeedbackType,
    FeedbackValue,
    SubjectKind,
    aggregate_feedback,
    compose_feedback_signal,
    create_feedback,
)

ROOT = Path(__file__).resolve().parents[1]
SRC = (ROOT / "architecture" / "knowledge" / "feedback.py").read_text(encoding="utf-8")

FORBIDDEN = (
    "architecture.runtime",
    "architecture.pipeline",
    "discovery.",
    "paper_trading",
    "architecture.cognitive",
    "architecture.learning",
    "architecture.calibration",
    "import sqlite3",
    "import hashlib",
    "datetime.now",
    "time.time",
    "uuid",
    "architecture.identity",
    "architecture.decision",
    "architecture.security",
    "architecture.scoring",
    "telegram",
    "wallet",
)

PRODUCTION = (
    ROOT / "architecture" / "runtime" / "__main__.py",
    ROOT / "architecture" / "runtime" / "__init__.py",
    ROOT / "architecture" / "pipeline" / "orchestrator.py",
    ROOT / "architecture" / "knowledge" / "__init__.py",
)


def test_empty_feedback():
    signal = compose_feedback_signal()
    assert signal.feedback_type is FeedbackType.OTHER
    assert signal.value is FeedbackValue.UNKNOWN
    assert signal.epistemic_status == EPISTEMIC_FEEDBACK_SIGNAL
    assert signal.timestamp is None
    assert signal.provenance is None
    assert signal.subject.canonical is False
    assert "timestamp" in signal.unknowns
    assert "provenance" in signal.unknowns
    assert "value" in signal.unknowns


def test_basic_feedback_creation():
    signal = create_feedback(
        FeedbackType.CONFIRMATION,
        FeedbackValue.CORRECT,
        subject_id="obs-1",
        subject_kind=SubjectKind.OBSERVATION,
        actor_class=ActorClass.HUMAN,
        rationale="looks right",
    )
    assert signal.feedback_id.startswith("feedback:")
    assert signal.correction_class is CorrectionClass.CONFIRMATION
    assert signal.consumer_contract == CONSUMER_CONTRACT
    assert create_feedback is compose_feedback_signal


def test_confirmation():
    signal = compose_feedback_signal("CONFIRMATION", "CORRECT", subject_id="d1", subject_kind="DECISION")
    assert signal.feedback_type is FeedbackType.CONFIRMATION
    assert signal.value is FeedbackValue.CORRECT


def test_correction():
    signal = compose_feedback_signal("CORRECTION", "INCORRECT", subject_id="d1", subject_kind="DECISION")
    assert signal.feedback_type is FeedbackType.CORRECTION
    assert signal.correction_class is CorrectionClass.CORRECTION


def test_disagreement():
    signal = compose_feedback_signal("DISAGREEMENT", "NEGATIVE", subject_id="d1", subject_kind="DECISION")
    assert signal.feedback_type is FeedbackType.DISAGREEMENT
    assert signal.correction_class is CorrectionClass.DISAGREEMENT


def test_false_positive():
    signal = compose_feedback_signal("FALSE_POSITIVE", "INCORRECT", subject_id="alert-1", subject_kind="ALERT")
    assert signal.feedback_type is FeedbackType.FALSE_POSITIVE


def test_false_negative():
    signal = compose_feedback_signal("FALSE_NEGATIVE", "INCORRECT", subject_id="alert-2", subject_kind="ALERT")
    assert signal.feedback_type is FeedbackType.FALSE_NEGATIVE


def test_missed_signal():
    signal = compose_feedback_signal("MISSED_SIGNAL", "NEGATIVE", subject_id="obs-9", subject_kind="OBSERVATION")
    assert signal.feedback_type is FeedbackType.MISSED_SIGNAL


def test_security_concern():
    signal = compose_feedback_signal(
        "SECURITY_CONCERN",
        "NEGATIVE",
        subject_id="tok",
        subject_kind="UNVALIDATED_TOKEN",
        authoritative_state={"security_state": "PASS"},
    )
    assert signal.feedback_type is FeedbackType.SECURITY_CONCERN
    assert signal.authoritative_state["security_state"] == "PASS"
    assert any("security" in c for c in signal.conflicts)


def test_identity_correction():
    signal = compose_feedback_signal(
        "IDENTITY_CORRECTION",
        "INCORRECT",
        subject_id="alias",
        subject_kind="ALIAS",
        authoritative_state={"identity_state": "UNRESOLVED"},
    )
    assert signal.subject.canonical is False
    assert signal.authoritative_state["identity_state"] == "UNRESOLVED"
    assert any("identity" in c for c in signal.conflicts)


def test_evidence_quality_feedback():
    signal = compose_feedback_signal("EVIDENCE_QUALITY", "UNCERTAIN", subject_id="ev1", subject_kind="EVIDENCE")
    assert signal.feedback_type is FeedbackType.EVIDENCE_QUALITY


def test_decision_quality_feedback():
    signal = compose_feedback_signal("DECISION_QUALITY", "NEGATIVE", subject_id="dec1", subject_kind="DECISION")
    assert signal.feedback_type is FeedbackType.DECISION_QUALITY


def test_alert_quality_feedback():
    signal = compose_feedback_signal("ALERT_QUALITY", "POSITIVE", subject_id="al1", subject_kind="ALERT")
    assert signal.feedback_type is FeedbackType.ALERT_QUALITY


def test_observation_quality_feedback():
    signal = compose_feedback_signal("OBSERVATION_QUALITY", "CORRECT", subject_id="ob1", subject_kind="OBSERVATION")
    assert signal.feedback_type is FeedbackType.OBSERVATION_QUALITY


def test_unresolved_subject():
    signal = compose_feedback_signal(
        "CONFIRMATION",
        "CORRECT",
        subject_id="maybe",
        subject_kind=SubjectKind.CANONICAL_TOKEN,
        identity_state="UNRESOLVED",
    )
    assert signal.subject.canonical is False
    assert signal.subject.kind is not SubjectKind.CANONICAL_TOKEN
    assert "canonical_identity_not_authorized" in signal.unknowns


def test_verified_canonical_subject():
    signal = compose_feedback_signal(
        "CONFIRMATION",
        "CORRECT",
        subject_id="abc123canonicalid",
        subject_kind=SubjectKind.CANONICAL_TOKEN,
        identity_state="VERIFIED",
    )
    assert signal.subject.canonical is True
    assert signal.subject.kind is SubjectKind.CANONICAL_TOKEN
    assert signal.subject.value == "abc123canonicalid"


def test_operational_id_remains_non_canonical():
    signal = compose_feedback_signal(
        "CONFIRMATION",
        "CORRECT",
        subject_id="solana:So111",
        subject_kind=SubjectKind.OPERATIONAL_TOKEN,
        identity_state="VERIFIED",
    )
    assert signal.subject.canonical is False
    assert signal.subject.kind is SubjectKind.OPERATIONAL_TOKEN


def test_symbol_cannot_become_canonical():
    signal = compose_feedback_signal(
        "IDENTITY_CORRECTION",
        "INCORRECT",
        subject_id="PEPE",
        subject_kind=SubjectKind.DISPLAY,
        identity_state="VERIFIED",
    )
    assert signal.subject.canonical is False
    assert signal.subject.kind is SubjectKind.DISPLAY


def test_aliases_cannot_become_canonical():
    signal = compose_feedback_signal(
        "IDENTITY_CORRECTION",
        "INCORRECT",
        subject_id="pepe-sol",
        subject_kind=SubjectKind.ALIAS,
        identity_state="VERIFIED",
    )
    assert signal.subject.canonical is False


def test_feedback_cannot_promote_epistemic_status():
    signal = compose_feedback_signal("CONFIRMATION", "CORRECT", metadata={"promote_to": "OBSERVED"})
    assert signal.epistemic_status == EPISTEMIC_FEEDBACK_SIGNAL
    assert signal.epistemic_status not in {"OBSERVED", "FACTUAL", "FACTUAL_PREMISE", "VERIFIED"}
    assert "OBSERVED" not in SRC or "never" in SRC.lower()


def test_feedback_cannot_overwrite_decision():
    signal = compose_feedback_signal(
        "DISAGREEMENT",
        "NEGATIVE",
        subject_id="d1",
        subject_kind="DECISION",
        authoritative_state={"decision_outcome": "REJECT"},
        rationale="I disagree; this looked legitimate.",
    )
    assert signal.authoritative_state["decision_outcome"] == "REJECT"
    assert signal.feedback_type is FeedbackType.DISAGREEMENT
    assert signal.value is FeedbackValue.NEGATIVE
    assert any("decision=REJECT" in c for c in signal.conflicts)


def test_feedback_cannot_overwrite_security():
    signal = compose_feedback_signal(
        "SECURITY_CONCERN",
        "NEGATIVE",
        rationale="I think this token is a scam.",
        authoritative_state={"security_state": "PASS"},
    )
    assert signal.authoritative_state["security_state"] == "PASS"
    assert signal.feedback_type is FeedbackType.SECURITY_CONCERN
    assert signal.epistemic_status == EPISTEMIC_FEEDBACK_SIGNAL


def test_feedback_cannot_overwrite_identity():
    signal = compose_feedback_signal(
        "IDENTITY_CORRECTION",
        "INCORRECT",
        subject_id="FORGED",
        subject_kind=SubjectKind.CANONICAL_TOKEN,
        identity_state="UNRESOLVED",
        authoritative_state={"identity_state": "UNRESOLVED"},
    )
    assert signal.authoritative_state["identity_state"] == "UNRESOLVED"
    assert signal.subject.canonical is False


def test_conflicting_human_feedback_preserved():
    a = compose_feedback_signal("CONFIRMATION", "CORRECT", subject_id="d1", subject_kind="DECISION", actor_id="A")
    b = compose_feedback_signal("DISAGREEMENT", "INCORRECT", subject_id="d1", subject_kind="DECISION", actor_id="B")
    summary = aggregate_feedback((a, b))
    assert summary.count == 2
    assert summary.disagreements
    assert a.value is FeedbackValue.CORRECT
    assert b.value is FeedbackValue.INCORRECT


def test_source_objects_unchanged():
    refs = {"decision_id": "d1", "nested": {"k": "v"}}
    auth = {"decision_outcome": "BUY"}
    compose_feedback_signal("CONFIRMATION", "CORRECT", referenced_ids=refs, authoritative_state=auth)
    assert refs["decision_id"] == "d1"
    assert refs["nested"]["k"] == "v"
    assert auth["decision_outcome"] == "BUY"


def test_nested_mutation_isolation():
    nested = {"inner": {"k": "v"}}
    signal = compose_feedback_signal(
        "CONFIRMATION",
        "CORRECT",
        referenced_ids={"nested": nested},
        provenance={"trace": nested},
    )
    nested["inner"]["k"] = "mutated"
    assert signal.referenced_ids["nested"]["inner"]["k"] == "v"
    assert signal.provenance["trace"]["inner"]["k"] == "v"


def test_export_mutation_safety():
    signal = compose_feedback_signal(
        "CONFIRMATION",
        "CORRECT",
        subject_id="abc123canonicalid",
        subject_kind=SubjectKind.CANONICAL_TOKEN,
        identity_state="VERIFIED",
        provenance={"src": "operator"},
    )
    exported = signal.as_dict()
    exported["value"] = "FACTUAL"
    exported["subject"]["canonical"] = False
    exported["provenance"]["src"] = "market"
    assert signal.value is FeedbackValue.CORRECT
    assert signal.subject.canonical is True
    assert signal.provenance["src"] == "operator"
    assert signal.epistemic_status == EPISTEMIC_FEEDBACK_SIGNAL


def test_deterministic_ids():
    a = compose_feedback_signal("CONFIRMATION", "CORRECT", subject_id="x", subject_kind="CLAIM", actor_id="h1")
    b = compose_feedback_signal("CONFIRMATION", "CORRECT", subject_id="x", subject_kind="CLAIM", actor_id="h1")
    assert a.feedback_id == b.feedback_id
    assert a.feedback_id.startswith("feedback:")
    assert a.feedback_id != a.subject.value


def test_no_generated_timestamp():
    signal = compose_feedback_signal("CONFIRMATION", "CORRECT")
    assert signal.timestamp is None
    assert "datetime.now" not in SRC
    assert "time.time" not in SRC


def test_provenance_preservation():
    signal = compose_feedback_signal(
        "CONFIRMATION",
        "CORRECT",
        provenance={"actor": "reviewer", "source_ref": "note-3"},
    )
    assert signal.provenance["actor"] == "reviewer"
    assert "provenance" not in signal.unknowns


def test_missing_provenance_remains_missing():
    signal = compose_feedback_signal("CONFIRMATION", "CORRECT")
    assert signal.provenance is None
    assert "provenance" in signal.unknowns


def test_missing_timestamp_remains_missing():
    signal = compose_feedback_signal("CONFIRMATION", "CORRECT", timestamp=None)
    assert signal.timestamp is None
    assert "timestamp" in signal.unknowns


def test_equivalent_inputs_produce_equivalent_outputs():
    kwargs = dict(
        feedback_type="DECISION_QUALITY",
        value="NEGATIVE",
        subject_id="d9",
        subject_kind="DECISION",
        rationale="too aggressive",
        actor_class="OPERATOR",
        timestamp=12.0,
        provenance={"src": "desk"},
    )
    assert compose_feedback_signal(**kwargs) == compose_feedback_signal(**kwargs)


def test_no_db_access(monkeypatch):
    def _boom(*_a, **_k):
        raise AssertionError("feedback must not open sockets or dbs")

    monkeypatch.setattr("builtins.open", _boom)
    compose_feedback_signal("CONFIRMATION", "CORRECT")
    aggregate_feedback(())


def test_no_filesystem_writes(monkeypatch):
    def _boom(*_a, **_k):
        raise AssertionError("feedback must not write files")

    monkeypatch.setattr("builtins.open", _boom)
    compose_feedback_signal("SYSTEM_BEHAVIOR", "UNCERTAIN")


def test_no_runtime_or_forbidden_imports():
    for snippet in FORBIDDEN:
        assert snippet not in SRC, snippet


def test_production_surfaces_do_not_reference_feedback():
    for path in PRODUCTION:
        text = path.read_text(encoding="utf-8")
        assert "compose_feedback_signal" not in text, path
        if path.name == "__init__.py" and "knowledge" in str(path):
            assert "feedback" not in text


def test_knowledge_init_does_not_export_feedback():
    import architecture.knowledge as knowledge_pkg
    assert not hasattr(knowledge_pkg, "compose_feedback_signal")
    assert not hasattr(knowledge_pkg, "FeedbackSignal")


def test_isolated_import():
    import subprocess
    import sys

    code = (
        "import importlib.util, sys\n"
        "from pathlib import Path\n"
        "root = Path(r'''" + str(ROOT) + "''')\n"
        "path = root / 'architecture' / 'knowledge' / 'feedback.py'\n"
        "spec = importlib.util.spec_from_file_location('ahos_feedback_isolated', path)\n"
        "mod = importlib.util.module_from_spec(spec)\n"
        "sys.modules[spec.name] = mod\n"
        "spec.loader.exec_module(mod)\n"
        "banned = [k for k in sys.modules if k == 'discovery' "
        "or k.startswith('discovery.') "
        "or k.startswith('paper_trading') "
        "or k.startswith('architecture.runtime') "
        "or k.startswith('architecture.pipeline') "
        "or k.startswith('architecture.cognitive') "
        "or k.startswith('architecture.learning') "
        "or 'memory.observation' in k]\n"
        "assert banned == [], banned\n"
        "sig = mod.compose_feedback_signal()\n"
        "assert sig.epistemic_status == 'FEEDBACK_SIGNAL'\n"
        "assert sig.timestamp is None\n"
    )
    proc = subprocess.run([sys.executable, "-B", "-c", code], cwd=str(ROOT), capture_output=True, text=True)
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_aggregate_does_not_choose_winner():
    a = compose_feedback_signal("CORRECTION", "INCORRECT", subject_id="d1", subject_kind="DECISION")
    b = compose_feedback_signal("CORRECTION", "INCORRECT", subject_id="d1", subject_kind="DECISION", actor_id="z")
    summary = aggregate_feedback((a, b))
    assert summary.repeated_corrections
    assert "weight" not in summary.as_dict()
    assert "winner" not in summary.as_dict()


def test_supplied_timestamp_is_preserved_not_invented():
    signal = compose_feedback_signal("CONFIRMATION", "CORRECT", timestamp=99.5)
    assert signal.timestamp == 99.5
    assert "timestamp" not in signal.unknowns

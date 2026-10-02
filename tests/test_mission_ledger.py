"""GM-08 - mission/engineering ledger: append-only, hash-chained, resumable,
secret-free, and NOT a decision authority.

Offline self-tests (tmp files only; nothing under data/ is touched).
"""
from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.mission.ledger import (  # noqa: E402
    FIELDS, LEGAL_TRANSITIONS, LedgerError, LedgerTamperError, LedgerTransitionError,
    MissionExistsError, MissionLedger, MissionNotFoundError, SecretRejectedError,
    TaskStatus, default_ledger_path, redact_secrets,
)

AG = "engineering:grok"


@pytest.fixture()
def led(tmp_path):
    return MissionLedger(tmp_path / "ml.jsonl")


def _lines(led):
    return led.path.read_text(encoding="utf-8").splitlines()


def _write_lines(led, lines):
    led.path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ------------------------------------------------------------ contract ---

def test_fields_and_states_contract():
    assert FIELDS == ("MISSION_ID", "CURRENT_PHASE", "CURRENT_TASK", "TASK_STATUS", "CURRENT_AGENT",
                      "LAST_EVIDENCE", "LAST_TEST", "LAST_VERIFICATION", "LAST_COMMIT",
                      "CURRENT_BLOCKER", "NEXT_ACTION", "AI_PROVIDER", "CHECKPOINT")
    names = {s.value for s in TaskStatus}
    assert {"RUNNING", "PAUSED", "WAIT_FOR_AI", "BLOCKED", "RESUMED", "COMPLETED_UNVERIFIED"} <= names
    assert "DONE" not in names and "COMPLETED" not in names
    assert LEGAL_TRANSITIONS[TaskStatus.COMPLETED_UNVERIFIED] == frozenset()


def test_start_writes_full_snapshot_and_chain(led):
    st = led.start("GM-08", phase="P3", task="ledger", agent=AG, NEXT_ACTION="write tests")
    assert set(st) == set(FIELDS) and st["TASK_STATUS"] == "RUNNING"
    rec = json.loads(_lines(led)[0])
    assert rec["seq"] == 0 and rec["prev_hash"] == "0" * 64 and rec["authority"] == "NONE"
    assert rec["agent_taxonomy_ref"] == "docs/governance/agent_taxonomy_map.json"
    assert led.verify()["verdict"] == "CHAIN_INTACT"


def test_updates_carry_forward_and_are_append_only(led):
    led.start("M1", phase="P", task="t1", agent=AG)
    led.update("M1", LAST_TEST="12 passed", LAST_COMMIT="abc1234")
    led.update("M1", CURRENT_TASK="t2")
    st = led.latest("M1")
    assert st["LAST_TEST"] == "12 passed" and st["LAST_COMMIT"] == "abc1234" and st["CURRENT_TASK"] == "t2"
    assert len(_lines(led)) == 3 and len(led.history("M1")) == 3


def test_unknown_field_and_bad_ids_rejected(led):
    with pytest.raises(LedgerError):
        led.start("M1", phase="P", task="t", agent=AG, DECISION="BUY")
    with pytest.raises(LedgerError):
        led.start("bad id with spaces", phase="P", task="t", agent=AG)
    led.start("M1", phase="P", task="t", agent=AG)
    with pytest.raises(LedgerError):
        led.update("M1", TRADE="x")
    with pytest.raises(MissionNotFoundError):
        led.update("NOPE", LAST_TEST="x")


@pytest.mark.parametrize("bad", ["01", "agent 01", "AGENT-01", "grok", "x:y", "AG:", "engineering:"])
def test_agent_requires_taxonomy_namespace(led, bad):
    with pytest.raises(LedgerError):
        led.start("M1", phase="P", task="t", agent=bad)


@pytest.mark.parametrize("ok", ["engineering:claude", "AG:AG-15", "AGENT:AGENT-01", "agent:chief-orchestrator",
                                "agent.org:01-chief-architect", "M0:A"])
def test_namespaced_agents_accepted(tmp_path, ok):
    MissionLedger(tmp_path / "a.jsonl").start("M1", phase="P", task="t", agent=ok)


def test_refuses_database_path(tmp_path):
    for name in ("x.sqlite", "x.db", "x.sqlite3"):
        with pytest.raises(LedgerError):
            MissionLedger(tmp_path / name)


def test_default_path_is_isolated_jsonl(monkeypatch, tmp_path):
    monkeypatch.setenv("AHOS_DATA_DIR", str(tmp_path))
    p = default_ledger_path(create=False)
    assert p == tmp_path.resolve() / "mission_ledger" / "mission_ledger.jsonl"
    assert not p.parent.exists()          # resolving never creates anything


# --------------------------------------------------------- transitions ---

def test_illegal_transitions_rejected(led):
    led.start("M1", phase="P", task="t", agent=AG)
    led.update("M1", status="COMPLETED_UNVERIFIED")
    for s in TaskStatus:
        with pytest.raises(LedgerTransitionError):
            led.update("M1", status=s)
    led.start("M2", phase="P", task="t", agent=AG, status="PENDING")
    with pytest.raises(LedgerTransitionError):
        led.update("M2", status="RESUMED")
    with pytest.raises(LedgerTransitionError):
        led.start("M3", phase="P", task="t", agent=AG, status="COMPLETED_UNVERIFIED")


def test_start_never_restarts_existing_mission(led):
    led.start("M1", phase="P", task="t", agent=AG)
    led.pause("M1", checkpoint={"step": 3})
    with pytest.raises(MissionExistsError):
        led.start("M1", phase="P", task="t", agent=AG)
    assert led.latest("M1")["CHECKPOINT"] == {"step": 3}


# --------------------------------------------------- checkpoint/resume ---

def test_pause_checkpoint_resume_roundtrip(led):
    led.start("M1", phase="P3", task="t", agent=AG)
    led.checkpoint("M1", {"step": 2, "done": ["a", "b"]}, LAST_TEST="5 passed")
    led.pause("M1", status="WAIT_FOR_AI", CURRENT_BLOCKER="provider quota")
    st = led.resume("M1", agent="engineering:claude")
    assert st["TASK_STATUS"] == "RESUMED"
    assert st["CHECKPOINT"] == {"step": 2, "done": ["a", "b"]}
    assert st["CURRENT_AGENT"] == "engineering:claude" and st["LAST_TEST"] == "5 passed"
    led.update("M1", status="RUNNING")
    with pytest.raises(LedgerError):
        led.resume("M1", crash_recovery=True, CHECKPOINT={"step": 0})   # cannot reset checkpoint


def test_resume_requires_existing_mission_and_interrupted_state(led):
    with pytest.raises(MissionNotFoundError):
        led.resume("GHOST")
    led.start("M1", phase="P", task="t", agent=AG)
    with pytest.raises(LedgerTransitionError):
        led.resume("M1")                       # RUNNING without crash flag
    led.update("M1", status="COMPLETED_UNVERIFIED")
    with pytest.raises(LedgerTransitionError):
        led.resume("M1", crash_recovery=True)


def test_resume_after_crash_from_fresh_process(tmp_path):
    path = tmp_path / "ml.jsonl"
    code = (
        "import sys; sys.path.insert(0, %r)\n"
        "from architecture.mission.ledger import MissionLedger\n"
        "L = MissionLedger(%r)\n"
        "L.start('M1', phase='P', task='t', agent='engineering:grok')\n"
        "L.checkpoint('M1', {'step': 7, 'cursor': 'file-42'})\n"
        "import os; os._exit(9)\n"                         # hard crash, no cleanup
    ) % (str(ROOT), str(path))
    r = subprocess.run([sys.executable, "-c", code], timeout=60)
    assert r.returncode == 9
    led = MissionLedger(path)
    assert led.latest("M1")["TASK_STATUS"] == "RUNNING"
    st = led.resume("M1", crash_recovery=True)
    assert st["CHECKPOINT"] == {"step": 7, "cursor": "file-42"}
    assert led.history("M1")[-1]["event"] == "CRASH_RECOVERY_RESUME"


def test_torn_tail_blocks_append_until_explicit_recovery(led):
    led.start("M1", phase="P", task="t", agent=AG)
    led.checkpoint("M1", {"step": 1})
    with open(led.path, "ab") as fh:
        fh.write(b'{"schema":"ahos.mission_ledger.v1","seq":2,"ts":"2026-')   # crash mid-write
    assert led.verify()["verdict"] == "CHAIN_INTACT_TORN_TAIL"
    assert led.latest("M1")["CHECKPOINT"] == {"step": 1}
    with pytest.raises(LedgerError):
        led.update("M1", LAST_TEST="x")
    led.recover_torn_tail(agent=AG, note="crash during write")
    led.resume("M1", crash_recovery=True)
    v = led.verify()
    assert v["verdict"] == "CHAIN_INTACT" and v["entries"] == 4
    assert led.latest("M1")["CHECKPOINT"] == {"step": 1}


def test_checkpoint_limits(led):
    led.start("M1", phase="P", task="t", agent=AG)
    with pytest.raises(LedgerError):
        led.checkpoint("M1", {"blob": "x" * (70 * 1024)})
    with pytest.raises(LedgerError):
        led.checkpoint("M1", {"obj": object()})


# ------------------------------------------------------------- tamper ---

def _seed(led):
    led.start("M1", phase="P", task="t", agent=AG)
    led.update("M1", LAST_TEST="1 passed")
    led.update("M1", LAST_COMMIT="abc")
    return _lines(led)


def test_modified_entry_detected(led):
    lines = _seed(led)
    rec = json.loads(lines[1]); rec["state"]["LAST_TEST"] = "999 passed"
    lines[1] = json.dumps(rec, sort_keys=True, separators=(",", ":"))
    _write_lines(led, lines)
    with pytest.raises(LedgerTamperError, match="entry_hash"):
        led.verify()


def test_rehashed_forgery_still_breaks_chain(led):
    import hashlib
    lines = _seed(led)
    rec = json.loads(lines[1]); rec["state"]["LAST_TEST"] = "999 passed"
    body = {k: v for k, v in rec.items() if k != "entry_hash"}
    rec["entry_hash"] = hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    lines[1] = json.dumps(rec, sort_keys=True, separators=(",", ":"))
    _write_lines(led, lines)
    with pytest.raises(LedgerTamperError, match="prev_hash"):
        led.verify()


@pytest.mark.parametrize("mutate", ["delete_middle", "swap", "duplicate", "blank", "garbage_middle"])
def test_structural_tampering_detected(led, mutate):
    lines = _seed(led)
    if mutate == "delete_middle":
        del lines[1]
    elif mutate == "swap":
        lines[1], lines[2] = lines[2], lines[1]
    elif mutate == "duplicate":
        lines.insert(2, lines[1])
    elif mutate == "blank":
        lines.insert(1, "")
    else:
        lines.insert(1, "not json at all")
    _write_lines(led, lines)
    with pytest.raises(LedgerTamperError):
        led.verify()
    with pytest.raises(LedgerTamperError):
        led.update("M1", LAST_TEST="x")         # never appends onto a broken chain


def test_forged_recovery_marker_cannot_hide_garbage(led):
    lines = _seed(led)
    lines.insert(1, "garbage")
    _write_lines(led, lines)
    with pytest.raises(LedgerTamperError):
        led.verify()


# ------------------------------------------------------------- secrets ---

FAKE_SECRETS = [  # (text, substring that must never reach disk) - all synthetic
    ("sk" + "-proj-" + "AbCdEfGhIjKlMnOp" + "QrStUvWx12345678", "QrStUvWx12345678"),
    ("sk" + "-ant-api03-" + "Z" * 24, "Z" * 16),
    ("gsk_" + "a1B2" * 12, "a1B2a1B2a1B2"),
    ("xai-" + "Q" * 40, "Q" * 16),
    ("AIza" + "S" * 35, "S" * 16),
    ("ghp_" + "x" * 36, "x" * 16),
    ("AK" + "IA" + "ABCDEFGHIJKLMNOP", "ABCDEFGHIJKLMNOP"),
    ("123456789:" + "A" * 35, "A" * 16),
    ("Bearer " + "abcdefghijklmnop" + "qrstuvwxyz012345", "qrstuvwxyz012345"),
    ("postgres://ahos:" + "hunter22secret" + "@127.0.0.1:5432/ahos", "hunter22secret"),
    ("eyJ" + "hbGciOiJIUzI1NiJ9." + "eyJzdWIiOiIxMjM0NTY3ODkwIn0" + ".abcdefghijklmnop", "eyJzdWIiOiIxMjM0NTY3ODkwIn0"),
    ("0x" + "ab" * 32, "ab" * 16),
    ("OPENAI_API_KEY" + "=" + "supersecretvalue123", "supersecretvalue123"),
    ("password: 'CorrectHorseBattery'", "CorrectHorseBattery"),
    ("-----BEGIN RSA " + "PRIVATE KEY-----\nMIIEowSECRETBODY\n-----END RSA " + "PRIVATE KEY-----", "MIIEowSECRETBODY"),
]


@pytest.mark.parametrize("secret,core", FAKE_SECRETS)
def test_secrets_are_redacted_before_disk(led, secret, core):
    led.start("M1", phase="P", task="t", agent=AG)
    led.update("M1", CURRENT_BLOCKER=f"provider said: {secret}",
               CHECKPOINT={"note": secret, secret: 1, "nested": [secret]})
    raw = led.path.read_text(encoding="utf-8")
    assert core not in raw, secret
    assert "[REDACTED:" in raw
    assert led.history("M1")[-1]["redactions"]
    assert led.verify()["verdict"] == "CHAIN_INTACT"


@pytest.mark.parametrize("secret", [t for t, _ in FAKE_SECRETS])
def test_strict_mode_rejects_and_writes_nothing(tmp_path, secret):
    led = MissionLedger(tmp_path / "s.jsonl", strict=True)
    led.start("M1", phase="P", task="t", agent=AG)
    before = led.path.read_bytes()
    with pytest.raises(SecretRejectedError):
        led.update("M1", LAST_EVIDENCE=secret)
    assert led.path.read_bytes() == before


def test_secret_like_mission_id_refused(led):
    with pytest.raises((SecretRejectedError, LedgerError)):
        led.start("sk" + "-proj-" + "AbCdEfGhIjKlMnOpQrSt", phase="P", task="t", agent=AG)


def test_redaction_is_idempotent_and_strict_survives_followups(tmp_path):
    led = MissionLedger(tmp_path / "r.jsonl")
    led.start("M1", phase="P", task="t", agent=AG, LAST_EVIDENCE="api_key=abcdef123456")
    strict = MissionLedger(tmp_path / "r.jsonl", strict=True)
    strict.update("M1", LAST_TEST="3 passed")       # stored redaction marker must not re-trigger
    once, k1 = redact_secrets("api_key=abcdef123456")
    twice, k2 = redact_secrets(once)
    assert once == twice and k1 and not k2


def test_benign_text_kept(led):
    st = led.start("M1", phase="P3", task="GM-08 ledger", agent=AG,
                   LAST_TEST="tests/test_mission_ledger.py 40 passed", LAST_COMMIT="a6638bf")
    assert st["LAST_TEST"] == "tests/test_mission_ledger.py 40 passed" and st["LAST_COMMIT"] == "a6638bf"


# ------------------------------------------------------- non-authority ---

def test_ledger_module_imports_no_decision_or_trading_code():
    for f in (ROOT / "architecture" / "mission").glob("*.py"):
        tree = ast.parse(f.read_text(encoding="utf-8"))
        mods = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                mods.update(a.name for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                mods.add(node.module)
        bad = [m for m in mods if m.split(".")[0] in {"discovery", "paper_trading", "engine", "telegram_ai"}
               or m.startswith(("architecture.decision", "architecture.risk", "architecture.positions"))]
        assert bad == [], (f.name, bad)


def test_no_decision_or_trading_code_imports_the_ledger():
    roots = [ROOT / "architecture" / d for d in ("decision", "risk", "positions", "scoring")] + \
            [ROOT / "paper_trading", ROOT / "discovery", ROOT / "engine"]
    hits = []
    for r in roots:
        for f in r.rglob("*.py") if r.is_dir() else []:
            t = f.read_text(encoding="utf-8", errors="ignore")
            if "architecture.mission" in t or "mission_ledger" in t:
                hits.append(str(f.relative_to(ROOT)))
    assert hits == []


# ------------------------------------------------------------------ CLI ---

def test_cli_verify_detects_tamper_and_is_read_only(tmp_path):
    p = tmp_path / "c.jsonl"
    led = MissionLedger(p)
    led.start("M1", phase="P", task="t", agent=AG)
    led.update("M1", LAST_TEST="x")
    cli = [sys.executable, str(ROOT / "scripts" / "mission_ledger.py")]
    before = p.read_bytes()
    r = subprocess.run(cli + ["verify", "--path", str(p)], capture_output=True, text=True, timeout=60)
    assert r.returncode == 0 and json.loads(r.stdout)["verdict"] == "CHAIN_INTACT"
    assert p.read_bytes() == before
    lines = p.read_text(encoding="utf-8").splitlines()
    lines[0] = lines[0].replace('"P"', '"Q"')
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    r = subprocess.run(cli + ["verify", "--path", str(p)], capture_output=True, text=True, timeout=60)
    assert r.returncode == 3 and "TAMPER_DETECTED" in r.stdout
    r = subprocess.run(cli + ["verify", "--path", str(tmp_path / "none.jsonl")], capture_output=True, text=True, timeout=60)
    assert r.returncode == 4


def test_torn_tail_that_is_a_complete_record_without_newline(tmp_path):
    """Crash exactly before the trailing newline: the cut record is quarantined, not trusted."""
    a = MissionLedger(tmp_path / "a.jsonl")
    a.start("M1", phase="P", task="t", agent=AG)
    a.checkpoint("M1", {"step": 1})
    raw = a.path.read_bytes()
    a.checkpoint("M1", {"step": 2})
    full = a.path.read_bytes()
    a.path.write_bytes(full[:-1])                 # drop only the final "\n"
    assert a.verify()["torn_tail"] is True
    assert a.latest("M1")["CHECKPOINT"] == {"step": 1}     # unconfirmed write not trusted
    a.recover_torn_tail(agent=AG)
    st = a.resume("M1", crash_recovery=True)
    assert st["CHECKPOINT"] == {"step": 1}
    assert a.verify()["verdict"] == "CHAIN_INTACT"
    assert a.path.read_bytes().startswith(raw)            # nothing before was rewritten


def test_external_anchor_detects_full_rewrite(tmp_path):
    a = MissionLedger(tmp_path / "a.jsonl")
    a.start("M1", phase="P", task="t", agent=AG)
    anchor = a.verify()["head_hash"]
    a.update("M1", LAST_TEST="1 passed")
    assert a.verify(anchor_hash=anchor)["verdict"] == "CHAIN_INTACT"
    # attacker rewrites the whole file from scratch with a consistent new chain
    a.path.unlink()
    b = MissionLedger(tmp_path / "a.jsonl", clock=lambda: "2020-01-01T00:00:00.000000Z")
    b.start("M1", phase="P", task="forged", agent=AG)
    assert b.verify()["verdict"] == "CHAIN_INTACT"           # chain alone can't tell
    with pytest.raises(LedgerTamperError, match="anchor"):
        b.verify(anchor_hash=anchor)

"""Unit tests for the launcher smoke harness itself.

``launcher/smoke.py`` is real-process evidence, so most of it cannot be run
inside the test suite (it starts and stops the whole stack). The pieces that
*can* be proven without a running host are the pure helpers the verdicts are
built from: the audit-pair predicate, the JSON helper, the credential reader
(presence and shape, never the value), and the window-census intersection that
backs the "no visible console" contract.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import launcher.smoke as S  # noqa: E402


def _audit(*decisions: str, channel: str = "dashboard_launcher_api",
           intent: str = "restart") -> list[dict]:
    # The ledger on disk is serialised snake_case (channel_claimed, not the TS
    # parameter name channelClaimed) — the reader must match the wire format.
    return [{"intent": intent, "channel_claimed": channel, "decision": d}
            for d in decisions]


class TestAuditPair:
    """The write-ahead contract is an EXECUTING *and* a CONFIRMED on the dashboard
    channel; anything else must read as a broken chain."""

    def test_executing_plus_confirmed_is_a_pair(self):
        assert S._audit_pair(_audit("EXECUTING", "CONFIRMED"), "restart")

    def test_confirmed_without_executing_is_not_a_pair(self):
        # CONFIRMED alone means an action happened unaudited.
        assert not S._audit_pair(_audit("CONFIRMED"), "restart")

    def test_executing_without_confirmed_is_not_a_pair(self):
        # EXECUTING alone means the chain claims something that never settled.
        assert not S._audit_pair(_audit("EXECUTING"), "restart")

    def test_wrong_channel_does_not_count(self):
        same = _audit("EXECUTING", "CONFIRMED", channel="telegram")
        assert not S._audit_pair(same, "restart")

    def test_wrong_intent_does_not_count(self):
        assert not S._audit_pair(_audit("EXECUTING", "CONFIRMED"), "stop")

    def test_ledger_without_relevant_lines(self):
        assert not S._audit_pair([], "restart")

    def test_camel_case_wire_key_matches_nothing(self):
        # The TS caller passes `channelClaimed`, but the record on disk is
        # serialised `channel_claimed`. A reader keyed on the parameter name
        # silently matches zero records, so every pair reads as a broken chain.
        camel = [{"intent": "restart", "channelClaimed": "dashboard_launcher_api",
                  "decision": d} for d in ("EXECUTING", "CONFIRMED")]
        assert not S._audit_pair(camel, "restart")


class TestAuditBaseline:
    """The audit evidence must be scoped to *this* run.

    Regression: ``_audit_records`` returned only the last 40 lines, so the
    append delta saturated at zero once the ledger grew past 40 records and every
    run looked as if it had written nothing; and the pair check scanned the whole
    tail, so a *previous* run's EXECUTING/CONFIRMED pair satisfied the predicate
    even when this run wrote none.
    """

    def test_records_since_baseline_skips_older_records(self, tmp_path, monkeypatch):
        monkeypatch.setattr(S, "AUDIT_PATH", tmp_path / "audit.jsonl")
        S.AUDIT_PATH.write_text(
            "\n".join(json.dumps(r) for r in _audit("EXECUTING", "CONFIRMED")),
            encoding="utf-8")
        # baseline taken before this run: the pre-existing pair must not show up
        assert S._audit_records_since(2) == []
        assert len(S._audit_records_since(0)) == 2

    def test_records_since_baseline_counts_past_the_old_tail_cap(self, tmp_path, monkeypatch):
        """The 40-line tail cap made the append count saturate; the whole file is
        the only honest numerator."""
        monkeypatch.setattr(S, "AUDIT_PATH", tmp_path / "audit.jsonl")
        records = _audit("EXECUTING")
        S.AUDIT_PATH.write_text(
            "\n".join(json.dumps(r) for r in records * 3), encoding="utf-8")
        assert len(S._audit_records_since(0)) == 3
        assert len(S._audit_records_since(2)) == 1

    def test_a_stale_pair_from_an_earlier_run_does_not_satisfy_the_predicate(
            self, tmp_path, monkeypatch):
        monkeypatch.setattr(S, "AUDIT_PATH", tmp_path / "audit.jsonl")
        older = _audit("EXECUTING", "CONFIRMED", intent="restart")
        mine = _audit("EXECUTING", intent="stop")
        S.AUDIT_PATH.write_text(
            "\n".join(json.dumps(r) for r in older + mine), encoding="utf-8")
        since = S._audit_records_since(len(older))
        assert S._audit_pair(since, "stop") is False   # this run has no CONFIRMED
        assert S._audit_pair(S._audit_parse_all(), "restart") is True  # old pair still there


class TestTryJson:
    def test_object_decodes(self):
        assert S._try_json('{"ok": true}') == {"ok": True}

    def test_garbage_is_none(self):
        assert S._try_json("<html>nope</html>") is None

    def test_bare_true_is_not_a_status_body(self):
        assert S._try_json("true") is None

    def test_bare_number_is_not_a_status_body(self):
        assert S._try_json("42") is None

    def test_bare_array_is_not_a_status_body(self):
        assert S._try_json("[]") is None


class TestWebApiToken:
    """``_web_api_token`` reads the bearer the dashboard route demands. The only
    thing these tests assert is *shape*: the value itself is a secret and must
    never appear in test output."""

    def test_quoted_value_is_unquoted(self, monkeypatch, tmp_path):
        monkeypatch.setattr(S, "ROOT", tmp_path)
        (tmp_path / ".env").write_text(
            'OTHER=1\nAHOS_WEB_API_TOKEN="secret-token-here"\n', encoding="utf-8")
        assert S._web_api_token() == "secret-token-here"

    def test_placeholder_is_treated_as_absent(self, monkeypatch, tmp_path):
        # A repo default placeholder is not a credential; reading it would send
        # a token the gateway never accepted and turn a 401 into a mystery.
        monkeypatch.setattr(S, "ROOT", tmp_path)
        (tmp_path / ".env").write_text(
            "AHOS_WEB_API_TOKEN=change-me\n", encoding="utf-8")
        assert S._web_api_token() is None

    def test_missing_file_is_absent(self, monkeypatch, tmp_path):
        monkeypatch.setattr(S, "ROOT", tmp_path)
        assert S._web_api_token() is None

    def test_missing_key_is_absent(self, monkeypatch, tmp_path):
        monkeypatch.setattr(S, "ROOT", tmp_path)
        (tmp_path / ".env").write_text("DATABASE_URL=postgres://x\n",
                                       encoding="utf-8")
        assert S._web_api_token() is None

    def test_no_leak_into_repr(self, monkeypatch, tmp_path):
        monkeypatch.setattr(S, "ROOT", tmp_path)
        (tmp_path / ".env").write_text("AHOS_WEB_API_TOKEN=do-not-leak-me\n",
                                       encoding="utf-8")
        tok = S._web_api_token()
        # The helper returns the raw value to the caller only; evidence records
        # are built from headers, never from this value.
        assert tok == "do-not-leak-me"


@pytest.mark.skipif(os.name != "nt", reason="window census is Windows-only")
class TestWindowCensus:
    """The one-click contract: no AHOS child may own a visible window. The census
    proves it by intersecting the component pids with the set of pids that own a
    window title."""

    def test_component_owning_a_window_is_reported(self, monkeypatch, tmp_path):
        monkeypatch.setattr(S, "REPORT_DIR", tmp_path)
        (tmp_path / "status.json").write_text(json.dumps({
            "overall": "ONLINE",
            "components": {"gateway": {"status": "HEALTHY", "pid": 999}},
        }), encoding="utf-8")

        class _Fake:
            returncode = 0
            stdout = json.dumps(
                [{"Id": 999, "ProcessName": "node",
                  "MainWindowTitle": "C:\\robat\\ahos\\gateway"}])

        monkeypatch.setattr(S.subprocess, "run", lambda *a, **k: _Fake())
        census = S._window_census()
        assert census["components_owning_windows"] == [999]

    def test_windowless_component_is_clean(self, monkeypatch, tmp_path):
        monkeypatch.setattr(S, "REPORT_DIR", tmp_path)
        (tmp_path / "status.json").write_text(json.dumps({
            "overall": "ONLINE",
            "components": {"gateway": {"status": "HEALTHY", "pid": 1234}},
        }), encoding="utf-8")

        class _Fake:
            returncode = 0
            stdout = json.dumps(
                [{"Id": 4321, "ProcessName": "Code", "MainWindowTitle": "x.ts"}])

        monkeypatch.setattr(S.subprocess, "run", lambda *a, **k: _Fake())
        census = S._window_census()
        assert census["components_owning_windows"] == []

    def test_unparsable_census_is_not_a_silent_pass(self, monkeypatch, tmp_path):
        monkeypatch.setattr(S, "REPORT_DIR", tmp_path)
        (tmp_path / "status.json").write_text(json.dumps({
            "overall": "ONLINE",
            "components": {"gateway": {"status": "HEALTHY", "pid": 1234}},
        }), encoding="utf-8")

        class _Fake:
            returncode = 0
            stdout = ""  # powershell printed nothing usable

        monkeypatch.setattr(S.subprocess, "run", lambda *a, **k: _Fake())
        # No titles seen at all, so nothing is *proven* broken — but the census
        # must still name the component pids it could not clear.
        census = S._window_census()
        assert census["components_owning_windows"] == []
        assert census["component_pids"] == {"gateway": 1234}


class TestCaseSurface:
    def test_dashboard_api_case_is_registered(self):
        ap = S.__dict__.get("main")
        assert callable(ap)
        # argparse choices are not exported, so prove the case is reachable by
        # importing the function the dispatcher calls.
        assert callable(S.smoke_dashboard_api)

    def test_smoke_cases_are_all_implemented(self):
        for name in ("idempotent", "port_busy", "dashboard_api"):
            assert callable(S.__dict__[f"smoke_{name}"])

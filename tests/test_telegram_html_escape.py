#!/usr/bin/env python3
"""Telegram HTML parse_mode must escape untrusted fields (fail-closed).

Does not send live Telegram. Does not mint BUY. Live E2E remains M-GAP-009.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from telegram_ai.pump_alert import escape_telegram_html, format_pump_alert  # noqa: E402


def test_escape_telegram_html_is_not_a_noop():
    assert escape_telegram_html("") == ""
    assert escape_telegram_html("plain") == "plain"
    assert escape_telegram_html("<b>x</b>") == "&lt;b&gt;x&lt;/b&gt;"
    assert escape_telegram_html("a & b") == "a &amp; b"
    assert escape_telegram_html("&<>") == "&amp;&lt;&gt;"
    assert escape_telegram_html("<") != "<"


def test_format_pump_alert_escapes_untrusted_fields_keeps_structure():
    text = format_pump_alert(
        symbol="<b>HAX</b>&x",
        chain="sol<ana",
        score=90.0,
        decision="BUY",
        reasons=["a < b & c"],
        risks=["x > y"],
        price=None,
        liquidity=None,
        volume_24h=None,
        change_1h=None,
        address="abc<script>",
    )
    assert "<b>هشدار فرصت پایش" in text
    assert "&lt;b&gt;HAX&lt;/b&gt;&amp;x" in text
    assert "<b>HAX</b>" not in text
    assert "abc&lt;script&gt;" in text
    assert "a &lt; b &amp; c" in text
    assert "x &gt; y" in text
    assert "sol&lt;ana" in text

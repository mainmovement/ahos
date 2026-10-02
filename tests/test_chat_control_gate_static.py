"""GM-04 static guards for the chat control capability gate (conservative form).

Self-test, not independent verification. Pure file reads: no network, no DB,
no services. Pins the capability-reducing wiring so a later edit cannot
silently re-enable engine start/stop or paper_buy from the chat path.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_chat_does_not_import_engine_control():
    src = _read("chat.ts")
    assert not re.search(r"\bstartEngine\b", src)
    assert not re.search(r"\bstopEngine\b", src)


def test_chat_gate_runs_before_snapshot_and_paper_branch():
    src = _read("chat.ts")
    body = src[src.index("export async function handleChat"):]
    i_detect = body.index("detectIntent(text)")
    i_gate = body.index("gateChatControl(")
    i_audit = body.index("recordControlAudit(")
    i_snapshot = body.index("commandSnapshot()")
    i_paper = body.index('intent === "paper_buy"')
    assert i_detect < i_gate < i_audit < i_snapshot < i_paper
    gate_block = body[i_gate:i_snapshot]
    assert "if (gate.controlled)" in gate_block
    assert 'decision: "REFUSED"' in gate_block
    assert "return {" in gate_block


def test_chat_no_substring_stop_or_start_patterns():
    src = _read("chat.ts")
    assert "(توقف|استاپ|stop|خاموش)" not in src
    assert "(شروع|استارت|start|روشن)" not in src
    # Phase 7: the router moved to chat_intent.ts (pure); chat.ts delegates to it.
    assert "routeIntent(text" in src
    router = _read("chat_intent.ts")
    assert "(توقف|استاپ|stop|خاموش)" not in router
    assert "(شروع|استارت|start|روشن)" not in router
    body = router[router.index("export function routeIntent"):]
    i_control = body.index("detectControlCommand(text)")
    i_paper = body.index("looksLikePaperBuy(text)")
    i_trade = body.index("isTradeSignalRequest(text)")
    i_stop = body.index("isStopLossQuestion(text)")
    i_price = body.index("isPriceQuestion(text)")
    # GM-04 control/paper detection runs before every new intent, so the gate still sees them.
    assert i_control < i_paper < i_trade < i_stop < i_price


def test_canonical_paper_pins_still_hold():
    src = _read("chat.ts")
    assert "paperAllowedFromCanonical" in src
    assert "CANONICAL_PAPER_DENIED" in src
    assert "running = Boolean(state?.running)" in src
    assert src.index("(رد شد|چرا رد|reject)") < src.index("(چرا|دلیل|شواهد|explain)")


def test_gate_module_is_deny_by_default():
    src = _read("chat_control_gate.ts")
    fn = src[src.index("export function gateChatControl"):]
    fn = fn[: fn.index("\n}\n")]
    # The only allowed=true path is the non-control early return.
    assert fn.count("allowed: true") == 1
    assert "NOT_A_CONTROL_INTENT" in fn
    assert "allowed: false" in fn
    # The client-claimed channel is never consulted for the decision.
    assert "channelClaimed" not in fn
    assert "channel" not in fn.replace("CHAT_PATH_CANNOT_PROVE_LOCAL_DASHBOARD", "")
    for intent in ("start", "stop", "paper_buy"):
        assert re.search(rf"\b{intent}: \"(ENGINE_CONTROL|PAPER_WRITE)\"", src)


def test_audit_record_has_no_raw_text_or_raw_id_fields():
    src = _read("chat_control_gate.ts")
    rec = src[src.index("export type ControlAuditRecord"):]
    rec = rec[: rec.index("};")]
    assert "user_id_hash" in rec and "message_sha256" in rec
    for banned in ("message:", "text:", "user_id:", "chat_id:", "username:"):
        assert banned not in rec
    assert "appendFileSync" in src
    assert "writeFileSync" not in src  # append-only


def test_gateway_forwards_channel_and_user_for_audit_only():
    src = _read("conversation_gateway.ts")
    assert "channel: req.channel ?? null" in src
    assert "userId: req.user_id ?? null" in src


def test_dashboard_engine_and_paper_routes_unchanged_capability():
    eng = _read("app/api/engine/route.ts")
    assert "startEngine()" in eng and "stopEngine()" in eng
    assert "authorizeWebApi(req)" in eng
    assert 'decision: "ALLOWED"' in eng  # audited
    paper = _read("app/api/paper/route.ts")
    assert "addPaper(" in paper


def test_npm_selftest_registered():
    pkg = _read("package.json")
    assert '"test:chat-control-gate"' in pkg
    assert "scripts/chat_control_gate_selftest.ts" in pkg
    assert (ROOT / "scripts" / "chat_control_gate_selftest.ts").is_file()
    assert '"audit:control-verify"' in pkg
    assert (ROOT / "scripts" / "verify_control_audit.ts").is_file()


def test_telegram_service_still_declares_telegram_channel():
    # The gate does not trust this value; it is recorded in the audit as a claim.
    src = _read("telegram_ai/service.py")
    assert '"channel": "telegram"' in src

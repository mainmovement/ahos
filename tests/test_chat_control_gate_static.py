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


def test_chat_gate_runs_before_snapshot_and_agent():
    src = _read("chat.ts")
    body = src[src.index("export async function handleChat"):]
    i_detect = body.index("detectIntent(text)")
    i_gate = body.index("gateChatControl(")
    i_audit = body.index("recordControlAudit(")
    i_main_snapshot = body.index("const snap = await commandSnapshot()")
    # MJ-4: control intents are gated and (for owners) turned into proposals
    # BEFORE the main snapshot is taken or the conversational agent runs.
    assert i_detect < i_gate < i_audit < i_main_snapshot
    gate_block = body[i_gate:i_main_snapshot]
    assert "if (gate.controlled)" in gate_block
    assert 'decision: "REFUSED"' in gate_block
    assert "propose(store, kind" in gate_block  # owner → proposal, never execution
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
    """MJ-4: chat.ts has no direct paper write at all. The canonical BUY gate
    guards the only paper-buy path, which is the confirm flow in chat_actions
    (the same functions /api/paper uses)."""
    chat = _read("chat.ts")
    assert "addPaper(" not in chat
    actions = _read("chat_actions.ts")
    assert "paperAllowedFromCanonical" in actions
    assert "addPaper(" in actions
    paper = _read("app/api/paper/route.ts")
    assert "paperAllowedFromCanonical" in paper


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


def test_gateway_forwards_resolved_identity_and_assertion_for_audit_only():
    """MJ-3/MJ-4: the server-verified identity wins; the client assertion is
    carried through for the audit only and is never a grant."""
    src = _read("conversation_gateway.ts")
    assert "channel: req.identity?.channel ?? req.channel ?? null" in src
    assert "userId: req.identity?.userId ?? req.user_id ?? null" in src
    assert "proven: Boolean(req.identity?.proven)" in src
    assert "never as a grant" in src


def test_dashboard_engine_and_paper_routes_audit_write_ahead():
    """MJ-2: the dashboard engine route writes an EXECUTING record BEFORE it
    touches the engine, refuses when the write fails, then records the outcome."""
    eng = _read("app/api/engine/route.ts")
    assert "startEngine()" in eng and "stopEngine()" in eng
    assert "authorizeDashboardEndpoint(req)" in eng
    assert 'decision: "EXECUTING"' in eng  # write-ahead (MJ-2)
    assert "AUDIT_WRITE_FAILED" in eng  # refused when the audit write fails
    i_executing = eng.index('decision: "EXECUTING"')
    i_start = eng.index("startEngine()")
    assert i_executing < i_start  # audit precedes the action
    assert 'decision: "CONFIRMED"' in eng  # outcome record
    assert 'decision: "FAILED"' in eng
    paper = _read("app/api/paper/route.ts")
    assert "addPaper(" in paper


def test_chat_reaches_engine_only_through_the_confirm_flow():
    """MJ-4: chat.ts may not call the engine/paper/watch functions directly.
    The only route to them is chat_actions.handleConfirmation, which checks
    owner identity, expiry and identity binding and consumes the code (take)
    before executing anything."""
    src = _read("chat.ts")
    for banned in ("startEngine(", "stopEngine(", "addPaper(", "addWatch("):
        assert banned not in src, banned
    assert "handleConfirmation(" in src
    actions = _read("chat_actions.ts")
    fn = actions[actions.index("export async function handleConfirmation"):]
    # Order matters: identity binding and owner check run BEFORE the code is
    # consumed and before anything executes.
    i_identity = fn.index("a.identityKey !== identityKey(id)")
    i_owner = fn.index("if (!isOwner(id, opts.env))")
    i_expired = fn.index("store.isExpired(a)")
    i_take = fn.index("store.take(code); // single use")
    i_executing = fn.index('"EXECUTING"')
    i_execute = fn.index("await deps.startEngine()")
    assert i_identity < i_owner < i_expired < i_take < i_executing < i_execute
    # The code is consumed before execution, so a failed run can never replay.
    assert "single use, even if execution fails" in fn
    # MJ-1: an audit write failure aborts the action.
    assert "AUDIT_WRITE_AHEAD" in fn
    # m5: wrong guesses are counted and lock the identity out.
    assert "store.registerFailure(id)" in fn
    assert "isLocked(id)" in fn


def test_chat_actions_owner_gate_never_trusts_a_claim():
    """MJ-4/MJ-6: isOwner requires a server-proven identity and the admin list."""
    src = _read("chat_actions.ts")
    fn = src[src.index("export function isOwner"):]
    fn = fn[: fn.index("\n}\n")]
    assert "if (!id.proven) return false;" in fn  # BL-3: never an owner unproven
    # The proven check must precede any channel comparison.
    assert fn.index("!id.proven") < fn.index('"telegram"') < fn.index('"dashboard"')
    assert "TELEGRAM_ADMIN_USER_IDS" in fn
    assert "TELEGRAM_ALLOWED_CHAT_IDS" not in fn  # MJ-6: readers are not owners



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

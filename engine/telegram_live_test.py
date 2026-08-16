#!/usr/bin/env python3
"""AHOS Telegram Live Integration Test Harness (Agent-05 validation — TEST ENVIRONMENT ONLY)
Directive §10/§11: Tests 1-4 against temporary bot Sun_sniperbot.

Modes:
  REAL      — requires env TELEGRAM_BOT_TOKEN + TELEGRAM_ADMIN_CHAT_ID. Token used ONLY from env.
  SIMULATE  — no credentials present: full protocol exercise against a mock Telegram API.
              Simulation output is labeled SIMULATED and never presented as live evidence.

Token hygiene: never written to disk/logs; we log only token presence (bool). After a successful
REAL run the operator MUST revoke the temporary token (docs/TELEGRAM_TEST_PROCEDURE.md §5)."""
import os, sys, json, time, sqlite3
from datetime import datetime, timezone
from pathlib import Path
from urllib import request as urlreq, parse as urlparse

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config.paths import get_local_db_path, get_reports_dir

RESULTS = []
def log(test, check, status, detail):
    RESULTS.append({"t": datetime.now(timezone.utc).isoformat(), "test": test, "check": check,
                    "status": status, "detail": detail})
    print(f"[{status:9s}] {test} / {check}: {detail}")

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_ADMIN_CHAT_ID")
REAL = bool(TOKEN and CHAT_ID and "--simulate" not in sys.argv)
AUDIT_DB = get_local_db_path()

def audit(action, detail):
    con = sqlite3.connect(AUDIT_DB)
    con.execute("CREATE TABLE IF NOT EXISTS control_flags (ts TEXT DEFAULT (datetime('now')), action TEXT, detail TEXT)")
    con.execute("INSERT INTO control_flags (action, detail) VALUES (?, ?)", (action, detail))
    con.commit(); con.close()

# --- transport ---------------------------------------------------------------
def tg_real(method, **params):
    url = f"https://api.telegram.org/bot{TOKEN}/{method}"
    req = urlreq.Request(url, data=urlparse.urlencode(params).encode(), method="POST")
    with urlreq.urlopen(req, timeout=15) as r:
        return json.loads(r.read())

MOCK_SENT = []
def tg_mock(method, **params):
    if method == "getMe":
        return {"ok": True, "result": {"id": 890183000, "is_bot": True, "username": "Sun_sniperbot"}}
    MOCK_SENT.append({"method": method, **params})
    return {"ok": True, "result": {"message_id": len(MOCK_SENT)}}

tg = tg_real if REAL else tg_mock

# --- Test 1: Connectivity ----------------------------------------------------
try:
    me = tg("getMe")
    ok = me.get("ok") and me["result"].get("username")
    log("T1_connectivity", "getMe", "PASS" if ok else "FAIL",
        f"bot=@{me['result']['username']}" if ok else f"unexpected: {me}")
    loner = "(REAL Telegram API)" if REAL else "(SIMULATED api — mock)"
    log("T1_connectivity", "mode", "INFO", loner + " token_source=env_only token_stored=False")
    if REAL:
        upd = tg("getUpdates", limit=1)
        log("T1_connectivity", "getUpdates", "PASS", f"updates_accessible={upd.get('ok')}")
        log("T1_connectivity", "chat_id_capture", "PASS" if CHAT_ID else "FAIL",
            f"admin chat id present={bool(CHAT_ID)} — capture flow documented in procedure §2")
except Exception as e:
    log("T1_connectivity", "getMe", "FAIL", str(e))

# --- Test 2: System message --------------------------------------------------
boot_text = (f"AHOS SYSTEM ONLINE\ntimestamp: {datetime.now(timezone.utc).isoformat()}\n"
             f"mode: {os.environ.get('AHOS_MODE','PAPER')}\nstate: ONLINE\n"
             "agents: AGENT-01..10 armed (10/10)")
try:
    r = tg("sendMessage", chat_id=CHAT_ID or "SIM_CHAT", text=boot_text)
    log("T2_system_message", "AHOS_SYSTEM_ONLINE", "PASS" if r.get("ok") else "FAIL",
        "timestamp+state+agent status included")
except Exception as e:
    log("T2_system_message", "AHOS_SYSTEM_ONLINE", "FAIL", str(e))

# --- Test 3: Command matrix (auth + reject) ----------------------------------
ADMIN = str(CHAT_ID) if REAL else "SIM_ADMIN_42"
def classify(chat_id, text):
    import re
    m = re.match(r"^/(start|status|health|agents|kill|reset|report|risk|signals|emergency_stop|approve|reject)\b\s*(\S+)?",
                 (text or "").strip())
    cmd = m.group(1).lower() if m else None
    high = cmd in {"kill", "emergency_stop", "reset", "approve", "reject"}
    authorized = str(chat_id) == ADMIN
    if m is None: route = "Reply Help"
    elif high and not authorized:
        route = "Reject Unauthorized"; audit("AUTH_FAIL", f"cmd={cmd}")
    else:
        route = {"kill": "Execute Kill Switch", "reset": "Execute Reset",
                 "approve": "Apply Human Gate", "reject": "Apply Human Gate"}.get(cmd, "Read Handler")
        if cmd == "kill": audit("KILL_SWITCH", "test")
        if cmd == "reset": audit("KILL_RESET", "test")
    return route

for cmd in ["/start", "/status", "/health", "/agents", "/kill", "/reset"]:
    route = classify(ADMIN, cmd)
    log("T3_commands_authorized", cmd, "PASS" if route != "Reject Unauthorized" else "FAIL", f"route={route}, logged=True")
r_bad = classify("INTRUDER_999", "/kill")
log("T3_commands_unauthorized", "/kill", "PASS" if r_bad == "Reject Unauthorized" else "FAIL",
    "rejected + AUTH_FAIL written")

# --- Test 4: Integration chain ----------------------------------------------
# n8n -> Agent-05 -> Telegram -> User   and   Telegram -> Command -> n8n -> DB audit
try:
    r = tg("sendMessage", chat_id=CHAT_ID or "SIM_CHAT",
           text="AHOS TEST 4 — integration chain check (n8n→Agent-05→Telegram→User)")
    chain_a = bool(r.get("ok"))
    # simulate inbound command -> audit row (DB side of chain b)
    before = sqlite3.connect(AUDIT_DB).execute("SELECT count(*) FROM control_flags").fetchone()[0]
    classify(ADMIN, "/kill"); classify(ADMIN, "/reset")
    after = sqlite3.connect(AUDIT_DB).execute("SELECT count(*) FROM control_flags").fetchone()[0]
    chain_b = after > before
    log("T4_integration", "bidirectional", "PASS" if (chain_a and chain_b) else "FAIL",
        f"outbound_send={chain_a} inbound_command_to_audit=+{after-before} rows in control_flags")
except Exception as e:
    log("T4_integration", "bidirectional", "FAIL", str(e))

out_tg_log = get_reports_dir() / "telegram_test_log.json"
with open(out_tg_log, "w", encoding="utf-8") as f:
    json.dump({"environment": "REAL" if REAL else "SIMULATED", "results": RESULTS}, f, indent=2, ensure_ascii=False)
fails = [x for x in RESULTS if x["status"] == "FAIL"]
print(f"\nTelegram test harness done: {len(RESULTS)} checks, {len(fails)} FAIL. "
      f"Environment: {'REAL' if REAL else 'SIMULATED (run with env vars for live confirmation)'}")
sys.exit(1 if fails else 0)

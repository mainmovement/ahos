#!/usr/bin/env python3
"""AHOS Telegram Bot (Agent-05) — production skeleton.
Rules: token ONLY from env; admin gate on HIGH-risk commands; no secrets in logs.
READ commands are informational; HIGH-risk commands write DB flags consumed by n8n/engine."""
import os, sys, logging, sqlite3
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config.paths import get_local_db_path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", stream=sys.stdout)
log = logging.getLogger("ahos-bot")

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
ADMIN_CHAT = os.environ.get("TELEGRAM_ADMIN_CHAT_ID")
if not TOKEN or not ADMIN_CHAT:
    log.error("TELEGRAM_BOT_TOKEN / TELEGRAM_ADMIN_CHAT_ID missing — refusing to start (Agent-04 rule).")
    sys.exit(2)

READ_CMDS = {"start", "status", "report", "risk", "signals", "daily", "help"}
HIGH_CMDS = {"kill", "emergency_stop", "close_all", "approve", "reject", "update_params"}
DB = os.environ.get("AHOS_LOCAL_DB", get_local_db_path())

def flag(action: str, detail: str = ""):
    con = sqlite3.connect(DB)
    con.execute("CREATE TABLE IF NOT EXISTS control_flags (ts TEXT DEFAULT (datetime('now')), action TEXT, detail TEXT)")
    con.execute("INSERT INTO control_flags (action, detail) VALUES (?, ?)", (action, detail))
    con.commit(); con.close()

async def handle(update, context):
    chat_id = str(update.effective_chat.id)
    text = (update.message.text or "").strip()
    cmd = text.lstrip("/").split()[0].split("@")[0].lower() if text.startswith("/") else ""
    if cmd in HIGH_CMDS and chat_id != str(ADMIN_CHAT):
        log.warning("AUTH_FAIL chat_id=%s cmd=%s", chat_id, cmd)   # no text content logged
        await update.message.reply_text("Unauthorized. Incident logged.")
        return
    if cmd in ("kill", "emergency_stop"):
        flag("KILL_SWITCH", cmd)
        await update.message.reply_text("KILL SWITCH ENGAGED. All trading halted pending Agent-10 review.")
    elif cmd == "close_all":
        flag("CLOSE_ALL", cmd)
        await update.message.reply_text("CLOSE_ALL requested — engine will flatten paper positions at next cycle.")
    elif cmd in ("approve", "reject"):
        arg = text.split(maxsplit=1)[1] if len(text.split()) > 1 else ""
        flag("HUMAN_GATE", f"{cmd}:{arg}")
        await update.message.reply_text(f"Human gate recorded: {cmd} {arg}")
    elif cmd in READ_CMDS:
        await update.message.reply_text(
            "AHOS online (PAPER mode).\n"
            "Read: /status /report /risk /signals /daily\n"
            "High-risk (admin): /kill /emergency_stop /close_all /approve <sym> /reject <sym>")
    else:
        await update.message.reply_text("Unknown command. /help for list.")

def main():
    from telegram.ext import Application, MessageHandler, filters
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.StatusUpdate.ALL, handle))
    log.info("AHOS bot started (admin gate active).")
    app.run_polling()

if __name__ == "__main__":
    main()

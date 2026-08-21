#!/usr/bin/env python3
"""AHOS / Sun Sniper — live Telegram bot runner.

Usage:
  export TELEGRAM_BOT_TOKEN="..."   # from BotFather — NEVER commit
  export TELEGRAM_ALLOWED_CHAT_IDS="123456789"  # your chat id (recommended)
  export ALL_PROXY="socks5://127.0.0.1:10808"  # if Telegram is filtered
  python scripts/run_sun_sniper_bot.py

Talk naturally in Persian. Paper-only. No real trades.
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    token = (os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip()
    if not token:
        print("ERROR: TELEGRAM_BOT_TOKEN is empty.")
        print("  1) Open @BotFather → /token or create bot")
        print("  2) export TELEGRAM_BOT_TOKEN='...'")
        print("  3) NEVER put the token in git")
        return 2

    # Optional allow-list (comma-separated chat ids)
    raw_ids = (os.environ.get("TELEGRAM_ALLOWED_CHAT_IDS") or "").strip()
    allowed = [x.strip() for x in raw_ids.split(",") if x.strip()]
    admin_raw = (os.environ.get("TELEGRAM_ADMIN_USER_IDS") or "").strip()
    admins = [x.strip() for x in admin_raw.split(",") if x.strip()]

    from telegram_ai.adapter import (
        ProductionTelegramAdapter,
        TelegramSecurityGate,
    )
    from telegram_ai.bot import TelegramBotRunner
    from telegram_ai.service import TelegramDomainService

    adapter = ProductionTelegramAdapter(bot_token=token)
    me = adapter.get_me()
    if not me.get("ok"):
        print(f"getMe failed: {me.get('error') or me}")
        print("Check token + ALL_PROXY if you are in a filtered network.")
        return 3

    bot_user = (me.get("result") or {}).get("username") or "?"
    print(f"Sun Sniper online as @{bot_user}")
    if allowed:
        print(f"Allow-list chats: {allowed}")
    else:
        print("WARNING: TELEGRAM_ALLOWED_CHAT_IDS empty — anyone can talk to the bot.")

    gate = TelegramSecurityGate(
        allowed_chat_ids=allowed or None,
        admin_user_ids=admins or None,
        rate_limit_user_rps=float(os.environ.get("TELEGRAM_RATE_LIMIT_RPS") or "1.0"),
    )
    runner = TelegramBotRunner(
        adapter=adapter,
        service=TelegramDomainService(),
        gate=gate,
    )

    offset: int | None = None
    print("Polling… Ctrl+C to stop.")
    while True:
        try:
            updates = adapter.poll_updates(offset=offset, timeout=25)
            for up in updates:
                offset = up.update_id + 1
                try:
                    out = runner.process_update(up)
                    intent = out.get("intent") or out.get("status")
                    print(f"  chat={up.chat_id} → {intent}")
                except Exception as e:
                    print(f"  handler error: {type(e).__name__}: {e}")
            if not updates:
                time.sleep(0.3)
        except KeyboardInterrupt:
            print("\nStopped.")
            return 0
        except Exception as e:
            print(f"poll loop: {type(e).__name__}: {e}")
            time.sleep(3)


if __name__ == "__main__":
    raise SystemExit(main())

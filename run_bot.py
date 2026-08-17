#!/usr/bin/env python3
"""AHOS Telegram bot launcher — the copy-paste entry point.

    python run_bot.py                 # long-poll against Telegram
    python run_bot.py --preflight     # check config/connectivity, then exit
    python run_bot.py --console       # talk to the bot locally, no Telegram

Configuration comes from a .env file beside this script (see .env.example).
The only mandatory value is TELEGRAM_BOT_TOKEN; everything else has a working
default.

DESIGN NOTES FOR THE DEPLOYMENT TARGET (single user, laptop, Iran):
  * api.telegram.org is filtered. Set ALL_PROXY=socks5://127.0.0.1:10808 (or
    whatever your tunnel exposes) and every outbound call honours it.
  * --console mode needs no network at all, so the analysis layer stays usable
    even when the tunnel is down.
  * Long-poll, not webhook: a webhook needs a public HTTPS endpoint, which
    means a VPS. There is no VPS here by design.
  * Ctrl+C shuts down cleanly and the update offset is persisted, so restarting
    never replays or drops messages.
"""
from __future__ import annotations

import argparse
import json
import os
import signal
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

OFFSET_FILE = ROOT / "data" / "telegram_offset.json"


# --------------------------------------------------------------------- env --

def load_dotenv(path: Path = ROOT / ".env") -> dict[str, str]:
    """Minimal .env loader. No dependency, no surprises."""
    loaded: dict[str, str] = {}
    if not path.exists():
        return loaded
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key, val = key.strip(), val.strip().strip('"').strip("'")
        if key:
            loaded[key] = val
            os.environ.setdefault(key, val)
    return loaded


def _ids(raw: str | None) -> list[str]:
    return [x.strip() for x in (raw or "").split(",") if x.strip()]


# ---------------------------------------------------------------- offsets --

def read_offset() -> int | None:
    try:
        return json.loads(OFFSET_FILE.read_text()).get("offset")
    except Exception:
        return None


def write_offset(offset: int) -> None:
    try:
        OFFSET_FILE.parent.mkdir(parents=True, exist_ok=True)
        OFFSET_FILE.write_text(json.dumps({"offset": offset,
                                           "updated": time.time()}))
    except Exception:
        pass  # A lost offset costs one replayed message; never worth crashing.


# -------------------------------------------------------------- preflight --

def preflight(verbose: bool = True) -> tuple[bool, list[str]]:
    """Check everything that could stop the bot working, and say so plainly."""
    notes: list[str] = []
    ok = True

    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        ok = False
        notes.append("❌ TELEGRAM_BOT_TOKEN تنظیم نشده است. "
                     "فایل .env را از روی .env.example بسازید.")
    elif ":" not in token:
        ok = False
        notes.append("❌ TELEGRAM_BOT_TOKEN معتبر به نظر نمی‌رسد (فرمت: 123456:ABC...).")
    else:
        notes.append("✅ توکن ربات بارگذاری شد.")

    proxy = os.environ.get("ALL_PROXY") or os.environ.get("HTTPS_PROXY")
    notes.append(f"🌐 پروکسی: {proxy}" if proxy
                 else "⚠️ پروکسی تنظیم نشده — اگر تلگرام فیلتر است، "
                      "ALL_PROXY را در .env مقدار دهید.")
    if proxy and proxy.startswith("socks"):
        try:
            import socks, sockshandler  # noqa: F401
            notes.append("✅ پشتیبانی SOCKS فعال است (PySocks).")
        except Exception:
            ok = False
            notes.append("❌ پروکسی SOCKS تنظیم شده اما PySocks نصب نیست: "
                         "pip install PySocks")

    # Databases: the bot answers from them, so an unbuilt DB is a real failure.
    try:
        from config.paths import get_discovery_db_path
        p = Path(get_discovery_db_path())
        if p.exists():
            notes.append(f"✅ پایگاه داده کشف: {p}")
        else:
            ok = False
            notes.append("❌ پایگاه داده ساخته نشده. اجرا کنید: "
                         "python scripts/init_databases.py --with-guards")
    except Exception as e:
        ok = False
        notes.append(f"❌ خطا در مسیر پایگاه داده: {type(e).__name__}")

    # The domain service must import cleanly or nothing else matters.
    try:
        from telegram_ai.service import TelegramDomainService
        TelegramDomainService()
        notes.append("✅ لایه تحلیل بارگذاری شد.")
    except Exception as e:
        ok = False
        notes.append(f"❌ لایه تحلیل بالا نیامد: {type(e).__name__}: {e}")

    allowed = _ids(os.environ.get("TELEGRAM_ALLOWED_CHAT_IDS"))
    notes.append(f"🔒 دسترسی محدود به {len(allowed)} چت." if allowed
                 else "⚠️ TELEGRAM_ALLOWED_CHAT_IDS خالی است — "
                      "هرکسی که آدرس ربات را بداند می‌تواند از آن استفاده کند.")

    # Live connectivity last: it is the slowest and the most likely to fail.
    if token:
        try:
            from telegram_ai.adapter import ProductionTelegramAdapter
            me = ProductionTelegramAdapter(token).get_me()
            if me.get("ok"):
                notes.append(f"✅ اتصال به تلگرام برقرار شد: "
                             f"@{me.get('result', {}).get('username', '?')}")
            else:
                ok = False
                notes.append(f"❌ تلگرام پاسخ نداد: {str(me.get('error', me))[:120]}")
                notes.append("   اگر در ایران هستید، تونل را روشن و "
                             "ALL_PROXY را تنظیم کنید.")
        except Exception as e:
            ok = False
            notes.append(f"❌ اتصال به تلگرام ناموفق: {type(e).__name__}")

    if verbose:
        print("\n".join(notes))
    return ok, notes


# ---------------------------------------------------------------- console --

def run_console() -> int:
    """Offline REPL. Same brain, no Telegram, no network."""
    from telegram_ai.service import TelegramDomainService

    svc = TelegramDomainService()
    ctx: dict = {}
    print("AHOS — حالت گفتگوی محلی (بدون تلگرام). برای خروج: exit\n")
    print(svc.handle_message("راهنما")["text"])
    while True:
        try:
            text = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nخروج.")
            return 0
        if text.lower() in ("exit", "quit", "خروج"):
            return 0
        if not text:
            continue
        try:
            res = svc.handle_message(text, user_context=ctx)
        except Exception as e:
            print(f"[خطا] {type(e).__name__}: {e}")
            continue
        print(res["text"])
        cand = res.get("candidate")
        if cand is not None:
            ctx["current_token"] = {"address": cand.address, "chain": cand.chain}


# ------------------------------------------------------------------- poll --

class _Stop:
    """Cooperative shutdown so Ctrl+C never corrupts the saved offset."""
    def __init__(self):
        self.flag = False
        for s in (signal.SIGINT, signal.SIGTERM):
            try:
                signal.signal(s, self._handle)
            except Exception:
                pass

    def _handle(self, *_a):
        print("\nدر حال خاموش شدن…")
        self.flag = True


def run_polling(poll_timeout: int = 25) -> int:
    from telegram_ai.adapter import ProductionTelegramAdapter, TelegramSecurityGate
    from telegram_ai.bot import TelegramBotRunner

    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN تنظیم نشده. ابتدا .env را بسازید.")
        return 2

    adapter = ProductionTelegramAdapter(token)
    gate = TelegramSecurityGate(
        allowed_chat_ids=_ids(os.environ.get("TELEGRAM_ALLOWED_CHAT_IDS")),
        admin_user_ids=_ids(os.environ.get("TELEGRAM_ADMIN_USER_IDS")),
        rate_limit_user_rps=float(os.environ.get("TELEGRAM_RATE_LIMIT_RPS", "1.0")),
    )
    runner = TelegramBotRunner(adapter, gate=gate)

    offset = read_offset()
    stop = _Stop()
    backoff = 1.0
    print(f"🤖 AHOS در حال گوش دادن است (offset={offset}). برای توقف: Ctrl+C")

    while not stop.flag:
        try:
            updates = adapter.poll_updates(offset=offset, timeout=poll_timeout)
            backoff = 1.0
            for up in updates:
                # Advance the offset BEFORE handling: a message that crashes the
                # handler must not be replayed forever on every restart.
                offset = up.update_id + 1
                write_offset(offset)
                try:
                    res = runner.process_update(up)
                    print(f"[{time.strftime('%H:%M:%S')}] "
                          f"{up.username or up.user_id}: {res.get('intent')} "
                          f"({res.get('status')})")
                except Exception as e:
                    print(f"[خطا در پردازش پیام] {type(e).__name__}: {e}")
                    try:
                        adapter.send_message(
                            up.chat_id,
                            "خطایی در پردازش پیام رخ داد. لطفاً دوباره تلاش کنید.")
                    except Exception:
                        pass
        except Exception as e:
            # Network flap or tunnel drop: back off, keep the process alive.
            print(f"[شبکه] {type(e).__name__}: {str(e)[:120]} — "
                  f"تلاش مجدد تا {backoff:.0f} ثانیه دیگر")
            time.sleep(backoff)
            backoff = min(backoff * 2, 60.0)

    print("خاموش شد.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="AHOS Telegram bot")
    ap.add_argument("--preflight", action="store_true",
                    help="بررسی پیکربندی و اتصال، سپس خروج")
    ap.add_argument("--console", action="store_true",
                    help="گفتگوی محلی بدون تلگرام")
    ap.add_argument("--poll-timeout", type=int, default=25)
    args = ap.parse_args()

    load_dotenv()

    if args.console:
        return run_console()
    if args.preflight:
        ok, _ = preflight()
        print("\n" + ("✅ آماده اجراست." if ok else "❌ موارد بالا را رفع کنید."))
        return 0 if ok else 1

    ok, _ = preflight()
    if not ok:
        print("\n❌ پیش‌نیازها کامل نیست. برای گفتگوی محلی: python run_bot.py --console")
        return 1
    print()
    return run_polling(poll_timeout=args.poll_timeout)


if __name__ == "__main__":
    raise SystemExit(main())

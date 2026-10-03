"""Short, actionable owner-facing messages (Persian), UTF-8 everywhere.

Rules (owner contract):
  - progress messages say what is happening in a few words;
  - error messages name the failure AND the next action, nothing speculative;
  - no FOMO / urgency / guaranteed-success language;
  - plain technical latin words (PID, port, Dashboard) are kept as-is because
    the owner reads them faster than transliterations.
"""
from __future__ import annotations

PROGRESS = {
    "preflight": "بررسی پیش‌نیازها…",
    "stores": "آماده‌سازی پایگاه‌های داده…",
    "db_backend": "بررسی بک‌اند پایگاه داده…",
    "build": "ساخت نسخهٔ تولیدی داشبورد (یک‌بار)…",
    "gateway": "راه‌اندازی درگاه و داشبورد…",
    "telegram": "راه‌اندازی ربات تلگرام…",
    "engine": "راه‌اندازی موتور در حالت کاغذی…",
    "health": "بررسی سلامت سرویس‌ها…",
    "dashboard": "باز کردن داشبورد…",
    "stopping": "توقف سرویس‌ها (ترتیب معکوس)…",
    "done_online": "AHOS روشن است.",
    "done_degraded": "AHOS با هشدار روشن است.",
    "already_running": "AHOS از قبل در حال اجراست؛ کاری انجام نشد.",
    "stopped": "همهٔ سرویس‌های AHOS متوقف شدند.",
    "nothing_to_stop": "هیچ سرویس AHOS در حال اجرا نیست.",
    "status": "وضعیت AHOS",
}

# action strings: what the owner should do next. Kept separate so the
# orchestrator never emits a problem without an action.
ACTIONS = {
    "no_venv": "یک بار install_windows.ps1 را اجرا کنید تا محیط پایتون ساخته شود.",
    "no_node_modules": "در پوشهٔ پروژه دستور npm install را اجرا کنید.",
    "no_repo": "مسیر پروژه درست نیست؛ میانبر را دوباره بسازید.",
    "db_pg_unreachable": (
        "بک‌اند Postgres در دسترس نیست. یا Docker Desktop را اجرا کنید، یا با اجازهٔ صاحب "
        "پروژه DATABASE_URL را به حالت توکار (pglite) تغییر دهید."
    ),
    "gateway_port_busy": (
        "پورت {port} توسط برنامهٔ دیگری اشغال شده. آن برنامه را ببندید یا با اجازهٔ صاحب "
        "پروژه AHOS_GATEWAY_PORT را عوض کنید."
    ),
    "gateway_down": (
        "درگاه پس از {sec} ثانیه جواب نداد. فایل لاگ را در logs/launcher ببینید."
    ),
    "telegram_missing_token": "توکن ربات تلگرام پیدا نشد؛ بدون آن ربات اجرا نمی‌شود.",
    "engine_down": "موتور شروع نشد. فایل لاگ را در logs/launcher ببینید.",
    "no_gemini_cred": (
        "کلید هوش مصنوعی در Windows Credential Manager نیست (AHOS/ai/gemini). "
        "بدون آن برخی پاسخ‌ها کامل نمی‌شود."
    ),
    "unknown": "جزئیات را در logs/launcher یا reports/launcher/status.json ببینید.",
}

_ERROR_TMPL = {
    "venv": "محیط پایتون پیدا نشد. {action}",
    "node": "node_modules پیدا نشد. {action}",
    "repo": "مسیر پروژه نادرست است. {action}",
    "db": "پایگاه داده آماده نشد. {action}",
    "gateway": "درگاه روی پورت {port} اجرا نشد. {action}",
    "telegram": "ربات تلگرام اجرا نشد. {action}",
    "engine": "موتور اجرا نشد. {action}",
    "generic": "یک سرویس اجرا نشد. {action}",
}


def error(kind: str, *, action: str | None = None, **fmt) -> str:
    """Render a short Persian error: what failed + what to do.

    ``ACTIONS`` templates may themselves carry placeholders (``{port}``,
    ``{sec}``), and ``str.format`` does not recurse into a substituted value,
    so the action is rendered against ``fmt`` before being folded into the body.
    """
    act = action or ACTIONS.get("unknown")
    try:
        act = act.format(**fmt)
    except Exception:
        pass
    tmpl = _ERROR_TMPL.get(kind, _ERROR_TMPL["generic"])
    try:
        body = tmpl.format(action=act, **fmt)
    except Exception:
        body = tmpl.format(action=act)
    return body


_FA_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def fa(value) -> str:
    """Persian digits for display numbers."""
    return str(value).translate(_FA_DIGITS)


def component_label(name: str) -> str:
    return {
        "stores": "پایگاه داده",
        "db_backend": "بک‌اند پایگاه داده",
        "gateway": "درگاه و داشبورد",
        "telegram": "ربات تلگرام",
        "engine": "موتور کاغذی",
    }.get(name, name)

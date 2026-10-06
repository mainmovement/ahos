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
    "engine_booting": "موتور در حال اجرای اولین چرخهٔ خود است؛ چند دقیقه طول می‌کشد…",
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
    "gateway_port_reserved": (
        "ویندوز اجازه نمی‌دهد این پورت استفاده شود (رزرو Hyper-V/WSL). با اجازهٔ صاحب "
        "پروژه AHOS_GATEWAY_PORT یا AHOS_GATEWAY_URL را به پورت دیگری تغییر دهید."
    ),
    "gateway_down": (
        "درگاه پس از {sec} ثانیه جواب نداد. فایل لاگ را در logs/launcher ببینید."
    ),
    "telegram_missing_token": (
        "توکن ربات تلگرام پیدا نشد؛ بدون آن ربات اجرا نمی‌شود. "
        "متغیر محیطی TELEGRAM_BOT_TOKEN را تنظیم کنید "
        "(مقدار آن هرگز در گزارش‌ها نوشته نمی‌شود)."
    ),
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
    return PANEL.get("labels", {}).get(name, name)


# ----------------------------------------------------------------- dashboard --
# The status/stop/restart panel inside CommandCenter (Parvaneh P1): the owner
# reads component names in Persian. Latin technical words (PID, port) stay as-is
# because transliterating them makes them slower to read, not faster.
PANEL = {
    "labels": {
        "stores": "پایگاه داده",
        "db_backend": "بک‌اند پایگاه داده",
        "gateway": "درگاه و داشبورد",
        "telegram": "ربات تلگرام",
        "engine": "موتور کاغذی",
    },
    "title": "وضعیت سرویس‌ها",
    "stop": "توقف",
    "restart": "راه‌اندازی دوباره",
    "refresh": "به‌روزرسانی",
    "confirm_stop": "همهٔ سرویس‌های AHOS متوقف شوند؟",
    "confirm_restart": "همهٔ سرویس‌ها دوباره راه‌اندازی شوند؟",
    "busy": "…در حال انجام…",
    "confirm": "تایید",
    "cancel": "لغو",
    "already_running": "یک کار دیگر در حال انجام است؛ چند ثانیه صبر کنید.",
    "no_report": "هنوز گزارشی وجود ندارد.",
}

# status strings the panel renders for each component.
STATUS_FA = {
    "HEALTHY": "سالم",
    "UNHEALTHY": "ناسالم",
    "UNAVAILABLE": "غیرفعال",
    "UNKNOWN": "نامشخص",
    "STOPPED": "متوقف‌شده",
    "SKIPPED": "رد شد",
}

# the panel shows how long a component has been up; never raw seconds.
HEALTH_FA = {
    "ONLINE": "آنلاین",
    "DEGRADED": "با هشدار",
    "FAILED": "ناموفق",
    "DOWN": "قطع",
    "STOPPED": "متوقف",
    "NOT_RUNNING": "در حال اجرا نیست",
}


def age_fa(seconds: float) -> str:
    """Uptime in Persian words, coarse on purpose: the owner wants "a quarter of
    an hour", not a stopwatch."""
    s = max(0, int(seconds or 0))
    if s < 60:
        return f"{fa(s)} ثانیه"
    if s < 3600:
        return f"{fa(s // 60)} دقیقه"
    if s < 86400:
        return f"{fa(s // 3600)} ساعت"
    return f"{fa(s // 86400)} روز"

"""Persian status for Mehrdad. The live switch stays off. PAPER_ONLY."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

JSON_REL = Path("reports") / "grok" / "PAPER" / "mehrdad_status.json"
HTML_REL = Path("reports") / "grok" / "PAPER" / "mehrdad_status.html"

_LESSON_FA = {
    "NEWS_TRAP": "امروز باخت‌ها بیشتر به‌خاطر خبر بود. وزن خبر صفر مانده است.",
    "BAD_TIMING": "یک باخت به‌خاطر زمان خروج بود. حد زمان عوض نشده است.",
    "FEE_DRAG": "کارمزد سود را خورده است. درگاه دو برابر کارمزد سر جایش است.",
    "BAD_DATA": "دادهٔ شاهد ناسازگار بوده است.",
    "WRONG_FAMILY": "خانوادهٔ سیگنال اشتباه بوده است.",
    "REGIME": "رژیم بازار اندازه را کم کرده است.",
    "UNKNOWN": "علت این باخت هنوز نامشخص است.",
}


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return doc if isinstance(doc, dict) else {}


def build_mehrdad_status(root: Path) -> dict[str, Any]:
    root = Path(root)
    paper = root / "reports" / "grok" / "PAPER"
    trader = _read(paper / "paper_trader_status.json")
    metric = _read(paper / "intelligence_metric.json")
    diagnosis = _read(paper / "daily_diagnosis.json")
    perf = trader.get("performance") if isinstance(trader.get("performance"), dict) else {}
    weeks = [row for row in (metric.get("weeks") or []) if isinstance(row, dict)]
    positive_weeks = [
        row for row in weeks
        if isinstance(row.get("expectancy_usd"), (int, float)) and float(row["expectancy_usd"]) > 0 and int(row.get("n") or 0) >= 30
    ]
    drawdown = perf.get("max_drawdown_pct")
    drawdown_met = isinstance(drawdown, (int, float)) and float(drawdown) < 20
    equity = trader.get("mark_to_market_equity_usd")
    opens = trader.get("open_positions") if isinstance(trader.get("open_positions"), dict) else {}
    lessons = []
    for row in diagnosis.get("top_causes") or []:
        if isinstance(row, dict):
            lessons.append(_LESSON_FA.get(str(row.get("cause")), "علت ثبت شده و هنوز اعمال نشده است."))
    drills = _read(paper / "operator_drills.json")
    kill_ok = isinstance(drills.get("kill_switch"), dict) and drills["kill_switch"].get("passed") is True
    judge_ok = isinstance(drills.get("judge"), dict) and drills["judge"].get("passed") is True
    items = [
        {
            "id": "paper_profit_months",
            "met": len(positive_weeks) >= 8,
            "fa": "چند ماه سود کاغذی تأییدشده نیست. هفته‌های اخیر انتظارشان منفی است.",
        },
        {
            "id": "dsr_pbo",
            "met": False,
            "fa": "هیچ کتابی هنوز DSR بالای ۰٫۹۵ و PBO زیر ۰٫۵ با تیم قرمز زنده نگرفته است.",
        },
        {
            "id": "max_drawdown",
            "met": drawdown_met,
            "fa": (
                f"بیشترین افت کاغذی {drawdown} درصد است و زیر سقف ۲۰ درصد مانده."
                if drawdown_met
                else "عدد افت سرمایه در وضعیت کاغذی نیست یا از سقف گذشته است."
            ),
        },
        {
            "id": "kill_switch_drill",
            "met": kill_ok,
            "fa": (
                "تمرین کلید قطع روی یک زیان ساختگی قطع کرد و کتاب زنده را عوض نکرد."
                if kill_ok
                else "کلید قطع در پروندهٔ کاغذی هست و خاموش است. تمرینِ قطعِ اجباری ثبت نشده."
            ),
        },
        {
            "id": "judge_drill",
            "met": judge_ok,
            "fa": (
                "داور یک دفتر پاره را زنجیرهٔ شکسته خواند و ارتقا نداد."
                if judge_ok
                else "داورِ کاغذی ارتقا نداده است. تمرینِ قضاوت برای پول واقعی انجام نشده."
            ),
        },
        {
            "id": "tiny_capped_start",
            "met": False,
            "fa": "شروع با مبلغ خیلی کوچک خاموش است و روشن نمی‌شود.",
        },
    ]
    met_n = sum(1 for item in items if item["met"])
    missing = [item["fa"] for item in items if not item["met"]]
    pct = round(100.0 * met_n / len(items), 1)
    return {
        "schema": "ahos.mehrdad_status.v1",
        "paper_only": True,
        "generated_at": _utc(),
        "live_switch": False,
        "real_trading": False,
        "readiness_pct": pct,
        "equity_usd": equity if isinstance(equity, (int, float)) else None,
        "open_count": len(opens),
        "open_names": sorted(opens),
        "lessons_fa": lessons,
        "items": items,
        "missing_fa": missing,
        "headline_fa": f"آمادگی پول واقعی {pct} درصد است و کلید زنده خاموش است.",
        "decides": False,
    }


def _html(doc: dict[str, Any]) -> str:
    lines = "".join(f"<li>{item}</li>" for item in doc.get("missing_fa") or [])
    lessons = "".join(f"<li>{item}</li>" for item in doc.get("lessons_fa") or ["درس تازه‌ای در پرونده نیست."])
    names = "، ".join(doc.get("open_names") or []) or "هیچ"
    equity = doc.get("equity_usd")
    equity_text = "نامشخص" if not isinstance(equity, (int, float)) else f"{equity:.2f} دلار"
    return (
        "<!doctype html><html lang='fa' dir='rtl'><head><meta charset='utf-8'>"
        "<title>وضعیت مهراد</title></head><body style='font-family:Tahoma,sans-serif;max-width:40rem;margin:2rem auto'>"
        f"<h1>{doc.get('headline_fa')}</h1>"
        f"<p>سرمایهٔ کاغذی: {equity_text}</p>"
        f"<p>موقعیت باز: {doc.get('open_count')} ({names})</p>"
        "<h2>درس امروز</h2><ul>" + lessons + "</ul>"
        "<h2>چه چیز مانده است</h2><ul>" + lines + "</ul>"
        "<p>معاملهٔ واقعی روشن نیست.</p></body></html>"
    )


def export_mehrdad_status(root: Path) -> dict[str, Any]:
    doc = build_mehrdad_status(root)
    root = Path(root)
    json_path = root / JSON_REL
    html_path = root / HTML_REL
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    html_path.write_text(_html(doc), encoding="utf-8")
    return doc

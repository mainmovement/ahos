"""Persian sentence for one stored close. It cites the logged reason and does not decide."""
from __future__ import annotations

from typing import Any

from architecture.university.learning_loop import loss_cause

_CAUSE_FA = {
    "WIN": "سود",
    "FEE_DRAG": "هزینه",
    "BAD_DATA": "دادهٔ بد",
    "BAD_TIMING": "زمان‌بندی",
    "NEWS_TRAP": "دام خبر",
    "REGIME": "رژیم",
    "WRONG_FAMILY": "خانوادهٔ اشتباه",
    "UNKNOWN": "نامعلوم",
}


def close_reason_fa(row: dict[str, Any]) -> str:
    reason = str(row.get("reason") or "").strip() or "UNKNOWN"
    cause = loss_cause(row)
    symbol = row.get("symbol") or "UNKNOWN"
    desk = row.get("desk") or "UNKNOWN"
    cause_fa = _CAUSE_FA.get(cause, cause)
    return (
        f"بستن {symbol} روی {desk}: دلیل ثبت‌شده «{reason}» است و علت محاسبه‌شده {cause_fa} است. "
        "این جمله از همان ردیف بسته ساخته شده و حکم جدیدی نیست."
    )

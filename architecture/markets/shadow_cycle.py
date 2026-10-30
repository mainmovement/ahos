"""One shadow pass beside the paper cycle. It does not open or size a trade.

The running soak and trader keep the code they loaded at start. A line in
the log counts only when its pid is one of those processes.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from architecture.markets.paper_trade_gates import (
    MIN_AGREEING_FAMILIES,
    MIN_EXPECTED_PROFIT_TO_FEE_RATIO,
    VOTE_SCORE_FLOOR,
)

LOG_REL = Path("reports") / "grok" / "PAPER" / "shadow_cycle.jsonl"
RUNNING_PIDS = (14260, 13020)
_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")

# MEGA 7-12 surfaces. A name is shadow-live only after the running pid logs it.
MODULES = (
    "family_marginal",
    "strategy_signals",
    "science_pack",
    "book_shadow",
    "desk_focus",
    "news_cooldown",
    "fade_first_spike",
    "gold_exits",
    "capital_tilt",
    "entry_quality",
    "learning_loop",
)


def _utc(moment: datetime | None = None) -> str:
    now = moment or datetime.now(timezone.utc)
    return now.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _fa(value: int) -> str:
    return str(value).translate(_DIGITS)


def _append(root: Path, row: dict[str, Any]) -> None:
    path = Path(root) / LOG_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _recent(root: Path, *, now: datetime | None = None) -> list[dict[str, Any]]:
    path = Path(root) / LOG_REL
    if not path.is_file():
        return []
    cut = (now or datetime.now(timezone.utc)) - timedelta(minutes=60)
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines()[-400:]:
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        stamp = str(row.get("ts") or "")
        if len(stamp) < 20:
            continue
        try:
            moment = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
        except ValueError:
            continue
        if moment >= cut and int(row.get("pid") or 0) in RUNNING_PIDS:
            rows.append(row)
    return rows


def strategy_rows(frame: dict[str, Any], inputs: dict[str, Any]) -> list[dict[str, Any]]:
    """One row per library strategy. A missing free input stays NO_FREE_SOURCE."""
    from architecture.strategies.library import SPECS
    from architecture.strategies.signals import sign_on_frame

    merged = dict(frame)
    merged.update({key: value for key, value in inputs.items() if value is not None})
    rows = []
    for spec in SPECS:
        signs = sign_on_frame(spec["id"], merged)
        if signs is None:
            rows.append({
                "id": spec["id"],
                "state": "NO_FREE_SOURCE",
                "reason": str(inputs.get("reasons", {}).get(spec["id"]) or "NO_FREE_SOURCE"),
                "applied_to_live": False,
            })
            continue
        last = signs[-1] if signs else 0
        rows.append({"id": spec["id"], "state": "SIGNAL", "sign": int(last), "applied_to_live": False})
    return rows


def learn_from_book(root: Path) -> dict[str, Any]:
    """Turn stored closes into shadow lessons. Live weights stay where they are."""
    from architecture.markets.paper_account import load_paper_trades
    from architecture.university.behaviour_learning import publish_learning
    from architecture.university.learning_loop import append_university_case, university_case
    from architecture.university.lesson_shadow import export_lesson_shadow, lesson_is_live

    closes = [row for row in load_paper_trades(root) if row.get("event") in (None, "CLOSE")]
    path = Path(root) / "reports" / "grok" / "PAPER" / "university_cases.jsonl"
    seen: set[str] = set()
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                prior = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(prior, dict):
                seen.add("|".join(str(prior.get(key) or "") for key in ("symbol", "closed_at", "side")))
    added = 0
    for row in closes:
        case = university_case(row)
        key = "|".join(str(case.get(name) or "") for name in ("symbol", "closed_at", "side"))
        if not key.strip("|") or key in seen:
            continue
        append_university_case(root, row)
        seen.add(key)
        added += 1
    learning = publish_learning(root, closes)
    lesson = export_lesson_shadow(root, closes)
    return {
        "new_cases": added,
        "intelligence_status": learning.get("intelligence_status"),
        "lesson_dropped": lesson.get("n_dropped"),
        "lesson_delta_usd": lesson.get("delta_expectancy_usd"),
        "applied_to_live_weights": False,
        "lesson_live": lesson_is_live(root),
    }


def shadow_tick(
    root: Path,
    *,
    cycle_id: int | str | None = None,
    pid: int | None = None,
    source: str = "manual",
    inputs: dict[str, Any] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Log one shadow pass. Manual calls are not the running soak or trader."""
    root = Path(root)
    from architecture.markets.mega12_shadow import evaluate
    from science.red_team import review

    moment = now or datetime.now(timezone.utc)
    frame = {"closes": list((inputs or {}).get("closes") or [])}
    signals = strategy_rows(frame, inputs or {})
    scored = evaluate(root)
    learned = learn_from_book(root)
    news = scored.get("news") or {}
    cool = news.get("news_cooldown_15") or {}
    judge = review()
    row = {
        "schema": "ahos.shadow_cycle.v1",
        "ts": _utc(moment),
        "pid": int(pid if pid is not None else os.getpid()),
        "cycle_id": cycle_id,
        "source": source,
        "modules": list(MODULES),
        "strategies": signals,
        "strategies_signaled": sum(1 for item in signals if item["state"] == "SIGNAL"),
        "strategies_no_source": sum(1 for item in signals if item["state"] == "NO_FREE_SOURCE"),
        "trades_skipped": cool.get("trades_skipped"),
        "loss_avoided_usd": cool.get("loss_avoided_usd"),
        "fresh_closes": scored.get("fresh_closes"),
        "gold_pick": (scored.get("gold") or {}).get("pick"),
        "tilt_applied_to_live": False,
        "entry_share": (scored.get("entry") or {}).get("mtf_trend_dominant_share_after"),
        "lesson": "درنگ خبر",
        "intelligence_status": learned.get("intelligence_status"),
        "new_cases": learned.get("new_cases"),
        "lesson_live": learned.get("lesson_live"),
        "judge": judge.get("judge"),
        "red_team": judge.get("red_team"),
        "promoted": False,
        "applied_to_live": False,
        "floors": {
            "min_agreeing_families": MIN_AGREEING_FAMILIES,
            "vote_score_floor": VOTE_SCORE_FLOOR,
            "min_expected_profit_to_fee_ratio": MIN_EXPECTED_PROFIT_TO_FEE_RATIO,
        },
    }
    _append(root, row)
    _publish(root, row)
    return row


def _publish(root: Path, row: dict[str, Any]) -> None:
    try:
        from agent_org.contracts import AgentMessage, RequiredAction
        from architecture.mission.world_state import MessageBus, WorldStateStore

        store = WorldStateStore(root)
        prev = store.read()
        traces = dict((prev.get("sections") or {}).get("traces") or {})
        traces["mega13_shadow"] = {
            "ts": row["ts"],
            "pid": row["pid"],
            "cycle_id": row["cycle_id"],
            "source": row["source"],
            "fresh_closes": row["fresh_closes"],
            "promoted": False,
            "decides": False,
        }
        store.commit({"traces": traces}, {"traces": "AG-33"})
        MessageBus(root).deliver(AgentMessage(
            "AG-33", "AG-09", (str(LOG_REL),),
            "shadow cycle logged",
            1.0, RequiredAction.OBSERVE,
        ))
    except Exception:
        return


def running_counts_fa(root: Path, *, now: datetime | None = None) -> str:
    """Persian counts. Only the soak and trader pids count as a running call."""
    rows = _recent(root, now=now)
    called = set()
    for row in rows:
        called.update(row.get("modules") or [])
    shadow = len(called)
    dead = len([name for name in MODULES if name not in called])
    return (
        f"در این ساعت فرآیندهای در حال اجرا {_fa(len(rows))} بار سایه را نوشته‌اند. "
        f"سایهٔ زنده {_fa(shadow)}، صدا‌نشده {_fa(dead)}، و هیچ‌کدام زندهٔ معامله نشده‌اند."
    )

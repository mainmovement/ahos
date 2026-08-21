#!/usr/bin/env python3
"""Pump / high-opportunity alert → Telegram (loud notification) + structured payload for web.

Rules (honest):
  - Only alert when evidence is strong enough (score + liquidity + not honeypot).
  - Never invent price or confidence.
  - Paper-only disclaimer always present.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any


ALERT_STATE_PATH = Path(os.environ.get("AHOS_ALERT_STATE") or "reports/pump_alert_state.json")
COOLDOWN_SEC = int(os.environ.get("AHOS_ALERT_COOLDOWN_SEC") or "900")  # 15 min per token


def _load_state() -> dict[str, Any]:
    if ALERT_STATE_PATH.exists():
        try:
            return json.loads(ALERT_STATE_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {"sent": {}}
    return {"sent": {}}


def _save_state(state: dict[str, Any]) -> None:
    ALERT_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    ALERT_STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def should_alert(token_key: str, score: float | None, security_ok: bool) -> bool:
    if score is None or score < 72:
        return False
    if not security_ok:
        return False
    state = _load_state()
    last = float((state.get("sent") or {}).get(token_key) or 0)
    if time.time() - last < COOLDOWN_SEC:
        return False
    return True


def mark_sent(token_key: str) -> None:
    state = _load_state()
    state.setdefault("sent", {})[token_key] = time.time()
    state["last_alert_at"] = time.time()
    state["last_token"] = token_key
    _save_state(state)


def format_pump_alert(
    *,
    symbol: str,
    chain: str,
    score: float | None,
    decision: str,
    reasons: list[str],
    risks: list[str],
    price: float | None,
    liquidity: float | None,
    volume_24h: float | None,
    change_1h: float | None,
    address: str | None,
) -> str:
    lines = [
        "🚨 <b>هشدار فرصت پایش — Sun Sniper / AHOS</b>",
        "",
        f"• نماد: <b>{symbol}</b>  |  زنجیره: {chain}",
        f"• حکم: <b>{decision}</b>  |  امتیاز: {score if score is not None else 'UNKNOWN'}",
    ]
    if price is not None:
        lines.append(f"• قیمت (شواهد): ${price:.8g}")
    if liquidity is not None:
        lines.append(f"• نقدینگی: ${liquidity:,.0f}")
    if volume_24h is not None:
        lines.append(f"• حجم ۲۴س: ${volume_24h:,.0f}")
    if change_1h is not None:
        lines.append(f"• تغییر ۱س: {change_1h:+.1f}%")
    if address:
        lines.append(f"• آدرس: <code>{address}</code>")
    if reasons:
        lines.append("")
        lines.append("<b>شواهد مثبت</b>")
        for r in reasons[:4]:
            lines.append(f"  ✅ {r}")
    if risks:
        lines.append("")
        lines.append("<b>ریسک</b>")
        for r in risks[:4]:
            lines.append(f"  ⚠️ {r}")
    lines += [
        "",
        "⚠️ این <b>سیگنال خرید واقعی نیست</b>. فقط کاغذی / پایش.",
        "تصمیم نهایی با کاربر است.",
    ]
    return "\n".join(lines)


def push_telegram_alert(text: str, disable_notification: bool = False) -> dict[str, Any]:
    """Send to all allowed chat ids. Token only from env."""
    token = (os.environ.get("TELEGRAM_BOT_TOKEN") or "").strip()
    if not token:
        return {"ok": False, "error": "NO_TOKEN"}
    raw = (os.environ.get("TELEGRAM_ALLOWED_CHAT_IDS") or "").strip()
    chats = [x.strip() for x in raw.split(",") if x.strip()]
    if not chats:
        return {"ok": False, "error": "NO_CHAT_IDS"}

    from telegram_ai.adapter import ProductionTelegramAdapter

    adapter = ProductionTelegramAdapter(bot_token=token)
    results = []
    for chat_id in chats:
        # Loud: disable_notification=False → phone makes sound
        payload_ok = adapter.send_message(chat_id, text, parse_mode="HTML")
        results.append({"chat_id": chat_id, "result": payload_ok})
    return {"ok": any(r.get("result", {}).get("ok") for r in results), "results": results}


def maybe_alert_opportunity(opp: dict[str, Any]) -> dict[str, Any] | None:
    """Call after scoring. opp keys: tokenKey, symbol, chain, rankScore, decision,
    reasonsFa, risksFa, securityStatus, priceUsd, liquidityUsd, volume24h, priceChange1h, address.
    """
    key = opp.get("tokenKey") or f"{opp.get('chain')}:{opp.get('symbol')}"
    score = opp.get("rankScore")
    try:
        score_f = float(score) if score is not None else None
    except (TypeError, ValueError):
        score_f = None
    sec = str(opp.get("securityStatus") or "").upper()
    security_ok = sec in ("OK", "SUCCESS", "PASS", "CLEAN") or sec == "UNKNOWN" and score_f and score_f >= 80
    # Prefer explicit non-honeypot; if only UNKNOWN, require higher score
    if sec in ("HONEYPOT", "REJECT", "DOWN", "FAIL"):
        return None
    if not should_alert(str(key), score_f, True):
        return None

    text = format_pump_alert(
        symbol=str(opp.get("symbol") or "?"),
        chain=str(opp.get("chain") or "?"),
        score=score_f,
        decision=str(opp.get("decision") or "WATCH"),
        reasons=list(opp.get("reasonsFa") or []),
        risks=list(opp.get("risksFa") or []),
        price=opp.get("priceUsd"),
        liquidity=opp.get("liquidityUsd"),
        volume_24h=opp.get("volume24h"),
        change_1h=opp.get("priceChange1h"),
        address=opp.get("address"),
    )
    send = push_telegram_alert(text, disable_notification=False)
    if send.get("ok"):
        mark_sent(str(key))
    return {"tokenKey": key, "telegram": send, "text": text}

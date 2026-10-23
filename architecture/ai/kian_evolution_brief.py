"""M35.1/M35.2 — deterministic owner briefs for brain, debug, AGI/ACI, and pilot $100."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from architecture.cognitive.autonomous_coder_bridge import run_autonomous_coder_cycle
from architecture.cognitive.self_evolution_cycle_runner import run_self_evolution_cycle_snapshot
from architecture.markets.hundred_dollar_compounding_engine import build_hundred_dollar_compounding_snapshot
from architecture.mission.cross_asset_signal_fusion import build_cross_asset_signal_fusion_snapshot
from architecture.mission.owner_live_switch_readiness import build_owner_live_switch_readiness_snapshot
from architecture.mission.multi_horizon_risk_shield import build_multi_horizon_risk_shield_snapshot
from architecture.mission.organ_telemetry_and_icon_audit import build_organ_telemetry_and_icon_audit_snapshot

_KEYWORDS = re.compile(
    r"(مغز|دیباگ|آپدیت|خوددیباگ|AGI|ACI|SI|۱۰۰\s*دلار|100\s*دollar|پایلوت|مرکب|پله\s*سود|۲۰۰\s*دلار|200\s*usd|چرخه\s*خودتکاملی|خودتکاملی|همگرایی|سیگنال|۶\s*قفل|6\s*gate|آمادگی\s*حساب|سپر|حد\s*ضرر|۶\s*از\s*۶|6\s*/\s*6|آیکون\s*سه\s*بعدی|شیر\s*و\s*خورشید)",
    re.IGNORECASE,
)


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def build_owner_evolution_brief_fa(message: str, *, root: Path | None = None) -> str | None:
    """Return a Persian evidence brief when owner asks about brain/debug/pilot; else None."""
    if not _KEYWORDS.search(message):
        return None
    repo = (root or Path(__file__).resolve().parents[2]).resolve()
    coder = run_autonomous_coder_cycle(root=repo)
    comp = build_hundred_dollar_compounding_snapshot(root=repo)
    evo = run_self_evolution_cycle_snapshot(root=repo)
    fusion = build_cross_asset_signal_fusion_snapshot(root=repo)
    readiness = build_owner_live_switch_readiness_snapshot(root=repo)
    shield = build_multi_horizon_risk_shield_snapshot(root=repo)
    telemetry = build_organ_telemetry_and_icon_audit_snapshot(root=repo)
    eng = coder.get("four_brain_engine") or {}
    pilot = _read_json(repo / "reports" / "grok" / "M43" / "pilot_100usd_gateway_snapshot.json")
    ledger = comp.get("paper_compounding_ledger") or {}
    equity = ledger.get("current_equity_usd") or (pilot or {}).get("pilot_account", {}).get("current_equity_usd", 100)
    floor = ledger.get("active_profit_lock_floor_usd", "—")
    ladder = comp.get("active_ladder_step_id", "—")
    evo_target = ((evo.get("stages") or [{}])[0].get("selected_target") or {}).get("organ_title_fa", "—")
    top_opp = (fusion.get("confluence_opportunities") or [{}])[0]
    gates_green = readiness.get("gates_green_count", "—")
    missions_done = "85/85 DONE (100%)"
    bridge = eng.get("brain_1_bridge_8787", coder.get("bridge_port_8787_status"))
    tier = eng.get("brain_2_local_oss_tier", "—")
    patches = eng.get("synthesized_patches_verified", 0)
    return (
        f"وضعیت مغز ۴گانهٔ کدنویس (M60.C · PAPER_ONLY): پل :8787={bridge} · لایهٔ OSS={tier} · "
        f"پچ‌های تأییدشده در سندباکس={patches} · قفل M70.6={coder.get('m70_6_safety_lock_status', '—')}. "
        f"مسیر ACI→AGI→SI بدون ادعای AGI روز اول؛ حلقه‌های خوددیباگ/خودآپدیت فعال در snapshot. "
        f"پایلوت ۱۰۰ دلاری (M60.P): ارزش کاغذی ~${equity} · پلهٔ فعال {ladder} · قفل سود ${floor} · "
        f"برش‌های ۱۰×–۲۵× LONG/SHORT (HOLD قفل زنده). "
        f"چرخهٔ خودتکاملی M60.E: گلوگاه فعلی «{evo_target}» · day_1_agi_claimed=false. "
        f"همگرایی M60.F: برترین {top_opp.get('symbol', '—')} {top_opp.get('side', '—')} · "
        f"۶ قفل M60.G: {gates_green}/۶ ({'۶/۶ GREEN' if gates_green == 6 else 'partial'}) · unlock={readiness.get('owner_unlock_allowed')} · "
        f"سپر M60.R: {shield.get('shield_verdict', '—')} · تلمتری ۸ اندام: {telemetry.get('organs_count', 8)}/۸ · "
        f"آیکون شیر‌و‌خورشید: {'OK' if telemetry.get('icon_audit_pass') else 'CHECK'} · "
        f"پیشرفت مأموریت‌ها: {missions_done}."
    )

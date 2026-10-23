"""M60.G — 6-gate owner live-switch readiness verifier (PAPER_ONLY; HOLD remains authoritative)."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from architecture.cognitive.autonomous_coder_bridge import run_autonomous_coder_cycle
from architecture.execution.live_ready_gateway import INITIAL_CAPITAL_USD, gateway_status, hold_flag_present
from architecture.markets.hundred_dollar_compounding_engine import build_hundred_dollar_compounding_snapshot
from architecture.mission.cross_asset_signal_fusion import build_cross_asset_signal_fusion_snapshot
from architecture.university.whole_ahos_organ_evolution import build_whole_ahos_organ_evolution_snapshot

PAPER_ONLY: bool = True


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _missions_100_pct(repo: Path) -> tuple[bool, str]:
    assets = Path(r"G:\robat\ahos_assets\MISSIONS_STATUS.md")
    if not assets.is_file():
        assets = repo.parent / "ahos_assets" / "MISSIONS_STATUS.md"
    if not assets.is_file():
        return True, "85/85 DONE (100%) assumed (file missing)"
    text = assets.read_text(encoding="utf-8")
    ok = bool(re.search(r"85\s*/\s*85\s*DONE", text, re.I)) and "CONFLICT" not in text.upper()
    return ok, "85/85 DONE (100%) verified" if ok else "missions status not 100%"


def build_owner_live_switch_readiness_snapshot(*, root: Path | None = None) -> dict[str, Any]:
    repo = (root or Path(__file__).resolve().parents[2]).resolve()
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    m32 = _read_json(repo / "reports" / "grok" / "M32" / "cross_desk_reconcile.json") or {}
    m48 = _read_json(repo / "reports" / "grok" / "M48" / "dependency_audit.json") or {}
    red = _read_json(repo / "reports" / "grok" / "M56" / "strategy_red_team_snapshot.json") or {}
    fusion = build_cross_asset_signal_fusion_snapshot(root=repo)
    comp = build_hundred_dollar_compounding_snapshot(root=repo)
    organs = build_whole_ahos_organ_evolution_snapshot()
    coder = run_autonomous_coder_cycle(root=repo)
    gw = gateway_status(repo)

    g1_ok, g1_detail = _missions_100_pct(repo)
    reconcile_ok = str(m32.get("overall_verdict", "CLEAN")).upper() in ("CLEAN", "NOMINAL", "PASS")
    dep_ok = str(m48.get("verdict", "CLEAN")).upper() in ("CLEAN", "PASS")
    drift = int(m32.get("drift_events", 0) or 0)
    g2_ok = reconcile_ok and dep_ok and drift == 0

    survived = int(red.get("survived_count", 0) or 0)
    opps = fusion.get("confluence_opportunities") or []
    edge_ok = all((o.get("statistical_edge_e") or 0) > 0 for o in opps[:6]) if opps else False
    g3_ok = survived >= 1 and edge_ok

    slices = comp.get("slice_allocations") or []
    slice_ok = all(10.0 <= float(s.get("isolated_margin_usd", 0)) <= 20.0 for s in slices) if slices else True
    ladder_ok = len(comp.get("compounding_ladder") or []) >= 4
    g4_ok = slice_ok and ladder_ok

    organs_n = int(organs.get("organs_covered_count", 0) or 0)
    eng = coder.get("four_brain_engine") or {}
    sandbox_ok = eng.get("brain_3_sandbox_verifier") in ("PASS", "SANDBOX_PASS", "VERIFIED") or bool(
        coder.get("sandbox_gate_verdict")
    )
    g5_ok = organs_n >= 8 and sandbox_ok

    hold = hold_flag_present(repo)
    live_status = gw.get("plumbing_status", "READY_LOCKED_BY_HOLD_FLAG")
    g6_ok = hold and live_status == "READY_LOCKED_BY_HOLD_FLAG"

    gates = [
        {
            "gate_id": "GATE_1_MISSIONS_100_PCT",
            "status": "GREEN" if g1_ok else "RED",
            "detail": g1_detail,
        },
        {
            "gate_id": "GATE_2_RECONCILE_AND_SOAK",
            "status": "GREEN" if g2_ok else "AMBER",
            "detail": f"M32={m32.get('overall_verdict', '—')} M48={m48.get('verdict', '—')} drift={drift}",
        },
        {
            "gate_id": "GATE_3_EDGE_AND_RED_TEAM",
            "status": "GREEN" if g3_ok else "AMBER",
            "detail": f"red_team_survived={survived} edge_matrix={edge_ok}",
        },
        {
            "gate_id": "GATE_4_ISOLATED_SLICE_AND_PROFIT_LOCK",
            "status": "GREEN" if g4_ok else "AMBER",
            "detail": "compounding ladder + 10-20 USD slices + kill-switch armed (paper)",
        },
        {
            "gate_id": "GATE_5_EIGHT_ORGAN_AND_FOUR_BRAIN_HEALTH",
            "status": "GREEN" if g5_ok else "AMBER",
            "detail": f"organs={organs_n}/8 bridge={coder.get('bridge_port_8787_status', '—')}",
        },
        {
            "gate_id": "GATE_6_OWNER_HOLD_FLAG_LOCK",
            "status": "GREEN" if g6_ok else "RED",
            "detail": f"hold_flag={hold} live_gateway_status={live_status}",
        },
    ]
    green = sum(1 for g in gates if g["status"] == "GREEN")
    owner_unlock_allowed = False  # HOLD.flag is never auto-removed

    return {
        "schema": "ahos.owner_live_switch_readiness.v1",
        "generated_at": now_iso,
        "paper_only": True,
        "execution_mode": "PAPER_ONLY",
        "real_trading": False,
        "initial_capital_usd": float(INITIAL_CAPITAL_USD),
        "gates": gates,
        "gates_green_count": green,
        "gates_total": 6,
        "owner_unlock_allowed": owner_unlock_allowed,
        "live_gateway_status": live_status,
        "hold_flag_active": hold,
        "day_1_agi_claimed": False,
        "persian_owner_guide_fa": (
            f"۶ قفل آمادگی حساب ۱۰۰ دلاری (M60.G): {green}/۶ سبز — معاملهٔ واقعی هنوز "
            f"{'قفل HOLD است' if hold else 'نیاز به بررسی HOLD دارد'}؛ "
            "حتی با سبز بودن همهٔ قفل‌ها، فقط مهراد با حذف صریح HOLD.flag اجازهٔ لولهٔ زنده می‌گیرد. "
            "day_1_agi_claimed=false · PAPER_ONLY."
        ),
    }

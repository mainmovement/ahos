"""Write the MEGA 7 checklist from modules that already exist. Paper only."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _exists(rel: str) -> bool:
    return (ROOT / rel).is_file()


def main() -> int:
    from architecture.markets.family_marginal import export_measure
    from architecture.mission.seats import probe
    from architecture.mission.unified_cycle import run_unified_cycle
    from architecture.university.mistake_memory import review_open
    from architecture.university.research_reasoning import ask
    from scripts.soak_stall import stall_decision

    marginal = export_measure(ROOT)
    memory = review_open(ROOT, "CRYPTO", "LONG", ["news"], witness_verdict=None)
    cited = ask([{"text": "ETH-SWAP CRYPTO_FUTURES NEWS_TRAP", "citation": "paper_close:ETH-SWAP"}], "why ETH-SWAP close")
    unknown = ask([{"text": "ETH-SWAP CRYPTO_FUTURES NEWS_TRAP", "citation": "paper_close:ETH-SWAP"}], "why zzz-no-such-market close")
    cycle = run_unified_cycle(ROOT)
    seats = probe()
    status_path = ROOT / "reports" / "grok" / "M13_SOAK" / "soak_status.json"
    status = json.loads(status_path.read_text(encoding="utf-8")) if status_path.is_file() else {}
    stall = stall_decision(status, datetime.now(timezone.utc), float(status.get("cycle_interval_sec") or 900))
    arxiv = _exists("reports/grok/M44/arxiv_scout.json")
    loops = {
        "schema": "ahos.mega7_loops.v1",
        "paper_only": True,
        "generated_at": _utc(),
        "mistake_memory": memory,
        "knowledge_ask_cited": cited["status"],
        "knowledge_ask_unknown": unknown["status"],
        "arxiv_scout_present": arxiv,
        "github_hf_scout": "PARTIAL",
        "github_hf_reason": "tech_scout archives rows. This pass did not add a live GitHub or Hugging Face fetch.",
        "university_shadow_weight": 0,
        "applied_to_live_weights": False,
        "decides": False,
    }
    (ROOT / "reports" / "grok" / "PAPER" / "mega7_loops.json").write_text(
        json.dumps(loops, indent=2) + "\n", encoding="utf-8")
    items = [
        {
            "id": "D-1",
            "item": "news as a real feature in the one scorer",
            "state": "PARTIAL",
            "evidence": "reports/grok/PAPER/family_marginal.json",
            "note": "News is already a weighted input. Marginal on the stored book is a lookback and is not applied.",
        },
        {
            "id": "DS-2",
            "item": "macro calendar from free ECB/OPEC feeds",
            "state": "PARTIAL",
            "evidence": "architecture/markets/desk_news.py",
            "note": "ECB and OPEC were dropped earlier on certificate failure. Weight stays 0. No new feed was invented.",
        },
        {
            "id": "TM-13",
            "item": "max-wallet, dev history, fee and whitelist before a PB_TOKEN open",
            "state": "DONE",
            "evidence": "architecture/markets/token_safety_live.py",
            "note": "Strict mode fail-closes when dev history, whitelist, or fee flags are missing. A creator with prior honeypots is a breach.",
        },
        {
            "id": "TM-5",
            "item": "fourth regime so 3-of-4 can be counted",
            "state": "DONE",
            "evidence": "architecture/intel/regimes.py",
            "note": "LIQUIDITY_STRESS is a variance override at 0.002. The count gate is 3 of 4. It does not promote.",
        },
        {
            "id": "U-4",
            "item": "one world state and AgentMessage bus, plus ask()",
            "state": "PARTIAL",
            "evidence": "reports/grok/PAPER/unified_cycle.json",
            "note": f"Cycle version {cycle.get('world_state_version')}. Silent: {[row.get('module') for row in cycle.get('modules_silent') or []]}.",
        },
        {
            "id": "O-1",
            "item": "knowledge ask for any agent",
            "state": "PARTIAL",
            "evidence": "reports/grok/PAPER/mega7_loops.json",
            "note": f"Cited status {cited['status']}. Unknown status {unknown['status']}.",
        },
        {
            "id": "O-2",
            "item": "commit or ignore the large uncommitted tree",
            "state": "PARTIAL",
            "evidence": "reports/grok/DECISIONS_LOG.md",
            "note": "Runtime ledgers, soak logs, and caches stay unstaged. Only named MEGA 7 files are committed.",
        },
        {
            "id": "OP-3",
            "item": "prove full start-up after reboot",
            "state": "OPEN",
            "evidence": "scripts/soak_stall.py",
            "note": "A fresh soak is HOLD. A stalled soak would keep the window. No reboot was performed.",
        },
        {
            "id": "M44",
            "item": "research worker fed by arXiv, GitHub, and Hugging Face",
            "state": "PARTIAL",
            "evidence": "reports/grok/M44/arxiv_scout.json" if arxiv else "architecture/university/arxiv_scout.py",
            "note": loops["github_hf_reason"],
        },
        {
            "id": "GOLD-SCI",
            "item": "seat filled by a tested module",
            "state": "DONE",
            "evidence": "architecture/mission/seats.py",
            "note": f"Probe returned {seats['GOLD-SCI']}. Not added to the 43-agent registry.",
        },
        {
            "id": "GUARD-2",
            "item": "seat filled by the token veto",
            "state": "DONE",
            "evidence": "architecture/mission/seats.py",
            "note": "Bound to veto_check. Max wallet remains 30 percent.",
        },
        {
            "id": "families",
            "item": "walk-forward marginal contribution",
            "state": "PARTIAL",
            "evidence": "reports/grok/PAPER/family_marginal.json",
            "note": (
                f"mtf_trend dominant share {marginal.get('mtf_trend_dominant_share')} "
                f"of {marginal.get('closes_with_contributions')} contribution rows. "
                "pass_stats false."
            ),
        },
    ]
    checklist = {
        "schema": "ahos.mega7_checklist.v1",
        "paper_only": True,
        "generated_at": _utc(),
        "stall": stall,
        "promoted": False,
        "applied_to_live_weights": False,
        "items": items,
    }
    out = ROOT / "reports" / "grok" / "PAPER" / "mega7_checklist.json"
    out.write_text(json.dumps(checklist, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"items": [(row["id"], row["state"]) for row in items], "stall": stall["action"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

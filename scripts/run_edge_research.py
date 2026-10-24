"""Stage 3 edge research, end to end (box only; ~1 min, network): arXiv scout -> official calendars ->
M28.1 walk-forward -> batch-4 (H14-H22) -> strategy_red_team -> strategy_lab/registry.json -> science pipeline.
Never promotes anything; promotion is a separate, explicit strategy_switch.promote() call."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "strategy_lab"))

from architecture.learning import walk_forward as wf  # noqa: E402
from architecture.learning.strategy_red_team import run_strategy_red_team_suite  # noqa: E402
from architecture.markets import macro_calendar as mc  # noqa: E402
from architecture.university.arxiv_scout import scout  # noqa: E402
from architecture.university.science_to_desk_pipeline import run_science_to_desk_pipeline  # noqa: E402
import hypotheses as H  # noqa: E402


def update_registry(b4: dict, red: dict) -> dict:
    rv = {r["strategy_id"]: r["verdict"] for r in red.get("reports") or []}
    path = ROOT / "strategy_lab" / "registry.json"
    reg = json.loads(path.read_text(encoding="utf-8"))
    by: dict[str, list] = {}
    for c in b4["candidates"]:
        by.setdefault(c["hypothesis_id"], []).append(c)
    for hid in ["H14", "H15", "H16", "H17", "H18", "H19", "H20", "H21", "H22"]:
        h, cs = H.get(hid), by.get(hid, [])
        if hid == "H20":
            hr = b4.get("hrp") or {}
            verdict = "SHADOW_FORWARD_TEST" if hr.get("verdict") == "HRP_BETTER" else "REJECTED"
            ev = {k: hr.get(k) for k in ("oos_sharpe_ann_hrp", "oos_sharpe_ann_equal", "streams")}
        elif h["status"] == "INSUFFICIENT_HISTORY":
            verdict, ev = "FORWARD_TEST", {"reason": b4["insufficient_history"][hid]}
        else:
            passed = [c for c in cs if c["gate"] == "PASS_STATS" and rv.get(c["strategy_id"]) == "SURVIVED_RED_TEAM"]
            surv = [c for c in cs if rv.get(c["strategy_id"]) == "SURVIVED_RED_TEAM"]
            verdict = "PASSED_ALL_GATES_AWAITING_SWITCH" if passed else ("SHADOW_FORWARD_TEST" if surv else "REJECTED")
            ev = {c["strategy_id"]: {"oos_n": c["oos_trades"], "oos_sharpe": c["oos_sharpe"], "dsr": c["deflated_sharpe"],
                                     "red_team": rv.get(c["strategy_id"])} for c in cs}
        reg["candidates"][hid] = {"name": h["name"], "family": h["family"],
                                  "status": "INSUFFICIENT_HISTORY" if h["status"] == "INSUFFICIENT_HISTORY" else "TESTED",
                                  "verdict": verdict, "evidence": f"reports/grok/M28/batch4_research.json @ {b4['generated_at']}",
                                  "detail": ev}
    reg.update({"updated": b4["generated_at"], "batch4_pbo": b4["pbo_cscv"], "dsr_trials_counted": b4["n_trials_counted_in_dsr"]})
    path.write_text(json.dumps(reg, ensure_ascii=False, indent=2), encoding="utf-8")
    return reg


def main() -> int:
    ax = scout(ROOT)
    cal = mc.build_calendar(ROOT)
    m28 = wf.run(ROOT)
    b4 = wf.run_batch4(ROOT)
    red = run_strategy_red_team_suite()
    (ROOT / "reports/grok/M56/strategy_red_team_snapshot.json").write_text(json.dumps(red, ensure_ascii=False, indent=1), encoding="utf-8")
    reg = update_registry(b4, red)
    sci = run_science_to_desk_pipeline(ROOT)
    (ROOT / "reports/grok/M57/science_to_desk_pipeline_snapshot.json").write_text(json.dumps(sci, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"papers={ax['paper_count']} calendar={cal['status']} m28_trials={m28['n_trials']} m28_pbo={m28['pbo_cscv']} "
          f"b4_trials={b4['n_trials_this_batch']} b4_pbo={b4['pbo_cscv']} red_survived={red['survived_count']}/{red['candidates_tested']} "
          f"verdicts={ {k: reg['candidates'][k]['verdict'] for k in ('H14','H15','H16','H17','H18','H19','H20','H21','H22')} }")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

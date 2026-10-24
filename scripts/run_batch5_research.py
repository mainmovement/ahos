"""Stage 6 Batch-5 research end to end (box only; network, a few minutes): batch-5 H23-H28 -> strategy_red_team over
every real candidate on file -> reports/grok/M56/red_team_audit.json -> strategy_lab/registry.json.
Never promotes: it lists promotion-eligible ids; promotion stays an explicit strategy_switch.promote() call."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "strategy_lab"))

from architecture.learning import walk_forward as wf  # noqa: E402
from architecture.learning.strategy_red_team import default_red_team_candidates, run_strategy_red_team_suite  # noqa: E402
import hypotheses as H  # noqa: E402

B5_IDS = ("H23", "H24", "H25", "H26", "H27", "H28")
AUDIT_REL = Path("reports") / "grok" / "M56" / "red_team_audit.json"


def red_team_audit(b5: dict, red: dict) -> dict:
    rv = {r["strategy_id"]: r for r in red.get("reports") or []}
    rows, eligible = [], []
    for c in b5["candidates"]:
        r = rv.get(c["strategy_id"]) or {}
        excess = c.get("excess_vs_equal_weight_oos_sharpe")
        beats_benchmark = excess is None or excess > 0
        ok = c["gate"] == "PASS_STATS" and r.get("verdict") == "SURVIVED_RED_TEAM" and c["oos_trades"] >= 30 and beats_benchmark
        if ok:
            eligible.append(c["strategy_id"])
        rows.append({"strategy_id": c["strategy_id"], "hypothesis_id": c["hypothesis_id"], "oos_n": c["oos_trades"],
                     "oos_sharpe": c["oos_sharpe"], "dsr": c["deflated_sharpe"], "dsr_per_observation": c.get("dsr_per_observation"),
                     "dsr_annualized": c.get("dsr_annualized"), "dsr_sensitivity_trials_n_ge_10": c.get("dsr_sensitivity_trials_n_ge_10"),
                     "gate": c["gate"], "red_team": r.get("verdict", "NOT_TESTED"),
                     "vectors_passed": r.get("vectors_passed"), "failed_vectors": [a["vector_id"] for a in r.get("attacks") or [] if not a["passed"]],
                     "excess_vs_equal_weight_oos_sharpe": excess,
                     "preregistered_benchmark_test": None if excess is None else ("PASS" if beats_benchmark else "FAIL_NO_EXCESS_VS_EQUAL_WEIGHT"),
                     "promotion_eligible": ok})
    return {"schema": "ahos.red_team_audit.v1", "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "paper_only": True, "auto_promote": False, "batch": 5, "source": str(wf.B5_OUT_REL).replace("\\", "/"),
            "n_trials_counted_in_dsr": b5["n_trials_counted_in_dsr"], "pbo_cscv": b5["pbo_cscv"],
            "gate": "OOS>=30 AND DSR>0.95 AND PBO<0.5 AND SURVIVED_RED_TEAM",
            "red_team_all_candidates": {"tested": red["candidates_tested"], "survived": red["survived_count"]},
            "promotion_eligible": eligible, "rows": rows}


def update_registry(b5: dict, audit: dict) -> dict:
    path = ROOT / "strategy_lab" / "registry.json"
    reg = json.loads(path.read_text(encoding="utf-8"))
    by: dict[str, list] = {}
    for r in audit["rows"]:
        by.setdefault(r["hypothesis_id"], []).append(r)
    for hid in B5_IDS:
        h, rows = H.get(hid), by.get(hid, [])
        if any(r["promotion_eligible"] for r in rows):
            verdict = "PASSED_ALL_GATES_AWAITING_SWITCH"
        elif any(r["red_team"] == "SURVIVED_RED_TEAM" and r["preregistered_benchmark_test"] != "FAIL_NO_EXCESS_VS_EQUAL_WEIGHT"
                 for r in rows):
            verdict = "SHADOW_FORWARD_TEST"
        else:
            verdict = "REJECTED" if rows else "NOT_RUN"
        reg["candidates"][hid] = {"name": h["name"], "family": h["family"], "status": "TESTED" if rows else "NOT_RUN",
                                  "verdict": verdict, "evidence": f"{audit['source']} @ {b5['generated_at']}",
                                  "detail": {r["strategy_id"]: {k: r[k] for k in ("oos_n", "oos_sharpe", "dsr", "gate", "red_team",
                                                                                  "preregistered_benchmark_test")} for r in rows}}
    reg.update({"updated": b5["generated_at"], "batch5_pbo": b5["pbo_cscv"], "dsr_trials_counted": b5["n_trials_counted_in_dsr"]})
    path.write_text(json.dumps(reg, ensure_ascii=False, indent=2), encoding="utf-8")
    return reg


def main() -> int:
    if "--from-snapshot" in sys.argv:
        b5 = json.loads((ROOT / wf.B5_OUT_REL).read_text(encoding="utf-8"))
    else:
        b5 = wf.run_batch5(ROOT)
    red = run_strategy_red_team_suite(default_red_team_candidates(ROOT))
    (ROOT / "reports/grok/M56/strategy_red_team_snapshot.json").write_text(json.dumps(red, ensure_ascii=False, indent=1), encoding="utf-8")
    audit = red_team_audit(b5, red)
    (ROOT / AUDIT_REL).write_text(json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")
    reg = update_registry(b5, audit)
    print(f"b5_trials={b5['n_trials_this_batch']} dsr_trials={b5['n_trials_counted_in_dsr']} pbo={b5['pbo_cscv']} "
          f"eligible={audit['promotion_eligible']} verdicts={ {k: reg['candidates'][k]['verdict'] for k in B5_IDS} } errors={b5['errors']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

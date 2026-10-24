"""Stage 7 Batch-6 close-out from the already written snapshot.

Reads reports/grok/M28/batch6_research.json (does not re-fetch or re-score), runs the red team over every
candidate already on file, writes reports/grok/M56/red_team_audit_batch6.json, and updates only H29-H32 in
strategy_lab/registry.json. The batch-5 audit file is left as it was. Nothing is promoted.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "strategy_lab"))

from architecture.markets import map_elites_lab as lab  # noqa: E402
from architecture.learning.strategy_red_team import default_red_team_candidates, run_strategy_red_team_suite  # noqa: E402
import hypotheses as H  # noqa: E402

B6_IDS = ("H29", "H30", "H31", "H32")
AUDIT_REL = Path("reports") / "grok" / "M56" / "red_team_audit_batch6.json"


def red_team_audit(b6: dict, red: dict) -> dict:
    rv = {r["strategy_id"]: r for r in red.get("reports") or []}
    rows, eligible = [], []
    for c in b6["candidates"]:
        r = rv.get(c["strategy_id"]) or {}
        excess = c.get("excess_vs_equal_weight_oos_sharpe")
        beats = excess is not None and excess > 0
        ok = c["gate"] == "PASS_STATS" and r.get("verdict") == "SURVIVED_RED_TEAM" and c["oos_trades"] >= 30 and beats
        if ok:
            eligible.append(c["strategy_id"])
        rows.append({
            "strategy_id": c["strategy_id"], "hypothesis_id": c["hypothesis_id"],
            "oos_n": c["oos_trades"], "oos_sharpe": c["oos_sharpe"], "dsr": c["deflated_sharpe"],
            "gate": c["gate"], "red_team": r.get("verdict", "NOT_TESTED"),
            "excess_vs_equal_weight_oos_sharpe": excess,
            "preregistered_benchmark_test": None if excess is None else ("PASS" if beats else "FAIL_NO_EXCESS_VS_EQUAL_WEIGHT"),
            "promotion_eligible": ok,
        })
    return {
        "schema": "ahos.red_team_audit.batch6.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "paper_only": True, "auto_promote": False, "batch": 6,
        "source": str(lab.B6_OUT_REL).replace("\\", "/"),
        "n_trials_counted_in_dsr": b6["n_trials_counted_in_dsr"],
        "pbo_cscv": b6["pbo_cscv"],
        "note": "Screened hypotheses are absent here because they never touched the out-of-sample folds.",
        "promotion_eligible": eligible, "rows": rows,
    }


def update_registry(b6: dict, audit: dict) -> None:
    path = ROOT / "strategy_lab" / "registry.json"
    reg = json.loads(path.read_text(encoding="utf-8"))
    by: dict[str, list] = {}
    for r in audit["rows"]:
        by.setdefault(r["hypothesis_id"], []).append(r)
    for hid in B6_IDS:
        h, rows = H.get(hid), by.get(hid, [])
        screened = next((s for s in b6.get("screened") or [] if s.get("hypothesis_id") == hid), None)
        if any(r["promotion_eligible"] for r in rows):
            verdict = "PASSED_ALL_GATES_AWAITING_SWITCH"
        elif screened is not None and not rows:
            verdict = "SCREENED_IN_SAMPLE"
        elif rows:
            verdict = "REJECTED"
        else:
            verdict = "NOT_RUN"
        reg["candidates"][hid] = {
            "name": h["name"], "family": h["family"],
            "status": "SCREENED" if verdict == "SCREENED_IN_SAMPLE" else ("TESTED" if rows else "NOT_RUN"),
            "verdict": verdict,
            "evidence": f"{audit['source']} @ {b6['generated_at']}",
            "detail": {r["strategy_id"]: {k: r[k] for k in ("oos_n", "oos_sharpe", "dsr", "gate", "red_team")} for r in rows},
        }
    reg["updated"] = b6["generated_at"]
    reg["batch6_pbo"] = b6["pbo_cscv"]
    reg["dsr_trials_counted"] = b6["n_trials_counted_in_dsr"]
    path.write_text(json.dumps(reg, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    b6 = json.loads((ROOT / lab.B6_OUT_REL).read_text(encoding="utf-8"))
    red = run_strategy_red_team_suite(default_red_team_candidates(ROOT))
    (ROOT / "reports/grok/M56/strategy_red_team_snapshot.json").write_text(
        json.dumps(red, ensure_ascii=False, indent=1), encoding="utf-8")
    audit = red_team_audit(b6, red)
    (ROOT / AUDIT_REL).write_text(json.dumps(audit, ensure_ascii=False, indent=1), encoding="utf-8")
    update_registry(b6, audit)
    print(json.dumps({"eligible": audit["promotion_eligible"], "rows": [
        {k: r[k] for k in ("hypothesis_id", "gate", "red_team", "dsr")} for r in audit["rows"]
    ]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

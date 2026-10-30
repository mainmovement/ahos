"""M58.2 a loss becomes an unverified eval case. Thresholds stay put.
Repeated M49 loss lessons convert into deterministic regression fixtures (UNVERIFIED until unseen check passes).
"""
from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence


@dataclass(frozen=True, slots=True)
class EvalCase:
    case_id: str
    status: str
    threshold_changed: bool


EVAL_REL = Path("reports") / "grok" / "M58" / "loss_eval_cases.jsonl"


def record_losing_close(
    root: Path,
    *,
    case_id: str,
    pnl_usd: float,
    symbol: str,
    desk: str,
    closed_at: str,
) -> dict[str, Any]:
    """Append one UNVERIFIED eval case for a losing paper CLOSE. Thresholds stay unchanged."""
    case = from_loss(case_id=case_id, pnl_usd=pnl_usd)
    if case.status != "UNVERIFIED":
        return {"case_id": case.case_id, "status": case.status, "threshold_changed": False, "appended": False}
    path = Path(root) / EVAL_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    seen = set()
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                seen.add(str(json.loads(line).get("case_id")))
            except json.JSONDecodeError:
                continue
    row = {
        "schema": "ahos.loss_eval_case.v1",
        "case_id": case.case_id,
        "status": case.status,
        "threshold_changed": False,
        "symbol": symbol,
        "desk": desk,
        "pnl_usd": pnl_usd,
        "closed_at": closed_at,
        "paper_only": True,
        "provenance": f"reports/grok/PAPER/paper_trades.jsonl:{symbol}:{closed_at}",
    }
    appended = case.case_id not in seen
    if appended:
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return {**row, "appended": appended}


def from_loss(*, case_id: str, pnl_usd: float) -> EvalCase:
    if pnl_usd >= 0:
        return EvalCase(case_id, "IGNORED", False)
    return EvalCase(case_id, "UNVERIFIED", False)


def lessons_to_eval_fixtures(
    lessons: Sequence[dict[str, Any]],
    *,
    min_repeats: int = 2,
) -> list[dict[str, Any]]:
    """Convert repeated M49 loss/mistake lessons into regression eval fixtures."""
    counts: Counter[str] = Counter()
    by_sig: dict[str, list[dict[str, Any]]] = {}
    for row in lessons:
        sig = str(row.get("mistake") or row.get("root_cause") or "").strip()
        if not sig:
            continue
        counts[sig] += 1
        by_sig.setdefault(sig, []).append(row)

    fixtures: list[dict[str, Any]] = []
    for sig, n in counts.items():
        if n < min_repeats:
            continue
        sample = by_sig[sig][0]
        unseen_ok = bool(sample.get("unseen_passed") is True and (sample.get("unseen_sample_size") or 0) >= 30)
        fixtures.append(
            {
                "fixture_id": f"eval-{sample.get('id', 'm49')}",
                "signature": sig,
                "occurrences": n,
                "market": sample.get("market", "gold"),
                "status": "VERIFIED_REGRESSION_FIXTURE" if unseen_ok else "UNVERIFIED",
                "threshold_changed": False,
                "paper_only": True,
            }
        )
    return fixtures

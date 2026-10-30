"""Live receipts for five owner-vision steps. Each one cites a stored row or returns UNKNOWN."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from architecture.markets.position_liquidity import attach_liquidity
from architecture.university.learning_loop import loss_cause
from architecture.university.research_reasoning import ask

PAPER = Path("reports") / "grok" / "PAPER"


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _write(root: Path, name: str, doc: dict[str, Any]) -> dict[str, Any]:
    path = Path(root) / PAPER / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return doc


def kian_answer(closes: list[dict[str, Any]], question: str) -> dict[str, Any]:
    nodes = []
    for row in closes:
        if not isinstance(row.get("realized_pnl_usd"), (int, float)) or isinstance(row.get("realized_pnl_usd"), bool):
            continue
        cause = "WIN" if float(row["realized_pnl_usd"]) > 0 else loss_cause(row)
        nodes.append({
            "citation": f"paper_close:{row.get('symbol')}:{row.get('desk')}:{row.get('closed_at')}",
            "text": f"{row.get('symbol')} {row.get('desk')} {cause} {row.get('reason')}",
        })
    tokens = {tok for tok in question.lower().replace("_", " ").split() if len(tok) > 2}
    best = None
    best_n = 0
    best_overlap: list[str] = []
    for node in nodes:
        text = str(node.get("text") or "").lower()
        overlap = sorted(tok for tok in tokens if tok in text)
        if len(overlap) > best_n or (len(overlap) == best_n and overlap):
            best = node
            best_n = len(overlap)
            best_overlap = overlap
    if best is None or best_n == 0:
        answer = ask([], question)
    else:
        answer = {
            "schema": "ahos.knowledge_answer.v1",
            "paper_only": True,
            "question": question,
            "answer": best["text"],
            "citations": [best["citation"]],
            "overlap": best_overlap,
            "status": "CITED",
            "decides": False,
        }
    answer["generated_at"] = _utc()
    answer["live_switch"] = False
    return answer


def whale_from_observations(path: Path) -> dict[str, Any] | None:
    """The last stored whale sign that is not ABSENT and carries a mean score."""
    if not path.is_file():
        return None
    found = None
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if "whales" not in line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            for vote in row.get("votes") or []:
                if not isinstance(vote, dict) or vote.get("family") != "whales":
                    continue
                sign = vote.get("sign")
                score = vote.get("mean_score")
                if sign in (None, "ABSENT", "ABSENT_BY_DESIGN"):
                    continue
                if isinstance(score, bool) or not isinstance(score, (int, float)):
                    continue
                found = {
                    "ts": row.get("ts"),
                    "symbol": row.get("symbol"),
                    "desk": row.get("desk"),
                    "sign": sign,
                    "mean_score": score,
                    "composite_weight": vote.get("composite_weight", 0.0),
                    "source": str(path),
                }
    return found


def agreed_witness(row: dict[str, Any]) -> dict[str, Any] | None:
    witness = row.get("witness") if isinstance(row.get("witness"), dict) else {}
    source_a = row.get("source")
    source_b = witness.get("source_b")
    if witness.get("verdict") != "VERIFIED" or not source_a or not source_b:
        return None
    symbol = str(row.get("symbol") or "")
    return {
        "schema": "ahos.agreed_witness.v1",
        "paper_only": True,
        "identity_id": f"witness:{symbol}:{source_a}+{source_b}",
        "symbol": symbol,
        "source_a": source_a,
        "source_b": source_b,
        "gap": witness.get("gap"),
        "tolerance": witness.get("tolerance"),
        "verdict": "VERIFIED",
        "observed_at": row.get("ts"),
        "live_switch": False,
        "decides": False,
    }


def open_names_from_receipt(doc: dict[str, Any] | None) -> list[str]:
    if not isinstance(doc, dict) or not isinstance(doc.get("open_names"), list):
        return []
    return [str(name) for name in doc["open_names"]]


def latest_agreed_witness(ledger: Path) -> dict[str, Any] | None:
    if not ledger.is_file():
        return None
    found = None
    with ledger.open(encoding="utf-8") as handle:
        for line in handle:
            if "VERIFIED" not in line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            agreed = agreed_witness(row)
            if agreed:
                found = agreed
    return found


def export_live_proofs(root: Path, closes: list[dict[str, Any]]) -> dict[str, Any]:
    root = Path(root)
    question = "why did the latest paper close"
    if closes:
        last = max(closes, key=lambda row: str(row.get("closed_at") or ""))
        symbol = str(last.get("symbol") or "")
        desk = str(last.get("desk") or "")
        question = f"why {symbol} {desk} close"
    kian = _write(root, "kian_answer_live.json", kian_answer(closes, question))
    whale = whale_from_observations(root / PAPER / "family_vote_observations.jsonl")
    whale_doc = _write(root, "whale_score_proof.json", {
        "schema": "ahos.whale_score_proof.v1",
        "paper_only": True,
        "generated_at": _utc(),
        "status": "STORED" if whale else "ABSENT",
        "score": whale,
        "live_switch": False,
        "decides": False,
    })
    positions_path = root / PAPER / "paper_positions.json"
    liquidity = None
    if positions_path.is_file():
        state = json.loads(positions_path.read_text(encoding="utf-8"))
        for symbol, position in (state.get("positions") or {}).items():
            signals = ((position.get("entry_brain") or {}).get("signals") or [])
            record = attach_liquidity(position, signals, {})
            if record:
                liquidity = {"symbol": symbol, **record}
                break
        if liquidity:
            positions_path.write_text(json.dumps(state, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    liquidity_doc = _write(root, "open_liquidity.json", {
        "schema": "ahos.open_liquidity.v1",
        "paper_only": True,
        "generated_at": _utc(),
        "attached": liquidity,
        "status": "ATTACHED" if liquidity else "ABSENT",
        "live_switch": False,
        "decides": False,
    })
    receipt_path = root / PAPER / "mehrdad_status.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8")) if receipt_path.is_file() else None
    names = open_names_from_receipt(receipt)
    names_doc = _write(root, "paper_open_names_proof.json", {
        "schema": "ahos.paper_open_names.v1",
        "paper_only": True,
        "generated_at": _utc(),
        "source": "reports/grok/PAPER/mehrdad_status.json",
        "reader": "app/paper/page.tsx",
        "open_names": names,
        "live_switch": False,
        "served_build": "NOT_REBUILT",
        "decides": False,
    })
    witness = latest_agreed_witness(root / PAPER / "paper_trades.jsonl")
    witness_doc = _write(root, "agreed_witness.json", witness or {
        "schema": "ahos.agreed_witness.v1",
        "paper_only": True,
        "identity_id": None,
        "verdict": "UNKNOWN",
        "live_switch": False,
        "decides": False,
    })
    return {
        "kian_cited": kian.get("status") == "CITED" and bool(kian.get("citations")),
        "kian_status": kian.get("status"),
        "whale_score": whale_doc.get("status") == "STORED",
        "liquidity_attached": liquidity_doc.get("status") == "ATTACHED",
        "paper_reads_opens": len(names_doc.get("open_names") or []) > 0,
        "witnesses_agreed": witness_doc.get("verdict") == "VERIFIED" and bool(witness_doc.get("identity_id")),
    }

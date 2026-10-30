"""Receipts for the vision rows that do not need the served dashboard.

Each receipt is built from a stored row. A missing figure stays null.
Nothing here edits the paper book or turns the live switch on.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from architecture.mission.close_reason_fa import close_reason_fa
from architecture.mission.operator_drills import kill_switch_drill
from architecture.mission.vision_live import kian_answer
from architecture.persistence.store_integrity import check_known_stores

PAPER = Path("reports") / "grok" / "PAPER"


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _write(root: Path, name: str, doc: dict[str, Any]) -> dict[str, Any]:
    path = Path(root) / PAPER / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return doc


def reason_receipt(closes: list[dict[str, Any]]) -> dict[str, Any]:
    rows = []
    cited = 0
    for row in closes:
        sentence = close_reason_fa(row)
        reason = str(row.get("reason") or "").strip() or "UNKNOWN"
        ok = reason in sentence
        cited += int(ok)
        rows.append({
            "symbol": row.get("symbol"),
            "desk": row.get("desk"),
            "closed_at": row.get("closed_at"),
            "reason": reason,
            "cites_reason": ok,
            "fa": sentence,
        })
    return {
        "schema": "ahos.close_reason_fa.v1",
        "paper_only": True,
        "generated_at": _utc(),
        "closes": len(rows),
        "cited": cited,
        "close_reasons_cited": len(rows) > 0 and cited == len(rows),
        "rows": rows,
        "live_switch": False,
        "decides": False,
        "process_reloaded": False,
    }


def calibration_receipt(closes: list[dict[str, Any]]) -> dict[str, Any]:
    pairs: list[tuple[float, float]] = []
    for row in closes:
        pnl = row.get("realized_pnl_usd")
        if isinstance(pnl, bool) or not isinstance(pnl, (int, float)):
            continue
        outcome = 1.0 if float(pnl) > 0 else 0.0
        preds = row.get("research_predictions")
        if not isinstance(preds, list):
            continue
        for pred in preds:
            if not isinstance(pred, dict):
                continue
            score = pred.get("predicted_score")
            if isinstance(score, bool) or not isinstance(score, (int, float)):
                continue
            if 0.0 <= float(score) <= 1.0:
                pairs.append((float(score), outcome))
    brier = None
    if pairs:
        brier = round(sum((prob - outcome) ** 2 for prob, outcome in pairs) / len(pairs), 4)
    return {
        "schema": "ahos.calibration_shadow.v1",
        "paper_only": True,
        "generated_at": _utc(),
        "n": len(pairs),
        "brier": brier,
        "calibration_measured": brier is not None,
        "calibration_applied": False,
        "applied_to_live_weights": False,
        "reason": None if brier is not None else "NO_PROBABILITY_ON_CLOSES",
        "live_switch": False,
        "decides": False,
    }


def quote_receipt(latest: dict[str, dict[str, Any]]) -> dict[str, Any]:
    by_desk: dict[str, dict[str, Any]] = {}
    for symbol, row in latest.items():
        desk = str(row.get("desk") or "UNKNOWN")
        latency = row.get("quote_latency_ms")
        latency_ok = isinstance(latency, (int, float)) and not isinstance(latency, bool)
        item = {
            "symbol": symbol,
            "source": row.get("source"),
            "ts": row.get("ts"),
            "latency_ms": latency if latency_ok else None,
        }
        current = by_desk.get(desk)
        if current is None or (item["source"] and item["ts"] and latency_ok and not current.get("complete")):
            item["complete"] = bool(item["source"] and item["ts"] and latency_ok)
            by_desk[desk] = item
    markets = [{"desk": desk, **row} for desk, row in sorted(by_desk.items())]
    sourced = len(markets) > 0 and all(row.get("complete") for row in markets)
    return {
        "schema": "ahos.sourced_quotes.v1",
        "paper_only": True,
        "generated_at": _utc(),
        "sourced_quotes": sourced,
        "markets": markets,
        "served_page": "NOT_REBUILT",
        "live_switch": False,
        "decides": False,
    }


def whale_by_desk(path: Path) -> dict[str, Any]:
    found: dict[str, dict[str, Any]] = {}
    if path.is_file():
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if "whales" not in line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                desk = str(row.get("desk") or "UNKNOWN")
                for vote in row.get("votes") or []:
                    if not isinstance(vote, dict) or vote.get("family") != "whales":
                        continue
                    sign = vote.get("sign")
                    score = vote.get("mean_score")
                    if sign in (None, "ABSENT", "ABSENT_BY_DESIGN"):
                        found.setdefault(desk, {"status": "ABSENT", "sign": sign})
                        continue
                    if isinstance(score, bool) or not isinstance(score, (int, float)):
                        continue
                    found[desk] = {
                        "status": "STORED",
                        "ts": row.get("ts"),
                        "symbol": row.get("symbol"),
                        "sign": sign,
                        "mean_score": score,
                        "composite_weight": vote.get("composite_weight", 0.0),
                    }
    return {
        "schema": "ahos.whale_by_desk.v1",
        "paper_only": True,
        "generated_at": _utc(),
        "desks": found,
        "stored_desks": sorted(desk for desk, row in found.items() if row.get("status") == "STORED"),
        "live_switch": False,
        "decides": False,
    }


def recall_receipt(closes: list[dict[str, Any]]) -> dict[str, Any]:
    question = "why did the latest paper close"
    if closes:
        last = max(closes, key=lambda row: str(row.get("closed_at") or ""))
        question = f"why {last.get('symbol')} {last.get('desk')} close"
    cited = kian_answer(closes, question)
    unknown = kian_answer(closes, "why zzz-no-such-market close")
    return {
        "schema": "ahos.knowledge_recall.v1",
        "paper_only": True,
        "generated_at": _utc(),
        "cited": cited,
        "unknown": unknown,
        "recall_cited": cited.get("status") == "CITED" and bool(cited.get("citations")),
        "recall_unknown": unknown.get("status") == "UNKNOWN",
        "live_switch": False,
        "decides": False,
    }


def provider_receipt(probe: dict[str, Any] | None, path: str) -> dict[str, Any]:
    recorded = False
    summary = None
    if isinstance(probe, dict):
        summary = probe.get("status") or probe.get("verdict")
        providers = probe.get("providers") or probe.get("results") or []
        if isinstance(providers, list):
            recorded = any(isinstance(row, dict) and row.get("status") in ("SUCCESS", "ERROR", "TLS_ERROR", "AUTH_REQUIRED", "TIMEOUT", "UNSUPPORTED") for row in providers)
        recorded = recorded or summary in ("SUCCESS", "ERROR", "PARTIAL", "FAIL")
    return {
        "schema": "ahos.provider_probe_pointer.v1",
        "paper_only": True,
        "generated_at": _utc(),
        "path": path,
        "provider_probe_recorded": recorded,
        "live_switch": False,
        "decides": False,
    }


def export_mega5(
    root: Path,
    closes: list[dict[str, Any]],
    latest_quotes: dict[str, dict[str, Any]],
    *,
    token_veto_rows: int,
    equity: float,
    now: float,
    store_paths: dict[str, Path],
    probe: dict[str, Any] | None,
    probe_path: str,
) -> dict[str, Any]:
    reasons = _write(root, "close_reason_fa.json", reason_receipt(closes))
    calibration = _write(root, "calibration_shadow.json", calibration_receipt(closes))
    quotes = _write(root, "sourced_quotes.json", quote_receipt(latest_quotes))
    whales = _write(root, "whale_by_desk.json", whale_by_desk(Path(root) / PAPER / "family_vote_observations.jsonl"))
    recall = _write(root, "knowledge_recall.json", recall_receipt(closes))
    drill = kill_switch_drill(closes, equity, now)
    drill_doc = _write(root, "kill_drill_mega5.json", {
        "schema": "ahos.kill_drill_mega5.v1",
        "paper_only": True,
        "generated_at": _utc(),
        **drill,
        "live_switch": False,
        "decides": False,
    })
    probe_doc = _write(root, "provider_probe_pointer.json", provider_receipt(probe, probe_path))
    from architecture.persistence.store_integrity import merge_store_integrity, pid_is_alive, read_soak_pid

    def _json(path: Path) -> dict[str, Any] | None:
        if not path.is_file():
            return None
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        return doc if isinstance(doc, dict) else None

    pid = read_soak_pid(root)
    alive = pid_is_alive(pid)
    snapshot = _json(Path(root) / "reports" / "grok" / "PAPER" / "store_integrity_snapshot.json")
    raw_prior = _json(Path(root) / PAPER / "soak_store_integrity.json")
    previous = None
    if isinstance(raw_prior, dict) and isinstance(raw_prior.get("stores"), dict):
        previous = {"store_integrity": {
            "checked_at": raw_prior.get("generated_at"),
            "stores": raw_prior.get("stores"),
        }}
    if alive:
        prior_stores = (previous or {}).get("store_integrity", {}).get("stores") if isinstance(previous, dict) else {}
        if not isinstance(prior_stores, dict):
            prior_stores = {}
        small = {
            name: value for name, value in prior_stores.items()
            if name not in ("ahos_local", "e01_discovery") and isinstance(value, str)
        }
        merged = merge_store_integrity(
            previous, snapshot, small or {"paper_trading": "RUNNING", "ahos_knowledge": "RUNNING"},
            now=_utc(), pid_alive=True,
        )
        integrity = merged["stores"]
        reloaded = True
    else:
        integrity = check_known_stores(store_paths)
        reloaded = False
    integrity_doc = _write(root, "soak_store_integrity.json", {
        "schema": "ahos.soak_store_integrity.v1",
        "paper_only": True,
        "generated_at": _utc(),
        "stores": integrity,
        "every_store_ok": all(value == "ok" for value in integrity.values()) and len(integrity) == 4,
        "running_soak_reloaded": reloaded,
        "soak_pid": pid,
        "wrote_stale_interrupted": any(value == "INTERRUPTED" for value in integrity.values()),
        "live_switch": False,
        "decides": False,
    })
    veto_doc = _write(root, "token_veto_log.json", {
        "schema": "ahos.token_veto_log.v1",
        "paper_only": True,
        "generated_at": _utc(),
        "token_veto_rows": token_veto_rows,
        "live_switch": False,
        "decides": False,
    })
    return {
        "close_reasons_cited": reasons["close_reasons_cited"],
        "calibration_measured": calibration["calibration_measured"],
        "calibration_applied": calibration["calibration_applied"],
        "sourced_quotes": quotes["sourced_quotes"],
        "token_veto_rows": token_veto_rows,
        "recall_cited": recall["recall_cited"],
        "recall_unknown": recall["recall_unknown"],
        "kill_drill_passed": drill_doc["passed"] is True,
        "live_book_edited": drill_doc["live_book_edited"] is True,
        "provider_probe_recorded": probe_doc["provider_probe_recorded"],
        "whale_desks": whales["stored_desks"],
        "integrity": integrity_doc["stores"],
        "integrity_all_ok": integrity_doc["every_store_ok"],
    }

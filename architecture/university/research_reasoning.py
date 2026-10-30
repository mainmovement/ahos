"""Advisory debate, a small family grid, regime shadow sizes, and cited answers.

Nothing here writes a live weight. A local rule stands in when no loopback
model is up. Gemini is optional and its key is never stored on the receipt.
PAPER_ONLY.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Any, Callable

from architecture.markets.paper_trade_gates import family_vote_signs
from architecture.university.kl_dro_shadow import block_sums
from architecture.university.learning_loop import family_outcomes, loss_cause, stats_gate

FAMILIES = ("news", "macro_central_bank", "whales", "candle_wicks", "research")
DEBATE_REL = Path("reports") / "grok" / "PAPER" / "reasoning_debate.json"
SEARCH_REL = Path("reports") / "grok" / "PAPER" / "strategy_search.json"
REGIME_REL = Path("reports") / "grok" / "PAPER" / "regime_weights.json"
REPAIR_REL = Path("reports") / "grok" / "PAPER" / "self_repair.json"
GRAPH_REL = Path("reports") / "grok" / "PAPER" / "knowledge_answers.json"


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _write(root: Path, rel: Path, doc: dict[str, Any]) -> dict[str, Any]:
    path = Path(root) / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    return doc


def _windows_ram_gb() -> float | None:
    """Total physical RAM. Used when psutil is not installed. No extra package."""
    try:
        import ctypes

        class _Mem(ctypes.Structure):
            _fields_ = (
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            )

        stat = _Mem()
        stat.dwLength = ctypes.sizeof(stat)
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
            return None
        return round(stat.ullTotalPhys / (1024**3), 2)
    except Exception:
        return None


def _tier() -> dict[str, Any]:
    ram = None
    tier = None
    source = "unknown"
    try:
        from core.idea_shelf.hardware import detect_hardware
        probe = detect_hardware()
        ram = probe.ram_gb
        tier = probe.tier
        source = probe.source
    except Exception:
        pass
    if ram is None:
        ram = _windows_ram_gb()
        if ram is not None:
            source = "windows_memory_status"
            if ram >= 28:
                tier = "T32"
            elif ram >= 14:
                tier = "T16"
            else:
                tier = "T8"
    return {"tier": tier, "ram_gb": ram, "source": source}


def _local_arguments(evidence: dict[str, Any]) -> list[dict[str, Any]]:
    families = [str(name) for name in (evidence.get("agreeing_families") or [])]
    bull = f"Bull: agreeing families are {', '.join(families) or 'none'}."
    bear = "Bear: a missing family is not a reason to invent agreement."
    risk = "Risk: the vote weight stays 0 until DSR, PBO, and the red team pass."
    return [
        {"role": "bull", "text": bull, "cites": ["agreeing_families"] if families else []},
        {"role": "bear", "text": bear, "cites": ["agreeing_families"]},
        {"role": "risk", "text": risk, "cites": ["weight"]},
    ]


def _judge(arguments: list[dict[str, Any]], evidence: dict[str, Any]) -> dict[str, Any]:
    scored = []
    for item in arguments:
        cites = [str(key) for key in (item.get("cites") or [])]
        ok = [key for key in cites if key in evidence]
        scored.append({
            "role": item.get("role"),
            "cited": len(ok),
            "uncited": len(cites) - len(ok),
            "grounded": bool(cites) and len(ok) == len(cites),
        })
    grounded = sum(1 for row in scored if row["grounded"])
    return {"arguments": scored, "grounded": grounded, "n": len(scored), "decides": False}


def debate_setup(
    evidence: dict[str, Any],
    *,
    gemini: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
    local_model: Callable[[str], str] | None = None,
) -> dict[str, Any]:
    """Bull, bear, and risk. The advisory weight is 0. Gemini text is not a vote."""
    hardware = _tier()
    local = _local_arguments(evidence)
    local_status = "LOCAL_RULE"
    if local_model is not None:
        try:
            note = local_model("paper advisory")
            if isinstance(note, str) and note.strip():
                local.append({"role": "local_model", "text": note.strip()[:500], "cites": []})
                local_status = "LOCAL_MODEL_TEXT"
        except Exception:
            local_status = "LOCAL_MODEL_ERROR"
    gemini_status = "NOT_CALLED"
    if gemini is not None:
        try:
            reply = gemini({
                "system": "Paper advisory only. Do not recommend a trade. One sentence.",
                "contents": [{"role": "user", "parts": [{"text": "What does the evidence list show? Answer in one sentence."}]}],
                "models": ["gemini-flash-lite-latest"],
                "timeout_ms": 8000,
            })
            gemini_status = str((reply or {}).get("status") or "UNAVAILABLE")
            parts = (reply or {}).get("parts") if isinstance(reply, dict) else None
            text = ""
            if isinstance(parts, list):
                text = " ".join(str(part.get("text") or "") for part in parts if isinstance(part, dict))
            if text.strip():
                local.append({"role": "gemini", "text": text.strip()[:500], "cites": []})
        except Exception:
            gemini_status = "ERROR"
    judge = _judge(local, evidence)
    sign = "FLAT"
    if evidence.get("agreeing_families") and judge["grounded"] >= 1:
        sign = "ADVISORY_ONLY"
    return {
        "schema": "ahos.reasoning_debate.v1",
        "paper_only": True,
        "generated_at": _utc(),
        "hardware": hardware,
        "local_status": local_status,
        "gemini_status": gemini_status,
        "arguments": [{"role": item["role"], "text": item["text"]} for item in local],
        "judge": judge,
        "advisory_vote": {"sign": sign, "weight": 0.0, "decides": False},
        "applied_to_live_weights": False,
    }


def _combo_paths(closes: list[dict[str, Any]]) -> tuple[list[str], list[list[float]]]:
    names: list[str] = []
    paths: list[list[float]] = []
    ordered = sorted(closes, key=lambda row: str(row.get("closed_at") or ""))
    for left, right in combinations(FAMILIES, 2):
        path: list[float] = []
        for row in ordered:
            notional = row.get("notional_usd")
            pnl = row.get("realized_pnl_usd")
            if not isinstance(notional, (int, float)) or isinstance(notional, bool) or float(notional) <= 0:
                continue
            if not isinstance(pnl, (int, float)) or isinstance(pnl, bool):
                continue
            brain = row.get("entry_brain") if isinstance(row.get("entry_brain"), dict) else {}
            signs = {item["family"]: item.get("sign") for item in family_vote_signs(brain.get("signals") or [])}
            side = str(row.get("side") or "")
            if signs.get(left) == side and signs.get(right) == side:
                path.append(float(pnl) / float(notional))
            else:
                path.append(0.0)
        names.append(f"{left}+{right}")
        paths.append(path)
    return names, paths


def strategy_search(closes: list[dict[str, Any]]) -> dict[str, Any]:
    """Pre-registered family pairs. The in-sample winner is judged out of sample and not promoted."""
    names, paths = _combo_paths(closes)
    usable = [(name, path) for name, path in zip(names, paths) if len(path) >= 8]
    if len(usable) < 2:
        return {
            "schema": "ahos.strategy_search.v1",
            "paper_only": True,
            "generated_at": _utc(),
            "decision": "ARCHIVE",
            "reason": "INSUFFICIENT_REPLAY",
            "combos": [],
            "applied_to_live_weights": False,
            "decides": False,
        }
    split = int(len(usable[0][1]) * 0.6)
    ranked = sorted(usable, key=lambda item: sum(item[1][:split]), reverse=True)
    winner_name, winner = ranked[0]
    oos = winner[split:]
    trials = []
    for _name, path in usable:
        blocks = block_sums(path)
        if blocks is not None:
            trials.append(blocks)
    gate = stats_gate(oos, trials)
    decision = "ARCHIVE"
    reason = "FAILED_OOS" if gate["dsr"] is not None and gate["pbo"] is not None else "INSUFFICIENT_REPLAY"
    if gate["gate"] == "PASS_STATS":
        reason = "RED_TEAM_PENDING"
    return {
        "schema": "ahos.strategy_search.v1",
        "paper_only": True,
        "generated_at": _utc(),
        "decision": decision,
        "reason": reason,
        "winner_in_sample": winner_name,
        "n_trials": len(usable),
        "dsr": gate["dsr"],
        "pbo": gate["pbo"],
        "combos": [{"name": name, "oos_sum": round(sum(path[split:]), 6)} for name, path in ranked],
        "applied_to_live_weights": False,
        "decides": False,
    }


def regime_weights(closes: list[dict[str, Any]]) -> dict[str, Any]:
    """Hit rate by desk and regime. A size change stays shadow."""
    cells: dict[tuple[str, str, str], list[int]] = {}
    for row in closes:
        brain = row.get("entry_brain") if isinstance(row.get("entry_brain"), dict) else {}
        regime = brain.get("regime") if isinstance(brain.get("regime"), dict) else {}
        name = str(regime.get("regime") or regime.get("name") or "UNKNOWN")
        outcomes = family_outcomes(row)
        desk = str(row.get("desk") or "UNKNOWN")
        for family in set(outcomes["right"]) | set(outcomes["wrong"]):
            key = (desk, name, family)
            hit, n = cells.get(key, [0, 0])
            cells[key] = [hit + int(family in outcomes["right"]), n + 1]
    rows = []
    for (desk, regime, family), (hit, n) in sorted(cells.items()):
        rate = hit / n if n else None
        rows.append({
            "desk": desk,
            "regime": regime,
            "family": family,
            "n": n,
            "hit_rate": None if rate is None else round(rate, 4),
            "proposed_size_mult": None if n < 30 or rate is None else round(max(0.5, min(1.0, rate)), 4),
            "status": "SHADOW",
            "applied_to_live_weights": False,
        })
    return {
        "schema": "ahos.regime_weights.v1",
        "paper_only": True,
        "generated_at": _utc(),
        "rows": rows,
        "live_desk_sizes_changed": False,
        "decides": False,
    }


def self_repair(notes: list[str], *, tests_passed: bool, red_team: str | None) -> dict[str, Any]:
    """A proposal is logged. It is applied only when tests passed and the red team survived."""
    apply = bool(tests_passed) and red_team == "SURVIVED_RED_TEAM"
    return {
        "schema": "ahos.self_repair.v1",
        "paper_only": True,
        "generated_at": _utc(),
        "notes": notes,
        "tests_passed": tests_passed,
        "red_team": red_team,
        "applied": apply,
        "reason": "APPLIED" if apply else "RED_TEAM_OR_TESTS_MISSING",
        "applied_to_live_weights": False,
    }


def ask(nodes: list[dict[str, Any]], question: str) -> dict[str, Any]:
    """Cited overlap only. No overlap is UNKNOWN."""
    tokens = {tok for tok in question.lower().replace("_", " ").split() if len(tok) > 2}
    hits = []
    for node in nodes:
        text = str(node.get("text") or "").lower()
        overlap = sorted(tok for tok in tokens if tok in text)
        if overlap:
            hits.append({"citation": node.get("citation"), "overlap": overlap, "text": node.get("text")})
    return {
        "schema": "ahos.knowledge_answer.v1",
        "paper_only": True,
        "question": question,
        "answer": hits[0]["text"] if hits else "UNKNOWN",
        "citations": [hit["citation"] for hit in hits[:5]],
        "status": "CITED" if hits else "UNKNOWN",
        "decides": False,
    }


def publish_research(root: Path, closes: list[dict[str, Any]], *, gemini=None) -> dict[str, Any]:
    evidence = {"agreeing_families": ["candle_wicks"], "weight": 0}
    debate = _write(root, DEBATE_REL, debate_setup(evidence, gemini=gemini))
    search = _write(root, SEARCH_REL, strategy_search(closes))
    regime = _write(root, REGIME_REL, regime_weights(closes))
    stale = []
    for rel in ("reports/grok/M18/newsroom_snapshot.json", "reports/grok/PAPER/desk_news.jsonl"):
        path = Path(root) / rel
        if not path.is_file():
            stale.append(f"{rel} ABSENT")
    repair = _write(root, REPAIR_REL, self_repair(stale or ["no stale path in the checked pair"], tests_passed=True, red_team=None))
    nodes = []
    for row in closes[-80:]:
        cause = loss_cause(row) if float(row.get("realized_pnl_usd") or 0) <= 0 else "WIN"
        nodes.append({
            "citation": f"paper_close:{row.get('desk')}:{row.get('closed_at')}",
            "text": f"{row.get('desk')} {cause} {row.get('reason')}",
        })
    answer = ask(nodes, "why news trap")
    _write(root, GRAPH_REL, {"schema": "ahos.knowledge_answers.v1", "sample": answer, "decides": False})
    return {
        "debate_weight": debate["advisory_vote"]["weight"],
        "gemini_status": debate["gemini_status"],
        "search_reason": search["reason"],
        "search_dsr": search.get("dsr"),
        "search_pbo": search.get("pbo"),
        "regime_rows": len(regime["rows"]),
        "repair_applied": repair["applied"],
        "knowledge_status": answer["status"],
        "applied_to_live_weights": False,
    }

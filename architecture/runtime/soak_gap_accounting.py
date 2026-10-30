"""Soak relaunch census and heartbeat gap accounting (PAPER_ONLY). Does not invent a 72h clean window."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

NOTES_REL = Path("reports") / "grok" / "M13_SOAK" / "GAP_NOTES.md"
STATUS_REL = Path("reports") / "grok" / "M13_SOAK" / "soak_status.json"
OUT_REL = Path("reports") / "grok" / "M13_SOAK" / "gap_accounting.json"
HEARTBEAT_REL = Path("reports") / "grok" / "M13_SOAK" / "soak_heartbeat.json"
M36_REL = Path("reports") / "grok" / "M36" / "soak_72h_receipt.json"

_RELAUNCH = re.compile(
    r"(?P<stamp>20\d\d-\d\d-\d\dT\d\d:\d\d:\d\d)(?:\s*\(\+03:30\))?.*?"
    r"(?:last cycle ts |Last cycle ts )(?P<last>20\d\d-\d\d-\d\dT\d\d:\d\d:\d\dZ)",
    re.I,
)


def _parse_iso(ts: str) -> datetime:
    if ts.endswith("Z"):
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    if "+" not in ts and "-" not in ts[10:]:
        return datetime.fromisoformat(ts).replace(tzinfo=timezone.utc)
    return datetime.fromisoformat(ts)


def parse_relaunch_lines(text: str) -> list[dict[str, Any]]:
    rows = []
    for i, line in enumerate(text.splitlines(), start=1):
        if "restart" not in line.lower() and "relaunch" not in line.lower() and "daemon via vbs" not in line.lower():
            continue
        m = _RELAUNCH.search(line)
        if not m:
            continue
        stamp_raw = m.group("stamp")
        # GAP_NOTES local stamps without Z are Asia/Tehran (+03:30) when the line says so, else treat as local +03:30
        # because every dated relaunch line in this file is written in +03:30.
        start_local = datetime.fromisoformat(stamp_raw + "+03:30")
        last = _parse_iso(m.group("last"))
        gap_s = (start_local - last).total_seconds()
        kind = "HOST_DOWNTIME" if gap_s >= 3600 else "SHORT_RELAUNCH"
        rows.append(
            {
                "line": i,
                "relaunched_local": start_local.isoformat(),
                "last_cycle_utc": last.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "gap_hours": round(gap_s / 3600, 2),
                "kind": kind,
            }
        )
    return rows


def build_gap_accounting(root: Path) -> dict[str, Any]:
    root = Path(root)
    text = (root / NOTES_REL).read_text(encoding="utf-8") if (root / NOTES_REL).is_file() else ""
    rows = parse_relaunch_lines(text)
    host = [r for r in rows if r["kind"] == "HOST_DOWNTIME"]
    short = [r for r in rows if r["kind"] == "SHORT_RELAUNCH"]
    oct_gap = next((r for r in rows if r["last_cycle_utc"].startswith("2026-10-26T18:45")), None)
    longest = max((r["gap_hours"] for r in rows), default=0)
    return {
        "schema": "ahos.soak_gap_accounting.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "paper_only": True,
        "source": str(NOTES_REL).replace("\\", "/"),
        "relaunch_rows_parsed": len(rows),
        "short_relaunches_under_1h": len(short),
        "host_downtime_gaps": len(host),
        "longest_gap_hours": longest,
        "oct_26_27_gap": oct_gap,
        "root_cause": (
            "Most parsed relaunches are SHORT_RELAUNCH: logon/VBS started a new soak because the previous "
            "process was already gone, often minutes after the last cycle (2026-10-21 burst). "
            "The 2026-10-26 18:45Z to 2026-10-27 14:18 +03:30 row is HOST_DOWNTIME (laptop off or asleep), "
            "not forty separate crashes. A naive same-clock subtraction of those two stamps is about 19.5h; "
            "timezone-correct gap is the gap_hours field."
        ),
        "rows": rows,
    }


def build_heartbeat(root: Path) -> dict[str, Any]:
    root = Path(root)
    status: dict[str, Any] = {}
    path = root / STATUS_REL
    if path.is_file():
        try:
            status = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            status = {}
    last = ((status.get("last_cycle") or {}) if isinstance(status.get("last_cycle"), dict) else {}).get("ts")
    now = datetime.now(timezone.utc)
    age_s = None
    if isinstance(last, str):
        age_s = max(0.0, (now - _parse_iso(last)).total_seconds())
    interval = float(status.get("cycle_interval_sec") or 900)
    return {
        "schema": "ahos.soak_heartbeat.v1",
        "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "paper_only": True,
        "last_cycle_utc": last,
        "cycle_interval_sec": interval,
        "age_sec": None if age_s is None else round(age_s, 1),
        "stale": bool(age_s is None or age_s > interval * 3),
        "cycles_ok": status.get("cycles_ok"),
        "cycles_failed": status.get("cycles_failed"),
    }


def build_m36_72h_receipt(
    accounting: dict[str, Any],
    heartbeat: dict[str, Any],
    *,
    window_started_utc: str | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Historical gaps stay on the receipt. A MET status is only the current window."""
    longest = float(accounting.get("longest_gap_hours") or 0)
    clock = now or datetime.now(timezone.utc)
    elapsed = None
    current = "NOT_RECORDED"
    status = "NOT_MET"
    reason = (
        "GAP_NOTES shows repeated process death and at least one multi-hour host gap. "
        "No unbroken 72h window is claimed."
    )
    if window_started_utc:
        elapsed = round(max(0.0, (clock - _parse_iso(window_started_utc)).total_seconds()) / 3600, 2)
        stale = bool(heartbeat.get("stale"))
        if elapsed >= 72 and not stale:
            status = "MET"
            current = "MET"
            reason = "The current window reached 72 hours and the heartbeat was not stale."
        elif not stale:
            current = "IN_PROGRESS"
            reason = "The current window is running and has not reached 72 hours."
        else:
            current = "STALE"
            reason = "The current window's heartbeat is stale. 72 hours are not claimed."
    return {
        "schema": "ahos.m36_soak_72h_receipt.v1",
        "generated_at": clock.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "paper_only": True,
        "target_continuous_hours": 72,
        "status": status,
        "current_window_status": current,
        "elapsed_hours": elapsed,
        "window_started_utc": window_started_utc,
        "reason": reason,
        "longest_recorded_gap_hours": longest,
        "relaunch_rows_parsed": accounting.get("relaunch_rows_parsed"),
        "heartbeat_stale": heartbeat.get("stale"),
        "last_cycle_utc": heartbeat.get("last_cycle_utc"),
        "auto_restart": "G:/robat/AHOS_Launcher/start_soak.ps1",
    }


def contiguous_window_start(text: str, interval_sec: float) -> str | None:
    """First cycle of the tail that has no gap longer than three intervals."""
    stamps: list[str] = []
    for line in text.splitlines():
        if "cycle" not in line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if row.get("kind") == "cycle" and isinstance(row.get("ts"), str):
            stamps.append(row["ts"])
    if not stamps:
        return None
    start = stamps[-1]
    prev = _parse_iso(stamps[-1])
    limit = float(interval_sec) * 3
    for ts in reversed(stamps[:-1]):
        cur = _parse_iso(ts)
        if (prev - cur).total_seconds() > limit:
            break
        start = ts
        prev = cur
    return start


def verify_logon_lightstart(logs_dir: Path) -> dict[str, Any]:
    """Confirm AHOS_Logon.ps1 invoked LightStart and light_start.log recorded a begin."""
    logs_dir = Path(logs_dir)
    logon = logs_dir / "logon.log"
    light = logs_dir / "light_start.log"
    begins = ends = light_begins = 0
    last_end = None
    if logon.is_file():
        for line in logon.read_text(encoding="utf-8", errors="replace").splitlines():
            if "lightstart invoke begin" in line:
                begins += 1
            if "lightstart invoke end" in line:
                ends += 1
                last_end = line.strip()[-180:]
    if light.is_file():
        light_begins = sum(1 for line in light.read_text(encoding="utf-8", errors="replace").splitlines() if line.endswith(" begin") or " begin" in line)
    return {
        "logs_dir": str(logs_dir),
        "logon_invoke_begins": begins,
        "logon_invoke_ends": ends,
        "light_start_begins": light_begins,
        "chain_seen": begins > 0 and ends > 0 and light_begins > 0,
        "last_logon_end": last_end,
    }


def export_soak_gap_receipts(root: Path) -> dict[str, Any]:
    root = Path(root)
    accounting = build_gap_accounting(root)
    heartbeat = build_heartbeat(root)
    logon = verify_logon_lightstart(root.parent / "AHOS_Launcher" / "logs")
    accounting["logon_lightstart"] = logon
    status_doc: dict[str, Any] = {}
    if (root / STATUS_REL).is_file():
        try:
            loaded = json.loads((root / STATUS_REL).read_text(encoding="utf-8"))
            status_doc = loaded if isinstance(loaded, dict) else {}
        except json.JSONDecodeError:
            status_doc = {}
    started = status_doc.get("window_started_utc") or status_doc.get("started_hint")
    source = "window_started_utc" if status_doc.get("window_started_utc") else "started_hint"
    if not status_doc.get("window_started_utc"):
        runlog = root / "reports" / "grok" / "M13_SOAK" / "soak_runlog.jsonl"
        if runlog.is_file():
            rebuilt = contiguous_window_start(
                runlog.read_text(encoding="utf-8", errors="replace"),
                float(status_doc.get("cycle_interval_sec") or 900),
            )
            if rebuilt:
                started = rebuilt
                source = "runlog_contiguous"
    m36 = build_m36_72h_receipt(accounting, heartbeat, window_started_utc=started if isinstance(started, str) else None)
    m36["window_clock_source"] = source
    m36["logon_lightstart_chain_seen"] = logon["chain_seen"]
    for rel, doc in ((OUT_REL, accounting), (HEARTBEAT_REL, heartbeat), (M36_REL, m36)):
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"accounting": accounting, "heartbeat": heartbeat, "m36": m36}

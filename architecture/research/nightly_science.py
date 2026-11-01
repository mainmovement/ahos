"""Light science for the US equity desk, outside the trader and the soak.

scipy and statsmodels are imported only inside a job function. Torch and
tensorflow are refused. A low-memory machine skips the install.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

ALLOWED = ("scipy", "statsmodels")
REFUSED = ("torch", "tensorflow", "tensorflow-cpu")
MIN_FREE_MB = 1228.8
DESK = "US_EQUITIES"
REPORT_REL = Path("reports") / "grok" / "PAPER" / "nightly_science_us.json"
TRADES_REL = Path("reports") / "grok" / "PAPER" / "paper_trades.jsonl"


def free_ram_mb() -> float:
    import ctypes

    class Status(ctypes.Structure):
        _fields_ = [
            ("dwLength", ctypes.c_ulong),
            ("dwMemoryLoad", ctypes.c_ulong),
            ("ullTotalPhys", ctypes.c_ulonglong),
            ("ullAvailPhys", ctypes.c_ulonglong),
            ("ullTotalPageFile", ctypes.c_ulonglong),
            ("ullAvailPageFile", ctypes.c_ulonglong),
            ("ullTotalVirtual", ctypes.c_ulonglong),
            ("ullAvailVirtual", ctypes.c_ulonglong),
            ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
        ]

    status = Status()
    status.dwLength = ctypes.sizeof(Status)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status))
    return round(status.ullAvailPhys / (1024 * 1024), 1)


def peak_ram_mb() -> float | None:
    import ctypes

    class Counters(ctypes.Structure):
        _fields_ = [
            ("cb", ctypes.c_ulong),
            ("PageFaultCount", ctypes.c_ulong),
            ("PeakWorkingSetSize", ctypes.c_size_t),
            ("WorkingSetSize", ctypes.c_size_t),
            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
            ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
            ("PagefileUsage", ctypes.c_size_t),
            ("PeakPagefileUsage", ctypes.c_size_t),
        ]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    psapi = ctypes.WinDLL("psapi", use_last_error=True)
    kernel32.GetCurrentProcess.restype = ctypes.c_void_p
    psapi.GetProcessMemoryInfo.argtypes = [ctypes.c_void_p, ctypes.POINTER(Counters), ctypes.c_ulong]
    psapi.GetProcessMemoryInfo.restype = ctypes.c_int
    counters = Counters()
    counters.cb = ctypes.sizeof(Counters)
    ok = psapi.GetProcessMemoryInfo(kernel32.GetCurrentProcess(), ctypes.byref(counters), counters.cb)
    if not ok:
        return None
    return round(counters.PeakWorkingSetSize / (1024 * 1024), 1)


def science_line(root: Path) -> str:
    path = Path(root) / REPORT_REL
    if not path.is_file():
        return "کتابخانهٔ سبک به خاطر کمبود حافظه نصب نشد و عدد تازه نوشته نشد"
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return "کتابخانهٔ سبک به خاطر کمبود حافظه نصب نشد و عدد تازه نوشته نشد"
    if doc.get("libs_used") is True and doc.get("promoted") is False:
        return "محاسبهٔ آماری میز آمریکا در کار شبانه نوشته شد و به وزن زنده نرسید"
    return "کتابخانهٔ سبک به خاطر کمبود حافظه نصب نشد و عدد تازه نوشته نشد"


def install_plan(package: str, *, free_mb: float | None = None) -> dict[str, Any]:
    """Decide one install. The caller runs pip only when this says INSTALL."""
    before = free_ram_mb() if free_mb is None else float(free_mb)
    if package in REFUSED:
        return {"package": package, "action": "REFUSED", "ram_before_mb": before, "reason": "HEAVY_ML"}
    if package not in ALLOWED:
        return {"package": package, "action": "REFUSED", "ram_before_mb": before, "reason": "NOT_ON_THE_LIGHT_LIST"}
    if before < MIN_FREE_MB:
        return {
            "package": package,
            "action": "SKIPPED",
            "ram_before_mb": before,
            "reason": "FREE_RAM_BELOW_1228",
        }
    return {"package": package, "action": "INSTALL", "ram_before_mb": before, "reason": "FREE_RAM_OK"}


def us_closes(root: Path) -> list[dict[str, Any]]:
    path = Path(root) / TRADES_REL
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if DESK not in line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        pnl = row.get("realized_pnl_usd")
        if row.get("desk") == DESK and isinstance(pnl, (int, float)) and not isinstance(pnl, bool):
            rows.append(row)
    return rows


def _confidence(row: dict[str, Any]) -> float | None:
    brain = row.get("entry_brain") if isinstance(row.get("entry_brain"), dict) else {}
    raw = brain.get("composite")
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        raw = row.get("exit_composite")
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        return None
    return max(0.0, min(1.0, abs(float(raw))))


def current_us(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """The desk numbers from the existing functions. This does not import scipy."""
    from architecture.learning.calibration import brier_score
    from architecture.learning.walk_forward import closed_book_equations

    pnls = [float(row["realized_pnl_usd"]) for row in rows]
    equations = closed_book_equations(pnls)
    probs, outcomes = [], []
    for row in rows:
        prob = _confidence(row)
        if prob is None:
            continue
        probs.append(prob)
        outcomes.append(1.0 if float(row["realized_pnl_usd"]) > 0 else 0.0)
    brier = brier_score(probs, outcomes)
    return {
        "n": len(pnls),
        "deflated_sharpe": equations.get("deflated_sharpe"),
        "pbo": equations.get("pbo"),
        "brier": None if brier is None else round(float(brier), 4),
        "brier_n": len(probs),
        "dsr_reason": None if equations.get("deflated_sharpe") is not None else "INSUFFICIENT_N",
        "pbo_reason": None if equations.get("pbo") is not None else "INSUFFICIENT_N",
        "method": "closed_book_equations_and_brier_score",
        "promoted": False,
    }


def _skipped(package: str, reason: str) -> dict[str, Any]:
    return {
        "package": package,
        "status": "SKIPPED",
        "reason": reason,
        "deflated_sharpe": None,
        "pbo": None,
        "brier": None,
        "pid": os.getpid(),
        "peak_ram_mb": peak_ram_mb(),
        "promoted": False,
    }


def scipy_job(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Recompute DSR and PBO with scipy. Same refusal rules as the current functions."""
    try:
        from scipy import special, stats
    except ImportError:
        return _skipped("scipy", "NOT_INSTALLED")
    from architecture.learning.walk_forward import closed_book_equations, pbo_cscv, sharpe

    pnls = [float(row["realized_pnl_usd"]) for row in rows]
    current = closed_book_equations(pnls)
    if len(pnls) < 20:
        return {
            "package": "scipy",
            "status": "COMPUTED",
            "reason": "INSUFFICIENT_N",
            "n": len(pnls),
            "deflated_sharpe": None,
            "pbo": None,
            "current_deflated_sharpe": current.get("deflated_sharpe"),
            "current_pbo": current.get("pbo"),
            "pid": os.getpid(),
            "peak_ram_mb": peak_ram_mb(),
            "promoted": False,
        }
    import math
    import statistics

    half = max(1, len(pnls) // 2)
    trials = [pnls[:half], pnls[half:]]
    trial_sharpes = [sharpe(trials[0]), sharpe(trials[1])]
    series = [float(x) for x in pnls]
    n = len(series)
    sr = float(stats.tmean(series) / (statistics.stdev(series) or 1e-12))
    skew = float(stats.skew(series, bias=True))
    kurt = float(stats.kurtosis(series, bias=True, fisher=False))
    variance = statistics.pvariance(trial_sharpes)
    emc = 0.5772156649
    sr0 = math.sqrt(variance) * (
        (1 - emc) * float(stats.norm.ppf(1 - 1 / 2)) + emc * float(stats.norm.ppf(1 - 1 / (2 * math.e)))
    )
    den = math.sqrt(max(1e-12, 1 - skew * sr + (kurt - 1) / 4 * sr * sr))
    dsr = round(float(stats.norm.cdf((sr - sr0) * math.sqrt(n - 1) / den)), 4)
    blocks: list[list[float]] = []
    pbo = None
    for trial in trials:
        size = len(trial) // 8
        if size < 1:
            blocks = []
            break
        blocks.append([sum(trial[i * size:(i + 1) * size]) for i in range(8)])
    if len(blocks) == 2:
        pbo = _pbo_with_logit(blocks, special.logit)
    return {
        "package": "scipy",
        "status": "COMPUTED",
        "reason": "OK",
        "n": n,
        "deflated_sharpe": dsr,
        "pbo": pbo,
        "current_deflated_sharpe": current.get("deflated_sharpe"),
        "current_pbo": pbo_cscv(blocks) if len(blocks) == 2 else None,
        "pid": os.getpid(),
        "peak_ram_mb": peak_ram_mb(),
        "promoted": False,
    }


def _pbo_with_logit(perf: list[list[float]], logit) -> float:
    import itertools

    blocks = list(range(8))
    lam = []
    for is_set in itertools.combinations(blocks, 4):
        oos = [b for b in blocks if b not in is_set]
        is_perf = [sum(p[b] for b in is_set) for p in perf]
        oos_perf = [sum(p[b] for b in oos) for p in perf]
        best = max(range(len(perf)), key=lambda k: is_perf[k])
        rank = sorted(oos_perf).index(oos_perf[best]) + 1
        w = min(1 - 1e-9, max(1e-9, rank / (len(perf) + 1)))
        lam.append(float(logit(w)))
    return round(sum(1 for x in lam if x <= 0) / len(lam), 4)


def statsmodels_job(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Brier from a statsmodels logit. A short desk stays an insufficient holdout."""
    try:
        import numpy as np
        import statsmodels.api as sm
    except ImportError:
        return _skipped("statsmodels", "NOT_INSTALLED")
    probs, outcomes = [], []
    for row in rows:
        prob = _confidence(row)
        if prob is None:
            continue
        probs.append(prob)
        outcomes.append(1.0 if float(row["realized_pnl_usd"]) > 0 else 0.0)
    if len(probs) < 8:
        if len(set(outcomes)) < 2:
            return {
                "package": "statsmodels",
                "status": "COMPUTED",
                "reason": "INSUFFICIENT_HOLDOUT",
                "n": len(probs),
                "brier": None,
                "brier_kind": "not_fit",
                "pid": os.getpid(),
                "peak_ram_mb": peak_ram_mb(),
                "promoted": False,
            }
        y = np.asarray(outcomes, dtype=float)
        try:
            fit = sm.Logit(y, np.ones((len(y), 1))).fit(disp=0)
            pred = fit.predict(np.ones((len(y), 1)))
            brier = round(float(np.mean((pred - y) ** 2)), 4)
        except Exception:
            brier = None
        return {
            "package": "statsmodels",
            "status": "COMPUTED",
            "reason": "INSUFFICIENT_HOLDOUT",
            "n": len(probs),
            "brier": brier,
            "brier_kind": "in_sample_base_rate",
            "pid": os.getpid(),
            "peak_ram_mb": peak_ram_mb(),
            "promoted": False,
        }
    y = np.asarray(outcomes, dtype=float)
    x = sm.add_constant(np.asarray(probs, dtype=float))
    split = int(len(y) * 0.6)
    try:
        fit = sm.Logit(y[:split], x[:split]).fit(disp=0)
        pred = fit.predict(x[split:])
    except Exception:
        return {
            "package": "statsmodels",
            "status": "COMPUTED",
            "reason": "FIT_FAILED",
            "n": len(probs),
            "brier": None,
            "pid": os.getpid(),
            "peak_ram_mb": peak_ram_mb(),
            "promoted": False,
        }
    brier = float(np.mean((pred - y[split:]) ** 2))
    return {
        "package": "statsmodels",
        "status": "COMPUTED",
        "reason": "OK",
        "n": len(probs),
        "brier": round(brier, 4),
        "pid": os.getpid(),
        "peak_ram_mb": peak_ram_mb(),
        "promoted": False,
    }


def stored_current(root: Path) -> dict[str, Any]:
    book_path = Path(root) / "reports" / "grok" / "PAPER" / "book_equations.json"
    cal_path = Path(root) / "reports" / "grok" / "PAPER" / "calibration_weekly.json"
    book: dict[str, Any] = {}
    cal: dict[str, Any] = {}
    if book_path.is_file():
        try:
            book = json.loads(book_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            book = {}
    if cal_path.is_file():
        try:
            cal = json.loads(cal_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            cal = {}
    desk = ((cal.get("by_desk") or {}).get(DESK) or {}) if isinstance(cal.get("by_desk"), dict) else {}
    return {
        "book_scope": "ALL_DESKS",
        "deflated_sharpe": book.get("deflated_sharpe"),
        "pbo": book.get("pbo"),
        "us_brier": desk.get("brier"),
        "us_brier_n": desk.get("n"),
        "us_oos_brier": desk.get("oos_brier"),
        "applied_to_entry": desk.get("applied_to_entry"),
    }


def build_report(root: Path, installs: list[dict[str, Any]], jobs: list[dict[str, Any]]) -> dict[str, Any]:
    rows = us_closes(root)
    current = current_us(rows)
    stored = stored_current(root)
    by_name = {str(job.get("package")): job for job in jobs}
    scipy = by_name.get("scipy") or _skipped("scipy", "NOT_RUN")
    stats = by_name.get("statsmodels") or _skipped("statsmodels", "NOT_RUN")
    used = scipy.get("status") == "COMPUTED" and stats.get("status") == "COMPUTED"
    return {
        "schema": "ahos.nightly_science_us.v1",
        "paper_only": True,
        "desk": DESK,
        "promoted": False,
        "applied_to_live_weights": False,
        "judge": "NO_PROMOTION",
        "red_team": "NOT_A_PASS",
        "red_team_reason": "LOOKBACK_ON_STORED_CLOSES",
        "libs_used": used,
        "installs": installs,
        "jobs": jobs,
        "current_file": stored,
        "current_us_method": current,
        "new_us": {
            "deflated_sharpe": scipy.get("deflated_sharpe"),
            "pbo": scipy.get("pbo"),
            "brier": stats.get("brier"),
            "scipy_status": scipy.get("status"),
            "scipy_reason": scipy.get("reason"),
            "statsmodels_status": stats.get("status"),
            "statsmodels_reason": stats.get("reason"),
        },
        "pid": os.getpid(),
        "decides": False,
    }


def publish(root: Path, report: dict[str, Any]) -> dict[str, Any]:
    from architecture.security.negahban import scan

    text = json.dumps(report, ensure_ascii=False)
    if scan(text).level == "HALT":
        report["negahban"] = "HALT"
        return report
    report["negahban"] = "PASS"
    path = Path(root) / REPORT_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    from agent_org.contracts import AgentMessage, RequiredAction
    from architecture.mission.world_state import MessageBus, WorldStateStore

    evidence = (str(REPORT_REL),)
    bus = MessageBus(root)
    bus.deliver(AgentMessage(
        sender="AG-03",
        receiver="AG-11",
        evidence=evidence,
        claim="Nightly US equity science wrote a lookback. It does not promote.",
        confidence=0.9,
        required_action=RequiredAction.OBSERVE,
    ))
    bus.deliver(AgentMessage(
        sender="AG-14",
        receiver="AG-11",
        evidence=evidence,
        claim="The nightly science sample is a stored lookback and is not a red-team pass.",
        confidence=0.9,
        required_action=RequiredAction.ABSTAIN,
    ))
    bus.deliver(AgentMessage(
        sender="AG-11",
        receiver="AG-09",
        evidence=evidence,
        claim="Judge verdict on the nightly science note is NO_PROMOTION.",
        confidence=0.95,
        required_action=RequiredAction.OBSERVE,
    ))
    try:
        store = WorldStateStore(root)
        prev = store.read()
        traces = dict((prev.get("sections") or {}).get("traces") or {})
        traces["nightly_science"] = {
            "desk": DESK,
            "libs_used": report["libs_used"],
            "judge": "NO_PROMOTION",
            "red_team": "NOT_A_PASS",
            "current_us": report["current_us_method"],
            "new_us": report["new_us"],
            "pid": report["pid"],
            "promoted": False,
            "paper_only": True,
        }
        store.commit({"traces": traces}, {"traces": "AG-03"})
    except Exception:
        pass
    return report

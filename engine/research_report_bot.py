#!/usr/bin/env python3
"""AHOS Research Report broadcaster — formats the lab registry into the Telegram digest and
sends via the SAME env-guarded path as telegram_live_test.py (REAL only with env vars; else SIMULATED transcript).
Output: telegram message text + dispatch record → research/reports/telegram_dispatch.json"""
import os, sys, json
from datetime import datetime, timezone
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config.paths import get_research_dir

def build_digest():
    """Render the FULL registry (13 hypotheses across batches). Each candidate points to its own
    evidence log; scoped candidates (e.g. H13 BTC-only) render only the symbols actually tested.
    Never fabricate per-symbol numbers for untested scopes (T-04 fix)."""
    reg_file = ROOT_DIR / "strategy_lab" / "registry.json"
    reg = json.loads(reg_file.read_text(encoding="utf-8"))
    logs = {}
    def load_log(fname):
        if fname not in logs:
            log_file = get_research_dir() / "experiments" / fname
            logs[fname] = json.loads(log_file.read_text(encoding="utf-8"))
        return logs[fname]
    latest = load_log(reg["experiment_log"])
    lines = ["AHOS RESEARCH DIGEST", f"ts: {datetime.now(timezone.utc):%Y-%m-%d %H:%M}Z",
             f"data: real 3.6y tri-asset + 6.6y BTC-ext (sha {list(latest['data'].values())[0]}…)",
             "gates: base PF>1.3 OOS, exp>0, DD<15%, MC>70%, WF>=60%, stress>1.1; batch-2/3 bar PF>1.5", ""]
    acc = testable = 0
    for hid, meta in reg["candidates"].items():
        if meta["status"] != "TESTED":
            lines.append(f"{hid} {meta['name']}: {meta['verdict']} (data-blocked: L2 order book)"); continue
        c = load_log(meta["evidence"])["candidates"][hid]
        syms = [s for s in c["per_symbol"]]
        fmt = lambda v: ("—" if v is None else v)  # truthful: None = zero trades (falsified by zero-signal)
        symline = " | ".join(f"{s[:3]} OOS-PF {fmt(c['per_symbol'][s]['oos']['pf'])}" for s in syms)
        scope = "" if set(syms) == {"BTCUSDT","ETHUSDT","SOLUSDT"} else f" [scope: {'/'.join(syms)}, 6.6y ext]"
        lines.append(f"{hid} {c['name']}: {c['verdict']} ({symline}){scope}")
        testable += 1
        acc += c["verdict"] == "ACCEPTED"
    lines += ["", f"accepted: {acc}/{testable} testable ({len(reg['candidates'])} registered) | live gate: CLOSED",
              "no parameter tuning performed · full logs in research/experiments/"]
    return "\n".join(lines)

def main():
    text = build_digest()
    print(text + "\n" + "-"*60)
    token, chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_ADMIN_CHAT_ID")
    record = {"ts": datetime.now(timezone.utc).isoformat(), "text": text}
    if token and chat and "--simulate" not in sys.argv:
        import urllib.request, urllib.parse  # independent transport (no harness import side-effects)
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        req = urllib.request.Request(url, data=urllib.parse.urlencode({"chat_id": chat, "text": text}).encode())
        with urllib.request.urlopen(req, timeout=15) as r:
            record.update(mode="REAL_SEND", api_ok=json.loads(r.read()).get("ok"))
        print("REAL send:", record["api_ok"])
    else:
        record.update(mode="SIMULATED", reason="no env credentials (or --simulate)")
        print("SIMULATED dispatch (no credentials in environment) — transcript captured.")
    out_dispatch = get_research_dir() / "reports" / "telegram_dispatch.json"
    out_dispatch.parent.mkdir(parents=True, exist_ok=True)
    out_dispatch.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")

if __name__ == "__main__":
    main()

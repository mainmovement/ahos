#!/usr/bin/env python3
"""AHOS n8n Workflow Validator — Agent-09 QA + Agent-04 Security.
Structural validation for n8n import-readiness. Exit 1 on any FAIL."""
import json, re, sys, glob

SECRET_PATTERNS = [
    (re.compile(r"\b\d{8,10}:[A-Za-z0-9_-]{35}\b"), "telegram bot token literal"),
    (re.compile(r"(?i)(api[_-]?key|api[_-]?secret|password)\s*[:=]\s*['\"][^'\"]{8,}['\"]"), "hardcoded credential"),
]
REQUIRED_NODE_KEYS = {"parameters", "id", "name", "type", "typeVersion", "position"}

def validate(path):
    errs, warns = [], []
    with open(path, encoding="utf-8") as f:
        try:
            wf = json.load(f)
        except Exception as e:
            return [f"JSON parse error: {e}"], []
    nodes = {n["name"]: n for n in wf.get("nodes", [])}
    # 1. node structural keys
    for n in wf["nodes"]:
        missing = REQUIRED_NODE_KEYS - set(n.keys())
        if missing: errs.append(f"node '{n.get('name','?')}' missing keys: {missing}")
        if not isinstance(n.get("position"), list) or len(n["position"]) != 2:
            errs.append(f"node '{n['name']}' invalid position")
    # 2. unique names + ids
    names = list(nodes.keys())
    if len(names) != len(set(names)): errs.append("duplicate node names")
    ids = [n["id"] for n in wf["nodes"]]
    if len(ids) != len(set(ids)): errs.append("duplicate node ids")
    # 3. connection integrity (bidirectional reference check)
    conns = wf.get("connections", {})
    for src, outs in conns.items():
        if src not in nodes: errs.append(f"connection source '{src}' not a node"); continue
        for group in outs.get("main", []):
            if group is None: continue
            for edge in group:
                if edge["node"] not in nodes:
                    errs.append(f"connection target '{edge['node']}' (from '{src}') not a node")
    # 4. reachability: every non-trigger node reachable from a trigger
    triggers = [n for n in wf["nodes"] if "Trigger" in n["type"] or "scheduleTrigger" in n["type"]]
    if not triggers: errs.append("no trigger node")
    reachable = set()
    frontier = [t["name"] for t in triggers]
    while frontier:
        cur = frontier.pop()
        if cur in reachable: continue
        reachable.add(cur)
        for group in conns.get(cur, {}).get("main", []):
            if group:
                for edge in group: frontier.append(edge["node"])
    for n in wf["nodes"]:
        if n["name"] not in reachable and not n.get("disabled"):
            errs.append(f"node '{n['name']}' unreachable from triggers")
    # 5. secret scan over entire file text
    raw = open(path, encoding="utf-8").read()
    for pat, label in SECRET_PATTERNS:
        if pat.search(raw): errs.append(f"possible {label} present in file")
    # 6. credentials must be placeholders (never real ids inline as numbers)
    for n in wf["nodes"]:
        for cred_type, cred in (n.get("credentials") or {}).items():
            if str(cred.get("id", "")).isdigit():
                errs.append(f"node '{n['name']}' has real numeric credential id inline")
    # 7. workflow governance checks
    has_telegram_alerts = any(n["type"] == "n8n-nodes-base.telegram" for n in wf["nodes"])
    if not has_telegram_alerts: warns.append("no telegram alert node (notifications absent)")
    if "telegramTrigger" not in raw:
        err_nodes = [n for n in wf["nodes"] if n.get("onError") == "continueErrorOutput"]
        if not err_nodes: warns.append("no error-output routing on any node (failure path weak)")
    return errs, warns

if __name__ == "__main__":
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    wf_dir = root / "n8n" / "workflows"
    fail_total = 0
    for path in sorted(wf_dir.glob("*.json")):
        errs, warns = validate(str(path))
        status = "FAIL" if errs else ("PASS(warn)" if warns else "PASS")
        print(f"[{status}] {path.name}")
        for e in errs: print(f"   ERROR: {e}")
        for w in warns: print(f"   WARN : {w}")
        fail_total += len(errs)
    sys.exit(1 if fail_total else 0)

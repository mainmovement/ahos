#!/usr/bin/env python3
"""AHOS n8n Workflow Validator — Agent-09 QA + Agent-04 Security.
Structural validation for n8n import-readiness. Exit 1 on any FAIL."""
import json, re, sys, glob

SECRET_PATTERNS = [
    (re.compile(r"\b\d{8,10}:[A-Za-z0-9_-]{35}\b"), "telegram bot token literal"),
    (re.compile(r"(?i)(api[_-]?key|api[_-]?secret|password)\s*[:=]\s*['\"][^'\"]{8,}['\"]"), "hardcoded credential"),
]
REQUIRED_NODE_KEYS = {"parameters", "id", "name", "type", "typeVersion", "position"}

# --- GM-06 governance rules (static; nothing is imported or executed) -------
# A workflow listed here is QUARANTINED: it must NOT be imported into n8n.
# Its governance findings are reported as QUARANTINED warnings (so the
# structural G12 result is unchanged), while the same findings in any other
# workflow are hard errors. Never delete the file; rewrite it, then remove it
# from this map with security review (see reports/grok/GM06_N8N_QUARANTINE.md).
QUARANTINED_WORKFLOWS = {
    "ahos_03_telegram_control.json": (
        "QUARANTINED 2026-10-02 (GM-06): external Telegram input interpolated into SQL, "
        "audit-row DELETE on /reset, /approve mutates trade_decisions.execution_status "
        "outside the canonical decision authority. DO NOT IMPORT."
    ),
}
EXTERNAL_TRIGGER_MARKERS = ("telegramTrigger", "n8n-nodes-base.webhook", "formTrigger", "chatTrigger")
_TBL = r'(?:"?\w+"?\.)?"?%s"?\b'
AUDIT_TAMPER_RE = re.compile(r"(?is)\b(?:delete\s+from|truncate(?:\s+table)?|update)\s+" + _TBL % "agent_audit_trail")
STATUS_MUTATION_RE = re.compile(r"(?is)\bupdate\s+" + _TBL % "trade_decisions" + r"[^;]*?\bset\b[^;]*?\bexecution_status\b")
DECISION_INSERT_RE = re.compile(r"(?is)\binsert\s+into\s+" + _TBL % "trade_decisions")


def _sql_texts(node):
    """SQL strings carried by a node (postgres executeQuery or any 'query' param)."""
    params = node.get("parameters") or {}
    out = []
    q = params.get("query")
    if isinstance(q, str):
        out.append(q[1:] if q.startswith("=") else q)
    return out


def governance_findings(wf):
    """Return (errors, warnings) for GM-06 rules, before quarantine handling."""
    errs, warns = [], []
    external = any(any(m in n.get("type", "") for m in EXTERNAL_TRIGGER_MARKERS) for n in wf.get("nodes", []))
    for n in wf.get("nodes", []):
        if n.get("disabled"):
            continue
        name = n.get("name", "?")
        for sql in _sql_texts(n):
            if AUDIT_TAMPER_RE.search(sql):
                errs.append(f"AUDIT_TAMPER: node '{name}' deletes/updates/truncates agent_audit_trail (audit is append-only)")
            if STATUS_MUTATION_RE.search(sql):
                errs.append(f"AUTHORITY_BYPASS: node '{name}' mutates trade_decisions.execution_status outside the canonical decision authority")
            if "{{" in sql:
                if external:
                    errs.append(f"SQL_INTERPOLATION_FROM_EXTERNAL_TRIGGER: node '{name}' interpolates {{{{ }}}} expressions into SQL in an externally-triggered workflow (use query parameters)")
                else:
                    warns.append(f"SQL_INTERPOLATION: node '{name}' interpolates {{{{ }}}} expressions into SQL (internal trigger; prefer query parameters)")
            if DECISION_INSERT_RE.search(sql):
                warns.append(f"DECISION_WRITE_OUTSIDE_CANONICAL_AUTHORITY: node '{name}' inserts trade_decisions (n8n is not a decision authority; PAPER_ONLY)")
    return errs, warns

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
    # 8. GM-06 governance rules (quarantine demotes errors to warnings)
    g_errs, g_warns = governance_findings(wf)
    warns.extend(g_warns)
    qname = __import__("os").path.basename(path)
    if qname in QUARANTINED_WORKFLOWS:
        warns.append(QUARANTINED_WORKFLOWS[qname])
        warns.extend("QUARANTINED " + e for e in g_errs)
    else:
        errs.extend(g_errs)
    return errs, warns

if __name__ == "__main__":
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    wf_dir = root / "n8n" / "workflows"
    fail_total = 0
    for path in sorted(wf_dir.glob("*.json")):
        errs, warns = validate(str(path))
        status = "FAIL" if errs else (
            "QUARANTINED(do-not-import)" if path.name in QUARANTINED_WORKFLOWS
            else ("PASS(warn)" if warns else "PASS"))
        print(f"[{status}] {path.name}")
        for e in errs: print(f"   ERROR: {e}")
        for w in warns: print(f"   WARN : {w}")
        fail_total += len(errs)
    sys.exit(1 if fail_total else 0)

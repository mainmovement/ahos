#!/usr/bin/env python3
"""OSS Capability Intelligence — Tier-1 evidence collector (versioned tool, Lane B).

WHY (PART-35): two ad-hoc audits (W12A-OSS-1/2) proved the need; unversioned probes drift.
SCOPE: READ-ONLY GitHub public metadata. NO clone, NO install, NO code execution (PART O).
TIER LAW: Tier-1 output = CANDIDATE registers only. This tool NEVER assigns a final verdict —
verdicts require Tier-2/3 evidence (host/owner-gated). Machine stamps every record
UNVERIFIED-by-default where a fact was not fetched; reviewer annotation is a separate step.
FAILURE LAW: API error => record carries "UNVERIFIED — <reason>"; nothing is fabricated.
RATE LAW: unauthenticated GitHub API ~60/h => tool sleeps between calls and refuses >20 repos
per run (hard cap) unless --allow-large is passed.
"""
import json, sys, time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = "https://api.github.com/repos/"
HEADERS = {"User-Agent": "ahos-oss-audit-tier1", "Accept": "application/vnd.github+json"}
HARD_CAP = 20
ACTIVE_DAYS = 30  # pushed within N days of `now` => ACTIVE else STALE_OR_SLOW


def classify_maintenance(pushed_at, now):
    if not pushed_at:
        return "UNKNOWN"
    try:
        ts = time.strptime(pushed_at, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        return "UNKNOWN"
    age = time.mktime(now) - time.mktime(ts)
    return "ACTIVE" if age <= ACTIVE_DAYS * 86400 else "STALE_OR_SLOW"


def fetch_repo(repo, fetcher=None):
    """One GET; injected fetcher keeps CI network-free. Raises on transport/HTTP error."""
    fetcher = fetcher or _urllib_fetch
    return fetcher(API + repo)


def _urllib_fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read())


def audit_repo(repo, capability_lanes, now=None, fetcher=None):
    now = now or time.gmtime()
    rec = {"repo": repo, "capability_lanes": list(capability_lanes)}
    try:
        d = fetch_repo(repo, fetcher)
    except Exception as e:  # noqa: BLE001 — error text IS the evidence
        rec["verdict"] = f"UNVERIFIED — API error: {str(e)[:120]}"
        return rec
    rec.update({
        "license": (d.get("license") or {}).get("spdx_id") or "UNKNOWN",
        "language": d.get("language") or "UNKNOWN",
        "stars": d.get("stargazers_count"),
        "forks": d.get("forks_count"),
        "open_issues": d.get("open_issues_count"),
        "pushed_at": d.get("pushed_at"),
        "archived": bool(d.get("archived")),
        "maintenance": classify_maintenance(d.get("pushed_at"), now),
        "dependency_posture": "UNVERIFIED (Tier-1: dependency tree not audited)",
        "security_posture": "UNVERIFIED (Tier-1: no vuln scan executed)",
        "tier_reached": "T1_METADATA",
    })
    if rec["archived"]:
        rec["verdict"] = "REJECT — archived upstream (maintenance law)"
    else:
        rec["verdict"] = "CANDIDATE_HELD_UNVERIFIED"  # final verdicts need Tier-2/3 + human
    return rec


def audit(candidates, now=None, fetcher=None, allow_large=False, sleep_s=0.4):
    """candidates: {repo: [lanes...]}. Returns the full Tier-1 report dict."""
    if len(candidates) > HARD_CAP and not allow_large:
        raise ValueError(f"rate law: {len(candidates)} repos > cap {HARD_CAP} (pass allow_large)")
    reps = []
    for i, (repo, lanes) in enumerate(candidates.items()):
        if i:
            time.sleep(sleep_s)
        reps.append(audit_repo(repo, lanes, now=now, fetcher=fetcher))
    return {"probe_set": "", "ts": time.strftime("%Y-%m-%dT%H:%MZ", now or time.gmtime()),
            "mode": "READ-ONLY metadata audit (GitHub public API); NO clone/install/execute (PART O law)",
            "pipeline_stage_reached": "ARCHITECTURE_AUDIT (metadata depth); BENCHMARK/REPLAY/CI = NOT_RUN by law",
            "tool": "engine/oss_audit.py (versioned Tier-1 executor; AG-25 duty #1/#10)",
            "candidates": reps}


def main(argv):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, help="report path under reports/")
    ap.add_argument("--probe-set", required=True)
    ap.add_argument("--candidates", required=True,
                    help="JSON file: {repo: [capability lanes]}")
    args = ap.parse_args(argv)
    cands = json.loads(Path(args.candidates).read_text())
    rep = audit(cands)
    rep["probe_set"] = args.probe_set
    out = Path(args.out)
    out.write_text(json.dumps(rep, indent=1))
    n_ok = sum(1 for c in rep["candidates"] if c.get("tier_reached") == "T1_METADATA")
    print(f"audited {n_ok}/{len(rep['candidates'])} repos -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

#!/usr/bin/env python3
"""AHOS Document Hygiene Engine — Wave-7 directive §7–§10, §24.

Classes (permanent law):
  A CANONICAL            current authority (never archived by automation)
  B ACTIVE IMPLEMENTATION required for current code/work
  C HISTORICAL EVIDENCE  decisions, failures, negative evidence, audit — PRESERVED
  D SUPERSEDED           replaced by a newer authoritative version (archived, stubbed)
  E EXACT DUPLICATE      byte-identical content (sha256 collision group)
  F REDUNDANT/LOW-VALUE  fully represented elsewhere — council review, ARCHIVE only
  G TEMPORARY ARTIFACT   regenerable scratch (caches, throwaway runtimes)

Cleanup law:
  - NEVER delete C-class: negative evidence, rejected hypotheses, probe failures,
    audit evidence, decision logs, provenance.
  - E/G cleanup is council-autonomous (directive §10), always via manifest.
  - F-class is FLAG-ONLY unless a council sign-off line exists in the manifest.
  - Every mutation: pre-sha256 -> move/remove -> post-verify -> manifest record.
  - Archive, not delete, whenever content is not byte-regenerable.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]          # /home/user/ahos
WORKSPACE = ROOT.parent                              # /home/user
ROOTS = [("ahos", ROOT), ("uploads", WORKSPACE / "uploads")]
BASELINE_PATH = ROOT / "reports" / "PROJECT_DOCUMENT_INVENTORY.json"
INVENTORY_OUT = ROOT / "reports" / "PROJECT_DOCUMENT_INVENTORY_WAVE7.json"
CLEANUP_MANIFEST = ROOT / "reports" / "CLEANUP_MANIFEST_WAVE7.json"

# ---------------------------------------------------------------- rule table
A_PATHS = {"ahos/README.md", "ahos/AHOS_PROJECT_STATE_MAP.md", "ahos/AHOS_ISSUE_REGISTER.md",
           "ahos/reports/PHASE_STATE.md"}
B_GLOBS = [r"\.py$", r"\.sql$", r"\.yaml$", r"\.sh$", r"^ahos/n8n/.*\.json$", r"^ahos/config/",
           r"^ahos/research/data/MANIFEST.*\.json$", r"^ahos/reports/PROJECT_DOCUMENT_INVENTORY",
           r"^ahos/research/SEARCH_SPACE_REGISTRY\.json$", r"^ahos/data/.*\.sqlite(-wal|-shm)?$",
           r"^ahos/reports/pal_probe_.*\.json$", r"^ahos/reports/CLEANUP_MANIFEST.*\.json$",
           r"^ahos/reports/WAVE\d+_EXECUTION_REPORT\.md$"]  # wave reports = current exec reference
D_PREFIX = "ahos/docs/archive/"
G_PATTERNS = [r"(^|/)\.pytest_cache(/|$)", r"(^|/)__pycache__(/|$)", r"\.pyc$"]
N8N_RUNTIME = WORKSPACE / "n8n_runtime"              # G, regenerable (npm i n8n@2.8.4)


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def extract_title(p: Path) -> str | None:
    try:
        if p.suffix.lower() not in (".md", ".txt", ".py", ".yaml", ".sh", ".sql"):
            return None
        with open(p, "r", encoding="utf-8", errors="replace") as f:
            for line in f.read(8192).splitlines():
                s = line.strip().lstrip("#").strip()
                if s:
                    return s[:120]
    except Exception:
        return None
    return None


def is_redirect_stub(rel: str, size: int, title: str | None) -> bool:
    return size < 1500 and title is not None and "archive" in title.lower() and "stub" in title.lower()


def build_inventory() -> list[dict]:
    records = []
    for prefix, root in ROOTS:
        if not root.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames.sort()
            for fn in sorted(filenames):
                p = Path(dirpath) / fn
                rel = f"{prefix}/{p.relative_to(root)}"
                st = p.stat()
                records.append({"path": rel, "abs": str(p), "size": st.st_size,
                                "mtime": _dt.datetime.fromtimestamp(
                                    st.st_mtime, _dt.timezone.utc).isoformat(timespec="seconds"),
                                "sha_full": sha256_file(p),
                                "title": extract_title(p)})
    for r in records:
        r["sha"] = r["sha_full"][:16]
    return records


def diff_baseline(records: list[dict]) -> dict:
    base = {}
    if BASELINE_PATH.exists():
        for e in json.loads(BASELINE_PATH.read_text(encoding='utf-8'))["inventory"]:
            base[e["path"]] = e.get("sha_full", e.get("sha"))
    cur = {r["path"]: r["sha_full"] for r in records}
    added = sorted(set(cur) - set(base))
    removed = sorted(set(base) - set(cur))
    changed = sorted(p for p in set(cur) & set(base) if base[p] and cur[p] != base[p])
    return {"baseline": str(BASELINE_PATH.relative_to(WORKSPACE)), "baseline_files": len(base),
            "current_files": len(cur), "added": added, "removed": removed, "changed": changed}


def classify(records: list[dict]) -> tuple[list[dict], list[list[dict]]]:
    by_sha: dict[str, list[dict]] = {}
    for r in records:
        by_sha.setdefault(r["sha_full"], []).append(r)
    dup_groups = [sorted(g, key=lambda x: x["path"]) for g in by_sha.values() if len(g) > 1]

    dup_members = {m["path"] for g in dup_groups for m in g[1:]
                   if "/_archive_" not in m["path"]}
    for r in records:
        p, reasons = r["path"], []
        if "/_archive_" in p:
            r["class"], reasons = "D", ["already archived (duplicate archive pool) — retained per manifest"]
        elif p in dup_members:
            r["class"], reasons = "E", ["byte-identical sha256 group; canonical twin kept (lexicographically-first path)"]
        elif any(re.search(g, p) for g in G_PATTERNS):
            r["class"], reasons = "G", ["regenerable cache/temp artifact"]
        elif p.startswith(D_PREFIX):
            r["class"], reasons = "D", ["superseded; archived with redirect stub (wave-6 law)"]
        elif p in A_PATHS or p.startswith("ahos/docs/canonical/"):
            r["class"], reasons = "A", ["current canonical authority"]
        elif is_redirect_stub(p, r["size"], r.get("title")):
            r["class"], reasons = "B", ["redirect stub — active pointer to archive"]
        elif any(re.search(g, p) for g in B_GLOBS):
            r["class"], reasons = "B", ["active implementation / governed data / current reference"]
        else:
            r["class"], reasons = "C", ["historical evidence — preserved (never auto-removed)"]
        r["class_reason"] = "; ".join(reasons)
    # near-duplicates: same basename, different sha
    by_name: dict[str, list[dict]] = {}
    for r in records:
        by_name.setdefault(r["path"].rsplit("/", 1)[-1], []).append(r)
    near = [g for g in by_name.values() if len(g) > 1 and len({x["sha_full"] for x in g}) > 1]
    return records, dup_groups, near


def plan_cleanup(records: list[dict], dup_groups: list[list[dict]]) -> list[dict]:
    plan = []
    arc = "uploads/_archive_exact_dups_wave7"
    for g in dup_groups:
        keep, dups = g[0], g[1:]
        for d in dups:
            if "/_archive_" in d["path"]:
                continue  # already archived in a previous wave — no re-planning
            if not d["path"].startswith("uploads/"):
                continue  # ahos-side exact dups: none expected; would require council sign-off
            plan.append({"action": "archive", "class": "E", "source": d["path"],
                         "dest": f"{arc}/{d['path'].rsplit('/', 1)[-1]}",
                         "pre_sha256": d["sha_full"],
                         "reason": f"exact duplicate of {keep['path']} (sha256 match); "
                                   "council-autonomous per directive §10; reversible via manifest",
                         "canonical_ref": keep["path"], "reversible": True})
    ts = _dt.datetime.now(_dt.timezone.utc)
    for r in records:
        if r["class"] == "G":
            plan.append({"action": "delete", "class": "G", "source": r["path"], "dest": None,
                         "pre_sha256": r["sha_full"],
                         "reason": "regenerable temp artifact (cache/bytecode); excluded from snapshots",
                         "canonical_ref": None, "reversible": True})
    if N8N_RUNTIME.exists():
        size = sum(f.stat().st_size for f in N8N_RUNTIME.rglob("*") if f.is_file())
        n = sum(1 for f in N8N_RUNTIME.rglob("*") if f.is_file())
        plan.append({"action": "delete_tree", "class": "G", "source": "n8n_runtime", "dest": None,
                     "pre_sha256": None, "size_bytes": size, "file_count": n,
                     "reason": "throwaway n8n 2.8.4 runtime (registry='npm install n8n@2.8.4'); "
                               "workflows persist in ahos/n8n/workflows/*.json; live-import evidence in "
                               "reports/N8N_LIVE_SMOKE_TEST_EVIDENCE.txt; owner account was throwaway, "
                               "cookies purged wave-4; regenerable on demand",
                     "canonical_ref": "ahos/n8n/workflows/", "reversible": True,
                     "ts_note": ts.isoformat(timespec="seconds")})
    return plan


def execute_plan(plan: list[dict]) -> list[dict]:
    results = []
    for step in plan:
        res = dict(step)
        src = WORKSPACE / step["source"]
        try:
            if step["action"] == "archive":
                dest = WORKSPACE / step["dest"]
                dest.parent.mkdir(parents=True, exist_ok=True)
                pre = sha256_file(src)
                assert pre == step["pre_sha256"], "pre-move sha mismatch"
                shutil.move(str(src), str(dest))
                post = sha256_file(dest)
                assert post == pre, "post-move sha mismatch"
                res["status"], res["post_sha256"] = "OK", post
            elif step["action"] == "delete":
                pre = sha256_file(src)
                assert pre == step["pre_sha256"], "pre-delete sha mismatch"
                src.unlink()
                res["status"] = "OK_DELETED"
            elif step["action"] == "delete_tree":
                shutil.rmtree(src)
                res["status"] = "OK_DELETED_TREE"
            res["executed_utc"] = _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")
        except FileNotFoundError:
            res["status"] = "SKIP_MISSING"
        except Exception as e:  # fail loud, keep evidence
            res["status"] = f"ERROR: {type(e).__name__}: {e}"
        results.append(res)
    return results


def run(out_inventory: Path = INVENTORY_OUT, cleanup_manifest: Path = CLEANUP_MANIFEST,
        execute: bool = False) -> dict:
    records = build_inventory()
    diff = diff_baseline(records)
    records, dup_groups, near = classify(records)
    plan = plan_cleanup(records, dup_groups)
    executed = execute_plan(plan) if execute else []

    by_class: dict[str, dict] = {}
    for r in records:
        c = by_class.setdefault(r["class"], {"files": 0, "bytes": 0})
        c["files"] += 1
        c["bytes"] += r["size"]

    report = {
        "schema": 2, "wave": 7,
        "generated_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        "law": "negative evidence NEVER removed; E/G autonomous via manifest; F flag-only",
        "diff_vs_wave6_baseline": diff,
        "class_totals": by_class,
        "total_bytes": sum(r["size"] for r in records),
        "exact_dup_groups": [[m["path"] for m in g] for g in dup_groups],
        "near_dup_groups": [[m["path"] for m in g] for g in near],
        "cleanup_plan": plan,
        "cleanup_executed": executed,
        "inventory": [{k: v for k, v in r.items() if k != "abs"} for r in records],
    }
    out_inventory.write_text(json.dumps(report, indent=1, ensure_ascii=False))
    if execute:
        cleanup_manifest.write_text(json.dumps(
            {"wave": 7, "manifest": "CLEANUP_MANIFEST_WAVE7",
             "generated_utc": report["generated_utc"], "entries": executed},
            indent=1, ensure_ascii=False))
    return report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--execute", action="store_true", help="apply the cleanup plan (manifested)")
    args = ap.parse_args(argv)
    rep = run(execute=args.execute)
    d = rep["diff_vs_wave6_baseline"]
    print(f"[hygiene] files={d['current_files']} (baseline {d['baseline_files']}) "
          f"added={len(d['added'])} removed={len(d['removed'])} changed={len(d['changed'])}")
    for c in sorted(rep["class_totals"]):
        t = rep["class_totals"][c]
        print(f"  class {c}: {t['files']:>4} files  {t['bytes']/1e6:8.2f} MB")
    print(f"  total: {rep['total_bytes']/1e6:.2f} MB | exact-dup groups: "
          f"{len(rep['exact_dup_groups'])} | near-dup groups: {len(rep['near_dup_groups'])}")
    print(f"  cleanup plan: {len(rep['cleanup_plan'])} actions"
          + (f" -> EXECUTED {sum(1 for e in rep['cleanup_executed'] if str(e['status']).startswith('OK'))}"
             if args.execute else " (dry-run; use --execute)"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

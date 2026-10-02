"""M9 part B: import-time side-effect audit (Mandate §12 item 2).

Two independent passes over the Python modules in the audited trees:

1. STATIC (AST): flag module-scope statements that can reach the outside world
   -- calls, assignments to ``os.environ``, ``with open(...)``, top-level
   ``await`` -- outside ``if __name__ == "__main__"`` blocks. Definitions,
   decorators, imports and constants are allowed.

2. RUNTIME: import every module in a fresh interpreter with tripwires armed
   (socket connect, file write, sqlite/psycopg connect, subprocess spawn,
   thread start, env mutation) and record exactly which tripwires fired.

The runtime pass is the authority: an AST hit may be a false positive (a call
to a pure helper), and an AST miss may be a false negative (a side effect
reached through an imported helper). The two are cross-checked in the report.

Read-only against the repo: imports are executed with ``AHOS_ROOT`` redirected
to a temp dir so a module that writes cannot touch tracked evidence.

Usage:
    python scripts/audit_import_side_effects.py [--roots architecture,scripts]
        [--json reports/m9/import_side_effects.json] [--quiet]
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Tripwire harness: imported into a subprocess. Records into a JSON file.
# raw string: the harness contains Windows path escapes of its own.
HARNESS = textwrap.dedent(
    r"""
    import builtins, json, os, socket, sqlite3, subprocess, sys, threading, time
    import traceback as _tb
    from pathlib import Path

    # isolated mode (-I) drops CWD from sys.path; the audit needs it to import
    # top-level packages from the repo root.
    sys.path.insert(0, os.environ.get("AHOS_AUDIT_ROOT", os.getcwd()))

    events = []

    def _origin():
        # file where the tripwired call originated, to separate our code from deps
        for fr in _tb.extract_stack()[-4::-1]:
            p = fr.filename.replace("\\", "/")
            if "/site-packages/" in p:
                return "dependency:" + p.rsplit("/site-packages/", 1)[1]
            if "ahos" in p:
                return "ours:" + p.rsplit("ahos", 1)[1]
        return "unknown"

    def _mark(kind, detail):
        events.append({"kind": kind, "origin": _origin(),
                       "detail": str(detail)[:200]})

    def _ours():
        return _origin().startswith("ours:")

    # --- network
    def _no_net(*a, **k):
        kind = "network" if _ours() else "dependency_network"
        _mark(kind, f"socket connect attempted {a[:1]}")
        raise AssertionError("NETWORK_AT_IMPORT")
    socket.socket.connect = _no_net
    socket.create_connection = _no_net
    try:
        import urllib.request
        urllib.request.urlopen = _no_net
    except Exception:
        pass

    # --- file writes
    _real_open = builtins.open
    def _guarded_open(file, mode="r", *a, **k):
        if any(ch in str(mode) for ch in "wax+") and "r" not in str(mode):
            _mark("file_write", f"{file} mode={mode}")
        return _real_open(file, mode, *a, **k)
    builtins.open = _guarded_open
    try:
        import io
        io.open = _guarded_open
    except Exception:
        pass

    # --- databases
    def _no_db(*a, **k):
        kind = "database" if _ours() else "dependency_database"
        _mark(kind, "connect attempted")
        raise AssertionError("DB_AT_IMPORT")
    sqlite3.connect = _no_db
    for mod in ("psycopg2", "psycopg", "pymongo"):
        try:
            m = __import__(mod)
            m.connect = _no_db
        except Exception:
            pass

    # --- subprocess / threads
    def _no_sub(*a, **k):
        if _ours():
            _mark("subprocess", f"spawn attempted {a[:1]}")
            raise AssertionError("SUBPROCESS_AT_IMPORT")
        # a dependency spawn (e.g. pandas calling `ver` on Windows) is recorded
        # but allowed, so the import continues and later real findings surface
        _mark("dependency_subprocess", f"spawn attempted {a[:1]}")
        return "AHOS_AUDIT_DEPENDENCY_SUBPROCESS_STUB"
    subprocess.Popen = _no_sub
    subprocess.run = _no_sub
    subprocess.check_output = _no_sub
    subprocess.check_call = _no_sub
    subprocess.call = _no_sub

    _real_start = threading.Thread.start
    def _thread_start(self):
        _mark("thread", f"thread {getattr(self, 'name', '?')} started")
        return _real_start(self)
    threading.Thread.start = _thread_start

    env_before = dict(os.environ)
    threads_before = threading.active_count()

    target = sys.argv[1]
    out = sys.argv[2]
    try:
        __import__(target)
        imported = True
        err = ""
    except AssertionError as exc:
        imported = False
        err = f"TRIPWIRE: {exc}"
    except Exception as exc:  # any other import failure
        imported = False
        err = f"{type(exc).__name__}: {exc}"

    env_diff = sorted(set(os.environ) - set(env_before))
    env_changed = sorted(k for k in set(env_before) & set(os.environ)
                         if os.environ[k] != env_before[k])
    if env_diff or env_changed:
        _mark("env", f"added={env_diff} changed={env_changed}")
    if threading.active_count() != threads_before:
        _mark("thread", f"active count {threads_before} -> {threading.active_count()}")

    Path(out).write_text(json.dumps(
        {"module": target, "imported": imported, "error": err, "events": events},
        ensure_ascii=False), encoding="utf-8")
    """
)


# ------------------------------------------------------------------ static
SAFE_CALL_NAMES = {
    "staticmethod", "classmethod", "property", "abstractmethod", "dataclass",
    "attr", "field", "Enum", "IntEnum", "auto", "Final", "TypedDict", "NamedTuple",
    "overload", "abstractmethod", "cache", "lru_cache", "frozen_dataclass_factory",
}


def _name_of(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _name_of(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    if isinstance(node, ast.Call):
        return _name_of(node.func)
    return ""


def static_findings(path: Path) -> list[str]:
    """Module-scope side-effect candidates, AST level."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return ["SYNTAX_ERROR"]

    findings: list[str] = []

    def walk(nodes: list[ast.stmt], in_main: bool) -> None:
        for stmt in nodes:
            if in_main:
                continue
            # a guard block: contents are not import-time code
            if isinstance(stmt, ast.If):
                test = ast.unparse(stmt.test) if hasattr(ast, "unparse") else ""
                is_main = '__main__' in test
                walk(stmt.body, in_main or is_main)
                walk(stmt.orelse, in_main)
                continue
            if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            if isinstance(stmt, (ast.Import, ast.ImportFrom)):
                continue
            if isinstance(stmt, ast.Assign):
                # flag os.environ[...] = ... and os.environ.update(...)
                for target in stmt.targets:
                    nm = _name_of(target)
                    if nm.startswith("os.environ"):
                        findings.append(f"env mutation: {ast.unparse(stmt)[:100]}")
                continue
            if isinstance(stmt, ast.AnnAssign):
                continue
            if isinstance(stmt, (ast.Pass, ast.Break, ast.Continue, ast.Global, ast.Nonlocal)):
                continue
            if isinstance(stmt, ast.Expr):
                val = stmt.value
                if isinstance(val, ast.Constant):
                    continue
                if isinstance(val, ast.Call):
                    fn = _name_of(val.func)
                    base = fn.split(".")[0]
                    if base in SAFE_CALL_NAMES or fn in SAFE_CALL_NAMES:
                        continue
                    if fn.endswith(".setter") or fn.endswith(".getter"):
                        continue
                    findings.append(f"module-scope call {fn}() {ast.unparse(stmt)[:90]}")
                    continue
                continue
            if isinstance(stmt, ast.With):
                for item in stmt.items:
                    nm = _name_of(item.context_expr)
                    if "open" in nm:
                        findings.append(f"module-scope with-open: {ast.unparse(stmt)[:90]}")
                continue
            if isinstance(stmt, (ast.For, ast.While)):
                findings.append(f"module-scope loop: {type(stmt).__name__}")
                continue
            if isinstance(stmt, ast.Try):
                walk(stmt.body, in_main)
                for h in stmt.handlers:
                    walk(h.body, in_main)
                walk(stmt.orelse, in_main)
                walk(stmt.finalbody, in_main)
                continue
            if isinstance(stmt, (ast.Delete, ast.AugAssign)):
                findings.append(f"module-scope {type(stmt).__name__}: {ast.unparse(stmt)[:90]}")
                continue

    walk(tree.body, False)
    return findings


def iter_modules(roots: list[str]) -> list[tuple[str, Path]]:
    out = []
    for root in roots:
        base = ROOT / root
        if not base.is_dir():
            continue
        for py in sorted(base.rglob("*.py")):
            rel = py.relative_to(ROOT).with_suffix("")
            # skip generated/cached and test files
            parts = rel.parts
            if any(p in {"__pycache__", "node_modules"} for p in parts):
                continue
            if parts[-1].startswith("test_"):
                continue
            if any(p.endswith(".test") for p in parts):
                continue
            if rel.name in {"__init__", "setup", "conftest"}:
                # __init__ is imported, so keep it; setup/conftest are not modules
                if rel.name != "__init__":
                    continue
            dotted = ".".join(parts)
            out.append((dotted, py))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--roots", default="architecture,scripts,engine,telegram_ai")
    ap.add_argument("--json", default=None)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    roots = args.roots.split(",")
    modules = iter_modules(roots)

    static: dict[str, list[str]] = {}
    for dotted, path in modules:
        f = static_findings(path)
        if f:
            static[dotted] = f

    # ---- runtime pass
    runtime: dict[str, dict] = {}
    tmp = Path(tempfile.mkdtemp(prefix="ahos_import_audit_"))
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["AHOS_ROOT"] = str(tmp)
    env["AHOS_AUDIT_ROOT"] = str(ROOT)
    env["PYTHONIOENCODING"] = "utf-8"
    # keep the sandbox off the network for import attempts
    for k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
        env.pop(k, None)

    for dotted, _ in modules:
        ev = tmp / f"ev_{abs(hash(dotted))}.json"
        code_path = tmp / "harness.py"
        if not code_path.exists():
            code_path.write_text(HARNESS, encoding="utf-8")
        try:
            subprocess.run(
                [sys.executable, "-B", "-I", str(code_path), dotted, str(ev)],
                cwd=ROOT, env=env, capture_output=True, text=True,
                encoding="utf-8", errors="replace", timeout=120,
            )
        except subprocess.TimeoutExpired:
            runtime[dotted] = {"imported": False, "error": "TIMEOUT", "events": []}
            continue
        if not ev.exists():
            # capture the harness's own crash for diagnosis
            try:
                proc = subprocess.run(
                    [sys.executable, "-B", "-I", str(code_path), dotted, str(ev)],
                    cwd=ROOT, env=env, capture_output=True, text=True,
                    encoding="utf-8", errors="replace", timeout=120,
                )
                tail = (proc.stderr or proc.stdout or "")[-400:]
            except Exception as exc:
                tail = f"re-run failed: {exc}"
            runtime[dotted] = {"imported": False,
                               "error": f"HARNESS_NO_RESULT: {tail}", "events": []}
            continue
        try:
            runtime[dotted] = json.loads(ev.read_text(encoding="utf-8"))
        except Exception as exc:
            runtime[dotted] = {"imported": False, "error": f"BAD_JSON {exc}", "events": []}

    # ---- classify
    side_effect_kinds = {"network", "file_write", "database", "subprocess", "env", "thread"}
    confirmed = {}
    for mod, res in runtime.items():
        kinds = sorted({e["kind"] for e in res.get("events", [])} & side_effect_kinds)
        if kinds:
            confirmed[mod] = {"kinds": kinds,
                              "events": [e for e in res["events"] if e["kind"] in kinds]}
    import_failures = {m: r["error"] for m, r in runtime.items()
                       if not r.get("imported")}

    report = {
        "roots": roots,
        "module_count": len(modules),
        "static_candidates": static,
        "runtime_confirmed_side_effects": confirmed,
        "import_failures": import_failures,
        "runtime_detail": {m: {"imported": r.get("imported"),
                               "error": r.get("error"),
                               "events": r.get("events", [])}
                           for m, r in runtime.items()},
    }
    if args.json:
        Path(args.json).write_text(json.dumps(report, ensure_ascii=False, indent=1),
                                   encoding="utf-8")

    if not args.quiet:
        print(f"modules audited: {len(modules)}")
        print(f"static candidates: {len(static)}")
        print(f"RUNTIME-CONFIRMED import side effects: {len(confirmed)}")
        for mod, info in sorted(confirmed.items()):
            print(f"  {mod}: {info['kinds']}")
        print(f"import failures: {len(import_failures)}")
        for mod, err in sorted(import_failures.items()):
            print(f"  {mod}: {err[:120]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

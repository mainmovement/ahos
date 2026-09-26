#!/usr/bin/env python3
"""AHOS import & architecture validation gate (Phase 6).

CI runs this BEFORE pytest so broken wiring fails fast with a precise report.
A local run is identical to CI — the script is deterministic and network-free.

Checks (each section fails the run independently):
  1. IMPORT — every module under the runtime packages imports cleanly in a
     fresh interpreter (broken imports, orphan references, syntax errors).
  2. EVIDENCE-BOUNDARY — the intelligence surface (intelligence / risk /
     features / scoring / explanations) must never import raw-data or
     trading lanes (discovery, paper_trading, telegram_ai, engine):
     "هیچ ماژول Intelligence اجازه مصرف مستقیم Raw Data ندارد."
  3. LANE-A FREEZE — the frozen scientific surface matches
     config/lane_a_freeze.sha256 (reuses scripts/freeze_lane_a, no duplicate
     hashing logic here). Drift or missing files fail; new untracked files warn.
  4. SECRETS — non-test source files must not contain secret-looking strings
     (reuses architecture.security.hygiene._SECRET_PATTERNS). Test fixtures and
     *.example placeholder docs are exempt.
  5. ARTIFACTS — no __pycache__ / .pytest_cache leftovers may exist in a clean
     checkout.

Usage:
    python scripts/validate_imports.py            # full gate
    python scripts/validate_imports.py --imports-only

Exit code: 0 = clean, 1 = any failure, 2 = invocation error.
"""

from __future__ import annotations

import argparse
import ast
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Packages whose every module must import cleanly.
RUNTIME_PACKAGES = [
    "architecture",
    "discovery",
    "paper_trading",
    "telegram_ai",
    "strategy_lab",
    "engine",
    "config",
]

# Modules that are executable entrypoints by design, not importable surfaces.
# The bar is that everything else imports. Every entry here needs its reason.
IMPORT_EXCLUDE: dict[str, str] = {
    # executable skeleton: reads env at module level and sys.exit(2) when the
    # bot credentials are absent (Agent-04 rule) — correct for a CLI, fatal
    # for an import. Its logic is exercised by tests/test_run_bot_launcher.py.
    "engine.bot_skeleton": "executable CLI skeleton (sys.exit at module level by design)",
    # executable validation tool: runs the whole backtest/validation pipeline
    # at module level and writes reports on import — a script, not a module.
    "engine.run_validation": "executable validation runner (module-level execution by design)",
}

# Evidence Architecture law: these surfaces consume EvidenceBundle / derived
# findings only — raw collection and trading lanes are structurally forbidden.
EVIDENCE_SURFACES = (
    "architecture/intelligence",
    "architecture/risk",
    "architecture/features",
    "architecture/scoring",
    "architecture/explanations",
)
FORBIDDEN_TOP_LEVELS = {"discovery", "paper_trading", "telegram_ai", "engine"}

# Secret-scan scope: source-like files, excluding test fixtures and placeholder docs.
SECRET_SUFFIXES = {".py", ".yaml", ".yml", ".json", ".sql", ".toml", ".sh"}
SECRET_SCAN_EXCLUDE_DIRS = {"tests", "docs"}
SECRET_SCAN_EXCLUDE_SUFFIX = (".example",)


# --------------------------------------------------------------------- checks

def collect_modules() -> list[str]:
    modules: list[str] = []
    for pkg in RUNTIME_PACKAGES:
        pkg_dir = ROOT / pkg
        if not pkg_dir.is_dir():
            print(f"ERROR: package directory missing: {pkg_dir}")
            sys.exit(2)
        for path in sorted(pkg_dir.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            rel = path.relative_to(ROOT)
            if rel.name == "__init__.py":
                module = rel.parent.as_posix().replace("/", ".")
            else:
                module = rel.with_suffix("").as_posix().replace("/", ".")
            if module not in IMPORT_EXCLUDE:
                modules.append(module)
    return modules


def _import_in_fresh_interpreter(module: str) -> tuple[int, str]:
    """Import one module in a subprocess — a genuinely fresh interpreter.

    In-process importing can mask breakage (sys.modules cross-contamination,
    import order, or a module that calls sys.exit() at import time killing the
    whole validator). A subprocess makes each module prove it imports cleanly
    on its own, and a SystemExit shows up as a failure instead of a dead run.
    """
    code = "import sys; sys.path.insert(0, %r); import %s" % (str(ROOT), module)
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"          # probing must not litter __pycache__
    try:
        proc = subprocess.run([sys.executable, "-B", "-c", code],
                              capture_output=True, text=True,
                              timeout=120, cwd=ROOT, env=env)
    except subprocess.TimeoutExpired:
        return 1, "import timed out (>120s)"
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or "").strip().splitlines()
        return proc.returncode, (tail[-1] if tail else f"exit code {proc.returncode}")
    return 0, ""


def check_imports() -> tuple[list[str], list[str]]:
    failures: list[str] = []
    ok_count = 0
    excluded = sorted(IMPORT_EXCLUDE)
    for module in collect_modules():
        rc, detail = _import_in_fresh_interpreter(module)
        if rc == 0:
            ok_count += 1
        else:
            failures.append(f"{module}: {detail}")
    notes = [f"{ok_count} modules imported cleanly in fresh interpreters"]
    if excluded:
        notes.append(f"{len(excluded)} documented executable entrypoints excluded: {excluded}")
    return failures, notes


def _module_roots(node: ast.AST) -> list[str]:
    roots: list[str] = []
    for n in ast.walk(node):
        if isinstance(n, ast.Import):
            for alias in n.names:
                roots.append(alias.name.split(".")[0])
        elif isinstance(n, ast.ImportFrom) and n.level == 0 and n.module:
            roots.append(n.module.split(".")[0])
    return roots


def check_evidence_boundaries() -> tuple[list[str], list[str]]:
    violations: list[str] = []
    scanned = 0
    for surface in EVIDENCE_SURFACES:
        surface_dir = ROOT / surface
        for path in sorted(surface_dir.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            scanned += 1
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except SyntaxError as e:
                violations.append(f"{path.relative_to(ROOT)}: syntax error: {e}")
                continue
            bad = sorted(set(FORBIDDEN_TOP_LEVELS) & set(_module_roots(tree)))
            for name in bad:
                violations.append(
                    f"{path.relative_to(ROOT)} imports forbidden lane '{name}' "
                    f"(Evidence Architecture law: no raw-data/trading imports)")
    return violations, [f"{scanned} evidence-surface files scanned"]


def check_lane_a_freeze() -> tuple[list[str], list[str]]:
    from scripts import freeze_lane_a as freeze_lane
    drift, missing, untracked = freeze_lane.verify(root=ROOT)
    failures = [f"DRIFT   {p}" for p in drift] + [f"MISSING {p}" for p in missing]
    warnings = [f"UNTRACKED (new Lane-A file, governance act pending): {p}"
                for p in untracked]
    if not failures:
        warnings.insert(0, f"Lane-A integrity OK ({len(freeze_lane.load_baseline(root=ROOT))} files pinned)")
    return failures, warnings


def check_secrets() -> tuple[list[str], list[str]]:
    from architecture.security.hygiene import _SECRET_PATTERNS
    failures: list[str] = []
    scanned = 0
    for path in sorted(ROOT.rglob("*")):
        if "__pycache__" in path.parts or ".git" in path.parts:
            continue
        rel = path.relative_to(ROOT)
        parts = set(rel.parts)
        if parts & SECRET_SCAN_EXCLUDE_DIRS:
            continue
        if path.name.startswith(".env") or path.name.endswith(SECRET_SCAN_EXCLUDE_SUFFIX):
            continue
        if path.suffix.lower() not in SECRET_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in _SECRET_PATTERNS:
            if pattern.search(text):
                failures.append(f"{rel}: secret-looking string (pattern: {pattern.pattern[:24]}...)")
                break
        scanned += 1
    return failures, [f"{scanned} source files scanned"]


# Vendored/ignored dirs that are not part of the source surface.
ARTIFACT_SKIP_DIRS = {".git", ".venv", "venv", "env", "node_modules", "data"}


def check_artifacts() -> tuple[list[str], list[str]]:
    failures: list[str] = []
    for name in ("__pycache__", ".pytest_cache"):
        for path in ROOT.rglob(name):
            if ARTIFACT_SKIP_DIRS & set(path.relative_to(ROOT).parts):
                continue
            failures.append(f"build artifact present: {path.relative_to(ROOT)}/")
    return failures, ["no build artifacts expected in a clean checkout"]


def _module_import_paths(path: Path) -> set[str]:
    """Every module path a source file imports, absolute and resolved
    relative (level N) — so `from ..features import extractor` inside a
    function body still registers `architecture.features.extractor` and a
    lazy import cannot hide an orphan.

    String-based lazy imports are also captured: `__init__.py` files in this
    repo commonly map attribute names to `(".engine", "SecurityIntelligence")`
    tuples inside `__getattr__`, which no AST Import node represents. Any
    dotted string literal in an `__init__.py` is resolved relative to the
    package, so those modules are never falsely reported as orphans.
    """
    out: set[str] = set()

    def _package_of(file: Path) -> str:
        rel = file.relative_to(ROOT).parent
        return ".".join(rel.parts) if str(rel) != "." else ""

    def _resolve_relative(rel_spec: str) -> str | None:
        # 1 leading dot = this package (".engine" -> "pkg.engine"),
        # 2 dots = parent, etc. — same semantics as a relative ImportFrom.
        dots = len(rel_spec) - len(rel_spec.lstrip("."))
        spec = rel_spec.lstrip(".")
        parts = pkg.split(".") if pkg else []
        if not spec or not parts:
            return None
        up = max(0, dots - 1)
        base = ".".join(parts[: len(parts) - up]) if len(parts) >= up else ""
        return f"{base}.{spec}" if base else spec

    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return out

    pkg = _package_of(path)
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for alias in n.names:
                out.add(alias.name)
        elif isinstance(n, ast.ImportFrom) and n.module:
            if n.level == 0:
                out.add(n.module)
                for alias in n.names:
                    if alias.name != "*":
                        out.add(f"{n.module}.{alias.name}")
            else:
                # relative: go up (level-1) packages from this file's package
                parts = pkg.split(".") if pkg else []
                up = max(0, n.level - 1)
                base = ".".join(parts[: len(parts) - up]) if len(parts) >= up else ""
                resolved = f"{base}.{n.module}" if base else n.module or ""
                if resolved:
                    out.add(resolved)
                    for alias in n.names:
                        if alias.name != "*":
                            out.add(f"{resolved}.{alias.name}")

    # string-based lazy imports (e.g. __getattr__ mapping tuples)
    if path.name == "__init__.py":
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                v = node.value
                if v.startswith(".") and v.lstrip(".").replace(".", "").isidentifier():
                    resolved = _resolve_relative(v)
                    if resolved:
                        out.add(resolved)
    return out


def check_orphans() -> tuple[list[str], list[str]]:
    """Dead-module detection (evolution mission §4B): a runtime module that
    nothing imports and no test exercises is a candidate for consolidation or
    removal. WARN-level only: a standalone executable entrypoint is
    legitimate, and removal is a governance decision, never an automatic
    action by this gate."""
    known = set(collect_modules())

    # A "leaf" is a real .py file, not a package directory (packages are
    # referenced implicitly by their submodules and are never orphaned).
    def _is_package(mod: str) -> bool:
        rel = Path(*mod.split("."))
        return (ROOT / rel / "__init__.py").exists()

    leaf_modules = {m for m in known if not _is_package(m)}
    referenced: set[str] = set()

    scan_targets = list(ROOT.rglob("*.py"))
    for path in scan_targets:
        if "__pycache__" in path.parts or ".venv" in path.parts or ".git" in path.parts:
            continue
        for mod in _module_import_paths(path):
            referenced.add(mod)

    orphans = sorted(m for m in leaf_modules
                     if m not in referenced and m not in IMPORT_EXCLUDE)
    notes = [f"{len(leaf_modules)} leaf modules scanned, "
             f"{len(referenced & leaf_modules)} referenced"]
    if orphans:
        notes.append(f"WARN: {len(orphans)} modules never imported by any module "
                     "or test (dead-code candidates, governance review): "
                     + ", ".join(orphans))
    else:
        notes.append("no orphaned leaf modules")
    return [], notes


# ---------------------------------------------------------------------- report

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="AHOS import & architecture validation gate")
    ap.add_argument("--imports-only", action="store_true",
                    help="run only the import check (fast local loop)")
    args = ap.parse_args(argv)

    # ARTIFACTS first: a clean checkout must be clean BEFORE imports run
    # (the import probes write nothing thanks to -B, but a pre-existing
    # cache from a developer run is exactly what this gate exists to catch).
    checks = [
        ("ARTIFACTS", check_artifacts),
        ("IMPORTS", check_imports),
    ]
    if not args.imports_only:
        checks += [
            ("EVIDENCE-BOUNDARY", check_evidence_boundaries),
            ("LANE-A FREEZE", check_lane_a_freeze),
            ("SECRETS", check_secrets),
            ("ORPHANS", check_orphans),
        ]

    rc = 0
    for name, fn in checks:
        failures, notes = fn()
        print(f"\n== {name} ==")
        for line in notes:
            if line.startswith("WARN:"):
                print(f"   WARN: {line[5:].strip()}")
            else:
                print(f"   info: {line}")
        for line in failures:
            print(f"   FAIL: {line}")
        if failures:
            rc = 1

    print("\n" + ("VALIDATION PASSED — repository wiring is clean."
                  if rc == 0 else "VALIDATION FAILED — see FAIL lines above."))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())

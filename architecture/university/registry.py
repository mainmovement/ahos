"""M16 university source registry and permissive open-source R&D crawler (read-only, zero code execution)."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence
from urllib.parse import urlparse

from config.paths import get_project_root

SCHEMA_V1 = "ahos.university.sources.v1"

PERMISSIVE_LICENSE_PREFIXES: tuple[str, ...] = (
    "mit",
    "bsd",
    "apache-2.0",
    "apache",
    "cc0",
    "cc-by",
    "arxiv",
    "openalex",
    "semanticscholar",
    "fred-public",
    "us-public-domain",
    "free-educational",
    "academic-open",
)

FORBIDDEN_LICENSE_TOKENS: tuple[str, ...] = (
    "gpl",
    "agpl",
    "lgpl",
    "proprietary",
    "commercial",
    "paid",
    "closed",
    "sspl",
)


@dataclass(frozen=True, slots=True)
class UniversitySource:
    url: str
    license: str
    faculty: str

    @property
    def domain(self) -> str:
        try:
            return urlparse(self.url).hostname or self.url
        except ValueError:
            return self.url


def default_sources_path() -> Path:
    return get_project_root() / "config" / "university" / "sources.yaml"


def parse_sources_yaml(text: str) -> tuple[str | None, list[UniversitySource]]:
    """Minimal YAML parser for the seeded sources file (no PyYAML dependency)."""
    schema: str | None = None
    sources: list[UniversitySource] = []
    cur: dict[str, str] | None = None

    def flush() -> None:
        nonlocal cur
        if cur and cur.get("url"):
            sources.append(
                UniversitySource(
                    url=cur["url"],
                    license=cur.get("license", ""),
                    faculty=cur.get("faculty", "research"),
                )
            )
        cur = None

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("schema:"):
            schema = stripped.split(":", 1)[1].strip()
            continue
        if line.startswith("  - url:"):
            flush()
            cur = {"url": _unquote(stripped.split(":", 1)[1].strip())}
            continue
        if cur and line.startswith("    "):
            key, _, val = stripped.partition(":")
            if key in ("license", "faculty"):
                cur[key] = _unquote(val.strip())
            continue
        if not line.startswith(" "):
            flush()
    flush()
    return schema, sources


def _unquote(value: str) -> str:
    v = value.strip()
    if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
        return v[1:-1]
    return v


def load_sources(path: Path | None = None) -> list[UniversitySource]:
    p = path or default_sources_path()
    text = p.read_text(encoding="utf-8")
    schema, rows = parse_sources_yaml(text)
    if schema is not None and schema != SCHEMA_V1:
        raise ValueError(f"unsupported university schema: {schema!r}")
    return rows


def is_permissive_rd_license(license_str: str) -> bool:
    low = (license_str or "").strip().lower()
    if not low:
        return False
    if any(bad in low for bad in FORBIDDEN_LICENSE_TOKENS):
        return False
    return any(low.startswith(pref) or pref in low for pref in PERMISSIVE_LICENSE_PREFIXES)


def default_github_rd_candidates() -> list[dict[str, Any]]:
    return [
        {
            "id": "rd-skfolio-hrp",
            "repo": "https://github.com/skfolio/skfolio",
            "title": "skfolio: Portfolio Optimization & Hierarchical Risk Parity on scikit-learn",
            "license": "BSD-3-Clause",
            "faculty": "quant",
            "stars": 1420,
            "paper_application": "Paper portfolio weight caps & CVaR risk parity (M24)",
        },
        {
            "id": "rd-kronos-candles",
            "repo": "https://github.com/shiyu-coder/Kronos",
            "title": "Kronos: Foundation Model for Financial Candlestick K-Lines",
            "license": "MIT",
            "faculty": "quant",
            "stars": 2150,
            "paper_application": "Paper-only challenger candle forecaster (M15.10 / M56)",
        },
        {
            "id": "rd-ruptures-changepoint",
            "repo": "https://github.com/deepcharles/ruptures",
            "title": "ruptures: Offline & PELT Structural Break Detection in Python",
            "license": "BSD-2-Clause",
            "faculty": "quant",
            "stars": 1680,
            "paper_application": "Structural regime change detection for Gold & Oil paper desks",
        },
        {
            "id": "rd-vectorbt-oss",
            "repo": "https://github.com/polakowo/vectorbt",
            "title": "vectorbt Open-Source Vectorized Backtesting Utilities",
            "license": "Apache-2.0",
            "faculty": "research",
            "stars": 4300,
            "paper_application": "Replay sandbox purged walk-forward validation (M28.1)",
        },
        {
            "id": "rd-gpl-copyleft-bot",
            "repo": "https://github.com/example/gpl-trading-bot",
            "title": "GPLv3 Copyleft Trading Bot (Rejected by License Gate)",
            "license": "GPL-3.0",
            "faculty": "quant",
            "stars": 800,
            "paper_application": "NONE — rejected by permissive license gate",
        },
        {
            "id": "rd-paid-closed-sdk",
            "repo": "https://github.com/example/paid-proprietary-signals",
            "title": "Commercial Paid Signal SDK (Rejected by Free-Source Gate)",
            "license": "Proprietary-Paid",
            "faculty": "quant",
            "stars": 310,
            "paper_application": "NONE — rejected by zero-paid-source rule",
        },
    ]


def crawl_open_source_rd(
    sources_path: Path | None = None,
    fixture_items: Sequence[Mapping[str, Any]] | None = None,
    out_path: Path | None = None,
) -> dict[str, Any]:
    """M16: Scan and validate open-source R&D releases against permissive licenses.
    Never installs packages or executes untrusted code. Writes reports/grok/M16/github_rd_crawl.json.
    """
    reg_sources = load_sources(sources_path)
    candidates = fixture_items if fixture_items is not None else default_github_rd_candidates()

    admitted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []

    for item in candidates:
        lic = str(item.get("license") or "")
        ok = is_permissive_rd_license(lic)
        row = {
            "id": str(item.get("id") or ""),
            "repo": str(item.get("repo") or ""),
            "title": str(item.get("title") or ""),
            "license": lic,
            "faculty": str(item.get("faculty") or "research"),
            "stars": int(item.get("stars", 0)),
            "paper_application": str(item.get("paper_application") or ""),
            "status": "ADMITTED_PAPER_RD" if ok else "REJECTED_LICENSE",
            "auto_install": False,
            "code_executed": False,
        }
        if ok:
            admitted.append(row)
        else:
            rejected.append(row)

    payload = {
        "schema": "ahos.university.github_rd_crawl.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "paper_only": True,
        "auto_install": False,
        "code_executed": False,
        "registry_sources_count": len(reg_sources),
        "candidates_scanned": len(candidates),
        "admitted_count": len(admitted),
        "rejected_count": len(rejected),
        "admitted": admitted,
        "rejected": rejected,
    }

    target = out_path or (get_project_root() / "reports" / "grok" / "M16" / "github_rd_crawl.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return payload

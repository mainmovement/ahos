"""M16 university source registry (read-only). No network fetch."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from config.paths import get_project_root

SCHEMA_V1 = "ahos.university.sources.v1"


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

"""Bounded research workspace. No raw filesystem API is exposed to agents."""

from __future__ import annotations

from pathlib import Path


class WorkspaceDenied(ValueError):
    pass


_SECRET_PARTS = frozenset(
    {
        ".env",
        ".git",
        "id_rsa",
        "id_ed25519",
        "credentials.json",
        "secrets",
    }
)
_SECRET_SUFFIXES = (".env", ".pem", ".key", ".pfx")


def research_sandbox_root(workspace_file: Path) -> Path:
    """Resolve sibling sandbox from this package file without embedding drive roots."""
    return workspace_file.resolve().parents[2] / "research-sandbox"


def inspect_requested_path(requested: str) -> None:
    raw = requested.strip() if requested else ""
    if not raw:
        raise WorkspaceDenied("empty_path")
    if "\x00" in raw:
        raise WorkspaceDenied("nul_in_path")
    if raw.startswith("\\\\") or raw.startswith("//"):
        raise WorkspaceDenied("unc_path_denied")
    if len(raw) >= 2 and raw[1] == ":":
        raise WorkspaceDenied("absolute_path_denied")
    if raw.startswith("/") or raw.startswith("\\"):
        raise WorkspaceDenied("absolute_path_denied")
    lowered = raw.lower()
    if "windows\\system32" in lowered.replace("/", "\\") or "windows/system32" in lowered:
        raise WorkspaceDenied("system_path_denied")
    if "\\users\\" in lowered.replace("/", "\\") or "/users/" in lowered:
        raise WorkspaceDenied("user_profile_path_denied")


def resolve_workspace_path(root: Path, requested: str) -> Path:
    inspect_requested_path(requested)
    normalized = requested.replace("\\", "/")
    parts = Path(normalized).parts
    if any(part == ".." for part in parts):
        raise WorkspaceDenied("path_traversal_denied")
    for part in parts:
        lowered = part.lower()
        if lowered in _SECRET_PARTS or lowered.startswith(".env"):
            raise WorkspaceDenied("secret_path_denied")
        if lowered.endswith(_SECRET_SUFFIXES):
            raise WorkspaceDenied("secret_path_denied")
    base = root.resolve()
    candidate = (base / normalized).resolve()
    try:
        candidate.relative_to(base)
    except ValueError as exc:
        raise WorkspaceDenied("workspace_escape_denied") from exc
    return candidate


class ResearchWorkspace:
    def __init__(self, root: Path) -> None:
        self.__root = root.resolve()
        self.__root.mkdir(parents=True, exist_ok=True)

    @property
    def root(self) -> Path:
        return self.__root

    def list_supplied(self) -> tuple[str, ...]:
        names: list[str] = []
        for path in sorted(self.__root.rglob("*")):
            if path.is_file() and path.name != ".gitkeep":
                names.append(path.relative_to(self.__root).as_posix())
        return tuple(names)

    def read_supplied(self, relative_path: str) -> str:
        path = resolve_workspace_path(self.__root, relative_path)
        if not path.is_file():
            raise WorkspaceDenied("supplied_artifact_not_found")
        return path.read_text(encoding="utf-8")

    def operator_write(self, relative_path: str, content: str) -> str:
        path = resolve_workspace_path(self.__root, relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path.relative_to(self.__root).as_posix()

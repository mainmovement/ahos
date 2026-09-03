"""Phase 0 Cursor engineering foundation — files, skills, and contract pins."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_SKILLS = [
    "ahos-governance-context",
    "ahos-domain-backend",
    "ahos-change-verification",
    "ahos-token-identity",
    "ahos-security-analysis",
    "ahos-market-intelligence",
    "ahos-research-intelligence",
    "ahos-opportunity-hunter",
    "ahos-ai-council",
    "ahos-web-experience",
    "ahos-product-intelligence",
]

REQUIRED_AGENTS = [
    "python-core.md",
    "web.md",
    "security-review.md",
    "verification.md",
]


def test_agents_md_exists_and_pins_laws():
    text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    for needle in (
        "PAPER_ONLY",
        "Lane A",
        "FROZEN",
        "Python Lane B",
        "UNKNOWN",
        "ralph-loop",
        "speed bump, not a security boundary",
        "INTEGRATION_READY",
    ):
        assert needle in text, needle


def test_cursor_skills_exist_with_matching_names():
    for name in REQUIRED_SKILLS:
        path = ROOT / ".cursor" / "skills" / name / "SKILL.md"
        assert path.is_file(), path
        head = path.read_text(encoding="utf-8").split("---", 2)[1]
        assert f"name: {name}" in head


def test_cursor_agents_exist():
    for name in REQUIRED_AGENTS:
        path = ROOT / ".cursor" / "agents" / name
        assert path.is_file(), path
    review = (ROOT / ".cursor" / "agents" / "security-review.md").read_text(
        encoding="utf-8"
    )
    assert "readonly: true" in review


def test_rules_and_hooks_and_worktrees_exist():
    for rel in (
        ".cursor/rules/10-lane-a-frozen.mdc",
        ".cursor/rules/20-python-authority.mdc",
        ".cursor/rules/30-edge-boundaries.mdc",
        ".cursor/rules/40-security-evidence.mdc",
        ".cursor/hooks.json",
        ".cursor/hooks/ahos-guard.py",
        ".cursor/worktrees.json",
        ".cursor/setup-worktree-unix.sh",
        ".cursor/setup-worktree-windows.ps1",
        ".cursor/environment.json",
        ".cursor/install.sh",
        ".cursor/start.sh",
        ".github/CODEOWNERS",
        ".github/PULL_REQUEST_TEMPLATE.md",
    ):
        assert (ROOT / rel).is_file(), rel


def test_environment_json_does_not_start_product_runtime():
    env = (ROOT / ".cursor" / "environment.json").read_text(encoding="utf-8")
    install = (ROOT / ".cursor" / "install.sh").read_text(encoding="utf-8")
    start = (ROOT / ".cursor" / "start.sh").read_text(encoding="utf-8")
    blob = env + install + start
    assert "drizzle-kit push" not in blob
    assert "init_databases.py" not in blob
    assert "npm run dev" not in env
    assert "AHOS_PAPER_ONLY" in start


def test_gitignore_isolates_worktree_local_state():
    gi = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert ".cursor-local/" in gi
    assert ".cursor/ralph/" in gi
    assert "!.env.example" in gi

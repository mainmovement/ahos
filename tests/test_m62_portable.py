"""M62 portable bundle: no secrets, no owner drive path, paper marker."""
from __future__ import annotations

from pathlib import Path

import pytest

from architecture.portable.pack import build_bundle


def test_bundle_drops_env_and_stays_paper_only(tmp_path: Path):
    src = tmp_path / "src"
    (src / "core" / "idea_shelf").mkdir(parents=True)
    (src / "architecture" / "health").mkdir(parents=True)
    (src / "config").mkdir()
    (src / ".env").write_text("TELEGRAM_TOKEN=should-not-copy\n", encoding="utf-8")
    (src / "core" / "__init__.py").write_text("# core\n", encoding="utf-8")
    (src / "architecture" / "__init__.py").write_text("# arch\n", encoding="utf-8")
    (src / "config" / "paths.py").write_text("def get_project_root():\n    return None\n", encoding="utf-8")
    (src / "config" / "idea_shelf.json").write_text("{}\n", encoding="utf-8")
    (src / "core" / "idea_shelf" / "__init__.py").write_text("# shelf\n", encoding="utf-8")
    (src / "architecture" / "health" / "__init__.py").write_text("# health\n", encoding="utf-8")
    (src / "architecture" / "health" / "monitor.py").write_text(
        "def assess_soak_health(status):\n    return status\n",
        encoding="utf-8",
    )
    leaked = src / "core" / "idea_shelf" / "hardware.py"
    leaked.write_text("PATH = r'C:\\Users\\Sniper\\secret'\n", encoding="utf-8")

    dest = tmp_path / "bundle"
    report = build_bundle(src, dest)
    assert not (dest / ".env").exists()
    assert report.env_present is False
    assert report.paper_only is True
    assert report.health_ok is False
    assert any(item.endswith("hardware.py") for item in report.owner_path_leaks)
    text = (dest / "DATA_MOVE.txt").read_text(encoding="utf-8")
    assert "Credential Manager" in text
    assert "DATABASE_URL" in text
    ps1 = (dest / "AHOS_Portable_Health.ps1").read_text(encoding="utf-8")
    assert "C:\\" not in ps1
    assert "$PSScriptRoot" in ps1


def test_clean_fixture_is_healthy(tmp_path: Path):
    src = tmp_path / "src"
    (src / "core" / "idea_shelf").mkdir(parents=True)
    (src / "architecture" / "health").mkdir(parents=True)
    (src / "config").mkdir()
    (src / "core" / "__init__.py").write_text("# core\n", encoding="utf-8")
    (src / "architecture" / "__init__.py").write_text("# arch\n", encoding="utf-8")
    (src / "config" / "paths.py").write_text("X = 1\n", encoding="utf-8")
    (src / "config" / "idea_shelf.json").write_text("{}\n", encoding="utf-8")
    (src / "core" / "idea_shelf" / "__init__.py").write_text("# shelf\n", encoding="utf-8")
    (src / "core" / "idea_shelf" / "hardware.py").write_text(
        "class Probe:\n    def __init__(self):\n        self.tier='T8'\n        self.source='fixture'\n"
        "def detect_hardware(override=None):\n    return Probe()\n",
        encoding="utf-8",
    )
    (src / "architecture" / "health" / "__init__.py").write_text("# health\n", encoding="utf-8")
    (src / "architecture" / "health" / "monitor.py").write_text("LEVEL = 'READ'\n", encoding="utf-8")
    dest = tmp_path / "bundle"
    report = build_bundle(src, dest)
    assert report.health_ok is True
    assert report.env_present is False


def test_refuses_to_pack_inside_the_source(tmp_path: Path):
    src = tmp_path / "src"
    src.mkdir()
    with pytest.raises(ValueError):
        build_bundle(src, src / "out")

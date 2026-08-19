"""Static contracts for the native Windows installation workflow.

The suite runs on Linux too, so it verifies the script's declared behavior
without pretending to execute PowerShell or prove a real Windows installation.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "install_windows.ps1"


def _text() -> str:
    return INSTALLER.read_text(encoding="utf-8")


def test_installer_requires_python_311_or_newer():
    text = _text()
    assert "sys.version_info >= (3, 11)" in text
    assert "CPython 3.11+" in text


def test_installer_uses_only_the_isolated_venv_after_creation():
    text = _text()
    assert ".venv\\Scripts\\python.exe" in text
    assert '& $VenvPython @PipArgs' in text
    assert "pip install" not in "\n".join(
        line for line in text.splitlines()
        if "$VenvPython" not in line and "$PipArgs" not in line)


def test_installer_supports_an_offline_wheelhouse():
    text = _text()
    assert "AHOS_WHEELHOUSE" in text
    assert "--no-index" in text and "--find-links" in text


def test_installer_creates_root_env_and_initializes_databases():
    text = _text()
    assert 'Copy-Item ".env.example" ".env"' in text
    assert "scripts\\init_databases.py --with-guards" in text


def test_installer_enforces_utf8_and_checks_native_exit_codes():
    text = _text()
    assert "PYTHONUTF8" in text and "PYTHONIOENCODING" in text
    assert "Stop-OnNativeFailure" in text


def test_installer_runs_offline_smoke_and_n8n_validation():
    text = _text()
    assert "architecture.pipeline.orchestrator" in text
    assert "tests\\validate_n8n.py" in text


def test_installer_adds_no_execution_surface():
    lowered = _text().lower()
    for forbidden in ("ccxt", "web3", "private_key", "place_order",
                      "create_order", "market_buy", "market_sell"):
        assert forbidden not in lowered


def test_installer_has_windows_line_endings():
    raw = INSTALLER.read_bytes()
    assert b"\r\n" in raw
    assert raw.count(b"\n") == raw.count(b"\r\n")

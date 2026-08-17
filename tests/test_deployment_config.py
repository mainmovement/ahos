"""Wave-25: deployment configuration must be truthful.

A compose file that references a missing env_file, or a Dockerfile whose pip
fallback silently installs different packages than requirements.txt, produces
the worst possible failure mode: it looks fine until the user tries to run it.
These tests are cheap and they keep 'copy, paste, run' honest.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
COMPOSE = ROOT / "docker-compose.yml"
DOCKERFILE = ROOT / "deployment" / "Dockerfile"
ENTRYPOINT = ROOT / "deployment" / "entrypoint.sh"


@pytest.fixture(scope="module")
def compose():
    return yaml.safe_load(COMPOSE.read_text(encoding="utf-8"))


def _services(compose):
    return compose["services"]


def test_every_referenced_env_file_exists(compose):
    """The original bug: env_file pointed at deployment/.env, which never existed."""
    for name, svc in _services(compose).items():
        for ef in (svc.get("env_file") or []):
            path = ROOT / ef
            example = path.with_name(path.name + ".example")
            assert path.exists() or example.exists(), (
                f"service '{name}' references {ef}, which does not exist "
                f"and has no .example to copy from")


def test_compose_uses_the_same_env_file_the_quickstart_creates(compose):
    """QUICKSTART tells the user to create ./.env. Compose must read that file."""
    for name in ("ahos-core", "ahos-bot"):
        assert ".env" in (_services(compose)[name].get("env_file") or [])


def test_bot_service_actually_runs_the_bot(compose):
    cmd = " ".join(_services(compose)["ahos-bot"]["command"])
    assert "run_bot.py" in cmd


def test_no_service_is_exposed_beyond_loopback(compose):
    """Single-user laptop deployment: nothing should be reachable off-machine."""
    for name, svc in _services(compose).items():
        for port in (svc.get("ports") or []):
            assert str(port).startswith("127.0.0.1:"), (
                f"service '{name}' publishes {port} on all interfaces")


def test_n8n_is_available_for_agent_workflows(compose):
    """The user explicitly asked for n8n agents in the stack."""
    n8n = _services(compose)["n8n"]
    assert "n8n" in n8n["image"]
    mounts = " ".join(n8n.get("volumes") or [])
    assert "n8n/workflows" in mounts, "shipped workflows are not mounted"


def test_n8n_telemetry_is_disabled(compose):
    env = _services(compose)["n8n"]["environment"]
    assert env.get("N8N_DIAGNOSTICS_ENABLED") == "false"


def test_data_directory_is_persisted_for_stateful_services(compose):
    for name in ("ahos-core", "ahos-bot"):
        mounts = " ".join(_services(compose)[name].get("volumes") or [])
        assert "./data:/app/data" in mounts


# ------------------------------------------------------------- Dockerfile --

def test_dockerfile_has_no_silent_dependency_fallback():
    """`pip install -r req.txt || pip install <other list>` builds a lying image."""
    txt = DOCKERFILE.read_text(encoding="utf-8")
    assert "|| pip install" not in txt


def test_dockerfile_does_not_reinstall_the_removed_anyio_phantom():
    """anyio was a phantom dependency; resolved by removal, not installation."""
    assert "anyio" not in DOCKERFILE.read_text(encoding="utf-8")


def test_entrypoint_exists_and_bootstraps_databases():
    assert ENTRYPOINT.exists()
    txt = ENTRYPOINT.read_text(encoding="utf-8")
    assert "init_databases.py" in txt
    assert txt.strip().endswith('exec "$@"'), "entrypoint must exec the CMD"


def test_entrypoint_is_made_executable_before_the_user_switch():
    """A chmod after USER can fail; then every container start breaks."""
    txt = DOCKERFILE.read_text(encoding="utf-8")
    assert txt.index("chmod +x /app/deployment/entrypoint.sh") < txt.index("USER ahosuser")


def test_container_runs_as_non_root():
    assert "USER ahosuser" in DOCKERFILE.read_text(encoding="utf-8")


# ----------------------------------------------------------------- config --

def test_env_example_documents_the_only_required_variable():
    txt = (ROOT / ".env.example").read_text(encoding="utf-8")
    assert "TELEGRAM_BOT_TOKEN=" in txt
    assert "ALL_PROXY=" in txt          # Iran path must be discoverable
    assert "DEXTOOLS_API_KEY=" in txt   # documented as optional


def test_env_example_ships_no_real_secrets():
    """Every key in the template must be blank or an obvious local default."""
    for line in (ROOT / ".env.example").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        if any(s in key.upper() for s in ("TOKEN", "KEY", "SECRET")):
            assert val == "", f"{key} ships a non-empty value in .env.example"


def test_env_file_is_gitignored_but_the_example_is_not():
    ig = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert ".env" in ig
    assert "!.env.example" in ig

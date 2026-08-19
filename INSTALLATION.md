# AHOS installation and setup

AHOS supports native Python 3.11+ on Windows 10/11, Linux, and macOS. Docker and
n8n are optional. No wallet, exchange key, or live execution dependency is
used.

## Windows (canonical native workflow)

```powershell
git clone <repo-url> ahos
cd ahos
Set-ExecutionPolicy -Scope Process Bypass
.\install_windows.ps1
# Optional: edit .env for Telegram, proxy, or provider settings
.\start_ahos.ps1       # or double-click start_ahos.bat
```

The installer verifies the interpreter version, creates `.venv`, installs only
from the declared requirement files, initializes SQLite, enforces UTF-8, and
runs offline smoke checks. To install from a local wheel cache:

```powershell
$env:AHOS_WHEELHOUSE = "D:\wheels"
.\install_windows.ps1
```

For an official 168-hour laptop soak, launching is not enough. Follow
[`AHOS_OPERATOR_QUICKSTART_WINDOWS.md`](AHOS_OPERATOR_QUICKSTART_WINDOWS.md)
and require its baseline and t0 gates.

## Linux / macOS

```bash
git clone <repo-url> ahos && cd ahos
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
python scripts/init_databases.py --with-guards
python tests/validate_n8n.py
```

One observation/scoring cycle:

```bash
AHOS_EVIDENCE_SOURCE=local python -m architecture.runtime \
  --single-cycle --observation-cycle --evidence-source local
```

Continuous runtime:

```bash
AHOS_EVIDENCE_SOURCE=local python -m architecture.runtime \
  --daemon --interval-sec 60 --observation-cycle --evidence-source local
```

`--observation-cycle` is required to run the frozen E-01 poller and outcome
labeler. Without it, score predictions cannot accumulate calibration pairs.

## Telegram bot only

The full runtime already polls Telegram when a valid token is configured. For a
bot-only process or offline console:

```bash
python run_bot.py --preflight
python run_bot.py
python run_bot.py --console
```

`TELEGRAM_BOT_TOKEN` is mandatory only for Telegram, not for deterministic
console/scoring logic. Restrict access with `TELEGRAM_ALLOWED_CHAT_IDS`.

## Optional laptop Docker profile

```bash
cp .env.example .env
# Edit .env as needed
docker compose up -d --build
docker compose logs -f ahos-core ahos-bot
```

The root compose file is canonical for the single-laptop profile. It runs the
observation cycle as local evidence, persists `data/`, binds n8n only to
`127.0.0.1`, and does not expose a trading service. Files under `deployment/`
include advanced PostgreSQL/VPS/target designs and may require additional
credentials; they are not the default native setup.

## Verification

```bash
python scripts/freeze_lane_a.py
python scripts/validate_imports.py
python tests/validate_n8n.py
python -m pytest -q -p no:cacheprovider
```

On Windows, use `.venv\Scripts\python.exe`; on Unix use `.venv/bin/python`.
See [`docs/canonical/CANONICAL_STATUS.md`](docs/canonical/CANONICAL_STATUS.md)
for current executed results and limitations.

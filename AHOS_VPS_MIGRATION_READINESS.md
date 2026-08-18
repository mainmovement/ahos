# AHOS VPS Migration Readiness (prepare only — no deploy)

**Date:** 2026-08-18  
**Scope:** paper-only observation daemon. No exchange keys. No wallet. No order APIs.  
**This document is not a deploy log.** Nothing here was executed on a VPS.

## Required packages

Host:

- Debian/Ubuntu-class Linux, systemd, `python3.11+`, `git`, `python3-venv`
- Optional: `chrony` or `systemd-timesyncd` (M-GAP-006 residual: absolute NTP)

Python (from `requirements.txt`):

```
PyYAML>=6.0.1
numpy>=1.26.0
pandas>=2.1.0
requests>=2.31.0
urllib3>=2.0.0
PySocks>=1.7.1
pytest>=7.4.0
pytest-timeout>=2.2.0
```

Runtime core uses stdlib `urllib`. No paid SDKs. Do **not** install exchange/web3 packages.

## Environment variables

Copy `.env.example` → `/etc/ahos/ahos.env` (`chmod 600`). **No secrets in git.**

| Variable | Required on VPS? | Purpose |
|---|---|---|
| `AHOS_ROOT` | no (default: clone path) | override project root |
| `AHOS_DATA_DIR` | recommended `/var/lib/ahos` | SQLite stores |
| `AHOS_CHAIN` | no (default `solana`) | observation chain |
| `TELEGRAM_BOT_TOKEN` | **no for soak** | leave empty → mock adapter |
| `TELEGRAM_ALLOWED_CHAT_IDS` | only if token set | |
| `ALL_PROXY` / `HTTPS_PROXY` | if egress filtered | SOCKS/HTTP |
| `DEXTOOLS_API_KEY` | no | unused unless purchased |
| `AHOS_EXECUTE_LIVE_TRADES` | must be unset/not `1` | safety veto (`architecture/security/hygiene.py`) |
| `AHOS_ALLOW_REAL_FUNDS` | must be unset/not `1` | same |

Do not set Binance/Coinbase/Kraken keys. Those names are vetoed when `=1`; they are not used as trading credentials.

## Directory layout

```
/opt/ahos/                      # git clone (code)
/opt/ahos/.venv/                # python -m venv
/etc/ahos/ahos.env              # optional secrets; chmod 600; not in git
/var/lib/ahos/                  # AHOS_DATA_DIR
  e01_discovery.sqlite
  paper_trading.sqlite
  ahos_local.sqlite
  ahos_knowledge.sqlite
/var/backups/ahos/              # nightly sqlite snapshots (not in git)
/etc/systemd/system/
  ahos-runtime.service          # from deployment/ahos-runtime.service
  ahos-watchdog.service
  ahos-watchdog.timer
```

Adjust `WorkingDirectory=` / `ExecStart=` / `AHOS_DATA_DIR` if paths differ from the shipped units (`deployment/ahos-runtime.service` lines 22–29).

## Backup policy

Tool: `scripts/sqlite_backup_restore.py` (Online Backup API).

Nightly (example, not installed here):

```
0 3 * * * AHOS_DATA_DIR=/var/lib/ahos /opt/ahos/.venv/bin/python \
  /opt/ahos/scripts/sqlite_backup_restore.py backup \
  --source /var/lib/ahos/ahos_local.sqlite \
  --dest /var/backups/ahos/ahos_local_$(date -u +\%Y\%m\%dT\%H\%MZ).sqlite
```

Repeat per store. Retain 7 days. After each backup, run `PRAGMA integrity_check` via the same script’s restore/drill path.

**Proven in-repo:** one restore drill — `reports/backup_restore_drill.json`.  
**Unproven:** 7 consecutive host nights + restore onto a fresh machine (M-GAP-010 residual).

## Monitoring requirements

| Signal | How | Gap if missing |
|---|---|---|
| Daemon alive | systemd `Restart=always` + `journalctl -u ahos-runtime` | |
| Heartbeat | `ahos-watchdog.timer` every 5 min; exit 2=STALE, 3=NO_HEARTBEATS | |
| Off-box alert | point a free uptime monitor at watchdog unit failure / a tiny HTTP wrapper | M-GAP-012 OPEN |
| Soak evidence | `python scripts/soak_snapshot.py` + `python scripts/system_state_snapshot.py` every 6h; commit snapshots | M-GAP-003 |
| Provider success | snapshot `provider_probe` on a host with working egress | M-GAP-007 |
| Integrity | snapshot `stores.*.integrity_check` | M-GAP-005 |

## Rollback plan

1. `systemctl stop ahos-runtime ahos-watchdog.timer`
2. `cd /opt/ahos && git fetch && git checkout <last known good SHA>`
3. Restore last good SQLite copies with `scripts/sqlite_backup_restore.py restore --backup … --dest …`
4. `python scripts/sqlite_backup_restore.py drill` (or per-store integrity)
5. `python scripts/validate_imports.py` and `pytest tests/ -q` on the VPS **or** accept the last committed `reports/*_run.json` for that SHA
6. `systemctl start ahos-runtime ahos-watchdog.timer`
7. Confirm watchdog `OK` via `python -m architecture.scheduling.watchdog --status --json`

Do not roll forward over a Lane-A hash change without a freeze governance commit.

## Explicitly out of scope for this migration

- n8n / Postgres stack in `docs/RUNBOOK_OPERATIONS.md` (legacy paper-cycle runbook; not the Phase-7/8 daemon)
- Live Telegram (M-GAP-009)
- Any exchange, wallet, or order path

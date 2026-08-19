# Windows laptop readiness report

## Verdict

**YELLOW by design/static evidence; RED as an unproven operational deployment.**

The repository contains a thoughtful native Windows path, but the audit host had neither Windows PowerShell nor `pwsh`; Docker was also unavailable. Therefore no PowerShell parse/execution, batch behavior, Python clean install, provider call, sleep/resume, reboot, Docker Desktop, or 168-hour run was proven.

## 1. Delivered Windows surfaces

| Surface | Purpose | Static finding |
|---|---|---|
| `install_windows.ps1` | find Python 3.11+, create `.venv`, install deps, create `.env`, initialize DBs, run smoke/n8n checks | coherent, fail-on-native-error helper, UTF-8, isolated interpreter |
| `start_ahos.ps1` | initialize stores and launch observation daemon with source `local` | correct current runtime flags, propagates exit code |
| `start_ahos.bat` | double-click wrapper/launcher | CRLF, UTF-8 code page, installer fallback, DB failure handling |
| `deployment/docker-compose.windows.yml` | optional Docker Desktop PG+n8n+runtime profile | unexecuted; mutable n8n tag; workflow mount does not satisfy command workflows |
| Windows quickstart/runbooks/soak protocol | gated operator sequence | detailed, but fixed commit reference is stale and execution is unproven |
| `config/paths.py` | root and data path resolution | cross-platform tests pass on Linux |

PowerShell, batch, and requirements files use CRLF; shell scripts use LF. `.gitattributes` preserves intended line endings.

## 2. Readiness dimensions

| Dimension | Rating | Evidence / gap |
|---|:---:|---|
| Python 3.11+ discovery | GREEN design | tries `py -3.11`, then `python`, and verifies version |
| Virtual environment | GREEN design | consistently uses `.venv\Scripts\python.exe` after creation |
| UTF-8/Persian output | GREEN design | environment, console encoding, and batch code page set |
| Path independence | YELLOW | script-root-relative paths and tests are good; no paths with spaces/non-ASCII Windows username were executed |
| Line endings | GREEN static | CRLF for Windows launchers/requirements, LF for shell assets |
| Dependency installation | RED reproducibility | lower bounds only; no lock/hashes/wheel cache shipped; clean Windows wheel resolution untested |
| Offline installation | YELLOW design | `AHOS_WHEELHOUSE` supported; no wheelhouse manifest/hash/architecture validation provided |
| SQLite initialization | GREEN component | idempotent bootstrap and temp-store tests pass; no Windows locking/AV/cloud-sync test |
| Runtime launch | YELLOW | flags and interpreter correct; PowerShell/batch not executed |
| Provider/network/proxy | RED operational | filtered-network handling is designed; no Windows proxy/TLS/provider proof |
| Telegram | RED operational/security | token required, no live test; blank allowlist opens access |
| Sleep/restart/recovery | RED | no service/task registration or auto-restart; manual window must stay open |
| Watchdog | YELLOW component | logic tested; no separate Windows scheduled monitor/alert owner |
| Backup/restore | YELLOW component | scripts tested locally; no real Windows file-lock/OneDrive/AV recovery drill |
| Docker Desktop | RED | compose not validated/executed; image context risk exists |
| n8n | RED | service/workflow import/path/credential mismatch |
| 168-hour soak | RED | no eligible baseline/t0/end artifact from a Windows host |

## 3. Correct Windows design decisions

- Repository path is derived from the launcher rather than hardcoded.
- The Python launcher avoids the Windows Store alias when possible.
- The installer stops after native failures rather than printing success.
- `.venv` is used for pip, smoke checks, DB initialization, and runtime.
- Database initialization is idempotent and uses canonical bootstrap code.
- `--observation-cycle` is present, so the frozen poller and outcome materializer can run.
- `--evidence-source local` is explicit; ordinary runtime defaults to `sandbox`.
- UTF-8 settings address Persian logs and text.
- Windows docs distinguish sandbox hours from official laptop evidence.
- Live trading, wallet, and exchange execution are absent.

These merits should be preserved during remediation.

## 4. Blocking findings

### WIN-001 — No native execution evidence

Linux tests that read a `.ps1` or assert strings do not parse or execute PowerShell. Required proof is a clean Windows 10/11 artifact containing OS build, PowerShell version, Python architecture/version, dependency fingerprint, exact commit, command results, and sanitized logs.

### WIN-002 — Dependency resolution is not reproducible

`requirements.txt` declares 8 lower-bounded core packages and `requirements-optional.txt` adds 3. There are no upper bounds, hashes, lock files, package metadata, or wheel manifest. A future clean install can select incompatible major versions or fail offline. The Linux audit happened to use pytest 9.1.1, NumPy 2.4.6, and pandas 3.0.5.

Required proof: generate and test a Python 3.11 Windows x64 lock/wheel manifest without committing a virtual environment or binary cache unnecessarily.

### WIN-003 — No unattended restart owner

The PowerShell/batch launcher runs a foreground process. If Python crashes, Windows reboots, the laptop sleeps, or the terminal closes, no Task Scheduler/Windows service restarts it. The Linux systemd assets do not solve this.

Required design: a minimal, user-approved scheduled task/service with delayed network startup, working directory, environment, log rotation, restart limits, and explicit stop/uninstall commands. Do not add a second scheduler inside AHOS.

### WIN-004 — Sleep/reboot time accounting is procedural only

Docs instruct the user to record interruptions. There is no demonstrated sleep prevention, resume hook, clock discontinuity handling on Windows, or automatically accumulated eligible-duration ledger. A 168-hour wall-clock claim must subtract downtime and survive reboot.

### WIN-005 — “local” is not cryptographically/gate-bound to an eligible baseline

The launchers mark every run `local` before checking the official baseline/t0 gates. `ScoreLedger` treats source `local` as calibration-eligible, so a user can generate eligible rows by double-clicking the launcher without completing provider/baseline/host gates. This does not corrupt no-peeking logic, but it weakens evidence provenance.

Recommendation: include a baseline artifact ID/hash and host fingerprint in each eligible prediction, and reject/namespace local calibration rows when the baseline is absent/stale. Preserve easy non-official operation under a separate source.

### WIN-006 — Telegram is open when allowlist is blank

`.env.example` leaves `TELEGRAM_ALLOWED_CHAT_IDS` blank and says only the bot token is mandatory. `TelegramSecurityGate` explicitly returns authorized for everyone when the allowlist set is empty. A private laptop intelligence bot should fail closed or require explicit `TELEGRAM_OPEN_ACCESS=1`.

### WIN-007 — Docker Desktop path is unsafe/unproven

There is no `.dockerignore`; a normal installer-created `.env`, local databases, `.venv`, `.git`, reports, and large data can be sent in build context and copied by `COPY . /app`. Windows compose also uses mutable n8n `latest`, maps port 8000 without a server, and does not operationally connect all workflows.

Do not run Docker builds until P0 packaging protection is approved.

### WIN-008 — Native logs and disk policy are incomplete

Runtime writes reports/databases and prints logs, but the foreground native launcher does not provide a rotating file log, disk quota/preflight enforcement, or Windows event log integration. Compose has some rotation; native mode does not.

### WIN-009 — Concurrent process/SQLite and Telegram ownership is under-specified

Root Docker profile runs core and standalone bot against shared data. Native docs can also lead users to run bot and daemon separately. The runtime's embedded Telegram poll passes no offset, while `run_bot.py` persists one; this can replay updates or compete for them. The adapter swallows poll errors (bypassing the launcher's documented backoff) and send callers can count `ok=false` as delivered. Scheduler locks cover cycles, not every table writer. SQLite WAL/backup/antivirus/cloud-sync behavior must be tested with the actual process topology.

## 5. Required native acceptance matrix

All results must be recorded; unavailable prerequisites are FAIL/NOT RUN, never inferred.

| Gate | Required action | Pass evidence |
|---|---|---|
| Clean install | fresh Windows user/path with spaces, Python 3.11 x64 | lock-resolved install and import gate |
| PowerShell | run installer/launcher under Windows PowerShell 5.1 and, optionally, PowerShell 7 | exact exit codes and UTF-8 logs |
| Batch | double-click/start `.bat` | correct installer fallback, Ctrl+C, exit/error behavior |
| Stores | bootstrap, integrity, append-only guard, concurrent lock tests | pre/post schema checksums and read/write evidence |
| Provider | run read-only provider probe | classified provider results; TLS remains enabled |
| Telegram | private bot with allowlist | unauthorized denial, authorized NLU, token-redacted logs |
| Local AI | optional Ollama install/model probe | model hash/tag, hardware, latency/RAM and offline response |
| Sleep/resume | sleep beyond lease/heartbeat limits | stale detection, no duplicate cycle, honest downtime |
| Hard crash | force-kill runtime | bounded restart, stale lease recovery, no row corruption |
| Reboot | restart Windows | delayed supervised recovery and preserved evidence source |
| Backup/restore | nightly backup and isolated restore drill | hashes, integrity, data equality, retention |
| Disk full/read-only | controlled temp target fault | visible failure, no false success, recovery steps |
| Docker Desktop | build after `.dockerignore`, run chosen profile | no secret in context/image, health, mount/port proof |
| 168-hour window | eligible baseline -> valid t0 -> uninterrupted/adjusted run -> end report | host/commit-bound duration and required evidence counts |

## 6. Phased Windows plan

1. **P0 safety:** `.dockerignore`; default-deny Telegram; side-effect-free imports/tests.
2. **P1 reproducibility:** lock/hashes/wheel manifest, LICENSE/SBOM, native clean-install CI/manual evidence.
3. **P1 operations:** one inbound Telegram owner, log rotation, supervised restart, baseline-bound evidence identity.
4. **P2 resilience:** sleep/reboot/crash/disk/backup drills on the actual laptop.
5. **P2/P3:** only then start the official 168-hour window; Local AI remains optional and separately gated.

No Windows readiness or soak completion should be claimed before these gates produce artifacts.

# AHOS Windows Operator Runbook

Official 168h soak starts **only** on the Windows laptop after every step below succeeds.

Sandbox / Arena time does **not** count.

Use PowerShell. Commands assume you are in the clone root.

---

## 1. Clone or update the repository

After the reconstruction PR is merged:

```
git clone https://github.com/mainmovement/ahos.git
cd ahos
git checkout main
git pull --ff-only
git rev-parse HEAD
```

If you already have the clone:

```
cd <path-to-ahos>
git fetch origin
git checkout main
git pull --ff-only
git status
```

`git status` must be clean. Record the exact `main` SHA in the baseline; do not rely on any unavailable historical SHA.

## 2. Create the environment

```
python --version
python -m venv .venv
```

Need Python 3.11+.

## 3. Install dependencies

```
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe scripts\init_databases.py
```

Do **not** install exchange or web3 packages.

## 4. Verify imports

```
.\.venv\Scripts\python.exe scripts\validate_imports.py
```

Must end: `VALIDATION PASSED`.

Optional record:

```
.\.venv\Scripts\python.exe scripts\record_test_run.py --out reports\validate_imports_run.json -- .\.venv\Scripts\python.exe scripts\validate_imports.py
```

## 5. Verify Lane-A

```
.\.venv\Scripts\python.exe scripts\freeze_lane_a.py
```

Must print: `Lane-A integrity OK`.

## 6. Create the laptop baseline

Working tree still clean:

```
git status
.\.venv\Scripts\python.exe scripts\record_local_laptop_baseline.py
```

## 7. Confirm baseline file

Open `reports\local_laptop_baseline.json`. Required:

| Field | Must be |
|---|---|
| `os.system` | `Windows` |
| `git.working_tree_clean` | `true` |
| `lane_a.ok` | `true` |
| `official_168h_eligible` | **`true`** |
| `databases.integrity.*` | `ok` (or create stores via `init_databases.py` first) |
| `AHOS_EXECUTE_LIVE_TRADES` | `null` / unset |

If `official_168h_eligible` is not `true`: **STOP. Do not start the daemon.**

Also confirm (see `AHOS_LAPTOP_READINESS_CHECKLIST.md`):

- AC power
- sleep / hibernate / lid = do nothing on AC
- `TELEGRAM_BOT_TOKEN` unset
- `AHOS_EXECUTE_LIVE_TRADES` unset

---

## Official soak start (only after §1–7)

This timestamp is **SOAK HOUR 0**.

```
.\.venv\Scripts\python.exe -m architecture.runtime --daemon --interval-sec 60 --observation-cycle
```

Leave that window open. Second PowerShell:

```
.\.venv\Scripts\python.exe -m architecture.scheduling.watchdog --status --max-age-sec 300 --json
.\.venv\Scripts\python.exe scripts\system_state_snapshot.py --probe-providers --out reports\soak\system_state_t0.json
```

Clock starts only when **all** are true on this laptop:

1. Windows laptop  
2. Clean git tree  
3. Baseline `official_168h_eligible=true`  
4. Watchdog `status=OK`  
5. First snapshot written  

Then write a **new** `reports\local_soak_start.json` with this laptop UTC. Do not reuse the sandbox start file.

During 168h: **no code changes**. Snapshots every 6h, daily status, nightly backups. Failures only on Day 1 / 3 / 5 per `AHOS_LOCAL_SOAK_PROTOCOL.md`.

# AHOS canonical status

**Status date:** 2026-08-19
**Runtime target:** Python 3.11+, one Windows laptop; Linux/macOS and optional
Docker remain supported.
**Safety status:** observation-first, paper-only, no wallet/exchange SDK, no
transaction signing or order-placement path.

## Architecture now

The canonical flow is:

```text
free/keyless providers or optional configured providers
  -> normalized candidate
  -> immutable Evidence bundle
  -> deterministic features + security/risk + opportunity score
  -> score ledger (only when explicitly injected)
  -> exitability + virality + whale context
  -> deterministic cognitive panel
  -> DecisionAdvisor
  -> ENTER-gated alert / Persian Telegram response
  -> optional paper-position review
```

The frozen Lane-A observation/outcome pipeline remains hash-pinned and separate
from runtime scoring. `architecture/intelligence` owns the Evidence-only score
path; `architecture/intel` supplies specialist context. `architecture/learning`
is the sole production prediction ledger/calibration layer. Versioned paper
engines remain research assets rather than duplicate live runtimes.

## Integrated capabilities

- Candidate/report pairing is preserved through ranking; alerts cannot combine
  one token's identity with another token's score.
- Every injected `ScoreLedger` records append-only, source-namespaced,
  version/fingerprint-pinned predictions. Calibration excludes test/sandbox
  rows, enforces no-peeking, and exposes a score-band rate only after strict
  sample and positive-count guards pass.
- Exitability, whale, virality, the cognitive panel, and advisor run before a
  special opportunity announcement. Only vetted action `ENTER` can reach that
  branch. Analyzer failure is recorded and fails closed for entry evidence.
- The known 30% sell-tax trap is rejected by scoring and independently by
  exitability/panel/advisor gates.
- The panel currently executes 42 unique deterministic lens functions. Team
  governance declares 39 active members across seven teams; the historical
  100-person registry has materially lower measured executable coverage. The
  roster response reports both instead of claiming “100 active agents.”
- Position monitoring is wired into the runtime for open positions in the
  canonical paper-position store, rejects stale/missing price data, and emits
  advice/alerts only. Telegram buy statements remain an append-only paper log
  and receive on-demand exit advice; they do not create or execute real orders.
- Telegram remembers recent autonomous announcements in a bounded, stale-aware,
  atomic local file, so a post-restart “I bought it” reply can resolve visibly.
  Token/feed/model-controlled text is escaped for Telegram HTML.
- Abnormal-movement and wash-divergence checks now use real 5-minute/1-hour
  fields populated by adapters; the unwritten `volume_velocity` field was
  removed.
- Optional AI providers and Ollama remain advisory. Missing keys/network return
  OFFLINE/UNKNOWN and can never override deterministic vetoes.
- Operational health responses use current SQLite/scheduler measurements. A
  missing or stale heartbeat is not called `RUNNING`, uptime is not inferred
  from the latest heartbeat, and diagnostic failure returns `UNKNOWN` rather
  than a fabricated green status or historical row counts.

## Data and preserved assets

- Twelve tracked research CSV datasets were read, row-counted, and matched to
  their SHA-256 manifests. Their manifest paths are now repository-relative;
  dataset bytes were not changed.
- Lane-A schemas, outcome history, research reports, experiments, registries,
  n8n workflows, and intentionally versioned paper engines are preserved.
- No historical SQLite database existed at audit start. Runtime SQLite stores
  are generated, ignored, integrity-checked, and reproducible from versioned
  schemas/bootstrap code.
- Three raw source patches and 25 phase snapshots were relocated, not deleted,
  to `docs/history/`. One byte-identical report alias was removed after its
  hash and replacement were manifested.

## Windows workflow

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\install_windows.ps1
# edit .env if Telegram/proxy/optional providers are desired
.\start_ahos.ps1       # or double-click start_ahos.bat
```

The installer proves CPython >=3.11, creates `.venv`, uses `.venv` for all pip
and validation commands, supports `AHOS_WHEELHOUSE` for offline installation,
forces UTF-8, creates the safe root `.env`, generates an ignored machine-local
path snapshot, initializes all SQLite schemas, and runs offline smoke/n8n
checks. The launchers preserve CRLF, initialize databases, run the observation
cycle, and explicitly stamp operator evidence `local`.

Docker is optional. Root `docker-compose.yml` is the canonical laptop profile:
it keeps ports on loopback, persists SQLite/n8n state, runs the observation
cycle, and starts the Telegram bot. Deployment subdirectory compose files are
advanced target designs and may require PostgreSQL/n8n credentials.

## Validation record

Pre-integration baseline:

- `pytest`: **1,158 passed, 1 failed**; the failure was a stale dependency hash
  in `AHOS_LAPTOP_OPERATION_REPORT.md`, not a suppressed test.
- import/secret/evidence validation: PASS (146 module imports at that time).
- Lane-A freeze: PASS, 36 pinned files.
- production `compileall`: PASS.
- six n8n workflows: static validation PASS.

Latest full-suite run before final documentation/cleanup:

- `pytest`: **1,395 passed, 1 failed in 170.44s**. The sole remaining failure was
  the same known operation-report hash and is corrected in this canonicalization.

Final post-integration validation on this Linux sandbox:

- `pytest -q -p no:cacheprovider`: **1,414 passed in 171.47s**.
- production `compileall`: PASS. Its generated `__pycache__` directories were
  removed before the clean-artifact gate.
- import/architecture/secret validation: PASS; **153 modules** imported in
  fresh interpreters, 17 evidence-boundary files and 2,073 source files scanned.
- Lane-A freeze: PASS, all **36** pinned files unchanged.
- n8n static validator: PASS, **6/6** workflows.
- structure parsing: PASS, **16 YAML** and **124 JSON** files.
- temporary bootstrap: PASS, **4 SQLite stores**, each `integrity_check=ok`.

The first import-validator invocation immediately after `compileall` correctly
failed its clean-artifact gate on the generated `__pycache__` directories. The
caches were deleted and the validator was rerun to the PASS recorded above.
No Docker service, live provider, Telegram connection, n8n process, or native
Windows host was started; static/config tests must not be read as those live
proofs.

## Honest limitations and next phase

- No live trading exists. `ENTER`, `EXIT`, and sizing are advisory/paper
  vocabulary, not executable orders.
- A high score is ordinal, not a probability. Until real local outcomes clear
  calibration guards, the sizing lens abstains.
- Free providers, news, Telegram, and cloud AI may be blocked, rate-limited, or
  unavailable. Static n8n JSON validation is not proof of a live n8n instance.
- The 100-person registry is a research roster, not 100 simultaneous agents.
  Several cards/members remain advisory, inert, or pending data.
- Paper positions opened through the canonical manager are autonomously
  reviewed. A Persian Telegram buy log lacks a trustworthy USD allocation and
  therefore is not silently promoted into that manager; exit advice is derived
  on demand from observations nearest its logged timestamp.
- Docker images are operational conveniences, not proof of the official
  Windows 168-hour soak. That gate must be run on the actual laptop using the
  documented baseline/t0 procedure.
- The next phase is real operator data accumulation, provider reachability
  measurement, calibration after guards clear, and a Windows soak—not more
  invented readiness labels or autonomous execution.

See `docs/DOCUMENT_CLASSIFICATION.md` for documentation precedence and
`docs/audit/` for inventory, data preservation, and cleanup evidence.

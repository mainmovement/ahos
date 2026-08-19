# Test reality report

## 1. Executed results

| Run | Result | Meaning |
|---|---|---|
| Pre-integration baseline | 1 failed, 1,158 passed in 155.26s | one stale documentation hash; failure was diagnosed, not suppressed |
| Intermediate full suite | 1 failed, 1,395 passed in 170.44s | same stale hash after expanded code integration |
| Final snapshot suite | **1,414 passed in 171.47s** | actual full result for `c775978...` on Linux sandbox |
| Audit-artifact regression | **1,414 passed in 170.56s** | rerun after adding only these audit Markdown artifacts; cache/bytecode disabled |
| Collection | **1,414 collected in 3.14s** | no collection error; cache/bytecode disabled |
| Provider focus | **83 passed in 6.80s** | provider contracts, adapters, registry, failures under injected/local transports |
| Score/calibration focus | **58 passed in 5.52s** | deterministic scoring ledger and calibration mechanics |
| n8n validator | **6/6** | structural JSON/workflow checks only |
| Import/architecture/secret gate | PASS | 153 fresh-interpreter imports; 17 evidence files; 2,073 source files |
| YAML/JSON parse | 16 YAML, 124 JSON passed | syntax/structure only |
| Temporary SQLite bootstrap | 4/4 stores, integrity OK | schema bootstrap on temporary stores |

No `skip`, `xfail`, or dynamic `pytest.skip` marker was found in `tests/`. This is positive for visible coverage but also means unavailable external/Windows capabilities are represented by mocks/static assertions rather than explicitly marked live tests.

## 2. Inventory and taxonomy

- 100 top-level `tests/test_*.py` modules.
- 1,414 collected test cases; parameterization contributes materially to the case count.
- 17 files use precise mock/patch/monkeypatch constructs.
- 40 files contain static source/config/existence inspection constructs.
- 57 files use `tmp_path`, `tempfile`, or `TemporaryDirectory`.
- 12 files launch subprocesses, generally Python CLIs rather than PowerShell/Docker.
- 4 files reference network primitives; calls are injected/local/mock-oriented in the passing suite, not public-provider E2E.

### Taxonomy by evidence type

| Type | Representative modules | Reality |
|---|---|---|
| Unit/component | scoring, features, risk, lenses, NLU, alert, cost/exitability, provider parsers | strong breadth and edge-case parameterization |
| Integration | `test_opportunity_pipeline_integration.py`, `test_phase4_intelligence_integration.py`, `test_positions_and_ledger_matrix.py`, `test_announcement_followup.py` | meaningful in-process wiring, mostly with fixtures/injected adapters |
| Contract/schema | provider abstraction, position ledger schema, store columns, agent matrix, master directive, score ledger/calibration | strong structural invariants; may not prove deployed service compatibility |
| Architecture/static | architecture P1, deployment config, launchers, operator docs, zero-money patterns, import boundary | valuable drift guards; many do not execute the referenced host/tool |
| Adversarial/fault | provider failure resilience, collector visibility, scheduler fault, operational failure, reliability challenge, anti-echo, security hardening | good deterministic failure coverage; public-network and OS faults are simulated |
| Runtime | runtime lifecycle/W11/hardening/observation/scheduler/pipeline tests | lifecycle components tested; not an unattended real daemon window |
| Windows | path/cross-platform, Windows installer, phase-18 launchers | text/line-ending/path/subprocess checks on Linux; no PowerShell host |
| Data/science | baseline stats, wave-7 research, E-01 gate, paper v1/v2/v3/v3.2, calibration | code mechanics strong; current real sample is empty/insufficient |
| Security | security hardening/intelligence, feature boundaries, zero-money, secret/import gate | strong static/type/logic controls; not a penetration or dependency vulnerability audit |
| E2E | `test_pipeline_e2e_matrix.py` and opportunity integration | in-process fake/injected E2E, not provider -> Windows -> Telegram -> persisted outcome E2E |
| Performance/soak | performance stress, control-plane soak, soak snapshot | deterministic/fake-clock and local-load tests; not 168 real hours, sleep, reboot, or resource exhaustion |

## 3. What the passing count proves

The suite gives strong evidence that:

- deterministic score/risk/security logic is internally consistent for fixtures;
- candidate/report identity remains paired through ranking;
- the complete specialist veto/panel/advisor chain suppresses unsafe announcements;
- missing/unknown provider data is not silently converted to success;
- score persistence and calibration eligibility/no-peeking guards work on temporary fixtures;
- paper-only and forbidden execution patterns are enforced by current source/tests;
- schema bootstrap, append-only triggers, scheduler leases, and many failure states work in SQLite;
- Telegram NLU, response shape, escaping, follow-up memory, and mock adapter behavior work (but failed-send acknowledgement and poll-error propagation are not correctly integrated);
- current source/config/JSON/YAML imports and parses on the audit Linux environment.

## 4. What it does not prove

The suite does **not** prove:

- native Windows PowerShell/batch execution or Docker Desktop behavior;
- any public provider's current endpoint, payload, availability, rate limit, or sanctions/filtering behavior;
- a real Telegram bot token, private access configuration, long-poll recovery, or dual-poller safety;
- Docker build safety or service startup;
- n8n import, credentials, PostgreSQL connectivity, `/opt/ahos` commands, or workflow execution;
- Ollama installation, model presence, Persian quality, latency, RAM/disk/CPU sufficiency;
- PostgreSQL schema/runtime parity;
- a 168-hour soak, sleep/resume, power loss, reboot, or supervised restart;
- empirical opportunity value or probability calibration;
- dependency resolution reproducibility or a clean install across future major versions;
- code coverage percentage. No pytest code-coverage configuration/artifact for this snapshot was generated;
- an autonomous planning/edit/test/repair/Git/rollback agent.

## 5. Weak or potentially misleading test classes

### 5.1 Static/existence-only tests

`test_deployment_config.py`, `test_windows_installer.py`, `test_phase18_launchers.py`, operator-document tests, and portions of architecture/security tests inspect file content, flags, strings, paths, or parseability. These are useful contract pins, but a string such as `--observation-cycle`, a service name, or a Docker healthcheck does not execute the tool.

Recommendation: retain these tests, but label them `static_contract`; add separately marked host/live tests rather than weakening or deleting assertions.

### 5.2 Over-mocking risk

The 17 precise mock-bearing files include provider, scheduler, runtime, Telegram, launcher, and follow-up paths. Injection is appropriate for deterministic CI; however, it can validate adapters against fixture assumptions while a live provider/API/OS has drifted.

Recommendation: keep mocks and add opt-in contract probes whose results are recorded and never required for offline deterministic CI.

### 5.3 Soak/performance naming

“soak” and “stress” tests use controlled clocks/local loops and validate logic. They are not elapsed-time host endurance evidence. Reports and docs must not turn their names into a claim that a real soak ran.

### 5.4 Source-pattern security checks

Pattern tests found no order/wallet execution and the isolated secret scanner found no tracked credential. Pattern absence does not prove dependency safety, image safety, authorization, or runtime secret non-disclosure. The missing `.dockerignore` and default-open Telegram gate are examples the green pattern suite did not prevent.

## 6. Test/store isolation finding

`tests/conftest.py` has a session-autouse fixture that bootstraps the four **repository-local ignored databases** when absent. It does not redirect every default path to a temporary directory. Consequences:

1. a supposedly read-only test run mutates workspace runtime state;
2. tests can observe machine-local rows and become host/order dependent;
3. schema bootstrap evidence is mixed with operator data;
4. an unsafe imported module can write into the real ignored store.

The concrete demonstration is `engine/telegram_live_test.py`: import validation ran its module-level harness and produced five `control_flags` rows per import. Four imports account for all 20 rows in `ahos_local.sqlite`.

Classification: **RED isolation defect**, despite all tests passing.

Required correction after approval:

- set all store/report/path environment overrides to a session temp root before importing application modules;
- bootstrap temporary stores there;
- add pre/post filesystem and SQLite row-count guards around import validation;
- reserve explicit `@pytest.mark.local_state`/opt-in tests for operator-store inspection;
- never delete the current 20 rows until a preservation/attribution artifact is approved.

## 7. Disabled and external tests

There are no skipped/xfail tests, but there is also no explicit marker taxonomy such as:

- `unit`, `integration`, `contract`, `architecture`, `security`;
- `windows_native`, `docker`, `n8n`, `postgres`, `ollama`, `telegram_live`, `provider_live`;
- `local_state`, `network`, `slow`, `soak`.

A test may therefore look “E2E” or “Windows” by filename while remaining an offline Linux contract test. Add markers and report each lane separately; do not force external lanes into ordinary CI and do not count unexecuted lanes as pass.

## 8. CI/reproducibility gaps

- No tracked `.github/workflows` CI configuration exists in this checkout.
- Requirements use lower bounds without a lock or hashes; the audit environment resolved pytest 9.1.1, NumPy 2.4.6, and pandas 3.0.5, not merely their documented minimums.
- `pytest-timeout` is declared/installed but no timeout marker or pytest timeout setting was found.
- Full-suite evidence should always record command, interpreter, OS, commit, dependency fingerprint, duration, and dirty status via `scripts/record_test_run.py`.

## 9. Test verdict

**GREEN for broad offline deterministic behavior; YELLOW overall; RED for workspace isolation and external/native operational proof.** The correct response is to add truthful lanes and isolation—not delete failures, reduce guard thresholds, or inflate the count.

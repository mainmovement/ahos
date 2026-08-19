# AHOS — Artificial Hybrid Opportunity Scoring System

> **Evidence-First Early Crypto Opportunity Intelligence & Decision Support Platform**  
> *Non-trading by law | Never an automated trading bot | $0/month cost ceiling | Iran-resilient*

---

## 1. Core Mission & Scientific Invariants
AHOS is an autonomous intelligence platform designed to observe, normalize, score, and explain early crypto market opportunities across Solana and EVM chains.

- **DATA > AI:** Empirical evidence and on-chain observations overrule AI narrative consensus.
- **DETERMINISTIC FLOOR:** Operates 100% reliably at $0 cost on free public feeds without requiring commercial AI keys.
- **100% PAPER ONLY:** Live trading execution is strictly prohibited by type-level constraints and governance law.
- **WHY-LAW MANDATED:** Every score, alert, and decision contains explicit positive reasons, risk deductions, and provenance evidence references.
- **PERSIAN-FIRST TELEGRAM EDGE:** Natural language query interface tailored for Persian-speaking users ending with: `«تصمیم نهایی با کاربر است.»`.

---

## 2. Windows 11 Laptop (No VPS Required)
AHOS supports a local, observation-only deployment on one Windows laptop. A VPS, cloud VM, Docker, exchange key, wallet key, and live-trading capability are **not** required.

For an ordinary local launch:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\install_windows.ps1
.\start_ahos.ps1
```

> `start_ahos.ps1` / `start_ahos.bat` start the daemon with
> `--daemon --interval-sec 60 --observation-cycle` and
> `AHOS_EVIDENCE_SOURCE=local`, so observation polling, outcome labeling, and
> calibration-eligible predictions are all active.

Starting the daemon is only one step of the official window. For the 168-hour reliability soak, the gated procedure still applies — follow these in order:

1. [`AHOS_OPERATOR_QUICKSTART_WINDOWS.md`](AHOS_OPERATOR_QUICKSTART_WINDOWS.md) — the single PowerShell path
2. [`AHOS_LOCAL_ACTIVATION_CHECKLIST.md`](AHOS_LOCAL_ACTIVATION_CHECKLIST.md) — power, disk, sleep, evidence source
3. Run `scripts/record_local_laptop_baseline.py` and require `official_168h_eligible=true`.
4. Start the daemon with `AHOS_EVIDENCE_SOURCE=local` and
   `--daemon --interval-sec 60 --observation-cycle`.
5. Run `scripts/soak_t0_snapshot.py` and require `t0_valid=true` — that timestamp is hour 0.
6. Follow [`AHOS_LOCAL_SOAK_PROTOCOL.md`](AHOS_LOCAL_SOAK_PROTOCOL.md).

Arena/sandbox runtime does not count toward the official laptop clock.

---

## 3. Architecture & Subsystems
- `architecture/runtime/`: Application lifecycle manager, startup validation, structured JSON logging with correlation `run_id`.
- `architecture/collector/`: Multi-provider polling engine (DexScreener, GeckoTerminal, GoPlus, RugCheck) with 3-state Circuit Breaker and exponential retry.
- `architecture/scheduling/`: Wall-clock schedule alignment ($s+15\text{m}$ to $s+7\text{d}$), atomic lease locking (`scheduler_locks`), and downtime gap registration (`missed:<slot>`).
- `architecture/scoring/`: 8-stage deterministic decision pipeline answering all 8 canonical opportunity questions.
- `architecture/positions/`: Event-sourced paper position manager with fee/slippage modeling and realizable PnL.
- `architecture/knowledge/`: Trust Registry (K-01), Versioned Claim Store (K-02), 10 Expert Lens Cards (K-03), and 12-Stage OSS Pipeline (K-04).
- `telegram_ai/`: Persian NLU intent parser, Section X Response Contract formatter, and Bot API abstraction.

---

## 4. Testing & Verification
```bash
python scripts/freeze_lane_a.py
python scripts/validate_imports.py
python -m pytest tests/ -q
```

The latest machine-readable results are committed in `reports/validate_imports_run.json` and `reports/pytest_run.json`; do not rely on a hard-coded historical count.

---

## 5. License & Governance
Governed by immutable `MASTER_DIRECTIVE_v1` (hash-pinned: `e2457c0d...`).  
Daily Agent Mode ops: `docs/AGENT_MODE_OPERATIONAL_DIRECTIVE_FA.md` (living; does not supersede v1).  
Licensed under the Apache-2.0 License.

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

## 2. Quick Start on Windows 11 Laptop
Double-click `install_windows.ps1` (or `start_ahos.bat`) to install dependencies, initialize databases, and launch the daemon.

```powershell
# In PowerShell:
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\install_windows.ps1
.\start_ahos.ps1
```

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
pytest tests/ -v
```
All 481+ tests pass with zero failures and zero warnings.

---

## 5. License & Governance
Governed by immutable `MASTER_DIRECTIVE_v1` (hash-pinned: `e2457c0d...`).  
Daily Agent Mode ops: `docs/AGENT_MODE_OPERATIONAL_DIRECTIVE_FA.md` (living; does not supersede v1).  
Licensed under the Apache-2.0 License.

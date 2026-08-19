# AHOS — Artificial Hybrid Opportunity Scoring System

> **Evidence-First Early Crypto Opportunity Intelligence & Decision Support Platform**  
> *Non-trading by law | Never an automated trading bot | $0/month cost ceiling | Iran-resilient*

---

## 1. Core Mission & Scientific Invariants
AHOS is an observation-first intelligence platform designed to normalize, score, vet, and explain early crypto market opportunities across Solana and EVM chains. It is not a readiness certificate or a trading system.

**Current capability, validation, and limitations:** [`docs/canonical/CANONICAL_STATUS.md`](docs/canonical/CANONICAL_STATUS.md)
**Documentation precedence:** [`docs/DOCUMENT_CLASSIFICATION.md`](docs/DOCUMENT_CLASSIFICATION.md)

- **DATA > AI:** Empirical evidence and on-chain observations overrule AI narrative consensus.
- **DETERMINISTIC FLOOR:** Scoring and safety logic require no commercial AI key; live feed availability is reported honestly and is never assumed.
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
- `discovery/`: hash-pinned Lane-A observation, identity, outcome, and research evidence path.
- `architecture/runtime/`: lifecycle, scheduling, local evidence namespace, observation cycle, Telegram polling, score persistence, and paper-position review.
- `architecture/collector/` + `architecture/providers/`: normalized multi-provider runtime collection with UNKNOWN/failure discipline.
- `architecture/intelligence/`, `features/`, `security/`, `risk/`, `scoring/`: the canonical Evidence-only deterministic score path.
- `architecture/intel/` + `architecture/decision/`: exitability, virality, whales, optional narrative context, and safety-ratcheting advice.
- `architecture/knowledge/`: 42 unique executable deterministic lens functions, seven governed teams, and measured—not advertised—coverage of the historical 100-person registry.
- `architecture/learning/`: append-only, source-isolated predictions and no-peeking guarded calibration.
- `architecture/positions/` + `paper_trading/`: paper-only position advice, monitoring, and intentionally versioned research engines.
- `telegram_ai/`: Persian intents, persistent announcement follow-up, HTML-safe response contracts, and Telegram adapters.

---

## 4. Testing & Verification
```bash
.venv/bin/python scripts/freeze_lane_a.py
.venv/bin/python scripts/validate_imports.py
.venv/bin/python tests/validate_n8n.py
.venv/bin/python -m pytest -q -p no:cacheprovider
```

On Windows replace `.venv/bin/python` with `.venv\Scripts\python.exe`. Historical machine-readable reports retain the host and time at which they were produced; use the executed-results section in the canonical status document for the current checkout.

---

## 5. License & Governance
Governed by immutable `MASTER_DIRECTIVE_v1` (hash-pinned: `e2457c0d...`).  
Daily Agent Mode ops: `docs/AGENT_MODE_OPERATIONAL_DIRECTIVE_FA.md` (living; does not supersede v1).  
Licensed under the Apache-2.0 License.

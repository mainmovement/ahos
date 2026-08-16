# AHOS Self-Repair & Health Manager Design Specification

## 1. Core Principles
The AHOS Health Manager (`engine/health_manager.py`) operates under strict epistemic governance:
1. **Detect ✅:** Automatically identifies missing files, corrupted databases, missing packages, and failed services.
2. **Explain ✅:** Provides clear human-readable explanations of detected issues.
3. **Suggest Fix ✅:** Recommends exact corrective commands and restoration steps.
4. **Never Modify Automatically ❌:** Files and databases are NEVER modified automatically without explicit user confirmation (`--repair --confirm`).

---

## 2. Diagnostic Inspection Areas
1. **Essential System Files:**
   - `contracts/agent_contract_v1.json`
   - `contracts/ai_council_contract_v1.json`
   - `contracts/improvement_proposal_v1.json`
   - `docs/canonical/MASTER_DIRECTIVE_v1.md`
   - `config/agent_registry.yaml`
   - `config/cognitive_principles.yaml`
   - `config/paths.py`
2. **Database Integrity:**
   - `data/e01_discovery.sqlite` (`PRAGMA integrity_check = ok`)
   - `data/paper_trading.sqlite` (`PRAGMA integrity_check = ok`)
   - `data/ahos_local.sqlite` (`PRAGMA integrity_check = ok`)
   - `data/ahos_knowledge.sqlite` (`PRAGMA integrity_check = ok`)
3. **Package Dependencies:**
   - `pytest`, `yaml` (PyYAML), `anyio`

---

## 3. Output Contract: `reports/health_report.json`
```json
{
  "timestamp_utc": "2026-08-16T07:37:27.600451+00:00",
  "overall_status": "GREEN",
  "total_issues": 0,
  "issues": [],
  "system_metrics": {
    "databases_checked": 4,
    "files_checked": 7,
    "packages_checked": 3,
    "python_version": "3.13.14",
    "platform": "windows"
  }
}
```

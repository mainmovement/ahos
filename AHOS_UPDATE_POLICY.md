# AHOS Update Governance & Version Policy

## 1. Immutable Update Laws
AHOS enforces strict safeguards against uncontrolled automated mutation:
1. **NEVER download code automatically:** No background agent may pull or apply unvetted git commits.
2. **NEVER modify architecture automatically:** Subsystem boundaries and schemas require explicit human governance approval.
3. **NEVER modify databases silently:** Historical observations, paper trades, and experiment records are append-only.
4. **NEVER upgrade dependencies without approval:** Package version bumps must pass the full 14-stage `improvement_proposal_v1` workflow.

---

## 2. Update Modes (`engine/update_manager.py`)
- **CHECK_ONLY Mode (Default):**
  Audits repository state, checks Master Directive hash integrity (`e2457c0d...`), and verifies schema versions without modifying files.
  ```bash
  python engine/update_manager.py --check-only
  ```
- **APPROVAL_REQUIRED Mode:**
  Requires explicit human approver identification and confirmation flag (`--confirm`).
  ```bash
  python engine/update_manager.py --apply --approver "lead_architect_human" --confirm
  ```

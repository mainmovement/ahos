# Self-research findings (development process)

Weakness discovery is a success condition. These are not closed.

| ID | Finding | Class |
|----|---------|-------|
| SR-001 | Cloud checkout has no Windows soak sqlite; treating `data/*.sqlite` here as T0 would fabricate soak evidence | DATA_LIMITATION |
| SR-002 | `eligible_join_pairs_estimate=0` in owner T0 snapshot — calibration cannot advance from that snapshot | WEAKNESS |
| SR-003 | `config/agent_registry.yaml` names 25 “agents”; most are libs/docs/MISSING — not a cognitive society | ARCHITECTURAL_LIMITATION |
| SR-004 | `contracts/ai_council_contract_v1.json` has no `members[]` roster | CONTRADICTION vs naive “council members” reading |
| SR-005 | Two hypothesis stores: cognitive JSONL lifecycle vs `duck_store` financial metrics — must not be silently unified | ARCHITECTURAL_LIMITATION |
| SR-006 | `docs/NEXT_DEVELOPMENT_BACKLOG.md` defers autonomous evolution while Charter sets AGI/ACI direction | CONTRADICTION (resolved by ADR-ACI-001, not by overwrite) |
| SR-007 | System Python in this Cloud image has no pytest (PEP 668) | ENVIRONMENT_LIMITATION |
| SR-008 | M-GAP-003 remains OPEN; 72h soak ≠ 7-day soak | WEAKNESS (operational) |
| SR-009 | No causal world model; observations are not a knowledge graph | MISSING_CAPABILITY |
| SR-010 | Cursor skills are developer instructions, not runtime agents | PROVIDER/TOOL LIMITATION (category mix-up) |

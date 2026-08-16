# AHOS — AGENT MAPPING FINAL
# Two-layer model (frozen): 10 system AGENTS (runtime actors) × 15 expert ROLES (review function).
# The 15 expert roles never bypass the 10-agent chain; they REVIEW its outputs per MULTI AGENT REVIEW RULE.

## Runtime agents (frozen — Phase-1 lock)
| Agent | Group | Duty (single responsibility) |
|---|---|---|
| AGENT-01 DataFetch | DATA | CCXT/LBank ingest, chunk loops, source tagging |
| AGENT-02 StrategyEngine | DATA | frozen-rule evaluation; NEVER self-modifies |
| AGENT-03 Execution | EXEC | order lifecycle; only PAPER until gates pass |
| AGENT-04 Security | EXEC | secrets, auth, kill switch, min-permission keys |
| AGENT-05 Telegram | COMMS | alerts + human-gate channel (admin-gated) |
| AGENT-06 Report | COMMS | reports, scorecards, audit surfacing |
| AGENT-07 LeadEngineer | SUPERVISORY | architecture, regression, failure analysis |
| AGENT-08 RiskManager | SUPERVISORY | sizing, leverage caps, daily-loss & DD halts |
| AGENT-09 QualityAssurance | SUPERVISORY | data gates, backtest/OOS/WF/MC, test suites |
| AGENT-10 FinalAuditor | AUDIT | veto power; final approval; rollback sign-off |

## 15-expert review panel → agent mapping
| # | Expert role (directive v2.0 list) | Maps to | Review duty |
|---|---|---|---|
| 1 | Chief Architect | AGENT-07 | architecture decisions, phase-map integrity |
| 2 | AI Systems Engineer | AGENT-02/07 | evolution-layer design (offline, gated) |
| 3 | Python Engineer | AGENT-01/02/03 code | engine correctness, no-look-ahead, determinism |
| 4 | Quant Researcher | AGENT-02/09 | strategy hypothesis design & edge hunting |
| 5 | Crypto Data Engineer | AGENT-01 | source attribution, integrity gates, chunk loops |
| 6 | Backtesting Specialist | AGENT-09 | OOS/WF/MC methodology, cost model realism |
| 7 | Statistics Expert | AGENT-09 | sample sufficiency, regime splits, significance testing |
| 8 | Risk Manager | AGENT-08 | cap math, DD halts, micro-capital guard |
| 9 | n8n Workflow Engineer | workflows 01–03 | node wiring, error branches, import checks |
| 10 | PostgreSQL DBA | database/ schema | constraints, indexes, dedupe keys |
| 11 | DevOps Docker Engineer | deployment/ | compose health, restart/recovery, backups |
| 12 | Cyber Security Engineer | AGENT-04 | secret hygiene, auth paths, key scoping |
| 13 | QA Engineer | AGENT-09 | pytest, dry-run, harness, regression gate |
| 14 | Auditor | AGENT-10 | contradictions register, status-letter enforcement |
| 15 | Product Manager | — (human-facing) | requirement traceability, honest status to user |

## Escalation chain (binding)
Producer (any builder agent) → Critic (Quant/Backtest) → Security (AGENT-04) → QA (AGENT-09) → Auditor (AGENT-10).
Disagreement unresolved ⇒ artifact stays "candidate", never "final". Human Gate is above AGENT-10 for LIVE only.

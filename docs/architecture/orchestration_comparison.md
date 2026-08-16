# AHOS — ORCHESTRATION DECISION: n8n vs Temporal vs Python-native (evidence-based)
2026-08-13 · W10 §17 / W11 §5 · Verdict at bottom. Environment facts: sandbox has NO Docker/host
(verified repeatedly); current runtime = cron-triggered Python; 24 agents; ~30s cycles; $0 law.

## Criteria matrix (1 = poor … 5 = strong), with evidence notes
| Criterion | n8n (current external layer) | Temporal | Python-native control plane |
|---|---|---|---|
| Durability of execution | 2 — workflow state in PG; replay semantics not byte-pinned | 5 — event-sourced workflow histories | 3 — append-only sqlite ledger (implemented today, trigger-pinned) |
| Retries | 3 — per-node retry config | 5 — first-class activity retries/policies | 3 — explicit failure_policy in registry (implemented) |
| Long-running workflows | 3 | 5 | 2 — processes die with host; cycles are short today |
| State recovery | 2 | 5 — resume from history | 3 — ledger resume implemented + tested (W11) |
| Idempotency | 2 — manual | 4 — workflow ids | 4 — idempotency keys implemented + tested (W11) |
| Observability | 3 — UI runs | 4 — Web UI + metrics | 2 — reports/ledger today; OTel target |
| Operational complexity | 3 — one container | 2 — server + workers + DB + SDK | 5 — stdlib only |
| Local deployment here | 0 — no host (BLOCKED) | 0 — no host (BLOCKED) | 5 — runs NOW (this suite) |
| VPS requirements | 1 container | PG + temporal server + workers | none beyond cron |
| Cost | $0 self-host | $0 self-host (infra cost) | $0 |
| Learning curve | already used (W7) | new subsystem to learn | none |
| Suitability for 24+ agents | 2 — not a brain | 5 — designed for this | 3 — sufficient at current scale |
| Failure recovery | 2 | 5 | 3 (ledger + checkpoints) |
| Lane-A contamination risk | low (external edge) | medium if misused | none today |

## Verdict
- **Temporal: RECOMMEND-AS-TARGET, DEFER-INSTALL.** It is the correct long-term durable-workflow
  owner (W11 §5 architecture stands), and W11 resolves the W10 tension explicitly: it is adopted
  as the TARGET and rejected as a TODAY install — the sandbox has no host, $0 law applies, and
  adopting it now would be precisely the "premature infrastructure" both directives forbid.
  Gate for adoption: host exists (VPS/Docker) + contracts stable (they are: control_plane_contract_v1
  phases map 1:1 onto workflow steps) + a Temporal migration replay test battery.
- **Python-native control plane: ADOPT-NOW (interim runtime).** It implements the full lifecycle
  semantics in-repo (one-start, halt/degrade, resume, idempotency, locks, ledger) with tests —
  so Temporal later is a SLOT-IN (the engine's phase handlers become Temporal activities).
- **n8n: KEEP as external automation/IO edge only** (Telegram, webhooks, notifications, human
  controls, admin triggers). It is explicitly NOT the AHOS brain and never becomes one (W11 §18).

## Anti-SPOF note (W11 §24)
Temporal must not become a hidden single point of failure: if Temporal is DOWN and Lane-A
deterministic core is healthy, system runs SYSTEM_DEGRADED with Python-native fallback cycles —
exactly what control_plane_component classes encode (temporal = NON_CRITICAL, fallback documented).

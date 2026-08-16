# H. 15-AGENT COUNCIL EXECUTION MODEL — Mission v1.1 §14 — 2026-08-11
# Roster: docs/COUNCIL_15_DESIGN.md (unchanged). THIS doc = how the council actually executes work.
# Anti-superficiality rule: each role has concrete decision rights + measurable outputs, not prompts.

## 1. Operating loop (per work item)
```
INTAKE (item: hypothesis/feature/design/bug)
 → OWNER role produces artifact (code/doc/measurement)
 → CRITIC (role 15) attacks: defects, overclaims, doctrine violations
 → QUANT (2/10/11) IF anything numeric: stats soundness, leakage, multiplicity
 → SECURITY (7/14) IF external data/auth/exec surface: veto rules, adversarial fixtures
 → ARCHITECT (1/13) layer boundaries + schema compatibility
 → QA (15): CI evidence linked; letters updated
 → AUDITOR (rotating ≠ producer): final consistency pass; disagreements logged
Resolution: PROCEED (recorded) / REVISE (loop) / REJECT (recorded)
Unresolved after 2 loops ⇒ artifact marked CANDIDATE, never FINAL (wave-3/4 law, kept)
```

## 2. Decision-rights matrix (who may approve what)
| Decision | Proposes | Must-review | Final gate |
|---|---|---|---|
| New feature definition (D-registry) | 2 Quant | 11 Backtest, 10 Stats, 15 QA | 10 (leakage/multiplicity) |
| New provider adapter | 8 DataEng | 14 Security, 1 Architect | 14 (ToS + hygiene) |
| Hard-veto registry change | 7 ContractSec | 14, 15 | 14 |
| Score promotion to user-visible | 2 | 10, 11, 15, Auditor | unanimous + research gate |
| n8n workflow change | 12 | 1, 15 | 15 via CI+import |
| Schema migration (v1.2+) | 13 | 1, 8 | 1 (additive-only rule) |
| Persian UX text change | 9(advisory)+3 | 15 tone rules | Auditor (no-certainty-language) |
| Live-execution anything | — | — | BLOCKED (law; human + evidence only) |

## 3. Multi-model usage (Mission §15)
External models (ChatGPT/Claude/Gemini/local) = reviewer/opinion TEXT inputs when the user supplies them.
They never write to the repo, never set numbers, never count as verification. Council-of-record = this
workspace: artifacts + CI + logged disagreements. (Current session: 15 roles enacted in-session per
AGENT_MAPPING.md; external opinions optional, not required — cost-zero compliance.)

## 4. Standing metrics the council answers to
- Fabrication incidents: must be 0 · Silent-failure incidents: must be 0
- UNKNOWN-discipline violations in tests: 0 · Gate-bypass attempts in history: 0
- Feature leakage tests: green · Provenance coverage: 100% of persisted discovery rows
- CI: 6-stage green before any delivery claim.

## 5. Wave-5 review record (this directive's A–J docs)
Producer: Architect+DataEng · Critic: QA (3 objections recorded→resolved: ①snapshot tolerance windows
needed exactness→F§2 fixed; ②Solana address lowercasing unsafe→C§1 chain-aware rule; ③coverage formula
ambiguous→D§3 explicit) · Quant: approved D-grid pre-registration, demanded availability_ts CHECK (added L3)
· Security: demanded single-provider confidence cap + veto-fixture label law (E§4/§5) · Auditor: PASS with
notes (all A–J letters consistent; Iran columns honestly UNKNOWN).

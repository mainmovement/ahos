# Planned 19-agent map (blueprint)

```text
DOCUMENT_ID      = PLANNED_19_AGENT_MAP
VERSION          = 0.1.0
STATUS           = PLANNED
IMMUTABLE        = NO
SEEDED_IN_CODE   = NO
MISSIONS_FINAL   = NO
```

This map is **not** the Slice 1 canonical registry. Compatibility: [AGENT_REGISTRY_MODEL.md](../governance/AGENT_REGISTRY_MODEL.md).

Do **not** issue full mission charters here. Fields only:

```text
AGENT_ID
PROVISIONAL_NAME
PROVISIONAL_ROLE
STATUS = PLANNED
```

`AGENT_ID` uses documentary namespace `agent.org.*` to avoid colliding with Slice 1 `agent.*` canonical ids.

---

## Registry (provisional)

| AGENT_ID | PROVISIONAL_NAME | PROVISIONAL_ROLE | STATUS |
| --- | --- | --- | --- |
| `agent.org.01-chief-architect` | Chief Architect | Organizational / system architecture leadership (documentary) | PLANNED |
| `agent.org.02-systems-architect` | Systems Architect | Systems structure and interfaces | PLANNED |
| `agent.org.03-security-architect` | Security Architect | Security architecture review (not a sandbox) | PLANNED |
| `agent.org.04-governance-constitution` | Governance & Constitution | Governance text and protocol consistency | PLANNED |
| `agent.org.05-epistemic-reasoning` | Epistemic Reasoning | Evidence/claim/hypothesis discipline | PLANNED |
| `agent.org.06-research-methodology` | Research Methodology | Method and study design | PLANNED |
| `agent.org.07-data-intelligence` | Data Intelligence | Data quality and schema reasoning | PLANNED |
| `agent.org.08-crypto-market-intelligence` | Crypto Market Intelligence | Market structure research (no live trade) | PLANNED |
| `agent.org.09-on-chain-intelligence` | On-Chain Intelligence | On-chain research (no production connectors) | PLANNED |
| `agent.org.10-token-security-scam-intelligence` | Token Security / Scam Intelligence | Token/scam analysis (no credential use) | PLANNED |
| `agent.org.11-risk-intelligence` | Risk Intelligence | Risk identification and framing | PLANNED |
| `agent.org.12-quant-backtesting` | Quant / Backtesting | Quant research design (no silent prod scoring) | PLANNED |
| `agent.org.13-ai-ml-intelligence` | AI / ML Intelligence | Model/eval research (no training runtime claimed) | PLANNED |
| `agent.org.14-agent-runtime-engineering` | Agent Runtime Engineering | Org runtime engineering (this repo) | PLANNED |
| `agent.org.15-prompt-instruction-engineering` | Prompt & Instruction Engineering | Instruction/charter engineering | PLANNED |
| `agent.org.16-qa-verification` | QA / Verification | Independent verification design | PLANNED |
| `agent.org.17-product-ux-intelligence` | Product / UX Intelligence | Product/UX research | PLANNED |
| `agent.org.18-frontend-visualization` | Frontend / Visualization | Frontend/visualization design | PLANNED |
| `agent.org.19-independent-red-team` | Independent Red Team | Adversarial review of org claims | PLANNED |

---

## ROLE_OVERLAP (not silently merged)

```text
ROLE_OVERLAP
  01 vs 02 vs 14 — architecture / runtime may duplicate “how the system is built”
  03 vs 10 — both “security”; application vs token/scam
  04 vs Slice 1 release-governance-reviewer / this Constitution authorship
  05 vs 06 — epistemic vs methodology boundary is thin
  08 vs 09 vs 11 vs 12 — market / chain / risk / quant may duplicate datasets
  16 vs 19 — QA vs red team both attack claims
  17 vs 18 — product/UX vs frontend
  01 vs Slice 1 chief-orchestrator vs future Agent One — three “top” names
```

```text
ROLE_GAP
  Slice 1 paper-trading, calibration, scoring-science, windows-runtime, integration,
  provider-data, identity, evidence-transport have no 1:1 blueprint row
  RESEARCH_ANALYST_AGENT is implemented but not in this map
  No dedicated “human operator” agent (correct — humans are not agents)
```

```text
POSSIBLE_MERGE   = 01+02 ; 17+18 ; 16+19 (QA+red-team) — NOT APPROVED
POSSIBLE_SPLIT   = 03 vs 10 already split; keep until L2
DEPENDENCY       = 04,05,16,19 should exist before operationalizing 08–13
                 14 depends on Slice 2B/research host reality
                 01 must not become Agent One
```

Human approval required to change this table’s membership.

---

## Explicit non-claims

- Not operational
- Not Agent One
- Not a replacement of `CANONICAL_AGENT_IDS`
- Not a grant of capabilities

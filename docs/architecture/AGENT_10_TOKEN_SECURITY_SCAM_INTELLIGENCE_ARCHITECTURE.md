# Agent Organization Token Security / Scam Intelligence Architecture

```text
DOCUMENT_ID      = AGENT_10_TOKEN_SECURITY_SCAM_INTELLIGENCE_ARCHITECTURE
MISSION_ID       = TASK-20260914-010
VERSION          = 0.1.0
STATUS           = PROPOSED / READ_ONLY_TOKEN_SECURITY_SCAM_INTELLIGENCE_ARCHITECTURE
AUTHORITY        = NONE CREATED
RUNTIME_EFFECT   = NONE
AHOS_EFFECT      = NONE
AGENT_ID         = AGENT-10 (agent.org.10-token-security-scam-intelligence — documentary)
DIRECT_COMMANDER = MASTER ORCHESTRATOR
PARENT           = MASTER ORCHESTRATOR
DUAL_19          = UNRESOLVED
AGENT_ONE        = NOT_IMPLEMENTED / FUTURE_NON_AUTHORITY_ROOT
```

This document is a **design, architecture, and security-analysis artifact** produced by AGENT-10 under explicit activation for TASK-20260914-010. It does not implement token security runtime, adopt governance, grant authority, modify AHOS, connect blockchain providers, execute contracts, control wallets, scan live tokens, or promote knowledge. Facts cite repository evidence with explicit classification labels (`[IMPLEMENTED]`, `[DOCUMENTED]`, `[PROPOSED]`, `[UNKNOWN]`). Architectural recommendations are labeled `[PROPOSED]`.

**Critical honesty constraint:**

```text
SECURITY SIGNAL              ≠ SECURITY PROOF
SECURITY FINDING             ≠ SCAM
UNKNOWN                      ≠ SAFE
NO DETECTED VULNERABILITY    ≠ SECURE
CONTRACT VERIFIED            ≠ PROJECT TRUSTWORTHY
RENOUNCED OWNERSHIP          ≠ SAFE
LIQUIDITY LOCKED             ≠ SAFE
AUDIT EXISTS                 ≠ SECURE
OPEN SOURCE                  ≠ SAFE
HIGH LIQUIDITY               ≠ LOW SECURITY RISK
MANY HOLDERS                 ≠ SAFE TOKEN
NO HONEYPOT FOUND            ≠ SAFE
SELL FAILED                  ≠ TOKEN IS A HONEYPOT
SIMULATION SUCCESS           ≠ REAL-WORLD EXECUTION SUCCESS
SIMULATION FAILURE           ≠ MALICIOUS CONTRACT
STATIC ANALYSIS              ≠ BEHAVIORAL PROOF
VERIFIED IMPLEMENTATION TODAY ≠ IMMUTABLE IMPLEMENTATION TOMORROW
NO CURRENT BLACKLIST         ≠ BLACKLIST IMPOSSIBLE
LOCKED LP                    ≠ IMMUTABLE ECONOMIC SAFETY
CLUSTER                      ≠ PROVEN COMMON OWNER
SAME CODE                    ≠ SAME INTENT
TOP HOLDER                   ≠ MALICIOUS (without evidence)
PRICE CRASH                  ≠ RUG PULL
LIQUIDITY DROP               ≠ MALICIOUS LIQUIDITY DRAIN
MULTIPLE SECURITY PROVIDERS  ≠ INDEPENDENT SECURITY PROOF
SECURITY SCORE               ≠ TRUTH
SECURITY SCORE               ≠ GUARANTEE
SECURITY ASSESSMENT          ≠ DECISION
SECURITY ASSESSMENT          ≠ EXECUTION AUTHORITY
SUSPICIOUS                   ↛ SCAM ↛ DANGER ↛ SELL (forbidden inference chain)
```

---

## 1. Executive Summary

`[VERIFIED]` The AHOS Agent Organization contains **no implemented Token Security / Scam Intelligence (TSI) layer** in code. There are no security-specific datatypes, honeypot simulators, privilege analyzers, static-analysis adapters, security provider registries, or scam classifiers in `ahos_org/`, `agent_org/`, or `research_worker/`. TSI today exists only as a **planned specialist role** (`agent.org.10-token-security-scam-intelligence`, `[PLANNED]`) in `PLANNED_19_AGENT_MAP.md`.

`[VERIFIED]` Foundational **upstream dependencies are partially documented** by peer architecture missions: Agent-03 (organizational security; explicitly distinguishes infra security from token/scam domain §9.2), Agent-05 (epistemic ladder), Agent-06 (research methodology, falsification design), Agent-07 (data quality, provider independence, semantic failures), Agent-08 (market boundary; security can invalidate actionability §35), Agent-09 (on-chain observations; Agent 10 owns SAFE/SCAM boundary §44). Slice 2B (`agent_org/epistemic.py`, `[IMPLEMENTED]` `[TESTED]`) provides generic `Observation`, `Evidence`, `Hypothesis`, and `ContradictionCase` types — not token-security domain semantics.

`[VERIFIED]` Slice 1 contains logical role `agent.security` with capabilities `security.inspect`, `policy.inspect`, `audit.read` (`ahos_org/registry.py`, `[IMPLEMENTED]`). This role covers **organizational/infrastructure security review**, not token contract analysis. Global deny policy blocks `provider.connect`, `trading.live`, credentials, and AHOS production access (`ahos_org/policy.py`, `[IMPLEMENTED]` `[TESTED]`).

`[VERIFIED]` `[INSPECTED_ONLY / NO_MODIFICATION]` AHOS sibling repository (`G:\robat\ahos`) contains **product-level** security signals (`SecuritySignals`, honeypot flags, RugCheck/GoPlus adapters, sell simulation concepts in demo UI). These are **not** organizational TSI runtime and must not be silently adopted as org authority without human L2 integration decisions (extends Agent 07 HD-11, Agent 09 HD-16).

**Central architectural question:** Can the system determine, with explicit evidence and uncertainty, whether a token, contract, liquidity structure, ownership/control structure, trading mechanism, or observed behavior presents a meaningful security threat — and what can it **not** legitimately conclude?

**Primary TSI objective:** prevent **security authority collapse** — where suspicious signals, provider labels, simulation results, static-analysis warnings, liquidity metrics, or honeypot heuristics silently become SCAM verdicts, DANGER classifications, SELL triggers, or execution authority.

**Current TSI posture:** `[DOCUMENTED]` blueprint only; `[PROPOSED]` peer boundaries from Agents 03–09; `[IMPLEMENTED]` generic epistemic and deny-policy substrate. **No token security intelligence runtime.**

**Dual-19 status:** `[VERIFIED]` `[CONFLICT / UNRESOLVED]` — Plane A (`agent.security`) and Plane D (`agent.org.10-token-security-scam-intelligence`) remain separate taxonomies. Agent 03 vs Agent 10 domain split is documented but not runtime-enforced.

**Agent One:** `NOT_IMPLEMENTED / FUTURE_NON_AUTHORITY_ROOT` — must never become security truth root or execution authority.

**AHOS:** `INSPECTED_ONLY` / `NO_MODIFICATION` / `AHOS_IMPACT = NONE`.

---

## 2. Mission Scope

### 2.1 In scope (TASK-20260914-010)

- Repository forensics and architecture design for Token Security / Scam Intelligence
- Formal distinction: security vulnerability vs scam vs risk vs decision
- Threat taxonomy, observation model, epistemic states, evidence hierarchy
- Honeypot, simulation, static/dynamic analysis, proxy/upgrade, privilege models
- Boundary definitions with Agents 03–09 and future 11–13, 16, 19
- Required object model (conceptual), matrices (A–J), contradiction analysis, human decisions

### 2.2 Out of scope (explicit prohibitions)

- AHOS modification; Lane A/B modification; live token scanning; RPC/explorer connections
- Contract execution; wallet control; signing; buy/sell/approve/mint/burn
- Runtime service implementation; honeypot execution; provider adapters
- Agent activation or creation; governance adoption; commits or pushes
- Resolving Dual-19; granting Agent 10 decision or execution authority
- Collapsing SUSPICIOUS → SCAM → DANGER → SELL automatically

---

## 3. Identity and Lifecycle

### 3.1 Agent-10 identity

| Field | Value |
| --- | --- |
| `AGENT_ID` (mission) | `AGENT-10` |
| Blueprint ID | `agent.org.10-token-security-scam-intelligence` |
| Provisional name | Token Security / Scam Intelligence Architect |
| Role | Design token security architecture: threat taxonomy, evidence discipline, honeypot/simulation models, cross-domain security composition |
| Authority class | `NONE` (design mission only) |
| Capabilities exercised | READ, ANALYZE, PROPOSE (documentation) |
| Forbidden | VERIFY (own conclusions), PROMOTE, EXECUTE, MODIFY runtime, CONNECT providers, CONTROL wallets, SIGN transactions, ACTIVATE other agents, emit BUY/SELL, declare tokens safe for trading without epistemic/risk gates |
| Supervisor | MASTER ORCHESTRATOR → human operator (MEHRDAD) |
| Source of truth | **Not** AGENT-10. Repository L0/L1 + governance L2/L3 only. |

AGENT-10 is **not** Agent One, **not** the Master Orchestrator, **not** Agent 03 (organizational security), **not** Agent 09 (on-chain observation producer), **not** Agent 11 (risk quantification), **not** Agent 05 (epistemic promotion), and **not** authorized to convert security assessments into decisions or execution.

### 3.2 Command chain

```text
MEHRDAD
  → MASTER ORCHESTRATOR
    → AGENT-10 (this mission)
```

- Direct commander: **MASTER ORCHESTRATOR**
- No subordinate agents created or activated
- Peer specialists (03–09, future 11–19) are not commanders

### 3.3 Lifecycle

```text
ACTIVATION_REQUESTED → AUTHORIZED → ACTIVE
  (TASK-20260914-010)
  → COMPLETED (this deliverable)
  → IDLE / DORMANT / WAITING_FOR_NEW_COMMAND
```

Recommendations in this document are **not** commands. AGENT-10 does not auto-continue to Agent 11 or any future mission.

---

## 4. Repository Findings

### 4.1 Implementation inventory (`ahos-agent-org`)

| Component | Path | TSI relevance | Status |
| --- | --- | --- | --- |
| Planned Agent 10 | `docs/agents/PLANNED_19_AGENT_MAP.md` | Blueprint row; 03 vs 10 overlap noted | `[PLANNED]` |
| Org security architecture | `docs/architecture/AGENT_ORGANIZATION_SECURITY_ARCHITECTURE.md` | Agent 10 sandboxed fetch note §9.2 | `[DOCUMENTED]` |
| OCI architecture | `docs/architecture/AGENT_09_ON_CHAIN_INTELLIGENCE_ARCHITECTURE.md` | §44 security boundary; honeypot traces | `[DOCUMENTED]` |
| CMI architecture | `docs/architecture/AGENT_08_CRYPTO_MARKET_INTELLIGENCE_ARCHITECTURE.md` | §35 security referral; conflict model | `[DOCUMENTED]` |
| Data intelligence | `docs/architecture/AGENT_07_DATA_INTELLIGENCE_ARCHITECTURE.md` | Provider independence; semantic failures | `[DOCUMENTED]` |
| Epistemic core | `agent_org/epistemic.py` | Generic Observation/Evidence/Hypothesis | `[IMPLEMENTED]` no TSI domain |
| Slice 1 `agent.security` | `ahos_org/registry.py` | Infra security role; not token analysis | `[IMPLEMENTED]` logical only |
| Global deny policy | `ahos_org/policy.py` | Blocks provider.connect, trading.live | `[IMPLEMENTED]` `[TESTED]` |
| Research analyst | `research_worker/analyst.py` | Label discipline; no security analysis | `[IMPLEMENTED]` Class A only |

**Conclusion:** `[VERIFIED]` Zero TSI runtime artifacts. All security-token semantics are documentary or external (AHOS product, not org authority).

### 4.2 AHOS boundary (`INSPECTED_ONLY`)

| AHOS artifact | Relevance | Org adoption |
| --- | --- | --- |
| `types.py` — `honeypot: YES/NO/UNKNOWN` | Product security signal shape | `[PROPOSED]` mediated mirror only; HD-20 |
| `GoPlusSecurityAdapter`, `RugCheckSecurityAdapter` | External security providers | Not org-connected; provider independence applies |
| Demo UI honeypot simulation narratives | UX concept | Not evidentiary proof |
| Security heuristics in seed data | Illustrative | Must not become org ground truth |

**Rule:** AHOS security outputs are **L0 product observations** of a separate system. Agent 10 architecture may **align conceptually** but adoption requires explicit human L2 integration — not silent merge.

### 4.3 What TSI must answer vs must not answer

| TSI may architect answers to | TSI must not auto-answer |
| --- | --- |
| What privileged capabilities exist? | "Should we buy?" |
| What security-relevant behaviors were observed? | "This is definitely a scam" (without hypothesis ladder) |
| What hypotheses explain sell failure? | "Sell now" |
| What evidence supports/contradicts honeypot hypothesis? | "Safe to trade" from absence of findings |
| What is UNKNOWN and why? | Override Agent 09 on-chain facts |
| What conflicts exist across security dimensions? | Promote to Knowledge without Agent 05 |

---

## 5. Security Definition

**Token Security Intelligence (TSI)** is the architectural domain responsible for interpreting blockchain-derived and security-provider-derived information about tokens, contracts, liquidity structures, trading mechanisms, and related behaviors **from a threat and capability perspective**, while preserving explicit uncertainty, evidence grade, and forbidden inference chains.

TSI is **not**:

- Organizational infrastructure security (Agent 03)
- Raw on-chain observation production (Agent 09)
- Market price/volume interpretation (Agent 08)
- Data quality validation alone (Agent 07)
- Epistemic promotion (Agent 05)
- Risk quantification and exposure framing (Agent 11)
- Trading or execution (denied globally)

**Scam Intelligence** is a **subset** of TSI focused on **patterns consistent with fraudulent intent or deceptive economic traps**, expressed only through explicit **ScamIndicator** and **ScamHypothesis** objects — never as raw observation labels.

---

## 6. Security Principles

| # | Principle | Rationale |
| --- | --- | --- |
| 1 | Security signal ≠ security proof | Prevents heuristic laundering |
| 2 | Security finding ≠ scam | Technical weakness ≠ malicious intent |
| 3 | Unknown ≠ safe | Absence of detection ≠ absence of threat |
| 4 | No detected vulnerability ≠ secure | Incomplete coverage is normal |
| 5 | Point-in-time assessments expire | Privileges and taxes change |
| 6 | Never collapse dimensions into one score without published justification | Prevents authority collapse |
| 7 | Preserve conflicts explicitly | Do not average CODE=LOW with LIQUIDITY=HIGH |
| 8 | Downstream inherits upstream uncertainty | Stale OCI → stale security |
| 9 | Provider disagreement is data, not resolution by vote | Methodology must be preserved |
| 10 | Simulation ≠ execution | Environment and state matter |
| 11 | Static analysis ≠ behavioral proof | Code path may be unreachable |
| 12 | Intent is speculation unless evidenced | Ownership ≠ malice |
| 13 | Scam hypothesis requires falsification criteria | Agent 06 alignment |
| 14 | Security assessment has zero decision authority | Handoff to risk/epistemic/human |
| 15 | Quarantine is explicit, auditable, expiring | No silent blocks |
| 16 | Historical claims require point-in-time evidence | No retroactive "obvious scam" |
| 17 | EVM semantics ≠ universal chain semantics | Solana mint/freeze/update authority |
| 18 | Labels from providers are indirect evidence | Not direct proof |
| 19 | Red-team and false-positive categories are first-class | Fail closed on ambiguity |
| 20 | SUSPICIOUS ↛ SCAM ↛ DANGER ↛ SELL | Forbidden chain |

Evaluated against Constitution §3.2 safety inequalities: **aligned** at documentation level; **not runtime-enforced** for TSI.

---

## 7. Security vs Scam

Formal non-collapse taxonomy:

| Category | Definition | Example | Auto-promotion forbidden |
| --- | --- | --- | --- |
| **Security Vulnerability** | Technical weakness exploitable or abusable | Unprotected `mint()` | → scam |
| **Security Weakness** | Suboptimal but not necessarily exploitable | Centralized admin without timelock | → malicious intent |
| **Security Risk** | Potential harm given exposure and conditions | Upgradeable proxy + active trading | → decision |
| **Malicious Capability** | Contract **can** perform harmful action | Owner can set 99% sell tax | → scam (capability ≠ intent) |
| **Malicious Behavior** | Observed action consistent with harm | LP removed 95% in one tx | → rug verdict without hypothesis |
| **Scam Indicator** | Pattern associated with scams in corpus | Buy succeeds, sell reverts for test wallet | → "honeypot confirmed" |
| **Scam Hypothesis** | Testable claim of fraudulent design/intent | "Token selectively blocks sells for non-exempt addresses" | → knowledge |
| **Scam Assessment** | Synthesized judgment with evidence map, conflicts, UNKNOWNs | "Honeypot hypothesis SUPPORTED for path P; REFUTED for path Q" | → SELL |

**Rules:**

- A technically vulnerable contract does not automatically prove malicious intent.
- A sophisticated scam may have technically valid, audited code.
- A safe-looking contract may belong to a malicious off-chain project.
- **Scam** language is reserved for **ScamHypothesis** and **ScamAssessment** lifecycle states ≥ `SUPPORTED`, never for raw observations.

---

## 8. Threat Taxonomy

### A. Exit Scams

| Threat | Observable signals | Verification vectors |
| --- | --- | --- |
| Liquidity drain | Large LP removal | OCI LP events + lock state + timing |
| LP removal | `removeLiquidity` success | Pool balance delta, authority |
| Treasury drain | Treasury outflows | Wallet graph, privileged calls |
| Privileged withdrawal | Owner withdraw functions | Static + dynamic privilege tests |
| Migration trap | New pool, old LP abandoned | Factory lineage, user routing |

### B. Honeypots

| Threat | Observable signals | Verification vectors |
| --- | --- | --- |
| Cannot sell | Sell sim revert | Multi-address governed simulation |
| Selective sell restriction | Sell succeeds for exempt only | Caller matrix tests |
| Address-based sell blocking | Blacklist hit on sell path | Blacklist state + sim |
| Tax-based effective sell blocking | 90%+ sell tax | Tax read + net output calc |
| Dynamic restrictions | Tax/rules change pre-sell | State transition monitoring |

### C. Rug Pulls

| Threat | Observable signals | Verification vectors |
| --- | --- | --- |
| Ownership abuse | Renounce then reclaim via proxy | Proxy admin trace |
| Liquidity removal | See exit scams | |
| Mint abuse | Supply spike | Mint events + authority |
| Treasury abuse | Dev wallet dumps | Holder analysis |
| Upgrade abuse | Implementation swap | Proxy events |

### D. Contract Privilege Abuse

Hidden admins, role escalation, proxy admin, timelock bypass — see §22 Privilege Model.

### E. Supply Manipulation

Hidden mint, rebasing abuse, balance manipulation, confiscation, freeze — see §25.

### F. Trading Manipulation

Fake liquidity, fake volume, wash trading — **Agent 08/09 observe**; TSI interprets security relevance only.

### G. Identity / Impersonation

Fake token, fake contract, clone project — coordinate with Agent 09 identity resolution.

### H. Infrastructure / Dependency

Oracle manipulation, bridge dependency, compromised library — see §31 Dependencies.

---

## 9. Observation Model

```text
Raw Security Observation (provider/RPC/simulator output)
        ↓  normalize: schema, chain, contract, timestamp, source version
Normalized Security Observation
        ↓  interpret: capability / behavior / mismatch
Security Finding (typed, bounded claim about one dimension)
        ↓  explain: competing causes, required tests
Security Hypothesis (falsifiable)
        ↓  governed verification (future runtime)
Verification Record (PASS/FAIL/INCONCLUSIVE + conditions)
        ↓  synthesize with conflicts and UNKNOWNs
Security Assessment (multi-dimensional, non-authoritative)
        ↓  Agent 05 epistemic evaluation
Evidence Candidate (not automatic Knowledge)
```

**Every transition must preserve:** source, timestamp, chain, token/contract identity, provenance, evidence refs, uncertainty, confidence (bounded), schema version, lifecycle status.

**Forbidden transitions:**

- NormalizedObservation → ScamAssessment (skip finding/hypothesis)
- SecurityFinding → EXECUTE or SELL
- ProviderLabel → Direct Evidence
- SimulationFailure → Scam (without hypothesis)

---

## 10. Epistemic States

Security-specific lifecycle states (mapped to but not silently merged with Slice 2B enums — HD-04):

| State | Meaning | Allowed transitions |
| --- | --- | --- |
| `UNKNOWN` | Insufficient data or undecodable semantics | → OBSERVED when data arrives |
| `OBSERVED` | Raw/normalized observation recorded | → SUSPICIOUS, ANOMALOUS, or remain OBSERVED |
| `SUSPICIOUS` | Pattern warrants investigation | → HYPOTHESIZED; **not** → SCAM |
| `ANOMALOUS` | Deviation from baseline; cause unclear | → HYPOTHESIZED |
| `HYPOTHESIZED` | Testable explanation proposed | → SUPPORTED, REFUTED, INCONCLUSIVE |
| `SUPPORTED` | Evidence meets predefined support threshold | → VERIFIED (independent verification) |
| `CONTRADICTED` | Strong counter-evidence exists | → REFUTED or CONFLICT |
| `VERIFIED` | Independent verification passed | → may supersede; not permanent |
| `REFUTED` | Falsification condition met | → SUPERSEDED if new tests |
| `STALE` | Underlying state or evidence expired | Re-assess required |
| `SUPERSEDED` | Replaced by newer assessment | Historical read-only |

**Explicit prohibition:** No state machine edge labeled `SUSPICIOUS → SCAM` or `SUSPICIOUS → DANGER`.

---

## 11. Evidence Hierarchy

| Tier | Examples | Reliability | Limitations |
| --- | --- | --- | --- |
| **Direct** | Verified tx receipt, contract storage read, verified source match, ownership state at block B, successful governed simulation under declared conditions | Highest when pinned to block | Coverage gaps; sim ≠ mainnet execution |
| **Derived** | Static analysis result, decoded calldata, graph metric, simulation output | Medium-high with methodology | Decoder errors; unreachable paths |
| **Indirect** | Explorer labels, social reports, "audit badge", reputation scores | Low for security proof | Spoofing; marketing |
| **Speculation** | Deployer intent, future rug prediction, anonymous identity | Not evidentiary | Must be labeled; no promotion |

**Upgrade rules:** Indirect → Direct requires explicit warrant chain. Speculation never becomes Direct without new evidence tier.

**Forbidden:** Lower-grade information silently becoming higher-grade in SecurityAssessment summaries.

---

## 12. Data Quality

Agent 10 **inherits** Agent 07 limitations:

| Data condition | Security impact |
| --- | --- |
| `STALE CONTRACT STATE` | `STALE SECURITY ASSESSMENT` |
| `UNKNOWN DECODER` | `UNKNOWN SEMANTIC SECURITY` |
| `INCOMPLETE HOLDER DATA` | `LIMITED CONCENTRATION ASSESSMENT` |
| `PROVIDER OUTAGE` | `UNKNOWN` for provider-dependent findings |
| `SEM_WRONG_IDENTITY` | Quarantine token identity |
| `TMP_FUTURE_LEAKAGE` | Invalidate historical security claims |

`[PROPOSED]` Every SecurityAssessment carries `DataQualityInheritance` ref listing upstream `DataQualityAssessment` IDs and propagated gaps.

---

## 13. On-Chain Boundary (Agent 09)

| Agent 09 produces | Agent 10 consumes | Agent 10 must not |
| --- | --- | --- |
| Authority observations (mint/freeze/upgrade keys) | PrivilegeAssessment | Rewrite OCI block hashes or tx facts |
| Liquidity movement facts | LiquiditySecurityAssessment | Declare LP removal = rug without hypothesis |
| Revert traces | Honeypot investigation input | Change decoded event semantics |
| Holder distribution snapshots | Concentration analysis | Label whale as malicious |
| Contract deployment lineage | Clone/deployer analysis | Merge cluster → common owner |

Agent 09 §44: Agent 09 **must not** declare `SAFE` or `SCAM`. Agent 10 **must not** override Agent 09 observations — only interpret via security objects.

---

## 14. Market Boundary (Agent 08)

| Market observation (Agent 08) | TSI rule |
| --- | --- |
| `PRICE CRASH` | Not automatically `RUG PULL` |
| `LIQUIDITY DROP` | Not automatically `MALICIOUS DRAIN` |
| `VOLUME SPIKE` | Not wash trading proof |
| `MOMENTUM STRONG` | Not security clearance |

`[PROPOSED]` `MarketSecurityConflict` when CMI actionability and TSI threat hypotheses disagree (Agent 08 §35, §1446). Example: strong momentum + unknown sellability → **conflict**, not opportunity.

---

## 15. Epistemic Boundary (Agent 05)

Agent 10 produces: SecurityObservation, SecurityFinding, SecurityHypothesis, SecurityAssessment candidates.

Agent 10 **does not** independently promote to Knowledge. Agent 05 controls epistemic classification via TCB gates (D-01/D-04).

```text
SECURITY ASSESSMENT ≠ EVIDENCE ≠ KNOWLEDGE
```

Handoff schema: §41.

---

## 16. Research Boundary (Agent 06)

Every important security claim should define:

| Field | Example (honeypot) |
| --- | --- |
| `hypothesis` | Token is selectively unsellable for non-exempt addresses |
| `expected_observation` | Sell sim fails for test wallet A, succeeds for exempt B |
| `falsification_condition` | Sell succeeds for A under same block/state/route |
| `test` | Governed multi-address sell simulation matrix |
| `required_data` | Pinned block, router, slippage, gas, sim version |
| `temporal_window` | Assessment valid for block range [B0, B1] |
| `replication` | Independent sim provider or repeated runs ≥ N |

**Not executed in this mission.**

---

## 17. Honeypot Intelligence

### 17.1 Observation dimensions

| Dimension | Security relevance |
| --- | --- |
| Buy success | Necessary but not sufficient for "not honeypot" |
| Sell success | Failure has many causes |
| Transfer success | May differ from DEX sell path |
| Tax asymmetry | High sell vs low buy tax → finding, not verdict |
| Address restrictions | Blacklist/whitelist/modifiers |
| Trading-state deps | Trading disabled until condition |
| Dynamic fees | Change between buy and sell block |
| Gas traps | Out-of-gas on sell path only |
| Max tx/wallet traps | Sell amount blocked |
| Liquidity conditions | Pool too shallow → failed sell ≠ honeypot |
| Router dependencies | Path-specific failures |

### 17.2 Failure cause taxonomy (sell failed)

| Cause class | Distinguishing evidence |
| --- | --- |
| Honeypot/selective restriction | Sim matrix: fails generic, succeeds exempt |
| Excessive tax | Net output below threshold; tax read confirms |
| Insufficient liquidity | Pool reserves; slippage exceeded |
| Trading disabled | `tradingEnabled` false |
| Router incompatibility | Path A fails, path B succeeds |
| Blacklist | Revert reason / storage |
| Block/state mismatch | Different results at pinned vs latest |
| Simulation artifact | Sim version bug; provider error |
| Chain congestion / gas | Tx never included vs revert |

### 17.3 Forbidden inference

```text
SELL FAILED  →  TOKEN IS A HONEYPOT   [FORBIDDEN without hypothesis ladder]
BUY SUCCESS + SELL FAIL  →  SCAM       [FORBIDDEN — investigate first]
```

### 17.4 `[PROPOSED]` SellabilityAssessment object

Tracks: paths tested, callers, blocks, routes, revert reasons, tax net, liquidity depth, epistemic state, UNKNOWN causes.

---

## 18. Simulation Security

Conceptual governed simulation architecture (future):

| Simulation type | Purpose |
| --- | --- |
| Buy simulation | Entry path viability |
| Sell simulation | Exit path viability |
| Transfer simulation | Wallet-to-wallet |
| Approve / allowance | Approval traps |
| Contract-call simulation | Privileged fn probe |

**Required output fields:** block state pin, caller, calldata, gas limit, route, slippage params, revert reason, state deps, simulator version, provider id.

**Invariants:**

```text
SIMULATION SUCCESS  ≠  REAL-WORLD EXECUTION SUCCESS
SIMULATION FAILURE  ≠  MALICIOUS CONTRACT
```

Simulations are **Derived Evidence** tier. Mainnet MEV, private pools, and timing attacks may invalidate sim results.

---

## 19. Static Analysis

Conceptual layers:

| Layer | Output |
| --- | --- |
| Source inspection | Function inventory, modifiers |
| Bytecode analysis | Opcode patterns, proxies |
| Control-flow | Reachability |
| Privilege analysis | Role → function map |
| Proxy detection | EIP-1967 slots, beacon |
| Dangerous opcodes | `delegatecall`, `selfdestruct` |
| External calls | Untrusted call graph |
| Storage analysis | Collision risks |
| Upgrade analysis | Admin change paths |

**Invariant:** `STATIC ANALYSIS ≠ BEHAVIORAL PROOF`

Unreachable admin functions still matter as **Malicious Capability** findings.

---

## 20. Dynamic Analysis

Future governed dynamic analysis (not implemented):

- Transaction simulation at pinned blocks
- State transition tests (tax change, blacklist add)
- Multi-address privilege tests
- Edge-case: max uint transfer, zero address, contract recipient
- Time-dependent behavior monitoring

All dynamic results → SecurityFinding or Hypothesis input, not ScamAssessment directly.

---

## 21. Proxy / Upgrade Security

| Element | Security concern |
| --- | --- |
| Proxy detection | User may interact with proxy, not logic |
| Implementation address | Can change |
| Admin / upgrade authority | Who can swap logic |
| Timelock | Delay vs instant upgrade |
| Beacon / factory | Indirect upgrade paths |
| Initialization | Uninitialized proxy takeover |
| Implementation history | Past malicious logic |

**Critical:** `VERIFIED IMPLEMENTATION TODAY ≠ IMMUTABLE IMPLEMENTATION TOMORROW`

`[PROPOSED]` UpgradeabilityAssessment: tracks admin, timelock, implementation timeline, change events, STALE triggers on `Upgraded` event.

---

## 22. Ownership / Privileges

Privilege graph:

```text
OWNER / ADMIN / ROLE MANAGER
        ↓
ROLE (MINTER, PAUSER, UPGRADER, ...)
        ↓
FUNCTION (setTax, mint, blacklist, ...)
        ↓
STATE CHANGE (storage)
        ↓
ECONOMIC EFFECT (user can/cannot sell, supply change, ...)
```

Actors: owner, admin, multisig, timelock, DAO, deployer, upgrade authority, hidden role holders.

**Rule:** Do not infer intent from ownership alone. Centralization is a **Security Risk** finding, not a **Scam** label.

Solana: mint authority, freeze authority, update authority — separate from EVM `onlyOwner`.

---

## 23. Token Tax Intelligence

| Mechanism | Observable | Finding type |
| --- | --- | --- |
| Buy / sell / transfer tax | On-chain read or sim | Tax asymmetry finding |
| Dynamic tax | Change events | Time-dependent risk |
| Max tax cap | Contract constant | Capability bound |
| Tax setter | Privileged address | Centralization |
| Tax recipient | Flow to dev wallet | Economic extraction |
| Exemptions | Whitelist pays 0% | Selective honeypot vector |

**Detect:** `NORMAL BUY + ABNORMAL SELL TAX` as security-relevant finding.

**Do not:** automatically call it a scam.

---

## 24. Blacklist / Whitelist

| Observation | Implication |
| --- | --- |
| Blacklist exists | Malicious Capability |
| Blacklist authority | Privilege finding |
| No current blacklist | **Not** blacklist impossible |
| Whitelist exemptions | Honeypot test matrix required |
| Address-specific behavior | Document per-address SellabilityAssessment |

---

## 25. Mint / Burn / Supply Authority

| Mechanism | EVM | Solana (non-EVM) |
| --- | --- | --- |
| Mint authority | `mint()`, roles | Mint authority account |
| Burn | `burn()`, deflation | Burn instruction |
| Supply cap | `maxSupply` | Fixed supply mint |
| Hidden expansion | Hidden mint fn, proxy | Authority not revoked |
| Freeze / confiscation | `pause`, blacklist | Freeze authority |
| Rebasing | balance manipulation | N/A typical |

Do not force EVM semantics onto Solana or Move chains without chain-specific decoders.

---

## 26. Liquidity Security

| Factor | Finding vs verdict |
| --- | --- |
| LP ownership | Who can remove |
| LP lock | Duration, locker contract, fake lock |
| Lock expiry | Time-bounded safety |
| LP concentration | Exit risk |
| Pool migration | User trap |
| Concentrated liquidity (CLMM) | Range manipulation |

**Critical:** `LOCKED LP ≠ IMMUTABLE ECONOMIC SAFETY`

Agent 09 observes lock **facts**; Agent 10 assesses **interpretation**; Agent 08 assesses **exit liquidity** market framing.

---

## 27. Holder Security

Analyze: top holders, deployer holdings, treasury, LP tokens as holdings, contract wallets, CEX addresses, burn addresses, clusters.

**Forbidden:** `TOP HOLDER = MALICIOUS` without evidence of harmful **behavior** or **privilege**.

Concentration → Security Risk dimension, not scam label.

---

## 28. Wallet Clustering

Suspicious clustering signals: common funding, coordinated timing, synchronized transfers, shared deployer, behavioral similarity.

**Rule:** `CLUSTER ≠ PROVEN COMMON OWNER`

Cluster → ScamIndicator at most; common ownership requires additional evidence tier.

---

## 29. Deployer Intelligence

| Signal | Use |
| --- | --- |
| Deployer history | Prior rugs → ScamIndicator (indirect) |
| Repeated deployments | Template scam pattern |
| Reused bytecode | Clone analysis |
| Funding sources | Indirect evidence |

**Point-in-time rule:** Do not apply information discovered at T1 to assessments claiming time T0 < T1.

---

## 30. Clone Analysis

Bytecode similarity, source similarity, factory templates, proxy patterns.

**Rule:** `SAME CODE ≠ SAME INTENT`

Clone match → investigative priority, not verdict.

---

## 31. Security Dependencies

Token security is not isolated:

| Dependency | Risk |
| --- | --- |
| Oracle | Price manipulation |
| Bridge | Wrapped token mismatch |
| Router / DEX | Path-specific failures |
| External token | Composability exploit |
| Library (OpenZeppelin) | Known CVE if outdated |
| Upgrade infrastructure | Admin compromise |
| Multisig | Key compromise |

`[PROPOSED]` DependencySecurityAssessment linked to primary contract assessment.

---

## 32. Security Composition

Compositional model:

```text
TOKEN + CONTRACT + LIQUIDITY + OWNERSHIP + TRADING + DEPENDENCIES + BEHAVIOR
        → ComposedSecurityAssessment (multi-dimensional)
```

A secure contract in an unsafe system → **conflict**, not average score.

Each dimension retains own epistemic state, evidence, and UNKNOWNs.

---

## 33. Conflict Intelligence

Examples:

| Finding A | Finding B | Resolution |
| --- | --- | --- |
| CODE = LOW RISK | LIQUIDITY = HIGH RISK | `SecurityConflict`; no auto-average |
| CONTRACT = IMMUTABLE | OWNER = RENOUNCED | Positive capability; still check liquidity |
| MARKET = MANIPULATED | NO HONEYPOT | Cross-domain conflict object |
| PROVIDER A = SAFE | PROVIDER B = HIGH RISK | Preserve disagreement (§49) |

`[PROPOSED]` SecurityConflict: conflict_id, finding_a, finding_b, conflict_type, resolution_status (UNRESOLVED default).

---

## 34. Security Score Boundary

If future scoring is proposed:

| Requirement | Rationale |
| --- | --- |
| Published dimensions | No hidden weighting |
| Provenance per dimension | Audit trail |
| Uncertainty bands | Not false precision |
| Missingness flags | Unknown ≠ 0 |
| Temporal validity | Expiry block/time |
| Weighting justification | Human L2 for production |
| Calibration record | Backtest of score vs outcomes |
| Adversarial robustness | Red-team gaming |

**Never:** `SECURITY_SCORE = TRUTH` or `SECURITY_SCORE = GUARANTEE`

Prefer **vector assessments** over scalar collapse (aligns with Agent 07 HD-04, Agent 05).

---

## 35. Readiness

`[PROPOSED]` TSI readiness levels (mapping only — do not replace Agent 07/08/09 readiness without HD):

| Level | Meaning |
| --- | --- |
| `UNKNOWN` | No security work |
| `SCREENING_ONLY` | Heuristic provider flags only |
| `RESEARCH_READY` | Hypotheses + partial verification |
| `PAPER_READY` | Independent verification on critical paths |
| `VERIFIED` | Reproducible assessment package |
| `PRODUCTION_CANDIDATE` | Human L2 + QA + red-team sign-off |

Mapping to Agent 07 data readiness: TSI cannot exceed upstream data readiness.

---

## 36. Incidents

| Incident class | Detection | Response |
| --- | --- | --- |
| Honeypot detection | Sell matrix pattern | Quarantine + hypothesis record |
| Liquidity drain | LP removal magnitude | Incident + stale assessments |
| Ownership compromise | Admin change | Re-privilege assessment |
| Privilege escalation | New role granted | PrivilegeAssessment update |
| Unexpected mint | Supply event | Supply incident |
| Unexpected blacklist | Blacklist add | Sellability re-test |
| Fee mutation | Tax change event | STALE tax findings |
| Proxy upgrade | Implementation change | STALE static analysis |
| Decoder regression | Golden vector fail | UNKNOWN semantic security |
| False positive | Falsification met | Refute hypothesis; FP category |
| False negative | Exploit occurred | FN category; post-mortem |
| Stale assessment | TTL exceeded | Mark STALE |
| Evidence contradiction | Conflicting tier-1 evidence | SecurityConflict + quarantine |

---

## 37. Quarantine

Quarantine when: critical UNKNOWN, conflicting evidence, failed verification, stale critical state, active exploit hypothesis, privilege uncertainty, identity ambiguity.

**Required fields:** reason, issuer (agent/human), timestamp, evidence refs, expiry, review path, release criteria.

**No silent quarantine.** Quarantine blocks **downstream actionability** recommendations from other agents consuming TSI — does not delete observations.

---

## 38. False Positives

| Category | Example |
| --- | --- |
| Legitimate admin functionality | Owner pause for migration |
| Legitimate high tax | Project fee model |
| Unusual but valid mechanics | Rebasing token |
| Router incompatibility | Sell fails on V2, succeeds on V3 |
| Temporary liquidity | Low depth at block |
| Provider decoding error | False honeypot flag |
| Simulation environment issue | Wrong router in sim |
| Chain congestion | Pending vs reverted confusion |

Each FP should link to falsification evidence and update hypothesis state to REFUTED.

---

## 39. False Negatives

| Category | Example |
| --- | --- |
| Hidden dynamic behavior | Tax changes on sell only |
| Time-dependent behavior | Honeypot activates after N blocks |
| Caller-dependent behavior | Only EOAs blocked |
| State-dependent behavior | First sell OK, second fails |
| Proxy upgrade | Benign impl → malicious |
| Unknown dependency | External contract trap |
| Incomplete source | Unverified proxy logic |
| Insufficient simulation | Single path tested |
| Novel exploit | Zero-day |

FN incidents trigger methodology review (Agent 06) and red-team cases (Agent 19).

---

## 40. UNKNOWN

Mandatory UNKNOWN categories:

| Category | Trigger |
| --- | --- |
| Unknown owner | Not readable or proxy obscured |
| Unknown upgrade authority | Admin slot empty / complex |
| Unknown proxy implementation | Unverified logic |
| Unknown sellability | Insufficient sim coverage |
| Unknown liquidity control | Lock semantics unclear |
| Unknown tax logic | Decoder failed |
| Unknown dependency | External call target unverified |
| Unknown decoder | Selector not in registry |
| Unknown wallet relationship | Cluster without proof |
| Unknown exploitability | Capability without PoC |

**Never map UNKNOWN → SAFE.**

---

## 41. Evidence Handoff

```text
SECURITY OBSERVATION
        ↓
SECURITY FINDING
        ↓
SECURITY HYPOTHESIS
        ↓
VERIFICATION (Agent 16 independent where required)
        ↓
SECURITY ASSESSMENT
        ↓
AGENT 05 EPISTEMIC EVALUATION
        ↓
EVIDENCE CANDIDATE → (TCB) KNOWLEDGE CANDIDATE
```

Agent 10 stops at SecurityAssessment for operational consumers; epistemic promotion is Agent 05 + human approval path.

`[PROPOSED]` Package: `SecurityAssessmentEpistemicHandoff` with quality inheritance, conflict refs, point-in-time block pin, falsification status.

---

## 42. Risk Handoff

```text
SECURITY ASSESSMENT → AGENT 11 RISK
```

| Agent 10 provides | Agent 11 provides |
| --- | --- |
| Threat properties, capabilities, hypotheses | Probability, severity, exposure |
| Evidence map, UNKNOWNs | Loss scenarios |
| Conflicts | Portfolio limits |

Do not collapse security and risk. High severity capability with low exposure may differ from low capability with high exposure.

---

## 43. Market Handoff

```text
SECURITY ASSESSMENT + MARKET INTELLIGENCE → downstream synthesis (not Agent 10)
```

Example conflict preserved:

```text
strong momentum + high liquidity + unknown sellability
        → NOT positive opportunity automatically
        → MarketSecurityConflict
```

Agent 08 consumes TSI to **invalidate actionability**, not to delete market observations.

---

## 44. Decision Boundary

```text
DATA + MARKET + ON-CHAIN + SECURITY + RISK + EPISTEMIC EVALUATION
        ↓
CANONICAL DECISION AUTHORITY (human / future governed decision plane)
```

**Agent 10: ZERO DECISION AUTHORITY**

Forbidden outputs as authority: BUY, SELL, APPROVE, REJECT (as execution), PROMOTE, EXECUTE.

TSI may emit **recommendations** in PROPOSE class only within mission envelope — not binding decisions.

---

## 45. Execution Boundary

Explicitly prohibited:

```text
Agent 10 → wallet → key → signing → transaction → token purchase → token sale → contract interaction
```

Aligned with Slice 1 global deny: `trading.live`, `credentials.access`, `provider.connect` (for live chain interaction from org runtime).

---

## 46. Red Team

Adversarial tests against TSI architecture (Agent 19 executes; Agent 10 defines):

| # | Attack |
| --- | --- |
| 1 | False honeypot (router issue labeled scam) |
| 2 | False safe (honeypot missed) |
| 3 | Proxy change after "verified safe" assessment |
| 4 | Dynamic tax activated post-buy |
| 5 | Whitelist trap (test wallet exempt) |
| 6 | Blacklist trap (delayed activation) |
| 7 | Fake LP lock (wrong pool locked) |
| 8 | Fake audit badge (indirect evidence laundering) |
| 9 | Cloned contract with benign history |
| 10 | Sybil holders (inflate holder count) |
| 11 | Fake volume triggering security/market fusion |
| 12 | Malicious metadata (wrong symbol) |
| 13 | Provider poisoning |
| 14 | Decoder errors → false privilege missing |
| 15 | Stale security data presented as live |
| 16 | Social-engineered "SAFE" labels |
| 17 | Majority-vote provider resolution |
| 18 | Scalar score hiding LP risk |
| 19 | SUSPICIOUS → auto-quarantine without reason |
| 20 | Historical rug label applied retroactively |

Architecture must fail closed or preserve UNKNOWN/CONFLICT.

---

## 47. Test Vectors

Future test vectors (design only):

| Vector | Expected handling |
| --- | --- |
| Sell succeeds | Refute honeypot hypothesis for path |
| Sell fails | Multi-cause investigation |
| Sell fails specific addresses only | Support selective restriction hypothesis |
| Tax changes mid-test | STALE prior findings |
| Blacklist changes | Re-run sell matrix |
| Owner changes | Re-run privilege graph |
| Proxy changes | STALE static analysis |
| Mint authority changes | Supply reassessment |
| Liquidity removed | Exit scam hypothesis; not auto verdict |
| LP transferred | Lock reassessment |
| Implementation upgraded | Full re-screen |
| Suspicious external call | Dependency hypothesis |
| Hidden privileged function | Static + dynamic escalation |

---

## 48. Provider Independence

Coordinate with Agent 07:

| Provider type | Method | Independence caveat |
| --- | --- | --- |
| RPC | Node read | Same upstream chain |
| Explorer API | Aggregated | May share indexer |
| Honeypot checker | Simulation/heuristic | Often opaque |
| GoPlus / RugCheck / similar | Pattern DB | Shared threat feeds possible |
| Static analyzer | Bytecode/source | Version dependent |
| Simulation provider | Fork/sim | Config sensitivity |

```text
MULTIPLE SECURITY PROVIDERS ≠ INDEPENDENT SECURITY PROOF
```

Document dependency graph per assessment.

---

## 49. Provider Conflict

When Provider A = SAFE, Provider B = HIGH RISK, Provider C = UNKNOWN:

| Required action | Forbidden action |
| --- | --- |
| Preserve all three with methodology + timestamp + version | Majority vote |
| Create SecurityConflict | Pick "best" silently |
| Default to UNKNOWN for composite if unresolved | Collapse to SAFE |
| Escalate to human if actionability requested | Auto-quarantine without reason |

---

## 50. Freshness

Critical properties with TTL (indicative — human L2 for production values):

| Property | Stale trigger |
| --- | --- |
| Ownership / admin | Admin transfer event |
| Proxy implementation | Upgraded event |
| Tax rates | Tax change event |
| Blacklist/whitelist | List mutation |
| Mint authority | Authority change |
| Liquidity / LP lock | LP event or TTL |
| Holder concentration | Snapshot age > policy |
| Trading state | enableTrading toggle |
| Sellability | Block drift > N or state change |

Previously valid assessment → `STALE` without automatic deletion.

---

## 51. Point-in-Time Security

Historical assessment at time T may use only evidence available ≤ T.

**Forbidden:** Current knowledge of rug at T+30d applied to assessment claiming time T.

`[PROPOSED]` `point_in_time_block` + `evidence_cutoff` mandatory on historical SecurityAssessment exports.

Aligns with Agent 06 leakage controls and Agent 09 §51.

---

## 52. Security Predictions

| Type | Requirements |
| --- | --- |
| Current vulnerability | Evidence now |
| Current risk | Agent 11 framing |
| Future exploit hypothesis | Target, horizon, cutoff, expected event, falsification |
| Future scam prediction | Same + explicit non-certainty label |

Predictions are **Speculation** tier until confirmed — use Prediction artifact (Agent 05), not SecurityFinding.

---

## 53. Failure Taxonomy

| Class | Examples |
| --- | --- |
| Data failure | Stale RPC, missing holder page |
| Identity failure | Wrong token contract |
| Decoder failure | Unknown selector |
| Static analysis failure | Unverified proxy |
| Dynamic analysis failure | Sim timeout |
| Simulation failure | Environment misconfig |
| Semantic failure | Mislabeled "renounced" |
| Temporal failure | Future leak, wrong block |
| Provider failure | API outage, poisoned response |
| Security interpretation failure | SUSPICIOUS → SCAM collapse |
| False positive / false negative | See §38–39 |
| Unknown handling failure | UNKNOWN → SAFE |
| Evidence boundary failure | Indirect → Direct upgrade |
| Risk boundary failure | TSI emits loss probability |
| Decision boundary failure | TSI triggers sell |

---

## 54. Object Model

Conceptual objects (not implemented):

### SecurityObservation

| Field | Description |
| --- | --- |
| `observation_id` | Stable id |
| `source` | Provider/sim/OCI ref |
| `timestamp` / `block` | Observation time |
| `chain` / `contract` / `token` | Identity refs |
| `provenance` | Full lineage |
| `raw_payload_ref` | Immutable raw |
| `normalization_version` | Schema version |
| `epistemic_state` | OBSERVED typical |
| `uncertainty` | Structured gaps |

### SecurityFinding

| Field | Description |
| --- | --- |
| `finding_id` | Stable id |
| `finding_type` | e.g. TAX_ASYMMETRY, UPGRADEABLE, BLACKLIST_CAP |
| `dimension` | CONTRACT / TRADING / LIQUIDITY / ... |
| `evidence_refs` | Tier-tagged |
| `confidence` | Bounded; not assurance of truth |
| `lifecycle` | OBSERVED → ... |
| `forbidden_transitions` | No direct → SCAM |

### SecurityHypothesis

| Field | Description |
| --- | --- |
| `hypothesis_id` | |
| `claim` | Falsifiable statement |
| `falsification_criteria` | Agent 06 required |
| `supported_by` / `contradicted_by` | Finding ids |
| `state` | HYPOTHESIZED / SUPPORTED / REFUTED |

### SecurityTest

| Field | Description |
| --- | --- |
| `test_id` | |
| `hypothesis_id` | |
| `method` | sim / static / ... |
| `preconditions` | Block, caller, route |
| `expected` / `falsification` | |

### SecurityVerification

| Field | Description |
| --- | --- |
| `verification_id` | |
| `test_id` | |
| `result` | PASS / FAIL / INCONCLUSIVE |
| `independent` | bool (Agent 16) |
| `conditions` | Exact environment |

### SecurityAssessment

| Field | Description |
| --- | --- |
| `assessment_id` | |
| `subject` | Token/contract composite ref |
| `dimensions` | Map dimension → finding states |
| `conflicts` | SecurityConflict refs |
| `unknowns` | Explicit list |
| `stale_at` | TTL |
| `readiness` | §35 level |
| `decision_authority` | **NONE** |

### SecurityConflict

Conflict between findings or cross-domain assessments.

### SecurityIncident

Active or historical incident record.

### SecurityQuarantine

Quarantine record with expiry and release criteria.

### PrivilegeAssessment

Owner/admin/role/function graph at block pin.

### SellabilityAssessment

Multi-path sell matrix results.

### LiquiditySecurityAssessment

LP ownership, lock, migration analysis.

### UpgradeabilityAssessment

Proxy/admin/timeline analysis.

### TokenMechanicsAssessment

Mint/burn/tax/freeze/confiscation summary.

**Universal forbidden transitions (all objects):** → EXECUTE, → PROMOTE_KNOWLEDGE (Agent 10), → SAFE_FOR_TRADING (without full ladder).

---

## 55. Required Matrices

### Matrix A — Threat Matrix

| Threat | Observation | Test | Evidence | Impact | Unknown |
| --- | --- | --- | --- | --- | --- |
| Honeypot | Sell revert pattern | Multi-address sell sim | Sim + revert reason | Exit blocked | Router vs malicious |
| LP rug | LP removal event | Lock verification | Direct tx | Capital loss | Intent |
| Hidden mint | Supply spike | Mint auth read | Direct event | Dilution | External minter |
| Upgrade trap | Proxy admin active | Implementation timeline | Direct storage | Logic swap | Future intent |
| Tax trap | Sell tax > 80% | Tax read + net calc | Direct/sim | Effective honeypot | Dynamic change |
| Blacklist trap | Transfer revert | Blacklist storage | Direct | Wallet blocked | Delayed activation |
| Fake lock | Lock UI claim | Locker contract read | Direct | False confidence | Wrong pool |
| Clone scam | Bytecode match | Clone graph | Derived | Identity confusion | Same intent? |
| Oracle manipulation | Price deviation | Oracle read | Direct/derived | Trading unfair | External |

### Matrix B — Contract Privilege Matrix

| Privilege | Actor | Function | State Effect | Risk |
| --- | --- | --- | --- | --- |
| Mint | MINTER_ROLE | `mint()` | Supply ↑ | Dilution |
| Pause | PAUSER | `pause()` | Transfers blocked | Exit denial |
| Blacklist | ADMIN | `blacklist(addr)` | Transfer revert | Selective trap |
| Set tax | OWNER | `setFees()` | Tax change | Economic extraction |
| Upgrade | PROXY_ADMIN | `upgradeTo()` | Logic swap | Total compromise |
| Withdraw LP | LP owner | `removeLiquidity` | Pool depth ↓ | Rug |
| Renounce | OWNER | `renounceOwnership` | Owner zero | **Not** risk elimination |

### Matrix C — Token Mechanics Matrix

| Mechanism | Observable | Security Concern | Verification |
| --- | --- | --- | --- |
| Mintable | Mint events / auth | Supply inflation | Auth read + history |
| Burnable | Burn fn | Deflationary trap rare | Source/static |
| Freeze | Pause/freeze flag | Transfer denial | State read |
| Transfer tax | Fee hooks | Hidden extraction | Sim transfer |
| Max wallet | Revert on large bal | Honeypot component | Sim buy |
| Anti-bot | Cooldown modifiers | Legit vs trap | Behavior matrix |
| Rebasing | Balance changes | Accounting trap | Event history |

### Matrix D — Security Evidence Matrix

| Evidence | Direct/Derived/Indirect | Reliability | Limitations |
| --- | --- | --- | --- |
| Storage read at block | Direct | High if pinned | Coverage |
| Verified source match | Direct | High | Proxy may differ |
| Sell simulation | Derived | Medium | Sim ≠ mainnet |
| Explorer "honeypot" label | Indirect | Low | Opaque method |
| Social "audit" post | Indirect | Very low | Marketing |
| Static analysis warning | Derived | Medium | Unreachable code |
| OCI revert trace | Derived | Medium | Decoder dependent |

### Matrix E — Security Provider Matrix

| Provider | Method | Dependency | Independence | Failure |
| --- | --- | --- | --- | --- |
| RPC node | eth_call | Chain infra | Low if single | Stale state |
| Explorer API | Aggregated | Indexer | Medium | Lag |
| GoPlus-style API | Heuristic DB | Vendor | Unknown | False flags |
| RugCheck-style | Program analysis | Vendor | Unknown | Chain-specific |
| Local static analyzer | Bytecode | Self | High if open | Unverified code |
| Fork sim | Tenderly-class | Sim vendor | Medium | Config errors |

### Matrix F — Security Conflict Matrix

| Finding A | Finding B | Conflict | Resolution |
| --- | --- | --- | --- |
| Code LOW risk | LP HIGH risk | Composition | Present both; no average |
| Provider SAFE | Sim sell fail | Provider vs derived | UNKNOWN until reconciled |
| No honeypot | High sell tax | Mechanism vs label | Tax finding + sell matrix |
| Renounced owner | Upgradeable proxy | Apparent vs actual | Proxy admin finding |
| Market momentum | Unknown sellability | Cross-domain | MarketSecurityConflict |

### Matrix G — Security Readiness Matrix

| Capability | Documented | Implemented | Tested | Verified |
| --- | --- | --- | --- | --- |
| Threat taxonomy | YES (this doc) | NO | NO | NO |
| Security object model | YES | NO | NO | NO |
| Honeypot sim runtime | YES (concept) | NO | NO | NO |
| Privilege graph builder | YES (concept) | NO | NO | NO |
| Provider adapter layer | YES (concept) | NO | NO | NO |
| Agent 09 consumption | YES (boundary) | NO | NO | NO |
| Epistemic handoff | YES (concept) | NO | NO | NO |
| Quarantine runtime | YES (concept) | NO | NO | NO |
| Slice 2B TSI types | NO | NO | NO | NO |

### Matrix H — Security Boundary Matrix

| Agent | Owns | Consumes | Produces | Must Not Override |
| --- | --- | --- | --- | --- |
| 03 Org Security | Infra threat model | Policy/audit | Security architecture | Token scam verdicts |
| 05 Epistemic | Promotion gates | Assessment candidates | Knowledge states | Security facts from OCI |
| 06 Research | Methodology | Hypothesis designs | ExperimentPlan | Execute sims in design mission |
| 07 Data | Quality/provenance | Raw provider data | DataQualityAssessment | Semantic security |
| 08 Market | Market observations | TSI for actionability | MarketIntel | Security verdicts |
| 09 OCI | Chain observations | Raw chain data | OCI observations | SAFE/SCAM labels |
| **10 TSI** | **Security interpretation** | **07,08,09 data** | **SecurityAssessment** | **OCI facts, decisions** |
| 11 Risk | Loss framing | SecurityAssessment | RiskAssessment | Security properties |
| 16 QA | Independent verify | Test specs | VerificationRecord | Findings |
| 19 Red Team | Adversarial probe | TSI architecture | Attack reports | Production changes |

### Matrix I — Security Incident Matrix

| Incident | Detection | Impact | Quarantine | Recovery |
| --- | --- | --- | --- | --- |
| Honeypot confirmed | Sell matrix | Exit loss | Yes | Refute if FP proven |
| FN exploit | External report | Loss | Re-assess | Methodology fix |
| FP quarantine | Falsification | Blocked trade | Release | FP taxonomy update |
| Proxy upgrade | Event | Stale safe label | STALE all | Re-screen |
| Provider poison | Conflict | Wrong verdict | UNKNOWN | Switch provider |
| Decoder regression | Golden fail | UNKNOWN security | Partial | Fix decoder |

### Matrix J — Security-to-Decision Matrix

| Layer | Input | Transformation | Output | Authority |
| --- | --- | --- | --- | --- |
| OCI | Chain raw | Normalize | Observations | None |
| TSI | Observations | Interpret | SecurityAssessment | None |
| Risk | Security + exposure | Quantify | RiskAssessment | None |
| Epistemic | Assessments | Evaluate | Evidence candidate | TCB gate |
| Human/L2 | All layers | Decide | Decision | **Human** |
| Execution | Decision + grant | Execute | Tx | **Denied to org agents** |

---

## 56. Contradictions

| CONTRADICTION_ID | LOCATION | SOURCE_A | SOURCE_B | CONFLICT | IMPACT | CURRENT_STATUS | RECOMMENDED_HUMAN_DECISION |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **TSI-C01** | Registry | Slice 1 `agent.security` | Plane D Agent 03 + Agent 10 | Three "security" roles | Token vs infra vs registry overlap | `UNRESOLVED` | HD-01: map agent.security scope |
| **TSI-C02** | Planned map | Agent 03 Security Architect | Agent 10 Token Security | Both "security" word | Analyst confusion | `UNRESOLVED` | Documented split; HD-02 enforce charter |
| **TSI-C03** | Dual-19 | Plane A roles | Plane D 08–10 | Unmapped specialists | No runtime owner for TSI | `UNRESOLVED` | Dual-19 mapping (HD-01) |
| **TSI-C04** | AHOS vs org | AHOS `SecuritySignals`, honeypot adapters | No org TSI runtime | Product vs org authority | Silent adoption risk | `UNRESOLVED` | HD-20: mediated integration |
| **TSI-C05** | Agent 09 §44 | "Rug risk verdict" listed under Agent 10 | This doc: verdict requires hypothesis ladder | Wording implies verdict without ladder | Overclaim risk | `PARTIALLY RESOLVED` | Use ScamAssessment not colloquial "verdict" |
| **TSI-C06** | Agent 08 §908 | LiquidityAssessment → "safe to trade" example | TSI/MI boundaries forbid auto-safe | Example could mislead | Actionability collapse | `UNRESOLVED` | HD-03: fix example or disambiguate |
| **TSI-C07** | Epistemic enums | Slice 2B HypothesisState | TSI security states §10 | Parallel state machines | Silent merge risk | `UNRESOLVED` | HD-04: mapped vs separate enums |
| **TSI-C08** | Agent 03 §9.2 | Agent 10 "sandboxed fetch" | Global `provider.connect` DENY | Design assumes fetch capability code denies | Implementation gap | `UNRESOLVED` | HD-05: future grant model vs read-only mirror |
| **TSI-C09** | AHOS types | `honeypot: YES/NO/UNKNOWN` trinary | TSI honeypot as hypothesis ladder | Product collapse vs org discipline | FP/FN handling | `UNRESOLVED` | HD-06: AHOS enum mapping |
| **TSI-C10** | CMI + TSI | MarketSecurityConflict proposed both sides | No joint schema | Integration blocked | `UNRESOLVED` | HD-07: cross-domain conflict schema |

Do not silently resolve. `DUAL_19 = UNRESOLVED`.

---

## 57. Human Decisions

| ID | Decision | Why It Matters | Options | Risk |
| --- | --- | --- | --- | --- |
| **HD-01** | Dual-19: map `agent.security` vs Agent 03 vs Agent 10 | Prevents authority and scope collision | A) Split charters B) Merge 03+10 C) Defer | Wrong owner for token scans |
| **HD-02** | Formalize Agent 03 vs Agent 10 charter boundary in L2 | "Security" word overload | Adopt split / rename roles / defer | Misrouted findings |
| **HD-03** | Disambiguate Agent 08 LiquidityAssessment "safe to trade" examples | Prevents market → safety collapse | Rewrite examples / add disclaimer / separate enum | False safety |
| **HD-04** | TSI epistemic states vs Slice 2B enum mapping | Prevents silent state merge | Separate / mapped / unified | Wrong promotion |
| **HD-05** | Future security data ingestion: sandboxed fetch vs mediated AHOS mirror vs deny | Agent 03 assumes fetch; code denies connect | Grant model / AHOS read API / offline only | Policy violation or no data |
| **HD-06** | AHOS `honeypot YES/NO/UNKNOWN` vs org hypothesis model | Product-org semantic alignment | Map YES→SUPPORTED only / keep separate / deprecate trinary | FP/FN mismatch |
| **HD-07** | MarketSecurityConflict + SecurityConflict joint schema (with Agent 08) | Cross-domain actionability | Joint object / linked refs / defer | Hidden opportunity bias |
| **HD-08** | SecurityAssessment scalar score: allow or forbid | Score gaming | Vector only / bounded scalar / defer | Authority collapse |
| **HD-09** | Minimum data readiness for PAPER_READY security claims | Fail-closed vs progress | Agent 07 RECONCILED / custom TSI bar | Stale trades |
| **HD-10** | Independent verification requirement for honeypot SUPPORTED | Agent 16 involvement | Always / critical only / defer | FP/FN |
| **HD-11** | Simulation provider admission and independence rules | Multi-provider ≠ proof | Provider registry / dependency graph | False confidence |
| **HD-12** | Quarantine authority: who may quarantine downstream actionability | Safety vs ops | TSI auto-flag / human only / Agent 11 | Wrong blocks |
| **HD-13** | Point-in-time security archive: org vs AHOS vs external | Historical correctness | Org archive / AHOS mirror / defer | Retroactive bias |
| **HD-14** | Solana/non-EVM TSI: separate decoder plane vs unified model | Chain semantics | Per-chain modules / unified with flags | Wrong privileges |
| **HD-15** | SecurityAssessment → Evidence handoff schema (with Agent 05) | Epistemic boundary | Joint workshop / attachment only | Assessment = knowledge |
| **HD-16** | Adoption of this architecture as L2 governance text | Organizational commitment | Adopt / revise / defer | Doc vs reality drift |
| **HD-17** | AHOS security provider federation (extends HD-20, Agent 07 HD-11) | Avoid duplicate provider logic | Mediated contract / org reimplementation / defer | Divergent verdicts |
| **HD-18** | Auto-action on SUPPORTED honeypot hypothesis (extends Agent 08 HD-13) | Safety vs FP | Never auto / flag only / human gate | Wrong reject |
| **HD-19** | Red-team sign-off before PRODUCTION_CANDIDATE TSI | Agent 19 gate | Mandatory / optional / defer | Gaming |
| **HD-20** | AHOS SecuritySignals integration boundary | TSI-C04 | Read-only mirror / event bus / isolated | Authority leak |

---

## 58. Implementation Gaps

| Gap | Severity | Blocker |
| --- | --- | --- |
| No TSI datatypes in `agent_org/` | HIGH | HD-04, HD-15 |
| No honeypot/simulation runtime | HIGH | HD-05, HD-11 |
| No privilege graph builder | HIGH | Agent 09 authority obs consumption |
| No static analysis adapter | HIGH | Provider admission |
| No security provider registry | HIGH | Agent 07 dependency model |
| No SellabilityAssessment implementation | HIGH | Core honeypot path |
| No SecurityConflict object in code | MEDIUM | HD-07 |
| No quarantine runtime | MEDIUM | HD-12 |
| No freshness/TTL enforcer | MEDIUM | Stale assessments |
| `agent.security` not mapped to Agent 10 | HIGH | HD-01 |
| Plane A/D unresolved | HIGH | HD-01 |
| AHOS integration undefined | MEDIUM | HD-17, HD-20 |
| No golden test vectors for security | HIGH | Agent 16 |
| No cross-domain MarketSecurityConflict schema | MEDIUM | HD-07 |
| Global provider.connect DENY | HIGH | HD-05 for any live scan |

**Current maturity:** `DOCUMENTED` only (this deliverable).

---

## 59. Recommended Future Missions — STATE ONLY

**Do not execute without new TASK ID and explicit command.**

1. **Agent 11 — Risk Intelligence Architecture** (consumes SecurityAssessment; probability/severity framing).
2. **TSI Object Schema Implementation Mission** (Slice 2B types only; no providers).
3. **Agent 16 — QA / Verification: Security Golden Vectors** (honeypot FP/FN baselines).
4. **Cross-Domain Conflict Schema Mission** (Agent 08 + Agent 10 joint HD-07).
5. **Human L2 Session:** Resolve HD-01 Dual-19 and HD-05 provider ingestion model.
6. **AHOS Mediated Security Mirror Design** (read-only; HD-17/HD-20).
7. **Agent 19 — Red Team: TSI Architecture Probe** (§46 attack suite).
8. **Simulation Governance Design Mission** (fork sim admission, independence).
9. **Non-EVM TSI Decoder Plane Mission** (Solana mint/freeze/update; HD-14).
10. **Epistemic Handoff Workshop** (Agent 05 + Agent 10 HD-15).

---

## 60. Final Assessment

**Architectural verdict:** The repository is **ready for token security architecture documentation** but **not ready for token security runtime**. Peer agents 07–09 have established boundaries that Agent 10 must respect. The primary failure mode to prevent is **security authority collapse** — especially the forbidden chain `SUSPICIOUS → SCAM → DANGER → SELL`.

**Strongest existing assets:**

- Epistemic non-collapse discipline (Agent 05, Slice 2B, Constitution)
- Explicit Agent 09 ↔ Agent 10 SAFE/SCAM boundary
- Agent 08 market-security conflict awareness
- Agent 03 least-privilege specialist template including Agent 10 sandbox note
- Research methodology falsification requirements (Agent 06)
- Global execution deny policy in Slice 1

**Critical missing pieces:**

- All TSI domain types and runtime
- Provider/simulation ingestion model under current DENY policy
- Dual-19 mapping for security roles
- AHOS product security vs org TSI integration decision
- Independent verification path for honeypot claims

**Honesty:** This document is `[PROPOSED]` / `DESIGN_ONLY`. It creates **no authority**, **no runtime**, and **no AHOS impact**.

---

```text
MISSION_STATUS = TOKEN_SECURITY_SCAM_INTELLIGENCE_ARCHITECTURE_ANALYSIS_COMPLETE_WITH_GAPS
AGENT_ID = AGENT-10
DIRECT_COMMANDER = MASTER ORCHESTRATOR
LIFECYCLE_STATUS = IDLE / DORMANT / WAITING_FOR_NEW_COMMAND
DUAL_19 = UNRESOLVED
AGENT_ONE = NOT_IMPLEMENTED / FUTURE_NON_AUTHORITY_ROOT
AHOS_IMPACT = NONE
CODE_CHANGES = NONE
RUNTIME_CHANGES = NONE
GOVERNANCE_CHANGES = NONE
COMMIT = NONE
PUSH = NONE
RECOMMENDED_NEXT_MISSION = STATE_ONLY — DO NOT EXECUTE
```

---

**Deliverable path:** `G:\robat\ahos-agent-org\docs\architecture\AGENT_10_TOKEN_SECURITY_SCAM_INTELLIGENCE_ARCHITECTURE.md`

**STOP** — Agent-10 returns to IDLE / DORMANT / WAITING_FOR_NEW_COMMAND. Only MASTER ORCHESTRATOR may issue the next mission.

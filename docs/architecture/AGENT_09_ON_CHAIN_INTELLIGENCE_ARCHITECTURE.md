# Agent Organization On-Chain Intelligence Architecture

```text
DOCUMENT_ID      = AGENT_09_ON_CHAIN_INTELLIGENCE_ARCHITECTURE
MISSION_ID       = TASK-20260914-009
VERSION          = 0.1.0
STATUS           = PROPOSED / READ_ONLY_ON_CHAIN_INTELLIGENCE_ARCHITECTURE
AUTHORITY        = NONE CREATED
RUNTIME_EFFECT   = NONE
AHOS_EFFECT      = NONE
AGENT_ID         = AGENT-09 (agent.org.09-on-chain-intelligence — documentary)
DIRECT_COMMANDER = MASTER ORCHESTRATOR
PARENT           = MASTER ORCHESTRATOR
DUAL_19          = UNRESOLVED
AGENT_ONE        = NOT_IMPLEMENTED / FUTURE_NON_AUTHORITY_ROOT
```

This document is a **design and architecture artifact** produced by AGENT-09 under explicit activation for TASK-20260914-009. It does not implement on-chain intelligence runtime, adopt governance, grant authority, modify AHOS, connect RPC providers or explorers, control wallets, or promote knowledge. Facts cite repository evidence with explicit classification labels (`[IMPLEMENTED]`, `[DOCUMENTED]`, `[PROPOSED]`, `[UNKNOWN]`). Architectural recommendations are labeled `[PROPOSED]`.

**Critical honesty constraint:**

```text
ON-CHAIN ACTIVITY              ≠ INTENT
ON-CHAIN OBSERVATION           ≠ TRUTH ABOUT THE REAL WORLD
WALLET ACTIVITY                ≠ HUMAN IDENTITY
ADDRESS LABEL                  ≠ PROVEN IDENTITY
TOKEN TRANSFER                 ≠ GENUINE DEMAND
WHALE ACTIVITY                 ≠ BULLISHNESS
LIQUIDITY ADDITION             ≠ SAFE LIQUIDITY
CONTRACT DEPLOYMENT            ≠ LEGITIMATE PROJECT
TRANSACTION SUCCESS            ≠ INTENDED ECONOMIC OUTCOME
BLOCKCHAIN DATA                ≠ MARKET DECISION
RAW LOG                        ≠ DECODED EVENT
DECODED EVENT                  ≠ CORRECT SEMANTIC INTERPRETATION
SUPPLY CHANGE                  ≠ PRICE IMPACT
LP LOCKED                      ≠ PROJECT SAFE
BRIDGED TOKEN                  ≠ CANONICAL TOKEN
SAME ADDRESS                   ≠ SAME ENTITY ACROSS CHAINS
SAME TOKEN SYMBOL              ≠ SAME TOKEN
SAME CONTRACT BYTECODE         ≠ SAME PROJECT
CODE CAPABILITY                ≠ ACTUAL INTENT
OWNERSHIP                      ≠ MALICE
RENOUNCED OWNERSHIP            ≠ SAFE
CLUSTER SIMILARITY             ≠ PROVEN COMMON OWNERSHIP
ADDRESS COUNT                  ≠ NUMBER OF INDEPENDENT OWNERS
POOL LIQUIDITY                 ≠ SAFE EXIT LIQUIDITY
ORACLE PRICE                   ≠ UNIVERSAL MARKET PRICE
MEV PATTERN                    ≠ MALICIOUS ACTOR IDENTITY
ANOMALY                        ≠ ATTACK
MULTIPLE PROVIDERS             ≠ MULTIPLE INDEPENDENT OBSERVATIONS
CURRENT STATE                  ≠ RETROACTIVE HISTORICAL TRUTH
BLOCK TIME                     ≠ INGESTION TIME ≠ ANALYSIS TIME
TX_SUCCESS                     ≠ ECONOMIC_SUCCESS
ON-CHAIN INTELLIGENCE          ≠ EVIDENCE ≠ DECISION ≠ EXECUTION
```

---

## 1. Executive Summary

`[VERIFIED]` The AHOS Agent Organization contains **no implemented On-Chain Intelligence (OCI) layer** in code. There are no chain-specific datatypes, decoder registries, finality assessors, reorg handlers, flow graphs, or RPC integrations in `ahos_org/`, `agent_org/`, or `research_worker/`. OCI today exists only as a **planned specialist role** (`agent.org.09-on-chain-intelligence`, `[PLANNED]`) in `PLANNED_19_AGENT_MAP.md`.

`[VERIFIED]` Foundational **upstream dependencies are partially documented** by peer architecture missions: Agent-07 (data quality, provenance, provider independence, §30 on-chain data primer), Agent-08 (market intelligence; explicit OCI boundary §36), Agent-05 (epistemic ladder), Agent-06 (research methodology, leakage controls), Agent-03 (security), Agent-04 (governance). Slice 2B (`agent_org/epistemic.py`, `[IMPLEMENTED]` `[TESTED]`) provides generic `Observation`, `Evidence`, `Hypothesis`, and `ContradictionCase` types — not on-chain domain semantics.

`[VERIFIED]` Slice 1 globally denies `provider.connect`, `trading.live`, and AHOS production access (`ahos_org/policy.py`, `[IMPLEMENTED]` `[TESTED]`). Logical roles `agent.provider-data` and `agent.reality-forensics` exist in the registry but **cannot connect to chain providers** and do not implement OCI.

`[VERIFIED]` AHOS (sibling repository `G:\robat\ahos`, **INSPECTED_ONLY / NO_MODIFICATION**) contains product-level identity resolution (`architecture/identity/`), canonical identity tests (`tests/test_canonical_identity.py`), and demo UI on-chain event schemas — these are **not** organizational OCI runtime and must not be silently adopted as org authority without human L2 integration decisions (see Agent 07 HD-11, HD-14).

**Central architectural question:** What can blockchain state and blockchain activity legitimately tell us — and what can they **not** tell us?

**Primary OCI objective:** prevent **on-chain authority collapse** — where raw RPC responses, decoded events, address labels, whale tags, liquidity metrics, or flow graphs silently become intent, identity, security clearance, market signals, or execution triggers.

**Current OCI posture:** `[DOCUMENTED]` blueprint only; `[PROPOSED]` peer boundaries from Agents 07–08; `[IMPLEMENTED]` generic epistemic and deny-policy substrate. **No on-chain intelligence runtime.**

**Dual-19 status:** `[VERIFIED]` `[CONFLICT / UNRESOLVED]` — Plane A (`agent.provider-data`, `agent.reality-forensics`) and Plane D (`agent.org.09-on-chain-intelligence`) remain separate taxonomies. This document analyzes compatibility only; it does not merge them.

**Agent One:** `NOT_IMPLEMENTED / FUTURE_NON_AUTHORITY_ROOT` — must never become on-chain truth root or execution authority.

**AHOS:** `INSPECTED_ONLY` / `NO_MODIFICATION` / `AHOS_IMPACT = NONE`.

---

## 2. Mission Scope

### 2.1 In scope (this mission)

- Repository forensics and architecture design for On-Chain Intelligence
- Rigorous definition of OCI vs raw chain data, analytics, security, market, and decision layers
- Blockchain state model, chain identity, finality, reorg, decoder governance
- Conceptual object model, epistemic layers, conflict and anomaly handling
- Boundary definitions with Agents 03–08 and future 10–13, 16, 19
- Required matrices (A–J), contradiction analysis, human decisions, implementation gaps

### 2.2 Out of scope (explicit prohibitions)

- AHOS modification; Lane A/B modification; live trading; wallet control; RPC/explorer connections
- Runtime service implementation; decoder implementation; provider adapters
- Agent activation or creation; governance adoption; commits or pushes
- Resolving Dual-19; granting Agent 09 decision authority
- Declaring tokens SAFE or SCAM (Agent 10 domain)
- Claiming any OCI capability is implemented or verified in `ahos-agent-org`

---

## 3. Identity and Lifecycle

### 3.1 Agent-09 identity

| Field | Value |
| --- | --- |
| `AGENT_ID` (mission) | `AGENT-09` |
| Blueprint ID | `agent.org.09-on-chain-intelligence` |
| Provisional name | On-Chain Intelligence Architect |
| Role | Design on-chain intelligence architecture: observation taxonomy, decoder discipline, finality/reorg models, identity and flow semantics |
| Authority class | `NONE` (design mission only) |
| Capabilities exercised | READ, ANALYZE, PROPOSE (documentation) |
| Forbidden | VERIFY (own conclusions), PROMOTE, EXECUTE, MODIFY runtime, CONNECT providers, CONTROL wallets, SIGN transactions, ACTIVATE other agents, declare SAFE/SCAM |
| Supervisor | MASTER ORCHESTRATOR → human operator (MEHRDAD) |
| Source of truth | **Not** AGENT-09. Repository L0/L1 + governance L2/L3 only. |

AGENT-09 is **not** Agent One, **not** the Master Orchestrator, **not** a blockchain node operator, **not** a data engineer (Agent 07 implements data plane), **not** a market analyst (Agent 08), **not** a security verdict engine (Agent 10), and **not** authorized to convert on-chain observations into decisions or execution.

### 3.2 Command chain

```text
MEHRDAD
  → MASTER ORCHESTRATOR
    → AGENT-09 (this mission)
```

- Direct commander: **MASTER ORCHESTRATOR**
- No subordinate agents created or activated
- Peer specialists (03–08, future 10–19) are not commanders

### 3.3 Lifecycle

```text
ACTIVATION_REQUESTED → AUTHORIZED → ACTIVE
  (TASK-20260914-009)
  → COMPLETED (this deliverable)
  → IDLE / DORMANT / WAITING_FOR_NEW_COMMAND
```

Recommendations in this document are **not** commands. AGENT-09 does not auto-continue to Agent 10 or any future mission.

---

## 4. Repository Findings

### 4.1 Implementation inventory (`ahos-agent-org`)

| Component | Path | OCI relevance | Status |
| --- | --- | --- | --- |
| Planned Agent 09 | `PLANNED_19_AGENT_MAP.md` | Blueprint row | `[PLANNED]` |
| Slice 1 registry | `ahos_org/registry.py` | `agent.provider-data`, `agent.reality-forensics` | `[IMPLEMENTED]` logical only |
| Global deny policy | `ahos_org/policy.py` | `provider.connect` denied | `[IMPLEMENTED]` `[TESTED]` |
| Epistemic core | `agent_org/epistemic.py` | Generic Observation/Evidence | `[IMPLEMENTED]` no chain domain |
| Research analyst | `research_worker/analyst.py` | Label discipline only | `[IMPLEMENTED]` Class A |
| Agent 07 architecture | `AGENT_07_DATA_INTELLIGENCE_ARCHITECTURE.md` | §30 on-chain data primer | `[DOCUMENTED]` |
| Agent 08 architecture | `AGENT_08_CRYPTO_MARKET_INTELLIGENCE_ARCHITECTURE.md` | §36 OCI boundary | `[DOCUMENTED]` |
| Chain decoder registry | — | — | `[PROPOSED]` none |
| Finality assessor | — | — | `[PROPOSED]` none |
| Reorg handler | — | — | `[PROPOSED]` none |
| Flow graph store | — | — | `[PROPOSED]` none |
| Address label registry | — | — | `[PROPOSED]` none |

### 4.2 AHOS boundary inspection (`INSPECTED_ONLY`)

| Component | Path | Relevance | Org adoption |
| --- | --- | --- | --- |
| Identity resolution | `architecture/identity/resolution.py` | Token/pool identity gates | `[UNKNOWN]` — HD-11 |
| Identity tests | `tests/test_canonical_identity.py` | EIP-55, Solana, provider conflict | L1 in AHOS, not org |
| Demo on-chain events | `*/db/schema.ts` `onchainEvents` | UI seed data | `[STALE]` product demo; not org TCB |
| Exitability analyzer | `architecture/intel/exitability.py` | Liquidity/exit overlap with Agent 08 | Product-only |

**Rule:** AHOS artifacts inform **compatibility analysis** only. They do not grant org runtime authority.

### 4.3 Honesty classification

```text
DOCUMENTED ≠ IMPLEMENTED
IMPLEMENTED ≠ VERIFIED (for OCI — nothing to verify in org repo)
VERIFIED ≠ PRODUCTION_READY
INSPECTED_ONLY ≠ ADOPTED
```

### 4.4 Dual-19 compatibility (not resolution)

| Plane A (Slice 1) | Plane D (Blueprint) | Overlap theme | Resolution |
| --- | --- | --- | --- |
| `agent.provider-data` | `agent.org.07-data-intelligence` | Raw chain data supply | `UNRESOLVED` (Agent 07) |
| `agent.reality-forensics` | `agent.org.09-on-chain-intelligence` | Reconstructing claims from ledger | `UNRESOLVED` |
| `agent.reality-forensics` | `agent.org.08-crypto-market-intelligence` | Cross-domain forensics | `UNRESOLVED` |
| `agent.scoring-science` | `agent.org.09` + `agent.org.12` | On-chain features in scoring | `UNRESOLVED` |

`[PROPOSED]` compatibility rule: Agent 09 owns **ledger meaning derivation** (what happened on-chain, with what certainty); Plane A roles remain logical policy placeholders until human L2 mapping.

---

## 5. Definition of On-Chain Intelligence

### 5.1 Architectural definition

**On-Chain Intelligence (OCI)** is the bounded architectural domain responsible for transforming **data-quality-qualified chain observations** into **explicitly labeled on-chain interpretations, assessments, hypotheses, and intelligence artifacts** — while preserving uncertainty, provenance, temporal semantics, finality status, and epistemic separation from evidence, security verdicts, market signals, risk approval, and execution.

OCI answers: **"What can we legitimately assert about blockchain state and activity — and with what certainty?"**

OCI does **not** answer: **"Should we buy?"**, **"Is this person Satoshi?"**, **"Is this token safe?"**, or **"What did the deployer intend?"**

### 5.2 Distinction table

| Term | Definition | OCI relationship |
| --- | --- | --- |
| Blockchain raw data | Bytes from node/indexer (blocks, txs, logs, account data) | **Input** to OCI pipeline — not intelligence |
| RPC response | Provider-specific JSON/binary wrapper around raw data | **Observed** with provider caveats |
| Block data | Header + body at a height/slot | **Observed** — canonicality separate |
| Transaction data | Signed intent + execution result | **Observed** — success ≠ economic success |
| Event logs | EVM log entries; Solana program logs | **Observed** — decoding is separate step |
| Decoded events | ABI/schema interpretation of logs | **Decoded** tier — not automatic truth |
| Token balances | Account/mint state at block | **Observed** at pinned block only |
| Wallet activity | Address-centric tx/event aggregation | **Interpreted** — wallet ≠ human |
| Contract state | Storage/slot/program data | **Observed** at pinned block |
| Address labels | Third-party or heuristic tags | **External inference** — provenance required |
| Blockchain analytics | Aggregated metrics (holders, flows) | **Derived** — leakage and sybil risks |
| On-chain evidence | Epistemic warrant artifact (Agent 05) | **Downstream** — OCI produces candidates only |
| Market intelligence | Price/volume/regime (Agent 08) | **Adjacent** — fusion requires explicit boundary |
| Security intelligence | Contract/token threat assessment (Agent 10) | **Adjacent** — OCI observes privileges; Agent 10 judges |
| Risk intelligence | Exposure and loss framing (Agent 11) | **Consumer** — observation ≠ quantified risk |
| Prediction | Forward statement | **Hypothesis tier** — not OCI default output |
| Decision | Trade/approve/reject | **Forbidden** for Agent 09 |
| Execution | Signing, broadcasting txs | **Globally forbidden** |

### 5.3 Purpose

- Structure chain observations with chain-aware identity and finality semantics
- Decode events with governed decoder provenance
- Classify flows, holders, pools, authorities as **assessments**, not facts about intent
- Surface anomalies and conflicts without attack or scam verdicts
- Propagate data-quality and provider limitations from Agent 07
- Produce intelligence artifacts eligible for epistemic packaging (Agent 05), not automatic evidence

### 5.4 Scope

**In scope:** blocks, transactions, instructions, logs/events, contract/program state, token identity, supply changes, holder sets, fund flows, DEX pool state, bridge messages, oracle reads on-chain, MEV patterns (conceptual), finality and reorg handling.

**Out of scope:** CEX order books (Agent 08), off-chain social/news (Agent 07 §31), token bytecode security verdicts (Agent 10), portfolio limits (Agent 11), backtest execution (Agent 12), model training (Agent 13), wallet signing, live RPC connections (denied globally).

---

## 6. Architectural Principles

### 6.1 Core principles

| # | Principle | Implication |
| --- | --- | --- |
| 1 | Observation before interpretation | Raw and decoded tiers never silently merge |
| 2 | Chain-native semantics | No false EVM/Solana equivalence |
| 3 | Pinned block/slot | All state claims anchor to block identity |
| 4 | Finality explicit | No universal N-confirmation rule |
| 5 | Reorg preserves history | SUPERSEDED, not silent delete |
| 6 | Identity tuple mandatory | `(chain_id, address/mint, standard, …)` |
| 7 | Decoder provenance | Every decode carries version and confidence |
| 8 | Label ≠ identity | Address labels are evidence-backed classifications |
| 9 | UNKNOWN first | Missing finality, owner, semantics → UNKNOWN |
| 10 | Zero decision authority | OCI stops before decision layer |
| 11 | Provider independence honest | Multiple endpoints may share one node |
| 12 | Point-in-time correctness | Historical queries use cutoff, not current state |
| 13 | Leakage prevention | No future labels in historical features |
| 14 | Anomaly ≠ attack | Flag deviation; Agent 10/19 adjudicate |
| 15 | Cross-domain conflict preserved | On-chain bullish + market bearish → conflict object |

### 6.2 Layer separation

```text
DATA LAYER (Agent 07)           → acquisition, quality, provider graph
ON-CHAIN LAYER (Agent 09)       → chain semantics, decode, finality, flows
MARKET LAYER (Agent 08)         → price, volume, CEX/DEX market meaning
SECURITY LAYER (Agent 10)       → SAFE/SCAM/danger verdicts (governed)
EPISTEMIC LAYER (Agent 05)      → evidence, claims, promotion
DECISION LAYER (future)         → canonical decision authority
EXECUTION LAYER (future/governed) → wallets, trades — separately governed
```

---

## 7. Blockchain State Model

### 7.1 Conceptual hierarchy (EVM-oriented baseline)

```text
CHAIN
  ↓
BLOCK (or SLOT on Solana)
  ↓
TRANSACTION (or VERSIONED TRANSACTION)
  ↓
INSTRUCTION / CALL / MESSAGE
  ↓
EVENT / LOG (where applicable)
  ↓
STATE TRANSITION
  ↓
ACCOUNT / CONTRACT / TOKEN STATE
```

**Warning:** Not every chain instantiates every level identically. UTXO chains (Bitcoin) use outputs not accounts; Solana uses accounts + programs + instructions without EVM-style logs for all programs.

### 7.2 State transition model `[PROPOSED]`

```text
StateTransition
  chain_id
  block_anchor           # height/slot + hash
  pre_state_root_ref     # optional
  post_state_root_ref    # optional
  affected_entities[]    # accounts, contracts, mints
  transition_kind        # BALANCE_CHANGE | STORAGE_WRITE | MINT | BURN | ...
  observation_refs[]     # tx, instruction, log refs
  finality_status
  epistemic_status       # OBSERVED | DECODED | INTERPRETED
```

### 7.3 Chain model variants

| Model | Examples | Primary unit | Event surface |
| --- | --- | --- | --- |
| Account + contract (EVM) | Ethereum, L2s | Address + storage | Logs via EVM |
| Account + program (Solana) | Solana | Account lamports/data | Program logs (partial) |
| UTXO | Bitcoin | Output | No account logs |
| Object (Sui) | Sui | Object ID | Events |
| Cosmos SDK | Cosmos chains | Module accounts | Events via ABCI |

OCI architecture must support **chain profile** metadata declaring which levels apply.

---

## 8. Chain Identity

### 8.1 Canonical chain identity `[PROPOSED]`

```text
ChainIdentity
  chain_id_numeric       # EVM chainId; SLIP-44 where relevant
  chain_slug             # human registry key (non-authoritative alone)
  genesis_hash           # where applicable
  native_asset_ref
  environment            # MAINNET | TESTNET | DEVNET | LOCAL
  finality_profile_ref
  address_encoding_rules # EIP-55, base58, bech32, ...
  semantic_profile_ref   # EVM | SOLANA | UTXO | ...
```

### 8.2 Identity failure modes

| Failure | Example | Response |
| --- | --- | --- |
| Wrong chain ID | Polygon tx labeled Ethereum | Quarantine; identity conflict |
| Testnet/mainnet confusion | Sepolia USDC treated as mainnet | Environment gate |
| Fork not distinguished | ETH vs ETHPoW post-merge | Genesis/canonical registry |
| Same address different chain | `0xabc…` on ETH and BSC | **Different entities** — never merge |
| Provider chain mismatch | RPC returns wrong network | Provider divergence incident |

### 8.3 Provider and endpoint identity

Every observation must record:

- `provider_id` (Agent 07 model)
- `endpoint_id` / locator
- `observed_chain_identity` (not assumed from config alone)

```text
SAME ADDRESS ≠ SAME ENTITY ACROSS CHAINS
SAME TOKEN SYMBOL ≠ SAME TOKEN
SAME CONTRACT BYTECODE ≠ SAME PROJECT
```

---

## 9. Block Intelligence

### 9.1 Block observation fields

| Field | Purpose |
| --- | --- |
| `block_height` / `slot` | Positional anchor |
| `block_hash` | Content identity |
| `parent_hash` / `previous_slot` | Chain linkage |
| `timestamp` | Block time (untrusted for precision) |
| `proposer` / `validator` | Where available |
| `transaction_count` | Inclusion set size |
| `observation_source` | RPC, indexer, explorer |
| `canonicality_status` | OBSERVED \| CANONICAL \| FINALIZED \| ORPHANED |

### 9.2 Block tiers

```text
OBSERVED BLOCK     = returned by a provider at observation time
CANONICAL BLOCK    = accepted by network consensus rules at depth T
FINALIZED BLOCK    = irreversible under chain finality rules (if defined)
ORPHANED BLOCK     = previously observed, later non-canonical
```

### 9.3 Transaction ordering

Block position and log index matter for causality **within a block**. Cross-block ordering follows chain consensus. MEV and builder ordering can violate naive "mempool order" assumptions.

---

## 10. Finality

### 10.1 Finality models (non-universal)

| Chain class | Finality model | Confirmation meaning |
| --- | --- | --- |
| Ethereum PoS | Checkpoint + epoch finality (~12.8 min) | Probabilistic before finality; deterministic after |
| Ethereum L2 (rollup) | L1 batch inclusion + challenge window | **Chain-specific** — not L1-equivalent |
| Solana | Optimistic confirmation + rooted/supermajority | "Confirmed" ≠ "Finalized" on RPC |
| BSC / PoA | Validator set signatures | Faster but trust assumptions differ |
| Bitcoin | Probabilistic (6 blocks heuristic) | Heuristic, not protocol finality |

**Forbidden rule:** `N confirmations = final` as universal policy.

### 10.2 FinalityAssessment `[PROPOSED]`

```text
FinalityAssessment
  chain_id
  block_anchor
  finality_tier          # UNCONFIRMED | PROBABLE | FINALIZED | UNKNOWN
  confirmations_count    # informational only
  finality_rule_version  # documents chain-specific logic
  assessed_at            # wall clock
  reorg_risk_label       # LOW | MEDIUM | HIGH | UNKNOWN
  limitations
```

### 10.3 Downstream propagation

Intelligence derived from blocks below organization's finality threshold must carry:

- `finality_status != FINALIZED`
- Degraded confidence
- Forbidden use cases: live execution triggers (already globally denied)

---

## 11. Reorganization

### 11.1 Reorg intelligence requirements

When chain reorganizes:

1. Previously observed blocks may become **ORPHANED**
2. Transactions may **revert** or **reorder**
3. Events in orphaned blocks become **non-canonical**
4. Balances at "latest" may change retroactively for unfinalized depth

### 11.2 Lifecycle: observed → superseded

```text
OBSERVED
  → SUPERSEDED_BY_REORG (block/tx/event)
  → INVALIDATED (if intelligence depended on non-canonical anchor)
```

**Never silently rewrite history.** Preserve orphaned observations with supersession link.

### 11.3 ReorgEvent `[PROPOSED]`

```text
ReorgEvent
  chain_id
  detected_at
  old_canonical_tip
  new_canonical_tip
  depth
  affected_block_refs[]
  affected_observation_refs[]
  provider_id
  epistemic_status
```

---

## 12. Transaction Intelligence

### 12.1 Transaction identity

| Chain | Primary ID | Notes |
| --- | --- | --- |
| EVM | `tx_hash` | Same hash rare cross-chain; still chain-scoped |
| Solana | `signature` | Base58; slot + index auxiliary |
| Bitcoin | `txid` | UTXO model |

### 12.2 Transaction observation fields

- `sender` / fee payer
- `recipient` / program targets
- `value` / lamports
- `gas` / compute units
- `fee` / priority fee
- `nonce` / recent blockhash (Solana)
- `status` (success/fail)
- `block_inclusion` (height, index)
- `execution_trace` (where available)
- `internal_calls` (EVM trace)
- `revert_reason` (if failed)

### 12.3 Non-EVM equivalents

| EVM | Solana |
| --- | --- |
| Transaction | Versioned transaction |
| Call | Instruction |
| Contract | Program |
| Log | Program log / inner instructions |
| Gas | Compute units + priority fee |
| Nonce | Recent blockhash + signature uniqueness |

---

## 13. Transaction Success ≠ Economic Success

Explicit preservation:

```text
TX_SUCCESS ≠ ECONOMIC_SUCCESS
```

A successful transaction may:

- Transfer worthless or malicious tokens
- Execute honeypot sell rejection on different path
- Incur extreme slippage vs user intent
- Change unexpected storage slots
- Approve unlimited allowance to attacker
- Complete bridge message with unfavorable rate

OCI records **execution outcome** separately from **economic outcome assessment** (interpretation tier, confidence bounded, intent UNKNOWN).

---

## 14. Event / Log Intelligence

### 14.1 Event identity

```text
EventIdentity (EVM) = (chain_id, tx_hash, log_index)
EventIdentity (Solana) = (chain_id, signature, instruction_index, log_index?)  # profile-specific
```

### 14.2 Event observation layers

| Layer | Content |
| --- | --- |
| Raw log | topics[], data, address |
| Decoded event | name, typed params |
| Semantic interpretation | "swap", "liquidity add", "ownership transfer" |

```text
RAW LOG ≠ DECODED EVENT
DECODED EVENT ≠ CORRECT SEMANTIC INTERPRETATION
```

### 14.3 Indexed parameters

EVM indexed topics enable filtering but lose dynamic type detail. Decoders must document what is **partial** vs **complete**.

---

## 15. Decoder Governance

### 15.1 Decoder architecture `[PROPOSED]`

```text
DecoderRegistry
  decoder_id
  decoder_version
  input_kind             # LOG | INSTRUCTION | TRACE
  output_schema_version
  abi_or_idl_source_ref
  maintainer
  verification_status
```

Every `DecodedChainObservation` preserves:

| Field | Purpose |
| --- | --- |
| `decoder_id` | Which decoder |
| `decoder_version` | Version pin |
| `abi_schema_source` | Origin of ABI/IDL |
| `decode_timestamp` | When decoded |
| `raw_input_ref` | Immutable raw observation link |
| `semantic_confidence` | HIGH \| MEDIUM \| LOW \| UNKNOWN |
| `unknown_fields[]` | Explicit gaps |
| `decode_errors[]` | Non-fatal issues |
| `partial_decode` | Boolean |

**Rule:** Decoders must never silently invent missing fields.

### 15.2 DecoderAssessment `[PROPOSED]`

Tracks regression, disagreement between decoder versions, and unverified ABIs.

---

## 16. Contract Intelligence

### 16.1 Contract observation dimensions

- Deployment tx and deployer
- Bytecode hash vs runtime code (proxy detection)
- Proxy pattern (EIP-1967, beacon, minimal proxy)
- Implementation address
- Admin / owner slots
- Upgradeability flag
- Privileged roles (minter, pauser, blacklist operator)
- Verified source status (explorer — **third-party**, not proof)

### 16.2 Forbidden inferences

```text
CODE CAPABILITY ≠ ACTUAL INTENT
OWNERSHIP ≠ MALICE
RENOUNCED OWNERSHIP ≠ SAFE
CONTRACT DEPLOYMENT ≠ LEGITIMATE PROJECT
```

Agent 10 owns security verdicts; Agent 09 observes **capabilities** and **state**.

---

## 17. Token Identity

### 17.1 Minimum identity tuple

```text
TokenIdentity = CHAIN + TOKEN_ADDRESS_OR_MINT + TOKEN_STANDARD + (optional metadata_version)
```

Never rely solely on `symbol`, `name`, or `decimals`.

### 17.2 Token variants

| Variant | Risk |
| --- | --- |
| Mutable metadata (Solana update authority) | Symbol spoofing |
| Proxy token | Implementation swap |
| Wrapped asset | Bridge/depeg semantics |
| Bridged asset | Non-canonical vs native |
| Synthetic / rebasing | Supply semantics differ |
| Fee-on-transfer | Balance reads misleading |

### 17.3 AHOS compatibility note

AHOS `architecture/identity/` implements resolution gates (`[VERIFIED]` in AHOS tests). Org OCI should **align conceptually** but adoption requires HD-11 — not automatic merge.

---

## 18. Token Supply Intelligence

### 18.1 Supply observation types

- Total supply (on-chain read at block)
- Circulating supply (**often off-chain definition** — mark INTERPRETED)
- Mint/burn events
- Freeze/confiscation (Solana)
- Rebasing adjustments
- Transfer taxes (balance delta ≠ transfer amount)

```text
SUPPLY CHANGE ≠ PRICE IMPACT
```

Price impact requires market domain (Agent 08) and causal methodology (Agent 06).

---

## 19. Address Intelligence

### 19.1 Terminology

| Term | Meaning |
| --- | --- |
| Address | Chain-encoded identifier |
| Account | State-holding entity (varies by chain) |
| Wallet | **Colloquial** — often EOA or key-controlled; not assumed human |
| Contract / Program | Code-controlled account |
| Multisig | Threshold-controlled |
| Smart contract wallet | Contract-mediated control |
| Deployer | Address that deployed contract (historical fact) |
| Treasury / LP / Bridge | **Labels** — require evidence |

```text
WALLET ACTIVITY ≠ HUMAN IDENTITY
ADDRESS IDENTITY = EVIDENCE-BACKED CLASSIFICATION
```

---

## 20. Address Labels

### 20.1 Label provenance model `[PROPOSED]`

```text
AddressLabel
  chain_id
  address
  label_type           # EXCHANGE | WHALE | DEPLOYER | MEV | ...
  label_value
  source_id
  source_kind          # EXPLORER | HEURISTIC | MANUAL | ML
  observed_at
  confidence           # 0-1 or enum
  classification_basis # explicit rule or evidence ref
  expiry               # optional TTL
  evidence_refs[]
  supersedes_label_id
```

Never treat labels as permanent truth. Labels are **hypotheses about classification**, not identity proof.

---

## 21. Holder Intelligence

### 21.1 Holder metrics

- Holder count (address count)
- Top-N holders
- Concentration (Gini, top10%)
- Holder delta over window
- Contract-held vs EOA-held
- Burn address detection
- LP token holders vs underlying

```text
ADDRESS COUNT ≠ NUMBER OF INDEPENDENT OWNERS
```

Sybil splits, custodial aggregation, and contract nesting distort counts.

---

## 22. Wallet Clustering

### 22.1 Conceptual methods

- Common funding source
- Coordinated timing
- Shared deployer
- Shared counterparties / protocols
- Shared gas/fee payer (Solana)
- Behavioral fingerprinting

```text
CLUSTER SIMILARITY ≠ PROVEN COMMON OWNERSHIP
```

Output tier: **HYPOTHESIZED** cluster with confidence and method version.

---

## 23. Fund Flow Intelligence

### 23.1 Flow model

```text
SOURCE → INTERMEDIATE(S) → TOKEN/PROTOCOL → DESTINATION
```

Dimensions: amount, asset, timestamp, block anchor, hop count, bridge/exchange involvement.

```text
TRANSFER ≠ ECONOMIC RELATIONSHIP
```

A transfer may be change return, wash movement, or contract routing without economic meaning.

---

## 24. Flow Graph

### 24.1 Graph model `[PROPOSED]`

```text
FlowGraph
  graph_id
  graph_version
  chain_scope
  time_window
  nodes[]                # addresses, contracts, pools
  edges[]                # typed flows
  edge_type              # TRANSFER | SWAP | BRIDGE | LP_ADD | ...
  amount
  asset_ref
  block_anchor
  provenance_refs[]
  confidence
  temporal_kind          # SNAPSHOT | ACCUMULATED
```

Supports temporal graphs and path analysis. **Graph adjacency ≠ causality.**

---

## 25. DEX / Pool Intelligence

### 25.1 Pool observation types

- Pool creation event
- Pool identity `(chain, factory, pool_address, pool_type)`
- Token pair / curve params
- Reserves / liquidity
- LP token mint/burn
- Swaps (amount in/out)
- Fee accumulation
- Concentrated liquidity ranges (Uniswap v3+)
- Pool migration

Coordinate with Agent 08: **market price** from pool vs **on-chain reserves** — related but not identical (path, manipulation, stale block).

```text
POOL LIQUIDITY ≠ SAFE EXIT LIQUIDITY
```

---

## 26. LP Intelligence

### 26.1 LP ownership dimensions

- LP token holders
- LP lock contracts and duration
- Locker identity
- LP burn (dead address)
- LP concentration

```text
LP LOCKED ≠ PROJECT SAFE
```

Lock can be short, fake, or on irrelevant pool. Agent 10 assesses rug patterns; Agent 08 assesses exit liquidity; Agent 09 observes lock **facts**.

---

## 27. DeFi Intelligence

Conceptual protocol classes: lending, staking, farming, AMMs, vaults, bridges, liquid staking, derivatives.

Each interaction records:

| Field | Tier |
| --- | --- |
| Protocol name/id | INTERPRETED (registry-dependent) |
| Contract/program | OBSERVED |
| Method/instruction | DECODED |
| Assets and amounts | DECODED/OBSERVED |
| State change | OBSERVED |
| Economic interpretation | INTERPRETED/HYPOTHESIS |
| Uncertainty | Required |

---

## 28. Bridge Intelligence

Bridge observations:

- Source/dest chain
- Bridge protocol contract
- Lock/mint / burn/release message
- Message status (pending/executed/failed)
- Latency
- Wrapped vs canonical asset mapping

```text
BRIDGED TOKEN ≠ CANONICAL TOKEN
```

Bridge risk scoring is Agent 11; OCI observes message and token mapping facts.

---

## 29. Oracle Intelligence

On-chain oracle reads:

- Feed address
- Update timestamp (on-chain)
- Value at block
- Deviation from other feeds (cross-domain)
- Staleness vs heartbeat

```text
ORACLE PRICE ≠ UNIVERSAL MARKET PRICE
```

Oracle may be manipulated, stale, or asset-specific.

---

## 30. MEV Intelligence

Conceptual categories: arbitrage, sandwich, backrun, frontrun, liquidation, priority gas, validator behavior.

```text
MEV PATTERN ≠ MALICIOUS ACTOR IDENTITY
```

MEV can be neutral or protective. Pattern detection is **INFERRED**; actor identity remains UNKNOWN unless independently evidenced.

---

## 31. Contract State Intelligence

State reads at pinned block:

- Ownership / admin
- Roles
- Balances and allowances
- Pause flags
- Mint/freeze authority
- Upgrade implementation slot
- Fee parameters
- Blacklist/whitelist maps

All state claims require: `chain_id`, `block_anchor`, `read_method`, `observation_time`.

---

## 32. Token Authorities (Solana and analogs)

| Authority | Solana | EVM analog (partial) |
| --- | --- | --- |
| Mint authority | Can inflate supply | Minter role |
| Freeze authority | Can freeze accounts | Pause/blacklist |
| Update authority | Metadata mutability | Proxy admin |
| Metadata | Off-chain URI + on-chain | URI storage |

Do not map Solana authorities 1:1 to EVM ownership concepts.

---

## 33. EVM vs Solana Semantics

See **Matrix A** (§59) for full comparison matrix.

Key semantic risks: account model vs contract storage, logs vs inner instructions, finality semantics, address encoding, token program vs ERC-20, upgrade patterns.

---

## 34. Temporal Integrity

### 34.1 Timestamp types

| Timestamp | Meaning |
| --- | --- |
| Block time | Chain-declared block timestamp |
| Slot time | Solana slot clock |
| Transaction time | Block time of inclusion |
| Event time | Same as inclusion unless delayed protocols |
| Observation time | Provider returned data |
| Ingestion time | System stored raw artifact |
| Decode time | Decoder ran |
| Analysis time | Intelligence computed |

```text
BLOCK TIME ≠ INGESTION TIME ≠ ANALYSIS TIME
```

All intelligence artifacts must declare which timestamp anchors the claim.

---

## 35. Historical Snapshots

Future system must answer:

> What did we know about this address/token/contract **at time T**?

Requirements:

- Snapshot id tied to block cutoff
- Decoder version at T
- Label set at T (not current labels)
- Finality status at T
- Provider availability at T

Prevent **hindsight contamination** (see §36).

---

## 36. Point-in-Time Correctness

Mandatory for:

- Balances
- Holder sets
- Ownership/admin
- Liquidity/reserves
- Labels
- Token metadata

```text
CURRENT STATE → RETROACTIVE HISTORICAL TRUTH   # FORBIDDEN
```

Historical queries use `as_of_block` / `as_of_time` parameters. Features for Agent 12 must declare block cutoff.

---

## 37. Leakage

Coordinate with Agent 06 and Agent 12.

| Leakage type | Example | Prevention |
| --- | --- | --- |
| Future block | Using block N+k in feature for time T | Strict cutoff |
| Future labels | Whale label applied retroactively | Label effective_time |
| Post-event holder info | Knowing rug exit wallets before event | Point-in-time holder snapshot |
| Future contract classification | "Scam" label from outcome | Forbidden in historical pipeline |
| Survivorship | Only tokens that survived | Universe definition at T |

---

## 38. Observation Model

```text
RawChainObservation
        ↓  (normalize bytes, chain context)
NormalizedChainObservation
        ↓  (ABI/IDL decode)
DecodedChainObservation
        ↓  (domain rules: swap, mint, flow)
OnChainInterpretation
        ↓  (synthesis, conflict check)
OnChainIntelligence
```

Every layer preserves: source, provider, chain, block anchor, timestamps, epistemic status, lineage.

---

## 39. Object Model

Conceptual objects (not implemented):

| Object | Identity key | Epistemic default |
| --- | --- | --- |
| **ChainIdentity** | `chain_id` + genesis/env | DOCUMENTED |
| **BlockObservation** | chain + height/hash | OBSERVED |
| **TransactionObservation** | chain + tx_id | OBSERVED |
| **InstructionObservation** | chain + tx + ix_index | OBSERVED |
| **EventObservation** | chain + tx + log_index | OBSERVED |
| **ContractObservation** | chain + address + block | OBSERVED |
| **TokenObservation** | chain + mint/address + block | OBSERVED |
| **AddressObservation** | chain + address + block | OBSERVED |
| **HolderObservation** | token + block + holder_set_hash | OBSERVED/DERIVED |
| **FlowObservation** | flow_id + block range | INTERPRETED |
| **PoolObservation** | chain + pool_address + block | OBSERVED |
| **AuthorityObservation** | chain + entity + authority_kind | OBSERVED |
| **FinalityAssessment** | chain + block | ASSESSED |
| **ReorgEvent** | chain + detected_at | OBSERVED |
| **DecoderAssessment** | decoder_id + version | METADATA |
| **OnChainAnomaly** | anomaly_id | DETECTED |
| **OnChainHypothesis** | hypothesis_id | HYPOTHESIZED |
| **OnChainIntelligenceAssessment** | assessment_id | SYNTHESIS |
| **OnChainConflict** | conflict_id | CONTRADICTED |

Each object carries: provenance, confidence, uncertainty, freshness, semantic_status, lifecycle, dependencies, forbidden_transitions (e.g., OBSERVED → VERIFIED without Agent 05 path).

---

## 40. Epistemic Layers

Explicit statuses — **do not silently merge**:

```text
RAW
OBSERVED
DECODED
NORMALIZED
INTERPRETED
INFERRED
HYPOTHESIZED
SUPPORTED
CONTRADICTED
UNKNOWN
STALE
SUPERSEDED
```

Mapping to Slice 2B: generic `Observation` may wrap OCI artifacts but domain status must remain on payload.

---

## 41. Conflict Intelligence

Conflict types:

- RPC disagreement (block hash, receipt)
- Explorer vs node
- Decoder version disagreement
- Reorg vs cached state
- Token metadata disagreement
- Label disagreement
- Balance disagreement (archive node vs pruned)
- Historical snapshot disagreement

**Do not auto-select majority provider.** Emit `OnChainConflict` with all sides preserved. Link to Agent 05 `ContradictionCase` when propositional conflict exists.

---

## 42. Provider Independence

Coordinate with Agent 07 §8.

```text
MULTIPLE PROVIDERS ≠ MULTIPLE INDEPENDENT OBSERVATIONS
```

`[PROPOSED]` Provider dependency graph:

- RPC A and RPC B may use same Geth node
- Indexer C may ingest from RPC A
- Explorer D may lag indexer C

Independence requires **upstream dependency evidence**, not brand count.

---

## 43. Anomaly Intelligence

| Category | Example | Tier |
| --- | --- | --- |
| Impossible state | Balance > total supply | DETECTED |
| Duplicate event | Same log indexed twice | DETECTED |
| Unexpected transfer | Large mint without prior | DETECTED |
| Balance mismatch | Trace vs state diff | DETECTED |
| Timestamp anomaly | Block time regression | DETECTED |
| Reorg anomaly | Depth > threshold | DETECTED |
| Decoder anomaly | Unknown selector spike | DETECTED |
| Provider divergence | Hash mismatch | DETECTED |
| Unusual flow | Circular wash pattern | INFERRED |
| Concentration spike | Top holder 90% | INFERRED |
| Authority change | New minter | OBSERVED |
| Liquidity anomaly | 90% LP removed | OBSERVED |

```text
ANOMALY ≠ ATTACK
```

---

## 44. Security Boundary (Agent 10)

| Agent 09 may observe | Agent 10 must govern |
| --- | --- |
| Mint/freeze/upgrade keys present | Is this exploitable? |
| Suspicious flow patterns | Is this a scam pattern? |
| Liquidity removal magnitude | Rug risk verdict |
| Honeypot-like revert traces | Security classification |

Agent 09 **must not** independently declare `SAFE` or `SCAM`.

---

## 45. Market Boundary (Agent 08)

Example preserved conflict:

| Domain | Observation |
| --- | --- |
| On-chain (09) | Whale accumulation |
| Market (08) | Price rising |
| Security (10) | Dangerous mint authority |
| Risk (11) | Thin exit liquidity |

**Do not collapse to `BUY`.** Use `CrossDomainConflict` or linked assessments.

Agent 08 §36 defines fusion as **hypothesis** only. Agent 09 symmetrically must not explain price moves from flows alone.

---

## 46. Risk Boundary (Agent 11)

OCI may surface: concentration, bridge exposure, LP dependency, whale holdings, authority concentration.

Observation **≠** quantified risk. Risk scoring requires Agent 11 frameworks and Agent 06 methodology.

---

## 47. Quant Boundary (Agent 12)

On-chain features for quant use must preserve:

- Point-in-time block cutoff
- Formula and version
- Source and decoder version
- Missingness encoding
- Leakage attestation
- Reproducibility hash

Agent 12 owns backtest validity; Agent 09 owns semantic definition of features.

---

## 48. AI/ML Boundary (Agent 13)

ML may consume normalized observations and graph features. ML must not:

- Treat heuristic labels as ground truth
- Impute missing chain state without flags
- Convert cluster hypotheses into identity labels silently

---

## 49. QA Boundary (Agent 16)

Future verification:

- Block pin correctness
- Tx/decoding golden vectors
- Token identity resolution
- Finality rule compliance
- Reorg supersession chain integrity
- Historical snapshot reproduction
- Graph construction determinism
- Decoder version regression tests

Agent 16 verifies; Agent 09 designs verifiable specs.

---

## 50. Red-Team Boundary (Agent 19)

Required adversarial questions (architecture must survive):

1. Can fake token identity confuse canonical token?
2. Can two chains share address mistaken for same entity?
3. Can current labels contaminate historical data?
4. Can reorgs create false historical events?
5. Can decoder misinterpret an event?
6. Can provider duplication appear as independent confirmation?
7. Can whale cluster be falsely treated as one entity?
8. Can sybil wallets inflate holder counts?
9. Can LP locks create false security?
10. Can mint authority be missed?
11. Can bridge wrappers be mistaken for canonical assets?
12. Can current state overwrite historical state?
13. Can tx succeed while economic intent fails?
14. Can graph proximity be mistaken for causality?

Agent 19 probes; architecture fails closed or preserves UNKNOWN/CONFLICT.

---

## 51. Identity Safety

Safeguards for ambiguous identity entering decision paths:

| Identity | Minimum key | Quarantine trigger |
| --- | --- | --- |
| CHAIN | chain_id + environment | Mismatch across providers |
| TOKEN | chain + address/mint + standard | Symbol-only reference |
| CONTRACT | chain + address + proxy impl | Unresolved proxy |
| ADDRESS | chain + encoded address | Cross-chain collision |
| TRANSACTION | chain + tx_id | Duplicate across chains |
| BLOCK | chain + height + hash | Hash disagreement |
| EVENT | chain + tx + log_index | Decoder failure |
| POOL | chain + factory + pool_id | Wrong pair tokens |
| PROTOCOL | registry version + contracts | Unverified mapping |

No ambiguous identity may pass to decision layer without explicit UNKNOWN or conflict flag.

---

## 52. UNKNOWN Handling

Required UNKNOWN states:

- Unknown address owner
- Unknown token legitimacy
- Unknown contract semantics (unverified ABI)
- Unknown decoder meaning
- Unknown bridge relationship
- Unknown wallet clustering
- Unknown provider correctness
- Unknown finality
- Unknown historical state (pruned node)
- Unknown economic intent

**Never convert UNKNOWN into SAFE, BULLISH, or LOW RISK.**

---

## 53. Evidence Boundary

```text
CHAIN OBSERVATION
        ↓
DATA QUALITY (Agent 07)
        ↓
SEMANTIC VALIDATION (Agent 09)
        ↓
ON-CHAIN INTERPRETATION
        ↓
ON-CHAIN INTELLIGENCE
        ↓
EPISTEMIC EVALUATION (Agent 05)
        ↓
EVIDENCE CANDIDATE
```

**Agent 09 stops at On-Chain Intelligence / assessment artifacts.** Evidence registration is Agent 05. Quality-pass alone is insufficient (Agent 07 §33).

---

## 54. Decision Boundary

```text
MARKET INTELLIGENCE (08)
+ ON-CHAIN INTELLIGENCE (09)
+ SECURITY INTELLIGENCE (10)
+ RISK INTELLIGENCE (11)
+ EPISTEMIC EVALUATION (05)
        ↓
CANONICAL DECISION AUTHORITY (future / human)
```

```text
AGENT-09 DECISION AUTHORITY = ZERO
```

---

## 55. Execution Boundary

Explicitly prohibited for Agent 09:

```text
wallet access | private keys | signing | broadcast | trade | LP provision | contract deploy
```

Aligns with Slice 1 global denies (`provider.connect`, `trading.live`, `credentials.access`).

---

## 56. Failure Taxonomy

| Class | Examples |
| --- | --- |
| Chain identity failure | Wrong network, testnet confusion |
| Provider failure | Outage, stale, pruned archive |
| Block failure | Orphan, hash mismatch |
| Finality failure | Treating unfinalized as final |
| Reorg failure | Silent history rewrite |
| Transaction failure | Missing receipt, wrong status |
| Decoder failure | Wrong ABI, partial decode |
| Semantic failure | Mislabeled swap as transfer |
| Token identity failure | Symbol collision |
| Address identity failure | Checksum error |
| Labeling failure | Stale whale tag |
| Temporal failure | Look-ahead block |
| Historical-state failure | Pruned history unavailable |
| Point-in-time failure | Current label on history |
| Graph failure | Wrong edge direction |
| Reconciliation failure | Auto-majority pick |
| Provenance failure | Missing decoder version |
| Epistemic boundary failure | Intelligence → evidence collapse |
| Security interpretation failure | OCI declares scam |
| Market interpretation failure | Flow → price claim |

See **Matrix H** (§59).

---

## 57. Readiness Model

### 57.1 OCI readiness levels `[PROPOSED]`

| Level | Meaning |
| --- | --- |
| CONCEPT | Idea only |
| DOCUMENTED | Architecture exists (this doc) |
| PROTOTYPE | Non-production code |
| TESTABLE | Golden decoder/finality tests |
| VERIFIED | Independent verification (Agent 16) |
| RESEARCH_READY | Bounded studies allowed |
| PAPER_READY | Paper-trading context |
| PRODUCTION_CANDIDATE | Ops prerequisites — still ≠ truth |

### 57.2 Current mapping

| Component | Readiness |
| --- | --- |
| OCI architecture (this doc) | DOCUMENTED |
| Slice 2B epistemic substrate | IMPLEMENTED (generic) |
| Agent 07 data foundation | DOCUMENTED |
| Agent 08 market boundary | DOCUMENTED |
| Chain decoders / finality runtime | CONCEPT |
| Research Agent OCI use | NOT APPLICABLE |

---

## 58. Observability

Future metrics:

- Provider latency and block lag
- Stale observation rate
- Reorg rate and depth
- Decoder error rate
- UNKNOWN field rate
- Reconciliation failure count
- Provider disagreement rate
- Identity ambiguity count
- Label churn rate
- Graph anomaly rate
- Historical reconstruction failures

---

## 59. Incidents

| Class | Response principle |
| --- | --- |
| Reorg incident | Supersede affected; halt finality-dependent features |
| Provider divergence | Preserve conflict; no auto-merge |
| Decoder regression | Pin previous version; quarantine outputs |
| Chain outage | Mark UNKNOWN; no imputation |
| Stale chain state | Degrade intelligence freshness |
| Wrong token identity | Quarantine downstream lineage |
| Wrong address classification | Supersede labels |
| Historical contamination | Invalidate affected snapshots |
| Data poisoning | Agent 03 + quarantine |
| False flow interpretation | Methodology review (Agent 06) |
| False security/market interpretation | Escalate to Agent 10/08 boundaries |

Escalation: data incidents → Agent 07; epistemic → Agent 05; governance → Agent 04.

---

## 60. Required Matrices

### Matrix A — Chain Semantic Matrix

| Concept | EVM | Solana | Other (e.g. UTXO) | Semantic Risk |
| --- | --- | --- | --- | --- |
| Account | Address with nonce + balance | Account lamports/data; no global nonce | UTXO set | Forced equivalence breaks identity |
| Contract/Program | Bytecode at address | Program + program-derived addresses | Script | Upgrade paths differ |
| Transaction | Signed tx, gas, nonce | Versioned tx, signatures, blockhash | UTXO inputs/outputs | Different failure modes |
| Instruction/Call | Internal/external calls | Instructions to programs | N/A | Log visibility differs |
| Event/Log | LOG opcodes, topics | Program logs (limited) | None native | Decoder strategies differ |
| Token | ERC-20/721 contracts | SPL mint + token accounts | Colored coins | Balance query semantics differ |
| Mint | contract mint function | Mint authority on mint account | Issuance tx | Authority model differs |
| Owner | Ownable, roles | Account owner; mint authority separate | Key holding UTXO | Solana has multiple authorities |
| Authority | Roles, Ownable | Mint/freeze/update | Miner/validator | Security reviews must be chain-aware |
| State | Storage slots | Account data segments | UTXO set | Historical queries differ |
| Finality | Epoch finality + confirmations | Optimistic + rooted | Probabilistic blocks | **No universal N-conf rule** |
| Fee | Gas × price | CU + priority fee | sat/byte | MEV attachment differs |
| Nonce/Sequence | Account nonce | Tx signature uniqueness | UTXO order | Replay protection differs |
| Upgradeability | Proxy patterns | Program upgrade authority | Soft forks | Proxy detection differs |

### Matrix B — On-Chain Object Matrix

| Object | Source | Identity | Temporal Anchor | Epistemic Status |
| --- | --- | --- | --- | --- |
| BlockObservation | RPC/indexer | chain+height+hash | block time | OBSERVED |
| TransactionObservation | RPC/indexer | chain+tx_id | inclusion block | OBSERVED |
| EventObservation | RPC/logs | chain+tx+log_index | inclusion block | OBSERVED |
| DecodedChainObservation | Decoder | raw ref+decoder v | decode time | DECODED |
| TokenObservation | RPC | chain+mint+block | block pin | OBSERVED |
| FinalityAssessment | Finality engine | chain+block | assessment time | INFERRED |
| ReorgEvent | Reorg detector | chain+tip change | detection time | OBSERVED |
| FlowObservation | Graph builder | flow_id | block range | INTERPRETED |
| OnChainConflict | Reconciler | conflict_id | observation time | CONTRADICTED |
| OnChainIntelligenceAssessment | OCI synthesizer | assessment_id | analysis time | SYNTHESIS |

### Matrix C — Identity Matrix

| Identity | Key | Ambiguity | Verification | Failure |
| --- | --- | --- | --- | --- |
| Chain | chain_id+env | Same slug different networks | Genesis hash match | Wrong chain |
| Token | chain+address+standard | Symbol collision | Multi-source + contract read | Fake token |
| Contract | chain+address | Proxy impl unknown | Storage slot read | Wrong impl |
| Address | chain+encoding | Cross-chain same hex | Checksum validation | Invalid encoding |
| Transaction | chain+tx_hash | Reorg replay | Receipt match | Orphan tx |
| Block | chain+height+hash | Fork | Multiple provider hash agree | Split view |
| Event | chain+tx+log_index | Anonymous events | Decoder match | Mis-decode |
| Pool | chain+pool_address | Clone pools | Factory event + tokens | Wrong pool |
| Protocol | registry id | Name collision | Contract registry | Spoof protocol |

### Matrix D — Provider Independence Matrix

| Provider | Upstream Dependency | Independent? | Evidence |
| --- | --- | --- | --- |
| RPC A (vendor 1) | Own Geth node | Partial | Need infra disclosure |
| RPC B (vendor 2) | Same cloud node as A | **No** | Dependency graph |
| Explorer C | Indexer on RPC A | **No** | Lag + same source |
| Indexer D | Own ingestion | Partial | May still use one node |
| Archive node E | Full history | Partial | Pruning policy matters |
| Aggregator F | Multiple RPCs | Partial | Correlation cluster |

### Matrix E — Finality Matrix

| Chain | Finality Model | Confirmation Meaning | Reorg Risk |
| --- | --- | --- | --- |
| Ethereum L1 | Checkpoint finality | Pre-finality probabilistic | Low post-finality |
| Ethereum L2 | L1 batch + challenge | **Profile-specific** | Medium until L1 final |
| Solana | Optimistic + rooted | RPC "confirmed" ≠ finalized | Non-zero pre-rooted |
| BSC | PoA validators | Fast but trust assumptions | Low depth, trust-based |
| Bitcoin | Probabilistic | 6-block heuristic only | Non-zero |

### Matrix F — Decoder Matrix

| Decoder | Input | Output | Version | Verification |
| --- | --- | --- | --- | --- |
| ERC-20 Transfer | LOG | Transfer event | semver | Golden log vectors |
| Uniswap V2 Swap | LOG | Swap params | semver | Pool regression |
| Uniswap V3 | LOG | Swap + ticks | semver | CL edge cases |
| SPL Token | Instruction | Transfer/mint | semver | Solana fixtures |
| Unknown proxy | LOG | partial/UNKNOWN | semver | Must not invent fields |

### Matrix G — Intelligence Boundary Matrix

| Agent | Owns | Consumes | Produces | Must Not Override |
| --- | --- | --- | --- | --- |
| 07 Data | Quality, provider graph | Raw bytes | DataQualityAssessment | OCI semantics |
| **09 OCI** | Chain meaning, decode, finality | Qualified data | OnChainIntelligence | Evidence, decisions |
| 08 Market | Price/volume/regime | OCI pool refs (optional) | MarketIntelligence | On-chain intent |
| 10 Security | SAFE/SCAM verdicts | OCI authority obs | SecurityAssessment | OCI observations |
| 11 Risk | Risk framing | OCI concentration | RiskAssessment | Risk quant from obs alone |
| 12 Quant | Backtest validity | OCI features | Study results | Feature semantics |
| 05 Epistemic | Evidence/claims | OCI assessments | Evidence | On-chain truth |

### Matrix H — Failure Matrix

| Failure | Detection | Impact | Quarantine | Recovery |
| --- | --- | --- | --- | --- |
| Reorg | Tip regression | False events | Supersede chain | Re-index from final |
| Decoder regression | Golden test fail | Wrong semantics | Pin old decoder | Fix + replay |
| Token ambiguity | Symbol-only ref | Wrong asset | Block downstream | Identity resolution |
| Provider split | Hash mismatch | Split brain | Conflict object | Human/provider policy |
| Label leakage | effective_time audit | Invalid research | Invalidate features | Rebuild snapshot |
| Finality overclaim | Rule audit | False certainty | Degrade tier | Correct rule version |

### Matrix I — Historical Integrity Matrix

| Data | Point-in-Time Requirement | Leakage Risk | Validation |
| --- | --- | --- | --- |
| Balance | block pin | current balance substitute | Archive node replay |
| Holders | block pin | post-hoc holder set | Indexer historical |
| Labels | label effective_time | future whale tag | Label versioning |
| Metadata | block + authority | post-update URI | On-chain read at block |
| LP reserves | block pin | post-rug liquidity | Pool state historical |
| Flow graph | window + cutoff | future tx inclusion | Graph rebuild at T |

### Matrix J — Data-to-Decision Matrix

| Layer | Input | Transformation | Output | Authority |
| --- | --- | --- | --- | --- |
| Raw chain | Node bytes | Capture | RawChainObservation | None |
| Data quality | Raw | Agent 07 assess | Quality vector | None |
| Decode | Raw+ABI | Decoder | DecodedObservation | None |
| OCI | Decoded | Domain rules | OnChainIntelligence | None |
| Epistemic | Intelligence | Agent 05 | Evidence candidate | None (promotion gated) |
| Decision | Multi-domain | Canonical authority | Decision | Human/governed |
| Execution | Decision | Mediated executor | Tx/trade | Separately governed |

---

## 61. Contradictions

| CONTRADICTION_ID | LOCATION | SOURCE_A | SOURCE_B | CONFLICT | IMPACT | CURRENT_STATUS | RECOMMENDED_HUMAN_DECISION |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **OCI-C01** | Registry | Slice 1 `CANONICAL_AGENT_IDS` (19) | `PLANNED_19_AGENT_MAP` Agent 09 | Two 19-role taxonomies | OCI role not in Plane A | `UNRESOLVED` | Dual-19 mapping (HD-01 Agent 07, new HD-09) |
| **OCI-C02** | Agent 07 §30 vs this doc §10 | "Invalidate below depth N" reorg | Chain-specific finality, no universal N | Reorg policy oversimplification | Wrong finality on L2/Solana | `UNRESOLVED` | Adopt chain profiles; supersede universal N |
| **OCI-C03** | Slice 1 registry | `agent.reality-forensics` | `agent.org.09-on-chain-intelligence` | Claim reconstruction vs OCI | Overlap on "what happened" | `UNRESOLVED` | Define forensic vs observational boundary |
| **OCI-C04** | Agent 08 §16 vs this doc §25 | Agent 08 DEX/pool intelligence | Agent 09 pool observations | LP event ownership | Duplicate or conflicting pool semantics | `UNRESOLVED` | Split: 09=on-chain facts, 08=market price/exit |
| **OCI-C05** | AHOS vs org | AHOS `architecture/identity/` | No org identity runtime | Product identity vs org design | Integration authority unclear | `UNRESOLVED` | HD-11 (Agent 07): mirror vs mediated |
| **OCI-C06** | Agent 07 §30 vs Agent 09 scope | Data layer on-chain primer | OCI domain ownership | Who owns decoder/finality specs | Gap or duplication | `UNRESOLVED` | 07=transport/quality; 09=semantics/decode |
| **OCI-C07** | Agent 05 Observation type | Generic observation | Chain-specific metadata | Insufficient pinning fields | Weak historical reproduction | `UNRESOLVED` | Extend payload schema or sidecar types |
| **OCI-C08** | Agent 08 §36 fusion | Cross-domain hypothesis | Agent 09 flow→price causal risk | Implicit narrative merge | False causal stories | `UNRESOLVED` | Mandate CrossDomainConflict objects |
| **OCI-C09** | Demo AHOS UI seed | Marketing on-chain claims | Epistemic protocol | "LP locked" shown as fact | Authority collapse in product UI | `UNRESOLVED` | Product labeling review (out of org scope) |
| **OCI-C10** | Agent 06 leakage vs Agent 07 temporal | Methodology rules | Data temporal model | Feature cutoff ownership | ML leakage | `UNRESOLVED` | Joint HD with Agent 12 |

Do not silently resolve any contradiction.

---

## 62. Human Decisions

| ID | Decision | Why It Matters | Options | Risk |
| --- | --- | --- | --- | --- |
| **HD-09** | Dual-19: map `agent.reality-forensics` vs `agent.org.09` | Prevents forensic/OCI authority overlap | A: merge roles B: split forensics=claims, 09=ledger C: defer | Wrong mapping blocks operational clarity |
| **HD-10** | Adopt OCI readiness levels (§57) as org vocabulary | Aligns with Agent 07/08 readiness | Adopt / modify / defer | Inconsistent maturity claims |
| **HD-11** | Chain finality profiles: per-chain vs configurable templates | Universal N-conf is unsafe | Per-chain registry / template library | Finality overclaim |
| **HD-12** | Decoder registry authority: org TCB vs git vs AHOS mirror | Decoder version is semantic truth anchor | Org-owned / AHOS read-only mirror / shared git | Decoder drift |
| **HD-13** | Historical state: archive node requirement vs indexer trust | Point-in-time correctness | Require archive / allow indexer with risk flag | Wrong historical features |
| **HD-14** | Label admission: who may attach address labels | Labels propagate to ML | Agent 09 only / Agent 07 provider labels / manual L2 | False identity |
| **HD-15** | OCI ↔ Evidence handoff schema (with Agent 05, extends HD-09 Agent 07) | Prevents quality-pass → evidence | Joint schema workshop | Epistemic collapse |
| **HD-16** | AHOS identity module adoption (extends Agent 07 HD-11) | Avoid duplicate identity logic | Mediated contract / org reimplementation / defer | Identity divergence |
| **HD-17** | Pool intelligence split Agent 08 vs 09 (OCI-C04) | LP remove semantics | 09 facts only / shared object model | Market/OCI conflict |
| **HD-18** | Reorg policy: supersession vs delete in storage | Audit and research integrity | Immutable supersession chain / compaction policy | History loss |
| **HD-19** | Adoption of this architecture as L2 governance text | Organizational commitment | Adopt / revise / defer | Doc vs reality drift |

---

## 63. Implementation Gaps

| Gap | Priority | Dependency |
| --- | --- | --- |
| No `ChainIdentity` registry | HIGH | HD-11, HD-16 |
| No decoder registry | HIGH | HD-12 |
| No finality assessor | HIGH | HD-11 |
| No reorg handler | HIGH | HD-18 |
| No raw chain artifact store | MEDIUM | Agent 07 data plane |
| No flow graph | MEDIUM | Decoder + identity |
| No label provenance store | MEDIUM | HD-14 |
| No OCI conflict type | MEDIUM | Agent 05 coordination |
| No historical snapshot API | HIGH | HD-13 |
| No chain semantic profiles | HIGH | Matrix A adoption |
| No observability | LOW | Runtime exists first |
| Slice 2B generic Observation insufficient for block pin | MEDIUM | OCI-C07 |
| `provider.connect` denied — no live validation | N/A | By design |

All gaps are `[PROPOSED]` future work. **No implementation in this mission.**

---

## 64. Recommended Future Missions — STATE ONLY

`RECOMMENDED_NEXT_MISSION = STATE_ONLY — DO NOT EXECUTE`

1. **Agent 10 — Token Security / Scam Intelligence Architecture** (consumes OCI authority observations; defines SAFE/SCAM boundary).
2. **Agent 11 — Risk Intelligence Architecture** (quantifies concentration, bridge, LP exposure from OCI features).
3. **Joint Agent 05 + 09 boundary mission:** OCI assessment → Evidence eligibility test cases.
4. **Joint Agent 07 + 09 mission:** Chain data contracts, provider dependency graph for RPC/indexer.
5. **Joint Agent 08 + 09 mission:** CrossDomainConflict schema for market/on-chain fusion.
6. **Joint Agent 12 + 09 mission:** On-chain feature registry with leakage and block cutoff specs.
7. **Agent 16 verification mission:** Golden decoder vectors and finality rule tests.
8. **Agent 19 red-team mission:** §50 adversarial question battery against OCI architecture.
9. **FUTURE_IMPLEMENTATION_REQUIRED:** `FinalityAssessment`, `ReorgEvent`, `OnChainConflict` artifact types.
10. **FUTURE_IMPLEMENTATION_REQUIRED:** Historical snapshot store with `as_of_block` queries.
11. **FUTURE_IMPLEMENTATION_REQUIRED:** Decoder registry with version pinning and regression suite.
12. **Human L2:** Resolve HD-09 through HD-19 before production OCI runtime.

**AGENT-09 does not execute any of the above.**

---

## 65. Final Assessment

The AHOS Agent Organization has **strong epistemic and data-intelligence foundations** (Slice 2B, Agent 07/08 architecture missions) but **no on-chain intelligence runtime**. Agent 09's role is to define how ledger observations become **bounded, chain-aware, temporally correct intelligence** without collapsing into identity proof, security verdicts, market signals, or execution authority.

The highest-risk failure modes are:

1. **Finality overclaim** (especially L2 and Solana)
2. **Decoder semantic drift** without version pins
3. **Label and current-state leakage** into historical research
4. **Provider independence illusion**
5. **Cross-domain narrative fusion** (flows explaining price)
6. **Authority collapse** from OCI to SAFE/BUY/EXECUTE

This architecture document establishes vocabulary, boundaries, objects, matrices, and human decisions required before any OCI implementation mission.

---

## Document provenance

| Field | Value |
| --- | --- |
| Author | AGENT-09 (On-Chain Intelligence Architect) |
| Task | TASK-20260914-009 |
| Commander | MASTER ORCHESTRATOR |
| Repository | `G:\robat\ahos-agent-org` |
| Code changes | NONE |
| Runtime changes | NONE |
| Governance changes | NONE |
| Commit | NONE |
| Push | NONE |
| AHOS inspection | INSPECTED_ONLY / NO_MODIFICATION |
| Lifecycle after delivery | IDLE / DORMANT / WAITING_FOR_NEW_COMMAND |

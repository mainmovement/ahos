# AGI/ACI Architecture Map (actual repository)

```text
                    HUMAN GOVERNANCE
                    (gap registers, freeze, PRs, soak owner)
                              |
        +---------------------+----------------------+
        |                     |                      |
   Lane A FROZEN         Lane B Python brain      Edges (not brains)
   discovery/**          architecture/**          TypeScript Command Center
   paper_trading/**      decision/authority       telegram_ai (gateway)
                         scoring / risk / intel   n8n workflows
                         learning/calibration     Cursor skills (devs)
                         knowledge/claims+panel
                         council (advisory)
                         evolution/engine+ledger+hindsight
                         runtime observation daemon
                         cognitive/  ← contracts + P2 memory + P3 loop (isolated)
```

## Cognitive Core vs domain adapters

```text
Cognitive Core (domain-general)
  contracts, hypothesis, experiment_bridge, self_research,
  novelty, evaluation, sandbox, capability, evolution_gate,
  world_model inventory, reasoning inventory, agent passports,
  counterfactual policy, cognitive memory store (isolated sqlite),
  P3 loop (retrieve → assemble → reason → critique → lesson)

Financial / token Domain Adapters (existing; not rewritten here)
  architecture/intel/*, architecture/intelligence/*,
  architecture/scoring, architecture/security overlay,
  frozen discovery collectors, frozen paper_trading
```

## Intelligence → execution (must remain)

```text
INTELLIGENCE (core + adapters)
    → DECISION (CanonicalDecisionAuthority / DecisionAdvisor)
        → RISK GOVERNOR (architecture/risk + security overlay)
            → PERMISSION (PAPER_ONLY; human gates)
                → EXECUTION (paper only; live NOT IMPLEMENTED)
```

Kill switch must not require Cognitive Core cooperation (n8n/telegram sketches exist; not upgraded here).

## Dual documentation authority

```text
Operational now: DOC_TRUTH_MAP, AHOS_GAP_REGISTER, NEXT_DEVELOPMENT_BACKLOG,
                 PRE_SOAK_PROTOCOL, WINDOWS_OPERATOR_HANDOFF, CALIBRATION_LIFECYCLE

Strategic evolution: AHOS_AGI_ACI_ARCHITECTURE_CHARTER_v1.0
                     ADR-ACI-001 (conflict record)

Superseded: AHOS_FINAL_STATUS.md
```

## Soak parallelism

```text
WINDOWS SOAK (owner host)  ||  Lane-B AGI/ACI contracts (this branch)
  run_1788987515_7ad11528  ||  no daemon, no T0, no calibration write
```

## What was deliberately not drawn as existing

- Knowledge graph / causal model
- Memory-bearing agents
- Autonomous evolution loop in production
- Live trading path
- 99.9% intelligence metric

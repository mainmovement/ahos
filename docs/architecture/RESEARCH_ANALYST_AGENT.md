# Research Analyst Agent

Status: implemented, non-production, Windows `spawn` tested in this workspace.

This is the first Class A bounded deterministic research agent. It is not
Slice 2C, Agent One, an LLM agent, a plugin host, a trading agent, or an
AHOS agent.

## Classification

```text
CLASS = A
RUNTIME = PROCESS_ISOLATED
INTERPRETER = FIXED_DETERMINISTIC
LLM = NOT_PRESENT
NETWORK = DENIED
CREDENTIALS = DENIED
AHOS = DENIED
SESSION = NONE
AUTHORITY = NONE
PROMOTION = DENIED
VERIFICATION = DENIED
PRODUCTION = NO
FULL_OS_SANDBOX = NO
```

Identity:

```text
AGENT_ID = RESEARCH_ANALYST_AGENT
KIND = RESEARCH_AGENT_CONTEXT
IDENTITY = NON_HUMAN / NON_PRODUCTION / NON_AUTHORITY
SESSION = NONE
RUNTIME = PROCESS_ISOLATED_WORKER
```

## Runtime path

The agent runs only through:

```text
IsolatedResearchRuntime
    -> process-isolated worker
    -> fixed deterministic interpreter
    -> WorkerRequest JSON messages
    -> host-side validation
    -> narrow allow-listed IPC operations
    -> TCB-mediated research writes
```

`ResearchAgentHost.invoke()` is not used. The worker does not receive a host
callback, TCB instance, operator session, store, callable, filesystem handle,
network client, credential, secret, or AHOS path.

The worker interprets a typed `ResearchTask` and emits a JSON `AgentOutput`.
The host validates that output before any write. A malformed output yields:

```text
REJECTED
NO_COMMIT
NO_TCB_WRITE
```

Every accepted output is labeled:

```text
NON_AUTHORITATIVE
UNVERIFIED
NON_PRODUCTION
```

## Interpreter

The interpreter is a fixed, explicit rule engine in
`research_worker/analyst.py`. It does not execute caller-supplied Python, does
not load plugins, and does not call an LLM.

Transparent rules:

1. Only items labeled `OBSERVATION` become observations.
2. Evidence keeps its provenance reference and is never converted into a claim.
3. Claims stay claims and are never converted into evidence.
4. Hypotheses must be labeled `HYPOTHESIS`.
5. Predictions must be labeled `PREDICTION`.
6. Missing provenance becomes `UNKNOWN` / `UNVERIFIED`, never `SAFE`.
7. Explicit `NOT <text>` pairs may produce a contradiction record.
8. An experiment is proposed only when a hypothesis exists, a required
   observation is missing, the method is descriptive, and execution is not
   requested.
9. Review requests identify a candidate or artifact ID only.
10. The agent never emits `VERIFIED`, `PROMOTED`, `AUTHORIZED`, `EXECUTABLE`,
    `APPROVED`, or `SAFE`.

## Allow-listed operations

This first agent may cause only:

```text
READ_CONTEXT
CREATE_MISSION
RECORD_SOURCE
RECORD_EVIDENCE
CREATE_CLAIM
CREATE_HYPOTHESIS
CREATE_PREDICTION
RECORD_OBSERVATION
RECORD_CONTRADICTION
PROPOSE_EXPERIMENT
RECORD_EXPERIMENT_RESULT
REQUEST_REVIEW
```

These operations remain gated and are not used by this agent:

```text
READ_EPISTEMIC_STATE
READ_SUPPLIED_ARTIFACT
CREATE_CANDIDATE
```

Denied:

```text
PROMOTE_KNOWLEDGE
RECORD_INDEPENDENT_VERIFICATION
CREATE_SESSION
CREATE_PRINCIPAL
DELEGATE_AUTHORITY
MODIFY_POLICY
EXECUTION
TCB_SUBMIT
```

`RECORD_CONTRADICTION` and `REQUEST_REVIEW` require a knowledge candidate in
the current TCB. This first agent does not call `CREATE_CANDIDATE`, so those
records remain in `AgentOutput` only. That is a classification choice, not a
hidden promotion path.

`IsolatedResearchRuntime` locks `IsolatedIpcHandler` to `FIRST_AGENT_OPERATIONS`.
Callers cannot widen that set. `CREATE_CANDIDATE` is denied on `handle_bytes`,
`handle_injected_bytes`, and `run_probe`. In-process `facade().create_candidate()`
remains an operator-held API and is not a worker ingress.

## Commit strategy

Mission 5.6 uses Strategy A (preflight, then sequential TCB commands).

```text
WORKER IPC
   -> parse only
   -> collect inert requests (READ_CONTEXT snapshot only; writes are not dispatched)
   -> receive final AgentOutput
   -> reject if any worker write was attempted
   -> validate complete AgentOutput
   -> preflight host-derived plan
   -> sequential TCB writes
```

The TCB is atomic per command, not across a multi-command batch. Therefore:

* preflight or first-write failure -> `REJECTED` / `NO_COMMIT`
* later write failure after an accepted write -> `PARTIAL_COMMIT_FAILURE`
* never `OK` / `COMMITTED` unless every planned write succeeded

Duplicate JSON keys are rejected (`DUPLICATE_JSON_KEY`). Operation names must
match allowed strings exactly (no trim, case-fold, or non-ASCII).

## Residual risk

```text
The worker is process-isolated but not a full OS sandbox.
The worker runs as the same Windows user.
OS-level file, environment, subprocess, import, and network abuse are not
proven impossible.
Therefore this agent is non-production and must not receive secrets,
credentials, network access, AHOS paths, or unrestricted code.
```

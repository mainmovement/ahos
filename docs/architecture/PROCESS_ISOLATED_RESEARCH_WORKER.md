# Process-Isolated Research Worker

Status: implemented, non-production, Windows `spawn` tested in this workspace.

This is not Slice 2C, not Agent One, not a full OS sandbox, and not live trading.

## Classification

```text
PROCESS_ISOLATION = YES          # untrusted cognitive worker vs trusted host
WINDOWS_PROCESS_MODEL = multiprocessing.get_context("spawn")
IPC_PROTOCOL = AHOS-WORKER-IPC/1
SERIALIZATION = json.dumps / json.loads (send_bytes/recv_bytes)
TCB_OBJECT_EXPOSED_TO_WORKER = NO
OPERATOR_SESSION_EXPOSED_TO_WORKER = NO
NETWORK_POLICY = APPLICATION_DENIED
OS_NETWORK_ISOLATION = NOT_PROVIDED
RESOURCE_QUOTAS = NOT_PROVIDED
```

The in-process `ResearchAgentHost.facade()` remains a same-process API. Its
existing tests still assert `PROCESS_ISOLATION_PROVIDED = False`. Isolation
applies to `IsolatedResearchRuntime`, which runs `research_worker.worker`
in a child process.

## Boundary

```text
UNTRUSTED WORKER PROCESS
  research_worker.worker
  JSON WorkerRequest only
           |
           | Pipe send_bytes / recv_bytes
           v
TRUSTED HOST PROCESS
  IsolatedIpcHandler (allow-list, schema, deny-list)
           |
           v
  ResearchAgentHost / TCB / session / audit
```

The child is started with a JSON-serializable `WorkerContext` (ids and
workspace *names* only). It does not receive TCB objects, sessions, stores,
approvals, or filesystem roots.

## Honest residuals

- The worker user identity is the same Windows user as the host.
- The worker can still use CPython builtins (`eval`, `open`, `subprocess`)
  unless blocked at OS level. Those are **not** provided as host capabilities.
  API denial is not OS impossibility.
- `agent_org.tcb` may still be importable from site path; the **host TCB
  instance and operator session are not in the worker process**.
- CPU/memory quotas are not implemented.
- No cryptographic worker identity and no durable audit.

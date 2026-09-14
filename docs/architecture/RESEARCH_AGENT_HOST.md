# Read-Only Cognitive Research Agent Host

Status: implemented, non-production, Windows-tested in this workspace.

This is not Slice 2C, not Agent One, not execution, and not unrestricted Python hosting.

## Runtime classification

```text
API_BOUNDARY = ENFORCED
PROCESS_ISOLATION = NOT PROVIDED   # in-process ResearchAgentHost.facade()
SAME_PROCESS_RUNTIME = NON_PRODUCTION
SAME_PROCESS_RESIDUAL = YES
```

Process isolation for untrusted cognitive code is a separate runtime:
`IsolatedResearchRuntime` (see PROCESS_ISOLATED_RESEARCH_WORKER.md).
The in-process host tests remain the honest classification for `facade()`.

The supported agent API is fail-closed. The runtime still executes in the same
Python process as the Trusted Command Boundary. A callback that already has
CPython reflection can walk function closures and reach the mediator. That is
classified, not advertised as an OS sandbox. D-13 (static AST import boundary)
is not the primary control.

## Boundary

```text
COGNITIVE AGENT
       |
       v
RESEARCH AGENT HOST  (facade only)
       |
 +-----+------+
 |            |
 v            v
READ COPY   BOUNDED RESEARCH WRITE
              |
              v
     CommandEnvelope constructed by host
              |
              v
     TrustedCommandBoundary.submit
              |
              v
     fail-closed Slice 2B policy
```

The agent does not receive TCB internals, stores, sessions, grants, approvals,
or identity administration.

## Identity

No agent session issuance.

Attribution uses `RESEARCH_AGENT_CONTEXT`. It is a host-supplied cognitive
principal/context for epistemic producer fields and host audit. It is not human
identity and not production authority. Command envelopes are submitted under the
local operator session held by the host.

## Allowed vs denied

Sandbox candidates: `READ`, `RESEARCH_WRITE`.

Denied fail-closed: `GOVERNANCE`, `EXECUTION`.

Research writes are mediated registrations and challenges (source, evidence,
claim, hypothesis, prediction, observation, contradiction, experiment plan/run,
candidate, request review).

Denied through the facade, including when arguments look valid:

- `PROMOTE_KNOWLEDGE`
- approval issuance
- independent verification records
- principal/session creation
- authority delegation
- policy modification
- execution, network, AHOS, credentials, eval/exec/compile/importlib, subprocess, shells

`ResearchMission.authority_resources` is intent text, not a grant. Protected
resource declarations and forbidden capability intents are rejected. A mission
does not create capabilities.

## Filesystem

Default sandbox: `research-sandbox` under the Agent Organization workspace root.
Agents may only read paths the host has already exposed, after traversal,
absolute-path, secret-name, and escape checks. There is no raw `open()` API.

## Honest limitations

- Same-process residual: facade methods close over the mediator.
- Host audit is local and not cryptographic human attribution.
- No process isolation, no network, no AHOS connection, no Agent One.

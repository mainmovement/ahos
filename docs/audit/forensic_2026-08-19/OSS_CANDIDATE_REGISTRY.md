# Open-source candidate registry

## 1. Audit boundary

This is a candidate registry only. No external repository was cloned, copied, installed, imported, or executed. Metadata was queried read-only through the GitHub API on 2026-08-19. Stars/issues are discovery signals, not correctness or security scores. License values are GitHub SPDX metadata, not a full legal review. Upstream tests, dependency trees, vulnerabilities, Windows wheels, offline behavior, and benchmark claims remain `UNVERIFIED` unless explicitly stated.

Pipeline law:

```text
DISCOVER -> LICENSE TEXT -> SECURITY -> DEPENDENCIES/SBOM -> MAINTENANCE
-> ARCHITECTURE FIT -> WINDOWS/OFFLINE -> BENCHMARK -> RED TEAM -> REPLAY/CI
-> ImprovementProposal -> HUMAN APPROVAL -> VERSIONED INTEGRATION
```

No candidate below has passed that pipeline.

## 2. Metadata snapshot

| Candidate | Capability | License metadata | Maturity/maintenance signals at query time | Security/test posture | Windows/offline | AHOS fit / integration cost | Verdict |
|---|---|---|---|---|---|---|---|
| `temporalio/sdk-python` | durable workflow, replay, long-running orchestration | MIT | official Temporal SDK; created 2022; 1,166 stars; 227 forks; 95 open issues; not archived; pushed 2026-08-19; release 1.31.0 on 2026-07-29 | no GitHub community security-policy link returned; source/tests/vulns/deps not audited | client/server Windows/offline topology unverified; Temporal service required | conceptual fit for future durable orchestration, but conflicts with current SQLite/single-laptop simplicity and needs server/migration/process redesign; **high cost** | **DEFER / NO INTEGRATION NOW** |
| `promptfoo/promptfoo` | LLM eval, RAG/agent red team | MIT | created 2023; 24,377 stars; 2,210 forks; 509 issues; not archived; pushed 2026-08-19; release 0.122.0 on 2026-08-04 | community profile 100%, but no security-policy link returned; no dependency/vuln/test audit | Node runtime and Windows/offline behavior unverified | useful only after AI/RAG has a measured benchmark; introduces a second runtime and broad attack surface; **medium/high cost** | **HOLD UNVERIFIED** |
| `crewAIInc/crewAI` | role-playing multi-agent runtime | MIT | created 2023; 57,318 stars; 8,186 forks; 813 issues; not archived; pushed 2026-08-19; release 1.15.16 on 2026-08-14 | no security-policy link returned; deps/tests/vulns unverified | unverified | persona/autonomous-agent emphasis is a poor fit for deterministic, evidence-first, no-fabricated-authority design; overlaps without closing tool/rollback gaps; **high cost** | **NO INTEGRATION / PRESERVE AS COMPARISON** |
| `asg017/sqlite-vec` | SQLite vector search | Apache-2.0 | created 2024; 8,024 stars; 349 forks; 202 issues; not archived; pushed 2026-05-18; release v0.1.9 on 2026-03-31 | no security-policy link returned; native extension/source/deps/vulns not audited | “runs anywhere” is upstream description, not audit proof; Windows wheel/CPU/offline proof unverified | could fit SQLite/local-first if RAG is justified; native extension packaging and migration add risk; compare with structured/keyword search first; **medium cost** | **CANDIDATE FOR FUTURE BENCHMARK ONLY** |
| `BerriAI/litellm` | multi-provider AI gateway/router | **NOASSERTION** from API | created 2023; 56,755 stars; 10,723 forks; 4,990 issues; not archived; pushed 2026-08-19; release v1.97.0 on 2026-08-16 | license text unresolved; no security-policy link returned; very broad provider surface; dependency/vuln/test audit absent | unverified | might consolidate three AHOS AI routers, but current stdlib client is smaller and advisory use is low volume; legal/dependency surface is disproportionate; **high cost** | **REJECT UNTIL LICENSE/NEED PROVEN; NO INTEGRATION** |
| `open-telemetry/opentelemetry-python` | traces/metrics/log context | Apache-2.0 | established 2019; 2,591 stars; 973 forks; 397 issues; not archived; pushed 2026-08-17; release v1.44.0 on 2026-07-16 | community profile 87%; no security-policy link returned; tests/deps/vulns not inspected | unverified | strong standardization candidate after one runtime is operational; currently adds packages/exporter decisions beyond lightweight local tracer; **medium cost** | **DEFER; BENCHMARK AGAINST CURRENT TRACER** |
| `jd/tenacity` | Python retry policies | Apache-2.0 | established 2016; 8,752 stars; 344 forks; 43 issues; not archived; pushed 2026-08-06; release 9.2.0 on 2026-08-05 | community profile 42%; no security-policy link returned; source/tests/deps/vulns not audited | unverified | could replace duplicated retry loops, but current retry behavior is explicit and test-pinned; dependency only justified by measured reduction/correctness; **low/medium cost** | **HOLD / NO INTEGRATION WITHOUT COMPARISON** |

## 3. Candidate-by-candidate acceptance questions

### Temporal Python SDK

- Can a single Windows laptop run the required service durably without Docker/WSL fragility or unacceptable RAM/disk use?
- What current scheduler/control-plane behavior would it replace rather than duplicate?
- Can SQLite evidence/state migrate and replay without semantic loss?
- Does it improve crash/restart evidence enough to justify a new server and schema?

Until answered by a Windows benchmark, the current scheduler remains the better fit.

### promptfoo

- Is there a stable local-AI prompt/evidence benchmark to evaluate?
- Can it run fully offline against Ollama with sanitized datasets?
- Is Node already justified for n8n, or would this create another unmanaged supply chain?
- Can output map to AHOS evidence IDs and deterministic-veto rules?

No AI benchmark exists yet, so adoption would be display-first.

### CrewAI

- Which concrete missing capability does it provide that a small typed tool orchestrator cannot?
- Can every role's authority be statically enforced?
- Can it prevent hallucinated tool calls/self-approval and produce executable rollback?
- Does it reduce code/dependencies relative to current contracts?

Current answer: no evidence. It is a comparison candidate, not an integration candidate.

### sqlite-vec

- Is vector retrieval measurably better than structured claims/FTS/keyword search for a defined AHOS corpus?
- Are signed/reproducible Windows x64 wheels/extensions available for the pinned Python/SQLite version?
- How are index version, source deletion, rebuild, citations, and sensitive data handled?
- Can the deterministic core run when the extension is absent?

### LiteLLM

- Resolve exact license/full text and component licensing first.
- Compare dependency/SBOM/attack surface with the current ~200-line stdlib client.
- Prove a need for gateway features at AHOS's expected local advisory volume.
- Ensure paid routing, telemetry, and proxy defaults cannot violate $0/privacy laws.

### OpenTelemetry Python

- Define the operational problem: cross-process traces, exporters, or standard metric semantics.
- Keep no-export/local-only operation available.
- Benchmark overhead and dependency count on Windows.
- Avoid running Prometheus/Grafana solely to claim observability.

### Tenacity

- Inventory all retry loops and identify actual semantic defects/duplication.
- Compare explicit current backoff/circuit behavior with a minimal dependency adoption.
- Preserve provider-specific rate-limit and evidence event semantics.

## 4. Missing candidate lanes

No candidate should be added merely to fill a category. Future read-only discovery may examine:

- Windows-native process supervision;
- SQLite migration/version tooling;
- SBOM/license/vulnerability scanning;
- local embedding models/runtimes;
- PostgreSQL migration/replay;
- deterministic property-based testing/fault injection.

Crypto exchange/order libraries are intentionally out of scope. A library such as CCXT would create live-execution pressure and is incompatible with the permanent paper-only boundary unless used solely in a quarantined metadata comparison; it is not recommended.

## 5. Security interpretation

“GitHub community security-policy link not returned” does **not** mean a project is insecure; it means this metadata probe did not find that one signal. Likewise, recent pushes and many stars do not establish maintainability for AHOS. Required next-stage evidence includes:

- full license and notice files;
- maintainers/release/signing/provenance review;
- dependency graph and SBOM;
- known-vulnerability/advisory scan;
- install scripts/network/telemetry review;
- tests and release automation inspection;
- Windows/offline installation proof;
- benchmark against the current implementation;
- rollback and removal cost.

## 6. Registry conclusion

The highest-fit near-term candidates are not agent frameworks. If later evidence justifies them, a small retry library, standard telemetry SDK, or SQLite-local vector extension may deserve a sandbox comparison. Temporal is a future orchestration target only after the single-laptop operational baseline. No external code should be integrated before the repository's P0/P1 safety, data, Windows, and dependency foundations are fixed and the user explicitly approves a candidate audit phase.

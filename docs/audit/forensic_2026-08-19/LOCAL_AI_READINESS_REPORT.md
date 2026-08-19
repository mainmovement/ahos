# Local AI, Ollama, routing, embeddings, RAG, and tool-readiness report

## Verdict

**Chat transport: YELLOW. Local AI operation: RED/unproven. Embeddings, RAG, vector memory, and tool execution: RED/absent.**

AHOS does not need AI for its deterministic score/safety path, which is the correct architectural choice. It has a usable advisory chat abstraction, but no Ollama process/model/hardware test ran, and three competing AI routing/configuration surfaces remain.

## 1. Implemented surfaces

### Active advisory council

- `architecture/ai/clients.py`
  - stdlib `urllib` OpenAI-compatible and Anthropic transports;
  - environment-only keys;
  - paid providers excluded by default;
  - normalized availability/error/latency/status/raw-hash envelope.
- `architecture/ai/council_live.py`
  - parallel provider calls;
  - constrained stance parsing;
  - safety-ratcheting AVOID behavior;
  - deterministic verdict supremacy;
  - disagreement and echo warnings;
  - `DETERMINISTIC_ONLY` when no provider responds.
- `config/ai_council_providers.yaml`
  - Ollama first at `http://localhost:11434/v1`;
  - model `qwen2.5:7b-instruct`;
  - cloud free-tier and paid entries.
- Production reachability: imported on demand from `telegram_ai/service.py` for an AI-assisted Telegram response. It is not part of the automatic canonical entry-vetting chain.
- Tests: `tests/test_ai_council_live.py` exercises injected clients, parsing, fallback, safety ratchet, and anti-echo behavior.

Status: `PARTIALLY_IMPLEMENTED`, `REQUIRES_EXTERNAL_SERVICE`, `REQUIRES_USER_ACTION`.

### Parallel AI implementations

| Surface | Role | Current reachability |
|---|---|---|
| `architecture/ai/*` + council registry | actual HTTP calls and synthesis | on-demand Telegram caller; preferred current transport |
| `telegram_ai/providers.py` + `ai_providers.yaml` | sequential capability fallback (`AIPAL`) | tests only; production orphan |
| `architecture/provider_router.py` + `ai_provider_registry.yaml` | capability/health/cost/circuit selection contract | tests only; performs no call |

These are semantically useful but not integrated. Availability, model, capability, cost, and evidence fields diverge.

## 2. Ollama readiness

| Requirement | Evidence | Rating |
|---|---|:---:|
| OpenAI-compatible chat request | implemented | GREEN component |
| Local endpoint configurable | YAML value exists, but no environment override in current loader | YELLOW |
| Ollama installation | not checked | RED |
| Model installed/present | not checked | RED |
| Model version/digest pinned | tag only, no digest | RED |
| Persian quality benchmark | none | RED |
| CPU/GPU/RAM/disk budget | none | RED |
| latency/timeout benchmark | none | RED |
| offline/no-network test | none | RED |
| Docker-to-host route | `localhost` would point to the AHOS container, not Windows host Ollama | RED for Docker |
| health/model-list probe | not implemented before chat | RED |
| context/token limit validation | not measured in active client | RED |
| model output persistence/provenance | response body hash exists in memory; council `to_dict()` omits `raw_responses`; no durable ledger | YELLOW/RED |

The configured model may be a reasonable candidate, but the repository has no evidence that it fits the target laptop or performs adequately in Persian. The note that it is “strong” and “keeps working” is a hypothesis conditional on installation and hardware, not measured truth.

## 3. Reliability and security findings

### AI-001 — Intended timeout is not necessarily an upper bound

`LiveCouncil.deliberate(timeout_sec=90)` cancels unfinished futures, but it uses a `ThreadPoolExecutor` context manager. Exiting that context waits for already-running tasks; the Ollama client has a 120-second request timeout. A missing/hung local service can therefore exceed the advertised council timeout. Add a test using a truly blocking transport and redesign cancellation/transport timeouts before unattended use.

### AI-002 — No preflight health/model probe

Keyless Ollama is structurally treated as available and attempted. There is no `/api/tags` or `/v1/models` check, no model presence check, and no circuit breaker in the active client. Repeated requests can repeatedly hit a down host.

The isolated AI `ProviderRouter` has circuit-breaker logic, but LiveCouncil does not use it.

### AI-003 — Three registries can route differently

The active council, legacy AIPAL, and contract router can disagree on paid/free status, availability, model name, endpoint, and capabilities. This makes docs/tests insufficient evidence for the production caller.

### AI-004 — Evidence containment is prompt-level, not a formal output verifier

The system prompt requires evidence-grounded reasons and structured fields. Parsing validates stance/confidence shape, but it does not mechanically link each numeric reason to an `evidence_ref`. The separate AI provider contract has numeric-provenance validation but is not connected to LiveCouncil.

AI advice remains non-authoritative, reducing impact, but user-visible claims still need a validator/redactor.

### AI-005 — Cloud metadata drifts

Provider model IDs, free tiers, paid status, accessibility, and endpoints can change. The current registry is configuration, not live evidence. Each cloud provider requires a dated read-only health probe and owner approval; paid calls must remain opt-in.

### AI-006 — Docker endpoint mismatch

When AHOS runs in Docker, `http://localhost:11434` addresses the container itself. Windows Docker Desktop commonly needs an explicitly configured host gateway such as `host.docker.internal`, with a local-only security boundary. No compose environment currently wires that.

### AI-007 — Optional `httpx` is unused

`requirements-optional.txt` says `httpx` is an Ollama convenience, but active source uses `urllib` and no `httpx` import was found. Do not add/display dependencies without a demonstrated caller.

## 4. Embeddings, RAG, memory, and long context

| Capability | Current implementation | Status |
|---|---|---|
| Text embeddings | none | `DOCUMENTED_ONLY`/absent |
| Embedding model routing | none | absent |
| Chunking/document ingestion | none | absent |
| Vector index/store | none | absent |
| Similarity search | none | absent |
| RAG prompt assembly | none | absent |
| Citation retrieval/verification | no RAG; deterministic evidence refs exist elsewhere | absent for AI |
| Index versioning/rebuild | none | absent |
| Sensitive-document filtering | none | absent |
| Long-context budget/truncation | only generic `max_tokens` output limit | `PARTIALLY_IMPLEMENTED` |
| Durable AI memory | no council ledger; knowledge claims are separate structured data | absent for conversations |

The existence of `architecture/knowledge` does not make it RAG. That package is deterministic lens/team/claim logic and a SQLite claim store, not embeddings or retrieval augmentation.

## 5. Tool and agent readiness

| Capability | Reality |
|---|---|
| Typed tool registry | absent |
| Filesystem/repository inspection tools | absent |
| Python/PowerShell command tool | absent |
| Test runner tool | absent |
| Sandboxed edit/apply tool | absent |
| Git status/diff/commit/revert tool | absent |
| Permission/approval scopes per tool | absent |
| Tool-call audit ledger | absent |
| Repair-loop orchestration | absent |
| Rollback executor | absent |

The AI council produces advice text only. The self-evolution state machine does not call models or tools. AHOS therefore has no autonomous engineering agent despite extensive agent/council terminology.

## 6. Safe local-AI acceptance plan

### Phase A — bounded chat proof (no architecture expansion)

1. Consolidate active AI config or explicitly adapt the contract router to LiveCouncil.
2. Add `AHOS_OLLAMA_BASE_URL` and a Docker-safe optional host route; keep loopback/local default.
3. Add read-only health and model-list probes with explicit `NO_HOST`/`NO_MODEL` states.
4. Pin and record model tag/digest, Ollama version, host hardware, RAM/disk, and exact prompt pack.
5. Benchmark Persian structured-output validity, p50/p95 latency, memory use, cancellation, and offline operation.
6. Persist only sanitized envelope/provenance needed for audit; do not retain secrets or uncontrolled prompts by default.
7. Keep all AI output advisory and unable to override deterministic vetoes.

### Phase B — evaluate embeddings/RAG only if a measured need exists

Before adding a dependency, define:

- target documents and query benchmark;
- citation/recall/precision failure criteria;
- data sensitivity and deletion/rebuild policy;
- Windows/offline wheel availability and resource budget;
- deterministic no-RAG fallback;
- candidate comparison in `OSS_CANDIDATE_REGISTRY.md`.

Do not install a vector database merely to display “memory.” A small SQLite-compatible candidate should be benchmarked against a simple keyword/structured claim lookup first.

### Phase C — tool use only under a separate approval

Any engineering tool loop must have a workspace sandbox, command allowlist, time/resource limits, secret redaction, clean Git precondition, diff size cap, test gate, approval boundary, evidence ledger, and executable rollback. It must never modify Lane A or promote itself.

## 7. Final Local AI assessment

AHOS is correctly designed to survive with zero AI. Preserve that. Prove one local advisory chat model on the real Windows laptop before adding embeddings, RAG, agent frameworks, or heavy dependencies. Current Local AI readiness remains **RED operationally** and must not be described as installed, active, or autonomous.

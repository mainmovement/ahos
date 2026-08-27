# AHOS AI Provider Architecture & Fallback Routing Strategy

This document establishes the multi-tier artificial intelligence routing matrix for AHOS. It guarantees that AHOS maintains 100% operational capability with **$0/month API cost**, zero vendor lock-in, and zero single-point-of-failure vulnerabilities.

---

## 1. Multi-Tier AI Provider Topology

```
                                  +-------------------------------+
                                  |     AHOS AI ROUTER V2         |
                                  +-------------------------------+
                                                  |
                 +--------------------------------+--------------------------------+
                 |                                |                                |
                 v                                v                                v
    +--------------------------+    +--------------------------+    +--------------------------+
    |         TIER 1           |    |         TIER 2           |    |         TIER 3           |
    |   LOCAL OFFLINE AI       |    |     FREE HOSTED APIS     |    | DETERMINISTIC HEURISTIC  |
    | (Zero Cost / 100% Local) |    |  (Optional Zero Cost)    |    |  (Zero Cost / 100% Floor)|
    +--------------------------+    +--------------------------+    +--------------------------+
    | - Ollama Local Daemon    |    | - Groq Free Tier         |    | - Pure-Python Rule Engine|
    |   • Qwen 2.5 (3B / 7B)   |    | - OpenRouter Free Tier   |    | - Statistical Z-Scores   |
    |   • Llama 3.2 (1B / 3B)  |    | - Gemini Free Tier API   |    | - Forensic Score Checks  |
    |   • Mistral Nemo (12B)   |    | - Cloudflare AI Workers  |    | - AMM Constant Product   |
    | - llama.cpp / LM Studio  |    | - Hugging Face Free Inf. |    | - Zero Network / CPU-Only|
    +--------------------------+    +--------------------------+    +--------------------------+
                 |                                |                                |
                 +--------------------------------+--------------------------------+
                                                  |
                                                  v
                                  +-------------------------------+
                                  |    INSTRUCTOR SCHEMA GUARD    |
                                  |  (Pydantic V2 Strict Validate)|
                                  +-------------------------------+
                                                  |
                                                  v
                                  +-------------------------------+
                                  |     STRUCTURED AI COUNCIL     |
                                  +-------------------------------+
```

---

## 2. Exhaustive AI Provider Matrix

| Tier | Provider Name | Model Name | Typical Latency | Cost / 1M Tokens | Free Rate Limits | Failure State & Fallback Target |
|---|---|---|---|---|---|---|
| **Tier 1 (Local)** | **Ollama Local** | `qwen2.5:7b-instruct` | 150-400 ms (GPU/CPU) | **$0.00** (Local) | Unlimited Local | Process down / Timeout (15s) $\rightarrow$ Tier 1 Backup (`llama3.2:3b`) $\rightarrow$ Tier 2 |
| **Tier 1 (Local)** | **Ollama Fast** | `llama3.2:3b` | 80-180 ms | **$0.00** (Local) | Unlimited Local | Timeout (10s) $\rightarrow$ Tier 2 Free Cloud / Tier 3 |
| **Tier 1 (Local)** | **llama.cpp / LM Studio** | `Mistral-7B-Instruct-v0.3-GGUF` | 120-300 ms | **$0.00** (Local) | Unlimited Local | Port unreachable $\rightarrow$ Tier 3 Heuristics |
| **Tier 2 (Free Cloud)** | **Groq Cloud** | `llama-3.3-70b-versatile` | 90-250 ms | **$0.00** (Free Tier)| 30 req / min (6k RPM) | HTTP 429 / Daily limit $\rightarrow$ OpenRouter Free |
| **Tier 2 (Free Cloud)** | **OpenRouter Free** | `meta-llama/llama-3.2-3b-instruct:free` | 200-600 ms | **$0.00** (Free Tier)| 20 req / min | HTTP 429 $\rightarrow$ Gemini Free API |
| **Tier 2 (Free Cloud)** | **Google Gemini Free**| `gemini-1.5-flash` | 300-800 ms | **$0.00** (Free Tier)| 15 req / min (1M TPM) | HTTP 429 $\rightarrow$ Tier 3 Heuristics |
| **Tier 2 (Free Cloud)** | **Cloudflare Workers AI**| `@cf/meta/llama-3-8b-instruct` | 150-450 ms | **$0.00** (Free Tier)| 10k neurons / day | Limit reached $\rightarrow$ Tier 3 Heuristics |
| **Tier 3 (Deterministic)**| **AHOS Rule Heuristic**| `deterministic-heuristic-v1` | **< 1 ms** | **$0.00** (CPU) | **Infinite** | **Deterministic Baseline Floor (Always Succeeds)** |
| *Optional Paid* | *Anthropic Claude* | *claude-3-5-sonnet* | *400-1200 ms* | *$3.00 / $15.00* | *Pay-as-you-go* | *Only if operator supplies ANTHROPIC_API_KEY* |
| *Optional Paid* | *OpenAI* | *gpt-4o-mini* | *250-600 ms* | *$0.15 / $0.60* | *Pay-as-you-go* | *Only if operator supplies OPENAI_API_KEY* |

---

## 3. Tiered Fallback & Resilience Algorithm

The AI router executes requests according to a strict priority hierarchy:

```python
async def route_ai_completion(prompt: str, schema: Type[T]) -> T:
    # 1. Try Local Ollama (Primary)
    if is_provider_healthy("ollama"):
        try:
            return await call_ollama(prompt, schema, timeout=12.0)
        except (TimeoutError, ConnectionError, SchemaValidationError) as e:
            record_provider_fault("ollama", e)

    # 2. Try Free Hosted Cloud APIs (Secondary)
    for cloud_provider in ["groq_free", "openrouter_free", "gemini_free"]:
        if is_provider_configured_and_healthy(cloud_provider):
            try:
                return await call_cloud_provider(
                    cloud_provider, prompt, schema, timeout=8.0
                )
            except Exception as e:
                record_provider_fault(cloud_provider, e)
                continue

    # 3. Deterministic Heuristic Floor (Guaranteed Fallback)
    # NEVER FAILS. Pure math and rule-based evaluation.
    return generate_deterministic_heuristic_evaluation(prompt, schema)
```

---

## 4. Anti-Hallucination & Schema Enforcement Guardrails

To ensure AI agents never corrupt data integrity or fabricate non-existent tokens:

1. **Deterministic Data Separation**:
   - The LLM receives pre-calculated metrics (RSI, liquidity reserve depth, holder Gini coefficient, honeypot test results).
   - The LLM is **FORBIDDEN** from performing basic arithmetic or inventing token statistics.
2. **Pydantic Schema Validation (Instructor Pattern)**:
   - Output must strictly parse into strongly typed schemas:
     ```python
     class AIHypothesisEvaluation(BaseModel):
         opportunity_score: float = Field(ge=0.0, le=100.0)
         bull_case_summary: str = Field(min_length=10, max_length=500)
         bear_risks: list[str] = Field(min_items=1)
         recommendation: Literal["WATCH", "RESEARCH", "PASS"]
         confidence: float = Field(ge=0.0, le=1.0)
     ```
3. **Error-Feedback Auto-Repair Loop**:
   - If a model produces invalid JSON or schema errors, the router catches the validation error string, prepends it to the prompt:
     `"Your previous output failed validation: {error_details}. Please fix the JSON output."`
   - Retries up to 2 times before gracefully stepping down to the heuristic tier.

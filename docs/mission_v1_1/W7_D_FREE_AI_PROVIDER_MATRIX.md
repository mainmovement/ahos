# FREE AI PROVIDER MATRIX (Deliverable D) — 2026-08-11
# $0/month law. No paid AI without explicit user authorization. Every status is probe-backed or UNKNOWN.
# Probes: PRB-20260811-AI-001 (reports/ai_provider_probe_20260811.json); sandbox site.

| Provider / model path | Cost | Key needed | Sandbox status (probe) | Iran accessibility | Role in chain |
|---|---|---|---|---|---|
| Ollama local (qwen2.5:7b-instruct, overridable) | free-local | none | DISABLED_NO_HOST (no server in sandbox) | LOCAL_IMMUNE | #1 when VPS exists (blocker ②) |
| GitHub Models (gpt-4o-mini) | free-tier (GitHub acct) | GITHUB_TOKEN | NEEDS_USER_KEY — not probed live | UNKNOWN (user probe reqs.) | #2 |
| Groq (llama-3.3-70b-versatile) | free-tier | GROQ_API_KEY | NEEDS_USER_KEY | UNKNOWN (signup may be geo-restricted) | #3 |
| Google AI Studio (gemini-2.0-flash, OpenAI-compat) | free-tier | GEMINI_API_KEY | NEEDS_USER_KEY | UNKNOWN — Google services are sanctioned in IR; likely filtered/rerouted; probe required | #4 |
| OpenRouter (`:free` models) | free-tier | OPENROUTER_API_KEY | NEEDS_USER_KEY | UNKNOWN | #5 |
| ~~Pollinations text (keyless)~~ | **REFUTED** | — | HTTP **402 Payment Required** (keyless tier GONE; site root 200) — verified twice 2026-08-11 | n/a | removed from chains; kept in registry as comment (no-silent-replacement law) |

## Findings (recorded, not hidden)
1. **No credible fully-keyless free LLM text API exists right now** (2026-08-11 evidence: pollinations
   402). The architecture therefore does NOT depend on keyless AI: chain = local first → free-tier
   keyed → DETERMINISTIC_ONLY. The degraded mode is first-class and test-pinned.
2. Cheapest realistic activation for the user: **one free GitHub account → GITHUB_TOKEN** (GitHub is
   generally reachable from Iran; UNKNOWN until user-side probe) or **Ollama on the future VPS**
   (zero network dependency). Both facts, no promises.
3. Re-probe protocol: engine/pal_probe.py --site user-iran covers data providers; the AI probe is
   telegram_ai/providers.AIPAL.chat on capability persian_parse — one call emits a probe-id record.

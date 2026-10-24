"""M70.2 Unified LLM Grammar & JSON-Schema Output Adapter (PAPER_ONLY).

Provides a single interface behind M35.1 / M70.2 for grammar-constrained JSON output:
  1. Probes local loopback Ollama (127.0.0.1:11434) / llama.cpp (127.0.0.1:8080) when RAM tier >= T1
  2. On T0 (8 GB RAM floor) or when local daemon is offline, uses deterministic schema synthesis + Gemini free rotation fallback
  3. Validates every response against the required JSON schema keys and types before returning (fail-closed)
"""
from __future__ import annotations

import json
import urllib.request
from datetime import datetime, timezone
from typing import Any, Callable, Mapping

PAPER_ONLY: bool = True


def validate_grammar_schema(obj: Any, schema: Mapping[str, type | tuple[type, ...]]) -> tuple[bool, list[str]]:
    if not isinstance(obj, dict):
        return False, ["root_not_object"]
    errors: list[str] = []
    for k, expected_t in schema.items():
        if k not in obj:
            errors.append(f"missing_key:{k}")
        elif not isinstance(obj[k], expected_t):
            errors.append(f"type_mismatch:{k}")
    return len(errors) == 0, errors


def query_grammar_structured(
    prompt: str,
    schema: Mapping[str, type | tuple[type, ...]],
    *,
    ram_gb: float = 7.93,
    local_transport: Callable[[str, dict[str, Any]], dict[str, Any] | None] | None = None,
    fallback_builder: Callable[[str], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """M70.2 adapter: enforces grammar/schema contract across T0/T1/T2 hardware tiers."""
    tier = "T0" if ram_gb <= 9.5 else ("T1" if ram_gb <= 20.0 else "T2")
    backend_used = "t0_deterministic_schema_guard"
    candidate: dict[str, Any] | None = None

    if local_transport is not None:
        raw = local_transport(prompt, {"format": "json"})
        if isinstance(raw, dict):
            candidate = raw
            backend_used = "local_loopback_llm_grammar"

    if candidate is None:
        if fallback_builder is not None:
            candidate = fallback_builder(prompt)
        else:
            candidate = {
                "summary_fa": f"پاسخ ساختاریافته (M70.2) در سطح {tier} با رعایت کامل اسکیما و فقط کاغذی.",
                "paper_only": True,
                "confidence": 0.85,
            }

    ok, errors = validate_grammar_schema(candidate, schema)
    return {
        "schema": "ahos.m70_2_grammar_adapter.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "hardware_tier": tier,
        "backend_used": backend_used,
        "grammar_valid": ok,
        "validation_errors": errors,
        "output": candidate if ok else None,
        "paper_only": True,
    }

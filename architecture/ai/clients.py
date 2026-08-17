#!/usr/bin/env python3
"""AHOS AI provider transport — OpenAI-compatible + Anthropic, stdlib only.

Every mainstream assistant now speaks the OpenAI chat-completions wire format, or
is one small adapter away from it:

    Ollama (local)   /v1/chat/completions   free, offline, Iran-immune
    Groq             /openai/v1             free tier
    Gemini           /v1beta/openai         free tier (AI Studio)
    OpenRouter       /api/v1                free models available
    GitHub Models    Azure inference        free with any GitHub account
    xAI / Grok       /v1                    paid
    OpenAI / ChatGPT /v1                    paid
    Anthropic/Claude /v1/messages           paid, different shape -> adapted here

LAWS
----
  - FREE FIRST: paid providers are excluded unless allow_paid=True is passed
    explicitly. The default council is free-only, honouring the $0 ceiling.
  - NO KEY, NO CALL: a provider without its env key is skipped silently, never
    attempted, never counted as a failure.
  - SECRETS NEVER LEAVE: keys are read from env at call time and are never
    logged, echoed, or embedded in a response envelope.
  - IRAN-RESILIENT: honours HTTPS_PROXY / ALL_PROXY; a blocked provider degrades
    to an availability=DOWN envelope instead of raising.
  - EVERY RESPONSE IS AN ENVELOPE: latency, http status, error state and a
    sha256 of the raw body, so the council can audit what it was told.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import yaml

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRY = ROOT / "config" / "ai_council_providers.yaml"

UA = {"User-Agent": "ahos-ai-council/1.0", "Content-Type": "application/json"}


@dataclass
class AIResponse:
    """Normalized envelope for one provider answer."""
    provider: str
    model: str | None
    availability: str                       # OK | DOWN | NO_KEY | SKIPPED_PAID
    content: str | None = None
    latency_ms: float | None = None
    http_status: int | None = None
    error_state: dict[str, Any] | None = None
    raw_sha256: str | None = None
    cost_class: str = "free"

    @property
    def ok(self) -> bool:
        return self.availability == "OK" and bool(self.content)

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider, "model": self.model,
            "availability": self.availability, "content": self.content,
            "latency_ms": self.latency_ms, "http_status": self.http_status,
            "error_state": self.error_state, "raw_sha256": self.raw_sha256,
            "cost_class": self.cost_class,
        }


class AIClient:
    """One provider. Speaks OpenAI-compatible or Anthropic wire format."""

    def __init__(self, name: str, spec: dict,
                 transport: Callable = urllib.request.urlopen):
        self.name = name
        self.spec = spec
        self.transport = transport

    # -- availability -------------------------------------------------------
    @property
    def key_env(self) -> str | None:
        return self.spec.get("key_env")

    @property
    def is_paid(self) -> bool:
        return str(self.spec.get("cost", "free")).lower().startswith("paid")

    def has_key(self) -> bool:
        env = self.key_env
        if not env:
            return True                       # local/keyless provider
        return bool(os.environ.get(env))

    # -- request building ---------------------------------------------------
    def _build(self, messages: list[dict], max_tokens: int) -> tuple[str, dict, bytes]:
        kind = self.spec.get("kind", "openai_compatible")
        base = str(self.spec.get("base_url", "")).rstrip("/")
        model = self.spec.get("model")
        key = os.environ.get(self.key_env) if self.key_env else None
        headers = dict(UA)

        if kind == "anthropic":
            url = f"{base}/v1/messages"
            headers["x-api-key"] = key or ""
            headers["anthropic-version"] = self.spec.get("api_version", "2023-06-01")
            system = "".join(m["content"] for m in messages if m.get("role") == "system")
            turns = [m for m in messages if m.get("role") != "system"]
            body = {"model": model, "max_tokens": max_tokens, "messages": turns}
            if system:
                body["system"] = system
        else:
            url = f"{base}/chat/completions"
            if key:
                headers["Authorization"] = f"Bearer {key}"
            body = {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": self.spec.get("temperature", 0.2),
            }
        return url, headers, json.dumps(body).encode("utf-8")

    @staticmethod
    def _extract(kind: str, payload: dict) -> str | None:
        try:
            if kind == "anthropic":
                blocks = payload.get("content") or []
                return "".join(b.get("text", "") for b in blocks) or None
            choices = payload.get("choices") or []
            if not choices:
                return None
            msg = choices[0].get("message") or {}
            return msg.get("content")
        except (AttributeError, IndexError, TypeError):
            return None

    # -- call ---------------------------------------------------------------
    def ask(self, messages: list[dict], max_tokens: int = 700,
            allow_paid: bool = False) -> AIResponse:
        cost_class = "paid" if self.is_paid else "free"
        model = self.spec.get("model")

        if self.is_paid and not allow_paid:
            return AIResponse(self.name, model, "SKIPPED_PAID", cost_class=cost_class,
                              error_state={"kind": "paid_excluded",
                                           "detail": "free-first law; pass allow_paid=True to enable"})
        if not self.has_key():
            return AIResponse(self.name, model, "NO_KEY", cost_class=cost_class,
                              error_state={"kind": "no_key",
                                           "detail": f"{self.key_env} is not set"})

        kind = self.spec.get("kind", "openai_compatible")
        timeout = float(self.spec.get("timeout_sec", 30))
        url, headers, data = self._build(messages, max_tokens)
        t0 = time.time()
        try:
            req = urllib.request.Request(url, data=data, headers=headers, method="POST")
            with self.transport(req, timeout=timeout) as resp:
                raw = resp.read()
                status = getattr(resp, "status", None)
            payload = json.loads(raw)
            content = self._extract(kind, payload)
            latency = (time.time() - t0) * 1000.0
            if not content:
                return AIResponse(self.name, model, "DOWN", latency_ms=latency,
                                  http_status=status, cost_class=cost_class,
                                  raw_sha256=hashlib.sha256(raw).hexdigest(),
                                  error_state={"kind": "empty_completion"})
            return AIResponse(self.name, model, "OK", content=content.strip(),
                              latency_ms=round(latency, 1), http_status=status,
                              raw_sha256=hashlib.sha256(raw).hexdigest(),
                              cost_class=cost_class)
        except urllib.error.HTTPError as e:
            return AIResponse(self.name, model, "DOWN",
                              latency_ms=(time.time() - t0) * 1000.0,
                              http_status=e.code, cost_class=cost_class,
                              error_state={"kind": "http_error", "detail": str(e.code)})
        except Exception as e:
            # Filtered, offline, TLS-blocked, malformed JSON — all recorded, never raised.
            return AIResponse(self.name, model, "DOWN",
                              latency_ms=(time.time() - t0) * 1000.0,
                              cost_class=cost_class,
                              error_state={"kind": type(e).__name__,
                                           "detail": str(e)[:160]})


def load_registry(path: str | Path = DEFAULT_REGISTRY) -> dict:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}


def build_clients_from_registry(path: str | Path = DEFAULT_REGISTRY,
                                transport: Callable = urllib.request.urlopen
                                ) -> list[AIClient]:
    """Instantiate one client per registry entry, in declared (free-first) order."""
    reg = load_registry(path)
    return [AIClient(name, spec, transport=transport)
            for name, spec in (reg.get("providers") or {}).items()
            if spec.get("enabled", True)]

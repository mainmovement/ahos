#!/usr/bin/env python3
"""AHOS AI-PAL — provider-agnostic FREE-FIRST AI layer (Wave-7 §13/§14/§16).

Envelope laws mirror discovery PAL: every call returns a normalized envelope with
availability/latency/error_state/raw sha256. Fallback law: ordered chain per capability;
if every provider is unavailable the answer is DEGRADED with mode=DETERMINISTIC_ONLY —
the deterministic parser + AHOS data still answer; AI is advisory, never authoritative.

Free-first order (registry): local self-hosted -> keyless public -> free-tier keyed.
Iran resilience: chain never collapses because one provider is blocked; DETERMINISTIC_ONLY
is always a valid operating mode. NO PAID PROVIDER may be added without user authorization.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import yaml

DEFAULT_REGISTRY = Path(__file__).resolve().parent / "ai_providers.yaml"
UA = {"User-Agent": "ahos-ai-pal/1.0"}


def load_registry(path: Path | str = DEFAULT_REGISTRY) -> dict:
    return yaml.safe_load(Path(path).read_text())


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


class AIProviderClient:
    def __init__(self, name: str, spec: dict, transport=urllib.request.urlopen):
        self.name, self.spec = name, spec
        self.transport = transport

    def available(self) -> bool:
        """Keyless/local providers are structurally callable; keyed ones need their env key."""
        key_env = self.spec.get("key_env")
        if key_env and not os.environ.get(key_env):
            return False
        return True

    def chat(self, messages: list[dict], max_tokens: int = 512) -> dict:
        env = {"provider_id": self.name, "model": self.spec.get("model"),
               "availability": "DOWN", "latency_ms": None, "content": None,
               "http_status": None, "error_state": None, "raw_sha256": None}
        if not self.available():
            env["error_state"] = {"kind": "no_key", "message": f"{self.spec.get('key_env')} not set"}
            return env
        kind = self.spec.get("kind")
        timeout = self.spec.get("timeout_sec", 30)
        t0 = time.time()
        try:
            if kind == "openai_compatible":
                body = json.dumps({"model": self.spec["model"], "messages": messages,
                                   "max_tokens": max_tokens, "temperature": 0.2}).encode()
                key = os.environ.get(self.spec.get("key_env") or "", "")
                headers = {**UA, "Content-Type": "application/json",
                           **({"Authorization": f"Bearer {key}"} if key else {})}
                url = self.spec["base_url"].rstrip("/") + "/chat/completions"
                req = urllib.request.Request(url, data=body, headers=headers)
                with self.transport(req, timeout=timeout) as r:
                    raw = r.read()
                    env["http_status"] = r.status
                payload = json.loads(raw)
                env["content"] = payload["choices"][0]["message"]["content"]
            elif kind == "pollinations_get":
                prompt = "\n".join(f"{m['role']}: {m['content']}" for m in messages)
                url = (self.spec["base_url"].rstrip("/") + "/" +
                       urllib.parse.quote(prompt) + "?model=" + urllib.parse.quote(self.spec["model"]))
                req = urllib.request.Request(url, headers=UA)
                with self.transport(req, timeout=timeout) as r:
                    raw = r.read()
                    env["http_status"] = r.status
                env["content"] = raw.decode("utf-8", errors="replace")
            else:
                raise ValueError(f"unknown provider kind: {kind}")
            env.update(availability="OK", latency_ms=round((time.time() - t0) * 1000),
                       raw_sha256=_sha(raw if isinstance(raw, bytes) else raw.encode()))
        except urllib.error.HTTPError as e:
            env.update(http_status=e.code,
                       error_state={"kind": "http_error", "message": str(e)[:200]})
        except Exception as e:
            env.update(error_state={"kind": "network_error",
                                    "message": f"{type(e).__name__}: {e}"[:200]})
        return env


class AIPAL:
    def __init__(self, registry_path: Path | str = DEFAULT_REGISTRY,
                 transport=urllib.request.urlopen):
        reg = load_registry(registry_path)
        self.capabilities = reg.get("capabilities", {})
        self.clients = {n: AIProviderClient(n, s, transport=transport)
                        for n, s in reg.get("providers", {}).items()}

    def chat(self, capability: str, messages: list[dict], max_tokens: int = 512) -> dict:
        chain = (self.capabilities.get(capability, {}) or {}).get("chain", [])
        if not chain:
            raise KeyError(f"AI capability '{capability}' not registered")
        attempts = []
        for name in chain:
            cli = self.clients[name]
            env = cli.chat(messages, max_tokens=max_tokens)
            attempts.append({"provider": name, "availability": env["availability"],
                             "error": (env.get("error_state") or {}).get("kind")})
            if env["availability"] == "OK":
                env["attempts"], env["mode"] = attempts, "AI_ASSISTED"
                return env
        return {"provider_id": None, "model": None, "availability": "DEGRADED",
                "latency_ms": None, "content": None, "http_status": None,
                "error_state": {"kind": "all_ai_providers_down",
                                "message": "deterministic-only mode"},
                "raw_sha256": None, "attempts": attempts, "mode": "DETERMINISTIC_ONLY"}


# Response-frame law for the command layer (consumed by bot glue in Phase 6):
ADVISORY_DISCLAIMER_FA = "این توضیح با کمک هوش مصنوعی تولید شده و صرفاً راهنماست؛ تصمیم نهایی با کاربر است."

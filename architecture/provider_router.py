#!/usr/bin/env python3
"""AHOS W11 Lane-B — AI provider router (contract ai_provider_contract_v1).

Laws implemented:
- FREE_FIRST: cost=0 first; paid providers are excluded unless allow_paid is set.
- NO superiority belief: a strength claim without probe_ref counts for NOTHING.
- NO silent availability: selection only from availability=OK providers; health is probed or UNKNOWN.
- DETERMINISTIC FLOOR: no candidates => DETERMINISTIC_ONLY verdict (never an error, never a halt).
- Circuit breaker per provider: failures >= threshold => OPEN; HALF_OPEN after cooldown (time injected).
- Deterministic: same registry + same health + same now => same selection (no wall-clock, no randomness).

This module NEVER imports Lane-A packages (lane isolation is test-pinned).
It performs NO network I/O itself — probing/health results are injected.
"""
from __future__ import annotations

import hashlib
import json
import time
from functools import lru_cache
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "config" / "ai_provider_registry.yaml"
CONTRACT_PATH = ROOT / "contracts" / "ai_provider_contract_v1.json"

FLOOR_RESULT = {"mode": "DETERMINISTIC_ONLY", "provider": None, "reason": "no_available_provider"}


@lru_cache(maxsize=8)
def load_registry(path: str | Path = REGISTRY_PATH) -> dict:
    """Load + parse the AI provider registry (YAML).

    W40: memoized. The registry is static repository configuration — it only
    changes when the repo changes — so re-reading and re-parsing the file on
    every call (the health snapshot calls this per cadence; AI routing per
    request) is pure waste. The cache is keyed on the resolved path, so a
    genuinely different path still parses; a process restart picks up a file
    edit. Callers must treat the returned dict as read-only.
    """
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def load_contract(path: str | Path = CONTRACT_PATH) -> dict:
    return json.loads(Path(path).read_text(encoding='utf-8'))


def validate_registry(reg: dict, contract: dict | None = None) -> list[str]:
    """Validate provider registry against the contract. [] = conformant."""
    contract = contract or load_contract()
    errs: list[str] = []
    allowed_avail = set(contract["enums"]["availability"])
    allowed_caps = set(contract["capabilities"])
    req = set(contract["provider_spec_fields"]["required"])
    reg_caps = set(reg.get("capabilities", []))
    if not reg_caps <= allowed_caps:
        errs.append(f"registry capabilities not subset of contract: {sorted(reg_caps - allowed_caps)}")
    for pid, spec in (reg.get("providers") or {}).items():
        missing = req - set(spec)
        # provider_id equals the registry mapping key by convention (no duplicated literals) —
        # contract note: the key IS the id.
        missing.discard("provider_id") if pid else None
        if missing:
            errs.append(f"{pid}: missing spec fields {sorted(missing)}")
        if spec.get("availability") not in allowed_avail:
            errs.append(f"{pid}: availability={spec.get('availability')} not in enum")
        claim_caps = set(spec.get("capabilities_claimed") or [])
        if not claim_caps <= allowed_caps:
            errs.append(f"{pid}: claims unknown capabilities {sorted(claim_caps - allowed_caps)}")
        for s in spec.get("strengths") or []:
            if not s.get("probe_ref"):
                # legal but ignored by routing — the contract demands we FLAG it
                errs.append(f"{pid}: strength claim without probe_ref (UNPROBED: {s.get('capability')}) — will be ignored by router, must stay out of routing weight")
    return errs


class CircuitBreaker:
    """Per-provider breaker. States: CLOSED -> OPEN (failures>=threshold) -> HALF_OPEN (after cooldown) -> CLOSED (on success)."""

    def __init__(self, threshold: int = 3, cooldown_s: float = 300.0):
        self.threshold = threshold
        self.cooldown_s = cooldown_s
        self._state: dict[str, dict] = {}

    def state(self, provider: str, now: float) -> str:
        st = self._state.get(provider)
        if not st:
            return "CLOSED"
        if st["state"] == "OPEN" and now - st["opened_ts"] >= self.cooldown_s:
            st["state"] = "HALF_OPEN"
        return st["state"]

    def allow(self, provider: str, now: float) -> bool:
        return self.state(provider, now) != "OPEN"

    def record_success(self, provider: str) -> None:
        self._state[provider] = {"state": "CLOSED", "failures": 0, "opened_ts": None}

    def record_failure(self, provider: str, now: float) -> str:
        st = self._state.get(provider, {"state": "CLOSED", "failures": 0, "opened_ts": None})
        st["failures"] += 1
        if st["state"] == "HALF_OPEN" or st["failures"] >= self.threshold:
            st["state"] = "OPEN"
            st["opened_ts"] = now
        self._state[provider] = st
        return st["state"]


def _is_free(spec: dict) -> bool:
    c = spec.get("cost_per_1k_usd")
    return isinstance(c, (int, float)) and c == 0


def _is_paid(spec: dict) -> bool:
    c = spec.get("cost_per_1k_usd")
    return c == "DECLARED_PAID" or (isinstance(c, (int, float)) and c > 0)


class ProviderRouter:
    """TASK -> CAPABILITY FILTER -> HEALTH -> COST -> CONTEXT -> PROBE EVIDENCE -> SELECTION."""

    def __init__(self, registry: dict | None = None, *, allow_paid: bool = False,
                 breaker: CircuitBreaker | None = None):
        self.reg = registry or load_registry()
        cost_law = self.reg.get("cost_budget", {})
        self.allow_paid = bool(cost_law.get("allow_paid", False)) if not allow_paid else True
        self.breaker = breaker or CircuitBreaker()
        self.providers = self.reg.get("providers") or {}

    def candidates(self, capability: str) -> list[str]:
        if capability not in self.reg.get("capabilities", []):
            raise KeyError(f"unregistered capability lane: {capability}")
        return [pid for pid, spec in self.providers.items()
                if capability in (spec.get("capabilities_claimed") or [])]

    def route(self, capability: str, *, context_tokens_needed: int = 0,
              health: dict[str, str] | None = None, now: float | None = None) -> dict:
        """Select a provider honestly. health = {provider: 'HEALTHY'|'UNHEALTHY'|'UNKNOWN'} from probes.
        Providers with availability!=OK are excluded up front (NO_KEY/REFUTED/etc are evidence states,
        not routes). Deterministic floor when nobody qualifies."""
        now = time.time() if now is None else now
        health = health or {}
        eligible = []
        excluded: dict[str, str] = {}
        for pid in self.candidates(capability):
            spec = self.providers[pid]
            if spec.get("availability") != "OK":
                excluded[pid] = f"availability={spec.get('availability')}"
                continue
            if _is_paid(spec) and not self.allow_paid:
                excluded[pid] = "paid excluded (allow_paid=false)"
                continue
            if not self.breaker.allow(pid, now):
                excluded[pid] = "circuit OPEN"
                continue
            if health.get(pid, "UNKNOWN") != "HEALTHY":
                excluded[pid] = f"health={health.get(pid, 'UNKNOWN')} (unprobed is not routable)"
                continue
            if context_tokens_needed and spec.get("context_tokens", 0) < context_tokens_needed:
                excluded[pid] = "context too small"
                continue
            eligible.append(pid)
        if not eligible:
            return {**FLOOR_RESULT, "capability": capability, "excluded": excluded,
                    "evidence": ["floor law: DETERMINISTIC_ONLY"], "advisory_only": True}
        # FREE_FIRST ordering: free before paid; within a tier, fewest measured failures first;
        # probe-backed strengths may promote a provider ONLY with probe_ref evidence (contract law).
        def rank(pid: str):
            spec = self.providers[pid]
            st = self.breaker._state.get(pid, {"failures": 0})
            strength_boost = 0
            for s in spec.get("strengths") or []:
                if s.get("capability") == capability and s.get("probe_ref"):
                    strength_boost = 1
            return (0 if _is_free(spec) else 1, -strength_boost, st["failures"], pid)
        ranked = sorted(eligible, key=rank)
        chosen = ranked[0]
        spec = self.providers[chosen]
        return {"mode": "PROVIDER_SELECTED", "provider": chosen, "capability": capability,
                "model": spec.get("model"), "cost_per_1k_usd": spec.get("cost_per_1k_usd"),
                "ranking": ranked, "excluded": excluded,
                "evidence": spec.get("probe_ids") or [],
                "advisory_only": True, "note": "AI output is advisory; numbers require evidence_refs"}

    @staticmethod
    def make_input_hash(payload: str) -> str:
        return hashlib.sha256(payload.encode()).hexdigest()

    @staticmethod
    def validate_response_envelope(env: dict) -> list[str]:
        """AI safety contract enforcement. [] = conformant."""
        contract = load_contract()
        errs: list[str] = []
        for f in contract["response_envelope_fields"]:
            if f not in env:
                errs.append(f"missing envelope field: {f}")
        if not env.get("probe_id"):
            errs.append("probe_id required (probe-id law applies to AI providers)")
        # numeric provenance law: every numeric claim must trace to evidence_refs
        numerics = env.get("numeric_claims") or []
        refs = env.get("evidence_refs") or []
        if numerics and not refs:
            errs.append("numeric_claims present but evidence_refs empty => INVALID")
        for nc in numerics:
            if not nc.get("evidence_ref"):
                errs.append(f"numeric claim lacks evidence_ref => INVALID: {nc.get('label', '?')}")
        return errs

"""
providers.base_provider — Formal provider contract for AHOS v2.

Every v2 provider implements three methods:

    fetch(chain, limit)   — retrieve raw payloads from the upstream (or synthetic for tests)
    health_check()        — liveness probe (no network assumption; must not raise)
    normalize(raw)        — convert raw payloads → list[Observation] (pure, no I/O)

Additional helpers:
    validate_contract(provider) — static verifier used by tests & runtime probes
    fetch_normalized(chain, limit) — convenience that composes fetch+normalize

Design notes
------------
* fetch() and normalize() are split so scoring, hindsight, and paper lab can
  use normalize() deterministically on archived raw_payloads without re-fetching.
* Evidence discipline: normalize() MUST anchor every Observation to an Evidence
  with source, timestamp, confidence, verification_status, raw_reference.
* No trading primitives: any fetch that attempts to call exchange order APIs
  is a SafetyViolation (checked in core.governance).

Example minimal provider (for tests):

    class MockProvider(BaseProvider):
        provider_id = "mock"
        def fetch(self, chain="solana", limit=10): return ProviderResult(...)
        def health_check(self): return ProviderHealth(ok=True)
        def normalize(self, raw): return [...]
"""

from __future__ import annotations

import inspect
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ProviderHealth:
    ok: bool
    provider_id: str = "unknown"
    latency_ms: float = 0.0
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"ok": self.ok, "provider_id": self.provider_id, "latency_ms": self.latency_ms, "message": self.message, "details": dict(self.details)}


@dataclass(frozen=True)
class ProviderResult:
    """
    Result of fetch() before normalization.

    Attributes
    ----------
    provider_id: originating provider string.
    raw: list of raw payload dicts / bytes (each will be normalized individually).
    retrieved_at: epoch seconds when fetch completed.
    latency_ms: wall-clock time spent fetching.
    status: OK | DEGRADED | DOWN | RATE_LIMITED (mirrors PAL envelope).
    error: optional error description when status != OK.
    raw_refs: optional list of raw_reference shas (populated by fetch impl).
    """

    provider_id: str
    raw: list[Any] = field(default_factory=list)
    retrieved_at: float = field(default_factory=time.time)
    latency_ms: float = 0.0
    status: str = "OK"
    error: str | None = None
    raw_refs: list[str] = field(default_factory=list)

    def is_ok(self) -> bool:
        return self.status == "OK" and self.error is None


class BaseProvider(ABC):
    """
    Abstract provider contract — all v2 providers must subclass this.

    Subclasses MUST set a non-empty class attribute `provider_id` (or override
    the property) and implement fetch(), health_check(), normalize() with the
    signatures below. See validate_contract() for the conformance test used in CI.
    """

    # Preferred: class attribute; fallback is property
    provider_id: str = ""  # subclasses set, e.g. "dexscreener"

    @property
    def id(self) -> str:  # compatibility alias
        return getattr(self, "provider_id", "") or self.__class__.__name__

    # ------------------------------------------------------------------
    # Abstract interface — exactly these three names required by spec
    # ------------------------------------------------------------------

    @abstractmethod
    def fetch(self, chain: str = "solana", limit: int = 10, **kwargs: Any) -> ProviderResult:
        """
        Retrieve raw payloads.

        Parameters
        ----------
        chain: normalized chain id (e.g. "solana", "ethereum", "base").
        limit: maximum raw items to retrieve (advisory, must be respected).
        **kwargs: optional provider-specific params (must have defaults).

        Returns
        -------
        ProviderResult with status, raw list, latency, errors.
        Must never raise on provider failure — return DOWN/DEGRADED result.
        """
        raise NotImplementedError

    @abstractmethod
    def health_check(self) -> ProviderHealth:
        """
        Liveness probe — must not raise.

        Returns
        -------
        ProviderHealth(ok=True means healthy). latency_ms should reflect
        probe cost; message may contain diagnostic when ok=False.
        """
        raise NotImplementedError

    @abstractmethod
    def normalize(self, raw: Any) -> list[Any]:
        """
        Pure normalization: raw payload (single item or list or ProviderResult)
        → list[core.models.observation.Observation].

        Constraints
        -----------
        * Pure: no I/O, no network, deterministic given inputs (clock injected via raw).
        * Evidence-anchored: every Observation carries Evidence with source,
          timestamp, confidence, verification_status, raw_reference. Missing fields → None/UNKNOWN.
        * Empty or unparseable → [] (not exception), error reflected in enclave if needed.
        """
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Convenience composition
    # ------------------------------------------------------------------

    def fetch_normalized(self, chain: str = "solana", limit: int = 10, **kwargs: Any) -> list[Any]:
        """fetch() followed by normalize() — honors limit and swallows normalization errors gracefully."""
        result = self.fetch(chain=chain, limit=limit, **kwargs)
        if result.status == "DOWN" or not result.raw:
            return []
        try:
            # normalize may accept ProviderResult or list[Any]
            obs: list[Any] = self.normalize(result)  # type: ignore[arg-type]
            if obs is not None and not isinstance(obs, list):
                obs = self.normalize(result.raw)
        except Exception:
            # Fallback: try list path
            try:
                obs = self.normalize(result.raw)  # type: ignore[arg-type]
            except Exception:
                return []
        # Ensure limit honored post-normalization
        return obs[:limit] if limit and isinstance(obs, list) else obs or []

    # ------------------------------------------------------------------
    # Contract validation — used by tests & runtime registry
    # ------------------------------------------------------------------

    @classmethod
    def validate_contract(cls, instance: Any = None) -> dict[str, Any]:
        """
        Validate that `instance` (or `cls()`) satisfies the BaseProvider contract.

        Checks:
        * provider_id non-empty string
        * fetch, health_check, normalize are implemented (not abstract) and callable
        * fetch signature accepts (chain, limit) and returns ProviderResult-like
        * health_check signature zero-arg (plus self) and returns ProviderHealth-like
        * normalize accepts single positional payload arg

        Returns a report dict:
            {"valid": bool, "provider_id": str, "checks": {...}, "errors": [str, ...]}

        Never raises — errors are collected into the report.
        """
        errors: list[str] = []
        checks: dict[str, Any] = {}

        # Resolve instance
        obj: Any
        if instance is not None:
            obj = instance
        else:
            try:
                obj = cls()  # type: ignore[call-arg]
            except Exception as exc:
                return {
                    "valid": False,
                    "provider_id": getattr(cls, "provider_id", ""),
                    "checks": {"instantiable": False},
                    "errors": [f"cannot instantiate {cls.__name__}: {exc}"],
                }

        # provider_id — must be explicit non-empty string attribute; do not accept class-name fallback
        raw_pid = getattr(obj, "provider_id", None)
        # Also accept 'id' property only when provider_id not set at all (not empty string)
        if raw_pid is None:
            raw_pid = getattr(obj, "id", None)
        pid = raw_pid if isinstance(raw_pid, str) else None
        checks["provider_id_present"] = bool(pid and pid.strip())
        if not checks["provider_id_present"]:
            errors.append("provider_id must be non-empty string (set class attr provider_id)")
        else:
            checks["provider_id"] = pid.strip()  # type: ignore[union-attr]
            pid = pid.strip()  # type: ignore[union-attr]

        # Abstract methods
        for method in ("fetch", "health_check", "normalize"):
            attr = getattr(obj, method, None)
            exists = callable(attr)
            checks[f"has_{method}"] = exists
            if not exists:
                errors.append(f"missing required method {method}()")
                continue

            sig = None
            try:
                sig = inspect.signature(attr)
            except Exception:
                pass

            if method == "fetch" and sig:
                params = list(sig.parameters.values())
                # filter self, chain, limit, kwargs
                names = [p.name for p in params if p.name != "self"]
                has_chain = "chain" in names
                has_limit = "limit" in names
                checks["fetch_accepts_chain_limit"] = has_chain and has_limit
                if not (has_chain and has_limit):
                    errors.append("fetch() must accept (chain, limit, **kwargs)")
            elif method == "health_check" and sig:
                # health_check should not require args beyond self
                required = [p for p in sig.parameters.values() if p.name != "self" and p.default is inspect._empty and p.kind not in (inspect.Parameter.VAR_KEYWORD, inspect.Parameter.VAR_POSITIONAL)]
                checks["health_check_no_required_args"] = len(required) == 0
                if len(required) != 0:
                    errors.append("health_check() must not require arguments")
            elif method == "normalize" and sig:
                params = [p for p in sig.parameters.values() if p.name != "self"]
                # must accept at least one payload arg
                checks["normalize_accepts_payload"] = len(params) >= 1
                if len(params) < 1:
                    errors.append("normalize() must accept payload argument")

            # Check not abstract (i.e., not the base ABC stub)
            is_abstract = getattr(attr, "__isabstractmethod__", False)
            checks[f"{method}_not_abstract"] = not is_abstract
            if is_abstract:
                errors.append(f"{method}() is still abstract — must be implemented")

        # Try-call health_check and fetch on mock to catch return-type issues
        if checks.get("has_health_check"):
            try:
                h = obj.health_check()
                checks["health_check_returns_ok"] = hasattr(h, "ok") and isinstance(getattr(h, "ok", None), bool)
                if not checks["health_check_returns_ok"]:
                    errors.append("health_check() must return ProviderHealth (or object with .ok: bool)")
            except Exception as exc:
                errors.append(f"health_check() raised: {type(exc).__name__}: {exc}")
                checks["health_check_returns_ok"] = False

        if checks.get("has_fetch"):
            try:
                r = obj.fetch(chain="solana", limit=1)
                checks["fetch_returns_ok"] = hasattr(r, "raw") and hasattr(r, "status")
                if not checks["fetch_returns_ok"]:
                    errors.append("fetch() must return ProviderResult (or object with .raw/.status)")
            except TypeError as exc:
                # Might require extra kwargs — try without args
                if "required positional" in str(exc):
                    try:
                        r2 = obj.fetch()  # type: ignore[call-arg]
                        checks["fetch_returns_ok"] = hasattr(r2, "raw")
                    except Exception as exc2:
                        errors.append(f"fetch() call failed: {exc2}")
                else:
                    errors.append(f"fetch() raised: {exc}")
            except Exception as exc:
                errors.append(f"fetch() raised: {type(exc).__name__}: {exc}")
                checks["fetch_returns_ok"] = False

        return {
            "valid": len(errors) == 0,
            "provider_id": pid.strip() if pid and isinstance(pid, str) else "",
            "checks": checks,
            "errors": errors,
        }


#!/usr/bin/env python3
"""AHOS Provider Abstraction Layer (PAL) v1 — Mission v1.1 §4/§5.
Free-first ordered chains (per-capability), normalized envelope, token-bucket rate limiting,
circuit breaker, optional TTL cache, dual timestamps, raw-payload archiving.
No provider schema leaks into the core. Errors surface as error_state — never silent.

Envelope fields (contract, Mission §4):
  provider_id, endpoint, chain, capability, data_type, freshness_sec,
  rate_limit, availability (OK|DEGRADED|DOWN), confidence,
  source_timestamp, retrieval_timestamp, error_state, payload
"""
from __future__ import annotations
import time, json, hashlib, urllib.request, urllib.error
from pathlib import Path

DISCOVERY_DIR = Path(__file__).resolve().parent
DEFAULT_REGISTRY = DISCOVERY_DIR / "providers.yaml"


def load_registry(path: Path | str = DEFAULT_REGISTRY) -> dict:
    """Load providers.yaml with strict shape validation (fail loud on structural surprises)."""
    import yaml
    reg = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(reg, dict) or "providers" not in reg or "capabilities" not in reg:
        raise ValueError("registry must contain top-level 'providers' and 'capabilities' maps")
    for name, spec in reg["providers"].items():
        if not isinstance(spec, dict) or "base_url" not in spec:
            raise ValueError(f"provider '{name}' missing base_url")
    for cap, cfg in reg["capabilities"].items():
        chain_list = (cfg or {}).get("chain") if isinstance(cfg, dict) else None
        if not isinstance(chain_list, list) or not chain_list:
            raise ValueError(f"capability '{cap}' needs a non-empty ordered 'chain' list")
        for pname in chain_list:
            if pname not in reg["providers"]:
                raise ValueError(f"capability '{cap}' references unknown provider '{pname}'")
    return reg


class Bucket:
    """Simple token bucket: capacity=burst, refill rate=rpm/60 tokens per second."""
    def __init__(self, rpm: int, burst: int):
        self.rate = max(rpm, 1) / 60.0
        self.capacity = max(burst, 1)
        self.tokens = float(self.capacity)
        self.ts = time.monotonic()
    def take(self):
        now = time.monotonic()
        self.tokens = min(self.capacity, self.tokens + (now - self.ts) * self.rate)
        self.ts = now
        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return True
        return False
    def wait_for(self, timeout: float):
        t0 = time.monotonic()
        while time.monotonic() - t0 < timeout:
            if self.take():
                return True
            time.sleep(0.05)
        return False


class Breaker:
    def __init__(self, fail_threshold: int, cooldown_sec: float):
        self.fail_threshold = fail_threshold
        self.cooldown = cooldown_sec
        self.consecutive_failures = 0
        self.opened_at: float | None = None
    def allow(self) -> bool:
        if self.opened_at is None:
            return True
        if time.monotonic() - self.opened_at >= self.cooldown:
            return True  # half-open probe allowed
        return False
    def on_success(self):
        self.consecutive_failures = 0
        self.opened_at = None
    def on_failure(self):
        self.consecutive_failures += 1
        if self.consecutive_failures >= self.fail_threshold and self.opened_at is None:
            self.opened_at = time.monotonic()
    @property
    def open(self) -> bool:
        return self.opened_at is not None and (time.monotonic() - self.opened_at) < self.cooldown


class ProviderClient:
    def __init__(self, name: str, spec: dict, cache_dir: Path | None = None, sleep=time.sleep):
        self.name = name
        self.spec = spec
        rate = spec.get("rate", {}) or {}
        br = spec.get("breaker", {}) or {}
        self.bucket = Bucket(rate.get("rpm", 30), rate.get("burst", 1))
        self.breaker = Breaker(br.get("fail_threshold", 3), br.get("cooldown_sec", 120))
        self.timeout = spec.get("timeout_sec", 12)
        self.cache_ttl = spec.get("cache_ttl_sec", 0)
        self._cache: dict[str, tuple[float, bytes]] = {}
        self.sleep = sleep

    def _endpoint(self, path_key: str, **fmt) -> str:
        base = self.spec["base_url"].rstrip("/")
        path = self.spec["path_templates"][path_key]
        if "chain" in fmt and "chain_map" in self.spec:
            fmt["chain"] = self.spec["chain_map"].get(fmt["chain"], fmt["chain"])
        if "chain" in fmt and "chain_num_map" in self.spec:
            fmt["chain_num"] = self.spec["chain_num_map"].get(fmt["chain"])
            fmt.pop("chain", None)
        return base + path.format(**fmt)

    def fetch(self, path_key: str, capability: str, chain: str | None = None,
              data_type: str = "json", now: float | None = None, **fmt) -> dict:
        """Returns the normalized envelope. `now` injectable for deterministic tests."""
        retrieval_ts = time.time() if now is None else now
        url = self._endpoint(path_key, chain=chain, **fmt)
        env = {
            "provider_id": (self.spec.get("provider_id") or self.name),
            "endpoint": url, "chain": chain, "capability": capability,
            "data_type": data_type, "freshness_sec": None,
            "rate_limit": {"rpm": self.spec.get("rate", {}).get("rpm")},
            "availability": "DOWN", "confidence": "LOW",
            "source_timestamp": None, "retrieval_timestamp": retrieval_ts,
            "error_state": None, "payload": None, "http_status": None,
            "raw_sha256": None,
        }
        if not self.breaker.allow():
            env["error_state"] = {"kind": "breaker_open", "message": "circuit open; fail-fast"}
            env["availability"] = "DOWN"
            return env
        cache_key = url
        if self.cache_ttl and cache_key in self._cache:
            ts, body = self._cache[cache_key]
            if retrieval_ts - ts <= self.cache_ttl:
                env.update(payload=json.loads(body), raw_sha256=hashlib.sha256(body).hexdigest(),
                           availability="OK", confidence="MED",
                           freshness_sec=round(retrieval_ts - ts, 3), http_status=200,
                           error_state={"kind": "cache_served", "message": "served from TTL cache"})
                return env
        if not self.bucket.wait_for(timeout=10.0):
            env["error_state"] = {"kind": "rate_starved", "message": "local budget exhausted"}
            return env
        req = urllib.request.Request(url, headers={"User-Agent": "ahos-discovery/1.1"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                body = r.read()
                env["http_status"] = r.status
        except urllib.error.HTTPError as e:
            self.breaker.on_failure()
            env["error_state"] = {"kind": "http_error", "message": str(e), "http_status": e.code}
            env["http_status"] = e.code
            return env
        except Exception as e:  # timeouts, DNS, TLS ...
            self.breaker.on_failure()
            env["error_state"] = {"kind": "network_error", "message": f"{type(e).__name__}: {e}"}
            return env
        self.breaker.on_success()
        env["raw_sha256"] = hashlib.sha256(body).hexdigest()
        try:
            env["payload"] = json.loads(body)
        except Exception as e:
            env["error_state"] = {"kind": "parse_error", "message": str(e)}
            env["availability"] = "DEGRADED"
            return env
        env["availability"] = "OK"
        env["confidence"] = "HIGH"
        if self.cache_ttl:
            self._cache[cache_key] = (retrieval_ts, body)
        return env


class PAL:
    """Ordered per-capability chains with fallback. First OK envelope wins;
    DEGRADED envelopes fall through but are remembered if everything else fails."""
    def __init__(self, registry_path: Path | str = DEFAULT_REGISTRY):
        reg = load_registry(registry_path)
        self.registry = reg
        self.capabilities = reg.get("capabilities", {})
        self.clients = {name: ProviderClient(name, spec) for name, spec in reg.get("providers", {}).items()}

    def call(self, capability: str, path_key: str, chain: str | None = None,
             data_type: str = "json", now: float | None = None, **fmt) -> dict:
        chain_list = (self.capabilities.get(capability, {}) or {}).get("chain", [])
        if not chain_list:
            raise KeyError(f"capability '{capability}' not registered")
        degraded: list[dict] = []
        attempts = []
        for name in chain_list:
            cli = self.clients[name]
            if cli.breaker.open:
                attempts.append({"provider": name, "skipped": "breaker_open"})
                continue
            env = cli.fetch(path_key, capability, chain=chain, data_type=data_type, now=now, **fmt)
            attempts.append({"provider": name, "availability": env["availability"],
                             "error": (env.get("error_state") or {}).get("kind")})
            if env["availability"] == "OK":
                env["attempts"] = attempts
                return env
            if env["availability"] == "DEGRADED":
                degraded.append(env)
        if degraded:
            d = degraded[0]
            d["attempts"] = attempts
            return d
        # everything failed: synthesized DOWN envelope (uniform contract)
        env = {"provider_id": chain_list[0], "endpoint": None, "chain": chain,
               "capability": capability, "data_type": data_type, "freshness_sec": None,
               "rate_limit": None, "availability": "DOWN", "confidence": "LOW",
               "source_timestamp": None, "retrieval_timestamp": now or time.time(),
               "error_state": {"kind": "all_providers_down", "message": str(attempts)},
               "payload": None, "http_status": None, "raw_sha256": None}
        env["attempts"] = attempts
        return env

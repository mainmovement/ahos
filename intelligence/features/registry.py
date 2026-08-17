"""
intelligence.features.registry — Versioned Feature Registry (Evidence-anchored)

Every feature must contain:
  - name: machine-readable identifier (e.g. "price_momentum_6h")
  - description: human-readable purpose (Persian allowed, but registry stores English source + Persian display)
  - source_evidence: description of required Evidence source(s) (e.g. "dexscreener:price_usd", "security_gate:is_honeypot")
  - calculation_method: string identifier of the calculation (e.g. "relative_change", "log_ratio", "threshold_check")
                       plus optional callable for execution (pure function: Evidence -> float | None)
  - version: semantic version string (e.g. "1.0.0") — bump on formula change, not on threshold tuning

Design:
  - Registry is append-only per version: (name, version) is unique, old versions are never mutated.
  - Features are frozen dataclasses.
  - Calculation method is stored as a string for audit; callable is optional and must be pure (Evidence -> value).
  - Source evidence is stored as a string descriptor referencing Evidence.source, not raw data.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field, asdict
from typing import Any, Callable, Dict, List, Optional

from core.models.evidence import Evidence

# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

_NAME_RE = re.compile(r"^[a-z][a-z0-9_]{2,49}$")
_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")


def _validate_name(name: str) -> None:
    if not isinstance(name, str) or not _NAME_RE.match(name):
        raise ValueError(f"Feature name must match {_NAME_RE.pattern}, got {name!r}")


def _validate_version(version: str) -> None:
    if not isinstance(version, str) or not _SEMVER_RE.match(version):
        raise ValueError(f"Feature version must be semver, got {version!r}")


# ---------------------------------------------------------------------------
# FeatureDefinition
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FeatureDefinition:
    """
    Frozen feature descriptor.

    Attributes
    ----------
    name: machine identifier, snake_case, 3-50 chars, starts with letter.
    description: human purpose (>10 chars).
    source_evidence: descriptor of required Evidence source(s). Example:
                     "dexscreener:price_usd" or "security_gate:is_honeypot,liquidity_locked_pct"
                     Stored as string for audit; runtime resolves via Evidence.source.
    calculation_method: string identifier of formula, e.g. "relative_change", "log_ratio",
                        "threshold_check", "wilson_ci", "concentration_ratio".
                        Must be non-empty. If callable provided, it is stored separately and
                        must be pure: (Evidence | list[Evidence]) -> float | None | dict.
    version: semver string, e.g. "1.0.0". Bump on formula change.
    calculation_callable: optional pure function for execution, not serialized to JSON by default.
    category: optional grouping (market, security, liquidity, whale, social, risk).
    metadata: optional free-form dict (unit, range, evidence_confidence requirement, etc.)
    """

    name: str
    description: str
    source_evidence: str
    calculation_method: str
    version: str
    calculation_callable: Optional[Callable[[Any], Any]] = field(default=None, compare=False, hash=False, repr=False)
    category: str = "market"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _validate_name(self.name)
        if not isinstance(self.description, str) or len(self.description.strip()) < 10:
            raise ValueError("Feature description must be >=10 chars")
        if not isinstance(self.source_evidence, str) or len(self.source_evidence.strip()) < 3:
            raise ValueError("Feature source_evidence must be non-empty descriptor (>=3 chars)")
        if not isinstance(self.calculation_method, str) or not self.calculation_method.strip():
            raise ValueError("Feature calculation_method must be non-empty string")
        if self.calculation_callable is not None and not callable(self.calculation_callable):
            raise ValueError("Feature calculation_callable must be callable or None")
        _validate_version(self.version)
        # Normalize
        object.__setattr__(self, "name", self.name.strip())
        object.__setattr__(self, "source_evidence", self.source_evidence.strip())
        object.__setattr__(self, "calculation_method", self.calculation_method.strip())
        object.__setattr__(self, "version", self.version.strip())
        object.__setattr__(self, "category", self.category.strip() if isinstance(self.category, str) else "market")
        if not isinstance(self.metadata, dict):
            raise ValueError("Feature metadata must be dict")

    @property
    def key(self) -> str:
        """Unique registry key: name@version"""
        return f"{self.name}@{self.version}"

    @property
    def provenance(self) -> str:
        """Deterministic hash over definition for audit (excludes callable)."""
        payload = f"{self.name}|{self.description}|{self.source_evidence}|{self.calculation_method}|{self.version}|{self.category}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        # Remove callable from serialization (not JSON serializable); keep method name
        d.pop("calculation_callable", None)
        d["key"] = self.key
        d["provenance"] = self.provenance
        return d

    def compute(self, evidence: Evidence | List[Evidence] | Dict[str, Evidence]) -> Any:
        """
        Execute the calculation_callable if present, otherwise return None.
        Pure: evidence in, value out. Never mutates global state.
        """
        if self.calculation_callable is None:
            return None
        return self.calculation_callable(evidence)


# ---------------------------------------------------------------------------
# FeatureRegistry
# ---------------------------------------------------------------------------

class FeatureRegistry:
    """
    Append-only registry for versioned features.
    Keyed by (name, version) — never mutates an existing entry.
    Thread-safety not required (single-threaded intelligence pipeline).
    """

    def __init__(self) -> None:
        self._by_key: Dict[str, FeatureDefinition] = {}
        self._by_name: Dict[str, List[FeatureDefinition]] = {}

    # ---- Write ----

    def register(self, feature: FeatureDefinition) -> None:
        """
        Register a new feature. Raises ValueError on duplicate (name, version).
        Appends, never overwrites.
        """
        if not isinstance(feature, FeatureDefinition):
            raise ValueError("register() requires FeatureDefinition")
        key = feature.key
        if key in self._by_key:
            raise ValueError(f"Feature {key} already registered — version is immutable, bump version for changes")
        self._by_key[key] = feature
        self._by_name.setdefault(feature.name, []).append(feature)
        # Keep versions sorted semver-lexicographically for determinism
        self._by_name[feature.name].sort(key=lambda f: f.version)

    def register_many(self, features: List[FeatureDefinition]) -> None:
        for f in features:
            self.register(f)

    # ---- Read ----

    def get(self, name: str, version: Optional[str] = None) -> Optional[FeatureDefinition]:
        """
        Retrieve by name. If version is None, returns latest version (last sorted).
        """
        lst = self._by_name.get(name)
        if not lst:
            return None
        if version is None:
            return lst[-1]
        for f in lst:
            if f.version == version:
                return f
        return None

    def get_by_key(self, key: str) -> Optional[FeatureDefinition]:
        return self._by_key.get(key)

    def list(self, category: Optional[str] = None) -> List[FeatureDefinition]:
        if category is None:
            return list(self._by_key.values())
        return [f for f in self._by_key.values() if f.category == category]

    def list_names(self) -> List[str]:
        return sorted(self._by_name.keys())

    def count(self) -> int:
        return len(self._by_key)

    def clear(self) -> None:
        """Test helper — clears all entries (never used in production)."""
        self._by_key.clear()
        self._by_name.clear()

    # ---- Validation ----

    def validate_all(self) -> List[str]:
        """
        Validate all registered features:
          - every feature has required fields (enforced at construction)
          - every source_evidence descriptor is non-empty
          - versions are unique per name (enforced at registration)
        Returns list of error strings (empty = valid).
        """
        errors: List[str] = []
        for key, f in self._by_key.items():
            if not f.name or not f.description or not f.source_evidence or not f.calculation_method or not f.version:
                errors.append(f"{key}: missing required field")
            if f.calculation_callable is not None and not callable(f.calculation_callable):
                errors.append(f"{key}: calculation_callable not callable")
        return errors

    # ---- Serialization ----

    def to_dict(self) -> dict[str, Any]:
        return {"features": [f.to_dict() for f in self.list()], "count": self.count()}

    def provenance(self) -> str:
        """Deterministic digest over all registered features' provenance."""
        parts = sorted(f.provenance for f in self._by_key.values())
        return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:16] if parts else "empty"


# ---------------------------------------------------------------------------
# Global singleton (convenience for wiring; still append-only via register)
# ---------------------------------------------------------------------------

_GLOBAL_REGISTRY: Optional[FeatureRegistry] = None


def get_global_registry() -> FeatureRegistry:
    global _GLOBAL_REGISTRY
    if _GLOBAL_REGISTRY is None:
        _GLOBAL_REGISTRY = FeatureRegistry()
        # Pre-register v2 genesis features covering the 5 scoring dimensions + risk
        _register_genesis_features(_GLOBAL_REGISTRY)
    return _GLOBAL_REGISTRY


def _register_genesis_features(reg: FeatureRegistry) -> None:
    """Genesis feature set for Intelligence Engine v2 (covers all scoring inputs)."""

    def _identity(ev):
        # Generic identity callable — returns value if evidence present
        if isinstance(ev, Evidence):
            return ev.value
        if isinstance(ev, list) and ev:
            return ev[0].value if isinstance(ev[0], Evidence) else None
        if isinstance(ev, dict):
            # dict of name->Evidence
            vals = list(ev.values())
            if vals and isinstance(vals[0], Evidence):
                return vals[0].value
        return None

    genesis = [
        FeatureDefinition(
            name="market_momentum",
            description="Price change momentum from evidence-backed price observations (evidence-only, no raw).",
            source_evidence="dexscreener:price_usd, geckoterminal:price_usd (Evidence.value)",
            calculation_method="relative_change",
            version="1.0.0",
            calculation_callable=_identity,
            category="market",
            metadata={"unit": "percent", "range": [-100, 1000]},
        ),
        FeatureDefinition(
            name="liquidity_depth",
            description="Liquidity depth relative to pool reserves, derived from liquidity_usd evidence.",
            source_evidence="dexscreener:liquidity_usd, geckoterminal:reserve_in_usd",
            calculation_method="log_ratio",
            version="1.0.0",
            calculation_callable=_identity,
            category="liquidity",
            metadata={"unit": "usd", "range": [0, 1e9]},
        ),
        FeatureDefinition(
            name="security_verdict",
            description="Security veto signal from honeypot / mint authority evidence.",
            source_evidence="security_gate:is_honeypot, has_mint_authority (Evidence.verification_status)",
            calculation_method="threshold_check",
            version="1.0.0",
            calculation_callable=_identity,
            category="security",
            metadata={"severity": "CRITICAL"},
        ),
        FeatureDefinition(
            name="whale_concentration",
            description="Top holder concentration ratio from whale evidence.",
            source_evidence="holders:top10_share, whales:concentration (Evidence.value)",
            calculation_method="concentration_ratio",
            version="1.0.0",
            calculation_callable=_identity,
            category="whale",
            metadata={"unit": "ratio", "threshold": 0.5},
        ),
        FeatureDefinition(
            name="social_velocity",
            description="Social/narrative velocity from news/viral evidence.",
            source_evidence="viral:volume_acceleration, news:narrative_score",
            calculation_method="velocity_score",
            version="1.0.0",
            calculation_callable=_identity,
            category="social",
            metadata={"unit": "score", "range": [0, 100]},
        ),
        FeatureDefinition(
            name="risk_aggregate",
            description="Aggregated risk penalty from contract, liquidity, concentration, manipulation evidence.",
            source_evidence="risk:contract, risk:liquidity, risk:concentration, risk:manipulation",
            calculation_method="weighted_penalty",
            version="1.0.0",
            calculation_callable=_identity,
            category="risk",
            metadata={"range": [0, 100]},
        ),
    ]
    for f in genesis:
        try:
            reg.register(f)
        except ValueError:
            pass  # idempotent for re-import

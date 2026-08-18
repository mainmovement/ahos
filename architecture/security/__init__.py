"""AHOS Security package.

Credential hygiene is imported eagerly so logging can redact secrets without
pulling the intelligence stack. Phase 5 analyzers resolve lazily.
"""
from .hygiene import (
    REDACTED_TEXT,
    assert_safe_environment,
    sanitize_dict,
    sanitize_secrets,
)

__all__ = [
    "REDACTED_TEXT",
    "assert_safe_environment",
    "sanitize_dict",
    "sanitize_secrets",
    "SecurityIntelligence",
    "SecurityReport",
    "ContractAnalyzer",
    "ContractReport",
    "LiquidityAnalyzer",
    "LiquidityReport",
    "HolderAnalyzer",
    "HolderReport",
    "ManipulationDetector",
    "ManipulationReport",
]

_LAZY = {
    "SecurityIntelligence": (".engine", "SecurityIntelligence"),
    "SecurityReport": (".engine", "SecurityReport"),
    "ContractAnalyzer": (".contract_analysis", "ContractAnalyzer"),
    "ContractReport": (".contract_analysis", "ContractReport"),
    "LiquidityAnalyzer": (".liquidity_analysis", "LiquidityAnalyzer"),
    "LiquidityReport": (".liquidity_analysis", "LiquidityReport"),
    "HolderAnalyzer": (".holder_analysis", "HolderAnalyzer"),
    "HolderReport": (".holder_analysis", "HolderReport"),
    "ManipulationDetector": (".manipulation_detection", "ManipulationDetector"),
    "ManipulationReport": (".manipulation_detection", "ManipulationReport"),
}


def __getattr__(name: str):
    if name not in _LAZY:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module, attr = _LAZY[name]
    from importlib import import_module
    return getattr(import_module(module, __name__), attr)

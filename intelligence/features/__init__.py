"""
intelligence.features — Feature Registry package
"""

from .registry import FeatureDefinition, FeatureRegistry, get_global_registry

__all__ = ["FeatureDefinition", "FeatureRegistry", "get_global_registry"]

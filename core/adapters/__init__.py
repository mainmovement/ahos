"""
core.adapters — Translators between core domain and legacy subsystems.

Discovery, paper_trading, architecture/* remain the owners of their
tables and contracts. Adapters are pure functions that map rows /
NormalizedTokenCandidate / OpportunityScoreReport → core domain objects
without mutating the legacy stores.

Import-time isolation: adapters import legacy modules ONLY inside the
function body (late import) so `import core.adapters` never collapses
if a legacy dependency is absent.
"""

from .discovery_adapter import discovery_row_to_observation, candidate_to_observation
from .scoring_adapter import score_report_to_decision

__all__ = ["discovery_row_to_observation", "candidate_to_observation", "score_report_to_decision"]

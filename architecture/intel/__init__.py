"""AHOS Narrative & Social Intelligence subsystem (Lane A).

Answers the questions the market-data pipeline cannot:
  - What is being SAID about this token right now?  (news.py)
  - Is attention ACCELERATING or decaying?          (viral.py)
  - Are large holders accumulating or exiting?      (whales.py)
  - If I buy, can I actually GET OUT?               (exitability.py)

LAW (inherited from the deterministic floor):
  Narrative is EVIDENCE, never proof. Every signal produced here is a bounded
  modifier with an explicit provenance reference. Social hype can never by
  itself create a BUY recommendation, and it can never override a security veto.
"""

from .news import NewsCollector, NewsItem, NarrativeSignal          # noqa: F401
from .viral import ViralityTracker, ViralitySignal                  # noqa: F401
from .whales import WhaleTracker, WhaleSignal                       # noqa: F401
from .exitability import ExitabilityAnalyzer, ExitabilityReport     # noqa: F401

__all__ = [
    "NewsCollector", "NewsItem", "NarrativeSignal",
    "ViralityTracker", "ViralitySignal",
    "WhaleTracker", "WhaleSignal",
    "ExitabilityAnalyzer", "ExitabilityReport",
]

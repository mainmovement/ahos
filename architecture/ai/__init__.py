"""AHOS Live AI Council transport layer.

`architecture/council.py` defines the council PROTOCOL (agreement matrix, red-team,
verdict synthesis) but deliberately performs no I/O — responses are injected, which
keeps it deterministic and unit-testable.

This package supplies the missing half: the live transport that actually asks
Claude, ChatGPT, Gemini, Grok, Groq, Ollama and friends a question, in parallel,
and normalizes their answers into the envelopes the council protocol expects.

LAW: AI is ADVISORY. It never decides, never approves, never overrides the
deterministic floor. Zero reachable providers is a supported operating mode.
"""

from .clients import AIClient, AIResponse, build_clients_from_registry   # noqa: F401
from .council_live import LiveCouncil, CouncilVerdict                    # noqa: F401

__all__ = ["AIClient", "AIResponse", "build_clients_from_registry",
           "LiveCouncil", "CouncilVerdict"]

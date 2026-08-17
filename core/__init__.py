"""
AHOS v2 — Core Intelligence Foundation
=======================================
Pure domain layer: no I/O, no network, no trading execution.
Every data point is an Evidence-anchored fact; every state change is an Event;
every action is screened by Governance.

This package never imports from discovery/, architecture/, paper_trading/
or telegram_ai/ at import-time — adapters perform the translation
explicitly so the core remains testable offline and independent of
storage implementation.

Paper-only law: this layer advises, never executes. Any attempt to
invoke wallet signing, transaction broadcast, or live order placement
is a SafetyViolation.
"""

from importlib import metadata as _metadata

__version__ = "2.0.0-core"
__all__ = []

"""
core.events — Domain event types and bus.

Events are facts that have happened. They carry the Evidence ids that
justify them and a correlation_id to trace a single pipeline run
across token → observation → score → decision → alert.
"""

from .event_types import Event, EventType, create_event
from .event_bus import EventBus

__all__ = ["Event", "EventType", "create_event", "EventBus"]

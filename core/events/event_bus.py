"""
core.events.event_bus — In-process, synchronous event bus.

Design: synchronous, append-only history, handler-error isolation.
* subscribe(event_type, handler) — handler: Callable[[Event], None]
* publish(event) — appends to history, fans out to matching handlers + wildcard ("*")
* unsubscribe, clear, replay

Thread-safety: a simple re-entrant lock so re-publishing from a handler is safe.
Persistence is NOT provided here (events are in-memory); durable stores remain
in the existing SQLite tables (discovery_observations, etc.).
"""

from __future__ import annotations

import threading
import traceback
from collections import defaultdict
from typing import Callable, Any

from .event_types import Event, EventType


Handler = Callable[[Event], Any]
WILDCARD = "*"


class EventBus:
    """
    In-memory domain event bus.

    Guarantees
    ----------
    * publish() never raises into the caller because of a handler exception
      — failures are collected and returned so safety can audit them.
    * History is append-only: once an event is published, it stays in
      self.history in publish order.
    * subscribe("*", fn) receives every event (used for audit / projection).
    """

    def __init__(self) -> None:
        self._handlers: dict[str, list[Handler]] = defaultdict(list)
        self._history: list[Event] = []
        self._handler_errors: list[dict[str, Any]] = []
        self._lock = threading.RLock()

    # ------------------------------------------------------------------
    # Subscription
    # ------------------------------------------------------------------

    def subscribe(self, event_type: str, handler: Handler) -> None:
        if not callable(handler):
            raise ValueError("handler must be callable")
        # Allow WILDCARD or any known EventType or custom string (future types)
        if not isinstance(event_type, str) or not event_type.strip():
            raise ValueError("event_type must be non-empty string")
        et = event_type.strip()
        # Warn (non-fatal) if subscribing to unknown type — future-proofing
        # (strict check would block extensibility)
        with self._lock:
            if handler not in self._handlers[et]:
                self._handlers[et].append(handler)

    def unsubscribe(self, event_type: str, handler: Handler) -> None:
        et = event_type.strip()
        with self._lock:
            lst = self._handlers.get(et, [])
            if handler in lst:
                lst.remove(handler)

    def clear_handlers(self) -> None:
        with self._lock:
            self._handlers.clear()

    # ------------------------------------------------------------------
    # Publishing
    # ------------------------------------------------------------------

    def publish(self, event: Event) -> dict[str, Any]:
        """
        Publish an event to all subscribed handlers.

        Returns a delivery report:
            {
              "event_id": str,
              "delivered_to": int,
              "failed": int,
              "errors": list[dict],
            }
        """
        if not isinstance(event, Event):
            raise ValueError("publish() requires an Event instance")
        with self._lock:
            self._history.append(event)
            # Capture handlers snapshot
            targets = list(self._handlers.get(event.event_type, [])) + list(self._handlers.get(WILDCARD, []))

        delivered = 0
        errors: list[dict[str, Any]] = []
        for handler in targets:
            try:
                handler(event)
                delivered += 1
            except Exception as exc:  # noqa: BLE001  isolation is intentional
                err = {
                    "handler": getattr(handler, "__name__", repr(handler)),
                    "event_id": event.event_id,
                    "event_type": event.event_type,
                    "error": f"{type(exc).__name__}: {exc}",
                    "traceback": traceback.format_exc()[-2000:],
                }
                with self._lock:
                    self._handler_errors.append(err)
                errors.append(err)

        return {
            "event_id": event.event_id,
            "delivered_to": delivered,
            "failed": len(errors),
            "errors": errors,
        }

    def publish_many(self, events: list[Event]) -> list[dict[str, Any]]:
        return [self.publish(ev) for ev in events]

    # ------------------------------------------------------------------
    # Inspection & replay
    # ------------------------------------------------------------------

    @property
    def history(self) -> list[Event]:
        with self._lock:
            return list(self._history)

    @property
    def handler_errors(self) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._handler_errors)

    def get_history(
        self,
        event_type: str | None = None,
        aggregate_id: str | None = None,
        correlation_id: str | None = None,
    ) -> list[Event]:
        with self._lock:
            result = list(self._history)
        if event_type:
            result = [e for e in result if e.event_type == event_type]
        if aggregate_id:
            result = [e for e in result if e.aggregate_id == aggregate_id]
        if correlation_id:
            result = [e for e in result if e.correlation_id == correlation_id]
        return result

    def replay(self, sink: Callable[[Event], Any] | None = None) -> int:
        """Replay history to a sink (or to current handlers if sink is None). Returns count."""
        with self._lock:
            hist = list(self._history)
        count = 0
        for ev in hist:
            if sink is not None:
                try:
                    sink(ev)
                except Exception:
                    # sink isolation — swallow for replay auditing
                    pass
            else:
                self.publish(ev)
            count += 1
        return count

    def clear(self) -> None:
        """Clear history and errors (handlers preserved)."""
        with self._lock:
            self._history.clear()
            self._handler_errors.clear()

    def clear_all(self) -> None:
        """Clear history, errors, and handlers (test reset)."""
        with self._lock:
            self._handlers.clear()
            self._history.clear()
            self._handler_errors.clear()

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def handler_count(self, event_type: str | None = None) -> int:
        with self._lock:
            if event_type:
                return len(self._handlers.get(event_type, []))
            return sum(len(v) for v in self._handlers.values())

    def __len__(self) -> int:
        with self._lock:
            return len(self._history)

    def __repr__(self) -> str:
        return f"<EventBus history={len(self)} handlers={self.handler_count()} errors={len(self.handler_errors)}>"

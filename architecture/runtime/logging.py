#!/usr/bin/env python3
"""AHOS Structured Production Logging Layer (Phase XX).

Features:
  - Structured JSON log entries.
  - Automatic sensitive secret redaction via architecture.security.
  - Correlation tracking via run_id.
  - ISO-8601 UTC timestamps.
  - Machine-parsable output for containerized / syslog log drivers.
"""
from __future__ import annotations

import json
import logging
import sys
import time
from datetime import datetime, timezone
from typing import Any
from ..security import sanitize_dict, sanitize_secrets


class JsonFormatter(logging.Formatter):
    def __init__(self, service_name: str = "ahos-runtime", version: str = "1.0.0"):
        super().__init__()
        self.service_name = service_name
        self.version = version

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "service": self.service_name,
            "version": self.version,
            "message": sanitize_secrets(record.getMessage()),
            "module": record.module,
            "line": record.lineno,
        }

        # Include run_id if attached to record
        if hasattr(record, "run_id") and record.run_id:
            log_entry["run_id"] = record.run_id

        # Include custom extra metadata if provided
        if hasattr(record, "meta") and isinstance(record.meta, dict):
            log_entry["meta"] = sanitize_dict(record.meta)

        # Include exception info if available
        if record.exc_info:
            log_entry["exception"] = sanitize_secrets(self.formatException(record.exc_info))

        return json.dumps(log_entry, ensure_ascii=False)


def get_logger(name: str = "ahos", run_id: str | None = None) -> logging.LoggerAdapter:
    """Returns a structured logger adapter with optional correlation run_id."""
    base_logger = logging.getLogger(name)
    if not base_logger.handlers:
        base_logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        base_logger.addHandler(handler)
        base_logger.propagate = False

    class RunIdAdapter(logging.LoggerAdapter):
        def process(self, msg: str, kwargs: Any) -> tuple[str, Any]:
            extra = kwargs.setdefault("extra", {})
            if self.extra and "run_id" in self.extra:
                extra["run_id"] = self.extra["run_id"]
            return msg, kwargs

    return RunIdAdapter(base_logger, {"run_id": run_id} if run_id else {})

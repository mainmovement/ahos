#!/usr/bin/env python3
"""AHOS Structured Observability & Provenance Tracing Layer.

Every operation records:
  - run_id: unique execution identifier
  - timestamp: ISO 8601 UTC timestamp
  - component: subsystem name
  - version: component version
  - input_provenance: hash / reference of inputs
  - provider: answering provider id
  - status: OK | ERROR | DEGRADED | REFUSED
  - duration_ms: latency in milliseconds
  - error_class: categorized error type (if any)
  - output_provenance: sha256 of generated output
"""
from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from typing import Any
from .security import sanitize_dict


def generate_run_id(prefix: str = "run") -> str:
    return f"{prefix}_{int(time.time())}_{uuid.uuid4().hex[:8]}"


def compute_sha256(data: Any) -> str:
    if isinstance(data, (dict, list)):
        payload = json.dumps(data, sort_keys=True).encode("utf-8")
    elif isinstance(data, str):
        payload = data.encode("utf-8")
    elif isinstance(data, bytes):
        payload = data
    else:
        payload = str(data).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@dataclass
class OperationTrace:
    run_id: str
    component: str
    operation: str
    status: str                                  # OK | ERROR | DEGRADED | REFUSED
    start_utc: str
    duration_ms: float
    input_provenance: str
    output_provenance: str | None = None
    provider: str | None = None
    version: str = "1.0"
    error_class: str | None = None
    error_message: str | None = None
    meta: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        d = asdict(self)
        clean = sanitize_dict(d)
        return json.dumps(clean, ensure_ascii=False)


class Tracer:
    def __init__(self, component: str, version: str = "1.0"):
        self.component = component
        self.version = version

    def trace_operation(self, operation: str, input_data: Any,
                        provider: str | None = None, run_id: str | None = None) -> TraceContext:
        return TraceContext(
            component=self.component,
            version=self.version,
            operation=operation,
            input_data=input_data,
            provider=provider,
            run_id=run_id or generate_run_id(self.component)
        )


class TraceContext:
    def __init__(self, component: str, version: str, operation: str,
                 input_data: Any, provider: str | None, run_id: str):
        self.component = component
        self.version = version
        self.operation = operation
        self.input_provenance = compute_sha256(input_data)
        self.provider = provider
        self.run_id = run_id
        self.t0 = time.time()
        self.start_utc = datetime.now(timezone.utc).isoformat()
        self.trace: OperationTrace | None = None

    def success(self, output_data: Any, meta: dict | None = None) -> OperationTrace:
        dt = (time.time() - self.t0) * 1000.0
        self.trace = OperationTrace(
            run_id=self.run_id,
            component=self.component,
            version=self.version,
            operation=self.operation,
            status="OK",
            start_utc=self.start_utc,
            duration_ms=round(dt, 2),
            input_provenance=self.input_provenance,
            output_provenance=compute_sha256(output_data),
            provider=self.provider,
            meta=meta or {}
        )
        return self.trace

    def failure(self, error: Exception, error_class: str = "RUNTIME_ERROR", meta: dict | None = None) -> OperationTrace:
        dt = (time.time() - self.t0) * 1000.0
        self.trace = OperationTrace(
            run_id=self.run_id,
            component=self.component,
            version=self.version,
            operation=self.operation,
            status="ERROR",
            start_utc=self.start_utc,
            duration_ms=round(dt, 2),
            input_provenance=self.input_provenance,
            output_provenance=None,
            provider=self.provider,
            error_class=error_class,
            error_message=str(error)[:300],
            meta=meta or {}
        )
        return self.trace

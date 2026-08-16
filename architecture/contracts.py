#!/usr/bin/env python3
"""AHOS Lane-B P1 — agent contract loader/validator + runtime envelope helpers.

No external schema dependency ($0 law): the schema JSON is a declarative document and this
module hand-validates against it. Deterministic, side-effect-free (pure functions only).
"""
from __future__ import annotations

import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "contracts" / "agent_contract_v1.json"


def load_schema(path: str | Path = SCHEMA_PATH) -> dict:
    return json.loads(Path(path).read_text(encoding='utf-8'))


def validate_spec(spec: dict, schema: dict | None = None) -> list[str]:
    """Validate an agent REGISTRY spec. Returns list of violations ([] = conformant)."""
    schema = schema or load_schema()
    errs: list[str] = []
    for f in schema["spec_fields"]["required"]:
        if f not in spec or spec[f] in (None, ""):
            errs.append(f"missing spec field: {f}")
    enums = schema["enums"]
    for f, allowed in (("status", enums["status"]), ("lane", enums["lane"]),
                       ("form", enums["form"]), ("cadence", enums["cadence"]),
                       ("criticality", enums["criticality"])):
        if f in spec and spec[f] not in allowed:
            errs.append(f"{f}={spec[f]} not in {allowed}")
    for f in ("allowed_authority", "forbidden_authority"):
        bad = [a for a in spec.get(f, []) if a not in enums["authority"]]
        if bad:
            errs.append(f"{f} contains invalid authority {bad}")
    overlap = set(spec.get("allowed_authority", [])) & set(spec.get("forbidden_authority", []))
    if overlap:
        errs.append(f"authority self-conflict: {sorted(overlap)} in both allowed and forbidden")
    # W9 law: AI-class agents may only ANALYZE/ADVISE/CHALLENGE
    if "AI" in (spec.get("capabilities") or []) and \
       set(spec.get("allowed_authority", [])) - {"ANALYZE", "ADVISE", "CHALLENGE"}:
        errs.append("AI-capable agent exceeds ANALYZE/ADVISE/CHALLENGE authority (W9 §6)")
    # W11 additive: optional ops block (validated only when present — v1 compatibility)
    if "ops" in spec:
        errs.extend(validate_ops_block(spec["ops"], schema))
    return errs


def validate_ops_block(ops: dict, schema: dict | None = None) -> list[str]:
    """Validate the W11 orchestration block. Optional in v1; machine-honest when present."""
    schema = schema or load_schema()
    meta = schema["spec_fields"].get("ops_fields", {})
    enums = schema["enums"]
    errs: list[str] = []
    if not isinstance(ops, dict):
        return ["ops must be an object"]
    for f in meta.get("required_when_present", []):
        if f not in ops or ops[f] in (None, ""):
            errs.append(f"ops missing field: {f}")
    if "runtime" in ops and ops["runtime"] not in enums.get("runtime", []):
        errs.append(f"ops.runtime={ops.get('runtime')} not in {enums.get('runtime')}")
    if "boot_class" in ops and ops["boot_class"] not in enums.get("boot_class", []):
        errs.append(f"ops.boot_class={ops.get('boot_class')} not in {enums.get('boot_class')}")
    op = ops.get("operability") or {}
    for b in ("implemented", "contracted", "orchestrated", "live"):
        if b in op and not isinstance(op[b], bool):
            errs.append(f"ops.operability.{b} must be bool")
    if op.get("live") and not op.get("implemented"):
        errs.append("ops.operability: live=True requires implemented=True (no fabricated liveness)")
    h = ops.get("health") or {}
    if isinstance(h, dict) and h.get("kind") not in (None, *enums.get("health_kind", [])):
        errs.append(f"ops.health.kind={h.get('kind')} not in {enums.get('health_kind')}")
    c = ops.get("circuit") or {}
    if isinstance(c, dict) and c.get("state") not in (None, *enums.get("circuit", [])):
        errs.append(f"ops.circuit.state={c.get('state')} not in {enums.get('circuit')}")
    return errs


def validate_envelope(env: dict, schema: dict | None = None) -> list[str]:
    """Validate a runtime OUTPUT envelope against agent_contract_v1. [] = conformant."""
    schema = schema or load_schema()
    errs: list[str] = []
    for f, meta in schema["fields"].items():
        if meta.get("required") and f not in env:
            errs.append(f"missing envelope field: {f}")
    if "error" in env and env["error"] not in schema["fields"]["error"]["values"]:
        errs.append(f"error={env['error']} not in enum")
    if "confidence" in env and env["confidence"] not in schema["fields"]["confidence"]["values"]:
        errs.append(f"confidence={env['confidence']} not in enum")
    if "timestamp" in env and not isinstance(env["timestamp"], (int, float)):
        errs.append("timestamp must be epoch number")
    if "evidence" in env and not isinstance(env["evidence"], list):
        errs.append("evidence must be array (ids/probe refs); empty allowed only with error!=NONE")
    if env.get("error", "NONE") == "NONE" and not env.get("evidence"):
        errs.append("no-error envelope must carry ≥1 evidence ref (no-claim-without-evidence law)")
    if "health" in env:
        h = env["health"] or {}
        if h.get("circuit") not in (None, "CLOSED", "OPEN", "HALF_OPEN"):
            errs.append("health.circuit must be CLOSED|OPEN|HALF_OPEN")
    return errs


def make_envelope(*, agent_version: str, output, evidence: list, lane: str,
                  confidence: str, error: str = "NONE", input: dict | None = None,
                  state: dict | None = None, producer: str = "lane-b",
                  health: dict | None = None, ts: float | None = None) -> dict:
    """Constructor so future agents cannot misshape the envelope."""
    return {"input": input or {}, "output": output,
            "state": state or {"reads": [], "writes": []}, "error": error,
            "evidence": evidence, "confidence": confidence,
            "timestamp": time.time() if ts is None else ts,
            "provenance": {"producer": producer, "lane": lane, "source_artifacts": []},
            "version": agent_version,
            "health": health or {"last_ok_ts": None, "circuit": "CLOSED"}}

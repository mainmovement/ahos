"""Bounded ResearchTask / AgentOutput contracts. Standard library only."""

from __future__ import annotations

import hashlib
import re
from typing import Any

from research_worker.protocol import (
    FORBIDDEN_AUTHORITY_KEYS,
    MAX_DICT_KEYS,
    MAX_LIST_ITEMS,
    MAX_STRING_CHARS,
    PROTOCOL_VERSION,
    ProtocolError,
)


AGENT_ID = "RESEARCH_ANALYST_AGENT"
ITEM_TYPES = frozenset({"OBSERVATION", "EVIDENCE", "CLAIM", "HYPOTHESIS", "PREDICTION"})
IDENTIFIER_RE = re.compile(r"^[A-Za-z][A-Za-z0-9._-]{0,63}$")
CONTEXT_ID_RE = re.compile(r"^research-context\.[A-Za-z0-9._-]{1,48}$")
TASK_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9._-]{0,63}$")

FORBIDDEN_STATUS_VALUES = frozenset(
    {
        "VERIFIED",
        "PROMOTED",
        "AUTHORIZED",
        "EXECUTABLE",
        "APPROVED",
        "SAFE",
    }
)

AUTHORITY_CLASS = "NON_AUTHORITATIVE"
EPISTEMIC_CLASS = "UNVERIFIED"
PRODUCTION_CLASS = "NON_PRODUCTION"

NETWORK_PREFIXES = (
    "http://",
    "https://",
    "ftp://",
    "ws://",
    "wss://",
    "socket:",
    "dns:",
    "mailto:",
    "file://",
)

_DRIVE_PATH_RE = re.compile(r"(^|[\s\"'])[A-Za-z]:[\\/]")
_UNIX_SENSITIVE_RE = re.compile(r"(^|[\s\"'])/(etc|usr|home|var|root|tmp)/")
_EXEC_RE = re.compile(
    r"(?i)(\b(eval|exec|compile)\s*\(|\b(__import__|importlib|subprocess|powershell|"
    r"cmd\.exe|os\.system|ctypes)\b|/bin/sh)"
)

TASK_REQUIRED = frozenset(
    {
        "protocol_version",
        "task_id",
        "agent_context_id",
        "mission_id",
        "objective",
        "supplied_items",
        "constraints",
    }
)
ITEM_REQUIRED = frozenset({"item_id", "item_type", "text", "provenance_ref"})
CONSTRAINT_REQUIRED = frozenset(
    {
        "max_observations",
        "max_claims",
        "max_hypotheses",
        "max_predictions",
        "max_contradictions",
        "max_experiments",
        "max_reviews",
    }
)
OUTPUT_REQUIRED = frozenset(
    {
        "protocol_version",
        "agent_context_id",
        "mission_id",
        "observations",
        "claims",
        "hypotheses",
        "predictions",
        "contradictions",
        "proposed_experiments",
        "requested_reviews",
        "uncertainty_labels",
        "provenance_refs",
        "authority_class",
        "epistemic_class",
        "production_class",
        "agent_id",
    }
)
OUTPUT_ARRAY_KEYS = (
    "observations",
    "claims",
    "hypotheses",
    "predictions",
    "contradictions",
    "proposed_experiments",
    "requested_reviews",
    "uncertainty_labels",
    "provenance_refs",
)


def _require_object(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ProtocolError("MALFORMED_PAYLOAD", f"{field}_must_be_object")
    if len(value) > MAX_DICT_KEYS:
        raise ProtocolError("MALFORMED_PAYLOAD", f"{field}_too_many_keys")
    return value


def _bounded_str(value: Any, *, field: str, maximum: int = MAX_STRING_CHARS) -> str:
    if not isinstance(value, str):
        raise ProtocolError("MALFORMED_PAYLOAD", f"{field}_must_be_string")
    if len(value) > maximum:
        raise ProtocolError("MALFORMED_PAYLOAD", f"{field}_too_long")
    if "\x00" in value:
        raise ProtocolError("MALFORMED_PAYLOAD", f"{field}_nul_denied")
    _reject_locator_and_executable(value, field=field)
    return value


def _bounded_int(value: Any, *, field: str, minimum: int, maximum: int) -> int:
    if type(value) is not int:
        raise ProtocolError("MALFORMED_PAYLOAD", f"{field}_must_be_int")
    if value < minimum or value > maximum:
        raise ProtocolError("MALFORMED_PAYLOAD", f"{field}_out_of_range")
    return value


def _reject_authority_fields(payload: dict[str, Any], *, field: str) -> None:
    for key in payload:
        if key in FORBIDDEN_AUTHORITY_KEYS:
            raise ProtocolError("FORBIDDEN_AUTHORITY_FIELD", f"untrusted_authority_field:{key}")
        if not isinstance(key, str) or not key:
            raise ProtocolError("MALFORMED_PAYLOAD", f"{field}_invalid_key")


def _reject_locator_and_executable(value: str, *, field: str) -> None:
    lowered = value.strip().lower()
    for prefix in NETWORK_PREFIXES:
        if prefix in lowered:
            raise ProtocolError("FORBIDDEN_NETWORK_LOCATOR", f"{field}_network_or_url_denied")
    if "\\\\" in value or _DRIVE_PATH_RE.search(value) or _UNIX_SENSITIVE_RE.search(value):
        raise ProtocolError("FORBIDDEN_FILESYSTEM_PATH", f"{field}_path_denied")
    if ".." in value.split() or value.strip().startswith(".."):
        raise ProtocolError("FORBIDDEN_FILESYSTEM_PATH", f"{field}_path_denied")
    if _EXEC_RE.search(value):
        raise ProtocolError("FORBIDDEN_EXECUTABLE_CONTENT", f"{field}_executable_denied")


def _require_identifier(value: Any, *, field: str, pattern: re.Pattern[str] = IDENTIFIER_RE) -> str:
    text = _bounded_str(value, field=field, maximum=64)
    if not pattern.fullmatch(text):
        raise ProtocolError("MALFORMED_PAYLOAD", f"{field}_identifier_invalid")
    return text


def _reject_forbidden_status_strings(value: Any, *, field: str) -> None:
    if isinstance(value, str) and value in FORBIDDEN_STATUS_VALUES:
        raise ProtocolError("FORBIDDEN_STATUS_VALUE", f"{field}_forbidden_status:{value}")
    if isinstance(value, dict):
        for nested_key, nested in value.items():
            _reject_forbidden_status_strings(nested, field=f"{field}.{nested_key}")
    if isinstance(value, list):
        for index, nested in enumerate(value):
            _reject_forbidden_status_strings(nested, field=f"{field}[{index}]")


def _require_keys(payload: dict[str, Any], required: frozenset[str], allowed: frozenset[str], *, field: str) -> None:
    missing = required - payload.keys()
    if missing:
        raise ProtocolError("MALFORMED_PAYLOAD", f"{field}_missing_fields:{','.join(sorted(missing))}")
    extra = payload.keys() - allowed
    if extra:
        raise ProtocolError("MALFORMED_PAYLOAD", f"{field}_unknown_fields:{','.join(sorted(extra))}")


def validate_research_task(raw: Any) -> dict[str, Any]:
    task = _require_object(raw, "research_task")
    _reject_authority_fields(task, field="research_task")
    _require_keys(task, TASK_REQUIRED, TASK_REQUIRED, field="research_task")
    if task["protocol_version"] != PROTOCOL_VERSION:
        raise ProtocolError("PROTOCOL_VERSION_MISMATCH", "protocol_version_mismatch")
    mission_id = task["mission_id"]
    if mission_id is not None:
        mission_id = _require_identifier(mission_id, field="mission_id")
    constraints_raw = _require_object(task["constraints"], "constraints")
    _reject_authority_fields(constraints_raw, field="constraints")
    _require_keys(constraints_raw, CONSTRAINT_REQUIRED, CONSTRAINT_REQUIRED, field="constraints")
    constraints = {
        key: _bounded_int(constraints_raw[key], field=key, minimum=0, maximum=MAX_LIST_ITEMS)
        for key in sorted(CONSTRAINT_REQUIRED)
    }
    items_raw = task["supplied_items"]
    if not isinstance(items_raw, list):
        raise ProtocolError("MALFORMED_PAYLOAD", "supplied_items_must_be_list")
    if len(items_raw) > MAX_LIST_ITEMS:
        raise ProtocolError("MALFORMED_PAYLOAD", "supplied_items_too_many")
    items: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    type_counts = {name: 0 for name in ITEM_TYPES}
    for index, item_raw in enumerate(items_raw):
        item_obj = _require_object(item_raw, f"supplied_items[{index}]")
        _reject_authority_fields(item_obj, field=f"supplied_items[{index}]")
        _require_keys(item_obj, ITEM_REQUIRED, ITEM_REQUIRED, field=f"supplied_items[{index}]")
        item_id = _require_identifier(item_obj["item_id"], field="item_id")
        if item_id in seen_ids:
            raise ProtocolError("MALFORMED_PAYLOAD", "item_id_duplicate")
        seen_ids.add(item_id)
        item_type = _bounded_str(item_obj["item_type"], field="item_type", maximum=32)
        if item_type not in ITEM_TYPES:
            raise ProtocolError("MALFORMED_PAYLOAD", "item_type_invalid")
        provenance_ref = item_obj["provenance_ref"]
        if provenance_ref is not None:
            provenance_ref = _require_identifier(provenance_ref, field="provenance_ref")
        items.append(
            {
                "item_id": item_id,
                "item_type": item_type,
                "text": _bounded_str(item_obj["text"], field="text"),
                "provenance_ref": provenance_ref,
            }
        )
        type_counts[item_type] += 1
    if type_counts["OBSERVATION"] > constraints["max_observations"]:
        raise ProtocolError("MALFORMED_PAYLOAD", "observations_exceed_max")
    if type_counts["CLAIM"] > constraints["max_claims"]:
        raise ProtocolError("MALFORMED_PAYLOAD", "claims_exceed_max")
    if type_counts["HYPOTHESIS"] > constraints["max_hypotheses"]:
        raise ProtocolError("MALFORMED_PAYLOAD", "hypotheses_exceed_max")
    if type_counts["PREDICTION"] > constraints["max_predictions"]:
        raise ProtocolError("MALFORMED_PAYLOAD", "predictions_exceed_max")
    return {
        "protocol_version": PROTOCOL_VERSION,
        "task_id": _require_identifier(task["task_id"], field="task_id", pattern=TASK_ID_RE),
        "agent_context_id": _require_identifier(
            task["agent_context_id"], field="agent_context_id", pattern=CONTEXT_ID_RE
        ),
        "mission_id": mission_id,
        "objective": _bounded_str(task["objective"], field="objective"),
        "supplied_items": items,
        "constraints": constraints,
    }


def _require_record_list(
    value: Any,
    *,
    field: str,
    maximum: int,
    required_keys: frozenset[str],
) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ProtocolError("MALFORMED_PAYLOAD", f"{field}_must_be_list")
    if len(value) > maximum:
        raise ProtocolError("MALFORMED_PAYLOAD", f"{field}_too_many")
    records: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        record = _require_object(item, f"{field}[{index}]")
        _reject_authority_fields(record, field=f"{field}[{index}]")
        extra = record.keys() - required_keys
        missing = required_keys - record.keys()
        if missing:
            raise ProtocolError("MALFORMED_PAYLOAD", f"{field}_missing_fields:{','.join(sorted(missing))}")
        if extra:
            raise ProtocolError("MALFORMED_PAYLOAD", f"{field}_unknown_fields:{','.join(sorted(extra))}")
        cleaned: dict[str, Any] = {}
        for key, nested in record.items():
            if nested is None and key in {"provenance_ref", "hypothesis_ref"}:
                cleaned[key] = None
            elif isinstance(nested, str):
                if key.endswith("_id") or key in {"artifact_id", "provenance_ref", "hypothesis_ref", "target_id"}:
                    if nested in {"UNKNOWN", "UNVERIFIED"}:
                        cleaned[key] = nested
                    else:
                        cleaned[key] = _require_identifier(nested, field=f"{field}.{key}")
                else:
                    cleaned[key] = _bounded_str(nested, field=f"{field}.{key}")
            elif type(nested) is bool and key == "execution_requested":
                if nested is True:
                    raise ProtocolError("FORBIDDEN_STATUS_VALUE", "execution_requested_must_be_false")
                cleaned[key] = False
            else:
                raise ProtocolError("MALFORMED_PAYLOAD", f"{field}.{key}_invalid_type")
        _reject_forbidden_status_strings(cleaned, field=field)
        records.append(cleaned)
    return records


def validate_agent_output(
    raw: Any,
    *,
    task: dict[str, Any],
    expected_context_id: str,
) -> dict[str, Any]:
    output = _require_object(raw, "agent_output")
    _reject_authority_fields(output, field="agent_output")
    _require_keys(output, OUTPUT_REQUIRED, OUTPUT_REQUIRED, field="agent_output")
    if output["protocol_version"] != PROTOCOL_VERSION:
        raise ProtocolError("PROTOCOL_VERSION_MISMATCH", "protocol_version_mismatch")
    agent_id = _bounded_str(output["agent_id"], field="agent_id", maximum=64)
    if agent_id != AGENT_ID:
        raise ProtocolError("MALFORMED_PAYLOAD", "agent_id_invalid")
    context_id = _require_identifier(
        output["agent_context_id"], field="agent_context_id", pattern=CONTEXT_ID_RE
    )
    if context_id != expected_context_id or context_id != task["agent_context_id"]:
        raise ProtocolError("MALFORMED_PAYLOAD", "agent_context_binding_mismatch")
    mission_id = output["mission_id"]
    if mission_id is not None:
        mission_id = _require_identifier(mission_id, field="mission_id")
    if mission_id != task["mission_id"]:
        raise ProtocolError("MALFORMED_PAYLOAD", "mission_binding_mismatch")
    if output["authority_class"] != AUTHORITY_CLASS:
        raise ProtocolError("FORBIDDEN_STATUS_VALUE", "authority_class_must_be_non_authoritative")
    if output["epistemic_class"] != EPISTEMIC_CLASS:
        raise ProtocolError("FORBIDDEN_STATUS_VALUE", "epistemic_class_must_be_unverified")
    if output["production_class"] != PRODUCTION_CLASS:
        raise ProtocolError("FORBIDDEN_STATUS_VALUE", "production_class_must_be_non_production")
    constraints = task["constraints"]
    observations = _require_record_list(
        output["observations"],
        field="observations",
        maximum=constraints["max_observations"],
        required_keys=frozenset({"observation_id", "text", "provenance_ref", "epistemic_class"}),
    )
    claims = _require_record_list(
        output["claims"],
        field="claims",
        maximum=constraints["max_claims"],
        required_keys=frozenset({"claim_id", "text", "epistemic_class"}),
    )
    hypotheses = _require_record_list(
        output["hypotheses"],
        field="hypotheses",
        maximum=constraints["max_hypotheses"],
        required_keys=frozenset({"hypothesis_id", "statement", "label", "epistemic_class"}),
    )
    predictions = _require_record_list(
        output["predictions"],
        field="predictions",
        maximum=constraints["max_predictions"],
        required_keys=frozenset(
            {"prediction_id", "statement", "label", "hypothesis_ref", "epistemic_class"}
        ),
    )
    contradictions = _require_record_list(
        output["contradictions"],
        field="contradictions",
        maximum=constraints["max_contradictions"],
        required_keys=frozenset({"contradiction_id", "left_item_id", "right_item_id", "rationale"}),
    )
    experiments = _require_record_list(
        output["proposed_experiments"],
        field="proposed_experiments",
        maximum=constraints["max_experiments"],
        required_keys=frozenset(
            {
                "experiment_id",
                "hypothesis_id",
                "method",
                "missing_observation",
                "execution_requested",
            }
        ),
    )
    reviews = _require_record_list(
        output["requested_reviews"],
        field="requested_reviews",
        maximum=constraints["max_reviews"],
        required_keys=frozenset({"artifact_id"}),
    )
    uncertainty = _require_record_list(
        output["uncertainty_labels"],
        field="uncertainty_labels",
        maximum=MAX_LIST_ITEMS,
        required_keys=frozenset({"target_id", "label"}),
    )
    provenance = _require_record_list(
        output["provenance_refs"],
        field="provenance_refs",
        maximum=MAX_LIST_ITEMS,
        required_keys=frozenset({"item_id", "item_type", "provenance_ref"}),
    )
    for hypothesis in hypotheses:
        if hypothesis["label"] != "HYPOTHESIS":
            raise ProtocolError("MALFORMED_PAYLOAD", "hypothesis_label_invalid")
    for prediction in predictions:
        if prediction["label"] != "PREDICTION":
            raise ProtocolError("MALFORMED_PAYLOAD", "prediction_label_invalid")
    for record in observations + claims + hypotheses + predictions:
        if record.get("epistemic_class") != EPISTEMIC_CLASS:
            raise ProtocolError("FORBIDDEN_STATUS_VALUE", "output_must_remain_unverified")
    for experiment in experiments:
        if experiment["execution_requested"] is not False:
            raise ProtocolError("FORBIDDEN_STATUS_VALUE", "experiment_must_not_request_execution")
    validated = {
        "protocol_version": PROTOCOL_VERSION,
        "agent_id": AGENT_ID,
        "agent_context_id": context_id,
        "mission_id": mission_id,
        "authority_class": AUTHORITY_CLASS,
        "epistemic_class": EPISTEMIC_CLASS,
        "production_class": PRODUCTION_CLASS,
        "observations": observations,
        "claims": claims,
        "hypotheses": hypotheses,
        "predictions": predictions,
        "contradictions": contradictions,
        "proposed_experiments": experiments,
        "requested_reviews": reviews,
        "uncertainty_labels": uncertainty,
        "provenance_refs": provenance,
    }
    _reject_forbidden_status_strings(validated, field="agent_output")
    return validated


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

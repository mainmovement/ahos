"""Versioned JSON IPC contracts. Standard library only. No pickle. No TCB."""

from __future__ import annotations

import json
import re
from typing import Any


PROTOCOL_VERSION = 1
IPC_PROTOCOL = "AHOS-WORKER-IPC/1"
SERIALIZATION = "json.dumps/json.loads"
WINDOWS_PROCESS_MODEL = "multiprocessing.get_context('spawn')"
MAX_MESSAGE_BYTES = 65536
MAX_STRING_CHARS = 4096
MAX_LIST_ITEMS = 32
MAX_DICT_KEYS = 24
REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")

MESSAGE_WORKER_REQUEST = "WORKER_REQUEST"
MESSAGE_WORKER_RESPONSE = "WORKER_RESPONSE"
MESSAGE_HOST_COMMAND = "HOST_COMMAND"
MESSAGE_PONG = "PONG"
MESSAGE_PROBE_RESULT = "PROBE_RESULT"

STATUS_OK = "OK"
STATUS_DENY = "DENY"
STATUS_REJECT = "REJECT"
STATUS_ERROR = "ERROR"

HOST_CMD_PING = "PING"
HOST_CMD_SHUTDOWN = "SHUTDOWN"
HOST_CMD_RUN_PROBE = "RUN_PROBE"
HOST_CMD_RUN_RESEARCH_TASK = "RUN_RESEARCH_TASK"

FIRST_AGENT_OPERATIONS: frozenset[str] = frozenset(
    {
        "READ_CONTEXT",
        "CREATE_MISSION",
        "RECORD_SOURCE",
        "RECORD_EVIDENCE",
        "CREATE_CLAIM",
        "CREATE_HYPOTHESIS",
        "CREATE_PREDICTION",
        "RECORD_OBSERVATION",
        "RECORD_CONTRADICTION",
        "PROPOSE_EXPERIMENT",
        "RECORD_EXPERIMENT_RESULT",
        "REQUEST_REVIEW",
    }
)
FIRST_AGENT_WRITE_OPERATIONS: frozenset[str] = FIRST_AGENT_OPERATIONS - {"READ_CONTEXT"}

GATED_OPERATIONS: frozenset[str] = frozenset(
    {
        "READ_EPISTEMIC_STATE",
        "READ_SUPPLIED_ARTIFACT",
        "CREATE_CANDIDATE",
    }
)

ALLOWED_OPERATIONS: frozenset[str] = frozenset(
    {
        "READ_CONTEXT",
        "READ_EPISTEMIC_STATE",
        "READ_SUPPLIED_ARTIFACT",
        "CREATE_MISSION",
        "RECORD_SOURCE",
        "RECORD_EVIDENCE",
        "CREATE_CLAIM",
        "CREATE_HYPOTHESIS",
        "CREATE_PREDICTION",
        "RECORD_OBSERVATION",
        "RECORD_CONTRADICTION",
        "PROPOSE_EXPERIMENT",
        "RECORD_EXPERIMENT_RESULT",
        "CREATE_CANDIDATE",
        "REQUEST_REVIEW",
    }
)

HARD_DENY_OPERATIONS: frozenset[str] = frozenset(
    {
        "PROMOTE_KNOWLEDGE",
        "ISSUE_APPROVAL",
        "RECORD_INDEPENDENT_VERIFICATION",
        "CREATE_PRINCIPAL",
        "CREATE_SESSION",
        "DELEGATE_AUTHORITY",
        "MODIFY_POLICY",
        "UPDATE_POLICY",
        "EXECUTION",
        "LIVE_TRADING",
        "AHOS_ACCESS",
        "CREDENTIAL_ACCESS",
        "NETWORK_ACCESS",
        "TELEGRAM",
        "N8N",
        "GIT_MUTATION",
        "SHELL",
        "POWERSHELL",
        "CMD",
        "SUBPROCESS",
        "DYNAMIC_IMPORT",
        "EVAL",
        "EXEC",
        "COMPILE",
        "ENVIRONMENT_SECRET",
        "TCB_SUBMIT",
        "STORE_ACCESS",
        "SPAWN_TRUSTED_WORKER",
    }
)

HARD_DENY_REASONS: dict[str, str] = {
    "PROMOTE_KNOWLEDGE": "promotion_firewall_denied",
    "ISSUE_APPROVAL": "approval_issuance_denied",
    "RECORD_INDEPENDENT_VERIFICATION": "verification_firewall_denied",
    "CREATE_PRINCIPAL": "identity_creation_denied",
    "CREATE_SESSION": "agent_session_issuance_denied",
    "DELEGATE_AUTHORITY": "authority_delegation_denied",
    "MODIFY_POLICY": "policy_modification_denied",
    "UPDATE_POLICY": "policy_modification_denied",
    "EXECUTION": "execution_capability_denied",
    "LIVE_TRADING": "execution_capability_denied",
    "AHOS_ACCESS": "ahos_firewall_denied",
    "CREDENTIAL_ACCESS": "credential_access_denied",
    "NETWORK_ACCESS": "network_denied",
    "TELEGRAM": "network_denied",
    "N8N": "network_denied",
    "GIT_MUTATION": "execution_capability_denied",
    "SHELL": "shell_execution_denied",
    "POWERSHELL": "shell_execution_denied",
    "CMD": "shell_execution_denied",
    "SUBPROCESS": "subprocess_denied",
    "DYNAMIC_IMPORT": "dynamic_code_denied",
    "EVAL": "dynamic_code_denied",
    "EXEC": "dynamic_code_denied",
    "COMPILE": "dynamic_code_denied",
    "ENVIRONMENT_SECRET": "environment_secret_denied",
    "TCB_SUBMIT": "tcb_internals_denied",
    "STORE_ACCESS": "internal_store_denied",
    "SPAWN_TRUSTED_WORKER": "recursive_spawn_denied",
}

FORBIDDEN_AUTHORITY_KEYS: frozenset[str] = frozenset(
    {
        "principal",
        "principal_id",
        "actor_principal_id",
        "session",
        "session_id",
        "operator_session",
        "approval",
        "approval_id",
        "approver",
        "grant",
        "grants",
        "capability_grant",
        "capability",
        "policy",
        "policy_version",
        "tcb",
        "store",
        "private_key",
        "authority_context_ref",
        "command_id",
        "expected_state_version",
        "independent_verification",
        "verification_status",
    }
)

_ALLOWED_MISSION_KEYS = frozenset(
    {
        "question",
        "unknowns",
        "hypothesis_ids",
        "required_evidence",
        "constraints",
        "allowed_methods",
        "authority_capabilities",
        "authority_resources",
        "deliverables",
        "success_criteria",
        "failure_criteria",
        "expires_in_seconds",
        "parent_mission_id",
        "causal_lineage",
    }
)


class ProtocolError(ValueError):
    def __init__(self, error_code: str, message: str) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.message = message


def encode_message(obj: dict[str, Any]) -> bytes:
    if not isinstance(obj, dict):
        raise ProtocolError("MALFORMED_PAYLOAD", "message_must_be_object")
    raw = json.dumps(obj, separators=(",", ":"), allow_nan=False).encode("utf-8")
    if len(raw) > MAX_MESSAGE_BYTES:
        raise ProtocolError("MESSAGE_TOO_LARGE", "message_exceeds_max_bytes")
    return raw


def _reject_duplicate_keys(pairs: list[tuple[Any, Any]]) -> dict[str, Any]:
    decoded: dict[str, Any] = {}
    for key, value in pairs:
        if key in decoded:
            raise ValueError("duplicate_json_key")
        decoded[str(key)] = value
    return decoded


def decode_message(raw: bytes) -> dict[str, Any]:
    if not isinstance(raw, (bytes, bytearray)):
        raise ProtocolError("MALFORMED_JSON", "message_must_be_bytes")
    if len(raw) > MAX_MESSAGE_BYTES:
        raise ProtocolError("MESSAGE_TOO_LARGE", "message_exceeds_max_bytes")
    try:
        text = bytes(raw).decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ProtocolError("MALFORMED_JSON", "message_not_utf8") from exc
    try:
        obj = json.loads(text, object_pairs_hook=_reject_duplicate_keys)
    except json.JSONDecodeError as exc:
        raise ProtocolError("MALFORMED_JSON", "malformed_json") from exc
    except ValueError as exc:
        if str(exc) == "duplicate_json_key":
            raise ProtocolError("DUPLICATE_JSON_KEY", "duplicate_json_key") from exc
        raise ProtocolError("MALFORMED_JSON", "malformed_json") from exc
    if not isinstance(obj, dict):
        raise ProtocolError("MALFORMED_PAYLOAD", "message_must_be_object")
    return obj


def _require_exact_operation(value: Any) -> str:
    if not isinstance(value, str) or not value:
        raise ProtocolError("MALFORMED_PAYLOAD", "operation_required")
    if len(value) > 64:
        raise ProtocolError("MALFORMED_PAYLOAD", "operation_too_long")
    try:
        value.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ProtocolError("MALFORMED_PAYLOAD", "operation_not_ascii") from exc
    if any(ord(char) < 32 or ord(char) == 127 for char in value):
        raise ProtocolError("MALFORMED_PAYLOAD", "operation_control_char")
    if value.strip() != value or " " in value or "\t" in value:
        raise ProtocolError("MALFORMED_PAYLOAD", "operation_not_exact")
    return value


def _require_request_id(value: Any) -> str:
    if not isinstance(value, str) or not REQUEST_ID_RE.fullmatch(value):
        raise ProtocolError("REQUEST_ID_INVALID", "request_id_invalid")
    return value


def _require_version(obj: dict[str, Any]) -> None:
    version = obj.get("protocol_version")
    if version != PROTOCOL_VERSION:
        raise ProtocolError("PROTOCOL_VERSION_MISMATCH", "protocol_version_mismatch")


def _bounded_str(value: Any, *, field: str) -> str:
    if not isinstance(value, str):
        raise ProtocolError("MALFORMED_PAYLOAD", f"{field}_must_be_string")
    if len(value) > MAX_STRING_CHARS:
        raise ProtocolError("MALFORMED_PAYLOAD", f"{field}_too_long")
    if "\x00" in value:
        raise ProtocolError("MALFORMED_PAYLOAD", f"{field}_nul_denied")
    return value


def _bounded_str_list(value: Any, *, field: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ProtocolError("MALFORMED_PAYLOAD", f"{field}_must_be_list")
    if len(value) > MAX_LIST_ITEMS:
        raise ProtocolError("MALFORMED_PAYLOAD", f"{field}_too_many_items")
    return tuple(_bounded_str(item, field=field) for item in value)


def _optional_str(payload: dict[str, Any], key: str) -> str | None:
    if key not in payload or payload[key] is None:
        return None
    return _bounded_str(payload[key], field=key)


def _bounded_int(value: Any, *, field: str, minimum: int, maximum: int) -> int:
    if type(value) is not int:
        raise ProtocolError("MALFORMED_PAYLOAD", f"{field}_must_be_int")
    if value < minimum or value > maximum:
        raise ProtocolError("MALFORMED_PAYLOAD", f"{field}_out_of_range")
    return value


def _reject_authority_fields(payload: dict[str, Any]) -> None:
    for key in payload:
        if key in FORBIDDEN_AUTHORITY_KEYS:
            raise ProtocolError("FORBIDDEN_AUTHORITY_FIELD", f"untrusted_authority_field:{key}")


def _require_keys(payload: dict[str, Any], required: frozenset[str], allowed: frozenset[str]) -> None:
    missing = required - payload.keys()
    if missing:
        raise ProtocolError("MALFORMED_PAYLOAD", f"missing_fields:{','.join(sorted(missing))}")
    extra = payload.keys() - allowed
    if extra:
        raise ProtocolError("MALFORMED_PAYLOAD", f"unknown_fields:{','.join(sorted(extra))}")
    if len(payload) > MAX_DICT_KEYS:
        raise ProtocolError("MALFORMED_PAYLOAD", "payload_too_many_keys")


def validate_worker_context(context: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(context, dict):
        raise ProtocolError("MALFORMED_PAYLOAD", "worker_context_must_be_object")
    allowed = frozenset(
        {"protocol_version", "context_id", "principal_id", "kind", "workspace_artifact_names"}
    )
    _require_keys(
        context,
        frozenset({"protocol_version", "context_id", "principal_id", "kind"}),
        allowed,
    )
    _require_version(context)
    kind = _bounded_str(context["kind"], field="kind")
    if kind != "RESEARCH_AGENT_CONTEXT":
        raise ProtocolError("MALFORMED_PAYLOAD", "worker_context_kind_invalid")
    names = context.get("workspace_artifact_names", [])
    return {
        "protocol_version": PROTOCOL_VERSION,
        "context_id": _bounded_str(context["context_id"], field="context_id"),
        "principal_id": _bounded_str(context["principal_id"], field="principal_id"),
        "kind": kind,
        "workspace_artifact_names": list(_bounded_str_list(names, field="workspace_artifact_names")),
    }


def validate_operation_payload(operation: str, payload: dict[str, Any]) -> dict[str, Any]:
    _reject_authority_fields(payload)
    if operation == "READ_CONTEXT":
        _require_keys(payload, frozenset(), frozenset())
        return {}
    if operation == "READ_EPISTEMIC_STATE":
        _require_keys(payload, frozenset(), frozenset())
        return {}
    if operation == "READ_SUPPLIED_ARTIFACT":
        _require_keys(payload, frozenset({"relative_path"}), frozenset({"relative_path"}))
        return {"relative_path": _bounded_str(payload["relative_path"], field="relative_path")}
    if operation == "CREATE_MISSION":
        required = frozenset(
            {
                "question",
                "unknowns",
                "hypothesis_ids",
                "required_evidence",
                "constraints",
                "allowed_methods",
                "deliverables",
                "success_criteria",
                "failure_criteria",
            }
        )
        _require_keys(payload, required, _ALLOWED_MISSION_KEYS)
        result: dict[str, Any] = {
            "question": _bounded_str(payload["question"], field="question"),
            "unknowns": _bounded_str_list(payload["unknowns"], field="unknowns"),
            "hypothesis_ids": _bounded_str_list(payload["hypothesis_ids"], field="hypothesis_ids"),
            "required_evidence": _bounded_str_list(
                payload["required_evidence"], field="required_evidence"
            ),
            "constraints": _bounded_str_list(payload["constraints"], field="constraints"),
            "allowed_methods": _bounded_str_list(
                payload["allowed_methods"], field="allowed_methods"
            ),
            "deliverables": _bounded_str_list(payload["deliverables"], field="deliverables"),
            "success_criteria": _bounded_str_list(
                payload["success_criteria"], field="success_criteria"
            ),
            "failure_criteria": _bounded_str_list(
                payload["failure_criteria"], field="failure_criteria"
            ),
        }
        if "authority_capabilities" in payload:
            result["authority_capabilities"] = _bounded_str_list(
                payload["authority_capabilities"], field="authority_capabilities"
            )
        if "authority_resources" in payload:
            result["authority_resources"] = _bounded_str_list(
                payload["authority_resources"], field="authority_resources"
            )
        if "expires_in_seconds" in payload:
            result["expires_in_seconds"] = _bounded_int(
                payload["expires_in_seconds"],
                field="expires_in_seconds",
                minimum=1,
                maximum=86400,
            )
        parent = _optional_str(payload, "parent_mission_id")
        if parent is not None:
            result["parent_mission_id"] = parent
        if "causal_lineage" in payload:
            result["causal_lineage"] = _bounded_str_list(
                payload["causal_lineage"], field="causal_lineage"
            )
        return result
    if operation == "RECORD_SOURCE":
        _require_keys(
            payload,
            frozenset({"source_type", "locator", "content_hash"}),
            frozenset({"source_type", "locator", "content_hash"}),
        )
        return {
            "source_type": _bounded_str(payload["source_type"], field="source_type"),
            "locator": _bounded_str(payload["locator"], field="locator"),
            "content_hash": _bounded_str(payload["content_hash"], field="content_hash"),
        }
    if operation == "RECORD_EVIDENCE":
        allowed = frozenset(
            {
                "source_id",
                "content_hash",
                "content_ref",
                "extraction_method",
                "assurance",
                "freshness_max_age_seconds",
            }
        )
        _require_keys(
            payload, frozenset({"source_id", "content_hash", "content_ref"}), allowed
        )
        result = {
            "source_id": _bounded_str(payload["source_id"], field="source_id"),
            "content_hash": _bounded_str(payload["content_hash"], field="content_hash"),
            "content_ref": _bounded_str(payload["content_ref"], field="content_ref"),
        }
        if "extraction_method" in payload:
            result["extraction_method"] = _bounded_str(
                payload["extraction_method"], field="extraction_method"
            )
        if "assurance" in payload:
            result["assurance"] = _bounded_int(
                payload["assurance"], field="assurance", minimum=0, maximum=100
            )
        if "freshness_max_age_seconds" in payload:
            result["freshness_max_age_seconds"] = _bounded_int(
                payload["freshness_max_age_seconds"],
                field="freshness_max_age_seconds",
                minimum=1,
                maximum=86400,
            )
        return result
    if operation == "CREATE_CLAIM":
        _require_keys(
            payload, frozenset({"statement", "evidence_ids"}), frozenset({"statement", "evidence_ids"})
        )
        return {
            "statement": _bounded_str(payload["statement"], field="statement"),
            "evidence_ids": _bounded_str_list(payload["evidence_ids"], field="evidence_ids"),
        }
    if operation == "CREATE_HYPOTHESIS":
        allowed = frozenset({"statement", "falsification_criteria", "supporting_claim_ids"})
        _require_keys(payload, frozenset({"statement", "falsification_criteria"}), allowed)
        result = {
            "statement": _bounded_str(payload["statement"], field="statement"),
            "falsification_criteria": _bounded_str_list(
                payload["falsification_criteria"], field="falsification_criteria"
            ),
        }
        if "supporting_claim_ids" in payload:
            result["supporting_claim_ids"] = _bounded_str_list(
                payload["supporting_claim_ids"], field="supporting_claim_ids"
            )
        return result
    if operation == "CREATE_PREDICTION":
        allowed = frozenset(
            {"hypothesis_id", "expected_observation", "evaluation_deadline_seconds"}
        )
        _require_keys(payload, frozenset({"hypothesis_id", "expected_observation"}), allowed)
        result = {
            "hypothesis_id": _bounded_str(payload["hypothesis_id"], field="hypothesis_id"),
            "expected_observation": _bounded_str(
                payload["expected_observation"], field="expected_observation"
            ),
        }
        if "evaluation_deadline_seconds" in payload:
            result["evaluation_deadline_seconds"] = _bounded_int(
                payload["evaluation_deadline_seconds"],
                field="evaluation_deadline_seconds",
                minimum=1,
                maximum=86400,
            )
        return result
    if operation == "RECORD_OBSERVATION":
        _require_keys(
            payload,
            frozenset({"experiment_run_id", "measured_value", "observation_method"}),
            frozenset({"experiment_run_id", "measured_value", "observation_method"}),
        )
        return {
            "experiment_run_id": _bounded_str(
                payload["experiment_run_id"], field="experiment_run_id"
            ),
            "measured_value": _bounded_str(payload["measured_value"], field="measured_value"),
            "observation_method": _bounded_str(
                payload["observation_method"], field="observation_method"
            ),
        }
    if operation == "RECORD_CONTRADICTION":
        _require_keys(
            payload,
            frozenset({"left_artifact_id", "right_artifact_id", "rationale", "candidate_id"}),
            frozenset({"left_artifact_id", "right_artifact_id", "rationale", "candidate_id"}),
        )
        return {
            "left_artifact_id": _bounded_str(
                payload["left_artifact_id"], field="left_artifact_id"
            ),
            "right_artifact_id": _bounded_str(
                payload["right_artifact_id"], field="right_artifact_id"
            ),
            "rationale": _bounded_str(payload["rationale"], field="rationale"),
            "candidate_id": _bounded_str(payload["candidate_id"], field="candidate_id"),
        }
    if operation == "PROPOSE_EXPERIMENT":
        allowed = frozenset(
            {
                "hypothesis_id",
                "method",
                "preconditions",
                "expected_observations",
                "reproducibility_requirements",
            }
        )
        _require_keys(
            payload,
            frozenset({"hypothesis_id", "method", "preconditions", "expected_observations"}),
            allowed,
        )
        result = {
            "hypothesis_id": _bounded_str(payload["hypothesis_id"], field="hypothesis_id"),
            "method": _bounded_str(payload["method"], field="method"),
            "preconditions": _bounded_str_list(payload["preconditions"], field="preconditions"),
            "expected_observations": _bounded_str_list(
                payload["expected_observations"], field="expected_observations"
            ),
        }
        if "reproducibility_requirements" in payload:
            result["reproducibility_requirements"] = _bounded_str_list(
                payload["reproducibility_requirements"], field="reproducibility_requirements"
            )
        return result
    if operation == "RECORD_EXPERIMENT_RESULT":
        allowed = frozenset({"experiment_plan_id", "outcome", "failure_class"})
        _require_keys(payload, frozenset({"experiment_plan_id", "outcome"}), allowed)
        result = {
            "experiment_plan_id": _bounded_str(
                payload["experiment_plan_id"], field="experiment_plan_id"
            ),
            "outcome": _bounded_str(payload["outcome"], field="outcome"),
        }
        failure = _optional_str(payload, "failure_class")
        if failure is not None:
            result["failure_class"] = failure
        return result
    if operation == "CREATE_CANDIDATE":
        _require_keys(
            payload,
            frozenset({"proposition", "claim_ids", "evidence_ids"}),
            frozenset({"proposition", "claim_ids", "evidence_ids"}),
        )
        return {
            "proposition": _bounded_str(payload["proposition"], field="proposition"),
            "claim_ids": _bounded_str_list(payload["claim_ids"], field="claim_ids"),
            "evidence_ids": _bounded_str_list(payload["evidence_ids"], field="evidence_ids"),
        }
    if operation == "REQUEST_REVIEW":
        _require_keys(payload, frozenset({"candidate_id"}), frozenset({"candidate_id"}))
        return {"candidate_id": _bounded_str(payload["candidate_id"], field="candidate_id")}
    raise ProtocolError("UNKNOWN_OPERATION", "unknown_operation")


def parse_worker_request(obj: dict[str, Any]) -> dict[str, Any]:
    _require_version(obj)
    if obj.get("message_type") != MESSAGE_WORKER_REQUEST:
        raise ProtocolError("MALFORMED_PAYLOAD", "expected_worker_request")
    request_id = _require_request_id(obj.get("request_id"))
    operation = _require_exact_operation(obj.get("operation"))
    payload = obj.get("payload", {})
    if payload is None:
        payload = {}
    if not isinstance(payload, dict):
        raise ProtocolError("MALFORMED_PAYLOAD", "payload_must_be_object")
    return {
        "protocol_version": PROTOCOL_VERSION,
        "message_type": MESSAGE_WORKER_REQUEST,
        "request_id": request_id,
        "operation": operation,
        "payload": payload,
    }


def worker_response(
    *,
    request_id: str,
    status: str,
    result: dict[str, Any] | None = None,
    error_code: str | None = None,
) -> dict[str, Any]:
    return {
        "protocol_version": PROTOCOL_VERSION,
        "message_type": MESSAGE_WORKER_RESPONSE,
        "request_id": request_id,
        "status": status,
        "result": result or {},
        "error_code": error_code,
    }


def host_command(
    *,
    request_id: str,
    command: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "protocol_version": PROTOCOL_VERSION,
        "message_type": MESSAGE_HOST_COMMAND,
        "request_id": request_id,
        "command": command,
        "payload": payload or {},
    }

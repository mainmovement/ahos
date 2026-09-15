"""Trusted-side JSON request handler. Untrusted payloads never become Python objects."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from agent_org.contracts import Capability, Resource
from agent_org.research_host.contracts import HostDecision, HostResult
from research_worker.protocol import (
    ALLOWED_OPERATIONS,
    FIRST_AGENT_OPERATIONS,
    HARD_DENY_OPERATIONS,
    HARD_DENY_REASONS,
    IPC_PROTOCOL,
    PROTOCOL_VERSION,
    SERIALIZATION,
    STATUS_DENY,
    STATUS_OK,
    STATUS_REJECT,
    WINDOWS_PROCESS_MODEL,
    ProtocolError,
    decode_message,
    parse_worker_request,
    validate_operation_payload,
    worker_response,
)


NETWORK_POLICY = "APPLICATION_DENIED"
OS_NETWORK_ISOLATION = "NOT_PROVIDED"
RESOURCE_QUOTAS = "NOT_PROVIDED"


def json_safe(value: Any, *, depth: int = 0) -> Any:
    if depth > 8:
        return "<truncated>"
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        return None
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, (list, tuple)):
        return [json_safe(item, depth=depth + 1) for item in value]
    if isinstance(value, dict):
        return {
            str(key): json_safe(item, depth=depth + 1)
            for key, item in value.items()
            if str(key) not in {"session", "session_id", "tcb", "plane"}
        }
    if is_dataclass(value) and not isinstance(value, type):
        return json_safe(asdict(value), depth=depth + 1)
    return str(type(value).__name__)


def host_result_dict(result: HostResult) -> dict[str, Any]:
    return {
        "decision": result.decision.value,
        "classification": result.classification.value,
        "operation": result.operation,
        "reason": result.reason,
        "resource": result.resource,
        "command_id": result.command_id,
        "correlation_id": result.correlation_id,
        "artifact_id": result.artifact_id,
        "payload": json_safe(result.payload),
    }


def isolated_runtime_overlay() -> dict[str, Any]:
    return {
        "api_boundary": "ENFORCED",
        "process_isolation": True,
        "windows_process_model": WINDOWS_PROCESS_MODEL,
        "ipc_protocol": IPC_PROTOCOL,
        "serialization": SERIALIZATION,
        "same_process_runtime": "WORKER_PROCESS",
        "same_process_residual": False,
        "host_facade_same_process_residual": True,
        "agent_one_implemented": False,
        "network_provided": False,
        "network_policy": NETWORK_POLICY,
        "os_network_isolation": OS_NETWORK_ISOLATION,
        "resource_quotas": RESOURCE_QUOTAS,
        "ahos_connected": False,
        "tcb_object_exposed_to_worker": False,
        "operator_session_exposed_to_worker": False,
    }


def _map_capabilities(values: tuple[str, ...]) -> tuple[Capability, ...]:
    return tuple(Capability(item) for item in values)


def _map_resources(values: tuple[str, ...]) -> tuple[Resource, ...]:
    return tuple(Resource(item) for item in values)


class IsolatedIpcHandler:
    """Fail-closed protocol gate in the trusted process."""

    def __init__(
        self,
        facade: Any,
        *,
        operation_policy: frozenset[str] | None = None,
        policy_locked: bool = False,
    ) -> None:
        self.__facade = facade
        if policy_locked:
            requested = (
                FIRST_AGENT_OPERATIONS
                if operation_policy is None
                else frozenset(operation_policy)
            )
            self.__policy = requested & FIRST_AGENT_OPERATIONS
            self.__policy_locked = True
        else:
            self.__policy = (
                frozenset(operation_policy) if operation_policy is not None else ALLOWED_OPERATIONS
            )
            self.__policy_locked = False

    def policy(self) -> frozenset[str]:
        return self.__policy

    def policy_locked(self) -> bool:
        return self.__policy_locked

    def _effective_operations(
        self, allowed_operations: frozenset[str] | None
    ) -> frozenset[str]:
        if self.__policy_locked:
            requested = self.__policy if allowed_operations is None else frozenset(allowed_operations)
            return requested & self.__policy & FIRST_AGENT_OPERATIONS
        if allowed_operations is not None:
            return frozenset(allowed_operations)
        return self.__policy

    def handle_bytes(
        self,
        raw: bytes,
        *,
        allowed_operations: frozenset[str] | None = None,
    ) -> dict[str, Any]:
        try:
            obj = decode_message(raw)
            parsed = parse_worker_request(obj)
        except ProtocolError as exc:
            request_id = "invalid"
            if isinstance(raw, (bytes, bytearray)):
                try:
                    preview = decode_message(raw)
                    if isinstance(preview.get("request_id"), str):
                        request_id = preview["request_id"][:64]
                except ProtocolError:
                    request_id = "invalid"
            return worker_response(
                request_id=request_id if request_id else "invalid",
                status=STATUS_REJECT,
                error_code=exc.error_code,
                result={"reason": exc.message, "committed": False},
            )
        return self.handle_parsed(parsed, allowed_operations=allowed_operations)

    def handle_parsed(
        self,
        parsed: dict[str, Any],
        *,
        allowed_operations: frozenset[str] | None = None,
    ) -> dict[str, Any]:
        request_id = parsed["request_id"]
        operation = parsed["operation"]
        allowed = self._effective_operations(allowed_operations)
        if operation in HARD_DENY_OPERATIONS:
            reason = HARD_DENY_REASONS[operation]
            return worker_response(
                request_id=request_id,
                status=STATUS_DENY,
                error_code="POLICY_DENIED",
                result={
                    "decision": HostDecision.DENY.value,
                    "operation": operation,
                    "reason": reason,
                    "committed": False,
                    "promoted": False,
                },
            )
        if operation not in allowed:
            if operation in ALLOWED_OPERATIONS and operation not in FIRST_AGENT_OPERATIONS:
                return worker_response(
                    request_id=request_id,
                    status=STATUS_REJECT,
                    error_code="FIRST_AGENT_OPERATION_DENIED",
                    result={"reason": "first_agent_operation_denied", "committed": False},
                )
            return worker_response(
                request_id=request_id,
                status=STATUS_REJECT,
                error_code="UNKNOWN_OPERATION",
                result={"reason": "unknown_operation", "committed": False},
            )
        try:
            payload = validate_operation_payload(operation, parsed["payload"])
        except ProtocolError as exc:
            return worker_response(
                request_id=request_id,
                status=STATUS_REJECT,
                error_code=exc.error_code,
                result={"reason": exc.message, "committed": False},
            )
        try:
            host_result = self._dispatch(operation, payload)
        except (ValueError, TypeError, KeyError) as exc:
            return worker_response(
                request_id=request_id,
                status=STATUS_REJECT,
                error_code="MALFORMED_PAYLOAD",
                result={"reason": f"dispatch_rejected:{exc}", "committed": False},
            )
        encoded = host_result_dict(host_result)
        if operation == "READ_CONTEXT" and isinstance(encoded.get("payload"), dict):
            encoded["payload"]["runtime"] = isolated_runtime_overlay()
        status = STATUS_OK if host_result.accepted else STATUS_DENY
        return worker_response(
            request_id=request_id,
            status=status,
            error_code=None if host_result.accepted else "POLICY_DENIED",
            result=encoded,
        )

    def _dispatch(self, operation: str, payload: dict[str, Any]) -> HostResult:
        api = self.__facade
        if operation == "READ_CONTEXT":
            return api.read_context()
        if operation == "READ_EPISTEMIC_STATE":
            return api.read_epistemic_state()
        if operation == "READ_SUPPLIED_ARTIFACT":
            return api.read_supplied_artifact(payload["relative_path"])
        if operation == "CREATE_MISSION":
            kwargs = dict(payload)
            if "authority_capabilities" in kwargs:
                kwargs["authority_capabilities"] = _map_capabilities(
                    kwargs["authority_capabilities"]
                )
            if "authority_resources" in kwargs:
                kwargs["authority_resources"] = _map_resources(kwargs["authority_resources"])
            return api.create_mission(**kwargs)
        if operation == "RECORD_SOURCE":
            return api.record_source(**payload)
        if operation == "RECORD_EVIDENCE":
            return api.record_evidence(**payload)
        if operation == "CREATE_CLAIM":
            return api.create_claim(**payload)
        if operation == "CREATE_HYPOTHESIS":
            return api.create_hypothesis(**payload)
        if operation == "CREATE_PREDICTION":
            return api.create_prediction(**payload)
        if operation == "RECORD_OBSERVATION":
            return api.record_observation(**payload)
        if operation == "RECORD_CONTRADICTION":
            return api.record_contradiction(**payload)
        if operation == "PROPOSE_EXPERIMENT":
            return api.propose_experiment(**payload)
        if operation == "RECORD_EXPERIMENT_RESULT":
            return api.record_experiment_result(**payload)
        if operation == "CREATE_CANDIDATE":
            return api.create_candidate(**payload)
        if operation == "REQUEST_REVIEW":
            return api.request_review(**payload)
        raise ProtocolError("UNKNOWN_OPERATION", "unknown_operation")

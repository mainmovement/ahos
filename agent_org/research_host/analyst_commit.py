"""Host-side commit of a validated AgentOutput through allow-listed WorkerRequests.

Strategy A: preflight the complete host-derived plan, then execute sequentially.
The TCB is atomic per command, not across a multi-command batch. Therefore:

* preflight failure -> zero writes, REJECTED, NO_COMMIT
* first write failure -> zero committed artifacts from this batch, REJECTED, NO_COMMIT
* later write failure after an accepted write -> PARTIAL_COMMIT_FAILURE (never OK/COMMITTED)
* unexpected exception after an accepted write -> INDETERMINATE_COMMIT_FAILURE

Worker-originated write requests are never executed. The plan is derived only
from a host-validated AgentOutput and ResearchTask.
"""

from __future__ import annotations

from typing import Any

from research_worker.protocol import (
    FIRST_AGENT_OPERATIONS,
    FIRST_AGENT_WRITE_OPERATIONS,
    PROTOCOL_VERSION,
    ProtocolError,
    encode_message,
    validate_operation_payload,
)
from research_worker.research_task import content_hash, validate_agent_output


STATUS_REJECTED = "REJECTED"
STATUS_OK = "OK"
STATUS_PARTIAL = "PARTIAL_COMMIT_FAILURE"
STATUS_INDETERMINATE = "INDETERMINATE_COMMIT_FAILURE"
COMMIT_NO = "NO_COMMIT"
COMMIT_YES = "COMMITTED"
COMMIT_PARTIAL = "PARTIAL_COMMIT_FAILURE"
COMMIT_INDETERMINATE = "INDETERMINATE_COMMIT_FAILURE"


class PreflightError(ValueError):
    def __init__(self, error_code: str, message: str) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.message = message


def rejected_result(error_code: str, reason: str) -> dict[str, Any]:
    return {
        "status": STATUS_REJECTED,
        "commit": COMMIT_NO,
        "tcb_write": "NO_TCB_WRITE",
        "error_code": error_code,
        "reason": reason,
        "agent_output": None,
        "commit_results": [],
        "plan": [],
    }


def collected_requests_contain_writes(collected: list[dict[str, Any]]) -> bool:
    for item in collected:
        operation = item.get("operation")
        if operation in FIRST_AGENT_WRITE_OPERATIONS:
            return True
        if operation not in {None, "READ_CONTEXT"} and operation in FIRST_AGENT_OPERATIONS:
            return True
        if isinstance(operation, str) and operation != "READ_CONTEXT":
            return True
    return False


def finish_research_task(
    handler: Any,
    *,
    task: dict[str, Any],
    expected_context_id: str,
    raw_output: Any,
    collected_requests: list[dict[str, Any]],
) -> dict[str, Any]:
    if collected_requests_contain_writes(collected_requests):
        return rejected_result(
            "WRITE_BEFORE_OUTPUT_VALIDATION",
            "worker_write_request_before_output_validation",
        )
    try:
        validated_output = validate_agent_output(
            raw_output,
            task=task,
            expected_context_id=expected_context_id,
        )
    except ProtocolError as exc:
        return rejected_result(exc.error_code, exc.message)
    return commit_validated_output(handler, validated_output, task)


def build_commit_plan(output: dict[str, Any], task: dict[str, Any]) -> list[dict[str, Any]]:
    plan: list[dict[str, Any]] = []
    unknowns = tuple_or_list([label["label"] for label in output["uncertainty_labels"]])
    if not unknowns:
        unknowns = ["supplied-context-bounds"]
    plan.append(
        {
            "operation": "CREATE_MISSION",
            "payload": {
                "question": task["objective"],
                "unknowns": unknowns,
                "hypothesis_ids": [],
                "required_evidence": ["supplied-context-only"],
                "constraints": ["offline", "non-authoritative", "unverified"],
                "allowed_methods": ["fixed-deterministic-interpreter"],
                "deliverables": ["non-authoritative-agent-output"],
                "success_criteria": ["bounded-research-loop-completed"],
                "failure_criteria": ["malformed-or-forbidden-output"],
            },
        }
    )
    evidence_items = [item for item in task["supplied_items"] if item["item_type"] == "EVIDENCE"]
    if output["claims"] and not evidence_items:
        raise PreflightError("PREFLIGHT_FAILED", "claim_requires_evidence_in_plan")
    for item in evidence_items:
        digest = content_hash(item["text"])
        locator = "research://supplied/" + item["item_id"]
        plan.append(
            {
                "operation": "RECORD_SOURCE",
                "payload": {
                    "source_type": "LOCAL_SYNTHETIC",
                    "locator": locator,
                    "content_hash": digest,
                },
            }
        )
        plan.append(
            {
                "operation": "RECORD_EVIDENCE",
                "payload": {
                    "source_id": "__plan_source__",
                    "content_hash": digest,
                    "content_ref": locator,
                    "extraction_method": "supplied-evidence-item",
                },
                "bind_source": True,
            }
        )
    if output["claims"] and evidence_items:
        for claim in output["claims"]:
            plan.append(
                {
                    "operation": "CREATE_CLAIM",
                    "payload": {
                        "statement": claim["text"],
                        "evidence_ids": ["__plan_evidence__"],
                    },
                    "bind_evidence": True,
                }
            )
    for hypothesis in output["hypotheses"]:
        plan.append(
            {
                "operation": "CREATE_HYPOTHESIS",
                "payload": {
                    "statement": hypothesis["statement"],
                    "falsification_criteria": [
                        "a counter-observation would falsify this hypothesis"
                    ],
                },
            }
        )
    if output["predictions"] and not output["hypotheses"]:
        raise PreflightError("PREFLIGHT_FAILED", "prediction_requires_hypothesis_in_plan")
    if output["proposed_experiments"] and not output["hypotheses"]:
        raise PreflightError("PREFLIGHT_FAILED", "experiment_requires_hypothesis_in_plan")
    if output["hypotheses"]:
        for prediction in output["predictions"]:
            plan.append(
                {
                    "operation": "CREATE_PREDICTION",
                    "payload": {
                        "hypothesis_id": "__plan_hypothesis__",
                        "expected_observation": prediction["statement"],
                    },
                    "bind_hypothesis": True,
                }
            )
        for experiment in output["proposed_experiments"]:
            plan.append(
                {
                    "operation": "PROPOSE_EXPERIMENT",
                    "payload": {
                        "hypothesis_id": "__plan_hypothesis__",
                        "method": experiment["method"],
                        "preconditions": [experiment["missing_observation"]],
                        "expected_observations": [
                            "descriptive missing observation remains unobserved"
                        ],
                    },
                    "bind_hypothesis": True,
                }
            )
    return plan


def preflight_plan(plan: list[dict[str, Any]]) -> None:
    if not plan:
        raise PreflightError("PREFLIGHT_FAILED", "empty_commit_plan")
    for step in plan:
        operation = step["operation"]
        if operation not in FIRST_AGENT_OPERATIONS:
            raise PreflightError("FIRST_AGENT_OPERATION_DENIED", operation)
        if operation == "CREATE_CANDIDATE":
            raise PreflightError("FIRST_AGENT_OPERATION_DENIED", "CREATE_CANDIDATE")
        payload = dict(step["payload"])
        if step.get("bind_source"):
            payload["source_id"] = "source.preflight"
        if step.get("bind_evidence"):
            payload["evidence_ids"] = ["evidence.preflight"]
        if step.get("bind_hypothesis"):
            payload["hypothesis_id"] = "hypothesis.preflight"
        try:
            validate_operation_payload(operation, payload)
        except ProtocolError as exc:
            raise PreflightError(exc.error_code, exc.message) from exc


def commit_validated_output(
    handler: Any,
    output: dict[str, Any],
    task: dict[str, Any],
    *,
    request_prefix: str = "analyst",
) -> dict[str, Any]:
    try:
        plan = build_commit_plan(output, task)
        preflight_plan(plan)
    except PreflightError as exc:
        return rejected_result(exc.error_code, exc.message)

    seq = 0
    commit_results: list[dict[str, Any]] = []
    accepted = 0
    source_ids: list[str] = []
    evidence_ids: list[str] = []
    hypothesis_ids: list[str] = []

    def dispatch(operation: str, payload: dict[str, Any]) -> dict[str, Any]:
        nonlocal seq
        if operation not in FIRST_AGENT_OPERATIONS or operation == "CREATE_CANDIDATE":
            return {
                "status": "REJECT",
                "error_code": "FIRST_AGENT_OPERATION_DENIED",
                "result": {"committed": False},
            }
        seq += 1
        raw = encode_message(
            {
                "protocol_version": PROTOCOL_VERSION,
                "message_type": "WORKER_REQUEST",
                "request_id": f"{request_prefix}-{seq}",
                "operation": operation,
                "payload": payload,
            }
        )
        return handler.handle_bytes(raw)

    try:
        for step in plan:
            payload = dict(step["payload"])
            if step.get("bind_source"):
                if not source_ids:
                    raise PreflightError("PREFLIGHT_FAILED", "source_binding_missing")
                payload["source_id"] = source_ids[-1]
            if step.get("bind_evidence"):
                if not evidence_ids:
                    raise PreflightError("PREFLIGHT_FAILED", "evidence_binding_missing")
                payload["evidence_ids"] = list(evidence_ids)
            if step.get("bind_hypothesis"):
                if not hypothesis_ids:
                    raise PreflightError("PREFLIGHT_FAILED", "hypothesis_binding_missing")
                payload["hypothesis_id"] = hypothesis_ids[0]
            response = dispatch(step["operation"], payload)
            artifact_id = (response.get("result") or {}).get("artifact_id")
            commit_results.append(
                {
                    "operation": step["operation"],
                    "status": response.get("status"),
                    "error_code": response.get("error_code"),
                    "artifact_id": artifact_id,
                }
            )
            if response.get("status") != "OK":
                if accepted == 0:
                    return {
                        "status": STATUS_REJECTED,
                        "commit": COMMIT_NO,
                        "tcb_write": "NO_TCB_WRITE",
                        "error_code": response.get("error_code") or "COMMIT_FAILED",
                        "reason": "first_required_write_failed",
                        "agent_output": output,
                        "commit_results": commit_results,
                        "plan": [step["operation"] for step in plan],
                    }
                return {
                    "status": STATUS_PARTIAL,
                    "commit": COMMIT_PARTIAL,
                    "tcb_write": "PARTIAL_TCB_WRITE",
                    "error_code": response.get("error_code") or "PARTIAL_COMMIT_FAILURE",
                    "reason": "required_write_failed_after_prior_commit",
                    "agent_output": output,
                    "commit_results": commit_results,
                    "plan": [item["operation"] for item in plan],
                }
            accepted += 1
            if step["operation"] == "RECORD_SOURCE" and artifact_id:
                source_ids.append(artifact_id)
            if step["operation"] == "RECORD_EVIDENCE" and artifact_id:
                evidence_ids.append(artifact_id)
            if step["operation"] == "CREATE_HYPOTHESIS" and artifact_id:
                hypothesis_ids.append(artifact_id)
    except PreflightError as exc:
        if accepted == 0:
            return rejected_result(exc.error_code, exc.message)
        return {
            "status": STATUS_INDETERMINATE,
            "commit": COMMIT_INDETERMINATE,
            "tcb_write": "PARTIAL_TCB_WRITE",
            "error_code": exc.error_code,
            "reason": exc.message,
            "agent_output": output,
            "commit_results": commit_results,
            "plan": [item["operation"] for item in plan],
        }
    except (ProtocolError, ValueError, TypeError, KeyError) as exc:
        if accepted == 0:
            return rejected_result("COMMIT_FAILED", str(exc))
        return {
            "status": STATUS_INDETERMINATE,
            "commit": COMMIT_INDETERMINATE,
            "tcb_write": "PARTIAL_TCB_WRITE",
            "error_code": "INDETERMINATE_COMMIT_FAILURE",
            "reason": str(exc),
            "agent_output": output,
            "commit_results": commit_results,
            "plan": [item["operation"] for item in plan],
        }

    return {
        "status": STATUS_OK,
        "commit": COMMIT_YES,
        "tcb_write": "TCB_WRITE",
        "error_code": None,
        "reason": "host_validated_output_committed",
        "agent_output": output,
        "commit_results": commit_results,
        "plan": [item["operation"] for item in plan],
    }


def tuple_or_list(values: list[str]) -> list[str]:
    cleaned = [value for value in values if value]
    return cleaned[:32]

"""Windows spawn supervisor for the untrusted research worker process."""

from __future__ import annotations

import multiprocessing
import secrets
from enum import StrEnum
from typing import Any, NoReturn

from agent_org.research_host.host import ResearchAgentHost
from agent_org.research_host.ipc_handler import IsolatedIpcHandler, isolated_runtime_overlay, json_safe
from agent_org.research_host.analyst_commit import finish_research_task, rejected_result
from research_worker.protocol import (
    FIRST_AGENT_OPERATIONS,
    HOST_CMD_PING,
    HOST_CMD_RUN_PROBE,
    HOST_CMD_RUN_RESEARCH_TASK,
    HOST_CMD_SHUTDOWN,
    IPC_PROTOCOL,
    MAX_MESSAGE_BYTES,
    MESSAGE_PONG,
    MESSAGE_PROBE_RESULT,
    MESSAGE_WORKER_REQUEST,
    PROTOCOL_VERSION,
    SERIALIZATION,
    STATUS_ERROR,
    STATUS_REJECT,
    WINDOWS_PROCESS_MODEL,
    ProtocolError,
    decode_message,
    encode_message,
    host_command,
    parse_worker_request,
    worker_response,
)
from research_worker.research_task import AGENT_ID, validate_research_task
from research_worker.worker import worker_main


class WorkerLifecycle(StrEnum):
    START = "START"
    RUNNING = "RUNNING"
    STOP_REQUESTED = "STOP_REQUESTED"
    STOPPED = "STOPPED"
    FAILED = "FAILED"


class WorkerBoundaryError(RuntimeError):
    def __init__(self, error_code: str, message: str) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.message = message


class IsolatedResearchRuntime:
    """Trusted owner of TCB/session. Worker receives only JSON WorkerContext."""

    def __init__(
        self,
        host: ResearchAgentHost,
        *,
        request_timeout_seconds: float = 5.0,
        start_timeout_seconds: float = 10.0,
    ) -> None:
        self.__host = host
        self.__handler = IsolatedIpcHandler(
            host.facade(),
            operation_policy=FIRST_AGENT_OPERATIONS,
            policy_locked=True,
        )
        self.__timeout = request_timeout_seconds
        self.__start_timeout = start_timeout_seconds
        self.__ctx = multiprocessing.get_context("spawn")
        self.__process: Any | None = None
        self.__conn: Any | None = None
        self.__lifecycle = WorkerLifecycle.STOPPED

    @property
    def lifecycle(self) -> WorkerLifecycle:
        return self.__lifecycle

    def handler(self) -> IsolatedIpcHandler:
        return self.__handler

    def runtime_overlay(self) -> dict[str, Any]:
        return isolated_runtime_overlay()

    def worker_context(self) -> dict[str, Any]:
        context = self.__host.context()
        return {
            "protocol_version": PROTOCOL_VERSION,
            "context_id": context.context_id,
            "principal_id": context.principal_id,
            "kind": context.kind,
            "workspace_artifact_names": list(
                self.__host.facade().read_context().payload["workspace_artifacts"]
            ),
        }

    def start(self) -> None:
        if self.__lifecycle is WorkerLifecycle.RUNNING:
            raise WorkerBoundaryError("ALREADY_RUNNING", "worker_already_running")
        self.__lifecycle = WorkerLifecycle.START
        parent, child = self.__ctx.Pipe(duplex=True)
        process = self.__ctx.Process(
            target=worker_main,
            args=(child, self.worker_context()),
            name="ahos-research-worker",
            daemon=True,
        )
        process.start()
        child.close()
        self.__process = process
        self.__conn = parent
        try:
            ping = self._exchange(
                host_command(request_id=_new_id("ping"), command=HOST_CMD_PING),
                expected_type=MESSAGE_PONG,
                timeout=self.__start_timeout,
            )
        except Exception:
            self._fail_closed()
            raise
        if ping.get("result", {}).get("tcb_module_loaded"):
            self._fail_closed()
            raise WorkerBoundaryError("TCB_IN_WORKER", "worker_imported_tcb_at_start")
        self.__lifecycle = WorkerLifecycle.RUNNING

    def stop(self) -> None:
        if self.__lifecycle in {WorkerLifecycle.STOPPED, WorkerLifecycle.FAILED}:
            self._close_handles()
            return
        self.__lifecycle = WorkerLifecycle.STOP_REQUESTED
        try:
            if self.__conn is not None and self.__process is not None and self.__process.is_alive():
                self.__conn.send_bytes(
                    encode_message(
                        host_command(request_id=_new_id("stop"), command=HOST_CMD_SHUTDOWN)
                    )
                )
                self.__process.join(self.__timeout)
        except Exception:
            pass
        if self.__process is not None and self.__process.is_alive():
            self.__process.terminate()
            self.__process.join(self.__timeout)
        self._close_handles()
        self.__lifecycle = WorkerLifecycle.STOPPED

    def terminate(self) -> None:
        if self.__process is not None and self.__process.is_alive():
            self.__process.terminate()
            self.__process.join(self.__timeout)
        self._close_handles()
        if self.__lifecycle is not WorkerLifecycle.FAILED:
            self.__lifecycle = WorkerLifecycle.STOPPED

    def handle_injected_bytes(self, raw: bytes) -> dict[str, Any]:
        if len(raw) > MAX_MESSAGE_BYTES:
            return worker_response(
                request_id="invalid",
                status=STATUS_REJECT,
                error_code="MESSAGE_TOO_LARGE",
                result={"reason": "message_exceeds_max_bytes", "committed": False},
            )
        return self.__handler.handle_bytes(raw)

    def run_probe(self, probe_name: str, *, timeout: float | None = None) -> dict[str, Any]:
        if self.__lifecycle is not WorkerLifecycle.RUNNING:
            raise WorkerBoundaryError("WORKER_NOT_RUNNING", "worker_not_running")
        request_id = _new_id("probe")
        deadline_timeout = self.__timeout if timeout is None else timeout
        try:
            self._send(
                host_command(
                    request_id=request_id,
                    command=HOST_CMD_RUN_PROBE,
                    payload={"probe": probe_name},
                )
            )
            return self._drain_until_result(request_id, timeout=deadline_timeout)
        except WorkerBoundaryError as exc:
            self._raise_fail_closed(exc)

    def run_research_task(self, task: dict[str, Any]) -> dict[str, Any]:
        if self.__lifecycle is not WorkerLifecycle.RUNNING:
            return rejected_result("WORKER_NOT_RUNNING", "worker_not_running")
        try:
            validated_task = validate_research_task(task)
        except ProtocolError as exc:
            return rejected_result(exc.error_code, exc.message)
        expected_context = self.__host.context().context_id
        if validated_task["agent_context_id"] != expected_context:
            return rejected_result("MALFORMED_PAYLOAD", "agent_context_binding_mismatch")
        request_id = _new_id("research")
        try:
            self._send(
                host_command(
                    request_id=request_id,
                    command=HOST_CMD_RUN_RESEARCH_TASK,
                    payload={"agent_id": AGENT_ID, "task": validated_task},
                )
            )
            message, collected = self._drain_research_task(request_id, timeout=self.__timeout)
        except WorkerBoundaryError as exc:
            self._raise_fail_closed(exc)
        if message.get("status") != "OK":
            return rejected_result(
                str(message.get("error_code") or "WORKER_REJECT"),
                "worker_research_task_rejected",
            )
        raw_output = (message.get("result") or {}).get("agent_output")
        return finish_research_task(
            self.__handler,
            task=validated_task,
            expected_context_id=expected_context,
            raw_output=raw_output,
            collected_requests=collected,
        )

    def _inert_worker_reply(self, parsed: dict[str, Any]) -> dict[str, Any]:
        request_id = parsed["request_id"]
        operation = parsed["operation"]
        if operation == "READ_CONTEXT":
            context = self.__host.context()
            return worker_response(
                request_id=request_id,
                status="OK",
                result={
                    "decision": "ALLOW",
                    "classification": "READ",
                    "operation": "read_context",
                    "reason": "inert_snapshot",
                    "resource": "RESEARCH_CONTEXT",
                    "command_id": None,
                    "correlation_id": None,
                    "artifact_id": None,
                    "payload": {
                        "research_agent_context": json_safe(context),
                        "runtime": isolated_runtime_overlay(),
                        "workspace_artifacts": self.worker_context()["workspace_artifact_names"],
                        "identity_note": "RESEARCH_AGENT_CONTEXT_IS_NOT_HUMAN_IDENTITY",
                    },
                    "committed": False,
                },
            )
        return worker_response(
            request_id=request_id,
            status=STATUS_REJECT,
            error_code="WRITE_BEFORE_OUTPUT_VALIDATION",
            result={"reason": "write_before_output_validation", "committed": False},
        )

    def _drain_research_task(
        self, request_id: str, *, timeout: float
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        collected: list[dict[str, Any]] = []
        while True:
            message = self._recv(timeout=timeout)
            message_type = message.get("message_type")
            if message_type == MESSAGE_WORKER_REQUEST:
                try:
                    parsed = parse_worker_request(message)
                except ProtocolError as exc:
                    raise WorkerBoundaryError(exc.error_code, exc.message) from exc
                collected.append(parsed)
                self._send(self._inert_worker_reply(parsed))
                continue
            if message_type == MESSAGE_PROBE_RESULT:
                if message.get("request_id") != request_id:
                    raise WorkerBoundaryError("REQUEST_ID_MISMATCH", "request_id_mismatch")
                return message, collected
            raise WorkerBoundaryError("WORKER_MALFORMED_RESPONSE", "unexpected_worker_message")

    def _raise_fail_closed(self, exc: WorkerBoundaryError) -> NoReturn:
        proc = self.__process
        if proc is not None:
            proc.join(0.5)
        dead = proc is not None and not proc.is_alive()
        crashed = dead and proc.exitcode not in (0, None)
        self._fail_closed()
        if crashed or (dead and exc.error_code == "WORKER_DISCONNECT"):
            raise WorkerBoundaryError("WORKER_CRASH", "worker_crash") from exc
        raise exc

    def _drain_until_result(
        self,
        request_id: str,
        *,
        timeout: float,
        allowed_operations: frozenset[str] | None = None,
    ) -> dict[str, Any]:
        while True:
            message = self._recv(timeout=timeout)
            message_type = message.get("message_type")
            if message_type == MESSAGE_WORKER_REQUEST:
                raw = encode_message(message)
                response = self.__handler.handle_bytes(raw)
                self._send(response)
                continue
            if message_type == MESSAGE_PROBE_RESULT:
                if message.get("request_id") != request_id:
                    raise WorkerBoundaryError("REQUEST_ID_MISMATCH", "request_id_mismatch")
                return message
            if message_type == MESSAGE_PONG and message.get("request_id") == request_id:
                return message
            raise WorkerBoundaryError("WORKER_MALFORMED_RESPONSE", "unexpected_worker_message")

    def _exchange(
        self, command: dict[str, Any], *, expected_type: str, timeout: float
    ) -> dict[str, Any]:
        self._send(command)
        message = self._recv(timeout=timeout)
        if message.get("message_type") != expected_type:
            raise WorkerBoundaryError("WORKER_MALFORMED_RESPONSE", "unexpected_worker_message")
        if message.get("request_id") != command["request_id"]:
            raise WorkerBoundaryError("REQUEST_ID_MISMATCH", "request_id_mismatch")
        return message

    def _send(self, obj: dict[str, Any]) -> None:
        if self.__conn is None:
            raise WorkerBoundaryError("WORKER_DISCONNECT", "worker_disconnect")
        self.__conn.send_bytes(encode_message(obj))

    def _recv(self, *, timeout: float) -> dict[str, Any]:
        conn = self.__conn
        process = self.__process
        if conn is None or process is None:
            raise WorkerBoundaryError("WORKER_DISCONNECT", "worker_disconnect")
        if not process.is_alive() and not conn.poll(0):
            raise WorkerBoundaryError("WORKER_CRASH", "worker_crash")
        if not conn.poll(timeout):
            if not process.is_alive():
                raise WorkerBoundaryError("WORKER_CRASH", "worker_crash")
            raise WorkerBoundaryError("WORKER_TIMEOUT", "worker_timeout")
        try:
            raw = conn.recv_bytes(MAX_MESSAGE_BYTES)
        except (EOFError, BrokenPipeError) as exc:
            raise WorkerBoundaryError("WORKER_DISCONNECT", "worker_disconnect") from exc
        except ValueError as exc:
            raise WorkerBoundaryError("MESSAGE_TOO_LARGE", "message_exceeds_max_bytes") from exc
        except OSError as exc:
            if process is not None and not process.is_alive():
                raise WorkerBoundaryError("WORKER_CRASH", "worker_crash") from exc
            detail = str(exc).lower()
            if "length" in detail or "too big" in detail or "too large" in detail:
                raise WorkerBoundaryError("MESSAGE_TOO_LARGE", "message_exceeds_max_bytes") from exc
            raise WorkerBoundaryError("WORKER_DISCONNECT", "worker_disconnect") from exc
        try:
            return decode_message(raw)
        except ProtocolError as exc:
            raise WorkerBoundaryError(exc.error_code, exc.message) from exc

    def _fail_closed(self) -> None:
        self.__lifecycle = WorkerLifecycle.FAILED
        try:
            if self.__process is not None and self.__process.is_alive():
                self.__process.terminate()
                self.__process.join(self.__timeout)
        except Exception:
            pass
        self._close_handles()

    def _close_handles(self) -> None:
        if self.__conn is not None:
            try:
                self.__conn.close()
            except Exception:
                pass
        self.__conn = None
        self.__process = None


def fail_closed_response(error_code: str) -> dict[str, Any]:
    return worker_response(
        request_id="invalid",
        status=STATUS_ERROR if error_code in {"WORKER_CRASH", "WORKER_TIMEOUT", "WORKER_DISCONNECT"} else STATUS_REJECT,
        error_code=error_code,
        result={"committed": False, "promoted": False, "granted": False},
    )


def _new_id(prefix: str) -> str:
    return f"{prefix}-{secrets.token_hex(8)}"


__all__ = [
    "IPC_PROTOCOL",
    "IsolatedResearchRuntime",
    "SERIALIZATION",
    "WINDOWS_PROCESS_MODEL",
    "WorkerBoundaryError",
    "WorkerLifecycle",
    "fail_closed_response",
]

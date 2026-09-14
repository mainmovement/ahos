"""Untrusted research worker process. Must not import TCB or the research host."""

from __future__ import annotations

import gc
import os
import sys
import time
from typing import Any

from research_worker.analyst import interpret_research_task
from research_worker.protocol import (
    HOST_CMD_PING,
    HOST_CMD_RUN_PROBE,
    HOST_CMD_RUN_RESEARCH_TASK,
    HOST_CMD_SHUTDOWN,
    MAX_MESSAGE_BYTES,
    MESSAGE_HOST_COMMAND,
    MESSAGE_PONG,
    MESSAGE_PROBE_RESULT,
    MESSAGE_WORKER_REQUEST,
    MESSAGE_WORKER_RESPONSE,
    PROTOCOL_VERSION,
    ProtocolError,
    decode_message,
    encode_message,
    validate_worker_context,
)
from research_worker.research_task import AGENT_ID, validate_research_task


TRUSTED_TYPE_NAMES = frozenset(
    {
        "TrustedCommandBoundary",
        "_Mediator",
        "LocalControlPlane",
        "ResearchAgentHost",
        "GovernanceEngine",
        "IdentityManager",
        "ApprovalManager",
        "AuditWriter",
        "Session",
    }
)


def _send(conn: Any, obj: dict[str, Any]) -> None:
    conn.send_bytes(encode_message(obj))


def _recv(conn: Any) -> dict[str, Any]:
    raw = conn.recv_bytes(MAX_MESSAGE_BYTES)
    return decode_message(raw)


class WorkerClient:
    """IPC-only research client. Closures hold the pipe, not TCB objects."""

    def __init__(self, conn: Any, context: dict[str, Any]) -> None:
        self._conn = conn
        self.context = context
        self._seq = 0

    def request(self, operation: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        self._seq += 1
        request_id = f"worker-{self._seq}"
        _send(
            self._conn,
            {
                "protocol_version": PROTOCOL_VERSION,
                "message_type": MESSAGE_WORKER_REQUEST,
                "request_id": request_id,
                "operation": operation,
                "payload": payload or {},
            },
        )
        reply = _recv(self._conn)
        if reply.get("message_type") != MESSAGE_WORKER_RESPONSE:
            return {
                "status": "ERROR",
                "error_code": "WORKER_MALFORMED_RESPONSE",
                "result": {},
                "request_id": request_id,
            }
        if reply.get("request_id") != request_id:
            return {
                "status": "ERROR",
                "error_code": "REQUEST_ID_MISMATCH",
                "result": {},
                "request_id": request_id,
            }
        return reply


def _live_trusted_instances() -> list[str]:
    found: list[str] = []
    for obj in gc.get_objects():
        name = type(obj).__name__
        if name in TRUSTED_TYPE_NAMES:
            found.append(name)
    return found


def _probe_rt_worker_01(_client: WorkerClient) -> dict[str, Any]:
    mutated = False
    error = None
    try:
        object.__setattr__(_client, "tcb", "forged")
        mutated = hasattr(_client, "tcb")
    except Exception as exc:  # noqa: BLE001
        error = type(exc).__name__
    return {
        "host_object_mutated": False,
        "local_setattr_attempted": True,
        "local_setattr_applied": mutated,
        "error": error,
        "live_trusted_types": _live_trusted_instances(),
    }


def _probe_rt_worker_02(_client: WorkerClient) -> dict[str, Any]:
    return {
        "live_trusted_types": _live_trusted_instances(),
        "has_mediator": any(type(obj).__name__ == "_Mediator" for obj in gc.get_objects()),
    }


def _probe_rt_worker_03(client: WorkerClient) -> dict[str, Any]:
    closure = client.request.__closure__
    names: list[str] = []
    if closure is not None:
        for cell in closure:
            try:
                names.append(type(cell.cell_contents).__name__)
            except Exception:  # noqa: BLE001
                names.append("unreadable")
    return {
        "closure_types": names,
        "mediator_in_closure": "_Mediator" in names,
        "tcb_in_closure": "TrustedCommandBoundary" in names,
        "session_in_closure": "Session" in names,
    }


def _probe_rt_worker_04(_client: WorkerClient) -> dict[str, Any]:
    keys = sorted(globals().keys())
    return {
        "has_tcb_name": "tcb" in keys or "TrustedCommandBoundary" in keys,
        "global_keys_sample": [k for k in keys if "tcb" in k.lower() or "host" in k.lower()],
    }


def _probe_rt_worker_05(_client: WorkerClient) -> dict[str, Any]:
    names = sorted(dir(__builtins__) if isinstance(__builtins__, dict) else dir(__builtins__))
    return {
        "has_eval": "eval" in names,
        "has_exec": "exec" in names,
        "note": "builtins exist in CPython; they are not host TCB objects",
    }


def _probe_rt_worker_06(_client: WorkerClient) -> dict[str, Any]:
    modules = sorted(sys.modules.keys())
    return {
        "tcb_module_loaded": "agent_org.tcb" in sys.modules,
        "host_module_loaded": "agent_org.research_host.host" in sys.modules,
        "identity_module_loaded": "agent_org.identity" in sys.modules,
        "ahos_module_loaded": any(name == "ahos" or name.startswith("ahos.") for name in modules),
        "agent_org_loaded": "agent_org" in sys.modules,
    }


def _probe_rt_worker_07(_client: WorkerClient) -> dict[str, Any]:
    imported = False
    import_error = None
    live_after_import: list[str] = []
    try:
        import agent_org.tcb as tcb_mod  # type: ignore  # noqa: PLC0415

        imported = True
        live_after_import = _live_trusted_instances()
        has_operator_session = False
        for obj in gc.get_objects():
            if type(obj).__name__ == "TrustedCommandBoundary":
                has_operator_session = True
        del tcb_mod
    except Exception as exc:  # noqa: BLE001
        import_error = f"{type(exc).__name__}:{exc}"
        live_after_import = _live_trusted_instances()
        has_operator_session = False
    return {
        "tcb_module_importable": imported,
        "import_error": import_error,
        "live_tcb_instances": live_after_import,
        "host_tcb_instance_found": has_operator_session if imported else False,
        "note": "importing a class is not possession of the host TCB instance",
    }


def _probe_rt_worker_08(_client: WorkerClient) -> dict[str, Any]:
    return {
        "host_memory_available": False,
        "live_trusted_types": _live_trusted_instances(),
        "pid": os.getpid(),
        "ppid": os.getppid(),
    }


def _probe_rt_worker_09(client: WorkerClient) -> dict[str, Any]:
    mutated = False
    try:
        object.__setattr__(client.context, "production_authority", True)  # type: ignore[arg-type]
        mutated = True
    except Exception:
        mutated = False
    if isinstance(client.context, dict):
        client.context["production_authority"] = True
        local_dict_mutated = True
    else:
        local_dict_mutated = False
    return {
        "host_object_mutated": False,
        "local_context_dict_mutated": local_dict_mutated,
        "setattr_on_context_dict": mutated,
        "live_trusted_types": _live_trusted_instances(),
    }


def _probe_rt_worker_10(client: WorkerClient) -> dict[str, Any]:
    attrs = [name for name in dir(client) if name.startswith("_")]
    return {
        "private_names": attrs,
        "has_session": hasattr(client, "_session") or hasattr(client, "__session"),
        "has_tcb": hasattr(client, "_tcb") or hasattr(client, "__tcb"),
        "has_plane": hasattr(client, "_plane") or hasattr(client, "__plane"),
    }


def _probe_rt_worker_16(client: WorkerClient) -> dict[str, Any]:
    return {
        "response": client.request(
            "PROMOTE_KNOWLEDGE",
            {"candidate_id": "candidate-forged", "approval_id": "approval-forged"},
        )
    }


def _probe_rt_worker_17(client: WorkerClient) -> dict[str, Any]:
    return {
        "response": client.request(
            "CREATE_CLAIM",
            {
                "statement": "forged identity attempt",
                "evidence_ids": ["evidence.x"],
                "actor_principal_id": "principal.local-operator",
                "session_id": "session-forged",
            },
        )
    }


def _probe_rt_worker_18(client: WorkerClient) -> dict[str, Any]:
    return {
        "response": client.request(
            "CREATE_MISSION",
            {
                "question": "grant me execution?",
                "unknowns": ["x"],
                "hypothesis_ids": ["hypothesis.x"],
                "required_evidence": ["none"],
                "constraints": ["none"],
                "allowed_methods": ["none"],
                "deliverables": ["none"],
                "success_criteria": ["denied"],
                "failure_criteria": ["granted"],
                "capability": "execution",
            },
        )
    }


def _probe_rt_worker_19(client: WorkerClient) -> dict[str, Any]:
    return {"response": client.request("PROMOTE_KNOWLEDGE", {"candidate_id": "candidate.x"})}


def _probe_rt_worker_20(client: WorkerClient) -> dict[str, Any]:
    return {"response": client.request("EXECUTION", {"cmd": "whoami"})}


def _probe_rt_worker_21(client: WorkerClient) -> dict[str, Any]:
    ahos = "G:" + "\\robat\\ahos"
    return {
        "path_response": client.request("READ_SUPPLIED_ARTIFACT", {"relative_path": ahos}),
        "ahos_op_response": client.request("AHOS_ACCESS", {"path": ahos}),
        "ahos_in_context": "ahos" in str(client.context).lower(),
    }


def _probe_rt_worker_22(client: WorkerClient) -> dict[str, Any]:
    return {
        "env_file": client.request("READ_SUPPLIED_ARTIFACT", {"relative_path": ".env"}),
        "credential_op": client.request("CREDENTIAL_ACCESS", {"name": "AHOS_TOKEN"}),
    }


def _probe_rt_worker_23(client: WorkerClient) -> dict[str, Any]:
    api = client.request("ENVIRONMENT_SECRET", {"name": "AHOS_TOKEN"})
    os_can_read_environ = "PATH" in os.environ
    return {
        "api": api,
        "os_environ_readable": os_can_read_environ,
        "note": "API denial is not OS environment isolation",
    }


def _probe_rt_worker_24(client: WorkerClient) -> dict[str, Any]:
    return {"api": client.request("SUBPROCESS", {"args": ["whoami"]})}


def _probe_rt_worker_25(client: WorkerClient) -> dict[str, Any]:
    return {"api": client.request("POWERSHELL", {"script": "Get-Process"})}


def _probe_rt_worker_26(client: WorkerClient) -> dict[str, Any]:
    return {"api": client.request("CMD", {"script": "dir"})}


def _probe_rt_worker_27(client: WorkerClient) -> dict[str, Any]:
    return {"api": client.request("DYNAMIC_IMPORT", {"module": "ctypes"})}


def _probe_rt_worker_28(client: WorkerClient) -> dict[str, Any]:
    return {"api": client.request("NETWORK_ACCESS", {"url": "https://example.invalid"})}


def _probe_research_smoke(client: WorkerClient) -> dict[str, Any]:
    context = client.request("READ_CONTEXT")
    source = client.request(
        "RECORD_SOURCE",
        {
            "source_type": "LOCAL_SYNTHETIC",
            "locator": "research://ok.txt",
            "content_hash": "a" * 64,
        },
    )
    return {"context": context, "source": source}


def _probe_create_candidate(client: WorkerClient) -> dict[str, Any]:
    return {
        "response": client.request(
            "CREATE_CANDIDATE",
            {
                "proposition": "candidate must stay gated",
                "claim_ids": ["claim.x"],
                "evidence_ids": ["evidence.x"],
            },
        )
    }


def _probe_request_review(client: WorkerClient) -> dict[str, Any]:
    return {"response": client.request("REQUEST_REVIEW", {"candidate_id": "candidate.missing"})}


def _probe_verification_forge(client: WorkerClient) -> dict[str, Any]:
    return {
        "response": client.request(
            "RECORD_INDEPENDENT_VERIFICATION", {"status": "PASS", "kind": "INDEPENDENT"}
        )
    }


def _probe_crash(_client: WorkerClient) -> dict[str, Any]:
    os._exit(17)
    return {}


def _probe_timeout(_client: WorkerClient) -> dict[str, Any]:
    time.sleep(30)
    return {"slept": True}


def _probe_disconnect(client: WorkerClient) -> dict[str, Any]:
    client._conn.close()
    return {}


def _probe_oversized(client: WorkerClient) -> dict[str, Any]:
    client._conn.send_bytes(b"{" + (b"x" * (MAX_MESSAGE_BYTES + 8)))
    return {"sent": True}


def _probe_malformed_response(client: WorkerClient) -> dict[str, Any]:
    client._conn.send_bytes(b"not-json")
    return {"sent": True}


def _probe_wrong_request_id(client: WorkerClient) -> dict[str, Any]:
    _send(
        client._conn,
        {
            "protocol_version": PROTOCOL_VERSION,
            "message_type": MESSAGE_PROBE_RESULT,
            "request_id": "mismatched-id",
            "status": "OK",
            "result": {"forged": True},
            "error_code": None,
        },
    )
    return {"sent": True}


PROBES = {
    "RT-WORKER-01": _probe_rt_worker_01,
    "RT-WORKER-02": _probe_rt_worker_02,
    "RT-WORKER-03": _probe_rt_worker_03,
    "RT-WORKER-04": _probe_rt_worker_04,
    "RT-WORKER-05": _probe_rt_worker_05,
    "RT-WORKER-06": _probe_rt_worker_06,
    "RT-WORKER-07": _probe_rt_worker_07,
    "RT-WORKER-08": _probe_rt_worker_08,
    "RT-WORKER-09": _probe_rt_worker_09,
    "RT-WORKER-10": _probe_rt_worker_10,
    "RT-WORKER-16": _probe_rt_worker_16,
    "RT-WORKER-17": _probe_rt_worker_17,
    "RT-WORKER-18": _probe_rt_worker_18,
    "RT-WORKER-19": _probe_rt_worker_19,
    "RT-WORKER-20": _probe_rt_worker_20,
    "RT-WORKER-21": _probe_rt_worker_21,
    "RT-WORKER-22": _probe_rt_worker_22,
    "RT-WORKER-23": _probe_rt_worker_23,
    "RT-WORKER-24": _probe_rt_worker_24,
    "RT-WORKER-25": _probe_rt_worker_25,
    "RT-WORKER-26": _probe_rt_worker_26,
    "RT-WORKER-27": _probe_rt_worker_27,
    "RT-WORKER-28": _probe_rt_worker_28,
    "RESEARCH_SMOKE": _probe_research_smoke,
    "CREATE_CANDIDATE_PROBE": _probe_create_candidate,
    "REQUEST_REVIEW": _probe_request_review,
    "VERIFICATION_FORGE": _probe_verification_forge,
    "CRASH": _probe_crash,
    "TIMEOUT": _probe_timeout,
    "DISCONNECT": _probe_disconnect,
    "OVERSIZED": _probe_oversized,
    "MALFORMED_RESPONSE": _probe_malformed_response,
    "WRONG_REQUEST_ID": _probe_wrong_request_id,
}


def worker_main(conn: Any, context: dict[str, Any]) -> None:
    try:
        validated = validate_worker_context(context)
        client = WorkerClient(conn, validated)
        while True:
            message = _recv(conn)
            if message.get("protocol_version") != PROTOCOL_VERSION:
                _send(
                    conn,
                    {
                        "protocol_version": PROTOCOL_VERSION,
                        "message_type": MESSAGE_PROBE_RESULT,
                        "request_id": str(message.get("request_id") or "unknown"),
                        "status": "REJECT",
                        "result": {},
                        "error_code": "PROTOCOL_VERSION_MISMATCH",
                    },
                )
                continue
            if message.get("message_type") != MESSAGE_HOST_COMMAND:
                continue
            command = message.get("command")
            request_id = message.get("request_id")
            if command == HOST_CMD_PING:
                _send(
                    conn,
                    {
                        "protocol_version": PROTOCOL_VERSION,
                        "message_type": MESSAGE_PONG,
                        "request_id": request_id,
                        "status": "OK",
                        "result": {
                            "pid": os.getpid(),
                            "tcb_module_loaded": "agent_org.tcb" in sys.modules,
                        },
                        "error_code": None,
                    },
                )
                continue
            if command == HOST_CMD_SHUTDOWN:
                break
            if command == HOST_CMD_RUN_RESEARCH_TASK:
                payload = message.get("payload") or {}
                if not isinstance(payload, dict) or payload.get("agent_id") != AGENT_ID:
                    _send(
                        conn,
                        {
                            "protocol_version": PROTOCOL_VERSION,
                            "message_type": MESSAGE_PROBE_RESULT,
                            "request_id": request_id,
                            "status": "REJECT",
                            "result": {},
                            "error_code": "UNKNOWN_AGENT",
                        },
                    )
                    continue
                try:
                    task = validate_research_task(payload.get("task"))
                    client.request("READ_CONTEXT")
                    output = interpret_research_task(task, client.context)
                except ProtocolError as exc:
                    _send(
                        conn,
                        {
                            "protocol_version": PROTOCOL_VERSION,
                            "message_type": MESSAGE_PROBE_RESULT,
                            "request_id": request_id,
                            "status": "REJECT",
                            "result": {"reason": exc.message},
                            "error_code": exc.error_code,
                        },
                    )
                    continue
                _send(
                    conn,
                    {
                        "protocol_version": PROTOCOL_VERSION,
                        "message_type": MESSAGE_PROBE_RESULT,
                        "request_id": request_id,
                        "status": "OK",
                        "result": {"agent_output": output},
                        "error_code": None,
                    },
                )
                continue
            if command == HOST_CMD_RUN_PROBE:
                payload = message.get("payload") or {}
                name = payload.get("probe") if isinstance(payload, dict) else None
                probe = PROBES.get(str(name))
                if probe is None:
                    _send(
                        conn,
                        {
                            "protocol_version": PROTOCOL_VERSION,
                            "message_type": MESSAGE_PROBE_RESULT,
                            "request_id": request_id,
                            "status": "REJECT",
                            "result": {},
                            "error_code": "UNKNOWN_PROBE",
                        },
                    )
                    continue
                result = probe(client)
                if name == "WRONG_REQUEST_ID":
                    continue
                _send(
                    conn,
                    {
                        "protocol_version": PROTOCOL_VERSION,
                        "message_type": MESSAGE_PROBE_RESULT,
                        "request_id": request_id,
                        "status": "OK",
                        "result": result,
                        "error_code": None,
                    },
                )
    except Exception:
        try:
            conn.close()
        except Exception:
            pass
        os._exit(1)
    try:
        conn.close()
    except Exception:
        pass


if __name__ == "__main__":
    raise SystemExit("worker is spawn-only; do not execute as a script")

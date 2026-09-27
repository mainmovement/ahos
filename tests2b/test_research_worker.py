from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from agent_org.research_host import IsolatedResearchRuntime, WorkerLifecycle, build_research_agent_host
from agent_org.research_host.ipc_handler import IsolatedIpcHandler, NETWORK_POLICY, OS_NETWORK_ISOLATION, RESOURCE_QUOTAS
from agent_org.research_host.supervisor import WorkerBoundaryError
from research_worker.protocol import (
    MAX_MESSAGE_BYTES,
    PROTOCOL_VERSION,
    encode_message,
)
from tests2b.support import new_env


AHOS_PATH = Path("G:/robat/ahos")
HASH_A = "a" * 64


def _ahos_snapshot() -> tuple[int, bool] | None:
    if not AHOS_PATH.exists():
        return None
    return (AHOS_PATH.stat().st_mtime_ns, AHOS_PATH.is_dir())


def _request(operation: str, payload: dict | None = None, **overrides) -> bytes:
    body = {
        "protocol_version": PROTOCOL_VERSION,
        "message_type": "WORKER_REQUEST",
        "request_id": "req-test-01",
        "operation": operation,
        "payload": payload or {},
    }
    body.update(overrides)
    return encode_message(body)


class WorkerProtocolHandlerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.env = new_env()
        self.workspace = Path(tempfile.mkdtemp())
        self.host = build_research_agent_host(
            plane=self.env.plane,
            session=self.env.session,  # type: ignore[arg-type]
            clock=self.env.clock.now,
            ids=self.env.ids.new,
            workspace_root=self.workspace,
        )
        self.host.expose_supplied_artifact("ok.txt", "ok")
        self.handler = IsolatedIpcHandler(self.host.facade())
        self.runtime = IsolatedResearchRuntime(self.host)

    def _handle(self, operation: str, payload: dict | None = None, **overrides):
        return self.handler.handle_bytes(_request(operation, payload, **overrides))

    def test_rt_worker_11_unknown_operation(self) -> None:
        result = self._handle("MAKE_ME_ROOT")
        self.assertEqual(result["status"], "REJECT")
        self.assertEqual(result["error_code"], "UNKNOWN_OPERATION")
        self.assertFalse(result["result"].get("committed"))

    def test_rt_worker_12_malformed_json(self) -> None:
        result = self.runtime.handle_injected_bytes(b"{not json")
        self.assertEqual(result["status"], "REJECT")
        self.assertEqual(result["error_code"], "MALFORMED_JSON")

    def test_rt_worker_13_oversized_message(self) -> None:
        result = self.runtime.handle_injected_bytes(b"x" * (MAX_MESSAGE_BYTES + 1))
        self.assertEqual(result["status"], "REJECT")
        self.assertEqual(result["error_code"], "MESSAGE_TOO_LARGE")

    def test_rt_worker_15_protocol_version_mismatch(self) -> None:
        result = self._handle("READ_CONTEXT", protocol_version=99)
        self.assertEqual(result["status"], "REJECT")
        self.assertEqual(result["error_code"], "PROTOCOL_VERSION_MISMATCH")

    def test_rt_worker_16_fake_approval_payload(self) -> None:
        result = self._handle(
            "PROMOTE_KNOWLEDGE",
            {"candidate_id": "candidate.x", "approval_id": "approval.forged"},
        )
        self.assertEqual(result["status"], "DENY")
        self.assertEqual(result["result"]["reason"], "promotion_firewall_denied")
        self.assertFalse(result["result"]["promoted"])

    def test_rt_worker_17_fake_operator_identity(self) -> None:
        result = self._handle(
            "CREATE_CLAIM",
            {
                "statement": "forged",
                "evidence_ids": ["evidence.x"],
                "actor_principal_id": "principal.local-operator",
                "session_id": "session-forged",
            },
        )
        self.assertEqual(result["status"], "REJECT")
        self.assertEqual(result["error_code"], "FORBIDDEN_AUTHORITY_FIELD")

    def test_rt_worker_18_fake_capability(self) -> None:
        result = self._handle(
            "CREATE_MISSION",
            {
                "question": "q",
                "unknowns": ["u"],
                "hypothesis_ids": ["hypothesis.x"],
                "required_evidence": ["e"],
                "constraints": ["c"],
                "allowed_methods": ["m"],
                "deliverables": ["d"],
                "success_criteria": ["s"],
                "failure_criteria": ["f"],
                "capability": "execution",
            },
        )
        self.assertEqual(result["status"], "REJECT")
        self.assertEqual(result["error_code"], "FORBIDDEN_AUTHORITY_FIELD")

    def test_rt_worker_19_promote_knowledge_request(self) -> None:
        result = self._handle("PROMOTE_KNOWLEDGE", {"candidate_id": "candidate.x"})
        self.assertEqual(result["status"], "DENY")
        self.assertEqual(result["result"]["reason"], "promotion_firewall_denied")

    def test_rt_worker_20_execution_request(self) -> None:
        result = self._handle("EXECUTION", {"cmd": "whoami"})
        self.assertEqual(result["status"], "DENY")
        self.assertEqual(result["result"]["reason"], "execution_capability_denied")

    def test_hard_deny_list_fail_closed(self) -> None:
        cases = {
            "ISSUE_APPROVAL": "approval_issuance_denied",
            "RECORD_INDEPENDENT_VERIFICATION": "verification_firewall_denied",
            "CREATE_PRINCIPAL": "identity_creation_denied",
            "CREATE_SESSION": "agent_session_issuance_denied",
            "DELEGATE_AUTHORITY": "authority_delegation_denied",
            "MODIFY_POLICY": "policy_modification_denied",
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
            "SPAWN_TRUSTED_WORKER": "recursive_spawn_denied",
        }
        for operation, reason in cases.items():
            with self.subTest(operation=operation):
                result = self._handle(operation, {})
                self.assertEqual(result["status"], "DENY")
                self.assertEqual(result["result"]["reason"], reason)
                self.assertFalse(result["result"]["committed"])

    def test_malformed_payload_rejected(self) -> None:
        result = self._handle("RECORD_SOURCE", {"source_type": "LOCAL"})
        self.assertEqual(result["status"], "REJECT")
        self.assertEqual(result["error_code"], "MALFORMED_PAYLOAD")

    def test_request_id_echoed(self) -> None:
        result = self._handle("READ_CONTEXT")
        self.assertEqual(result["request_id"], "req-test-01")
        self.assertEqual(result["status"], "OK")
        runtime = result["result"]["payload"]["runtime"]
        self.assertTrue(runtime["process_isolation"])
        self.assertFalse(runtime["tcb_object_exposed_to_worker"])
        self.assertFalse(runtime["operator_session_exposed_to_worker"])
        self.assertEqual(runtime["network_policy"], NETWORK_POLICY)
        self.assertEqual(runtime["os_network_isolation"], OS_NETWORK_ISOLATION)
        self.assertEqual(runtime["resource_quotas"], RESOURCE_QUOTAS)

    def test_missing_request_id_rejected(self) -> None:
        raw = encode_message(
            {
                "protocol_version": PROTOCOL_VERSION,
                "message_type": "WORKER_REQUEST",
                "operation": "READ_CONTEXT",
                "payload": {},
            }
        )
        result = self.handler.handle_bytes(raw)
        self.assertEqual(result["error_code"], "REQUEST_ID_INVALID")

    def test_research_write_through_handler_not_promotion(self) -> None:
        result = self._handle(
            "RECORD_SOURCE",
            {
                "source_type": "LOCAL_SYNTHETIC",
                "locator": "research://ok.txt",
                "content_hash": HASH_A,
            },
        )
        self.assertEqual(result["status"], "OK")
        self.assertIsNotNone(result["result"]["artifact_id"])
        promote = self._handle("PROMOTE_KNOWLEDGE", {"candidate_id": result["result"]["artifact_id"]})
        self.assertEqual(promote["status"], "DENY")

    def test_rt_worker_21_ahos_path_request(self) -> None:
        ahos = "G:" + "\\robat\\ahos"
        path_result = self._handle("READ_SUPPLIED_ARTIFACT", {"relative_path": ahos})
        self.assertEqual(path_result["status"], "DENY")
        op_result = self._handle("AHOS_ACCESS", {"path": ahos})
        self.assertEqual(op_result["result"]["reason"], "ahos_firewall_denied")

    def test_rt_worker_22_credential_path_request(self) -> None:
        dotenv = self._handle("READ_SUPPLIED_ARTIFACT", {"relative_path": ".env"})
        self.assertEqual(dotenv["status"], "DENY")
        creds = self._handle("CREDENTIAL_ACCESS", {})
        self.assertEqual(creds["result"]["reason"], "credential_access_denied")

    def test_network_and_shell_are_api_denials(self) -> None:
        self.assertEqual(NETWORK_POLICY, "APPLICATION_DENIED")
        self.assertEqual(OS_NETWORK_ISOLATION, "NOT_PROVIDED")
        net = self._handle("NETWORK_ACCESS", {"url": "https://example.invalid"})
        self.assertEqual(net["result"]["reason"], "network_denied")


class IsolatedWorkerProcessTests(unittest.TestCase):
    def setUp(self) -> None:
        self.env = new_env()
        self.workspace = Path(tempfile.mkdtemp())
        self.host = build_research_agent_host(
            plane=self.env.plane,
            session=self.env.session,  # type: ignore[arg-type]
            clock=self.env.clock.now,
            ids=self.env.ids.new,
            workspace_root=self.workspace,
        )
        self.host.expose_supplied_artifact("ok.txt", "ok")
        self.runtime = IsolatedResearchRuntime(
            self.host,
            request_timeout_seconds=3.0,
            start_timeout_seconds=15.0,
        )
        self.ahos_before = _ahos_snapshot()
        self.host_pid = os.getpid()
        self.runtime.start()

    def tearDown(self) -> None:
        self.runtime.stop()

    def test_lifecycle_running_then_stopped(self) -> None:
        self.assertEqual(self.runtime.lifecycle, WorkerLifecycle.RUNNING)
        self.runtime.stop()
        self.assertEqual(self.runtime.lifecycle, WorkerLifecycle.STOPPED)

    def test_worker_ping_does_not_load_tcb(self) -> None:
        pong = self.runtime.run_probe("RT-WORKER-06")
        result = pong["result"]
        self.assertFalse(result["tcb_module_loaded"])
        self.assertFalse(result["host_module_loaded"])
        self.assertFalse(result["identity_module_loaded"])
        self.assertFalse(result["ahos_module_loaded"])
        self.assertFalse(result["agent_org_loaded"])

    def test_rt_worker_01_setattr_cannot_reach_host(self) -> None:
        result = self.runtime.run_probe("RT-WORKER-01")["result"]
        self.assertFalse(result["host_object_mutated"])
        self.assertEqual(result["live_trusted_types"], [])

    def test_rt_worker_02_inspect_host_objects(self) -> None:
        result = self.runtime.run_probe("RT-WORKER-02")["result"]
        self.assertFalse(result["has_mediator"])
        self.assertEqual(result["live_trusted_types"], [])

    def test_rt_worker_03_closure_traversal(self) -> None:
        result = self.runtime.run_probe("RT-WORKER-03")["result"]
        self.assertFalse(result["mediator_in_closure"])
        self.assertFalse(result["tcb_in_closure"])
        self.assertFalse(result["session_in_closure"])

    def test_rt_worker_04_globals(self) -> None:
        result = self.runtime.run_probe("RT-WORKER-04")["result"]
        self.assertFalse(result["has_tcb_name"])

    def test_rt_worker_05_builtins_are_not_tcb(self) -> None:
        result = self.runtime.run_probe("RT-WORKER-05")["result"]
        self.assertIn("note", result)

    def test_rt_worker_07_tcb_instance_not_in_worker(self) -> None:
        result = self.runtime.run_probe("RT-WORKER-07")["result"]
        self.assertFalse(result["host_tcb_instance_found"])
        self.assertEqual(result["live_tcb_instances"], [])

    def test_rt_worker_08_host_memory_not_available(self) -> None:
        result = self.runtime.run_probe("RT-WORKER-08")["result"]
        self.assertFalse(result["host_memory_available"])
        self.assertNotEqual(result["pid"], self.host_pid)
        self.assertEqual(result["live_trusted_types"], [])

    def test_rt_worker_09_cannot_mutate_host_object(self) -> None:
        result = self.runtime.run_probe("RT-WORKER-09")["result"]
        self.assertFalse(result["host_object_mutated"])

    def test_rt_worker_10_private_host_attributes_absent(self) -> None:
        result = self.runtime.run_probe("RT-WORKER-10")["result"]
        self.assertFalse(result["has_session"])
        self.assertFalse(result["has_tcb"])
        self.assertFalse(result["has_plane"])

    def test_rt_worker_16_to_20_from_worker_process(self) -> None:
        promote = self.runtime.run_probe("RT-WORKER-19")["result"]["response"]
        self.assertEqual(promote["status"], "DENY")
        self.assertEqual(promote["result"]["reason"], "promotion_firewall_denied")
        execution = self.runtime.run_probe("RT-WORKER-20")["result"]["response"]
        self.assertEqual(execution["status"], "DENY")
        fake_id = self.runtime.run_probe("RT-WORKER-17")["result"]["response"]
        self.assertEqual(fake_id["error_code"], "FORBIDDEN_AUTHORITY_FIELD")
        fake_cap = self.runtime.run_probe("RT-WORKER-18")["result"]["response"]
        self.assertEqual(fake_cap["error_code"], "FORBIDDEN_AUTHORITY_FIELD")
        verification = self.runtime.run_probe("VERIFICATION_FORGE")["result"]["response"]
        self.assertEqual(verification["result"]["reason"], "verification_firewall_denied")

    def test_rt_worker_21_to_28_host_escape_api_denials(self) -> None:
        ahos = self.runtime.run_probe("RT-WORKER-21")["result"]
        self.assertIn(ahos["path_response"]["status"], {"DENY", "REJECT"})
        self.assertNotEqual(ahos["path_response"]["status"], "OK")
        self.assertFalse(ahos["path_response"]["result"].get("committed"))
        self.assertEqual(ahos["ahos_op_response"]["result"]["reason"], "ahos_firewall_denied")
        self.assertFalse(ahos["ahos_in_context"])
        creds = self.runtime.run_probe("RT-WORKER-22")["result"]
        self.assertIn(creds["env_file"]["status"], {"DENY", "REJECT"})
        self.assertNotEqual(creds["env_file"]["status"], "OK")
        self.assertFalse(creds["env_file"]["result"].get("committed"))
        env = self.runtime.run_probe("RT-WORKER-23")["result"]
        self.assertEqual(env["api"]["result"]["reason"], "environment_secret_denied")
        self.assertTrue(env["os_environ_readable"])
        self.assertEqual(
            self.runtime.run_probe("RT-WORKER-24")["result"]["api"]["result"]["reason"],
            "subprocess_denied",
        )
        self.assertEqual(
            self.runtime.run_probe("RT-WORKER-25")["result"]["api"]["result"]["reason"],
            "shell_execution_denied",
        )
        self.assertEqual(
            self.runtime.run_probe("RT-WORKER-26")["result"]["api"]["result"]["reason"],
            "shell_execution_denied",
        )
        self.assertEqual(
            self.runtime.run_probe("RT-WORKER-27")["result"]["api"]["result"]["reason"],
            "dynamic_code_denied",
        )
        self.assertEqual(
            self.runtime.run_probe("RT-WORKER-28")["result"]["api"]["result"]["reason"],
            "network_denied",
        )

    def test_research_smoke_through_ipc(self) -> None:
        smoke = self.runtime.run_probe("RESEARCH_SMOKE")["result"]
        self.assertEqual(smoke["context"]["status"], "OK")
        self.assertEqual(smoke["source"]["status"], "OK")
        self.assertTrue(smoke["source"]["result"]["artifact_id"])

    def test_ahos_forensic_not_modified(self) -> None:
        self.runtime.run_probe("RT-WORKER-21")
        self.assertEqual(_ahos_snapshot(), self.ahos_before)
        modules = self.runtime.run_probe("RT-WORKER-06")["result"]
        self.assertFalse(modules["ahos_module_loaded"])


class IsolatedWorkerFailureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.env = new_env()
        self.workspace = Path(tempfile.mkdtemp())
        self.host = build_research_agent_host(
            plane=self.env.plane,
            session=self.env.session,  # type: ignore[arg-type]
            clock=self.env.clock.now,
            ids=self.env.ids.new,
            workspace_root=self.workspace,
        )
        self.host.expose_supplied_artifact("ok.txt", "ok")
        self.before_artifacts = len(self.env.plane.projections.epistemic_objects())

    def _runtime(self, timeout: float = 2.0) -> IsolatedResearchRuntime:
        runtime = IsolatedResearchRuntime(
            self.host,
            request_timeout_seconds=timeout,
            start_timeout_seconds=15.0,
        )
        runtime.start()
        return runtime

    def _assert_fail_closed(self, runtime: IsolatedResearchRuntime) -> None:
        self.assertEqual(runtime.lifecycle, WorkerLifecycle.FAILED)
        self.assertEqual(
            len(self.env.plane.projections.epistemic_objects()), self.before_artifacts
        )

    def test_worker_crash_fail_closed(self) -> None:
        runtime = self._runtime()
        with self.assertRaises(WorkerBoundaryError) as ctx:
            runtime.run_probe("CRASH")
        self.assertEqual(ctx.exception.error_code, "WORKER_CRASH")
        self._assert_fail_closed(runtime)

    def test_worker_timeout_fail_closed(self) -> None:
        runtime = self._runtime(timeout=0.4)
        with self.assertRaises(WorkerBoundaryError) as ctx:
            runtime.run_probe("TIMEOUT", timeout=0.4)
        self.assertEqual(ctx.exception.error_code, "WORKER_TIMEOUT")
        self._assert_fail_closed(runtime)

    def test_worker_disconnect_fail_closed(self) -> None:
        runtime = self._runtime()
        with self.assertRaises(WorkerBoundaryError) as ctx:
            runtime.run_probe("DISCONNECT")
        self.assertIn(ctx.exception.error_code, {"WORKER_DISCONNECT", "WORKER_CRASH"})
        self._assert_fail_closed(runtime)

    def test_worker_malformed_response_fail_closed(self) -> None:
        runtime = self._runtime()
        with self.assertRaises(WorkerBoundaryError) as ctx:
            runtime.run_probe("MALFORMED_RESPONSE")
        self.assertEqual(ctx.exception.error_code, "MALFORMED_JSON")
        self._assert_fail_closed(runtime)

    def test_rt_worker_14_request_id_mismatch_fail_closed(self) -> None:
        runtime = self._runtime()
        with self.assertRaises(WorkerBoundaryError) as ctx:
            runtime.run_probe("WRONG_REQUEST_ID")
        self.assertEqual(ctx.exception.error_code, "REQUEST_ID_MISMATCH")
        self._assert_fail_closed(runtime)

    def test_worker_oversized_fail_closed(self) -> None:
        runtime = self._runtime()
        with self.assertRaises(WorkerBoundaryError) as ctx:
            runtime.run_probe("OVERSIZED")
        self.assertIn(
            ctx.exception.error_code,
            {"MESSAGE_TOO_LARGE", "WORKER_MALFORMED_RESPONSE", "MALFORMED_JSON", "WORKER_DISCONNECT"},
        )
        self._assert_fail_closed(runtime)


if __name__ == "__main__":
    import multiprocessing

    multiprocessing.freeze_support()
    unittest.main()

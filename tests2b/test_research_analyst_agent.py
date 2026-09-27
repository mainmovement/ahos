from __future__ import annotations

import inspect
import tempfile
import unittest
from pathlib import Path

from agent_org.epistemic import KnowledgeCandidate, KnowledgeState
from agent_org.research_host import IsolatedResearchRuntime, WorkerLifecycle, build_research_agent_host
from agent_org.research_host.analyst_commit import (
    build_commit_plan,
    finish_research_task,
)
from agent_org.research_host.ipc_handler import IsolatedIpcHandler
from agent_org.research_host.supervisor import WorkerBoundaryError
from research_worker import analyst as analyst_mod
from research_worker.analyst import interpret_research_task
from research_worker.protocol import (
    ALLOWED_OPERATIONS,
    FIRST_AGENT_OPERATIONS,
    GATED_OPERATIONS,
    MAX_STRING_CHARS,
    PROTOCOL_VERSION,
    ProtocolError,
    decode_message,
    encode_message,
)
from research_worker.research_task import (
    AGENT_ID,
    validate_agent_output,
    validate_research_task,
)
from tests2b.support import new_env


AHOS_PATH = Path("G:/robat/ahos")
CONTEXT_ID = "research-context.local-cognitive"


def _ahos_snapshot() -> tuple[int, bool] | None:
    if not AHOS_PATH.exists():
        return None
    return (AHOS_PATH.stat().st_mtime_ns, AHOS_PATH.is_dir())


def _constraints(**overrides: int) -> dict[str, int]:
    values = {
        "max_observations": 8,
        "max_claims": 8,
        "max_hypotheses": 8,
        "max_predictions": 8,
        "max_contradictions": 8,
        "max_experiments": 8,
        "max_reviews": 8,
    }
    values.update(overrides)
    return values


def _item(item_id: str, item_type: str, text: str, provenance_ref: str | None = None) -> dict:
    return {
        "item_id": item_id,
        "item_type": item_type,
        "text": text,
        "provenance_ref": provenance_ref,
    }


def _task(items: list[dict] | None = None, **overrides) -> dict:
    body = {
        "protocol_version": PROTOCOL_VERSION,
        "task_id": "task.research-analyst-01",
        "agent_context_id": CONTEXT_ID,
        "mission_id": None,
        "objective": "inspect the supplied bounded context",
        "supplied_items": items
        or [
            _item("item.obs-1", "OBSERVATION", "the valve is closed", "prov.local-1"),
            _item("item.ev-1", "EVIDENCE", "log line says closed", "prov.local-1"),
            _item("item.claim-1", "CLAIM", "the valve remains closed"),
            _item("item.hyp-1", "HYPOTHESIS", "the valve is closed because pressure dropped"),
            _item("item.pred-1", "PREDICTION", "the next log line will still say closed"),
        ],
        "constraints": _constraints(),
    }
    body.update(overrides)
    return body


class ResearchTaskValidationTests(unittest.TestCase):
    def test_valid_bounded_research_task(self) -> None:
        validated = validate_research_task(_task())
        self.assertEqual(validated["protocol_version"], PROTOCOL_VERSION)
        self.assertEqual(len(validated["supplied_items"]), 5)

    def test_malformed_task_rejection(self) -> None:
        with self.assertRaises(ProtocolError) as ctx:
            validate_research_task({"protocol_version": PROTOCOL_VERSION})
        self.assertEqual(ctx.exception.error_code, "MALFORMED_PAYLOAD")

    def test_unknown_field_rejection(self) -> None:
        task = _task()
        task["unexpected"] = "no"
        with self.assertRaises(ProtocolError) as ctx:
            validate_research_task(task)
        self.assertIn("unknown_fields", ctx.exception.message)

    def test_oversized_task_rejection(self) -> None:
        task = _task()
        task["objective"] = "x" * (MAX_STRING_CHARS + 1)
        with self.assertRaises(ProtocolError) as ctx:
            validate_research_task(task)
        self.assertEqual(ctx.exception.error_code, "MALFORMED_PAYLOAD")

    def test_forbidden_authority_field_rejection(self) -> None:
        task = _task()
        task["session"] = "session-forged"
        with self.assertRaises(ProtocolError) as ctx:
            validate_research_task(task)
        self.assertEqual(ctx.exception.error_code, "FORBIDDEN_AUTHORITY_FIELD")

    def test_forbidden_url_path_network_rejection(self) -> None:
        with self.assertRaises(ProtocolError) as ctx:
            validate_research_task(_task([_item("item.bad-1", "CLAIM", "see https://example.invalid")]))
        self.assertEqual(ctx.exception.error_code, "FORBIDDEN_NETWORK_LOCATOR")
        with self.assertRaises(ProtocolError) as ctx:
            validate_research_task(_task([_item("item.bad-2", "CLAIM", "G:" + "\\robat\\ahos\\secret.txt")]))
        self.assertEqual(ctx.exception.error_code, "FORBIDDEN_FILESYSTEM_PATH")
        with self.assertRaises(ProtocolError) as ctx:
            validate_research_task(_task([_item("item.bad-3", "CLAIM", "eval('1')")]))
        self.assertEqual(ctx.exception.error_code, "FORBIDDEN_EXECUTABLE_CONTENT")


class DeterministicInterpreterTests(unittest.TestCase):
    def test_deterministic_output_from_identical_input(self) -> None:
        context = {"context_id": CONTEXT_ID}
        first = interpret_research_task(_task(), context)
        second = interpret_research_task(_task(), context)
        self.assertEqual(first, second)

    def test_claim_evidence_distinction(self) -> None:
        output = interpret_research_task(_task(), {"context_id": CONTEXT_ID})
        claim_ids = {item["claim_id"] for item in output["claims"]}
        observation_ids = {item["observation_id"] for item in output["observations"]}
        evidence_ids = {
            item["item_id"] for item in output["provenance_refs"] if item["item_type"] == "EVIDENCE"
        }
        self.assertIn("item.claim-1", claim_ids)
        self.assertNotIn("item.ev-1", claim_ids)
        self.assertNotIn("item.ev-1", observation_ids)
        self.assertIn("item.ev-1", evidence_ids)
        self.assertNotIn("item.claim-1", evidence_ids)

    def test_hypothesis_and_prediction_labeling(self) -> None:
        output = interpret_research_task(_task(), {"context_id": CONTEXT_ID})
        self.assertEqual(output["hypotheses"][0]["label"], "HYPOTHESIS")
        self.assertEqual(output["predictions"][0]["label"], "PREDICTION")
        self.assertEqual(output["hypotheses"][0]["epistemic_class"], "UNVERIFIED")

    def test_contradiction_creation(self) -> None:
        output = interpret_research_task(
            _task(
                [
                    _item("item.a", "CLAIM", "the valve is closed"),
                    _item("item.b", "CLAIM", "NOT the valve is closed"),
                ]
            ),
            {"context_id": CONTEXT_ID},
        )
        self.assertEqual(len(output["contradictions"]), 1)
        self.assertEqual(output["contradictions"][0]["left_item_id"], "item.a")
        self.assertEqual(output["contradictions"][0]["right_item_id"], "item.b")

    def test_experiment_proposal(self) -> None:
        output = interpret_research_task(
            _task([_item("item.hyp-1", "HYPOTHESIS", "pressure dropped")]),
            {"context_id": CONTEXT_ID},
        )
        self.assertEqual(len(output["proposed_experiments"]), 1)
        self.assertFalse(output["proposed_experiments"][0]["execution_requested"])

    def test_review_request_creation(self) -> None:
        output = interpret_research_task(_task(), {"context_id": CONTEXT_ID})
        self.assertEqual(output["requested_reviews"][0], {"artifact_id": "item.claim-1"})

    def test_output_bounds(self) -> None:
        output = interpret_research_task(
            _task(
                [
                    _item("item.claim-1", "CLAIM", "alpha"),
                    _item("item.claim-2", "CLAIM", "beta"),
                ],
                constraints=_constraints(max_reviews=1),
            ),
            {"context_id": CONTEXT_ID},
        )
        self.assertEqual(len(output["requested_reviews"]), 1)

    def test_output_forbidden_status_rejection(self) -> None:
        output = interpret_research_task(_task(), {"context_id": CONTEXT_ID})
        output["epistemic_class"] = "VERIFIED"
        with self.assertRaises(ProtocolError) as ctx:
            validate_agent_output(output, task=validate_research_task(_task()), expected_context_id=CONTEXT_ID)
        self.assertEqual(ctx.exception.error_code, "FORBIDDEN_STATUS_VALUE")

    def test_output_forbidden_key_rejection(self) -> None:
        output = interpret_research_task(_task(), {"context_id": CONTEXT_ID})
        output["session"] = "no"
        with self.assertRaises(ProtocolError) as ctx:
            validate_agent_output(output, task=validate_research_task(_task()), expected_context_id=CONTEXT_ID)
        self.assertEqual(ctx.exception.error_code, "FORBIDDEN_AUTHORITY_FIELD")
        output = interpret_research_task(_task(), {"context_id": CONTEXT_ID})
        output["extra"] = "no"
        with self.assertRaises(ProtocolError) as ctx:
            validate_agent_output(output, task=validate_research_task(_task()), expected_context_id=CONTEXT_ID)
        self.assertIn("unknown_fields", ctx.exception.message)


class IsolatedResearchAnalystTests(unittest.TestCase):
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
        self.runtime = IsolatedResearchRuntime(
            self.host,
            request_timeout_seconds=5.0,
            start_timeout_seconds=15.0,
        )
        self.ahos_before = _ahos_snapshot()
        self.before_artifacts = len(self.env.plane.projections.epistemic_objects())
        self.runtime.start()

    def tearDown(self) -> None:
        self.runtime.stop()

    def test_mission_context_binding_and_valid_loop(self) -> None:
        result = self.runtime.run_research_task(_task())
        self.assertEqual(result["status"], "OK")
        output = result["agent_output"]
        self.assertEqual(output["agent_context_id"], CONTEXT_ID)
        self.assertIsNone(output["mission_id"])
        self.assertEqual(output["authority_class"], "NON_AUTHORITATIVE")
        self.assertEqual(output["epistemic_class"], "UNVERIFIED")
        self.assertEqual(output["production_class"], "NON_PRODUCTION")
        self.assertEqual(output["agent_id"], AGENT_ID)
        mismatch = _task(agent_context_id="research-context.other")
        rejected = self.runtime.run_research_task(mismatch)
        self.assertEqual(rejected["status"], "REJECTED")
        self.assertEqual(rejected["commit"], "NO_COMMIT")
        self.assertEqual(rejected["tcb_write"], "NO_TCB_WRITE")

    def test_repeated_identical_task_produces_identical_result(self) -> None:
        first = self.runtime.run_research_task(_task())["agent_output"]
        second = self.runtime.run_research_task(_task())["agent_output"]
        self.assertEqual(first, second)

    def test_no_session_tcb_or_host_callback_in_worker(self) -> None:
        self.runtime.run_research_task(_task())
        modules = self.runtime.run_probe("RT-WORKER-06")["result"]
        self.assertFalse(modules["tcb_module_loaded"])
        self.assertFalse(modules["host_module_loaded"])
        self.assertFalse(modules["ahos_module_loaded"])
        types = self.runtime.run_probe("RT-WORKER-02")["result"]
        self.assertEqual(types["live_trusted_types"], [])
        self.assertFalse(types["has_mediator"])
        private = self.runtime.run_probe("RT-WORKER-10")["result"]
        self.assertFalse(private["has_session"])
        self.assertFalse(private["has_tcb"])
        tcb = self.runtime.run_probe("RT-WORKER-07")["result"]
        self.assertFalse(tcb["host_tcb_instance_found"])

    def test_no_host_invoke_network_credentials_or_ahos(self) -> None:
        source = inspect.getsource(IsolatedResearchRuntime.run_research_task)
        self.assertNotIn("invoke(", source)
        analyst_source = inspect.getsource(analyst_mod)
        self.assertNotIn("ResearchAgentHost.invoke", analyst_source)
        self.assertNotIn("urllib", analyst_source)
        self.assertNotIn("socket", analyst_source)
        self.assertNotIn("os.environ", analyst_source)
        self.assertNotIn("getenv", analyst_source)
        self.assertNotIn("ahos", analyst_source.lower())
        net = self.runtime.run_probe("RT-WORKER-28")["result"]["api"]
        self.assertEqual(net["result"]["reason"], "network_denied")
        creds = self.runtime.run_probe("RT-WORKER-22")["result"]
        self.assertEqual(creds["credential_op"]["result"]["reason"], "credential_access_denied")
        self.runtime.run_research_task(_task())
        self.assertEqual(_ahos_snapshot(), self.ahos_before)

    def test_no_promotion_verification_or_governance(self) -> None:
        result = self.runtime.run_research_task(_task())
        operations = [item["operation"] for item in result["commit_results"]]
        self.assertNotIn("PROMOTE_KNOWLEDGE", operations)
        self.assertNotIn("RECORD_INDEPENDENT_VERIFICATION", operations)
        self.assertNotIn("CREATE_CANDIDATE", operations)
        self.assertNotIn("MODIFY_POLICY", operations)
        self.assertNotIn("CREATE_SESSION", operations)
        promote = self.runtime.handler().handle_bytes(
            encode_message(
                {
                    "protocol_version": PROTOCOL_VERSION,
                    "message_type": "WORKER_REQUEST",
                    "request_id": "req-analyst-promote",
                    "operation": "PROMOTE_KNOWLEDGE",
                    "payload": {"candidate_id": "candidate.x"},
                }
            ),
            allowed_operations=FIRST_AGENT_OPERATIONS,
        )
        self.assertEqual(promote["status"], "DENY")
        verification = self.runtime.handler().handle_bytes(
            encode_message(
                {
                    "protocol_version": PROTOCOL_VERSION,
                    "message_type": "WORKER_REQUEST",
                    "request_id": "req-analyst-verify",
                    "operation": "RECORD_INDEPENDENT_VERIFICATION",
                    "payload": {},
                }
            ),
            allowed_operations=FIRST_AGENT_OPERATIONS,
        )
        self.assertEqual(verification["result"]["reason"], "verification_firewall_denied")
        policy = self.runtime.handler().handle_bytes(
            encode_message(
                {
                    "protocol_version": PROTOCOL_VERSION,
                    "message_type": "WORKER_REQUEST",
                    "request_id": "req-analyst-policy",
                    "operation": "MODIFY_POLICY",
                    "payload": {},
                }
            ),
            allowed_operations=FIRST_AGENT_OPERATIONS,
        )
        self.assertEqual(policy["result"]["reason"], "policy_modification_denied")
        candidates = [
            item
            for item in self.env.plane.projections.epistemic_objects()
            if isinstance(item, KnowledgeCandidate)
        ]
        self.assertEqual(candidates, [])
        self.assertTrue(
            all(getattr(item, "lifecycle_state", None) is not KnowledgeState.PROMOTED for item in self.env.plane.projections.epistemic_objects())
        )

    def test_gated_operations_denied_for_first_agent(self) -> None:
        for operation in sorted(GATED_OPERATIONS):
            payload = {"relative_path": "ok.txt"} if operation == "READ_SUPPLIED_ARTIFACT" else {}
            if operation == "CREATE_CANDIDATE":
                payload = {"proposition": "no", "claim_ids": ["claim.x"], "evidence_ids": ["evidence.x"]}
            result = self.runtime.handler().handle_bytes(
                encode_message(
                    {
                        "protocol_version": PROTOCOL_VERSION,
                        "message_type": "WORKER_REQUEST",
                        "request_id": "req-gated-01",
                        "operation": operation,
                        "payload": payload,
                    }
                ),
                allowed_operations=FIRST_AGENT_OPERATIONS,
            )
            self.assertEqual(result["error_code"], "FIRST_AGENT_OPERATION_DENIED")

    def test_worker_mutation_cannot_alter_host_state(self) -> None:
        self.runtime.run_research_task(_task())
        after_task = len(self.env.plane.projections.epistemic_objects())
        mutated = self.runtime.run_probe("RT-WORKER-09")["result"]
        self.assertFalse(mutated["host_object_mutated"])
        self.assertEqual(len(self.env.plane.projections.epistemic_objects()), after_task)
        self.assertGreater(after_task, self.before_artifacts)


class IsolatedResearchAnalystFailureTests(unittest.TestCase):
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
        self.before_artifacts = len(self.env.plane.projections.epistemic_objects())

    def _runtime(self, timeout: float = 2.0) -> IsolatedResearchRuntime:
        runtime = IsolatedResearchRuntime(
            self.host,
            request_timeout_seconds=timeout,
            start_timeout_seconds=15.0,
        )
        runtime.start()
        return runtime

    def test_crash_timeout_malformed_fail_closed(self) -> None:
        runtime = self._runtime()
        with self.assertRaises(WorkerBoundaryError) as ctx:
            runtime.run_probe("CRASH")
        self.assertEqual(ctx.exception.error_code, "WORKER_CRASH")
        self.assertEqual(runtime.lifecycle, WorkerLifecycle.FAILED)
        self.assertEqual(len(self.env.plane.projections.epistemic_objects()), self.before_artifacts)

        runtime = self._runtime(timeout=0.4)
        with self.assertRaises(WorkerBoundaryError) as ctx:
            runtime.run_probe("TIMEOUT", timeout=0.4)
        self.assertEqual(ctx.exception.error_code, "WORKER_TIMEOUT")
        self.assertEqual(runtime.lifecycle, WorkerLifecycle.FAILED)

        runtime = self._runtime()
        with self.assertRaises(WorkerBoundaryError) as ctx:
            runtime.run_probe("MALFORMED_RESPONSE")
        self.assertEqual(ctx.exception.error_code, "MALFORMED_JSON")
        self.assertEqual(runtime.lifecycle, WorkerLifecycle.FAILED)
        self.assertEqual(len(self.env.plane.projections.epistemic_objects()), self.before_artifacts)


class Mission56HardeningTests(unittest.TestCase):
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
        self.handler = IsolatedIpcHandler(
            self.host.facade(),
            operation_policy=FIRST_AGENT_OPERATIONS,
            policy_locked=True,
        )
        self.before_artifacts = len(self.env.plane.projections.epistemic_objects())

    def _valid_pair(self):
        task = validate_research_task(_task())
        output = interpret_research_task(task, {"context_id": CONTEXT_ID})
        return task, output

    def test_worker_request_before_output_validation_is_inert(self) -> None:
        task, output = self._valid_pair()
        collected = [
            {
                "operation": "CREATE_CLAIM",
                "payload": {"statement": "forged", "evidence_ids": ["evidence.x"]},
            }
        ]
        result = finish_research_task(
            self.handler,
            task=task,
            expected_context_id=CONTEXT_ID,
            raw_output=output,
            collected_requests=collected,
        )
        self.assertEqual(result["status"], "REJECTED")
        self.assertEqual(result["commit"], "NO_COMMIT")
        self.assertEqual(result["tcb_write"], "NO_TCB_WRITE")
        self.assertEqual(result["error_code"], "WRITE_BEFORE_OUTPUT_VALIDATION")
        self.assertEqual(len(self.env.plane.projections.epistemic_objects()), self.before_artifacts)

    def test_invalid_output_after_collected_request_writes_nothing(self) -> None:
        task, output = self._valid_pair()
        output = dict(output)
        output["epistemic_class"] = "VERIFIED"
        result = finish_research_task(
            self.handler,
            task=task,
            expected_context_id=CONTEXT_ID,
            raw_output=output,
            collected_requests=[{"operation": "READ_CONTEXT", "payload": {}}],
        )
        self.assertEqual(result["commit"], "NO_COMMIT")
        self.assertEqual(len(self.env.plane.projections.epistemic_objects()), self.before_artifacts)

    def test_forged_context_mission_and_agent_identity(self) -> None:
        task, output = self._valid_pair()
        forged_context = dict(output)
        forged_context["agent_context_id"] = "research-context.other"
        result = finish_research_task(
            self.handler,
            task=task,
            expected_context_id=CONTEXT_ID,
            raw_output=forged_context,
            collected_requests=[],
        )
        self.assertEqual(result["commit"], "NO_COMMIT")
        forged_mission = dict(output)
        forged_mission["mission_id"] = "mission.forged"
        result = finish_research_task(
            self.handler,
            task=task,
            expected_context_id=CONTEXT_ID,
            raw_output=forged_mission,
            collected_requests=[],
        )
        self.assertEqual(result["error_code"], "MALFORMED_PAYLOAD")
        forged_agent = dict(output)
        forged_agent["agent_id"] = "AGENT_ONE"
        result = finish_research_task(
            self.handler,
            task=task,
            expected_context_id=CONTEXT_ID,
            raw_output=forged_agent,
            collected_requests=[],
        )
        self.assertEqual(result["commit"], "NO_COMMIT")
        self.assertEqual(len(self.env.plane.projections.epistemic_objects()), self.before_artifacts)

    def test_preflight_failure_writes_nothing(self) -> None:
        task = validate_research_task(
            _task([_item("item.claim-1", "CLAIM", "unsupported claim")])
        )
        output = interpret_research_task(task, {"context_id": CONTEXT_ID})
        result = finish_research_task(
            self.handler,
            task=task,
            expected_context_id=CONTEXT_ID,
            raw_output=output,
            collected_requests=[],
        )
        self.assertEqual(result["status"], "REJECTED")
        self.assertEqual(result["commit"], "NO_COMMIT")
        self.assertEqual(result["error_code"], "PREFLIGHT_FAILED")
        self.assertEqual(len(self.env.plane.projections.epistemic_objects()), self.before_artifacts)

    def test_first_middle_final_write_failure_not_ok_committed(self) -> None:
        task, output = self._valid_pair()
        plan = build_commit_plan(output, task)
        self.env.failures.arm("state_mutation", after=0)
        first = finish_research_task(
            self.handler,
            task=task,
            expected_context_id=CONTEXT_ID,
            raw_output=output,
            collected_requests=[],
        )
        self.assertEqual(first["status"], "REJECTED")
        self.assertEqual(first["commit"], "NO_COMMIT")
        self.assertNotEqual(first["status"], "OK")
        self.assertEqual(len(self.env.plane.projections.epistemic_objects()), self.before_artifacts)

        self.env.failures.arm("state_mutation", after=max(len(plan) // 2, 1))
        middle = finish_research_task(
            self.handler,
            task=task,
            expected_context_id=CONTEXT_ID,
            raw_output=output,
            collected_requests=[],
        )
        self.assertNotEqual(middle["status"], "OK")
        self.assertNotEqual(middle["commit"], "COMMITTED")
        self.assertEqual(middle["status"], "PARTIAL_COMMIT_FAILURE")
        self.assertEqual(middle["commit"], "PARTIAL_COMMIT_FAILURE")

        self.env.failures.arm("state_mutation", after=len(plan) - 1)
        final = finish_research_task(
            self.handler,
            task=task,
            expected_context_id=CONTEXT_ID,
            raw_output=output,
            collected_requests=[],
        )
        self.assertNotEqual(final["status"], "OK")
        self.assertNotEqual(final["commit"], "COMMITTED")
        self.assertEqual(final["status"], "PARTIAL_COMMIT_FAILURE")

    def test_create_candidate_denied_on_every_first_agent_ingress(self) -> None:
        payload = {
            "proposition": "no",
            "claim_ids": ["claim.x"],
            "evidence_ids": ["evidence.x"],
        }
        raw = encode_message(
            {
                "protocol_version": PROTOCOL_VERSION,
                "message_type": "WORKER_REQUEST",
                "request_id": "req-candidate-01",
                "operation": "CREATE_CANDIDATE",
                "payload": payload,
            }
        )
        runtime = IsolatedResearchRuntime(self.host, request_timeout_seconds=5.0, start_timeout_seconds=15.0)
        injected = runtime.handle_injected_bytes(raw)
        self.assertEqual(injected["error_code"], "FIRST_AGENT_OPERATION_DENIED")
        widened = runtime.handler().handle_bytes(raw, allowed_operations=ALLOWED_OPERATIONS)
        self.assertEqual(widened["error_code"], "FIRST_AGENT_OPERATION_DENIED")
        runtime.start()
        try:
            probe = runtime.run_probe("CREATE_CANDIDATE_PROBE")["result"]["response"]
            self.assertEqual(probe["error_code"], "FIRST_AGENT_OPERATION_DENIED")
        finally:
            runtime.stop()

    def test_operation_exactness_and_duplicate_json_keys(self) -> None:
        runtime = IsolatedResearchRuntime(self.host)
        for operation in (" CREATE_CANDIDATE", "create_candidate", "CREATE_CANDİDATE"):
            raw = (
                b'{"protocol_version":1,"message_type":"WORKER_REQUEST",'
                b'"request_id":"req-exact-01","operation":'
                + json_bytes(operation)
                + b',"payload":{}}'
            )
            result = runtime.handle_injected_bytes(raw)
            self.assertIn(
                result["error_code"],
                {"MALFORMED_PAYLOAD", "UNKNOWN_OPERATION", "FIRST_AGENT_OPERATION_DENIED"},
            )
            self.assertNotEqual(result["status"], "OK")
        nested = encode_message(
            {
                "protocol_version": PROTOCOL_VERSION,
                "message_type": "WORKER_REQUEST",
                "request_id": "req-nested-01",
                "operation": "CREATE_CLAIM",
                "payload": {
                    "statement": "x",
                    "evidence_ids": ["evidence.x"],
                    "operation": "CREATE_CANDIDATE",
                },
            }
        )
        nested_result = runtime.handle_injected_bytes(nested)
        self.assertEqual(nested_result["status"], "REJECT")
        duplicate = (
            b'{"protocol_version":1,"message_type":"WORKER_REQUEST","request_id":"req-dup-01",'
            b'"operation":"READ_CONTEXT","operation":"CREATE_CANDIDATE","payload":{}}'
        )
        dup = runtime.handle_injected_bytes(duplicate)
        self.assertEqual(dup["error_code"], "DUPLICATE_JSON_KEY")
        with self.assertRaises(ProtocolError) as ctx:
            decode_message(duplicate)
        self.assertEqual(ctx.exception.error_code, "DUPLICATE_JSON_KEY")

    def test_runtime_zero_writes_on_task_validation_failure(self) -> None:
        runtime = IsolatedResearchRuntime(
            self.host, request_timeout_seconds=5.0, start_timeout_seconds=15.0
        )
        runtime.start()
        try:
            rejected = runtime.run_research_task(_task(agent_context_id="research-context.other"))
            self.assertEqual(rejected["commit"], "NO_COMMIT")
            self.assertEqual(
                len(self.env.plane.projections.epistemic_objects()), self.before_artifacts
            )
        finally:
            runtime.stop()


def json_bytes(value: str) -> bytes:
    import json

    return json.dumps(value, ensure_ascii=False).encode("utf-8")


if __name__ == "__main__":
    import multiprocessing

    multiprocessing.freeze_support()
    unittest.main()

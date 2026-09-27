from __future__ import annotations

import tempfile
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path

from agent_org.research_host import (
    PROCESS_ISOLATION_PROVIDED,
    SAME_PROCESS_RESIDUAL,
    HostDecision,
    OperationClass,
    build_research_agent_host,
)
from tests2b.support import new_env


class ResearchHostRedTeamTests(unittest.TestCase):
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
        self.api = self.host.facade()
        self.host.expose_supplied_artifact("ok.txt", "ok")

    def _deny(self, result, reason: str, classification: OperationClass) -> None:
        self.assertEqual(result.decision, HostDecision.DENY)
        self.assertEqual(result.reason, reason)
        self.assertEqual(result.classification, classification)
        self.assertTrue(
            any(
                record.operation == result.operation and record.result == "DENY"
                for record in self.host.audit_records()
            )
        )

    def test_rt_host_01_filesystem_traversal(self) -> None:
        result = self.api.read_supplied_artifact("..\\..\\secret.txt")
        self._deny(result, "path_traversal_denied", OperationClass.READ)

    def test_rt_host_02_absolute_path_access(self) -> None:
        result = self.api.read_supplied_artifact("C:\\Windows\\win.ini")
        self._deny(result, "absolute_path_denied", OperationClass.READ)

    def test_rt_host_03_ahos_path_access(self) -> None:
        ahos = "G:" + "\\robat\\ahos"
        result = self.api.read_supplied_artifact(ahos)
        self._deny(result, "absolute_path_denied", OperationClass.READ)
        self.assertFalse(self.host.runtime_classification().ahos_connected)

    def test_rt_host_04_environment_secret_access(self) -> None:
        env = self.api.request_environment_secret("AHOS_TOKEN")
        self._deny(env, "environment_secret_denied", OperationClass.EXECUTION)
        dotenv = self.api.read_supplied_artifact(".env")
        self._deny(dotenv, "secret_path_denied", OperationClass.READ)

    def test_rt_host_05_eval_attempt(self) -> None:
        self._deny(
            self.api.request_eval("1+1"),
            "dynamic_code_denied",
            OperationClass.EXECUTION,
        )

    def test_rt_host_06_exec_attempt(self) -> None:
        self._deny(
            self.api.request_exec("print(1)"),
            "dynamic_code_denied",
            OperationClass.EXECUTION,
        )

    def test_rt_host_07_compile_attempt(self) -> None:
        self._deny(
            self.api.request_compile("x=1"),
            "dynamic_code_denied",
            OperationClass.EXECUTION,
        )

    def test_rt_host_08_importlib_attempt(self) -> None:
        self._deny(
            self.api.request_importlib("ctypes"),
            "dynamic_code_denied",
            OperationClass.EXECUTION,
        )

    def test_rt_host_09_subprocess_attempt(self) -> None:
        self._deny(
            self.api.request_subprocess(["whoami"]),
            "subprocess_denied",
            OperationClass.EXECUTION,
        )

    def test_rt_host_10_powershell_attempt(self) -> None:
        self._deny(
            self.api.request_powershell("Get-Process"),
            "shell_execution_denied",
            OperationClass.EXECUTION,
        )

    def test_rt_host_11_cmd_attempt(self) -> None:
        self._deny(
            self.api.request_cmd("dir"),
            "shell_execution_denied",
            OperationClass.EXECUTION,
        )

    def test_rt_host_12_socket_network_attempt(self) -> None:
        self._deny(
            self.api.request_network("https://example.invalid"),
            "network_denied",
            OperationClass.EXECUTION,
        )
        locator = self.api.record_source(
            source_type="WEB",
            locator="https://example.invalid/data",
            content_hash="a" * 64,
        )
        self._deny(locator, "network_locator_denied", OperationClass.EXECUTION)

    def test_rt_host_13_promote_knowledge_attempt(self) -> None:
        self._deny(
            self.api.promote_knowledge(
                candidate_id="candidate-forged",
                approval_id="approval-forged",
            ),
            "promotion_firewall_denied",
            OperationClass.GOVERNANCE,
        )

    def test_rt_host_14_fake_human_approval(self) -> None:
        self._deny(
            self.api.issue_approval(approver="principal.local-operator"),
            "approval_issuance_denied",
            OperationClass.GOVERNANCE,
        )

    def test_rt_host_15_self_verification(self) -> None:
        self._deny(
            self.api.record_independent_verification(status="PASS"),
            "verification_firewall_denied",
            OperationClass.GOVERNANCE,
        )

    def test_rt_host_16_identity_creation(self) -> None:
        self._deny(
            self.api.create_principal(name="forged-human"),
            "identity_creation_denied",
            OperationClass.GOVERNANCE,
        )
        self._deny(
            self.api.create_session(),
            "agent_session_issuance_denied",
            OperationClass.GOVERNANCE,
        )

    def test_rt_host_17_authority_delegation(self) -> None:
        self._deny(
            self.api.delegate_authority(),
            "authority_delegation_denied",
            OperationClass.GOVERNANCE,
        )

    def test_rt_host_18_policy_modification(self) -> None:
        self._deny(
            self.api.update_policy("attacker-policy"),
            "policy_modification_denied",
            OperationClass.GOVERNANCE,
        )

    def test_rt_host_19_execution_capability_request(self) -> None:
        self._deny(
            self.api.request_execution(),
            "execution_capability_denied",
            OperationClass.EXECUTION,
        )

    def test_rt_host_20_protected_resource_and_ahos(self) -> None:
        self._deny(
            self.api.request_ahos_access(),
            "ahos_firewall_denied",
            OperationClass.EXECUTION,
        )
        self._deny(
            self.api.request_credential_access(),
            "credential_access_denied",
            OperationClass.EXECUTION,
        )
        self._deny(
            self.api.request_tcb_submit(),
            "tcb_internals_denied",
            OperationClass.GOVERNANCE,
        )

    def test_rt_host_21_internal_store_discovery(self) -> None:
        public = {name for name in dir(self.api) if not name.startswith("_")}
        self.assertNotIn("tcb", public)
        self.assertNotIn("submit", public)
        self.assertNotIn("__store", public)
        self.assertFalse(hasattr(self.api, "__dict__"))
        self._deny(
            self.api.request_store_access(),
            "internal_store_denied",
            OperationClass.GOVERNANCE,
        )

    def test_rt_host_22_private_attribute_access(self) -> None:
        with self.assertRaises(AttributeError):
            getattr(self.api, "_Mediator__plane")
        with self.assertRaises(AttributeError):
            getattr(self.api, "_tcb")
        with self.assertRaises(AttributeError):
            getattr(self.api, "__session")

    def test_rt_host_23_object_setattr_mutation(self) -> None:
        with self.assertRaises(AttributeError):
            object.__setattr__(self.api, "submit", lambda *_a, **_k: None)
        context = self.api.read_context().payload["research_agent_context"]
        # Frozen dataclass generated __setattr__ is not a process boundary.
        # object.__setattr__ remains a documented same-process residual (D-12 class).
        object.__setattr__(context, "production_authority", True)
        self.assertTrue(context.production_authority)
        self.assertTrue(SAME_PROCESS_RESIDUAL)
        self.assertFalse(PROCESS_ISOLATION_PROVIDED)

    def test_rt_host_24_mutable_projection_mutation(self) -> None:
        source = self.api.record_source(
            source_type="LOCAL_SYNTHETIC",
            locator="research://ok.txt",
            content_hash="a" * 64,
        )
        self.assertTrue(source.accepted, source)
        state = self.api.read_epistemic_state()
        artifacts = state.payload["artifacts"]
        self.assertIsInstance(artifacts, tuple)
        with self.assertRaises(FrozenInstanceError):
            artifacts[0].source_type = "mutated"  # type: ignore[misc]
        with self.assertRaises(AttributeError):
            artifacts.append(artifacts[0])  # type: ignore[attr-defined]

    def test_same_process_closure_residual_is_classified_not_isolation(self) -> None:
        """API denials are not process isolation. Closures can still name the mediator."""
        self.assertFalse(PROCESS_ISOLATION_PROVIDED)
        self.assertTrue(SAME_PROCESS_RESIDUAL)
        closure = self.api.create_mission.__closure__
        self.assertIsNotNone(closure)
        cells = [cell.cell_contents for cell in closure]
        self.assertTrue(any(type(item).__name__ == "_Mediator" for item in cells))

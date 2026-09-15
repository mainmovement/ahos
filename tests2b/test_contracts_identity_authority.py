from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError, fields, replace
from datetime import timedelta

from agent_org.authority import CapabilityGrant, derive_authority, validate_delegation
from agent_org.commands import CreateTaskPayload
from agent_org.contracts import (
    Capability,
    CommandType,
    GovernedTask,
    Operation,
    POLICY_VERSION,
    Resource,
    TaskState,
)
from agent_org.identity import AgentIdentity, Session
from tests2b.support import (
    create_task,
    delegate_for_command,
    make_command,
    new_env,
    register_agent,
)


class ContractIdentityAuthorityTests(unittest.TestCase):
    def test_identity_contract_has_no_caller_trust_flags(self) -> None:
        names = {item.name for item in fields(AgentIdentity)}
        self.assertFalse(
            names & {"trusted", "verified", "operational", "human_approved"}
        )

    def test_contracts_are_immutable(self) -> None:
        env = new_env()
        agent = register_agent(env)
        with self.assertRaises(FrozenInstanceError):
            agent.status = "REVOKED"  # type: ignore[misc]

    def test_local_operator_session_is_bounded_and_nonproduction(self) -> None:
        env = new_env()
        self.assertEqual(
            env.session.auth_method, "NON_PRODUCTION_LOCAL_OPERATOR_AUTH"
        )
        with self.assertRaises(ValueError):
            env.plane.local_operator_auth.create_session(timedelta(hours=1))

    def test_expired_session_denied(self) -> None:
        env = new_env()
        task = GovernedTask(
            task_id=env.ids.new("task"),
            owner_principal_id=env.plane.operator.principal_id,
            state=TaskState.PROPOSED,
            capability_scope=(Capability.TASK_MANAGE,),
            resource_scope=(Resource.TASK_STORE,),
            created_at=env.clock.now(),
            updated_at=env.clock.now(),
        )
        command = make_command(
            env,
            CommandType.CREATE_TASK,
            lambda _cid: CreateTaskPayload(task),
        )
        env.clock.advance(1201)
        result = env.plane.tcb.submit(command, env.session)
        self.assertFalse(result.accepted)
        self.assertEqual(result.reason, "session_expired")

    def test_revoked_session_denied(self) -> None:
        env = new_env()
        task = GovernedTask(
            task_id=env.ids.new("task"),
            owner_principal_id=env.plane.operator.principal_id,
            state=TaskState.PROPOSED,
            capability_scope=(Capability.TASK_MANAGE,),
            resource_scope=(Resource.TASK_STORE,),
            created_at=env.clock.now(),
            updated_at=env.clock.now(),
        )
        command = make_command(
            env, CommandType.CREATE_TASK, lambda _cid: CreateTaskPayload(task)
        )
        revoked = env.plane.local_operator_auth.revoke(env.session.session_id)
        result = env.plane.tcb.submit(command, revoked)
        self.assertEqual(result.reason, "session_revoked")

    def test_forged_session_denied(self) -> None:
        env = new_env()
        forged = replace(
            env.session,
            principal_id="principal.someone-else",
        )
        task = GovernedTask(
            task_id=env.ids.new("task"),
            owner_principal_id=env.plane.operator.principal_id,
            state=TaskState.PROPOSED,
            capability_scope=(Capability.TASK_MANAGE,),
            resource_scope=(Resource.TASK_STORE,),
            created_at=env.clock.now(),
            updated_at=env.clock.now(),
        )
        command = make_command(
            env, CommandType.CREATE_TASK, lambda _cid: CreateTaskPayload(task)
        )
        result = env.plane.tcb.submit(command, forged)
        self.assertEqual(result.reason, "forged_or_unknown_session")

    def test_authority_context_from_caller_is_rejected_by_schema(self) -> None:
        env = new_env()
        task = create_task(env)
        with self.assertRaises(ValueError):
            replace(
                make_command(
                    env,
                    CommandType.CREATE_TASK,
                    lambda _cid: CreateTaskPayload(task),
                ),
                authority_context_ref="caller-says-trusted",
            )

    def test_exact_authority_dimensions_enforced(self) -> None:
        env = new_env()
        task = create_task(env)
        child = delegate_for_command(env, task.task_id, CommandType.TRANSITION_TASK)
        grants = {
            grant.grant_id: grant
            for grant in env.plane.projections.capability_status(
                env.plane.operator.principal_id
            ).grants
        }
        base = dict(
            grants=grants,
            principal_id=env.plane.operator.principal_id,
            task_id=task.task_id,
            capability_id=child.capability_id,
            operation=child.operation,
            resource_id=child.resource_id,
            policy_version=POLICY_VERSION,
            now=env.clock.now(),
        )
        self.assertTrue(derive_authority(**base).allowed)
        variants = (
            {"principal_id": "principal.wrong"},
            {"task_id": "task.wrong"},
            {"capability_id": Capability.EPISTEMIC_WRITE},
            {"operation": Operation.CREATE},
            {"resource_id": Resource.EPISTEMIC_STORE},
        )
        for change in variants:
            args = {**base, **change}
            self.assertFalse(derive_authority(**args).allowed, change)

    def test_expired_and_revoked_grants_denied(self) -> None:
        env = new_env()
        task = create_task(env)
        child = delegate_for_command(
            env,
            task.task_id,
            CommandType.TRANSITION_TASK,
            expires_in=timedelta(seconds=2),
        )
        grants = {
            grant.grant_id: grant
            for grant in env.plane.projections.capability_status(
                env.plane.operator.principal_id
            ).grants
        }
        env.clock.advance(3)
        result = derive_authority(
            grants,
            principal_id=child.principal_id,
            task_id=child.task_id,
            capability_id=child.capability_id,
            operation=child.operation,
            resource_id=child.resource_id,
            policy_version=POLICY_VERSION,
            now=env.clock.now(),
        )
        self.assertFalse(result.allowed)
        self.assertEqual(result.reason, "grant_expired")
        active = replace(
            child,
            expires_at=env.clock.now() + timedelta(minutes=10),
            revoked_at=env.clock.now(),
        )
        grants[active.grant_id] = active
        self.assertEqual(
            derive_authority(
                grants,
                principal_id=active.principal_id,
                task_id=active.task_id,
                capability_id=active.capability_id,
                operation=active.operation,
                resource_id=active.resource_id,
                policy_version=POLICY_VERSION,
                now=env.clock.now(),
            ).reason,
            "grant_revoked",
        )

    def test_child_authority_cannot_exceed_parent_or_depth(self) -> None:
        env = new_env()
        task = create_task(env)
        child = delegate_for_command(env, task.task_id, CommandType.TRANSITION_TASK)
        status = env.plane.projections.capability_status(
            env.plane.operator.principal_id
        )
        grants = status.grants
        self.assertTrue(
            any(item.child_grant_id == child.grant_id for item in status.delegations)
        )
        parent = next(item for item in grants if item.grant_id == child.parent_grant_id)
        excessive = replace(child, capability_id=Capability.EPISTEMIC_WRITE)
        self.assertEqual(
            validate_delegation(parent, excessive, now=env.clock.now()),
            "child_authority_exceeds_parent",
        )
        too_deep = replace(child, delegation_depth=4)
        self.assertIn(
            validate_delegation(parent, too_deep, now=env.clock.now()),
            {"broken_delegation_depth", "delegation_depth_exceeded"},
        )

    def test_broken_authority_chain_denied(self) -> None:
        env = new_env()
        task = create_task(env)
        child = delegate_for_command(env, task.task_id, CommandType.TRANSITION_TASK)
        grants = {
            item.grant_id: item
            for item in env.plane.projections.capability_status(
                env.plane.operator.principal_id
            ).grants
            if item.grant_id != child.parent_grant_id
        }
        result = derive_authority(
            grants,
            principal_id=child.principal_id,
            task_id=child.task_id,
            capability_id=child.capability_id,
            operation=child.operation,
            resource_id=child.resource_id,
            policy_version=POLICY_VERSION,
            now=env.clock.now(),
        )
        self.assertFalse(result.allowed)
        self.assertEqual(result.reason, "broken_authority_chain")

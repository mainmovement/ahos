"""Provider status -> mission ledger integration (GM-09).

``guard_provider_call`` runs one AI provider call for a mission and records the
outcome in the GM-08 ledger, without ever crashing on a provider outage:

  READY                          -> AI_PROVIDER updated, mission keeps running
  QUOTA_EXHAUSTED / AUTH_FAILED  -> mission PAUSED with a checkpoint, plus a Persian
                                    owner message asking for a new key through
                                    the credential-store abstraction
  UNAVAILABLE / DEGRADED / MODEL_UNAVAILABLE / BLOCKED
                                 -> mission WAIT_FOR_AI with a checkpoint (resume later)

The key is never passed to, logged by, or stored in this module or the ledger.
Advisory/engineering only: nothing here decides or gates trading.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from architecture.ai.credential_store import CredentialRef, CredentialStore, NullCredentialStore
from architecture.ai.provider_status import AIProviderStatus, ProviderAssessment, safe_provider_call
from architecture.mission.ledger import MissionLedger, TaskStatus


@dataclass(frozen=True)
class GuardOutcome:
    result: Any | None
    assessment: ProviderAssessment
    mission_status: str
    owner_message_fa: str | None = None


def guard_provider_call(ledger: MissionLedger, mission_id: str, provider: str,
                        call: Callable[[], Any], *, checkpoint: Any = None,
                        credential_store: CredentialStore | None = None) -> GuardOutcome:
    store = credential_store or NullCredentialStore()
    result, a = safe_provider_call(provider, call)
    ai_field = {"name": provider, "status": a.status.value, "reason": a.reason_code}
    cur = ledger.latest(mission_id)
    if cur is None:
        raise LookupError(f"mission {mission_id} not in ledger; start() it first")
    ckpt = checkpoint if checkpoint is not None else cur.get("CHECKPOINT")

    if a.status == AIProviderStatus.READY:
        if cur["TASK_STATUS"] in ("RESUMED", "PENDING"):
            st = ledger.update(mission_id, status=TaskStatus.RUNNING, AI_PROVIDER=ai_field)
        else:
            st = ledger.update(mission_id, AI_PROVIDER=ai_field)
        return GuardOutcome(result, a, st["TASK_STATUS"])

    if a.needs_credential_action:
        reason = "NO_KEY" if a.reason_code == "NO_KEY" else a.status.value
        req = store.request_new_credential(CredentialRef(provider), reason, mission_id)
        st = ledger.pause(mission_id, status=TaskStatus.PAUSED, checkpoint=ckpt, AI_PROVIDER=ai_field,
                          CURRENT_BLOCKER=f"AI provider {provider}: {a.status.value} ({a.reason_code})",
                          NEXT_ACTION=f"OWNER_ACTION: store a new key under {req.target}, then resume()")
        return GuardOutcome(None, a, st["TASK_STATUS"], req.message_fa)

    st = ledger.pause(mission_id, status=TaskStatus.WAIT_FOR_AI, checkpoint=ckpt, AI_PROVIDER=ai_field,
                      CURRENT_BLOCKER=f"AI provider {provider}: {a.status.value} ({a.reason_code})",
                      NEXT_ACTION="retry later or switch provider, then resume()")
    return GuardOutcome(None, a, st["TASK_STATUS"])

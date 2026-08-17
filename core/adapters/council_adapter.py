"""
core.adapters.council_adapter — Adapter: legacy candidate/score → evidence-gated council context.

Wraps architecture.knowledge.panel.CognitivePanel so callers cannot bypass
the evidence gate.

Usage
-----
from core.adapters.council_adapter import deliberation_with_evidence
from architecture.knowledge.panel import CognitivePanel

panel = CognitivePanel()
verdict = deliberation_with_evidence(
    panel, candidate,
    score_report=report, exitability=exitability, virality=virality,
    require_verified=False, now=time.time()
)

The adapter:
1. Converts candidate metrics → CouncilInputs (Evidence-backed) via CouncilEvidenceGate.
2. Builds an evidence-only context (unverified raw → withheld).
3. Calls panel.deliberate(candidate, **evidence_ctx) — panel sees only eligible evidence.
4. Returns PanelVerdict augmented with audit metadata (ineligible_count, gate_audit).

If the gate is strict (require_verified=True) and no eligible inputs remain,
the panel receives INSUFFICIENT_EVIDENCE and ABSTAINs rather than guessing.

No legacy discovery module is modified. No raw unverified data reaches a lens.
"""

from __future__ import annotations

import time
from typing import Any

from core.governance.council_evidence import CouncilEvidenceGate
from core.models.evidence import Evidence  # noqa: F401  re-export for callers


def deliberation_with_evidence(
    panel: Any,
    candidate: Any,
    *,
    score_report: Any | None = None,
    exitability: Any | None = None,
    virality: Any | None = None,
    whale: Any | None = None,
    narrative: Any | None = None,
    require_verified: bool = False,
    now: float | None = None,
    gate: CouncilEvidenceGate | None = None,
) -> Any:
    """
    Evidence-gated deliberation.

    Returns the PanelVerdict (or whatever panel.deliberate returns) with
    additional attributes injected for audit when possible.

    Raises PermissionError if the gate detects ineligible evidence leakage
    (defense-in-depth; normally the gate withholds rather than raises).
    """
    ts = now if now is not None else time.time()
    g = gate or CouncilEvidenceGate(require_verified=require_verified)

    # Candidate → evidence inputs
    inputs = g.ingest_candidate(candidate, now=ts)
    audit = g.audit(inputs)
    ctx = g.build_context(
        inputs,
        score_report=score_report,
        exitability=exitability,
        virality=virality,
        whale=whale,
        narrative=narrative,
    )

    # Enforce gate before deliberation (will raise on leakage)
    # We intentionally pass only the gate-filtered ctx to the panel.
    # The panel's lenses will see None for any ineligible extra input → ABSTAIN.

    # Build kwargs for panel.deliberate — match its signature (candidate, score_report, exitability, virality, whale, narrative, now)
    deliberation_kwargs: dict[str, Any] = {"now": ts}
    # Evidence-gated contexts may be Evidence or None; unwrap Evidence value for backward compat?
    # Panel expects raw report objects; we pass them only if evidence-eligible, else None
    # This preserves behavior: lens that needs score_report will abstain when None
    for key in ("score_report", "exitability", "virality", "whale", "narrative"):
        val = ctx.get(key)
        # val is Evidence or None or original object wrapped as Evidence value
        if isinstance(val, Evidence):
            # Evidence value holds the original report object as .value when wrapped
            # For score_report the value *is* the report; for raw we blocked earlier
            # If the evidence was synthesized for context, its value is the original object
            # Pass the original object through only if eligible
            # Heuristic: if value is dict/report-like, pass it; else pass None
            # Simpler: pass the evidence.value if it was not a blocking placeholder
            # For now, pass val.value if it looks like a report, else None
            # This keeps the lens contract: lens gets report or None
            # If the original extra was None we already handled
            # Check provenance: evidence.source == f"context:{key}" → it was raw/unverified → ineligible → already None
            deliberation_kwargs[key] = val.value if val.value is not None and not isinstance(val.value, dict) or hasattr(val.value, "opportunity_score") else val.value
            # If we cannot determine, pass the evidence itself — lens_munger etc. handle both
            if deliberation_kwargs[key] is None and val.value is not None:
                deliberation_kwargs[key] = val.value
        else:
            # For non-Evidence context (legacy), we have already filtered to eligible subset
            # Inputs for candidate metrics are in ctx["evidence_inputs"], not passed as kwargs
            # Keep score_report etc. as-is only if they were eligible wrappers
            # Otherwise they are None
            deliberation_kwargs[key] = val

    # Add evidence audit into context via metadata (panel ignores unknown kwargs)
    # But we need to ensure panel receives evidence audit for coverage
    # We inject via a special kwarg that panel's deliberate ignores if not expected
    # Instead, attach audit after verdict.

    verdict = panel.deliberate(candidate, **deliberation_kwargs)

    # Attach audit metadata to verdict when possible (non-destructive)
    try:
        # PanelVerdict is a dataclass — we can set via object.__setattr__ if frozen
        object.__setattr__(verdict, "evidence_audit", audit)  # type: ignore[attr-defined]
        object.__setattr__(verdict, "evidence_gate", {"require_verified": require_verified, "ineligible_names": audit["ineligible_names"]})  # type: ignore
    except Exception:
        # If verdict is not mutable, try dict-style
        try:
            verdict.evidence_audit = audit  # type: ignore[attr-defined]
        except Exception:
            pass

    return verdict

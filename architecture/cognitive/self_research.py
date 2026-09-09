"""Machine-readable self-research reports from caller-provided snapshots.

The builder NEVER opens the Windows soak SQLite, starts a daemon, or
treats Cloud-agent ``data/*.sqlite`` as soak authority. Every numeric
field is copied from the snapshot or marked unknown.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class SelfResearchReport:
    """One self-research cycle. Weakness discovery is a success condition."""

    generated_at_utc: str
    data_label: str
    soak_snapshot_is_authoritative: bool
    what_i_know: tuple[str, ...]
    what_i_dont_know: tuple[str, ...]
    where_i_fail: tuple[str, ...]
    why_i_fail: tuple[str, ...]
    uncertain_about: tuple[str, ...]
    missing_capabilities: tuple[str, ...]
    test_next: tuple[str, ...]
    snapshot_fields: Mapping[str, Any] = field(default_factory=dict)
    open_gaps: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["what_i_know"] = list(self.what_i_know)
        d["what_i_dont_know"] = list(self.what_i_dont_know)
        d["where_i_fail"] = list(self.where_i_fail)
        d["why_i_fail"] = list(self.why_i_fail)
        d["uncertain_about"] = list(self.uncertain_about)
        d["missing_capabilities"] = list(self.missing_capabilities)
        d["test_next"] = list(self.test_next)
        d["open_gaps"] = list(self.open_gaps)
        d["snapshot_fields"] = dict(self.snapshot_fields)
        return d


def build_self_research_report(
    *,
    snapshot: Mapping[str, Any],
    data_label: str,
    soak_snapshot_is_authoritative: bool,
    extra_unknowns: Sequence[str] = (),
    extra_gaps: Sequence[str] = (),
) -> SelfResearchReport:
    """Derive a report from an operator- or test-supplied snapshot.

    ``data_label`` must be one of REAL / SYNTHETIC / SIMULATION / TEST /
    UNKNOWN so reports cannot be mistaken for soak evidence.
    """
    label = str(data_label).strip().upper()
    if label not in {"REAL", "SYNTHETIC", "SIMULATION", "TEST", "UNKNOWN"}:
        raise ValueError(f"data_label must be typed; got {data_label!r}")

    know: list[str] = []
    dont: list[str] = []
    fail: list[str] = []
    why: list[str] = []
    uncertain: list[str] = []
    missing: list[str] = []
    next_tests: list[str] = []

    if soak_snapshot_is_authoritative:
        know.append(
            "Caller marked this snapshot as soak-authoritative; "
            "this process did not recompute soak T0."
        )
    else:
        dont.append(
            "This process is not the Windows soak authority; "
            "do not treat local sqlite counts as T0."
        )

    obs = snapshot.get("OBSERVING")
    res = snapshot.get("RESOLVED")
    labels = snapshot.get("outcome_labels")
    pairs = snapshot.get("eligible_join_pairs_estimate")
    if obs is not None:
        know.append(f"Snapshot OBSERVING={obs} (copied, not recomputed).")
    if res is not None:
        know.append(f"Snapshot RESOLVED={res} (copied, not recomputed).")
    if labels is not None:
        know.append(f"Snapshot outcome_labels={labels} (copied, not recomputed).")
    if pairs is not None:
        know.append(f"Snapshot eligible_join_pairs_estimate={pairs} (copied).")
        if pairs == 0:
            fail.append("eligible_join_pairs_estimate is 0 in the snapshot.")
            why.append(
                "Join-pair eligibility is gated on resolved outcomes with "
                "matching predictions; zero pairs means calibration cannot "
                "advance from this snapshot."
            )
            uncertain.append("Whether later soak hours will produce eligible joins.")
            next_tests.append("Wait for T+72h soak evidence before calibration retune.")

    if snapshot.get("live_trading_enabled"):
        fail.append("Snapshot claims live trading enabled — PAPER_ONLY doctrine violated.")
        why.append("PAPER_ONLY must remain enforced; this report flags the contradiction.")
    else:
        know.append("Snapshot does not claim live trading is enabled.")

    missing.extend(
        [
            "Unified working/episodic/semantic/procedural memory with provenance.",
            "Causal world model (observations are not a world model).",
            "Memory-bearing cognitive agents with independent tools.",
            "Validated counterfactual engine (must not overwrite observed outcomes).",
        ]
    )
    dont.extend(extra_unknowns)
    missing.extend(extra_gaps)
    next_tests.append("Do not close M-GAP-003 (≥7-day soak) because a 72h soak exists.")
    next_tests.append("Do not fabricate join pairs or outcome labels.")

    return SelfResearchReport(
        generated_at_utc=_utc_now(),
        data_label=label,
        soak_snapshot_is_authoritative=soak_snapshot_is_authoritative,
        what_i_know=tuple(know),
        what_i_dont_know=tuple(dont),
        where_i_fail=tuple(fail),
        why_i_fail=tuple(why),
        uncertain_about=tuple(uncertain),
        missing_capabilities=tuple(missing),
        test_next=tuple(next_tests),
        snapshot_fields=dict(snapshot),
        open_gaps=tuple(extra_gaps),
    )

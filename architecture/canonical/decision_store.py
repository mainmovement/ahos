"""Canonical decision store — local-first JSON ledger (One-Brain, Option B).

ONE writer (the Python canonical brain) · many read-only adapters. Chosen over
SQLite/PostgreSQL/Redis because it needs no server or new dependency, the web
already reads ``reports/*.json`` via fs, docker-compose already shares the
``./reports`` volume, and it works identically on Windows/Docker/local.

Layout (under ``reports/canonical/decisions/``):
  * ``latest.json``  — map {canonical_token_id -> CanonicalDecision dict}, the
    current authoritative snapshot; written ATOMICALLY (temp + os.replace) so a
    reader never observes a partial file.
  * ``ledger.jsonl`` — append-only audit trail of every written decision.

Fail-closed everywhere: a missing file, malformed JSON, invalid record, version
mismatch, or stale decision is NEVER a positive opportunity.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Iterable, Optional

from config.paths import get_reports_dir
from .contract import CanonicalDecision

#: Freshness budget for a canonical decision. A decision older than this is
#: treated as stale (fail-safe). Default 900s (15 min) comfortably exceeds the
#: daemon cycle cadence (~60-75s) while preventing indefinitely-stale emission.
DECISION_FRESHNESS_BUDGET_SEC = float(os.environ.get("AHOS_CANONICAL_FRESHNESS_SEC") or "900")


def _default_dir() -> Path:
    override = os.environ.get("AHOS_CANONICAL_DECISIONS_DIR")
    if override:
        return Path(override)
    return get_reports_dir() / "canonical" / "decisions"


class CanonicalDecisionStore:
    """Sole canonical writer + read-only adapter accessor."""

    def __init__(self, store_dir: str | os.PathLike | None = None,
                 freshness_budget_sec: float | None = None):
        self.dir = Path(store_dir) if store_dir is not None else _default_dir()
        self.budget = float(freshness_budget_sec) if freshness_budget_sec is not None \
            else DECISION_FRESHNESS_BUDGET_SEC

    @property
    def latest_path(self) -> Path:
        return self.dir / "latest.json"

    @property
    def ledger_path(self) -> Path:
        return self.dir / "ledger.jsonl"

    # ------------------------------------------------------------ writer --
    def write_decisions(self, decisions: Iterable[CanonicalDecision],
                        now: float | None = None) -> int:
        """Persist valid decisions. Invalid records are dropped (never written).

        Returns the count actually written. Atomic snapshot replace + append audit.
        """
        ts = time.time() if now is None else now
        valid = [d for d in decisions if isinstance(d, CanonicalDecision) and d.validate()]
        if not valid:
            return 0
        self.dir.mkdir(parents=True, exist_ok=True)

        # Append-only audit ledger first (immutable evidence).
        with self.ledger_path.open("a", encoding="utf-8") as fh:
            for d in valid:
                fh.write(json.dumps({**d.to_dict(), "written_at": ts}, ensure_ascii=False) + "\n")

        # Merge into the latest snapshot (latest decision per token wins).
        snapshot = self._load_latest_raw()
        for d in valid:
            snapshot[d.canonical_token_id] = d.to_dict()

        tmp = self.dir / f".latest.{os.getpid()}.{int(ts*1000)}.tmp"
        tmp.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, self.latest_path)  # atomic on POSIX + Windows
        return len(valid)

    # ------------------------------------------------------------ reader --
    def _load_latest_raw(self) -> dict:
        """Load the latest snapshot map; fail-closed to {} on any problem.

        One read-retry covers the brief window around an atomic replace.
        """
        for attempt in range(2):
            try:
                raw = self.latest_path.read_text(encoding="utf-8")
                data = json.loads(raw)
                return data if isinstance(data, dict) else {}
            except FileNotFoundError:
                return {}
            except (json.JSONDecodeError, OSError):
                if attempt == 0:
                    time.sleep(0.02)
                    continue
                return {}
        return {}

    def get(self, canonical_token_id: str, now: float | None = None) -> Optional[CanonicalDecision]:
        """Return a VALID, FRESH decision for the token, else None (fail-closed)."""
        if not canonical_token_id or not isinstance(canonical_token_id, str):
            return None
        raw = self._load_latest_raw().get(canonical_token_id)
        rec = CanonicalDecision.from_dict(raw)  # fail-closed on malformed/invalid
        if rec is None:
            return None
        ts = time.time() if now is None else now
        if rec.is_stale(ts, self.budget):
            return None
        return rec

    def is_positive_opportunity(self, canonical_token_id: str, now: float | None = None) -> bool:
        """THE canonical gate for any adapter: True only for a valid, fresh,
        eligible (⇒ security PASS) record. Everything else fails closed."""
        rec = self.get(canonical_token_id, now=now)
        return bool(rec and rec.opportunity_eligible)

    def list_eligible(self, now: float | None = None) -> list[CanonicalDecision]:
        """The single canonical source of "opportunities": valid, fresh, eligible
        records only. This is what every adapter's "best opportunities" must read.
        Fail-closed: excludes missing/malformed/stale/UNKNOWN/VETO. Sorted by score
        (evidence ordering only — the eligibility gate already happened)."""
        ts = time.time() if now is None else now
        out: list[CanonicalDecision] = []
        for tid in self._load_latest_raw().keys():
            rec = self.get(tid, now=ts)
            if rec is not None and rec.opportunity_eligible:
                out.append(rec)
        out.sort(key=lambda r: r.opportunity_score, reverse=True)
        return out

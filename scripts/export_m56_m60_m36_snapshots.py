#!/usr/bin/env python3
"""Export M56 Tournament, M60 Astra Engine, M32 Reconcile Bridge, M48 Dependency Audit, and M36 World Orchestration snapshots."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.health.dependency_lock_audit import audit_dependency_locks
from architecture.learning.astra_engine import run_astra_evolution_cycle
from architecture.learning.strategy_tournament import run_strategy_tournament
from architecture.markets.reconcile_bridge import reconcile_desk_states
from architecture.mission.world_orchestrator import run_autonomous_world_cycle


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    m56 = run_strategy_tournament()
    _write_json(ROOT / "reports" / "grok" / "M56" / "tournament_snapshot.json", m56)

    m60 = run_astra_evolution_cycle(root=ROOT)
    _write_json(ROOT / "reports" / "grok" / "M60" / "astra_snapshot.json", m60)

    m32 = reconcile_desk_states()
    _write_json(ROOT / "reports" / "grok" / "M32" / "cross_desk_reconcile.json", m32)

    m48 = audit_dependency_locks(repo_root=ROOT)
    _write_json(ROOT / "reports" / "grok" / "M48" / "dependency_audit.json", m48)

    m36 = run_autonomous_world_cycle(root=ROOT)
    _write_json(ROOT / "reports" / "grok" / "M36" / "world_orchestration_snapshot.json", m36)

    print(
        f"exported M56(leader={m56['leader_id']}), M60({m60['overall_status']}), "
        f"M32({m32['overall_verdict']}), M48({m48['verdict']}), M36({m36['world_state']})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""MEGA9 stays shadow. The registration hash must still match."""
from __future__ import annotations

from pathlib import Path

from science.block_bootstrap import survives
from science.conformal import abstain, interval
from science.cost_model import net_return
from science.integrate import run_all
from science.kelly_ceiling import ceiling
from science.prereg import hash_ok, trial_counts
from science.purged_cv import leaks, purged_folds
from science.pump_anomaly import pump_veto
from science.red_team import review
from science.triple_barrier import barrier_label


def test_registration_hash_matches_and_trials_are_one() -> None:
    root = Path(__file__).resolve().parents[1]
    assert hash_ok(root)
    counts = trial_counts(root)
    assert len(counts) == 12
    assert set(counts.values()) == {1}


def test_modules_do_not_promote(tmp_path: Path) -> None:
    yaml = Path(__file__).resolve().parents[1] / "docs" / "prereg" / "MEGA9.yaml"
    digest = Path(__file__).resolve().parents[1] / "docs" / "prereg" / "MEGA9.sha256"
    dest = tmp_path / "docs" / "prereg"
    dest.mkdir(parents=True)
    (dest / "MEGA9.yaml").write_bytes(yaml.read_bytes())
    (dest / "MEGA9.sha256").write_text(digest.read_text(encoding="utf-8"), encoding="utf-8")
    doc = run_all(tmp_path)
    assert doc["promoted"] == 0
    assert doc["applied_to_live"] is False
    assert doc["hash_ok"] is True
    assert [row["id"] for row in doc["rows"]] == [f"M9-{i:02d}" for i in range(1, 13)]
    assert all(row["promoted"] is False and row["applied_to_live"] is False for row in doc["rows"])
    assert all(row["ram_within_cap"] for row in doc["rows"])
    assert doc["rows"][11]["state"] == "OPEN"
    assert doc["rows"][11]["moirai"] == "REFUSED_CC_BY_NC"
    assert doc["red_team"]["red_team"] == "NOT_SURVIVED"
    assert review()["attacks_caught"] is True


def test_the_methods_hold_on_a_toy() -> None:
    assert barrier_label([100, 101, 106], 0, 0.05, 0.05, 3) == 1
    folds = purged_folds(20, horizon=2, n_splits=4, embargo=1)
    assert folds and all(not leaks(train, test, 2, 1) for train, test in folds)
    low, high = interval(0.0, [-0.02, 0.03])
    assert abstain(low, high, 0.0, 0.01) is True
    filled = net_return(0.01, fee_per_side=0.001, spread_pct=1.0, quantity=1, adv=1, impact_coef=0.1, funding_rate=0.001, hold_days=1, slices=2)
    assert filled["net"] < filled["gross"]
    assert ceiling(1.0, 1.0, stop_pct=0.2, drawdown_limit=0.02) <= 0.1
    assert survives([-0.02] * 10) is False
    veto = pump_veto(liquidity_locked=False, holder_growth=True, change=1.0)
    assert veto["veto"] is True and veto["live_open"] is False

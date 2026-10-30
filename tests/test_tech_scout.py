from datetime import datetime, timezone

from architecture.university.tech_scout import (
    ALLOWED_LICENSES,
    DROPPED,
    advance_shadows,
    decide,
    negahban_review,
    parse_github_search,
    parse_github_trending,
    parse_hf_model,
    rank,
    reopen_static_passes,
    run_week,
    shadow_queue,
    weight_bytes,
)
from architecture.markets.paper_trade_gates import MIN_AGREEING_FAMILIES, MIN_EXPECTED_PROFIT_TO_FEE_RATIO

NOW = datetime(2026, 10, 30, tzinfo=timezone.utc)
_PASS_RETURNS = [0.02, 0.018, 0.021, 0.019, 0.022, 0.017, 0.02, 0.019, 0.021, 0.018, 0.02, 0.019]
_PASS_TRIALS = [
    [0.03, 0.028, 0.031, 0.029, 0.03, 0.027, 0.032, 0.029],
    [0.02, 0.018, 0.021, 0.019, 0.02, 0.017, 0.022, 0.019],
]


def _repo(name, license_id, pushed="2026-10-01T00:00:00Z"):
    return {
        "full_name": name,
        "html_url": f"https://github.com/{name}",
        "license": {"spdx_id": license_id} if license_id else None,
        "pushed_at": pushed,
        "archived": False,
        "private": False,
    }


def test_license_size_and_staleness_archive_before_the_top_five():
    candidates = parse_github_search(
        {"items": [
            _repo("good/risk", "MIT"),
            _repo("bad/gpl", "GPL-3.0"),
            _repo("old/quant", "Apache-2.0", pushed="2020-01-01T00:00:00Z"),
        ]},
        domain="risk",
    )
    huge = parse_hf_model({
        "id": "org/huge",
        "cardData": {"license": "mit"},
        "lastModified": "2026-10-01T00:00:00Z",
        "safetensors": {"total": 2_000_000_000},
    })
    small = parse_hf_model({
        "id": "org/small",
        "cardData": {"license": "apache-2.0"},
        "lastModified": "2026-10-01T00:00:00Z",
        "safetensors": {"total": 1_000_000},
    })
    trending = parse_github_trending('<h2 class="h3"><a href="/someone/trending-repo"></a></h2>')
    top, archived = rank([*candidates, huge, small, *trending], NOW)
    reasons = {row["idea"]: row["reason"] for row in archived}
    assert reasons["bad/gpl"] == "LICENSE"
    assert reasons["old/quant"] == "STALE"
    assert reasons["org/huge"] == "TOO_LARGE_FOR_8GB"
    assert reasons["someone/trending-repo"] == "LICENSE"
    assert [row["idea"] for row in top] == ["good/risk", "org/small"]
    assert weight_bytes({"safetensors": {"total": 10}}) == 40
    assert "ssrn" in DROPPED and "papers_with_code" in DROPPED
    assert "mit" in ALLOWED_LICENSES and "gpl-3.0" not in ALLOWED_LICENSES


def test_a_passing_static_review_stays_a_shadow_candidate_until_we_score_it():
    candidate = parse_github_search({"items": [_repo("good/risk", "BSD-3-Clause")]}, domain="risk")[0]
    review = negahban_review(candidate)
    assert review["verdict"] == "PASS_STATIC"
    assert review["executed"] is False and review["sandboxed_run"] is False
    week = run_week([candidate], now=NOW)
    assert week[0]["decision"] == "SHADOW_CANDIDATE"
    assert week[0]["evidence"]["reason"] == "AWAITING_OWN_SCORE"
    assert week[0]["evidence"]["applied_to_live_weights"] is False
    assert week[0]["evidence"]["predicted_score"] is None
    short = decide(candidate, review, [0.01, 0.02], [[0.01], [0.02]], None)
    assert short["decision"] == "ARCHIVE" and short["evidence"]["reason"] == "INSUFFICIENT_REPLAY"


def test_promote_requires_the_stats_gate_and_the_red_team():
    candidate = parse_github_search({"items": [_repo("good/risk", "MIT")]}, domain="risk")[0]
    review = negahban_review(candidate)
    held = decide(candidate, review, _PASS_RETURNS, _PASS_TRIALS, None)
    assert held["decision"] == "ARCHIVE" and held["evidence"]["reason"] == "RED_TEAM_PENDING"
    promoted = decide(candidate, review, _PASS_RETURNS, _PASS_TRIALS, "SURVIVED_RED_TEAM")
    assert promoted["decision"] == "PROMOTE_ELIGIBLE"
    assert promoted["evidence"]["applied_to_live_weights"] is False
    assert MIN_AGREEING_FAMILIES == 2
    assert MIN_EXPECTED_PROFIT_TO_FEE_RATIO == 2.0


def _shadow(idea: str, impact: int = 4) -> dict:
    return {
        "source": "arxiv",
        "idea": idea,
        "decision": "SHADOW_CANDIDATE",
        "evidence": {"impact": impact, "domain": "data", "kind": "paper", "license": "NOT_CODE", "reason": "AWAITING_OWN_SCORE"},
    }


def test_the_queue_scores_only_the_idea_we_implemented():
    papers = [
        _shadow("Propose-Filter-Release: Scaling Noise to Typical Sensitivity via Private Filtering"),
        _shadow("Rethinking Neural Thickets Without Weight Perturbations"),
        _shadow("Read, Allocate, Route: Role-Coupled Tokenization for Pixel-Space Generative Transformers"),
        _shadow("Adaptive Scenario Generation for KL-DRO Around a Learned Density Model"),
        _shadow("world2vec: Mechanistic world models through latent dynamics learning"),
    ]
    queued = shadow_queue(papers, limit=2)
    assert queued[0]["idea"].startswith("Adaptive Scenario")
    assert queued[1]["idea"].startswith("world2vec")
    closes = [
        {"desk": "CRYPTO", "notional_usd": 10.0, "realized_pnl_usd": 0.1, "closed_at": f"2026-10-{i:02d}T00:00:00Z"}
        for i in range(1, 41)
    ]
    extra = advance_shadows(papers, closes, red_team=None)
    assert extra[0]["step"] == "decide"
    assert extra[0]["decision"] == "ARCHIVE"
    assert extra[0]["evidence"]["reason"] == "FAILED_OOS"
    assert extra[0]["evidence"]["applied_to_live_weights"] is False
    assert extra[0]["evidence"]["upstream_executed"] is False
    assert isinstance(extra[0]["evidence"]["predicted_score"]["CRYPTO"], float)
    assert extra[0]["evidence"]["sample_n"]["CRYPTO"] == 40
    assert extra[0]["evidence"]["predicted_score"]["FOREX"] is None
    assert extra[0]["evidence"]["sample_n"]["FOREX"] == 0
    assert extra[1]["decision"] == "SHADOW_CANDIDATE"
    assert extra[1]["evidence"]["reason"] == "NO_OWN_IMPLEMENTATION"
    reopened = reopen_static_passes([{
        "source": "arxiv",
        "idea": papers[3]["idea"],
        "decision": "ARCHIVE",
        "evidence": {"reason": "NO_OOS_NUMBER", "domain": "data", "review": {"verdict": "PASS_STATIC", "executed": False}},
    }])
    assert reopened[0]["decision"] == "SHADOW_CANDIDATE"
    assert reopened[0]["evidence"]["supersedes"] == "NO_OOS_NUMBER"


def test_the_weekly_task_stays_on_g():
    from architecture.continuation.windows_scheduler import TASK_SPECS, load_task_registry
    from pathlib import Path

    spec = next(row for row in TASK_SPECS if row["task_name"] == "AHOS_tech_scout_weekly")
    assert spec["schedule_type"] == "WEEKLY"
    assert spec["script"].startswith("scripts/")
    root = Path(__file__).resolve().parents[1]
    doc = load_task_registry(root)
    task = next(row for row in doc["tasks"] if row["task_name"] == "AHOS_tech_scout_weekly")
    command = task["command"].lower()
    assert "g:\\robat\\ahos" in command or "g:/robat/ahos" in command
    assert "c:\\users" not in command

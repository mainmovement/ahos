from architecture.university.research_institute import (
    DESKS,
    SSRN_STATUS,
    decide_hypothesis,
    score_counterfactual,
    weekly_report,
)

_PASS_RETURNS = [0.02, 0.018, 0.021, 0.019, 0.022, 0.017, 0.02, 0.019, 0.021, 0.018, 0.02, 0.019]
_PASS_TRIALS = [
    [0.03, 0.028, 0.031, 0.029, 0.03, 0.027, 0.032, 0.029],
    [0.02, 0.018, 0.021, 0.019, 0.02, 0.017, 0.022, 0.019],
]
_FAIL_RETURNS = [0.01] * 12
_FAIL_TRIALS = [[0.02] * 8, [0.01] * 8]


def test_top_three_ideas_are_shadow_on_every_desk_without_an_invented_score():
    scout = {
        "papers_by_hypothesis": {
            "H15": [
                {"arxiv_id": "1", "title": "old", "published": "2020-01-01"},
                {"arxiv_id": "2", "title": "mid", "published": "2024-01-01"},
            ],
            "H16": [
                {"arxiv_id": "3", "title": "new", "published": "2026-01-01"},
                {"arxiv_id": "4", "title": "newer", "published": "2026-06-01"},
            ],
        }
    }
    doc = weekly_report(scout)
    assert doc["ssrn"] == SSRN_STATUS == "ABSENT_NO_FEED"
    assert [idea["arxiv_id"] for idea in doc["ideas"]] == ["4", "3", "2"]
    assert all(idea["predicted_score"] is None for idea in doc["ideas"])
    assert len(doc["hypotheses"]) == 3 * len(DESKS)
    assert "LISTED_FUTURES" in DESKS
    assert {row["desk"] for row in doc["hypotheses"]} == set(DESKS)
    assert all(row["applied_to_live_weights"] is False for row in doc["hypotheses"])
    assert score_counterfactual(doc["hypotheses"][0], 0.01)["status"] == "UNSCORED"


def test_a_numeric_score_is_kept_and_failed_oos_is_killed():
    scout = {"papers_by_hypothesis": {"H18": [{
        "arxiv_id": "9", "title": "measured", "published": "2026-02-01", "predicted_score": 0.2,
    }]}}
    row = weekly_report(scout)["hypotheses"][0]
    assert row["desk"] == DESKS[0]
    assert row["predicted_score"] == 0.2
    scored = score_counterfactual(row, -0.01)
    assert scored["hit"] is False and scored["applied_to_live_weights"] is False
    killed = decide_hypothesis(row, _FAIL_RETURNS, _FAIL_TRIALS, "SURVIVED_RED_TEAM")
    assert killed["status"] == "KILL"
    assert killed["reason"] == "FAILED_OOS"
    assert killed["applied_to_live_weights"] is False


def test_promote_requires_the_red_team_and_does_not_write_a_weight():
    row = {"predicted_score": 0.2}
    held = decide_hypothesis(row, _PASS_RETURNS, _PASS_TRIALS, None)
    assert held["status"] == "KEEP_SHADOW"
    promoted = decide_hypothesis(row, _PASS_RETURNS, _PASS_TRIALS, "SURVIVED_RED_TEAM")
    assert promoted["status"] == "PROMOTE_ELIGIBLE"
    assert promoted["applied_to_live_weights"] is False
    assert decide_hypothesis({"predicted_score": None}, _PASS_RETURNS, _PASS_TRIALS, "SURVIVED_RED_TEAM")["status"] == "KEEP_SHADOW"

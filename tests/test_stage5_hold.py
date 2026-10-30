import json
from datetime import datetime, timezone
from pathlib import Path

from architecture.markets.multi_signal_block_counter import build_gate_window_report
from architecture.markets.news_desk import sanitize_untrusted_headline
from architecture.markets.signal_brain import news_signal
from architecture.mission.digest_streak import build_digest_streak
from architecture.security.prompt_injection_corpus import CORPUS
from architecture.university.scout_research_bridge import build_research_task, dedupe_papers
import time


def test_news_score_stays_zero_until_two_sources():
    now = time.time()
    one = news_signal("CRYPTO", [{"title": "Bitcoin surges on inflows", "source": "only", "ts": now - 60}])
    assert one["evidence"]["corroborated_2src"] is False
    assert one["score"] == 0.0
    assert one["evidence"]["credibility"] == 0.0
    two = news_signal(
        "CRYPTO",
        [
            {"title": "Bitcoin surges on inflows", "source": "desk-a", "ts": now - 60},
            {"title": "Bitcoin rallies after approval", "source": "desk-b", "ts": now - 120},
        ],
    )
    assert two["evidence"]["corroborated_2src"] is True
    assert two["evidence"]["credibility"] > 0
    assert two["evidence"]["authority"] == "EVIDENCE_ONLY"


def test_injection_corpus_is_neutralized():
    for raw in CORPUS:
        cleaned, hit = sanitize_untrusted_headline(raw)
        assert hit is True
        assert "ignore previous instructions" not in cleaned.lower()
        assert "place live order" not in cleaned.lower()


def test_scout_dedupe_builds_a_non_executing_task():
    papers = dedupe_papers(
        {
            "papers_by_hypothesis": {"H1": [{"arxiv_id": "2510.1", "title": "Calibration"}, {"arxiv_id": "2510.1", "title": "dup"}]},
            "papers_by_pillar": {"P1": [{"arxiv_id": "2510.2", "title": "Momentum"}]},
        }
    )
    assert len(papers) == 2
    task = build_research_task(papers)
    assert task["constraints"]["max_experiments"] == 0
    assert {item["item_id"] for item in task["supplied_items"]} == {"arxiva2510-1", "arxiva2510-2"}


def test_digest_send_stays_blocked(tmp_path: Path):
    day = tmp_path / "reports" / "grok" / "M13_SOAK"
    day.mkdir(parents=True)
    (day / "2026-10-28_digest.json").write_text("{}", encoding="utf-8")
    (day / "2026-10-29_digest.json").write_text("{}", encoding="utf-8")
    doc = build_digest_streak(tmp_path, today=datetime(2026, 10, 29, tzinfo=timezone.utc).date())
    assert doc["consecutive_local_nights"] == 2
    assert doc["sends"] == 0
    assert doc["send_status"] == "BLOCKED"


def test_composite_census_names_the_family_that_moved(tmp_path: Path):
    log = tmp_path / "reports" / "grok" / "PAPER" / "paper_trades.jsonl"
    log.parent.mkdir(parents=True)
    log.write_text(
        json.dumps(
            {
                "event": "NO_TRADE",
                "reason": "COMPOSITE_BELOW_ENTRY",
                "ts": "2026-10-30T01:00:00Z",
                "desk": "GOLD",
                "composite": 0.1,
                "signal_scores": {"news": 0.0, "macro": 0.4, "candles": 0.0, "large_trades": 0.0},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    doc = build_gate_window_report(tmp_path, since="2026-10-30T00:40:16Z", now=datetime(2026, 10, 30, 2, tzinfo=timezone.utc))
    census = doc["composite_stop_census"]
    assert census["every_desk_stopped_at_composite_below_entry"] is True
    gold = census["by_desk"][0]
    assert gold["families_with_any_nonzero_score"] == ["macro_central_bank"]
    assert gold["composite_distribution"]["buckets_vs_entry_0.32"]["inside_entry_band"] == 1

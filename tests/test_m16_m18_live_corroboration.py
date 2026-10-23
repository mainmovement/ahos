"""Tests for M16 Open-Source R&D Crawler and M18 Multi-Source RSS Corroboration & Nightly Brief."""
from __future__ import annotations

from pathlib import Path

from architecture.markets.news_desk import (
    build_nightly_news_brief_fa,
    ingest_rss_feeds,
)
from architecture.university.registry import (
    crawl_open_source_rd,
    is_permissive_rd_license,
)


def test_m16_crawl_open_source_rd_filters_licenses(tmp_path: Path) -> None:
    assert is_permissive_rd_license("MIT") is True
    assert is_permissive_rd_license("BSD-3-Clause") is True
    assert is_permissive_rd_license("Apache-2.0") is True
    assert is_permissive_rd_license("GPL-3.0") is False
    assert is_permissive_rd_license("AGPL-3.0") is False
    assert is_permissive_rd_license("Proprietary-Paid") is False

    out_file = tmp_path / "github_rd_crawl.json"
    res = crawl_open_source_rd(out_path=out_file)
    assert out_file.is_file()
    assert res["paper_only"] is True
    assert res["auto_install"] is False
    assert res["code_executed"] is False
    assert res["admitted_count"] == 4
    assert res["rejected_count"] == 2


def test_m18_ingest_rss_feeds_and_nightly_brief_fa() -> None:
    rss_xml_1 = """<?xml version="1.0"?>
    <rss version="2.0"><channel>
      <item>
        <title>Gold spot holds firm on central bank demand</title>
        <link>https://fred.stlouisfed.org/news/1</link>
        <category>GOLD</category>
      </item>
    </channel></rss>"""
    rss_xml_2 = """<?xml version="1.0"?>
    <rss version="2.0"><channel>
      <item>
        <title>COMEX Gold futures steady on treasury yields</title>
        <link>https://finance.yahoo.com/news/2</link>
        <category>GOLD</category>
      </item>
    </channel></rss>"""

    clusters = ingest_rss_feeds([rss_xml_1, rss_xml_2])
    assert len(clusters) == 1
    assert clusters[0]["topic"] == "GOLD"
    assert clusters[0]["state"] == "CORROBORATED"
    assert len(clusters[0]["independent_domains"]) == 2

    default_clusters = ingest_rss_feeds()
    assert len(default_clusters) >= 3
    assert all(c["state"] == "CORROBORATED" for c in default_clusters)

    brief = build_nightly_news_brief_fa(default_clusters)
    assert "PAPER_ONLY" in brief
    assert "GOLD" in brief

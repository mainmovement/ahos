---
name: ahos-research-intelligence
description: News, narrative, and investigative evidence — rumor vs fact, source independence, timelines. Converts research into AHOS evidence, not headlines.
paths:
  - "architecture/intel/news.py"
  - "architecture/intel/catalyst.py"
  - "architecture/knowledge/**"
---

# AHOS research intelligence

Turn public sources into evidence atoms with provider, timestamp, hash, and
confidence. Distinguish rumor from fact. Cross-check independent sources.

Existing: `architecture/intel/news.py`, RSS providers, `architecture/knowledge/`.

Rules:

- No fabricated prices, quotes, or engagement numbers.
- Missing feed ⇒ UNAVAILABLE, never a bullish default.
- Narrative sentiment is not an opportunity score.
- Do not scrape X/IG/TikTok (policy).
- Cache and provenance required before a claim enters a decision packet.

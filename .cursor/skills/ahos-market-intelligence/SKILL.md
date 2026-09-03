---
name: ahos-market-intelligence
description: AHOS market structure — discovery, DEX, volume, liquidity, momentum, whales, microstructure. Use for opportunity/market analytics, not final decisions.
paths:
  - "architecture/intel/**"
  - "architecture/providers/**"
  - "architecture/pipeline/**"
  - "providers.ts"
---

# AHOS market intelligence

Existing modules: `architecture/intel/market_structure.py`, `tokenomics.py`,
`catalyst.py`, `exitability.py`, `whales.py`, `viral.py`,
`architecture/providers/`, `architecture/collector/`, Lane A discovery
(read-only).

Low-latency WebSocket/order-book engine is currently MISSING. Do not claim HFT.
Do not rewrite the stack in Rust without profiling evidence.

Outputs are evidence and candidate features. Canonical decision remains Python
`IntelligenceEngine` / future Decision API. Do not emit FOMO language.
Preserve UNKNOWN for missing books, holders, or locked-LP data.

Social scrape of X/IG/TikTok is OUT_OF_POLICY. DEXTools full API is COST_BLOCKED
without a key. Record BLOCKED honestly.

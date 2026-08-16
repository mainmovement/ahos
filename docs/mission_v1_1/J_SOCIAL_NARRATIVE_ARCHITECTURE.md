# J. SOCIAL / NARRATIVE INTELLIGENCE ARCHITECTURE — Wave-6 (Part VII) — 2026-08-11
# Interfaces first (no premature paid APIs). ATTENTION ≠ ORGANIC DEMAND — enforced structurally.

## 1. Source feasibility (state)
| Source | Path | State |
|---|---|---|
| RSS (CoinTelegraph/TheBlock LIVE VERIFIED) | PAL narrative_rss chain | IMPLEMENTABLE NOW (adapter design below) |
| CryptoPanic | endpoint 404 at probe (R-13) | BLOCKED-UNVERIFIED; re-probe before build |
| Reddit | OAuth JSON (free) — signup/keys user-side | DESIGNED; needs user keys → UNKNOWN |
| Telegram public channels | Telethon (user acct; MTProto proxy for IR) | DESIGNED; ToS-gray → advisory-only data |
| X/Twitter | $200/mo | COST-BLOCKED (documented, excluded) |
| GitHub | API free 60/h(anon) LIVE VERIFIED | IMPLEMENTABLE (dev-activity aspect) |
| Instagram/Discord | scraping fragility + ToS | OUT (documented) |

## 2. Architecture (narrative_rss MVP → later channels)
social_event(event_id, channel, token_ref NULL, text_hash, author_ref NULL, ts_published, ts_retrieved,
  platform, language, url, raw_ref)   — provenance + dual timestamps (never fabricate author/ts).
Features (future fs_v0.3): mention_velocity_1h/24h · unique_author_ratio · engagement_velocity ·
cross_platform_propagation (same story across ≥2 channels within Δt) · narrative_emergence (burst z-score
vs 7d baseline) · narrative_persistence (half-life of mentions) · dev_activity (commit/issue velocity).
Matching: deterministic ticker/cashtag/contract-address matching ONLY (no fuzzy LLM matching into features).

## 3. ATTENTION vs ORGANIC DEMAND (structural separation)
Two distinct feature families, never merged upstream:
- attention_* (mentions/velocity/propagation)
- demand_proxies_* (unique buyers growth, unique maker diversity, buy-sell imbalance — from market data)
A social-alerts channel may mark `attention_spike`, but ranking requires demand/security evidence —
social alone NEVER generates an opportunity (Mission law; ranker comment + tests pin it).

## 4. Anti-manipulation (investigation backlog)
bot-ish heuristics: account age/entropy unknown on RSS (N/A), recycled-content via text_hash dedupe,
coordinated timing across channels (flash-mob signature), paid-promo markers ("sponsored"/known shill
phrase bank — versioned, reviewable). Each heuristic = fixture-tested before entering registry.

## 5. AI layer (Part XVII link)
Narrative summarization may call AI-PAL (free-tier/local first, advisory text). Embeddings/clustering =
deterministic or local-model only; nothing from AI enters numeric features unvalidated.

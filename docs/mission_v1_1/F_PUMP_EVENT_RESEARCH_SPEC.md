# F. PUMP-EVENT RESEARCH SPECIFICATION v1 — Wave-6 (Part III) — 2026-08-11
# "Pump" is hereby replaced by a formal event grammar. PRE-REGISTERED. Not a signal.

## 1. Event grammar
EVENT(chain?) := MOVE(class) within HORIZON(h) from ENTRY(e), witnessed in stored series.
- classes MOVE ∈ {+25%, +50%, +100%, +200%} (and symmetric −25/−50% as decay classes)
- h ∈ {15m, 1h, 4h, 12h, 24h, 72h, 7d}
- e = first stored price with retrieved_ts ≤ T0+15m (T0 = first reliable discovery time)
- base variant: RAW (+ auxiliary variants §3)

## 2. Per-candidate event record (extends outcome_label semantics — Part III extras)
max_favorable_excursion (MFE) · max_adverse_excursion (MAE) · time_to_event (first hit ts, per class) ·
drawdown_before_event (min run-up-prior trough → peak path distance) · hit_at (ts) — all from stored ticks.
Granularity law: horizons below tick spacing (5–15m in practice) get uncertainty notes; 15m labels only when
a ≥2-point window exists (wave-5 semantics kept, test-pinned).

## 3. Variant grid (anti-delusion — Part III tail)
- RAW: hit = MFE ≥ class.
- LIQ_ADJ: hit requires MFE ≥ class AND min liquidity within window ≥ $25k at hit (primitive floor —
  constant, versioned, NOT optimized; refined only by registered batch).
- RUG_ADJ: hit counted regardless (raw), but a companion flag EVENT_WITH_RUG (post-event retracement ≥70%
  within remaining window) separated — a +100% that ends −80% is studied as its own class.
A raw +100% in an illiquid token is NEVER equated to a healthy opportunity (Part III rule embedded as
LIQ_ADJ + RUG_ADJ variants).

## 4. Statistical usefulness evaluation (council task, periodic)
Grid fitness = baseline-rate × discriminability × coverage (share of resolved candidates whose labels
computable). Grid may be CHANGED only via a new pre-registered spec version (v2) — never tuned on the
same data that suggested the change (multiplicity law).

## 5. Required sample plan (power honesty)
Descriptive baselines: any n. Feature claims: n ≥ 200 resolved per stratum with ≥20 positives for the
class, else verdict = INSUFFICIENT_DATA (hard-coded in baseline_stats). Multiplicity: family-wise budget
documented per study batch (search-space registry, doc H).

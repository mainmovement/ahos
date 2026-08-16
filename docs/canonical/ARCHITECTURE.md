# AHOS CANONICAL — ARCHITECTURE
Layer map (current truth). Detail: docs/TARGET_ARCHITECTURE_vNext.md, docs/ARCHITECTURE_FINAL.md (legacy base),
docs/mission_v1_1/C.

```
PROVIDERS (12 LIVE-probed 2026-08-11; fallbacks per capability)   [docs/canonical/PROVIDERS.md]
  → PAL (discovery/pal.py; envelope contract; breaker; budget; cache; raw-archive)
  → DISCOVERY (discovery/collect.py — GT new_pools + DEX profiles; 5-min poll capable)
  → IDENTITY (canonical token_id/pair_id; chain registry)         [discovery/identity.py]
  → STORE (schema v1.2: tokens/pairs/observations/raw_payloads/…; sqlite canonical, pg twin)
  → LIFECYCLE 72h (DISCOVERED→OBSERVING→DEAD→RESOLVED; gaps registered, never faked)
  → SECURITY GATE (veto registry; UNKNOWN≠PASS; fixtures)         [discovery/security_gate.py]
  → FEATURE STORE fs_v0.1 (16 features; leakage L1–L4)            [discovery/feature_store.py]
  → OUTCOMES (7 horizons × 4 classes; no-peeking horizon closure) [discovery/outcomes.py]
  → RANK (rank-first; no numeric score; NO OPPORTUNITY valid)     [discovery/ranker.py]
  → RESEARCH LAB (H1–H13 rejected evidence; H14+ from E-01 data)  [strategy_lab/]
  → TELEGRAM (Persian contract frozen; REAL pending blocker①)     [docs/mission_v1_1/I]
```

## Invariants (enforced by tests/CI)
1. Every persisted row carries provider+timestamps (replayable). 2. Security veto precedes ranking.
3. Deterministic code owns numbers; AI layer is advisory text only (future: AI-PAL, free-tier first).
4. Score weights are lab hypotheses — none ship unvalidated. 5. n8n orchestrates; core logic lives in Python services
   (Execute Command avoided for new flows after R-10). 6. $0/month.

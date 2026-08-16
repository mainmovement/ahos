# F. 72-HOUR OBSERVATION STATE MACHINE v0.1 — Mission v1.1 §7 — 2026-08-11
# Code: discovery/lifecycle.py (STEP 5). Deterministic, clock-injected (now() is a parameter — testable).

## 1. States
```
DISCOVERED ──(poll snapshots)──► OBSERVING ──► RESOLVED (T+72h reached)
    │                              │  ▲
    │ DEAD (no obs > 24h: provider  │  └── SECURITY-EVENT can occur any time (flag, not a terminal state)
    │        empty, price/liq NULL) │        → token flagged; observation continues; ranking excludes
    ▼                              ▼
  DEAD(terminal)              SECURITY_FLAGGED (parallel attribute)
```
Any state → REJECTED? — **no**: candidates are never "rejected" from history; they RESOLVE with outcomes.
Exclusion from ranking is a ranking-layer decision, not lifecycle deletion.

## 2. Snapshot schedule (per token, driven by availability, not wall-clock assumptions)
S0 at discovery, then ±tolerance: +15m(±5m), +1h(±10m), +4h, +12h, +24h, +48h, +72h(±30m), +7d(optional tail).
Collector ticks every 5 min; lifecycle computes DUE snapshots from first_seen_ts + schedule.
Missed slot (downtime) ⇒ gap_register entry; NO backfill fabrication (late data lands with its real retrieved_ts).

## 3. Transition rules (pure functions)
```
on_observation(token, obs):        OBSERVING.streak resets; DEAD-watch clears; state=OBSERVING
tick(token, now):                  if last_obs < now−24h and state==OBSERVING → DEAD
                                   if now ≥ first_seen+72h and state∈{DISCOVERED,OBSERVING} → RESOLVED
                                   DEAD tokens keep T+72h outcome resolution (data may resume) → RESOLVED(from DEAD)
on_security_veto(token):           security_flagged=True (attribute), lifecycle state unchanged
```
RESOLVED triggers outcome computation (STEP 8): for each horizon h ∈ {15m,1h,4h,12h,24h,72h(+7d)} and
event class E ∈ {+25,+50,+100,+200%}: hit = max_favorable_within_h ≥ E, entry = first obs price with
retrieved_ts ≤ first_seen+15min (closest-to-discovery price, availability-consistent).

## 4. Persistence
```
observation_state(token_id PK, state, entered_ts, first_seen_ts, last_obs_ts, security_flagged, meta)
lifecycle_events(id, token_id, ts, from_state, to_state, reason)   -- full audit trail
gap_register(id, token_id, kind, expected_ts, noted_ts, detail)    -- no silent holes
```

## 5. Exit criterion semantics (what 72h "PASS" means for Phase-2 exit — roadmap)
System-level 72h exit = the *pipeline* ran 72h continuously with ≥X tokens observed end-to-end.
Sandbox wave-5 delivers code + fixtures + MOCK-clock proof + first REAL T0 cohort (collection started
2026-08-11 UTC); full 72h live window completes ≥ 2026-08-14 and is reported as its own evidence item
(VPS removes sandbox-uptime limits; sandbox runs are best-effort continuity).

## 6. Event-class neutrality (Mission §11)
+25/+50/+100/+200 at listed horizons = study grid, NOT final signal thresholds; promotion requires the
research gate (train-only association → OOS replication → multiplicity budget). The grid itself is
pre-registered here to avoid post-hoc threshold shopping.

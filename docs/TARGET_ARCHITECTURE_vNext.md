# AHOS — TARGET ARCHITECTURE vNext (opportunity-intelligence platform) — 2026-08-11
# Additive over frozen Phase-1 base. No verified component rewritten. All external access via PAL.

```
EXTERNAL SOURCES (DexScreener · GeckoTerminal · GoPlus · RugCheck · RPCs · RSS/CryptoPanic ·
                    BinanceVision/LBank · GitHub … all behind PAL: fallback+cache+breaker+provenance)
        │
        ▼
DISCOVERY ENGINE (M2)            — 5-min poll: new pairs/pools → candidates (dedupe, source-stamp)
        ▼
NORMALIZATION (PAL schemas)      — token_meta / pair_state / raw payloads archived for replay
        ▼
SECURITY ENGINE (M4)  ── HARD VETO ──► verdict row per token (UNKNOWN ≠ PASS; unknown ⇒ cap recommendation)
        ▼
ON-CHAIN ENGINE (M6)             — holders, deployer history, concentration (public RPC, rate-budgeted)
        ▼
WHALE INTELLIGENCE (M6)          — wallet net-flow, clusters; reputation earned over evidence
        ▼
MICROSTRUCTURE + NARRATIVE (M7)  — vol/liq trajectories; mention velocity, unique-authors ratio
        ▼
EVENT/CATALYST ENGINE            — listings, launchpads, announcements (source-stamped, time-decayed)
        ▼
OPPORTUNITY SCORING (M8)         — explainable, rank-first (numeric only post-E-01 calibration)
        ▼
RISK ENGINE (existing discipline) — concentration/liquidity/execution penalties; veto check
        ▼
RESEARCH/BACKTEST ENGINE (existing LAB) — score-hypothesis validation + E-01 outcome studies
        ▼
DECISION ENGINE                  — {WATCH, WAIT, HIGH-RISK-ENTRY*, AVOID}  *only if all gates + user risk mode
        ▼
PERSIAN TELEGRAM UX (M9)         — alerts, position intake (confirm-first), monitoring levels
        ▼
USER                                       ┃  POSITION MONITOR (parallel): watch→🟢🟡🟠🔴 alerts
```

## Invariants (enforced by tests where possible)
1. Every persisted row carries provenance (provider, fetched_at) — replayable.
2. Security veto precedes scoring; unknown checks cap recommendation.
3. Deterministic code owns numbers; free-tier AI layer is advisory text only.
4. Score weights are lab hypotheses; no weight ships unvalidated.
5. n8n workflows call PAL/engine endpoints; Telegram never talks logic, only UX.
6. Cost ceiling: $0/month recurring by design (free tiers + public endpoints only).

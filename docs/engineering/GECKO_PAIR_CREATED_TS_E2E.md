# GeckoTerminal `pool_created_at` → SQLite `pair_created_ts` E2E

**Date:** 2026-09-09  
**HEAD verified:** `cf7711ea25b9a7487fbf71de776666ec8af2ed0c` (`main` after PR **#78**)  
**Classification:** `RUNTIME_VERIFIED` for this persist path only.  
**Product classification unchanged:** `INTEGRATION_READY` (agent-host).  
**Not claimed:** `OPERATOR_READY`, `PRODUCTION_READY`, Phase 3 `COMPLETE`, identity `VERIFIED`, overlay `PASS`, canonical `BUY`.

Does **not** edit Lane A. Does **not** backfill historical NULLs. Does **not** treat pair age as security PASS.

---

## What this supersedes

`docs/engineering/PHASE2_SECURITY_GATE.md` recorded (as of that phase) that
SQLite `production_observations` did not persist `pair_created_ts`. That was
true **then**. It is **not** current repository truth.

| Change | Merge | What it did |
|--------|-------|-------------|
| PR **#77** | `e0d68b5` | Lane B collector INSERT + additive column for `pair_created_ts` |
| PR **#78** | `cf7711e` | GeckoTerminal adapter maps `pool_created_at` → `NormalizedTokenCandidate.pair_created_ts` |

PHASE2 is historical evidence. This note + `reports/gecko_pair_created_ts_e2e_RUNTIME_VERIFIED.json` are the living proof of the full path.

---

## Path proven (not adapter-only)

```text
GeckoTerminal pool_created_at
  → NormalizedTokenCandidate.pair_created_ts
  → CollectorEngine persist
  → SQLite production_observations.pair_created_ts
  → fresh SQLite reload (second connection)
  → independent GET /networks/solana/pools/{address} exact epoch match
```

Official command (agent-host, calibration-ineligible):

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m architecture.runtime \
  --single-cycle --observation-cycle --evidence-source sandbox --chain solana --limit 5
```

- `run_id`: `run_1788966487_3b43873d`
- start: `2026-09-09T15:08:07Z`
- exit: `0`
- SQLite: `data/e01_discovery.sqlite`
- evidence namespace: **`sandbox`** (not `local`)

---

## Runtime facts

| Fact | Value |
|------|-------|
| Rows before cycle | 16 |
| Rows after cycle | 24 |
| Historical rows rewritten | **0** |
| New GeckoTerminal rows | 5 / 5 with `pair_created_ts` set |
| New GeckoTerminal `unknown_fields` contains `pair_created_ts` | **no** |
| Independent Gecko pool lookup | **5/5 exact match** |
| Pre-#78 GeckoTerminal rows still NULL | 10 (honest; no backfill) |
| Dexscreener this cycle | 2 known + 1 provider-null `pairCreatedAt` |
| Canonical outcomes | 8 × `INSUFFICIENT_EVIDENCE` |
| Identity | 8 × `UNRESOLVED` |
| Security overlay | 8 × `INCOMPLETE` |
| Live BUY / alerts_allowed | **0** |
| Lane A freeze | OK (36) |

Pair age present ≠ overlay PASS. Missing honeypot / LP lock / tax / holders remain UNKNOWN → INCOMPLETE.

---

## Identity STOP (unchanged)

Gecko `NormalizedTokenCandidate.address` is still the **pool** address, not the
base token. Changing that is identity-adjacent and is **not** done here.

---

## Evidence artifact

`reports/gecko_pair_created_ts_e2e_RUNTIME_VERIFIED.json`

Phase 3 remains **PARTIAL**.

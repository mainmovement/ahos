# AHOS — Next Development Backlog

**Date:** 2026-08-27  
**Branch:** `cursor/ahos-cleanup-alignment-4bde` (PR #19)  
**Current classification:** `INTEGRATION_READY` (agent-host)  
**Law:** Implement real capability; do not spawn status docs without engineering change.

---

## Completed this pass (do not re-implement)

| ID | Result |
|----|--------|
| P0-1 | LIVE SUCCESS probe on agent host (dexscreener, geckoterminal) |
| P0-2 partial | `local` ledger accruing predictions; **outcomes still missing** |
| P0-3 | Narrative feed-through wired (R-80) |
| P1-1 | Market structure analyzer + risk findings |
| P1-2 | Tokenomics analyzer (unlock/vesting stays UNKNOWN) |
| P1-3 | Catalyst detector with provenance |
| P1-5 partial | Scoring semantic contract v1 (numeric parity deferred) |

---

## P0 — Remaining integration blockers

| ID | Goal | Why | Acceptance | Priority |
|----|------|-----|------------|----------|
| P0-2b | Produce outcome labels for `local` predictions | Calibration has 348 preds / 0 pairs (`no_matching_label`) | Non-zero eligible pairs OR documented blocker in observation/active-set seeding | P0 |
| P0-1b | Operator Windows laptop `--probe-providers` SUCCESS | Iran/filter egress may differ from agent host | Committed laptop probe JSON | P0 (OWNER) |

## P1 — Intelligence depth

| ID | Goal | Priority |
|----|------|----------|
| P1-4 | Holder/smart-money live path where free RPC allows | P1 |
| P1-5b | Optional numeric parity harness TS↔Python (advisory) | P1 |
| P1-6 | Development-activity collector (honest UNKNOWN without stars-as-quality) | P1/P5 |

## P2 — Calibration / learning

| ID | Goal | Priority |
|----|------|----------|
| P2-1 | First real calibration report with guards met | P2 |
| P2-2 | Governed weight proposals only | P2 |

## P3 — UX

| ID | Goal | Priority |
|----|------|----------|
| P3-1 | Live Telegram via gateway | P3 (OWNER token) |
| P3-2 | Persian evidence Q&A on gateway | P3 |

## P4 — Operations

| ID | Goal | Priority |
|----|------|----------|
| P4-1 | Execute 168h soak | P4 (OWNER) |
| P4-2 | 7-night backups | P4 (OWNER) |
| P4-3 | Optional CI | P4 (OWNER workflows) |

---

## Recommended next single step

**Seed/fix observation active-set so Lane-A outcome labels join `local` predictions** (P0-2b) — unlocks real calibration without fabricating data.

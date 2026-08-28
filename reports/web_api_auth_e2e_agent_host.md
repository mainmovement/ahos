# Agent-host E2E — Lane-B web API auth (not Windows OPERATOR_READY)

**Date:** 2026-08-28T20:34Z  
**Branch tip:** `8419bc9` (PR #31)  
**Claim:** Auth gate works against live `next dev --hostname 127.0.0.1`  
**Not claimed:** Windows G1–G11, PRE_SOAK, OPERATOR_READY

## Matrix (live :3000)

| Request | HTTP | Meaning |
|---------|------|---------|
| No `Authorization` | 401 `WEB_API_UNAUTHORIZED` | Fail-closed |
| Wrong Bearer | 401 `WEB_API_UNAUTHORIZED` | Fail-closed |
| Matching `AHOS_WEB_API_TOKEN` | **not 401** (this host: 500 DB query — Postgres not reachable here) | Auth passed; app ran |

## Operator gate G2 on this host

With token in `.env` (gitignored): G2 reaches the live probe and reports **FAIL** on HTTP 500 (honest — no local Postgres). Without token: G2 **BLOCKED** before probe.

Windows owner Postgres (STATE B) is required for G2 **PASS**.

## Next owner step

Merge PR #31 → post-merge reconcile (ensures token) → `npm run dev` → Windows operator gate → paste JSON.

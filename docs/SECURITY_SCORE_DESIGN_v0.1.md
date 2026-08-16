# AHOS — SECURITY SCORE DESIGN v0.1 (DESIGN — Maturity A) — Security can veto opportunity.

## Hard-veto registry (any TRUE ⇒ verdict AVOID, logged, non-overridable by score)
| Check | Source(s) | Note |
|---|---|---|
| Honeypot / cannot sell | GoPlus (+Honeypot.is EVM 2nd opinion) | buy-sim/block flag |
| Sell tax > 25% or dynamic-tax abuse | GoPlus | extreme extraction |
| Blacklist / trading-disable functions | GoPlus/RugCheck | user can be frozen |
| Hidden/uncapped mint authority active | RugCheck(SOL)/GoPlus(EVM) | supply attack |
| Proxy admin can drain/upgrade to malicious | GoPlus proxy checks | upgradeable risk |
| Deployer linked to prior rug | RugCheck creator history + repo watchlist | grows from E-01 frauds |
| LP not locked/burned AND pool age < 7d | RugCheck/GoPlus LP info | rug-time risk |

## Soft penalties (reduce score, no veto)
LP lock < 30 days · top-10 holders > 20% (scale 20–50%) · creator-holding > 10% · freeze authority
present (SOL) · mutable metadata · unverified contract source (EVM) · zero audits + high FDV ·
bundled-supply heuristics (E-01 feature, matures later).

## UNKNOWN discipline
Every check unavailable → UNKNOWN (not PASS). Confidence of security verdict = coverage-weighted.
Recommendation ceiling: any UNKNOWN hard-veto check ⇒ recommendation ≤ WATCH (never HIGH-RISK-ENTRY).

## Storage
security_checks(token_id, ts, provider, check_key, value, raw_ref) — raw JSON pointer retained for audit.

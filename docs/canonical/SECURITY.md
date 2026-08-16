# AHOS CANONICAL — SECURITY (two layers: token-security veto + platform security)
Detail: docs/mission_v1_1/E · docs/SECURITY_CHECKLIST.md · docs/SECURITY_SCORE_DESIGN_v0.1.md.

## Token security gate (wave-5+)
Registry (E §2): honeypot · sell_tax_extreme · blacklist_function · mint_authority_active ·
freeze_authority_active · lp_not_locked_fresh_pool · deployer_prior_rug (CRITICAL) +
proxy_risk_upgradeable · ownership_renounced_absent · holder_concentration_high (HIGH).
TRUE(any CRITICAL) ⇒ SECURITY_VETO (recommendation AVOID; excluded from ranking with reason).
UNKNOWN among CRITICAL ⇒ PASS_WITH_UNKNOWN (recommendation ≤ WATCH). UNKNOWN never = PASS.
Providers: RugCheck (SOL, LIVE VERIFIED) → GoPlus (DEGRADED, re-probe pending) → on-chain RPC heuristics (Phase-3).
Fixture veto set = 7/7 (labeled FIXTURE; never a real-world detection claim).

## Platform security
- Secrets env-only (TELEGRAM_BOT_TOKEN etc.); scans clean each wave; compromised legacy token = OPEN blocker①.
- Auth-first admin gating (chat-id allowlist); kill switch three enforcement points (dryrun-proven S4/S5).
- n8n v2 secure defaults honored (ExecuteCommand env-gated, R-10).
- Raw evidence append-only; verdicts supersede by timestamp (never overwrite).
- Fail-closed: provider down ⇒ error_state rows + coverage drop ⇒ recommendations cap themselves.

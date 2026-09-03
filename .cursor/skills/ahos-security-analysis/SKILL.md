---
name: ahos-security-analysis
description: Defensive token and platform security review — honeypot, sellability, mint/freeze, taxes, rugs, auth, secrets. White-hat only. Never attack external systems.
paths:
  - "architecture/security/**"
  - "architecture/providers/adapters.py"
  - "discovery/security_gate.py"
  - "paper_trading/security_multi.py"
disable-model-invocation: true
---

# AHOS security analysis (defensive)

This skill is white-hat analysis of AHOS-held evidence. Do not probe or attack
third-party systems, wallets, or contracts beyond documented public APIs
already used by AHOS.

Lane A `discovery/security_gate.py` verdicts are FROZEN:
`SECURITY_VETO` / `PASS_WITH_UNKNOWN` / `PASS`.
Lane B may compose a documented overlay:

- REJECT ⇐ SECURITY_VETO / confirmed critical risk
- INCOMPLETE ⇐ unknown critical (do not call this PASS)
- STALE ⇐ expired security evidence
- PASS ⇐ all criticals resolved FALSE and coverage sufficient

Never treat missing security as safe. Do not copy the GoPlus adapter pattern
that defaults missing `is_honeypot` to false.

Critical rejection classes: honeypot, unsellability, malicious blacklist,
dangerous mint/freeze, extreme sell tax, active rug, fraudulent deployer,
trapped liquidity.

NO SECURITY PASS ⇒ no positive eligibility, paper entry, or opportunity alert.

Platform: fail-closed web/Telegram auth, no secret commits, HTML escape,
`AHOS_PAPER_ONLY=1`.

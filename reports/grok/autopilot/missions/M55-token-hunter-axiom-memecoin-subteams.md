# M55: Token Hunter upgrade (Axiom-class terminals, memecoin pump hunting) + agent sub-teams

Owner directive 2026-10-07 01:05 Tehran (Mehrdad). Newest owner statement wins; extends M33 Token Hunter and M12 agent organisation. Do NOT build parallel modules: search G:\robat\ahos first and extend M33 / config/agent_registry.yaml / existing token-hunter, on-chain, and Tina scam-check code.

## 1. Use Axiom and similar terminals as signal sources
- Axiom (axiom.trade, Solana memecoin terminal) and peers such as DexScreener, DexTools, GMGN, Birdeye, Photon and BullX: use their public or legal data (new pairs, migrations, smart-money and whale wallets, holder distribution, volume spikes) as INPUT signals for AHOS.
- Read-only adapters first. No wallet connection, no private keys, no automated buys through these terminals. Respect each site's ToS; prefer official APIs; no scraping behind logins.
- Each source gets a reliability score that Dana (data quality) keeps updated.
- Status: VISION until adapters + tests exist.

## 2. Hunt memecoins that can pump at any moment (much more effort)
- Early-detection pipeline: new launches (pump.fun-style launchpads, Raydium/Meteora migrations), first-minute liquidity, buyer velocity, smart-wallet entries, social and news bursts.
- A Tina scam gate is mandatory before any signal: mint/freeze authority, LP lock/burn, honeypot simulation, top-holder concentration, dev-wallet history, bundled-buy detection.
- Speed matters: event-driven (websocket/stream), not slow polling.
- PAPER_ONLY: small paper slice, hard stop-loss and take-profit ladder, per-token max loss, and a daily memecoin loss cap. Every trade is logged to the single ledger with the reason.
- Honest metrics: hit rate, rug rate avoided, paper PnL. No claims without evidence.

## 3. No agent should be overloaded: sub-teams under each domain agent
- Each domain lead (e.g. US stocks, crypto/Kamyar, on-chain/Nima, token security/Tina, gold/oil, Asian/European stocks) can run a team of sub-agents: scanner workers, analysts and an executor-proposer.
- Example: while the US-stocks lead is busy with one buy, a scanner sub-agent keeps watching other opportunities and queues them with scores, so good setups aren't missed.
- The lead assigns work; sub-agents have authority NONE by default (propose only). Execution still goes through the deterministic Execution Gateway + risk (Ramin) + kill switch.
- Capacity rule: when a lead's queue of unhandled opportunities exceeds a threshold, spawn a worker from an approved template (bounded count, budget cap, logged). No unbounded auto-creation.
- Register sub-agent templates in config/agent_registry.yaml (extend M12; one registry).

## Acceptance (when Claude implements)
- Adapters for at least DexScreener + one Axiom-class source behind a fail-closed interface, with mocked tests.
- Memecoin pipeline with Tina gate tests (honeypot, mint authority, LP) and paper-only execution path tests.
- Sub-team spec in the registry + an orchestrator test showing a second opportunity is captured while the lead is busy.
- PAPER_ONLY, no keys, no push. 19-agent review per owner workflow.

# L. 15-AGENT COUNCIL — WAVE-6 DECISION LOG — 2026-08-11
# Chain: Producer → Critic → Quant → Security → Red-Team → QA → Auditor. Disagreements recorded (never hidden).

## D1. Document hygiene plan — APPROVED (14/15, 1 reservation)
- Architect: canonical set shrinks context while preserving traceability — APPROVE.
- Data Architect: schema files untouched; canonical DATA_MODEL references live DDLs — APPROVE.
- Researcher: negative evidence untouched (uploads dup groups NOT auto-deleted) — APPROVE.
- QA: demanded hash-recording pre-move — satisfied (D manifest) — APPROVE.
- Security (14) RESERVATION: `docs/ISSUES_REGISTER.md` stub must keep the exact archive path (it does);
  uploads dedup deletion requires USER sign-off — recorded as binding rule, not objection. ✔ carried.
ACTION: 2 files archived with stubs + sha256; 194-file inventory + dup report published.

## D2. Holder-probe refutation — LOGGED (Part XXIV case study)
- Producer (On-chain, 4) had drafted "getTokenLargestAccounts LIVE VERIFIED" expectation.
- Probe battery (5/5 rejections: 429×3, 403, timeout, 401) REFUTED feasibility from free public RPCs.
- Red-Team: "this is exactly why probes precede claims" — adopted as standing rule: no capability claim
  without a probe id in the record. Docs E/I corrected with explicit "standing correction" notes (kept visible).
ACTION: holder features fs_v0.2 code-complete but emit only from REAL snapshot rows (currently absent);
alternatives (Helius/QuickNode free tiers) marked UNKNOWN — user-signup-dependent.

## D3. fs_v0.2 additive approval — APPROVED
- Quant (10): volume_acceleration-style features on 5m series need the ≥12-point guard — PRESENT (VOL_WINDOW).
- Backtesting (11): persistence stamp feature_set in computed_by — done.
- Statistician: baseline guards MIN_N=200/MIN_POS=20 locked as module constants (not args) — done.
ACTION: 5 features (3 market COMPUTABLE now; 2 holder awaiting source) + registry⇄computed equality test.

## D4. baseline_stats implementation — APPROVED with one guard tightened
- Critic: original `evaluate_condition` allowed caller-made SQL fragments — acceptable (internal research
  tool, not user-exposed) BUT every cell must be logged into SEARCH_SPACE_REGISTRY — enforced in CLI path;
  note added to doc G §2. Verdict language restricted to {INSUFFICIENT_DATA, DESCRIPTIVE_OK} (no "signal").
- Live REPORT-mode run: 2 pre-registered cells → both INSUFFICIENT_DATA (0 resolved tokens; 72h barrier
  not elapsed). Registry seeded (2 batches… corrected to batch B1 only; see registry JSON).

## D5. Canonical set (12 docs) — APPROVED
QA verified: no fact in canonical docs contradicts detail docs (spot-check STATE/SECURITY/RESEARCH);
README now points newcomers to canonical set first.

## Standing confirmations
Live trading CLOSED · $0/month · rank-first · H1–H13 immutable · E-01 collection continues
(127 tokens/155 obs at wave-6 close) · blockers ①② unchanged (user).

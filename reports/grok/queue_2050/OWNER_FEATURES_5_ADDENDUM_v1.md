<!-- Tehran: 2026-10-09 16:41 (UTC+3:30) | Version: v1 | Author: Soltan | Reason: owner approval 2026-10-09 16:30 (5 features: results judge, circuit breaker, nightly digest, backups, teaching mode). -->
# OWNER FEATURES 5 ADDENDUM v1
Status: PLAN ONLY. Input for M34.1 like DEDUP_MERGE_MAP.md. Do not implement here.

## Coverage (owner approval 16:30 Tehran)

| # | Feature | Existing mission | Class | Addendum spec |
|---|---|---|---|---|
| 1 | Independent results judge (computes paper P&L; no self-grade) | **M42** hash-chained ledger + Accounting/Financial Ledger Agent (#36, P1-29). Not Independent Decision Judge #38 (council GO/NO-GO). Erfan = evidence hash only. | **OVERLAP** | Results Judge reads ONLY the single hash-chained ledger; recomputes realized/unrealized paper P&L + fees itself. Trading/CIO/strategy agents MUST NOT self-report P&L for grading. Output = signed P&L snapshot (INV-19) feeding M25 gate + M35.4 digest. M58.1 self-eval stays advisory, never promotion authority. |
| 2 | Circuit breaker: daily/weekly paper loss -> halt + Telegram | **M39** kill switch + fault injection; vision drawdown ladder (daily loss); M47 READ/DOWNGRADE/HALT; `architecture/risk` CircuitBreaker. | **OVERLAP** | Add daily AND weekly paper-loss limits (config, PAPER_ONLY). On breach: flatten remaining paper + HALT new entries (fail-closed) + Telegram alert to owner allowlist (M61 path; no second bot). Monthly fault-injection drill must include loss-limit trip. AI cannot override HALT. |
| 3 | Nightly Persian Telegram digest (trades, reasons, P&L, University learned) | **M35.4** Nightly Persian report by Kian (extends **M31**; no second reporter). | **OVERLAP** | Digest body must include: closed paper trades + reasons, P&L from Results Judge/ledger (not agent claims), and what the University learned that day (M30/M49/M59 lesson deltas). Number-consistency vs ledger snapshot (M31.3). Idempotent send (M31.4). |
| 4 | Automatic nightly backups of memories + ledger (portable, outside working tree) | **G10** backup/restore drill (`scripts/sqlite_backup_restore.py`); M42 ledger; M30 memory; M62 portable. Default `data/backups` is INSIDE tree today. | **OVERLAP** | Nightly job backs up memory stores + ledger to a portable path OUTSIDE the repo working tree (e.g. sibling `ahos_backups/`). G10 drill must stay green on that dest. No secrets/.env in archives. Restore dry-run weekly. |
| 5 | Owner teaching mode: explain every trade in simple Persian | None (Kian M35 chat/report is not teaching-mode). | **NEW M65** | On owner request (and optionally after each paper close): explain the trade in simple Persian — what, why, risk, outcome — using ledger + decision record only. No live tips, no profit promises. Reuses M35.1/M61 channels; no second Telegram bot. |

## Acceptance tests
1. Judge: seeded paper ledger; Judge P&L matches hand calc; trading agent forged P&L is ignored for M25.
2. Breaker: inject daily then weekly paper loss over limit -> HALT + Telegram mock/allowlist receipt; resume only by owner.
3. Digest: one idempotent Persian message with trades, reasons, Judge P&L, University lessons; numbers match ledger.
4. Backup: nightly artifact outside tree; G10 drill PASS; restore into scratch equals source hashes.
5. M65: sample closed paper trade yields simple Persian explanation with evidence_refs; refuses LIVE advice.

## Laws (binding)
PAPER_ONLY (INV-01) — two-source (1 source = UNKNOWN, disagreement = CONFLICT) — zero cost (free/keyless or owner-approved $0) — no .env reads/edits — no profit promises (North Star aspirational, INV-15) — no push (INV-04) — Lane A frozen (INV-03).

## Order (see DEDUP_MERGE_MAP v1.3)
F1 with step 13 (M42) — F4 with G10 + step 10 (M62 dest) and step 13 (ledger inclusion) — F3 with step 16 (M35.4) — F5 **M65** after M35.4 in step 16 (needs M61) — F2 with step 19 (M39).
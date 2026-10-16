# PACK_ISSUES - AHOS content pack (03_content) validator findings

Pack files under `src/mock/content`, `src/i18n`, `src/types/contract.ts`, `src/lib/{format,status}.ts` are unmodified copies.
`node scripts/validate.mjs` (pack's own script, run on an LF-normalised copy; the patch checkout had CRLF, which alone produced 23 extra encoding errors) reports **16 errors / 149 checks**. None were fixed here.

| # | Check | Finding | Cause |
|---|-------|---------|-------|
| 1 | 1 hygiene | `scripts/validate.mjs` contains mojibake marker strings | validator source contains the very patterns it scans for (self-trip) |
| 2 | 6 paper-only notice | "no real money" wording missing on fa/en pages markets, signals, agents, risk, operator | pack i18n content |
| 3-4 | 7 mock | agents.json: 29 problems (`nextRunAt` after generatedAt) + same as uniqueness check | pack data, or validator too strict for forward-looking fields |
| 5-6 | 7 mock | signals.json: 5 problems (`expiresAt` in the future) + uniqueness check | same |
| 7-8 | 7 mock | paper-positions.json: 15 problems (`timeStopAt` in the future) + uniqueness check | same |
| 9-10 | 7 mock | risk-state.json: breaker `cooldownEndsAt` in the future + uniqueness check | same |
| 11-12 | 7 mock | operator-session.json: 5 problems (task `expiresAt` in the future) + uniqueness check | same |
| 13 | 9 arithmetic | quotes: spread vs implied spread mismatch (BTC 23 vs 83.3, ETH 40 vs 67.3, SOL, BNB, XRP, ADA ...) | pack mock data |
| 14 | 9 arithmetic | signal `sig.demo.016`: stop on the wrong side of entry | pack mock data |
| 15 | 11 secrets | `scripts/validate.mjs` reads an environment variable | validator source (self-trip) |
| 16 | 12 network | `scripts/validate.mjs` contains fetch/XMLHttpRequest/got/WebSocket/EventSource/child_process | validator source (self-trip); also uses child_process legitimately |

Manifest sha256 check passes only on LF files. Arena treats every pack value as DEMO/UNKNOWN as shipped; it does not rely on the flagged fields.
# AHOS — Next.js Gateway & G2 Mission Report (A–J)

> **PARTIALLY SUPERSEDED — pre-soak entry verdict (2026-10-03).** Section G of
> this report concludes `pre_soak_entry_ok = TRUE` with "G1–G10 all PASS". The
> **standing** authority file `reports/PRE_SOAK_STATUS.txt` — re-read
> 2026-10-03 — holds `pre_soak_entry_ok = False` with **G2, G3, G10 =
> `NOT_VERIFIED`**. The two cannot both be true: this report's G2/G3/G10 passes
> were transitory (a live gateway on `127.0.0.1:3500`, a probe run), while the
> standing file records that those gates are not currently satisfied. The
> standing file governs; pre-soak entry remains **BLOCKED**. Everything else in
> this report (gateway probe receipts, control-surface gating evidence) stands.
> Current capability state: `reports/grok/REMAINING_REALITY_REGISTER.md` §10.

**Mission:** M-20261002-02 (Phase C directive)
**Window:** 2026-10-02T01:10:00Z → 2026-10-02T02:39:05Z
**Branch / HEAD:** `ahos` / `6cf3f5ab71c4e367c17ca3e1b0dbb24f83253799`
**Headline:** Canonical **G2 = PASS** against the live gateway on `127.0.0.1:3500`, and the
full canonical gate suite returns **G1–G10 all PASS ⇒ `pre_soak_entry_ok = true`**.

Every conclusion below is classified **PROVEN BY EVIDENCE** / **STRONGLY INDICATED** /
**POSSIBLE-NEEDS TEST** / **UNKNOWN**, with the artifact that carries it.

---

## A. DASHBOARD STATUS

**HTTP 200 — real HTML, not a process-existence check.**

| Property | Value |
|---|---|
| URL | `http://127.0.0.1:3500/` |
| HTTP status | 200 |
| Latency | 105.4 ms (warm); 1955 ms on the first cold compile |
| Content-Type | `text/html; charset=utf-8` |
| Body check | 4000-byte sample contains real HTML markup (`looks_like_html: true`) |

Artifact: `reports/g2_canonical_probe_20261002.json` → `dashboard`.

**PROVEN BY EVIDENCE:** the dashboard serves a real HTML document, not a bare listener.

---

## B. NEXT.JS STATUS

**READY — and readiness was verified by response, not by process existence.**

- Next.js 16.2.6 (Turbopack), `next dev --hostname 127.0.0.1 -p 3500`, ✓ Ready in 36.0 s.
- `node_modules` present; node v24.19.0, npm 11.17.0.
- Slow-filesystem warning for `G:\robat\ahos\.next/dev` (network-adjacent drive) — a
  performance notice, **not** a failure. **STRONGLY INDICATED** benign.
- All observed routes returned 200: `GET /` and every `POST /api/chat`.

**Note on the port premise:** the mission directive states Windows cannot bind port 3000 and
3500 must be used. Both directives were honoured (the gateway runs on 3500). However, on this
host **both 3000 and 3500 were measured FREE**, and the prior G2 failure was
`ConnectionRefused` (no listener running), not a bind error. Recorded as a factual
discrepancy with the stated premise; **POSSIBLE-NEEDS TEST** if the operator has evidence of a
specific bind failure on 3000 (e.g. a group-policy/Hyper-V port reservation) that a plain
free-port check would not catch.

---

## C. API CHAT STATUS

**HTTP 200 with a real Persian reply — and the Postgres-backed write path is proven working.**

| | Cold (first compile) | Warm |
|---|---|---|
| HTTP status | 200 | 200 |
| Latency | 286.8 ms | 260.0 ms |
| Raw body | 1999 bytes | 1999 bytes (identical) |
| `reply` length | 481 chars | 481 chars |
| Persian content | yes | yes |
| `intent` | `general` | `general` |
| `uncertainty` | `["UNKNOWN preserved where data missing"]` | same |

Reply content (live): regime RANGE, bitcoin ۷۹٫۷۳ هزار دلار (+۰٫۱۵٪), 0 canonical BUY /
0 REJECT, latest Persian news (Ethena ENA fee proposal), engine-off notice, and the final
user-decision line. `focusToken: null` — honest, not a fabricated token.

Artifacts: `reports/g2_raw_body_cold.json`, `reports/g2_raw_body_warm.json`,
`reports/g2_chat_response_20261002.json`.

**Postgres dependency confirmed and exercised.** `chat.ts:197-198` inserts the user and
assistant rows via the `@/db` pg pool, and `route.ts` retries transient Postgres errors once.
The request was served with `DATABASE_URL` set and `ahos_postgres_win` healthy, so the real
write path ran. **PROVEN BY EVIDENCE** by the 4-row live table plus the pg_dump from the
recovery mission (`reports/pgdump_ahos_chat_messages_20261002T002200Z.sql`).

### The cold-start `UnicodeEncodeError` — RESOLVED (not an API defect)

An earlier probe saw the first request return a body containing
`ERROR 2974.6ms UnicodeEncodeError 'charmap' codec can't encode characters in position 0-5`.
Investigation:

1. No code anywhere constructs an `ERROR {ms} {exception}` string. Checked `chat.ts`
   (catch blocks at 123/187/199/209 all return Persian fixed strings),
   `conversation_gateway.ts` (returns `answer`, no error formatting), and
   `app/api/chat/route.ts` (returns `خطای داخلی: …` with **status 500**, plus a
   `console.error` stack print).
2. The server access log showed every `POST /api/chat` as **200** with **no**
   `[api/chat] POST failed:` line and no stack — impossible if that body came from the route.
3. The message is exactly the shape of a Python `print()` of Persian text on a cp1252 Windows
   console.

A clean probe that persists raw response bytes to UTF-8 files and prints only ASCII returns
**identical healthy Persian replies cold and warm** (1999 B each).

**Classification: PROVEN BY EVIDENCE — the error string was an artifact of the probe's own
cp1252 console output, not a gateway defect. Cold-compile and warm behaviour are identical.**

---

## D. G2 STATUS

**PASS — measured by the canonical gate function, unmodified.**

```
G2 Gateway  PASS  http_200 from http://127.0.0.1:3500/api/chat
            database_url_set=true  web_api_token_set=true  attempt=1
```

`scripts/operator_validation_gate.py::g2_gateway(skip_network=False)` was called directly
rather than via `main()`. Reason: `main()` force-overwrites `AHOS_GATEWAY_URL` from `.env`,
which pins `http://127.0.0.1:3000/api/chat` (`.env:99`) — a dead port in this run. Calling the
gate function with the same env seeding `main()` uses leaves the gate source byte-identical and
changes only the probed URL to the live 3500 gateway. No `.env` edit, no source edit.

**Operational gap this exposes (recorded, not fixed):** the documented owner path
(`scripts/windows_run_operator_gate.ps1` → the CLI runner) would probe port 3000 and FAIL while
the gateway runs on 3500. Either the gateway must run on 3000 or `.env`'s `AHOS_GATEWAY_URL`
must be repointed. Both are operator config decisions; **not** made here. **STRONGLY
INDICATED** as the single remaining friction in reproducing this PASS via the stock CLI.

---

## E. POSTGRES STATUS

**HEALTHY — verified read-only; no writes, no migrations, no schema changes.**

| Check | Result |
|---|---|
| Container | `ahos_postgres_win` — Up, **healthy**, `127.0.0.1:5432->5432/tcp` |
| `pg_isready` | `/var/run/postgresql:5432 - accepting connections` |
| Server version | 16.15 |
| Public tables | 156 |
| `ahos_chat_messages` rows | 4 (2 user / 2 assistant) |
| Schema owner | Drizzle migrations (`database/postgresql_schema.sql` defines only 8 unrelated tables — it is **not** the live schema) |

STATE B honoured throughout: no `db:migrate`, no `db:push`, no writes.

---

## F. RUNTIME CONTAINER STATUS

| Container | Status | Note |
|---|---|---|
| `ahos_postgres_win` | Up (healthy) | Real dependency for the chat path; healthy |
| `ahos_runtime_win` | Up (**unhealthy**) | Healthcheck artifact, **not** data loss |
| `ahos_n8n_win` | Up | Not a real AHOS runtime dependency (proven in the forensic mission) |

**`ahos_runtime_win` unhealthy — identified dependency, not fixed (per directive step 10).**
The container's Docker healthcheck runs `PRAGMA integrity_check`, which takes ~20.3 s against
the 5 s healthcheck timeout. The committed compose disables that check; the running container
predates the committed compose. **STRONGLY INDICATED** by the prior forensic probe returning
healthy in 20.3 s. The real dependency for the chat path is Postgres, not this container's
health state.

---

## G. PRE_SOAK_ENTRY STATUS

**`pre_soak_entry_ok = TRUE`** — the hard entry condition in `docs/PRE_SOAK_PROTOCOL.md` is met.

Full canonical G1–G12 suite (`reports/operator_validation_report_windows_20261002.json`):

| Gate | Name | Status |
|---|---|---|
| G1 | Environment | **PASS** (py 3.11.9, node v24.19.0, npm 11.17.0) |
| G2 | Gateway | **PASS** (http_200 on 3500) |
| G3 | Discovery providers | **PASS** (dexscreener + geckoterminal, 2 tokens each, live) |
| G4 | Evidence persistence | **PASS** (111 096 discovery / 33 333 production observations) |
| G5 | Scoring / predictions | **PASS** (27 485 local predictions) |
| G6 | Security / PAPER_ONLY | **PASS** (paper_only_enforced, zero_real_trading) |
| G7 | Lane-A freeze | **PASS** (pinned, no drift) |
| G8 | Prediction lifecycle registration | **PASS** (22 240 active) |
| G9 | Observation lifecycle | **PASS** (508 outcome labels) |
| G10 | Restart/recovery | **PASS** (backup drill 5/5) |
| G11 | Telegram live E2E | **NOT_VERIFIED** — OWNER_ACTION (see H) |
| G12 | n8n | **STRUCTURAL_VALID** (allowed for entry; operational not required) |

`summary.missing = ["G11:NOT_VERIFIED"]`; `classification = INTEGRATION_READY`;
`operator_ready = false` with reason *"Windows G1–G10 PASS — pre-soak entry OK; G11 still
required for OPERATOR_READY"* — which is exactly what the protocol permits for a short pre-soak.

**Consequence:** pre-soak step 1 has been executed (mission M-20261002-03): one bounded
opportunity cycle, T0 registered at **2026-10-02T02:54:19Z**, lifecycle deltas verified against
the cycle's own counts, Lane-A freeze and PAPER_ONLY re-verified clean afterwards.

---

## H. EXACT BLOCKER

**For OPERATOR_READY (not for pre-soak): G11 Telegram live E2E — OWNER_ACTION_REQUIRED.**

- The runner never auto-PASSes G11; the owner must run a live Telegram session and archive
  `reports/telegram_e2e_<UTC>.md`, then re-run the gate with `--telegram-e2e-artifact`.
- A `TELEGRAM_BOT_TOKEN` **is** present, but driving a live Telegram conversation is an
  outward-facing action on the operator's account and is explicitly designated an owner step.
  **Recorded as `OWNER_ACTION_REQUIRED`, not executed.**

**No blocker remains for pre-soak.** Residual frictions (not blockers):

1. `.env:99` pins `AHOS_GATEWAY_URL` to port 3000, so the stock CLI gate runner cannot
   reproduce this G2 PASS while the gateway runs on 3500. Operator config decision.
2. `ahos_runtime_win` shows unhealthy from a 20.3 s-vs-5 s healthcheck timeout (artifact).
3. Soak-duration gaps are wall-clock bound: M-GAP-003 (≥7 days), M-GAP-010 (7 *distinct*
   nights; night 1/7 now recorded), M-GAP-008 (calibration needs real T+72h labels —
   `outcome_labels` deliberately unchanged).

---

## I. FILES CHANGED

No source code, no `.env`, no governance documents, no Lane-A files, no Postgres schema.

Created (evidence only):
- `reports/g2_chat_response_20261002.json`
- `reports/g2_raw_body_cold.json`, `reports/g2_raw_body_warm.json`
- `reports/g2_canonical_probe_20261002.json`
- `reports/operator_validation_report_windows_20261002.json`
- `reports/LATEST_WINDOWS_GATE.txt`
- `reports/provider_probe_opval_20261002T023855Z.json` (written by canonical G3)
- `reports/presoak_t0_20261002.json`, `reports/presoak_cycle1_20261002.json`
- `reports/nightly_backup_series.json` (canonical nightly backup series ledger)
- `reports/mission_ledger_20261002.json`
- `next-env.d.ts` — **untracked, auto-generated by the Next.js dev server** (not a source edit)
- `data/backups/20261002T*/<store>.sqlite` — verified nightly backups (read-only w.r.t. sources)
- `reports/backup_restore_drill.json` — overwritten by the canonical G10 drill (scratch stores only)

Working-tree modifications pre-dating this mission and not touched here:
`.cursor/hooks.json`, `reports/backup_restore_drill.json`,
`reports/month1_failure_matrix.json`, `reports/reliability_matrix.json`,
plus `.cursor/hooks.json.local-backup`, `ahos-hooks-local-diff.txt`.

**No commits made.**

---

## J. NEXT SAFE HIGH-VALUE MISSION

**Already selected and running** (12-hour continuous-execution addendum):

1. **M-20261002-05 — fresh full-suite pytest evidence** via the canonical
   `scripts/record_test_run.py` recorder (in progress at report time). Priority tier 4
   (tests and verification).
2. **Evidence synchronization** (tier 5): the canonical G3 run produced a *Windows-laptop*
   live provider SUCCESS artifact (`reports/provider_probe_opval_20261002T023855Z.json`,
   dexscreener + geckoterminal, tokens > 0) — the exact "operator Windows laptop re-probe"
   that M-GAP-007 lists as USER ACTION. Record it in a session evidence file; the gap
   register itself is **not** edited (governance-document prohibition).
3. **Continue nightly backups on subsequent distinct UTC days** to advance M-GAP-010 toward
   7/7 (cannot be produced in one sitting by design).

Deferred to the owner (governance / outward-facing):
- G11 live Telegram E2E transcript archive → unlocks OPERATOR_READY.
- The `.env` `AHOS_GATEWAY_URL` 3000-vs-3500 decision.
- Any long daemon soak (sustained resource commitment on a 7.93 GB-RAM host).

**Stop conditions re-checked:** no permitted useful mission is exhausted; the only Human
Approval needed (G11) has an independent alternative for pre-soak (protocol allows it); the
environment is live; no fundamental blocker; safety/governance satisfied.

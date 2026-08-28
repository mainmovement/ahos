# AHOS Windows live Postgres classification (from owner REPORT 2026-08-28)

Source report: `reports/windows_post_merge_reconcile_20260828_231950.json` (owner paste)

## Git / laptop

| Item | Evidence |
|---|---|
| Branch | `main` |
| HEAD | `e2292fdea1844625f760ea3b88a069ca9635812d` (= `origin/main`) |
| Ahead/behind | `0 / 0` |
| Containers | `ahos_runtime_win` healthy, `ahos_n8n_win` up, `ahos_postgres_win` healthy |

## Live Postgres identity

- database: `ahos`
- user: `ahos_user`
- version: PostgreSQL **16.15** (Alpine)

## Tables

- **19** `public.ahos_*` tables (exact names match canonical `schema.ts` / `drizzle/0000_ahos_canonical_tables.sql` set)
- `public.__drizzle_migrations`: **ABSENT** (`drizzle_migrations_exists = f`)
- Origin of tables: **ORIGIN_UNKNOWN** (not explained by migrate journal; docker init SQL creates 0 `ahos_*`)

## Exact row counts (evidence-bearing)

| Table | Rows |
|---|---:|
| ahos_chat_messages | 0 |
| ahos_council_reports | 32 |
| ahos_cycles | 1 |
| ahos_expert_votes | 352 |
| ahos_findings | 2 |
| ahos_lessons | 0 |
| ahos_market_snapshots | 1 |
| ahos_news_items | 56 |
| ahos_observations | 32 |
| ahos_opportunities | 32 |
| ahos_outcomes | 0 |
| ahos_paper_positions | 1 |
| ahos_predictions | 29 |
| ahos_provider_snapshots | 66 |
| ahos_security_reports | 10 |
| ahos_system_state | 1 |
| ahos_tokens | 32 |
| ahos_translation_cache | 56 |
| ahos_watchlist | 1 |

**Total non-zero evidence rows across tables: >600.** Data exists. Recreate/replace/reset is forbidden.

## Classification

### STATE B

Tables exist; migration history is missing/inconsistent (`__drizzle_migrations` absent) while live `ahos_*` inventory is populated.

Not STATE A (no migration journal + no live DDL equality proof in this report).  
Not empty.

## Migration decision

**MIGRATION BLOCKED**

Do **not** run:

- `npm run db:migrate`
- `npm run db:push`
- `drizzle-kit migrate` / `push`

Reason: additive `CREATE TABLE` migration against existing 19 tables would error or create ambiguity; data-bearing tables must be preserved; history gap means migrate cannot be assumed safe.

## Next safe engineering action

1. Keep using the live DB read-only for app/dev.
2. Optionally capture live DDL (`pg_dump --schema-only`) for offline diff vs `drizzle/0000_ahos_canonical_tables.sql` — still no migrate.
3. Only after explicit owner authorization + DDL reconciliation plan may a **non-destructive** history baseline be considered (separate design; not this wave).

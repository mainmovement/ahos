#!/usr/bin/env node
/**
 * AHOS Postgres probe for One-Brain /api/chat (STATE B — no migrate).
 *
 * Loads .env DATABASE_URL, runs the same first queries commandSnapshot needs,
 * prints a single JSON line with ok/error (password redacted).
 *
 * Usage:
 *   node scripts/ahos_pg_probe.mjs
 *   node scripts/ahos_pg_probe.mjs --json-out reports/pg_probe_latest.json
 */
import { config } from "dotenv";
import { writeFileSync, mkdirSync, existsSync } from "node:fs";
import { dirname, resolve, join } from "node:path";
import { fileURLToPath } from "node:url";
import pg from "pg";
import { isPgliteBackend, pgliteDataDir } from "../db/pglite_url.mjs";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
config({ path: resolve(root, ".env") });

function redact(url) {
  if (!url || typeof url !== "string") return "";
  return url.replace(/:([^:@/]+)@/, ":***@");
}

function classify(message) {
  const m = String(message || "");
  if (/ECONNREFUSED|ENOTFOUND|connect\s+ECONNREFUSED/i.test(m)) return "CONN_REFUSED";
  if (/password authentication failed/i.test(m)) return "AUTH_FAILED";
  if (/database \".*\" does not exist/i.test(m)) return "DB_MISSING";
  if (/relation \".*\" does not exist/i.test(m)) return "RELATION_MISSING";
  if (/DIRECTORY_NOT_FOUND|does not exist|not initialized|Failed to open/i.test(m))
    return "STORE_MISSING";
  if (/DATABASE_URL is required|timeout/i.test(m)) return "CONFIG_OR_TIMEOUT";
  return "QUERY_OR_OTHER";
}

const outArg = process.argv.indexOf("--json-out");
const outPath =
  outArg >= 0 && process.argv[outArg + 1]
    ? resolve(process.argv[outArg + 1])
    : null;

const databaseUrl = (process.env.DATABASE_URL || "").trim();
const report = {
  schema: "ahos.pg_probe.v1",
  ok: false,
  backend: null,
  database_url_set: Boolean(databaseUrl),
  database_url_redacted: redact(databaseUrl),
  error_class: null,
  error: null,
  system_state_rows: null,
  ahos_table_count: null,
  probe_via: null,
  note: "STATE B: no db:migrate / db:push",
};

// The snapshot queries both backends must serve. Identical SQL is the point:
// PGlite IS PostgreSQL 16, so the probe proves the gateway's real read path
// rather than a backend-specific approximation of it.
const SNAPSHOT_QUERIES = [
  "SELECT 1 FROM ahos_cycles LIMIT 1",
  "SELECT 1 FROM ahos_market_snapshots LIMIT 1",
  "SELECT 1 FROM ahos_opportunities LIMIT 1",
];

async function probePostgres(url) {
  const client = new pg.Client({ connectionString: url, connectionTimeoutMillis: 8000 });
  try {
    await client.connect();
    const state = await client.query("SELECT COUNT(*)::int AS n FROM ahos_system_state");
    report.system_state_rows = state.rows[0]?.n ?? 0;
    const tables = await client.query(
      "SELECT COUNT(*)::int AS n FROM information_schema.tables WHERE table_schema='public' AND table_name LIKE 'ahos_%'",
    );
    report.ahos_table_count = tables.rows[0]?.n ?? 0;
    for (const q of SNAPSHOT_QUERIES) await client.query(q);
    report.ok = true;
  } finally {
    try {
      await client.end();
    } catch {
      /* ignore */
    }
  }
}

async function probePglite(url) {
  // Mirror the launcher's permanent readiness gate (scripts/pglite_restore.ts
  // --check): no PG_VERSION means the store was never initialised, and opening
  // PGlite would create an empty directory — a fabricated "store". Fail first.
  const dataDir = pgliteDataDir(url);
  report.probe_via = "pglite_embedded";
  if (!existsSync(join(dataDir, "PG_VERSION"))) {
    throw new Error(
      `DIRECTORY_NOT_FOUND: PG_VERSION missing under ${dataDir} (store not initialised; ` +
        `run the launcher once, or: npm run db:restore-pglite -- --dataDir ${dataDir})`,
    );
  }
  // Lazy import: the WASM module must never load on the Postgres path, exactly
  // as db/index.ts keeps it lazy.
  const { PGlite } = await import("@electric-sql/pglite");
  const db = new PGlite(dataDir);
  try {
    const state = await db.query("SELECT COUNT(*)::int AS n FROM ahos_system_state");
    report.system_state_rows = state.rows[0]?.n ?? 0;
    const tables = await db.query(
      "SELECT COUNT(*)::int AS n FROM information_schema.tables WHERE table_schema='public' AND table_name LIKE 'ahos_%'",
    );
    report.ahos_table_count = tables.rows[0]?.n ?? 0;
    for (const q of SNAPSHOT_QUERIES) await db.query(q);
    report.ok = true;
  } finally {
    try {
      await db.close();
    } catch {
      /* ignore */
    }
  }
}

async function main() {
  if (!databaseUrl) {
    report.error_class = "CONFIG_OR_TIMEOUT";
    report.error = "DATABASE_URL unset in process env / .env";
    return report;
  }

  try {
    if (isPgliteBackend(databaseUrl)) {
      report.backend = "pglite";
      report.note = "native embedded PGlite (M10): no db:migrate / db:push";
      await probePglite(databaseUrl);
    } else {
      report.backend = "postgres";
      await probePostgres(databaseUrl);
    }
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    report.error = message.replace(/:([^:@/]+)@/g, ":***@");
    report.error_class = classify(message);
  }
  return report;
}

const result = await main();
const line = JSON.stringify(result, null, 2);
if (outPath) {
  mkdirSync(dirname(outPath), { recursive: true });
  writeFileSync(outPath, line + "\n", "utf8");
}
console.log(line);
process.exit(result.ok ? 0 : 2);

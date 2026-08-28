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
import { writeFileSync, mkdirSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import pg from "pg";

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
  database_url_set: Boolean(databaseUrl),
  database_url_redacted: redact(databaseUrl),
  error_class: null,
  error: null,
  system_state_rows: null,
  ahos_table_count: null,
  note: "STATE B: no db:migrate / db:push",
};

async function main() {
  if (!databaseUrl) {
    report.error_class = "CONFIG_OR_TIMEOUT";
    report.error = "DATABASE_URL unset in process env / .env";
    return report;
  }

  const client = new pg.Client({
    connectionString: databaseUrl,
    connectionTimeoutMillis: 8000,
  });
  try {
    await client.connect();
    const state = await client.query(
      "SELECT COUNT(*)::int AS n FROM ahos_system_state",
    );
    report.system_state_rows = state.rows[0]?.n ?? 0;
    const tables = await client.query(
      "SELECT COUNT(*)::int AS n FROM information_schema.tables WHERE table_schema='public' AND table_name LIKE 'ahos_%'",
    );
    report.ahos_table_count = tables.rows[0]?.n ?? 0;
    // Touch the same tables commandSnapshot reads first (existence only).
    await client.query("SELECT 1 FROM ahos_cycles LIMIT 1");
    await client.query("SELECT 1 FROM ahos_market_snapshots LIMIT 1");
    await client.query("SELECT 1 FROM ahos_opportunities LIMIT 1");
    report.ok = true;
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    report.error = message.replace(/:([^:@/]+)@/g, ":***@");
    report.error_class = classify(message);
  } finally {
    try {
      await client.end();
    } catch {
      /* ignore */
    }
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

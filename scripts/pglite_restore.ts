/**
 * Mission 10 (Docker removal) — native embedded Postgres restore + parity tool.
 *
 * Applies the canonical Drizzle migration to a PGlite dataDir, restores the
 * `ahos_*` rows from a `pg_dump --no-owner --no-privileges` plain-format file,
 * and verifies exact row-count parity against a recorded baseline.
 *
 * PAPER_ONLY. Read-only against the dump and counts files. Never deletes the
 * source dump. Everything it writes goes into --dataDir.
 *
 * Usage:
 *   node --experimental-strip-types scripts/pglite_restore.ts \
 *      --dataDir G:/robat/ahos_runtime/pglite/ahos \
 *      --dump   G:/robat/ahos_backups/pg_20261003T091351Z/ahos_full.sql \
 *      --counts G:/robat/ahos_backups/pg_20261003T091351Z/row_counts.txt
 *
 *   --dataDir (required) target PGlite directory (created if absent)
 *   --dump    (optional) pg_dump plain file to restore
 *   --counts  (optional) "<table>|<count>" baseline to verify against
 *   --reset   (optional) drop and recreate the ahos_* schema before restore
 *
 * Exit codes: 0 = success including full parity, 1 = any failure or parity gap.
 * Exit code is deliberate so the launcher can treat restore as a real gate.
 */
import { mkdirSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import process from "node:process";
import {
  applyMigration,
  insertBlocks,
  parseCopyBlocks,
  resetSchema,
  verifyParity,
} from "./pglite_restore_lib.ts";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");

const args = process.argv.slice(2);
const flag = (name: string) => {
  const i = args.indexOf(name);
  return i >= 0 ? args[i + 1] : undefined;
};

const dataDir = flag("--dataDir");
const dumpPath = flag("--dump");
const countsPath = flag("--counts");
const doReset = args.includes("--reset");

if (!dataDir) {
  console.error("missing --dataDir");
  process.exit(2);
}

const { PGlite } = await import("@electric-sql/pglite");

mkdirSync(dataDir, { recursive: true });
const db = new PGlite(dataDir);

const MIGRATION = join(ROOT, "drizzle", "0000_ahos_canonical_tables.sql");

try {
  if (doReset) {
    const dropped = await resetSchema(db);
    if (dropped) console.log(`reset: dropped ${dropped} ahos_* tables`);
  }

  const applied = await applyMigration(db, readFileSync(MIGRATION, "utf8"));
  console.log(`migration: applied ${applied} statements`);

  if (dumpPath) {
    const blocks = parseCopyBlocks(readFileSync(dumpPath, "utf8"));
    const { total, perTable } = await insertBlocks(db, blocks);
    console.log(
      `restore: copied ${total} rows across ${Object.keys(perTable).length} tables`,
    );
  } else {
    console.log("restore: no --dump given, schema only");
  }

  if (countsPath) {
    const results = await verifyParity(db, readFileSync(countsPath, "utf8"));
    const ok = results.filter((r) => r.ok);
    const bad = results.filter((r) => !r.ok);
    for (const r of bad) {
      console.log(`PARITY FAIL ${r.table}: want=${r.expected} got=${r.got}`);
    }
    console.log(`PARITY: ${ok.length} OK / ${bad.length} FAIL of ${results.length}`);
    if (bad.length) {
      console.error("parity gap — refusing to report success");
      process.exitCode = 1;
    }
  }

  // Round-trip spot checks on the two Postgres types the gateway leans on most.
  const jb = (
    await db.query(
      "SELECT evidence FROM ahos_chat_messages WHERE evidence IS NOT NULL LIMIT 1",
    )
  ).rows as { evidence: unknown }[];
  console.log(
    "jsonb spot check:",
    jb.length ? JSON.stringify(jb[0].evidence).slice(0, 90) : "(no jsonb rows)",
  );
  const ts = (
    await db.query("SELECT created_at FROM ahos_chat_messages ORDER BY id LIMIT 1")
  ).rows as { created_at: unknown }[];
  console.log(
    "timestamptz spot check:",
    ts.length ? ts[0].created_at : "(none)",
  );
} finally {
  await db.close();
}

/**
 * Mission 10 (Docker removal) — embedded PGlite backend self-test.
 * Run: npm run test:pglite-backend
 * Self-test, not independent verification.
 *
 * Proves, inside the repo with no Docker and no network:
 *   1. DATABASE_URL scheme selects the backend and yields the right dataDir.
 *   2. The lazy `db` client works end-to-end over embedded Postgres through
 *      the real drizzle layer (serial, jsonb, timestamptz round-trip).
 *   3. The pg_dump restore parser handles COPY blocks, ignores non-ahos
 *      blocks, maps `\N` to NULL, and reaches exact row-count parity.
 *   4. `pool` (legacy node-postgres) refuses to masquerade on the pglite path.
 */
import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { mkdtempSync, readFileSync, rmSync } from "node:fs";
import { describe, it } from "node:test";
import os from "node:os";
import path from "node:path";
import process from "node:process";
import {
  applyMigration,
  insertBlocks,
  parseCopyBlocks,
  verifyParity,
} from "./pglite_restore_lib.ts";
import { db, isPgliteBackend, pgliteDataDir, pool } from "@/db";

// drizzle-orm is CommonJS; its named exports are not visible to a stripped-TS
// ESM import, and the pg column builders live in the pg-core subpath.
const { integer, jsonb, pgTable, serial, timestamp } = createRequire(import.meta.url)(
  "drizzle-orm/pg-core",
);

/** Throwaway table with the Postgres types the gateway leans on most. */
const rt = pgTable("selftest_rt", {
  id: serial("id").primaryKey(),
  meta: jsonb("meta").notNull(),
  at: timestamp("at", { withTimezone: true }).notNull(),
  atNaive: timestamp("at_naive").notNull(),
  qty: integer("qty"),
});

const AT = "2026-10-03T09:13:51.000Z";

describe("DATABASE_URL backend selection", () => {
  it("treats a postgresql:// URL as the legacy Pool backend", () => {
    const u = "postgresql://ahos_user:***@127.0.0.1:5432/ahos";
    assert.equal(isPgliteBackend(u), false);
  });
  it("treats a pglite: URL as the embedded backend", () => {
    assert.equal(isPgliteBackend("pglite:G:/robat/ahos_runtime/pglite/ahos"), true);
  });
  it("extracts a Windows absolute dataDir", () => {
    assert.equal(
      pgliteDataDir("pglite:G:/robat/ahos_runtime/pglite/ahos"),
      "G:/robat/ahos_runtime/pglite/ahos",
    );
  });
  it("tolerates a leading slash in the dataDir", () => {
    assert.equal(pgliteDataDir("pglite:/G:/somewhere/db"), "G:/somewhere/db");
  });
  it("handles a relative dataDir", () => {
    assert.equal(pgliteDataDir("pglite:data/pglite"), "data/pglite");
  });
});

describe("embedded client round-trip", () => {
  let dir: string | undefined;

  it("boots Postgres, round-trips types through drizzle", async () => {
    dir = mkdtempSync(path.join(os.tmpdir(), "ahos-pglite-rt-"));
    process.env.DATABASE_URL = `pglite:${dir}`;
    // Rebind the lazily-cached singletons to the new URL.
    const g = globalThis as Record<string, unknown>;
    g.__ahosDb = undefined;
    g.__ahosPgliteClient = undefined;

    const client = db.$client;
    await client.query(
      "CREATE TABLE selftest_rt (id serial PRIMARY KEY, meta jsonb NOT NULL, " +
        "at timestamptz NOT NULL, at_naive timestamp NOT NULL, qty integer);",
    );

    const meta = { intent: "paper_check", focusToken: "SOL", nested: { ok: true } };
    await client.query(
      "INSERT INTO selftest_rt (meta, at, at_naive, qty) VALUES ($1, $2, $3, $4);",
      [JSON.stringify(meta), AT, "2026-10-03 09:13:51", 7],
    );

    const raw = (await client.query("SELECT id, meta, at, at_naive, qty FROM selftest_rt;"))
      .rows[0];
    assert.equal(raw.id, 1, "serial PK should start at 1");
    assert.deepEqual(raw.meta, meta, "jsonb must round-trip as a parsed object");
    // timestamptz comes back as a UTC-preserving Date; plain timestamp is
    // session-local, so only its wall-clock time part is stable to assert on.
    assert.equal(raw.at instanceof Date, true, "timestamptz returns a Date");
    assert.equal(raw.at.toISOString(), AT, "timestamptz must be UTC-exact");
    assert.equal(raw.at_naive instanceof Date, true, "timestamp returns a Date");
    assert.equal(
      String(raw.at_naive).includes("09:13:51"),
      true,
      "naive timestamp keeps its wall-clock time",
    );
    assert.equal(raw.qty, 7);
  });

  it("works through the drizzle query builder, not just raw SQL", async () => {
    const rows = await db
      .select({ id: rt.id, qty: rt.qty })
      .from(rt)
      .orderBy(rt.id);
    assert.equal(rows.length, 1);
    assert.equal(rows[0].id, 1);
    assert.equal(rows[0].qty, 7);
  });

  it("refuses to serve the legacy Pool on the embedded path", () => {
    assert.throws(() => pool.end(), /legacy node-postgres Pool/);
  });

  it("cleans up", () => {
    if (dir) rmSync(dir, { recursive: true, force: true });
  });
});

describe("pg_dump restore parser", () => {
  // Columns and NOT NULL constraints match the real migration:
  // ahos_system_state has NOT NULL on running/last_cycle_status/cycle_count/
  // interval_sec/execution_mode/updated_at, so the NULL marker can only land
  // in a nullable column (last_error) — exactly as in the real backup.
  const dump = [
    "CREATE SCHEMA drizzle;",
    "",
    "COPY public.ahos_system_state (id, running, last_cycle_status, cycle_count, last_error, execution_mode, updated_at) FROM stdin;",
    "1\tt\tOK\t3\t\\N\tPAPER_ONLY\t2026-08-30T10:09:09.821Z",
    "2\tf\tUNKNOWN\t0\tstopped by operator\tPAPER_ONLY\t2026-08-30T10:10:00.000Z",
    "\\.",
    "",
    "COPY public.\"user\" (id, email) FROM stdin;",
    "1\tdrop-me@example.com",
    "\\.",
    "",
    "COPY public.ahos_findings (id, finding_id, severity, title_fa, evidence_fa, confidence) FROM stdin;",
    "1\tF-001\tLOW\ttab\\there\tproof with \\\\ backslash\t0.71",
    "\\.",
  ].join("\n");

  it("collects only ahos_* COPY blocks and keeps their order", () => {
    const blocks = parseCopyBlocks(dump);
    assert.deepEqual(
      blocks.map((b) => b.table),
      ["ahos_system_state", "ahos_findings"],
      "non-ahos blocks (public.user) must be ignored",
    );
  });

  it("parses columns without quotes and maps the NULL marker", () => {
    const [state] = parseCopyBlocks(dump);
    assert.deepEqual(state.columns, [
      "id",
      "running",
      "last_cycle_status",
      "cycle_count",
      "last_error",
      "execution_mode",
      "updated_at",
    ]);
    assert.equal(state.rows[0][4], null, "\\N must become null");
    assert.equal(state.rows[1][4], "stopped by operator");
  });

  it("unescapes \\t and \\\\ back to real characters", () => {
    const [, findings] = parseCopyBlocks(dump);
    assert.equal(findings.rows.length, 1);
    // `tab\there` in the dump is a tab *inside* the value, not a separator.
    assert.equal(findings.rows[0][3], "tab\there");
    // `proof with \\ backslash` — one literal backslash.
    assert.equal(findings.rows[0][4], "proof with \\ backslash");
  });

  it("treats an empty block as zero rows", () => {
    const empty = [
      "COPY public.ahos_lessons (id, body) FROM stdin;",
      "\\.",
    ].join("\n");
    assert.equal(parseCopyBlocks(empty)[0].rows.length, 0);
  });

  it("restores into embedded Postgres and reaches exact parity", async () => {
    const dir = mkdtempSync(path.join(os.tmpdir(), "ahos-pglite-restore-"));
    process.env.DATABASE_URL = `pglite:${dir}`;
    const g = globalThis as Record<string, unknown>;
    g.__ahosDb = undefined;
    g.__ahosPgliteClient = undefined;
    try {
      const client = db.$client;
      const applied = await applyMigration(
        client,
        readFileSync(
          path.join(import.meta.dirname, "..", "drizzle", "0000_ahos_canonical_tables.sql"),
          "utf8",
        ),
      );
      assert.ok(applied > 10, `migration should apply many statements, got ${applied}`);

      const { total, perTable } = await insertBlocks(client, parseCopyBlocks(dump));
      assert.equal(total, 3, "2 system_state rows + 1 finding carry data");
      assert.deepEqual(perTable, { ahos_system_state: 2, ahos_findings: 1 });

      const counts = [
        "ahos_system_state|2",
        "ahos_findings|1",
        "ahos_lessons|0",
        "drizzle.some_other|99", // non-ahos baseline lines must be ignored
      ].join("\n");
      const results = await verifyParity(client, counts);
      assert.equal(results.length, 3, "only ahos_* baselines are checked");
      assert.equal(results.every((r) => r.ok), true);

      // Restored values land typed and with escaping resolved.
      const state = (
        await client.query("SELECT updated_at, last_error FROM ahos_system_state WHERE id = 1;")
      ).rows[0];
      assert.equal(
        state.updated_at instanceof Date &&
          state.updated_at.toISOString().startsWith("2026-08-30T10:09:09"),
        true,
        "timestamptz restored as a UTC-exact Date",
      );
      assert.equal(state.last_error, null, "\\N restored as SQL NULL, not an empty string");
      const finding = (
        await client.query("SELECT title_fa FROM ahos_findings WHERE id = 1;")
      ).rows[0];
      assert.equal(finding.title_fa, "tab\there", "escaped tab restored as a real tab");
    } finally {
      rmSync(dir, { recursive: true, force: true });
    }
  });
});

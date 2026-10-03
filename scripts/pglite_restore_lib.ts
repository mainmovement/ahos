/**
 * Mission 10 (Docker removal) — restore/parity library, imported by
 * scripts/pglite_restore.ts (the operator CLI) and by the self-test.
 * Kept side-effect free: importing this module runs no CLI, touches no data.
 */

/** Structural client type: enough to run SQL, loose enough for any backend. */
export interface SqlClient {
  query(sql: string, params?: unknown[]): Promise<{ rows: unknown[] }>;
}

/** One parsed `COPY ... FROM stdin;` block: table name, columns, raw row values. */
export interface CopyBlock {
  table: string;
  columns: string[];
  rows: (string | null)[][];
}

/** A row-count comparison result against the recorded baseline. */
export interface ParityResult {
  table: string;
  expected: number;
  got: number;
  ok: boolean;
}

/** Match `COPY public.<table> (cols...) FROM stdin;` from a pg_dump plain dump. */
const COPY_HEADER = /^COPY public\.(ahos_\w+) \(([^)]*)\) FROM stdin;$/;

/**
 * Unescape one pg_dump COPY field. Postgres escapes special characters with a
 * leading backslash and marks NULL as a lone `\N`. Only `\N` appears in the
 * current backup (verified: zero other escapes across all 1,897 data rows),
 * but handling the full set keeps the tool correct for any future dump.
 */
export function unescapeCopyValue(value: string): string | null {
  if (value === "\\N") return null;
  let out = "";
  for (let i = 0; i < value.length; i++) {
    if (value[i] === "\\" && i + 1 < value.length) {
      const next = value[i + 1];
      switch (next) {
        case "b": out += "\b"; break;
        case "f": out += "\f"; break;
        case "n": out += "\n"; break;
        case "r": out += "\r"; break;
        case "t": out += "\t"; break;
        case "v": out += "\v"; break;
        case "\\": out += "\\"; break;
        default: out += next; // unknown escape: keep the character
      }
      i++;
    } else {
      out += value[i];
    }
  }
  return out;
}

/**
 * Apply the canonical Drizzle migration. Statements are separated by the
 * drizzle-kit `--> statement-breakpoint` marker, exactly as drizzle-kit emits.
 */
export async function applyMigration(client: SqlClient, migrationSql: string): Promise<number> {
  const stmts = migrationSql
    .split("--> statement-breakpoint")
    .map((s) => s.trim())
    .filter(Boolean);
  for (const s of stmts) {
    await client.query(s);
  }
  return stmts.length;
}

/**
 * Parse `COPY public.<table> (cols...) FROM stdin;` / `\.` blocks out of a
 * pg_dump plain dump. `\N` is Postgres's NULL marker. Values are returned as
 * raw strings — they are bound as parameters, so quoting is never hand-rolled.
 */
export function parseCopyBlocks(dumpText: string): CopyBlock[] {
  const lines = dumpText.split("\n");
  const blocks = [];
  let i = 0;
  while (i < lines.length) {
    const m = lines[i].match(COPY_HEADER);
    if (!m) {
      i++;
      continue;
    }
    const table = m[1];
    const columns = m[2].split(", ").map((c) => c.replace(/"/g, ""));
    const rows = [];
    i++;
    while (i < lines.length && lines[i] !== "\\.") {
      rows.push(lines[i].split("\t").map(unescapeCopyValue));
      i++;
    }
    blocks.push({ table, columns, rows });
    i++; // consume the `\.` terminator
  }
  return blocks;
}

/** Insert parsed rows in bounded batches via parameterized multi-row INSERT. */
export async function insertBlocks(client: SqlClient, blocks: CopyBlock[], batchSize = 200): Promise<{ total: number; perTable: Record<string, number> }> {
  let total = 0;
  const perTable: Record<string, number> = {};
  for (const { table, columns, rows } of blocks) {
    for (let start = 0; start < rows.length; start += batchSize) {
      const batch = rows.slice(start, start + batchSize);
      const ncol = columns.length;
      const valuesSql = batch
        .map(
          (_, r) =>
            "(" +
            columns.map((_, c) => "$" + (r * ncol + c + 1)).join(",") +
            ")",
        )
        .join(",");
      const sql = `INSERT INTO "${table}" (${columns.join(
        ",",
      )}) VALUES ${valuesSql};`;
      await client.query(sql, batch.flat());
    }
    perTable[table] = rows.length;
    total += rows.length;
  }
  return { total, perTable };
}

/** Verify row counts against a "<table>|<count>" baseline. */
export async function verifyParity(client: SqlClient, countsText: string): Promise<ParityResult[]> {
  const want: Record<string, number> = {};
  for (const line of countsText.split("\n")) {
    const [t, c] = line.split("|");
    if (t && t.startsWith("ahos_")) want[t] = parseInt(c || "0", 10);
  }
  const results = [];
  for (const [table, expected] of Object.entries(want).sort()) {
    const rows = (
      await client.query(`SELECT count(*)::int AS c FROM "${table}"`)
    ).rows as { c: number }[];
    const got = rows[0].c;
    results.push({ table, expected, got, ok: got === expected });
  }
  return results;
}

/**
 * Drop the ahos_* tables so a restore starts clean. CASCADE takes dependent
 * indexes/constraints with their tables. Returns the number of tables dropped.
 */
export async function resetSchema(client: SqlClient): Promise<number> {
  const tables = (
    await client.query(`
      SELECT tablename FROM pg_tables
      WHERE schemaname = 'public' AND tablename LIKE 'ahos\_%'
    `)
  ).rows as { tablename: string }[];
  const tableNames = tables.map((r) => r.tablename);
  if (!tableNames.length) return 0;
  await client.query(`DROP TABLE ${tableNames.map((t) => `"${t}"`).join(", ")} CASCADE;`);
  return tableNames.length;
}

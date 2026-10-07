import { createRequire } from "node:module";
import { drizzle } from "drizzle-orm/node-postgres";
import { Pool } from "pg";
import * as schema from "./schema";
// The canonical pglite URL parser lives in a plain .mjs so node scripts (the
// readiness probe) and this module read the exact same code. Two copies would
// let a green probe describe a store the gateway never opens.
export { isPgliteBackend, pgliteDataDir, PGLITE_PREFIX } from "./pglite_url.mjs";
// Type-only: erased at compile time, so this never loads the WASM module. The
// runtime import stays lazy (lazyRequire below) so the legacy Postgres path
// never pays for PGlite or inherits its failure mode.
import type { PGlite } from "@electric-sql/pglite";
// Value binding: `export { pgliteDataDir } from ...` re-exports the name but does
// NOT bind it locally, so getPgliteClient()'s call below used to throw
// ReferenceError at runtime — the gateway booted and then failed closed with
// "pgliteDataDir is not defined" on every pglite: URL (caught by the Stage 4c
// gateway smoke, 2026-10-07). Both names are imported here as values.
import { isPgliteBackend, pgliteDataDir } from "./pglite_url.mjs";

/**
 * Two backends, selected by the DATABASE_URL scheme:
 *
 *   postgresql://user:pass@host:port/db  node-postgres Pool — Docker or native
 *                                         standalone Postgres (legacy path).
 *   pglite:<dataDir>                     embedded PostgreSQL 16 (PGlite WASM),
 *                                         a user process with no port and no
 *                                         service — the native default.
 *
 * Both expose the same drizzle PgDatabase API, so callers stay backend-agnostic.
 * The native path exists so the gateway no longer requires Docker; see
 * reports/grok/DECKER_N8N_MIGRATION.md (Mission 10).
 *
 * `isPgliteBackend` / `pgliteDataDir` are re-exported from ./pglite_url.mjs.
 */

type AhosDb = ReturnType<typeof drizzle<typeof schema>>;

const globalForDb = globalThis as typeof globalThis & {
  __ahosPool?: Pool;
  __ahosDb?: AhosDb;
  __ahosDatabaseUrl?: string;
  __ahosPgliteClient?: PGlite;
};

/**
 * Lazy CommonJS require, so the WASM module is only loaded on the pglite path.
 * The legacy Postgres path must never pay that cost or inherit its failure mode.
 */
const lazyRequire = createRequire(import.meta.url);

function getDatabaseUrl(): string {
  const databaseUrl = (process.env.DATABASE_URL || "").trim();
  if (!databaseUrl) {
    throw new Error(
      "DATABASE_URL is required. Set it in .env — either the native embedded " +
        "store (pglite:<dataDir>, e.g. pglite:G:/robat/ahos_runtime/pglite/ahos; " +
        "no Docker needed) or a Postgres URL (postgresql://user:***@host:5432/ahos, " +
        "e.g. the Docker ahos_postgres_win container). " +
        "On Windows: powershell -ExecutionPolicy Bypass -File .\\scripts\\windows_ensure_database_url.ps1 " +
        "then restart npm run dev. STATE B: do not db:migrate/db:push.",
    );
  }
  return databaseUrl;
}

function getPool(): Pool {
  const databaseUrl = getDatabaseUrl();
  // Recreate pool if DATABASE_URL changed (dev HMR / misconfigured stale singleton).
  if (globalForDb.__ahosPool && globalForDb.__ahosDatabaseUrl !== databaseUrl) {
    void globalForDb.__ahosPool.end().catch(() => undefined);
    globalForDb.__ahosPool = undefined;
    globalForDb.__ahosDb = undefined;
  }
  if (!globalForDb.__ahosPool) {
    globalForDb.__ahosPool = new Pool({
      connectionString: databaseUrl,
      connectionTimeoutMillis: 10_000,
      idleTimeoutMillis: 30_000,
      max: 10,
    });
    globalForDb.__ahosDatabaseUrl = databaseUrl;
    globalForDb.__ahosPool.on("error", (err) => {
      console.error("[ahos/db] idle client error:", err?.message || err);
    });
  }
  return globalForDb.__ahosPool;
}

/** Embedded PGlite client. PGlite does not create the parent directory. */
function getPgliteClient() {
  const databaseUrl = getDatabaseUrl();
  if (globalForDb.__ahosPgliteClient && globalForDb.__ahosDatabaseUrl !== databaseUrl) {
    void globalForDb.__ahosPgliteClient.close?.().catch?.(() => undefined);
    globalForDb.__ahosPgliteClient = undefined;
    globalForDb.__ahosDb = undefined;
  }
  if (!globalForDb.__ahosPgliteClient) {
    const { mkdirSync } = lazyRequire("node:fs");
    const dataDir = pgliteDataDir(databaseUrl);
    mkdirSync(dataDir, { recursive: true });
    // Loaded lazily: a WASM import failure must not break the legacy path.
    const { PGlite } = lazyRequire("@electric-sql/pglite");
    globalForDb.__ahosPgliteClient = new PGlite(dataDir);
    globalForDb.__ahosDatabaseUrl = databaseUrl;
  }
  return globalForDb.__ahosPgliteClient;
}

function getDb(): AhosDb {
  if (!globalForDb.__ahosDb) {
    if (isPgliteBackend(getDatabaseUrl())) {
      const { drizzle: drizzlePglite } = lazyRequire("drizzle-orm/pglite");
      globalForDb.__ahosDb = drizzlePglite(getPgliteClient(), { schema });
    } else {
      globalForDb.__ahosDb = drizzle(getPool(), { schema });
    }
  }
  // Both branches above assign; TS cannot narrow a property on globalThis.
  return globalForDb.__ahosDb as AhosDb;
}

/**
 * Lazy pool + drizzle client.
 * Importing this module must never throw — only actual DB use throws when DATABASE_URL is missing.
 * That lets API route try/catch return honest CODE_FAILURE / NO_KEY snapshots instead of crashing Next.js.
 *
 * `pool` is the legacy node-postgres Pool. It is unused by live modules today
 * (grep `@/db` consumers: snapshot.ts, engine.ts, chat.ts, news.ts — all use `db`)
 * and has no meaning on the pglite path, where it throws a clear message.
 */
export const pool = new Proxy({} as Pool, {
  get(_target, prop) {
    if (isPgliteBackend(getDatabaseUrl())) {
      throw new Error(
        "[ahos/db] `pool` is the legacy node-postgres Pool and is not available " +
          "on the embedded pglite backend. Use `db` instead.",
      );
    }
    const real = getPool();
    const value = Reflect.get(real, prop, real);
    return typeof value === "function" ? (value as (...a: unknown[]) => unknown).bind(real) : value;
  },
});

export const db = new Proxy({} as ReturnType<typeof drizzle<typeof schema>>, {
  get(_target, prop) {
    const real = getDb();
    const value = Reflect.get(real, prop, real);
    return typeof value === "function" ? (value as (...a: unknown[]) => unknown).bind(real) : value;
  },
});

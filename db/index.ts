import { drizzle } from "drizzle-orm/node-postgres";
import { Pool } from "pg";
import * as schema from "./schema";

const globalForDb = globalThis as typeof globalThis & {
  __ahosPool?: Pool;
  __ahosDb?: ReturnType<typeof drizzle<typeof schema>>;
  __ahosDatabaseUrl?: string;
};

function getDatabaseUrl(): string {
  const databaseUrl = (process.env.DATABASE_URL || "").trim();
  if (!databaseUrl) {
    throw new Error(
      "DATABASE_URL is required. Set it in .env to the same Postgres as Docker " +
        "ahos_postgres_win (e.g. postgresql://ahos_user:***@127.0.0.1:5432/ahos). " +
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

function getDb() {
  if (!globalForDb.__ahosDb) {
    globalForDb.__ahosDb = drizzle(getPool(), { schema });
  }
  return globalForDb.__ahosDb;
}

/**
 * Lazy pool + drizzle client.
 * Importing this module must never throw — only actual DB use throws when DATABASE_URL is missing.
 * That lets API route try/catch return honest CODE_FAILURE / NO_KEY snapshots instead of crashing Next.js.
 */
export const pool = new Proxy({} as Pool, {
  get(_target, prop) {
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

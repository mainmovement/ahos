import { drizzle } from "drizzle-orm/node-postgres";
import { Pool } from "pg";
import * as schema from "./schema";

const globalForDb = globalThis as typeof globalThis & {
  __ahosPool?: Pool;
};

function getDatabaseUrl(): string {
  const databaseUrl = process.env.DATABASE_URL;
  if (!databaseUrl) {
    throw new Error(
      "DATABASE_URL is required. Set it in .env (e.g. postgresql://postgres:postgres@127.0.0.1:5432/app_db)",
    );
  }
  return databaseUrl;
}

function getPool(): Pool {
  if (!globalForDb.__ahosPool) {
    globalForDb.__ahosPool = new Pool({ connectionString: getDatabaseUrl() });
  }
  return globalForDb.__ahosPool;
}

/**
 * Lazy pool + drizzle client.
 * Importing this module must never throw — only actual DB use throws when DATABASE_URL is missing.
 * That lets API route try/catch return honest CODE_FAILURE / NO_KEY snapshots instead of crashing Next.js.
 */
export const pool = new Proxy({} as Pool, {
  get(_target, prop, receiver) {
    const real = getPool();
    const value = Reflect.get(real, prop, receiver);
    return typeof value === "function" ? value.bind(real) : value;
  },
});

export const db = new Proxy({} as ReturnType<typeof drizzle<typeof schema>>, {
  get(_target, prop, receiver) {
    const real = drizzle(getPool(), { schema });
    const value = Reflect.get(real, prop, receiver);
    return typeof value === "function" ? value.bind(real) : value;
  },
});

import { drizzle } from "drizzle-orm/node-postgres";
import { Pool } from "pg";
import * as schema from "./schema";

const databaseUrl = process.env.DATABASE_URL;

const globalForDb = globalThis as typeof globalThis & {
  __ahosPool?: Pool;
};

function createPool(): Pool {
  if (!databaseUrl) {
    throw new Error(
      "DATABASE_URL is required. Set it in .env (e.g. postgresql://postgres:postgres@127.0.0.1:5432/app_db)",
    );
  }
  return new Pool({ connectionString: databaseUrl });
}

export const pool = globalForDb.__ahosPool ?? createPool();

if (process.env.NODE_ENV !== "production") {
  globalForDb.__ahosPool = pool;
}

export const db = drizzle(pool, { schema });

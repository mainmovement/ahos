/**
 * Drizzle Kit config — must target the SAME Postgres as AHOS runtime.
 *
 * Runtime (`db/index.ts`) reads process.env.DATABASE_URL.
 * Verified Windows operator target (redacted):
 *   postgresql://ahos_user:***@127.0.0.1:5432/ahos
 *   Docker: ahos_postgres_win (postgres:16-alpine)
 *
 * DO NOT hardcode app_db / postgres:postgres here — that mismatch caused
 * kit tooling to point at a non-runtime database.
 *
 * tablesFilter: only ahos_* — never manage n8n / legacy public tables.
 */
import "dotenv/config";
import { defineConfig } from "drizzle-kit";

const url = process.env.DATABASE_URL;
if (!url || !url.trim()) {
  throw new Error(
    "DATABASE_URL is required for drizzle-kit. Set it in .env to the same " +
      "Postgres the AHOS runtime uses (Windows verified: 127.0.0.1:5432/ahos as ahos_user).",
  );
}

export default defineConfig({
  dialect: "postgresql",
  schema: "./schema.ts",
  out: "./drizzle",
  dbCredentials: {
    url,
  },
  tablesFilter: ["ahos_*"],
  strict: true,
  verbose: true,
});

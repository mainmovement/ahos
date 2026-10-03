import type { NextConfig } from "next";

// PGlite ships PostgreSQL compiled to WASM. Keep it out of the server bundler
// (it must be resolved at runtime, not webpack-processed) and it is server-only.
// See reports/grok/DECKER_N8N_MIGRATION.md (Mission 10, Docker removal).
const nextConfig: NextConfig = {
  serverExternalPackages: ["@electric-sql/pglite"],
};

export default nextConfig;

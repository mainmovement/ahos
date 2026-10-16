import type { NextConfig } from "next";
import { existsSync } from "node:fs";
import path from "node:path";

// Optional Arena hero: src/components/orb/PulseOrb.tsx (default-export a component taking PulseOrbProps).
// "@arena-orb" resolves to it when the file exists, otherwise to a null stub, so /arena builds either way.
const orbReal = "./src/components/orb/PulseOrb.tsx";
const orbTarget = existsSync(path.join(process.cwd(), orbReal)) ? orbReal : "./src/components/orb/PulseOrbAbsent.ts";

// PGlite ships PostgreSQL compiled to WASM. Keep it out of the server bundler
// (it must be resolved at runtime, not webpack-processed) and it is server-only.
// See reports/grok/DECKER_N8N_MIGRATION.md (Mission 10, Docker removal).
const nextConfig: NextConfig = {
  serverExternalPackages: ["@electric-sql/pglite"],
  turbopack: { resolveAlias: { "@arena-orb": orbTarget } },
  webpack(config) {
    config.resolve.alias = { ...config.resolve.alias, "@arena-orb": path.resolve(process.cwd(), orbTarget) };
    return config;
  },
};

export default nextConfig;
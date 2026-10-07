import { defineConfig, globalIgnores } from "eslint/config";
import nextCoreWebVitals from "eslint-config-next/core-web-vitals";

export default defineConfig([
  // Keep the starter on the flat config export that actually runs under the pinned ESLint/Next toolchain.
  ...nextCoreWebVitals,
  globalIgnores([
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
    // TS ambient declarations have no runtime code and the JS parser cannot
    // read type-only syntax; db/pglite_url.d.mts is types for the .mjs parser.
    "**/*.d.mts",
    "01/**",
    "advanced-3d-audiovisual-website/**",
    "advanced-3d-audiovisual-website (1)/**",
    "سایت درختadvanced-3d-audiovisual-platform/**",
    "درخت کاملتر immersive-3d-audiovisual-website/**",
  ]),
]);

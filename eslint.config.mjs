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
    "advanced-3d-audiovisual-website/**",
    "advanced-3d-audiovisual-website (1)/**",
    "سایت درختadvanced-3d-audiovisual-platform/**",
    "درخت کاملتر immersive-3d-audiovisual-website/**",
  ]),
]);

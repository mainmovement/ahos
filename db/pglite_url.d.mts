/**
 * Types for ./pglite_url.mjs.
 *
 * The parser itself is a plain .mjs on purpose (see that file): node scripts
 * such as scripts/ahos_pg_probe.mjs import it with bare `node`, no
 * strip-types loader, so the gateway and the readiness provably run the same
 * code. TypeScript does not type-check .mjs files under this tsconfig
 * (allowJs is false), which would leave the two `db/index.ts` imports
 * implicitly `any` — this declaration restores the JSDoc types the module
 * already documents, so the value bindings stay checked.
 *
 * Keep in sync with the JSDoc in pglite_url.mjs.
 */
export const PGLITE_PREFIX: "pglite:";
export function isPgliteBackend(databaseUrl: string): boolean;
export function pgliteDataDir(databaseUrl: string): string;

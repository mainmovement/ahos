/**
 * PGlite DATABASE_URL parsing — the single source of truth.
 *
 * Imported by `db/index.ts` (the gateway) and by `scripts/ahos_pg_probe.mjs`
 * (the readiness probe). One copy, on purpose: if the probe parsed the URL any
 * differently from the gateway it could report a store the gateway does not
 * open, or vice versa, and a green probe would silently lie about the flip.
 *
 * This is a plain .mjs (not .ts) so node scripts can import it without the
 * strip-types loader; types come from JSDoc so `db/index.ts` keeps its safety.
 *
 * @module
 */

export const PGLITE_PREFIX = "pglite:";

/**
 * True when DATABASE_URL selects the native embedded backend.
 * @param {string} databaseUrl
 * @returns {boolean}
 */
export function isPgliteBackend(databaseUrl) {
  return typeof databaseUrl === "string" && databaseUrl.startsWith(PGLITE_PREFIX);
}

/**
 * dataDir from a `pglite:<dataDir>` URL.
 *
 * Accepted forms: `pglite:G:/x`, `pglite:/G:/x` and `pglite://G:/x` (Windows
 * drive; the leading slashes are dropped), `pglite:/abs/path` and
 * `pglite:///abs/path` (POSIX absolute; kept absolute), `pglite:rel/path`.
 * Stripping every leading slash unconditionally turned a POSIX absolute path
 * into a cwd-relative one, so the gateway silently opened a fresh, empty
 * database under the working directory instead of the configured store.
 *
 * @param {string} databaseUrl
 * @returns {string}
 */
export function pgliteDataDir(databaseUrl) {
  let dir = databaseUrl.slice(PGLITE_PREFIX.length);
  if (dir.startsWith("//")) dir = dir.slice(2); // URL authority form: pglite://<path>
  if (/^\/+[A-Za-z]:/.test(dir)) dir = dir.replace(/^\/+/, ""); // /G:/x -> G:/x
  return dir;
}

/**
 * Node test helper: resolve extensionless / .js specifiers to .ts
 * so --experimental-strip-types can load production modules. It also honours
 * the tsconfig `@/*` path alias (e.g. `@/db` -> <root>/db/index.ts), so a
 * self-test can import root modules that use the alias. Scoped packages
 * (`@scope/name`) are untouched — only the exact `@/` prefix is mapped.
 */
import { existsSync } from "node:fs";
import { dirname, extname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { register } from "node:module";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");

if (!process.env.AHOS_TS_STRIP_LOADER) {
  process.env.AHOS_TS_STRIP_LOADER = "1";
  register(import.meta.url);
}

function resolveToTs(absPath) {
  if (extname(absPath) === ".ts" && existsSync(absPath)) return absPath;
  const asFile = `${absPath}.ts`;
  if (existsSync(asFile)) return asFile;
  const asIndex = join(absPath, "index.ts");
  if (existsSync(asIndex)) return asIndex;
  return null;
}

export async function resolve(specifier, context, nextResolve) {
  if (specifier.startsWith("@/")) {
    const hit = resolveToTs(join(ROOT, specifier.slice(2)));
    if (hit) return { url: pathToFileURL(hit).href, shortCircuit: true };
  }
  if (specifier.startsWith(".") && context.parentURL) {
    const parentDir = dirname(fileURLToPath(context.parentURL));
    const bare = specifier.replace(/\.js$/i, "");
    const candidate = bare.endsWith(".ts") ? join(parentDir, specifier) : join(parentDir, `${bare}.ts`);
    if ((extname(specifier) === "" || specifier.endsWith(".js")) && existsSync(candidate)) {
      return { url: pathToFileURL(candidate).href, shortCircuit: true };
    }
  }
  return nextResolve(specifier, context);
}

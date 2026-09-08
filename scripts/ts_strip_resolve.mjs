/**
 * Node test helper: resolve extensionless / .js specifiers to .ts
 * so --experimental-strip-types can load production modules.
 */
import { existsSync } from "node:fs";
import { dirname, extname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { register } from "node:module";

if (!process.env.AHOS_TS_STRIP_LOADER) {
  process.env.AHOS_TS_STRIP_LOADER = "1";
  register(import.meta.url);
}

export async function resolve(specifier, context, nextResolve) {
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

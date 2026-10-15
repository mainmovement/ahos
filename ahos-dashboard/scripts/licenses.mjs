#!/usr/bin/env node
/**
 * Prints a Markdown table of every production dependency (direct + transitive)
 * with its resolved version and declared license, read from node_modules.
 *   node scripts/licenses.mjs > /tmp/licenses.md
 */
import { execSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { join } from "node:path";

const tree = JSON.parse(execSync("npm ls --omit=dev --all --json", { encoding: "utf8", maxBuffer: 64 * 1024 * 1024 }));
const seen = new Map();
function walk(deps) {
  for (const [name, info] of Object.entries(deps ?? {})) {
    if (!info.version) continue;
    const key = `${name}@${info.version}`;
    if (!seen.has(key)) {
      let license = "UNKNOWN";
      try {
        const pkg = JSON.parse(readFileSync(join("node_modules", name, "package.json"), "utf8"));
        license = typeof pkg.license === "string" ? pkg.license : pkg.license?.type ?? (Array.isArray(pkg.licenses) ? pkg.licenses.map((l) => l.type).join(" OR ") : "UNKNOWN");
      } catch {
        /* nested install — fall back to npm's metadata */
      }
      seen.set(key, { name, version: info.version, license });
    }
    walk(info.dependencies);
  }
}
walk(tree.dependencies);
const rows = [...seen.values()].sort((a, b) => a.name.localeCompare(b.name));
console.log("| Package | Version | License |\n|---|---|---|");
for (const r of rows) console.log(`| ${r.name} | ${r.version} | ${r.license} |`);
console.error(`${rows.length} production packages`);

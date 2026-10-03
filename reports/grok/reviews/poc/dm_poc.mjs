// Reproduction harness for the dev-mission redaction findings of the
// 2026-10-02 independent reviews (Agent-16 QA BL-1/BL-2/MN-5, REDTEAM M2).
//
// Original form embedded VERBATIM COPIES of redactMissionSecrets /
// titleFromSummaryFa and therefore kept reproducing the bug even after a fix.
// This version exercises the LIVE module (dev_missions.ts) through a child
// node process with the TS strip loader, so the PoC now genuinely fails
// (prints false / the corrected marker) once the fix lands.
//
// Run:  node reports/grok/reviews/poc/dm_poc.mjs
//
// Pre-fix output (verified 2026-10-02, see the review):
//   titleFa  leaks fake key: true
//   summaryFa leaks fake key: false
//   second key survives redaction (non-global regex): true
//   URL_CREDENTIALS output: 0[REDACTED:URL_CREDENTIALS]@host/db
//
// Post-fix expectations (Mission 9.5):
//   titleFa  leaks fake key: false          (redact first, then derive the title)
//   second key survives redaction: false    (every rule carries the g flag)
//   URL_CREDENTIALS output: postgres://[REDACTED:URL_CREDENTIALS]@/db
//   tamper then append: null                 (fail-closed chain, MJ-8)
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const HERE = dirname(fileURLToPath(import.meta.url));
// reports/grok/reviews/poc -> repo root is four levels up.
const ROOT = join(HERE, "..", "..", "..", "..");

const probe = `
import { redactMissionSecrets, titleFromSummaryFa, DevMissionStore } from "./dev_missions.ts";
import { writeFileSync, readFileSync, mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const FAKE = "AIza" + "Q".repeat(35); // synthetic, not a real key
const summary = \`کلید گوگل \${FAKE} رو ذخیره کن\`;
const red = redactMissionSecrets(summary);
console.log("titleFa  leaks fake key:", titleFromSummaryFa(red).includes(FAKE));
console.log("summaryFa leaks fake key:", red.includes(FAKE));
const two = \`\${FAKE} و \${"AIza" + "R".repeat(35)}\`;
console.log("second key survives redaction:", redactMissionSecrets(two).includes("AIza" + "R".repeat(35)));
console.log("URL_CREDENTIALS output:", redactMissionSecrets("postgres://u:p4ssw0rdXYZ@host/db"));

// MJ-8: a tampered chain must refuse to append (no duplicate DM-000001).
const dir = mkdtempSync(join(tmpdir(), "dm-poc-"));
const p = join(dir, "q.jsonl");
const s = new DevMissionStore(p);
s.append({ summaryFa: "اولین ماموریت" });
const raw = readFileSync(p, "utf8");
writeFileSync(p, raw.replace('"seq":0', '"seq":7')); // tamper, keep line count
const after = s.append({ summaryFa: "دومین ماموریت" });
console.log("tamper then append:", after === null ? "null (fail-closed)" : after.id);
// Post-fix (MJ-8): a broken chain is untrusted, so records() exposes nothing
// and no duplicate DM-000001 can ever be written onto it.
console.log("no duplicate id written:", after === null && s.records().length === 0);
`;

import { pathToFileURL } from "node:url";
const LOADER = pathToFileURL(join(ROOT, "scripts", "ts_strip_resolve.mjs")).href;

const res = spawnSync(
  process.execPath,
  ["--experimental-strip-types", "--import", LOADER, "-e", probe],
  { cwd: ROOT, encoding: "utf8" },
);
if (res.error) {
  console.error("PoC could not run:", res.error.message);
  process.exit(1);
}
process.stdout.write(res.stdout);
if (res.stderr.trim()) process.stderr.write(res.stderr);
process.exit(res.status ?? 0);

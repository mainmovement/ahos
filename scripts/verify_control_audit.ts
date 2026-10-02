/**
 * GM-04: verify the chat control audit hash chain (read-only).
 * Run: npm run audit:control-verify [-- <path>]
 * Default path: AHOS_CONTROL_AUDIT_PATH, else (AHOS_DATA_DIR || ./data)/control_audit/chat_control_audit.jsonl
 * Prints counts only (no message content exists in the file by design).
 */
import { existsSync, readFileSync } from "node:fs";
import { defaultAuditPath, verifyAuditLines } from "../chat_control_gate.ts";

const path = process.argv[2] || defaultAuditPath();
if (!existsSync(path)) {
  console.log(JSON.stringify({ path, exists: false, lines: 0, status: "NO_AUDIT_FILE" }));
  process.exit(0);
}
const lines = readFileSync(path, "utf8").split("\n").filter((l) => l.trim());
const firstBad = verifyAuditLines(lines);
const counts: Record<string, number> = {};
for (const l of lines) {
  try {
    const r = JSON.parse(l) as { surface?: string; intent?: string; decision?: string };
    const k = `${r.surface}:${r.intent}:${r.decision}`;
    counts[k] = (counts[k] ?? 0) + 1;
  } catch {
    counts.UNPARSEABLE = (counts.UNPARSEABLE ?? 0) + 1;
  }
}
console.log(JSON.stringify({ path, exists: true, lines: lines.length, first_bad_index: firstBad, status: firstBad === -1 ? "CHAIN_OK" : "CHAIN_BROKEN", counts }, null, 2));
process.exit(firstBad === -1 ? 0 : 2);

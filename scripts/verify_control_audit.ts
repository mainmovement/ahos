/**
 * GM-04 / Mission 9.5: verify the chat control audit hash chain (read-only).
 * Run: npm run audit:control-verify [-- <path>]
 * Default path: AHOS_CONTROL_AUDIT_PATH, else (AHOS_DATA_DIR || ./data)/control_audit/chat_control_audit.jsonl
 * Prints counts only (no message content exists in the file by design).
 *
 * Mission 9.5 MJ-13: a MISSING file is now a failure (exit 3), because a
 * deleted audit used to verify as OK. Pass --allow-empty to accept an absent
 * file (e.g. a fresh install). Truncation/rewind is caught with an external
 * anchor: `--write-anchor` records {lines, headHash} for the current file, and
 * a later verify checks that the anchored prefix is still intact and still in
 * order. The anchor path defaults to `<auditfile>.anchor.json` and can be
 * pointed at a committed location (e.g. under reports/) with
 * AHOS_CONTROL_AUDIT_ANCHOR or --anchor-path.
 */
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { defaultAuditPath, verifyAuditLines } from "../chat_control_gate.ts";

const EXIT_OK = 0;
const EXIT_CHAIN_BROKEN = 2;
const EXIT_NO_FILE = 3;
const EXIT_ANCHOR_VIOLATION = 4;

type Anchor = { path: string; lines: number; headHash: string; ts: string };

function defaultAnchorPath(auditPath: string): string {
  const explicit = (process.env.AHOS_CONTROL_AUDIT_ANCHOR || "").trim();
  return explicit || `${auditPath}.anchor.json`;
}

function readAnchor(path: string): Anchor | null {
  try {
    const a = JSON.parse(readFileSync(path, "utf8")) as Partial<Anchor>;
    if (typeof a.lines === "number" && typeof a.headHash === "string" && typeof a.path === "string") {
      return { path: a.path, lines: a.lines, headHash: a.headHash, ts: String(a.ts ?? "") };
    }
  } catch {
    /* no anchor yet, or unreadable */
  }
  return null;
}

function writeAnchor(auditPath: string, lines: number, headHash: string): string {
  const anchorPath = defaultAnchorPath(auditPath);
  const anchor: Anchor = { path: auditPath, lines, headHash, ts: new Date().toISOString() };
  writeFileSync(anchorPath, JSON.stringify(anchor, null, 2) + "\n", { encoding: "utf8" });
  return anchorPath;
}

/**
 * The work lives in main() behind an import.meta.main guard so that importing
 * this module does not read files or terminate the process (M9 import-safety).
 */
function main(): void {
  const args = process.argv.slice(2);
  const allowEmpty = args.includes("--allow-empty");
  const writeAnchorFlag = args.includes("--write-anchor");
  const auditPathArg = args.find((a) => !a.startsWith("--")) ?? "";
  const path = auditPathArg || defaultAuditPath();

  if (!existsSync(path)) {
    if (allowEmpty) {
      console.log(JSON.stringify({ path, exists: false, lines: 0, status: "NO_AUDIT_FILE_ALLOWED" }));
      process.exit(EXIT_OK);
    }
    console.log(JSON.stringify({ path, exists: false, lines: 0, status: "NO_AUDIT_FILE" }));
    process.exit(EXIT_NO_FILE);
  }
  const lines = readFileSync(path, "utf8").split("\n").filter((l) => l.trim());
  const firstBad = verifyAuditLines(lines);
  const counts: Record<string, number> = {};
  let headHash = null;
  for (const l of lines) {
    try {
      const r = JSON.parse(l) as { surface?: string; intent?: string; decision?: string; entry_hash?: string };
      const k = `${r.surface}:${r.intent}:${r.decision}`;
      counts[k] = (counts[k] ?? 0) + 1;
      if (r.entry_hash) headHash = r.entry_hash;
    } catch {
      counts.UNPARSEABLE = (counts.UNPARSEABLE ?? 0) + 1;
    }
  }

  if (writeAnchorFlag) {
    if (firstBad !== -1) {
      console.log(JSON.stringify({ path, status: "CHAIN_BROKEN", first_bad_index: firstBad, anchor: "not written — fix the chain first" }));
      process.exit(EXIT_CHAIN_BROKEN);
    }
    const anchorPath = writeAnchor(path, lines.length, String(headHash ?? ""));
    console.log(JSON.stringify({ path, status: "ANCHOR_WRITTEN", lines: lines.length, headHash, anchor: anchorPath }));
    process.exit(EXIT_OK);
  }

  const anchor = readAnchor(defaultAnchorPath(path));
  let anchorStatus = "NO_ANCHOR";
  if (anchor) {
    if (anchor.path !== path) {
      anchorStatus = `ANCHOR_PATH_MISMATCH`;
    } else if (lines.length < anchor.lines) {
      anchorStatus = `ANCHOR_SHRUNK:${anchor.lines}->${lines.length}`;
    } else {
      // The anchored prefix must still sit at the same position with the same
      // hash: this is what catches a truncation that re-chains cleanly.
      let prefixHash: string | null = null;
      try {
        prefixHash = (JSON.parse(lines[anchor.lines - 1]) as { entry_hash?: string }).entry_hash ?? null;
      } catch {
        prefixHash = null;
      }
      anchorStatus = prefixHash === anchor.headHash ? "ANCHOR_OK" : `ANCHOR_PREFIX_CHANGED`;
    }
  }

  const anchorBroken =
    anchorStatus.startsWith("ANCHOR_PATH_MISMATCH") ||
    anchorStatus.startsWith("ANCHOR_PREFIX_CHANGED") ||
    anchorStatus.startsWith("ANCHOR_SHRUNK");
  const status = firstBad === -1 && !anchorBroken ? "CHAIN_OK" : "CHAIN_BROKEN";
  console.log(
    JSON.stringify(
      { path, exists: true, lines: lines.length, first_bad_index: firstBad, anchor: anchorStatus, status, counts },
      null,
      2,
    ),
  );
  if (firstBad !== -1) process.exit(EXIT_CHAIN_BROKEN);
  if (anchorBroken) process.exit(EXIT_ANCHOR_VIOLATION);
  process.exit(EXIT_OK);
}

if (import.meta.main) {
  main();
}

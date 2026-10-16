import type { PaperPosition } from "./model";
import { rowDisplay } from "./rowStatus";

const ATTENTION = ["CONFLICT", "REJECTED", "STALE", "UNKNOWN"] as const;

/** Rows that need a reader's attention first (conflict / rejected / stale / unknown / not authorized), then the rest; at most `max`. */
export function pickHighlights(rows: readonly PaperPosition[], max = 7): PaperPosition[] {
  const rank = (row: PaperPosition): number => {
    const status = rowDisplay({ status: row.status, updatedAt: row.updatedAt, sourceId: row.sourceId }).status;
    if (!row.paperAllowed) return 0;
    const i = (ATTENTION as readonly string[]).indexOf(status);
    return i === -1 ? 10 : 1 + i;
  };
  return rows
    .map((row, index) => ({ row, index }))
    .sort((a, b) => rank(a.row) - rank(b.row) || a.index - b.index)
    .slice(0, Math.min(7, max))
    .map((x) => x.row);
}

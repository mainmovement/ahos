// FILE: 13_missions_batch3/src/components/truth/TruthChip.tsx
import type { ChipStatus } from "@/contract/types";

export interface TruthChipProps {
  status: ChipStatus;
}

const CLASS_BY_STATUS: Record<ChipStatus, string> = {
  LIVE: "ah-chip ah-chip-live",
  STALE: "ah-chip ah-chip-stale",
  UNKNOWN: "ah-chip ah-chip-unknown",
  DEMO: "ah-chip ah-chip-demo",
  CONFLICT: "ah-chip ah-chip-danger",
  REJECTED: "ah-chip ah-chip-danger",
  UNAVAILABLE: "ah-chip ah-chip-danger",
  ERROR: "ah-chip ah-chip-danger",
  PARTIAL: "ah-chip ah-chip-info",
  SIMULATED: "ah-chip ah-chip-demo",
  LOADING: "ah-chip ah-chip-info",
  EMPTY: "ah-chip ah-chip-muted",
  PLANNED: "ah-chip ah-chip-muted",
  MISSING: "ah-chip ah-chip-muted",
};

/**
 * Status chip. Truth rules: UNKNOWN is grey and never green; DEMO/SIMULATED
 * are visibly striped; LIVE is the only green chip.
 */
export function TruthChip({ status }: TruthChipProps) {
  const cls = CLASS_BY_STATUS[status] ?? "ah-chip ah-chip-unknown";
  return (
    <span className={cls} data-status={status} data-testid="truth-chip">
      {status}
    </span>
  );
}

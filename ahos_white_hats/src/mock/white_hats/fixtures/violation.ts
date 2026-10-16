import type { WhiteHatsSnapshot } from "@/features/white-hats/types";
import { buildCalmSnapshot } from "./calm";

/**
 * The VIOLATION demo fixture: the mock claims LIVE mode and real trading —
 * exactly the two triggers the red bar must catch. The screen stays read-only;
 * the bar exists to loudly refuse the claim, not to offer any control.
 */
export function buildViolationSnapshot(): WhiteHatsSnapshot {
  const calm = buildCalmSnapshot();
  return {
    ...calm,
    executionMode: "LIVE",
    realTrading: true,
    freshness: "CONFLICT",
    breaker: {
      ...calm.breaker,
      state: "TRIPPED",
      limits: [
        { key: "drawdown", label: "افت سرمایه از اوج", unit: "٪", current: 9.1, limit: 8 },
        { key: "weekly-loss", label: "ضرر هفته", unit: "٪", current: 3.4, limit: 3 },
        { key: "daily-loss", label: "ضرر روز", unit: "٪", current: 1.4, limit: 1.2 },
        { key: "open-exposure", label: "حجه باز", unit: "٪", current: 27.5, limit: 25 },
      ],
    },
    decisions: calm.decisions.map((d) =>
      d.verdict === "CLEAN" && !d.demo ? { ...d, verdict: "FINDING" as const } : d,
    ),
  };
}

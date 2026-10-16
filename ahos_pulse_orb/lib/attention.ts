import type { Department, Health, Signal } from "@/components/PulseOrb";

export interface CalmHighlightSelection {
  departmentIds: Set<string>;
  signals: Signal[];
  overflow: number;
}

export function selectCalmHighlights(
  departments: Department[],
  signals: Signal[],
  health: Health,
  limit = 7,
): CalmHighlightSelection {
  const issues: Array<{ kind: "department"; id: string } | { kind: "signal"; signal: Signal } | { kind: "health" }> = [];
  for (const department of departments) {
    if (department.status !== "LIVE") issues.push({ kind: "department", id: department.id });
  }
  for (const signal of signals) {
    if (signal.outcome !== "absorbed") issues.push({ kind: "signal", signal });
  }
  if (health.stale) issues.push({ kind: "health" });

  const shown = issues.slice(0, Math.max(0, limit));
  return {
    departmentIds: new Set(shown.flatMap((item) => item.kind === "department" ? [item.id] : [])),
    signals: shown.flatMap((item) => item.kind === "signal" ? [item.signal] : []),
    overflow: Math.max(0, issues.length - Math.max(0, limit)),
  };
}

export function selectSignalParticles(
  departments: Department[],
  signals: Signal[],
  health: Health,
  calm: boolean,
  capacity: number,
): Signal[] {
  const eligible = calm ? selectCalmHighlights(departments, signals, health, 7).signals : signals;
  return eligible.slice(0, Math.max(0, capacity));
}

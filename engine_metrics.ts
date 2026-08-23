export type CycleMetrics = {
  cycle_id: string;
  start_time: string;
  end_time: string | null;
  duration_ms: number | null;
  providers_checked: number;
  providers_success: number;
  providers_failed: number;
  candidates_found: number;
  candidates_rejected: number;
  candidates_scored: number;
  top_opportunities: string[];
  alerts_emitted: number;
  errors: string[];
  status: "RUNNING" | "OK" | "PARTIAL" | "FAILED";
};

const history: CycleMetrics[] = [];
let current: CycleMetrics | null = null;
let n = 0;

export function startCycle(): CycleMetrics {
  n++;
  current = {
    cycle_id: `cyc-${Date.now()}-${n}`,
    start_time: new Date().toISOString(),
    end_time: null,
    duration_ms: null,
    providers_checked: 0,
    providers_success: 0,
    providers_failed: 0,
    candidates_found: 0,
    candidates_rejected: 0,
    candidates_scored: 0,
    top_opportunities: [],
    alerts_emitted: 0,
    errors: [],
    status: "RUNNING",
  };
  return current;
}

export function getCurrentCycle(): CycleMetrics | null {
  return current;
}

export function finishCycle(
  partial?: Partial<CycleMetrics>,
): CycleMetrics | null {
  if (!current) return null;
  current.end_time = new Date().toISOString();
  current.duration_ms =
    new Date(current.end_time).getTime() -
    new Date(current.start_time).getTime();
  if (partial) Object.assign(current, partial);
  if (current.status === "RUNNING") {
    current.status = current.errors.length
      ? current.providers_success
        ? "PARTIAL"
        : "FAILED"
      : "OK";
  }
  history.unshift({ ...current });
  if (history.length > 50) history.length = 50;
  const done = current;
  current = null;
  return done;
}

export function listRecentCycles(limit = 10): CycleMetrics[] {
  return history.slice(0, limit);
}

export function resetMetrics(): void {
  history.length = 0;
  current = null;
  n = 0;
}

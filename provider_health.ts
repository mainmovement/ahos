import type { ProviderHealthEntry, ProviderHealthStatus } from "./types";

const registry = new Map<string, ProviderHealthEntry>();

function empty(name: string): ProviderHealthEntry {
  return {
    name,
    status: "UNKNOWN",
    last_success: null,
    last_failure: null,
    latency_ms: null,
    error_count: 0,
    request_count: 0,
    availability: null,
    error_type: null,
  };
}

export function getProviderHealth(name: string): ProviderHealthEntry {
  return registry.get(name) ?? empty(name);
}

export function listProviderHealth(): ProviderHealthEntry[] {
  return Array.from(registry.values()).sort((a, b) =>
    a.name.localeCompare(b.name),
  );
}

export function recordProviderResult(
  name: string,
  ok: boolean,
  latencyMs: number | null,
  errorType?: string | null,
): ProviderHealthEntry {
  const cur = getProviderHealth(name);
  const now = new Date().toISOString();
  const next: ProviderHealthEntry = {
    ...cur,
    request_count: cur.request_count + 1,
    latency_ms: latencyMs,
  };
  if (ok) {
    next.status = "LIVE";
    next.last_success = now;
    next.error_type = null;
  } else {
    next.error_count = cur.error_count + 1;
    next.last_failure = now;
    next.error_type = errorType ?? "UNKNOWN";
    const et = (errorType || "").toUpperCase();
    next.status = (
      et.includes("TIMEOUT")
        ? "TIMEOUT"
        : et.includes("RATE") || et.includes("429")
          ? "RATE_LIMITED"
          : et.includes("AUTH") || et.includes("401")
            ? "AUTH_FAILED"
            : et.includes("NO_KEY")
              ? "NO_KEY"
              : et.includes("NETWORK")
                ? "NETWORK_UNAVAILABLE"
                : et.includes("SOURCE")
                  ? "SOURCE_UNAVAILABLE"
                  : "DEGRADED"
    ) as ProviderHealthStatus;
  }
  if (next.request_count > 0) {
    next.availability = Math.max(0, 1 - next.error_count / next.request_count);
  }
  registry.set(name, next);
  return next;
}

export function resetProviderHealth(): void {
  registry.clear();
}

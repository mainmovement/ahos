export interface GateState {
  absorbed: number;
  dissipated: number;
  strictness?: number;
}

export function computeStrictness(gate?: GateState): number {
  if (!gate) return 0.5;
  if (typeof gate.strictness === "number" && !Number.isNaN(gate.strictness)) {
    return Math.max(0, Math.min(1, gate.strictness));
  }
  const total = gate.absorbed + gate.dissipated;
  if (total === 0) return 0.5;
  return gate.dissipated / total;
}
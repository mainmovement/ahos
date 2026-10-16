import type { NewsroomScenario } from "./adapters";
import { parseTier, type Tier } from "@/src/features/newsroom/lib/tier";

/** Demo scenarios, switchable via ?state=... (view/filter only). */
export const NEWSROOM_SCENARIOS = ["calm", "violation", "empty", "unavailable", "error"] as const satisfies readonly NewsroomScenario[];

export function parseScenario(value: string | null | undefined): NewsroomScenario {
  return (NEWSROOM_SCENARIOS as readonly string[]).includes(value ?? "") ? (value as NewsroomScenario) : "calm";
}

export function parseFlag(value: string | null | undefined): boolean {
  return value === "1";
}

export { parseTier };
export type { Tier };

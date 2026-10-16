import type { WhiteHatsSnapshot } from "@/src/features/white-hats/types";
import type { WhiteHatsScenario } from "../scenarios";
import { buildCalmSnapshot } from "./calm";
import { buildViolationSnapshot } from "./violation";
import { buildEmptySnapshot } from "./empty";

export class WhiteHatsUnavailableError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "WhiteHatsUnavailableError";
  }
}

/** Builds the typed snapshot for a scenario. `unavailable` throws instead. */
export function buildFixture(scenario: WhiteHatsScenario): WhiteHatsSnapshot {
  switch (scenario) {
    case "calm":
      return buildCalmSnapshot();
    case "violation":
      return buildViolationSnapshot();
    case "empty":
      return buildEmptySnapshot();
    case "unavailable":
      throw new WhiteHatsUnavailableError(
        "منبع بازبینی در دسترس نیست (شبیه‌سازی قطعی آداپتور نمایشی)",
      );
  }
}

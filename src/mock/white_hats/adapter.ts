import type { WhiteHatsSnapshot } from "@/src/features/white-hats/types";
import type { WhiteHatsScenario } from "./scenarios";
import { buildFixture, WhiteHatsUnavailableError } from "./fixtures";

/**
 * The adapter seam. Today: MockWhiteHatsAdapter (typed fixtures, artificial
 * latency). Tomorrow: an HttpWhiteHatsAdapter with the same signature —
 * see README_MERGE.md for the endpoint mapping. No component changes needed.
 */
export interface WhiteHatsAdapter {
  readonly sourceId: string;
  fetchSnapshot(signal?: AbortSignal): Promise<WhiteHatsSnapshot>;
}

const delay = (ms: number, signal?: AbortSignal) =>
  new Promise<void>((resolve, reject) => {
    const t = setTimeout(resolve, ms);
    signal?.addEventListener(
      "abort",
      () => {
        clearTimeout(t);
        reject(new DOMException("Aborted", "AbortError"));
      },
      { once: true },
    );
  });

export class MockWhiteHatsAdapter implements WhiteHatsAdapter {
  readonly sourceId = "mock://white-hats/snapshot@v1";

  constructor(
    private readonly scenario: WhiteHatsScenario = "calm",
    private readonly latencyMs = 280,
  ) {}

  async fetchSnapshot(signal?: AbortSignal): Promise<WhiteHatsSnapshot> {
    await delay(this.latencyMs, signal);
    if (signal?.aborted) {
      throw new DOMException("Aborted", "AbortError");
    }
    // `unavailable` throws ⇒ surfaces render UNAVAILABLE (never fake data).
    return buildFixture(this.scenario);
  }
}

export { WhiteHatsUnavailableError };

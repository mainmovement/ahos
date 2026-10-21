import type { WhiteHatsAdapter } from "@/src/mock/white_hats/adapter";
import { WhiteHatsUnavailableError } from "@/src/mock/white_hats/adapter";
import type { WhiteHatsSnapshot } from "../types";

export class SoakWhiteHatsAdapter implements WhiteHatsAdapter {
  readonly sourceId = "reports/grok/M13_SOAK";

  async fetchSnapshot(signal?: AbortSignal): Promise<WhiteHatsSnapshot> {
    const res = await fetch("/api/white-hats/snapshot", { signal, cache: "no-store" });
    if (!res.ok) throw new WhiteHatsUnavailableError("M13_SOAK artifacts unavailable");
    const body = (await res.json()) as { ok?: boolean; snapshot?: WhiteHatsSnapshot };
    if (!body.ok || !body.snapshot) throw new WhiteHatsUnavailableError("empty soak snapshot");
    return body.snapshot;
  }
}

"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  MockWhiteHatsAdapter,
  WhiteHatsUnavailableError,
  type WhiteHatsAdapter,
} from "@/mock/white_hats/adapter";
import type { WhiteHatsScenario } from "@/mock/white_hats/scenarios";
import type { WhiteHatsSnapshot } from "../types";

export type SnapshotPhase =
  | { phase: "loading" }
  | { phase: "ready"; snapshot: WhiteHatsSnapshot }
  | { phase: "unavailable"; message: string };

/**
 * Loads the snapshot through the adapter seam. Unavailable sources surface as
 * `unavailable` — components must then render UNAVAILABLE, never fake data.
 */
export function useWhiteHatsSnapshot(
  scenario: WhiteHatsScenario,
  adapterFactory: (scenario: WhiteHatsScenario) => WhiteHatsAdapter = (s) =>
    new MockWhiteHatsAdapter(s),
) {
  const [state, setState] = useState<SnapshotPhase>({ phase: "loading" });
  const [nonce, setNonce] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setState({ phase: "loading" });
    const adapter = adapterFactory(scenario);
    adapter
      .fetchSnapshot(controller.signal)
      .then((snapshot) => {
        if (!controller.signal.aborted) setState({ phase: "ready", snapshot });
      })
      .catch((error: unknown) => {
        if (controller.signal.aborted) return;
        const message =
          error instanceof WhiteHatsUnavailableError
            ? error.message
            : "خواندن از منبع بازبینی ممکن نشد.";
        setState({ phase: "unavailable", message });
      });
    return () => controller.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scenario, nonce]);

  const reload = useCallback(() => setNonce((n) => n + 1), []);

  // Stable identity across renders so consumers can safely use it in effect deps.
  return useMemo(() => ({ ...state, reload }), [state, reload]);
}

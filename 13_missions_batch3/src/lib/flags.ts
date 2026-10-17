// FILE: 13_missions_batch3/src/lib/flags.ts
/**
 * Query-flag parsing shared by every page.
 *   ?demo=1                    → force the DEMO banner
 *   ?violation=1               → force the red VIOLATION bar
 *   ?tier=0|1|2                → visual tier (T0 tables/SVG only, T1 solid
 *                                panels, T2+ decoration/blur allowed)
 *   ?state=loading|empty|error|unavailable → force a display state (QA)
 */

export type ForcedState = "loading" | "empty" | "error" | "unavailable";

export interface PageFlags {
  demo: boolean;
  violation: boolean;
  tier: 0 | 1 | 2;
  state: ForcedState | null;
}

export const DEFAULT_FLAGS: PageFlags = {
  demo: false,
  violation: false,
  tier: 1,
  state: null,
};

function parseSearch(search: string): PageFlags {
  const params = new URLSearchParams(search);
  const tierRaw = params.get("tier");
  const tier: 0 | 1 | 2 =
    tierRaw === "0" ? 0 : tierRaw === "2" ? 2 : tierRaw === "1" ? 1 : DEFAULT_FLAGS.tier;
  const stateRaw = params.get("state");
  const state: ForcedState | null =
    stateRaw === "loading" || stateRaw === "empty" || stateRaw === "error" || stateRaw === "unavailable"
      ? stateRaw
      : null;
  return {
    demo: params.get("demo") === "1",
    violation: params.get("violation") === "1",
    tier,
    state,
  };
}

/** Read flags from the current URL. Safe on the server (returns defaults). */
export function readFlags(search?: string): PageFlags {
  if (search !== undefined) return parseSearch(search);
  if (typeof window === "undefined") return { ...DEFAULT_FLAGS };
  return parseSearch(window.location.search);
}

/** True when `?demo=1` is present — the only switch that may expose the demo fallback. */
export function isDemoForced(): boolean {
  return readFlags().demo;
}

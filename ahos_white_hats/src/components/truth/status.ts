/* ─────────────────────────────────────────────────────────────────────────
   AHOS truth rules — the ONLY statuses allowed in the UI.
   These literals are the single source of truth shared by chips and types.
   ───────────────────────────────────────────────────────────────────────── */

/** Data-level truth statuses. */
export const TRUTH_STATUSES = [
  "LIVE",
  "STALE",
  "UNKNOWN",
  "DEMO",
  "CONFLICT",
  "REJECTED",
] as const;
export type TruthStatus = (typeof TRUTH_STATUSES)[number];

/** Component-level states (how a surface is doing, not what the data says). */
export const COMPONENT_STATES = [
  "LOADING",
  "EMPTY",
  "ERROR",
  "UNKNOWN",
  "UNAVAILABLE",
  "STALE",
  "PARTIAL",
  "LIVE",
  "SIMULATED",
] as const;
export type ComponentState = (typeof COMPONENT_STATES)[number];

/** Every chip label this page can ever render. */
export type ChipStatus =
  | TruthStatus
  | ComponentState
  | "CLEAN"
  | "FINDING"
  | "BLOCKED"
  | "ARMED"
  | "TRIPPED"
  | "OPEN"
  | "RESOLVED"
  | "INFO"
  | "MINOR"
  | "MAJOR"
  | "CRITICAL"
  | "FAIL"
  | "PASS";

/** Visual tone. `live` is reserved for LIVE; UNKNOWN is always `grey`. */
export type Tone = "live" | "grey" | "danger" | "sand" | "cyan" | "gold";

/**
 * Status → tone map (non-negotiable AHOS mapping):
 * - UNKNOWN → grey (never green, never red)
 * - LIVE → the only tone that uses green
 * - danger is reserved for hard safety states (BLOCKED/TRIPPED/VIOLATION/ERROR/CRITICAL/CONFLICT/REJECTED/PASS-canary)
 * - outcomes are never coloured good/bad: CLEAN is informational cyan
 */
export const STATUS_TONE: Record<ChipStatus, Tone> = {
  LIVE: "live",
  STALE: "sand",
  UNKNOWN: "grey",
  DEMO: "gold",
  CONFLICT: "danger",
  REJECTED: "danger",

  LOADING: "cyan",
  EMPTY: "grey",
  ERROR: "danger",
  UNAVAILABLE: "grey",
  PARTIAL: "sand",
  SIMULATED: "cyan",

  CLEAN: "cyan",
  FINDING: "sand",
  BLOCKED: "danger",

  ARMED: "cyan",
  TRIPPED: "danger",

  OPEN: "sand",
  RESOLVED: "grey",

  INFO: "grey",
  MINOR: "sand",
  MAJOR: "sand",
  CRITICAL: "danger",

  FAIL: "cyan",   // canary FAIL is the EXPECTED healthy result → informational
  PASS: "danger", // canary PASS means the cheat was NOT caught → safety alarm
};

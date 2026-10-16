import type { Department, Freshness, KillSwitchState, Signal, SystemHealth } from "./contract";

/** Hero orb view mode. `calm` = quiet globe, `breach` = gate under stress (rejections dominate), `map` = flat dot map. */
export type OrbMode = "calm" | "breach" | "map";

/** A market / hub shown on the orb. Optional: when omitted the orb draws geographic reference hubs only. */
export interface OrbMarker {
  id: string;
  nameFa: string;
  nameEn: string;
  lat: number;
  lng: number;
  /** Stated by the data source, never inferred. UNKNOWN renders as a dashed grey ring, never green or gold. */
  freshness: Freshness;
  /** ISO-8601 timestamp, or null when the source reported none. */
  asOf: string | null;
  /** Percent change; null/undefined means unknown and no percentage is printed. */
  changePct?: number | null;
  needsAttention?: boolean;
}

/** Absorption-gate counts. `null` (or both zero) means UNKNOWN: the orb prints UNKNOWN, never 0%. */
export interface OrbGateCounts {
  absorbed: number | null;
  dissipated: number | null;
  /** Operator-set strictness 0..1; derived from the counts when absent. */
  strictness?: number | null;
  /** Where the counts come from. DEMO counts are labelled DEMO on the orb. */
  freshness?: Freshness;
}

/** Props every PulseOrb implementation receives. All data are contract records (Observed<T> with freshness). */
export interface PulseOrbProps {
  health: SystemHealth;
  departments: Department[];
  signals: Signal[];
  /** The kill-switch / execution gate record. */
  gate: KillSwitchState;
  /** Calm mode: no motion, low contrast. Set when reduced motion or low visual quality is requested. */
  calm: boolean;
  language?: "fa" | "en";
  /** View mode (default "calm"). */
  mode?: OrbMode;
  /** Markets / hubs to draw. Default: geographic reference hubs, labelled by the health record's freshness. */
  markers?: OrbMarker[];
  /** Gate absorbed/dissipated counts. Default: unknown (in a DEMO workspace, labelled DEMO sample counts). */
  gateCounts?: OrbGateCounts;
  /** When true (DEMO workspaces only) the orb shows a small calm/breach/map toggle. Default: health.demo. */
  devToggle?: boolean;
  /** Called when the dev toggle changes the mode. */
  onModeChange?: (mode: OrbMode) => void;
}
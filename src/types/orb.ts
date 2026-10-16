import type { Department, KillSwitchState, Signal, SystemHealth } from "./contract";

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
}
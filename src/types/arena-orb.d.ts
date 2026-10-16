declare module "@arena-orb" {
  import type { ComponentType } from "react";
  import type { PulseOrbProps } from "./orb";
  /** The real PulseOrb component when src/components/orb/PulseOrb.tsx exists, otherwise null. */
  const PulseOrb: ComponentType<PulseOrbProps> | null;
  export default PulseOrb;
}
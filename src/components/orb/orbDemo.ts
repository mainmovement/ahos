// DEMO-only sample data for the hero orb. Every number here is invented on purpose and is only ever
// used when the workspace itself is a DEMO workspace (health.demo === true); the orb labels the gate
// "DEMO" whenever these are on screen. Real/unknown workspaces never receive these values.
import type { OrbGateCounts, OrbMode } from "../../types/orb";

export function demoGateCounts(mode: OrbMode): OrbGateCounts {
  return mode === "breach"
    ? { absorbed: 44, dissipated: 63, freshness: "DEMO" }
    : { absorbed: 62, dissipated: 17, freshness: "DEMO" };
}
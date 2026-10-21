/**
 * Read-only portable evidence from launcher state (no invented health/smoke).
 */
import type { PortableSnapshot } from "../contract/types";

export function ramTierFromGb(ramGb: number | null): PortableSnapshot["hardware"]["tier"] {
  if (ramGb === null || !Number.isFinite(ramGb)) return "UNKNOWN";
  if (ramGb < 8) return "T0";
  if (ramGb < 16) return "T1";
  return "T2";
}

export function heavyFeaturesFromRam(ramGb: number | null): boolean | null {
  if (ramGb === null || !Number.isFinite(ramGb)) return null;
  return ramGb >= 16;
}

export function buildPortableFromLauncherEvidence(input: {
  arenaCommit: string | null;
  arenaDist: string | null;
  buildId: string | null;
  generatedAt: string | null;
  ramGb: number | null;
  cpuModel: string | null;
  launcherIniPresent: boolean;
}): PortableSnapshot {
  const checklist: PortableSnapshot["checklist"] = {
    nodeBundled: "UNKNOWN",
    fonts: input.buildId ? "PARTIAL" : "UNKNOWN",
    models: "NOT STARTED",
    configTemplate: input.launcherIniPresent ? "DONE" : "UNKNOWN",
    smokeTest: input.arenaCommit ? "PARTIAL" : "UNKNOWN",
  };
  const tier = ramTierFromGb(input.ramGb);
  const version =
    input.arenaCommit?.slice(0, 12) ??
    input.buildId ??
    null;
  return {
    executionMode: "PAPER_ONLY",
    realTrading: false,
    source: "AHOS_Launcher (built_commit, served_commit, dist slot — read-only)",
    generatedAt: input.generatedAt,
    demo: false,
    availability: "AVAILABLE",
    packageVersion: version,
    buildTime: input.generatedAt,
    checklist,
    hardware: {
      tier,
      ramGb: input.ramGb,
      cpu: input.cpuModel,
      gpu: null,
      heavyFeaturesAllowed: heavyFeaturesFromRam(input.ramGb),
      note:
        tier === "T0"
          ? "RAM under 8 GB — heavy features gated (T0)."
          : null,
    },
  };
}

export function parsePortableSnapshotJson(text: string): PortableSnapshot | null {
  try {
    const j = JSON.parse(text) as { portable?: PortableSnapshot };
    const p = j.portable ?? (j as PortableSnapshot);
    if (!p || typeof p !== "object" || !p.checklist || !p.hardware) return null;
    return {
      ...p,
      demo: false,
      executionMode: p.executionMode ?? "PAPER_ONLY",
      realTrading: false,
      availability: p.availability ?? "AVAILABLE",
    };
  } catch {
    return null;
  }
}

import type { Mission, ParsedMissions } from "../contract/types";

/** When MISSIONS_STATUS.md is absent, surface tier_gate open questions only (honest, partial). */
export function parseMissionsFromSoakTierGate(status: Record<string, unknown>): ParsedMissions | null {
  const tg = status.last_tier_gate;
  if (!tg || typeof tg !== "object") return null;
  const gate = tg as Record<string, unknown>;
  const generatedAt =
    typeof gate.ts === "string"
      ? gate.ts
      : typeof gate.day === "string"
        ? `${gate.day}T12:00:00Z`
        : null;
  const missions: Mission[] = [];
  const measurablePassed = typeof gate.measurable_passed === "number" ? gate.measurable_passed : null;
  const measurableTotal = typeof gate.measurable_total === "number" ? gate.measurable_total : null;
  if (measurablePassed !== null && measurableTotal !== null) {
    missions.push({
      id: "M13-TIER-GATE",
      title: `Tier gate ${String(gate.tier ?? "?")} · ${measurablePassed}/${measurableTotal} measurable`,
      group: "M",
      state: gate.ok === true ? "PARTIAL" : "NOT_STARTED",
      blockedOwner: gate.ready_for_owner_review === false && Array.isArray(gate.open_questions) && gate.open_questions.length > 0,
      evidence: typeof gate.gate_md === "string" ? gate.gate_md : null,
      lastUpdate: generatedAt,
      caveat: "from soak_status.json last_tier_gate (not MISSIONS_STATUS.md)",
    });
  }
  const oq = gate.open_questions;
  if (Array.isArray(oq)) {
    for (let i = 0; i < oq.length; i++) {
      const text = String(oq[i]);
      const idMatch = /^([A-Z][\w-]+):/.exec(text);
      const id = idMatch ? idMatch[1] : `SOAK-OQ-${i + 1}`;
      missions.push({
        id,
        title: text.length > 160 ? `${text.slice(0, 159)}…` : text,
        group: "M",
        state: "PARTIAL",
        blockedOwner: /owner act/i.test(text),
        evidence: measurablePassed !== null && measurableTotal !== null ? `tier_gate ${measurablePassed}/${measurableTotal}` : null,
        lastUpdate: generatedAt,
        caveat: "open_question from soak tier_gate",
      });
    }
  }
  if (missions.length === 0) return null;
  const done = missions.filter((m) => m.state === "DONE").length;
  const partial = missions.filter((m) => m.state === "PARTIAL").length;
  const notStarted = missions.filter((m) => m.state === "NOT_STARTED").length;
  return {
    missions,
    generatedAt,
    header: { units: missions.length, done, partial, notStarted },
  };
}

/** Demo scenarios, switchable via ?scenario=… (view/filter — allowed verbs). */
export const WHITE_HATS_SCENARIOS = ["calm", "violation", "empty", "unavailable"] as const;
export type WhiteHatsScenario = (typeof WHITE_HATS_SCENARIOS)[number];

export const SCENARIO_LABELS: Record<WhiteHatsScenario, string> = {
  calm: "آرام (پیش‌فرض)",
  violation: "نقض حالت اجرا",
  empty: "خالی",
  unavailable: "منبع قطع",
};

export function parseScenario(value: string | null | undefined): WhiteHatsScenario {
  return (WHITE_HATS_SCENARIOS as readonly string[]).includes(value ?? "")
    ? (value as WhiteHatsScenario)
    : "calm";
}

/** Quality tiers: t0 = tables only · t1 = solid panels (default). */
export const QUALITY_TIERS = ["t0", "t1"] as const;
export type QualityTier = (typeof QUALITY_TIERS)[number];

export function parseTier(value: string | null | undefined): QualityTier {
  return value === "t0" ? "t0" : "t1";
}

/** Drawer deep-link: `open=finding:<id>` or `open=evidence:<id>`. */
export type OpenTarget =
  | { kind: "finding"; id: string }
  | { kind: "evidence"; id: string }
  | null;

export function parseOpenTarget(value: string | null | undefined): OpenTarget {
  if (!value) return null;
  const [kind, id] = value.split(":");
  if ((kind === "finding" || kind === "evidence") && id) return { kind, id };
  return null;
}

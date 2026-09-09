export function cx(...parts: Array<string | false | null | undefined>): string {
  return parts.filter(Boolean).join(" ");
}

/** Deterministic hash for gradient identity. */
export function hashCode(s: string): number {
  let h = 0;
  for (let i = 0; i < s.length; i++) h = (Math.imul(31, h) + s.charCodeAt(i)) | 0;
  return Math.abs(h);
}

export const CHAIN_LABEL: Record<string, string> = {
  base: "Base",
  bsc: "BNB Chain",
  ethereum: "Ethereum",
  arbitrum: "Arbitrum",
  polygon: "Polygon",
  solana: "Solana",
};

export type Tone =
  | "gold" | "jade" | "rose" | "sky" | "violet" | "amber" | "zinc" | "cyan";

export const TONE: Record<
  Tone,
  { text: string; bg: string; border: string; dot: string; hex: string }
> = {
  gold: {
    text: "text-gild-300",
    bg: "bg-gild-400/10",
    border: "border-gild-400/35",
    dot: "bg-gild-400",
    hex: "#f5b73f",
  },
  jade: {
    text: "text-jade-300",
    bg: "bg-jade-400/10",
    border: "border-jade-400/30",
    dot: "bg-jade-400",
    hex: "#34d399",
  },
  rose: {
    text: "text-flare",
    bg: "bg-flare/10",
    border: "border-flare/35",
    dot: "bg-flare",
    hex: "#fb7185",
  },
  sky: {
    text: "text-ice",
    bg: "bg-ice/10",
    border: "border-ice/30",
    dot: "bg-ice",
    hex: "#7dd3fc",
  },
  violet: {
    text: "text-vio",
    bg: "bg-vio/10",
    border: "border-vio/30",
    dot: "bg-vio",
    hex: "#c4b5fd",
  },
  amber: {
    text: "text-amber-300",
    bg: "bg-amber-400/10",
    border: "border-amber-400/30",
    dot: "bg-amber-400",
    hex: "#fbbf24",
  },
  zinc: {
    text: "text-zinc-400",
    bg: "bg-zinc-400/10",
    border: "border-zinc-400/25",
    dot: "bg-zinc-400",
    hex: "#a1a1aa",
  },
  cyan: {
    text: "text-cyn",
    bg: "bg-cyn/10",
    border: "border-cyn/30",
    dot: "bg-cyn",
    hex: "#67e8f9",
  },
};

export const DECISION_TONE: Record<string, Tone> = {
  STRONG_CANDIDATE: "gold",
  CANDIDATE: "jade",
  MONITOR: "sky",
  SKIP: "violet",
  REJECT: "rose",
};

export const IDENTITY_TONE: Record<string, Tone> = {
  VERIFIED: "jade",
  CONFLICT: "rose",
  UNRESOLVED: "amber",
  INVALID: "rose",
  STALE: "zinc",
  UNSUPPORTED: "zinc",
};

export const GATE_TONE: Record<string, Tone> = {
  PASS: "jade",
  REJECT: "rose",
  INCOMPLETE: "amber",
  STALE: "zinc",
};

export const STANCE_TONE: Record<string, Tone> = {
  BULLISH: "jade",
  BEARISH: "amber",
  NEUTRAL: "zinc",
  ABSTAIN: "sky",
  ALARM: "rose",
};

export const PROVIDER_TONE: Record<string, Tone> = {
  OK: "jade",
  DEGRADED: "amber",
  STALE: "zinc",
  BLOCKED: "rose",
  FAILING: "rose",
};

export function scoreTone(v: number): Tone {
  return v >= 75 ? "jade" : v >= 55 ? "gold" : v >= 35 ? "amber" : "rose";
}

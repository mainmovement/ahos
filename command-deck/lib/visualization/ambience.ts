import type { AmbiencePreset, SeasonPreset } from "@/lib/types";

export interface AmbienceSpec {
  /** CSS backdrop behind the 3D canvas / fallback. */
  css: string;
  three: {
    key: number; // hex
    rim: number; // hex
    fill: number; // hex
    ringOpacity: number;
    dot: number; // base dot color
    dotAlt: number;
    /** sky-dome gradient (top, bottom) */
    skyTop: number;
    skyBottom: number;
    /** UnrealBloom strength for this preset */
    bloom: number;
    /** atmosphere tint */
    atmosphere: number;
  };
}

export const AMBIENCE: Record<AmbiencePreset, AmbienceSpec> = {
  night: {
    css: "radial-gradient(ellipse 80% 70% at 60% 20%, rgba(34,211,238,0.10), transparent 60%), radial-gradient(ellipse 70% 60% at 30% 80%, rgba(212,175,55,0.08), transparent 60%)",
    three: {
      key: 0xf3d27a, rim: 0x22d3ee, fill: 0x1b2848, ringOpacity: 0.55, dot: 0xd4af37, dotAlt: 0x7fd8e8,
      skyTop: 0x04060d, skyBottom: 0x0b1226, bloom: 0.52, atmosphere: 0x22d3ee,
    },
  },
  dawn: {
    css: "radial-gradient(ellipse 80% 70% at 60% 20%, rgba(246,231,184,0.16), transparent 60%), radial-gradient(ellipse 70% 60% at 30% 80%, rgba(139,92,246,0.10), transparent 60%)",
    three: {
      key: 0xf6e7b8, rim: 0x8b5cf6, fill: 0x24345c, ringOpacity: 0.5, dot: 0xe7c55c, dotAlt: 0xb39ddb,
      skyTop: 0x080a18, skyBottom: 0x2a1f42, bloom: 0.44, atmosphere: 0x8b5cf6,
    },
  },
  day: {
    css: "radial-gradient(ellipse 80% 70% at 60% 20%, rgba(148,197,255,0.14), transparent 60%), radial-gradient(ellipse 70% 60% at 30% 80%, rgba(34,197,94,0.08), transparent 60%)",
    three: {
      key: 0xffffff, rim: 0x7dd3fc, fill: 0x33456e, ringOpacity: 0.42, dot: 0xd4af37, dotAlt: 0x93c5fd,
      skyTop: 0x0a1424, skyBottom: 0x1d3a5c, bloom: 0.34, atmosphere: 0x7dd3fc,
    },
  },
  dusk: {
    css: "radial-gradient(ellipse 80% 70% at 60% 20%, rgba(212,175,55,0.14), transparent 60%), radial-gradient(ellipse 70% 60% at 30% 80%, rgba(239,68,68,0.08), transparent 60%)",
    three: {
      key: 0xe7c55c, rim: 0xf87171, fill: 0x1b2848, ringOpacity: 0.5, dot: 0xd4af37, dotAlt: 0xf0a5a5,
      skyTop: 0x07060e, skyBottom: 0x3d1f2e, bloom: 0.46, atmosphere: 0xf87171,
    },
  },
};

/** Seasonal tint applied to atmosphere + key light (decorative only). */
export const SEASON_TINTS: Record<SeasonPreset, { tint: number; strength: number }> = {
  spring: { tint: 0x9fffc4, strength: 0.35 },
  summer: { tint: 0xffd98a, strength: 0.3 },
  autumn: { tint: 0xffab7a, strength: 0.4 },
  winter: { tint: 0xa8d4ff, strength: 0.45 },
};

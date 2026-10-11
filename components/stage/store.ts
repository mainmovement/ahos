/**
 * M-D5.2 — the stage's UI-only store.
 *
 * REFERENCE_BOARD ref 8: "One small client store for UI state (theme, sound,
 * motion, quality, selected entity). It must never hold authority data; that
 * stays server-derived from `/api/command`." This is that store. Nothing in it
 * is a fact about a market, a token, or a decision; every field is a preference
 * or a presentation state the user can set and the stage can read.
 *
 * The tier lives here because it is a *rendering* decision (how many particles
 * to draw), never an authority one. It arrives from `probeQuality()` already
 * resolved by the pure `resolveTier`, so the store only carries the verdict.
 *
 * Persistence is `localStorage` and is best-effort: a private window or a denied
 * storage permission simply starts from defaults. Nothing here is worth an error
 * toast, and nothing here is worth a network round-trip.
 */
import { create } from "zustand";

import { resolveTheme, type ThemeName } from "@/dashboard_tokens";
import type { RenderTier, TierVerdict } from "@/components/stage/quality";

/** A null verdict means the probe has not run yet — not "T0". */
export interface StageState {
  theme: ThemeName;
  /** The measured verdict, or null until `probeQuality()` lands. */
  verdict: TierVerdict | null;
  /** Convenience: the resolved tier, defaulting to the safest rung. */
  tier: RenderTier;
  muted: boolean;
  /** 0–100. Spec §8.2: the default on first unmute is 40. */
  volume: number;
  /** Honours the OS setting *or* the in-app toggle (spec §11). */
  reducedMotion: boolean;
  /** The stage is mounted and has rendered at least one frame. */
  ready: boolean;
  /** The WebGL context was lost and the 2D fallback is in force (M-D5.4). */
  contextLost: boolean;
  setTheme: (t: string | null | undefined) => void;
  setVerdict: (v: TierVerdict) => void;
  setMuted: (m: boolean) => void;
  setVolume: (v: number) => void;
  setReducedMotion: (r: boolean) => void;
  setReady: (r: boolean) => void;
  setContextLost: (lost: boolean) => void;
}

const MOTION_KEY = "ahos.stage.reducedMotion";
const MUTE_KEY = "ahos.stage.muted";
const VOLUME_KEY = "ahos.stage.volume";
const THEME_KEY = "ahos.stage.theme";

function readStored(key: string): string | null {
  try {
    return globalThis.localStorage?.getItem(key) ?? null;
  } catch {
    return null;
  }
}

function writeStored(key: string, value: string): void {
  try {
    globalThis.localStorage?.setItem(key, value);
  } catch {
    // unwritable storage: the preference just will not survive a reload
  }
}

/**
 * The OS reduced-motion preference, read once at construction. The store keeps
 * its own copy so the in-app toggle can override it, per spec §11.
 */
function initialReducedMotion(): boolean {
  if (typeof window === "undefined" || typeof window.matchMedia !== "function") return false;
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

function initialTheme(): ThemeName {
  return resolveTheme(readStored(THEME_KEY));
}

function initialMuted(): boolean {
  const raw = readStored(MUTE_KEY);
  // Spec §8.2: "Starts muted." Absent storage means muted, not "last session".
  return raw === null ? true : raw !== "false";
}

function initialVolume(): number {
  const raw = readStored(VOLUME_KEY);
  const n = raw === null ? NaN : Number(raw);
  if (!Number.isFinite(n)) return 40;
  return Math.min(100, Math.max(0, Math.round(n)));
}

export const useStageStore = create<StageState>((set) => ({
  theme: initialTheme(),
  verdict: null,
  // Until the probe lands, assume the floor — the ladder only ever runs down.
  tier: "T1",
  muted: initialMuted(),
  volume: initialVolume(),
  reducedMotion: initialReducedMotion(),
  ready: false,
  contextLost: false,

  setTheme: (t) => {
    const theme = resolveTheme(t);
    writeStored(THEME_KEY, theme);
    set({ theme });
  },
  setVerdict: (v) => set({ verdict: v, tier: v.tier }),
  setMuted: (m) => {
    writeStored(MUTE_KEY, String(m));
    set({ muted: m });
  },
  setVolume: (v) => {
    const clamped = Math.min(100, Math.max(0, Math.round(v)));
    writeStored(VOLUME_KEY, String(clamped));
    set({ volume: clamped });
  },
  setReducedMotion: (r) => {
    writeStored(MOTION_KEY, String(r));
    set({ reducedMotion: r });
  },
  setReady: (r) => set({ ready: r }),
  setContextLost: (lost) => set({ contextLost: lost }),
}));

/**
 * The motion budget for a tier, in one place, so a scene reads "how much may I
 * move?" instead of branching on the tier at every animated object.
 *
 * Reduced motion zeroes the budget regardless of tier (spec §11: combinable with
 * any tier), and T0 has no budget at all because it has no 3D.
 */
export function motionBudget(tier: RenderTier, reducedMotion: boolean): {
  rotate: number;
  particles: number;
  drift: number;
  /** How many dots the M-D6 globe draws. Always under the 30k the owner capped a
   *  point globe at; one draw call, so even T1 may have a populated globe. */
  globePoints: number;
} {
  if (reducedMotion) {
    // Nothing moves, but a static globe is still a globe: the density is the T1
    // count and the rotation is the only thing the preference takes away.
    return { rotate: 0, particles: 0, drift: 0, globePoints: 6000 };
  }
  switch (tier) {
    case "T3":
      return { rotate: 1, particles: 900, drift: 1, globePoints: 24000 };
    case "T2":
      return { rotate: 1, particles: 450, drift: 0.6, globePoints: 14000 };
    case "T1":
      // §11 Low-power: no loose particles; DPR 1. The globe is geometry, not
      // particles, and one draw call of 6k dots is not what T1 is protecting
      // against — so the centrepiece stays populated and only the extras go.
      return { rotate: 0.5, particles: 0, drift: 0.2, globePoints: 6000 };
    case "T0":
    default:
      return { rotate: 0, particles: 0, drift: 0, globePoints: 0 };
  }
}

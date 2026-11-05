"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import type {
  AmbiencePreset,
  Density,
  MotionPreference,
  RefreshInterval,
  SeasonPreset,
  SceneView,
} from "@/lib/types";

const STORAGE_KEY = "ahos-deck-prefs.v1";

export interface DeckPrefs {
  density: Density;
  motion: MotionPreference;
  chartWatermark: boolean;
  chartGrid: boolean;
  refreshInterval: RefreshInterval;
  sceneEnabled: boolean;
  ambience: AmbiencePreset;
  season: SeasonPreset;
  sceneView: SceneView;
  datasetBannerDismissed: boolean;
}

export const DEFAULT_PREFS: DeckPrefs = {
  density: "comfortable",
  motion: "system",
  chartWatermark: true,
  chartGrid: true,
  refreshInterval: "off",
  sceneEnabled: true,
  ambience: "night",
  season: "spring",
  sceneView: "room",
  datasetBannerDismissed: false,
};

interface SettingsContextValue {
  prefs: DeckPrefs;
  setPref: <K extends keyof DeckPrefs>(key: K, value: DeckPrefs[K]) => void;
  resetPrefs: () => void;
  hydrated: boolean;
  /** Effective reduced-motion: explicit override OR system preference. */
  reducedMotion: boolean;
}

const SettingsContext = createContext<SettingsContextValue | null>(null);

function readStored(): DeckPrefs {
  if (typeof window === "undefined") return DEFAULT_PREFS;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return DEFAULT_PREFS;
    const parsed: unknown = JSON.parse(raw);
    if (parsed === null || typeof parsed !== "object") return DEFAULT_PREFS;
    return { ...DEFAULT_PREFS, ...(parsed as Partial<DeckPrefs>) };
  } catch {
    return DEFAULT_PREFS;
  }
}

export function SettingsProvider({ children }: { children: ReactNode }) {
  const [prefs, setPrefs] = useState<DeckPrefs>(DEFAULT_PREFS);
  const [systemReduced, setSystemReduced] = useState(false);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    setPrefs(readStored());
    setHydrated(true);
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    setSystemReduced(mq.matches);
    const onChange = (e: MediaQueryListEvent) => setSystemReduced(e.matches);
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, []);

  useEffect(() => {
    if (!hydrated) return;
    document.documentElement.dataset.density = prefs.density;
    document.documentElement.dataset.motion = prefs.motion === "reduce" ? "reduce" : "full";
  }, [prefs.density, prefs.motion, hydrated]);

  const setPref = useCallback(<K extends keyof DeckPrefs>(key: K, value: DeckPrefs[K]) => {
    setPrefs((prev) => {
      const next = { ...prev, [key]: value };
      try {
        window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
      } catch {
        /* storage unavailable — prefs stay in-memory */
      }
      return next;
    });
  }, []);

  const resetPrefs = useCallback(() => {
    setPrefs(DEFAULT_PREFS);
    try {
      window.localStorage.removeItem(STORAGE_KEY);
    } catch {
      /* ignore */
    }
  }, []);

  const reducedMotion = prefs.motion === "reduce" || (prefs.motion === "system" && systemReduced);

  const value = useMemo<SettingsContextValue>(
    () => ({ prefs, setPref, resetPrefs, hydrated, reducedMotion }),
    [prefs, setPref, resetPrefs, hydrated, reducedMotion],
  );

  return <SettingsContext.Provider value={value}>{children}</SettingsContext.Provider>;
}

export function useSettings(): SettingsContextValue {
  const ctx = useContext(SettingsContext);
  if (!ctx) throw new Error("useSettings must be used inside SettingsProvider");
  return ctx;
}

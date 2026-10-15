"use client";

import { createContext, useContext, useEffect, useMemo, useState, useSyncExternalStore, type ReactNode } from "react";
import {
  COOKIE_KEY,
  DEFAULT_SETTINGS,
  QUALITY_BUDGETS,
  STORAGE_KEY,
  sanitizeSettings,
  serializeCookieSettings,
  type QualityBudget,
  type QualityProfile,
  type Settings,
} from "./types";

interface SettingsContextValue {
  settings: Settings;
  update: (patch: Partial<Settings>) => void;
  /** Resolved motion preference (explicit setting or OS preference). */
  reducedMotion: boolean;
  budget: QualityBudget;
  dir: "rtl" | "ltr";
}

const SettingsContext = createContext<SettingsContextValue | null>(null);

function detectQuality(): QualityProfile {
  const nav = navigator as Navigator & { deviceMemory?: number };
  const cores = nav.hardwareConcurrency ?? 8;
  const mem = nav.deviceMemory ?? 8;
  const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reduce || cores <= 2 || mem <= 2) return "low";
  if (cores <= 4 || mem <= 4) return "balanced";
  return "high";
}

function applyToDocument(s: Settings) {
  const html = document.documentElement;
  html.lang = s.locale;
  html.dir = s.locale === "fa" ? "rtl" : "ltr";
  html.dataset.quality = s.quality;
  html.dataset.theme = s.theme;
  html.dataset.motion = s.motion;
}

/**
 * External store for settings. localStorage is the client source of truth;
 * a cookie mirrors the SSR-relevant subset so the server renders the right
 * <html lang/dir/data-*> on the next request (no flash, no hydration drift).
 */
function createSettingsStore(serverInitial: Settings, hasCookie: boolean) {
  let state = serverInitial;
  let loaded = false;
  const listeners = new Set<() => void>();

  const load = () => {
    if (loaded || typeof window === "undefined") return;
    loaded = true;
    try {
      const raw = window.localStorage.getItem(STORAGE_KEY);
      if (raw) state = { ...state, ...sanitizeSettings(JSON.parse(raw)) };
      else if (!hasCookie) state = { ...state, quality: detectQuality() };
    } catch {
      /* storage unavailable — keep server state */
    }
  };

  const persist = (s: Settings) => {
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(s));
    } catch {
      /* ignore quota/private-mode errors */
    }
    document.cookie = `${COOKIE_KEY}=${serializeCookieSettings(s)}; path=/; max-age=31536000; samesite=lax`;
  };

  return {
    subscribe(cb: () => void) {
      listeners.add(cb);
      return () => {
        listeners.delete(cb);
      };
    },
    getSnapshot(): Settings {
      load();
      return state;
    },
    getServerSnapshot(): Settings {
      return serverInitial;
    },
    set(patch: Partial<Settings>) {
      load();
      state = { ...state, ...patch };
      persist(state);
      listeners.forEach((l) => l());
    },
  };
}

function subscribeReducedMotion(cb: () => void) {
  const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
  mq.addEventListener("change", cb);
  return () => mq.removeEventListener("change", cb);
}
const getReducedMotion = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const getReducedMotionServer = () => false;

export function SettingsProvider({ initial, children }: { initial: Partial<Settings>; children: ReactNode }) {
  const [store] = useState(() => createSettingsStore({ ...DEFAULT_SETTINGS, ...initial }, Object.keys(initial).length > 0));
  const settings = useSyncExternalStore(store.subscribe, store.getSnapshot, store.getServerSnapshot);
  const osReduced = useSyncExternalStore(subscribeReducedMotion, getReducedMotion, getReducedMotionServer);

  useEffect(() => {
    applyToDocument(settings);
  }, [settings]);

  const value = useMemo<SettingsContextValue>(() => {
    const reducedMotion = settings.motion === "reduced" || (settings.motion === "system" && osReduced);
    return {
      settings,
      update: store.set,
      reducedMotion,
      budget: QUALITY_BUDGETS[settings.quality],
      dir: settings.locale === "fa" ? "rtl" : "ltr",
    };
  }, [settings, store, osReduced]);

  return <SettingsContext.Provider value={value}>{children}</SettingsContext.Provider>;
}

export function useSettings(): SettingsContextValue {
  const ctx = useContext(SettingsContext);
  if (!ctx) throw new Error("useSettings must be used inside <SettingsProvider>");
  return ctx;
}

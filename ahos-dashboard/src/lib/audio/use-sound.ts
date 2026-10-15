"use client";

import { useCallback, useEffect } from "react";
import { useSettings } from "@/lib/settings/provider";
import { soundEngine, type SoundName } from "./engine";

/** Keeps the engine in sync with settings; mount once (AppShell). */
export function useSoundSync() {
  const { settings } = useSettings();
  useEffect(() => {
    soundEngine.configure({ muted: settings.muted, volume: settings.volume });
    if (!settings.muted && settings.ambient) soundEngine.startAmbient();
    else soundEngine.stopAmbient();
  }, [settings.muted, settings.volume, settings.ambient]);
}

/** Returns a stable `play(name)` that respects mute + UI-sounds settings. */
export function useSound() {
  const { settings } = useSettings();
  const enabled = !settings.muted && settings.uiSounds;
  return useCallback(
    (name: SoundName) => {
      if (enabled) soundEngine.play(name);
    },
    [enabled],
  );
}

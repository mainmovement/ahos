"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { getMuted, primeAudio, setMuted, sfx } from "@/lib/useSound";

type AudioCtxValue = {
  muted: boolean;
  toggleMuted: () => void;
  play: typeof sfx;
};

const AudioCtx = createContext<AudioCtxValue | null>(null);

export function AudioProvider({ children }: { children: React.ReactNode }) {
  const [muted, setMutedState] = useState(false);

  useEffect(() => {
    setMutedState(getMuted());
    const prime = () => {
      primeAudio();
      window.removeEventListener("pointerdown", prime);
      window.removeEventListener("keydown", prime);
    };
    window.addEventListener("pointerdown", prime);
    window.addEventListener("keydown", prime);
    return () => {
      window.removeEventListener("pointerdown", prime);
      window.removeEventListener("keydown", prime);
    };
  }, []);

  const toggleMuted = useCallback(() => {
    setMutedState((prev) => {
      const next = !prev;
      setMuted(next);
      if (!next) sfx.toggleOn();
      return next;
    });
  }, []);

  const value = useMemo(() => ({ muted, toggleMuted, play: sfx }), [muted, toggleMuted]);

  return <AudioCtx.Provider value={value}>{children}</AudioCtx.Provider>;
}

export function useAudio() {
  const ctx = useContext(AudioCtx);
  if (!ctx) throw new Error("useAudio must be used within AudioProvider");
  return ctx;
}

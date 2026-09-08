"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { isAudioEnabled, play, setAudioEnabled, startAmbient, stopAmbient, unlockAudio } from "@/components/audio-engine";

type AudioApi = {
  enabled: boolean;
  toggle: () => void;
  play: typeof play;
};

const AudioCtx = createContext<AudioApi>({
  enabled: true,
  toggle: () => {},
  play,
});

export function useAudio() {
  return useContext(AudioCtx);
}

export function Providers({ children }: { children: React.ReactNode }) {
  const [enabled, setEnabled] = useState(true);
  const [hot, setHot] = useState(false);

  useEffect(() => {
    document.body.classList.add("ahos-cursor");
    const saved = localStorage.getItem("ahos-audio");
    if (saved === "off") {
      setEnabled(false);
      setAudioEnabled(false);
    }
    const onFirst = async () => {
      await unlockAudio();
      if (isAudioEnabled()) startAmbient();
    };
    window.addEventListener("pointerdown", onFirst, { once: true });

    const dot = document.getElementById("ahos-dot");
    const ring = document.getElementById("ahos-ring");
    let x = window.innerWidth / 2;
    let y = window.innerHeight / 2;
    let rx = x;
    let ry = y;
    const move = (e: PointerEvent) => {
      x = e.clientX;
      y = e.clientY;
      if (dot) {
        dot.style.left = `${x}px`;
        dot.style.top = `${y}px`;
      }
      const t = e.target as HTMLElement | null;
      const isHot = !!t?.closest("a,button,input,textarea,[data-hot]");
      setHot(isHot);
    };
    const loop = () => {
      rx += (x - rx) * 0.18;
      ry += (y - ry) * 0.18;
      if (ring) {
        ring.style.left = `${rx}px`;
        ring.style.top = `${ry}px`;
      }
      requestAnimationFrame(loop);
    };
    window.addEventListener("pointermove", move);
    const raf = requestAnimationFrame(loop);
    return () => {
      window.removeEventListener("pointermove", move);
      cancelAnimationFrame(raf);
      document.body.classList.remove("ahos-cursor");
    };
  }, []);

  const toggle = useCallback(() => {
    setEnabled((prev) => {
      const next = !prev;
      setAudioEnabled(next);
      localStorage.setItem("ahos-audio", next ? "on" : "off");
      if (next) {
        void unlockAudio().then(() => startAmbient());
        play("success");
      } else {
        stopAmbient();
      }
      return next;
    });
  }, []);

  const api = useMemo(() => ({ enabled, toggle, play }), [enabled, toggle]);

  return (
    <AudioCtx.Provider value={api}>
      <div className="grain" />
      <div className="scan" />
      <div id="ahos-dot" className="ahos-cursor-dot" />
      <div id="ahos-ring" className={`ahos-cursor-ring${hot ? " hot" : ""}`} />
      {children}
    </AudioCtx.Provider>
  );
}

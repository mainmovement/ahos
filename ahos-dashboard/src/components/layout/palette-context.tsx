"use client";

import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

interface PaletteCtx {
  open: boolean;
  setOpen: (open: boolean) => void;
}

const Ctx = createContext<PaletteCtx | null>(null);

export function PaletteProvider({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen((o) => !o);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);
  const value = useMemo(() => ({ open, setOpen }), [open]);
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function usePalette(): PaletteCtx {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("usePalette must be used inside <PaletteProvider>");
  return ctx;
}

/** Globe command bus: lets the palette / chat drive the globe without coupling. */
export type GlobeCommand = "fly-iran" | "back-global" | "reset";
export const GLOBE_EVENT = "ahos:globe";
export function sendGlobeCommand(cmd: GlobeCommand) {
  window.dispatchEvent(new CustomEvent<GlobeCommand>(GLOBE_EVENT, { detail: cmd }));
}

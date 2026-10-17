// FILE: 13_missions_batch3/src/lib/useFlags.ts
"use client";
import { useEffect, useState } from "react";
import { DEFAULT_FLAGS, readFlags, type PageFlags } from "./flags";

/**
 * Hydration-safe flags hook: renders defaults on the server, reads the real
 * query flags (?demo=1, ?violation=1, ?tier=0|1|2, ?state=…) after mount.
 */
export function useFlags(): PageFlags {
  const [flags, setFlags] = useState<PageFlags>(DEFAULT_FLAGS);
  useEffect(() => {
    const update = () => setFlags(readFlags());
    update();
    window.addEventListener("popstate", update);
    return () => window.removeEventListener("popstate", update);
  }, []);
  return flags;
}

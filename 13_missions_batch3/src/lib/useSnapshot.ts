// FILE: 13_missions_batch3/src/lib/useSnapshot.ts
"use client";
/**
 * Tiny client-side snapshot loader. Pages are read-only displays: this hook
 * fetches once through the page adapter and reports a display phase. It never
 * throws — contract failures surface as UNAVAILABLE.
 */
import { useEffect, useState } from "react";

export type SnapshotPhase = "LOADING" | "READY" | "ERROR";

export function useSnapshot<T>(load: () => Promise<T>): { phase: SnapshotPhase; data: T | null } {
  const [phase, setPhase] = useState<SnapshotPhase>("LOADING");
  const [data, setData] = useState<T | null>(null);

  useEffect(() => {
    let alive = true;
    setPhase("LOADING");
    load()
      .then((snap) => {
        if (!alive) return;
        setData(snap);
        setPhase("READY");
      })
      .catch(() => {
        if (!alive) return;
        setData(null);
        setPhase("ERROR");
      });
    return () => {
      alive = false;
    };
    // `load` is intentionally called once per mount.
  }, []);

  return { phase, data };
}

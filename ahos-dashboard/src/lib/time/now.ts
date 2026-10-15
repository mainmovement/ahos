"use client";

import { useSyncExternalStore } from "react";

/**
 * Shared 1 Hz clock. One interval for the whole app; components subscribe via
 * useSyncExternalStore. Returns null during SSR/hydration so time-dependent
 * text never causes hydration mismatches.
 */
let current = 0;
let timer: ReturnType<typeof setInterval> | undefined;
const listeners = new Set<() => void>();

function tick() {
  current = Date.now();
  listeners.forEach((l) => l());
}

function subscribe(cb: () => void) {
  listeners.add(cb);
  if (!timer) {
    current = Date.now();
    timer = setInterval(tick, 1000);
  }
  return () => {
    listeners.delete(cb);
    if (listeners.size === 0 && timer) {
      clearInterval(timer);
      timer = undefined;
    }
  };
}

function getSnapshot(): number {
  if (current === 0) current = Date.now();
  return current;
}

function getServerSnapshot(): number | null {
  return null;
}

export function useNow(): number | null {
  return useSyncExternalStore<number | null>(subscribe, getSnapshot, getServerSnapshot);
}

/** Minute-resolution variant (re-renders once per minute). */
let currentMinute = 0;
function getMinuteSnapshot(): number {
  const m = Math.floor(getSnapshot() / 60000) * 60000;
  if (m !== currentMinute) currentMinute = m;
  return currentMinute;
}

export function useNowMinute(): number | null {
  return useSyncExternalStore<number | null>(subscribe, getMinuteSnapshot, getServerSnapshot);
}

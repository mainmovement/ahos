"use client";

/**
 * A clock that exists only on the client.
 *
 * Server render and the first client render both use `null`, so markup is deterministic and
 * hydration cannot mismatch. After mount the browser clock is adopted (and refreshed every 30 s
 * while the tab is visible) so Persian relative timestamps ("۳ دقیقه پیش") stay honest.
 *
 * Passing `fixed` pins the clock: tests and screenshots get reproducible text, and the hook never
 * starts a timer.
 */

import { useEffect, useState } from "react";

const REFRESH_MS = 30_000;

export function useClientClock(fixed?: number): number | null {
  const [internal, setInternal] = useState<number | null>(null);

  useEffect(() => {
    if (fixed !== undefined) return;
    let cancelled = false;
    const tick = () => {
      if (!cancelled && document.visibilityState === "visible") setInternal(Date.now());
    };
    // Adopt the browser clock as soon as the first frame is ready, then keep it fresh.
    const first = window.setTimeout(tick, 0);
    const interval = window.setInterval(tick, REFRESH_MS);
    return () => {
      cancelled = true;
      window.clearTimeout(first);
      window.clearInterval(interval);
    };
  }, [fixed]);

  return fixed !== undefined ? fixed : internal;
}

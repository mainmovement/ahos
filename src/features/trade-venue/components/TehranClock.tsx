"use client";

import { useMemo, useSyncExternalStore } from "react";
import { TEHRAN_ZONE_LABEL, tehranParts } from "@/src/features/trade-venue/logic/format";
import { MISSING_GLYPH } from "@/src/features/trade-venue/logic/truth";

/**
 * Tehran wall-clock for the topbar.
 *
 * Truthfulness details:
 *  · the server snapshot and the very first client paint show «—»: the ambient
 *    clock is not part of the data contract, and every *data* age label on the
 *    page is derived from the bundle's own timestamps instead;
 *  · under `prefers-reduced-motion` the clock drops to minute resolution and
 *    refreshes every 20s, so no digit "counts up" on a sensitive display;
 *  · implemented with `useSyncExternalStore` (a real subscription) rather than
 *    an effect that calls setState, so there is no cascading render.
 */

let motionQuery: MediaQueryList | null = null;

function getMotionQuery(): MediaQueryList | null {
  if (typeof window === "undefined" || typeof window.matchMedia !== "function") return null;
  motionQuery ??= window.matchMedia("(prefers-reduced-motion: reduce)");
  return motionQuery;
}

function subscribeMotion(callback: () => void): () => void {
  const query = getMotionQuery();
  if (!query) return () => undefined;
  query.addEventListener("change", callback);
  return () => query.removeEventListener("change", callback);
}

function getMotionSnapshot(): boolean {
  return getMotionQuery()?.matches ?? false;
}

function getMotionServerSnapshot(): boolean {
  return false;
}

export function TehranClock({ label = TEHRAN_ZONE_LABEL }: { label?: string }) {
  const reduced = useSyncExternalStore(
    subscribeMotion,
    getMotionSnapshot,
    getMotionServerSnapshot,
  );

  const subscribeTime = useMemo(() => {
    const period = reduced ? 20_000 : 1_000;
    return (callback: () => void) => {
      const timer = window.setInterval(callback, period);
      return () => window.clearInterval(timer);
    };
  }, [reduced]);

  /* Seconds since epoch as the store value: cheap, stable and serialisable. */
  const epochSeconds = useSyncExternalStore(
    subscribeTime,
    () => Math.floor(Date.now() / 1000),
    () => 0,
  );

  const now = epochSeconds > 0 ? new Date(epochSeconds * 1000) : null;
  const parts = now ? tehranParts(now) : null;

  return (
    <div className="ah-clock" data-clock="tehran">
      <span className="ah-clock__time" data-clock-time="" dir="ltr">
        {parts ? parts.time.slice(0, reduced ? 5 : 8) : MISSING_GLYPH}
      </span>
      <span className="ah-clock__zone">
        {label}
        {reduced ? " · دقت دقیقه" : ""} · {parts ? parts.weekday : MISSING_GLYPH}{" "}
        {parts ? parts.date : ""}
      </span>
    </div>
  );
}

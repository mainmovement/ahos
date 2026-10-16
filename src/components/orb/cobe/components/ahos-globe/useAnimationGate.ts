"use client";

/**
 * Decides whether the globe is allowed to animate.
 *
 * Three independent brakes, all required by the brief:
 *  - the tab is hidden  (`document.visibilityState`),
 *  - the element is off-screen (`IntersectionObserver`),
 *  - the user asked for less motion (`prefers-reduced-motion: reduce`).
 *
 * The decision itself lives in the pure `shouldAnimate()` helper so it can be tested without a DOM.
 */

import { useEffect, useState } from "react";

export type AnimationGateInput = {
  /** Motion is even possible for this render (WebGL present, globe mode, not frozen). */
  enabled: boolean;
  hidden: boolean;
  offscreen: boolean;
  reducedMotion: boolean;
};

/** Pure decision function — unit-tested in `tests/animation-gate.test.ts`. */
export function shouldAnimate(input: AnimationGateInput): boolean {
  return input.enabled && !input.hidden && !input.offscreen && !input.reducedMotion;
}

export type AnimationGateState = {
  animate: boolean;
  hidden: boolean;
  offscreen: boolean;
  reducedMotion: boolean;
};

export function useAnimationGate(
  targetRef: React.RefObject<Element | null>,
  enabled: boolean,
): AnimationGateState {
  const [hidden, setHidden] = useState(false);
  const [offscreen, setOffscreen] = useState(false);
  const [reducedMotion, setReducedMotion] = useState(false);
  useEffect(() => {
    if (typeof document === "undefined") return;
    const update = () => setHidden(document.visibilityState === "hidden");
    update();
    document.addEventListener("visibilitychange", update);
    return () => document.removeEventListener("visibilitychange", update);
  }, []);

  useEffect(() => {
    if (typeof window === "undefined" || typeof window.matchMedia !== "function") return;
    const query = window.matchMedia("(prefers-reduced-motion: reduce)");
    const update = () => setReducedMotion(query.matches);
    update();
    if (typeof query.addEventListener === "function") {
      query.addEventListener("change", update);
      return () => query.removeEventListener("change", update);
    }
    // Safari < 14 and older jsdom implementations.
    query.addListener(update);
    return () => query.removeListener(update);
  }, []);

  useEffect(() => {
    const node = targetRef.current;
    if (!node || typeof IntersectionObserver !== "function") return;
    const observer = new IntersectionObserver(
      (entries) => {
        const entry = entries[entries.length - 1];
        if (entry) setOffscreen(!entry.isIntersecting);
      },
      { threshold: 0.05 },
    );
    observer.observe(node);
    return () => observer.disconnect();
  }, [targetRef]);

  return {
    hidden,
    offscreen,
    reducedMotion,
    animate: shouldAnimate({ enabled, hidden, offscreen, reducedMotion }),
  };
}

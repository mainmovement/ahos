"use client";

/**
 * M-D5.2 — the lazy boundary around the 3D stage.
 *
 * Spec §12: the 3D chunk ("three + r3f + drei + postprocessing + scene") must be
 * `dynamic(() => import(...), {ssr:false})` so it is a separate bundle that the
 * 2D shell never pays for. Spec §11 sharpens it: at T0 "the three.js chunk is
 * never downloaded" — so the shell does not render this component at all when
 * the probe returns T0, and `Stage` can assume a real backend once mounted.
 *
 * `ssr: false` keeps `three` off the server. The SSR build has no WebGL and no
 * business importing a renderer; the shell renders its own 2D markup and the
 * stage appears as a client island.
 *
 * The fallback is a Persian loading line, not a spinner with a fake percentage
 * and not a skeleton that implies data is already there (spec §7: loading copy
 * is "در حال دریافت…" and shows no numbers).
 */
import dynamic from "next/dynamic";

export default dynamic(() => import("@/components/stage/Stage"), {
  ssr: false,
  loading: () => (
    <div
      className="stage-fallback"
      role="status"
      aria-live="polite"
      dir="rtl"
      lang="fa"
    >
      در حال آماده‌سازیِ صحنه…
    </div>
  ),
});

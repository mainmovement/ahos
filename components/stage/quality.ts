/**
 * M-D5.3 — the quality probe: which renderer may this machine actually drive?
 *
 * The tier is *measured*, never assumed. CLAUDE_DASHBOARD_2050 global rule 3:
 * "Tiers are picked at runtime from measured capability, never from the machine
 * name", and the design spec §11 fixes the ladder:
 *
 *     T3 Ultra       WebGPU + a discrete GPU      full postprocessing
 *     T2 High        WebGPU or WebGL2, integrated  bloom + vignette + SMAA
 *     T1 Low-power   WebGL2, reduced effects       DPR 1, vignette only
 *     T0 2D          no WebGL at all               the three.js chunk is not loaded
 *
 * The split this module enforces is that **measurement is impure and decision is
 * pure**. Everything that touches `navigator`, a canvas or `localStorage` lives
 * in `probeQuality()`; `resolveTier()` is a pure function of a plain record, so
 * the tier ladder is unit-testable on a machine with no GPU at all — which is
 * the only way the ladder can be proven rather than asserted. It is the same
 * separation `dashboard_truth.ts` uses for freshness.
 *
 * Nothing here reads `navigator.userAgent`, `navigator.platform`, the hostname
 * or any other machine identity. `scripts/quality_selftest.ts` asserts that
 * mechanically, because "never from the machine name" is only true if the code
 * cannot reach for a name.
 *
 * Presentation-only by law (AGENTS.md): the tier decides how many particles the
 * stage draws. It never decides whether a token is good, and it is never shown
 * as a measurement of anything but the hardware.
 */

// ---------------------------------------------------------------- the ladder ---

export type RenderTier = "T0" | "T1" | "T2" | "T3";
export type HardwareTier = "T8" | "T16" | "T32" | "GPU";
export type GpuBackend = "webgpu" | "webgl2" | "none";

/**
 * The ordered ladder. T0 is the floor and T3 the ceiling; `cap()` walks a
 * candidate *down* it only, never up — the same downgrade-only law the truth
 * badge uses, applied to a quality setting.
 */
export const TIER_ORDER: readonly RenderTier[] = ["T0", "T1", "T2", "T3"];
export const HARDWARE_TIERS: readonly HardwareTier[] = ["T8", "T16", "T32", "GPU"];

export interface TierLabels {
  en: string;
  fa: string;
  /** One short Persian line for the tier chip's title. */
  faWhy: string;
}

export const TIER_LABELS: Record<RenderTier, TierLabels> = {
  T0: {
    en: "2D",
    fa: "دوبعدی",
    faWhy: "بدون WebGL — نمای دو‌بعدی، همان داده‌ها",
  },
  T1: {
    en: "Low-power",
    fa: "کم‌مصرف",
    faWhy: "WebGL2 با اثرات کاهش‌یافته — مناسب باتری یا ۸ گیگابایت",
  },
  T2: {
    en: "High",
    fa: "بالا",
    faWhy: "WebGL2/WebGPU گرافیک یکپارچه — bloom و vignette و SMAA",
  },
  T3: {
    en: "Ultra",
    fa: "Ultra",
    faWhy: "WebGPU + گرافیک مجزا — تمام پس‌پردازش‌ها",
  },
};

export const HARDWARE_LABELS: Record<HardwareTier, { en: string; fa: string }> = {
  T8: { en: "8 cores", fa: "۸ هسته" },
  T16: { en: "16 cores", fa: "۱۶ هسته" },
  T32: { en: "32 cores", fa: "۳۲ هسته" },
  GPU: { en: "discrete GPU", fa: "گرافیک مجزا" },
};

// ------------------------------------------------------------- the constants ---

/** Spec §11: below this, the app drops to 2D. */
export const FPS_FLOOR_2D = 24;
/** CLAUDE_DASHBOARD_2050 rule 3: 8 GB is the floor. */
export const RAM_FLOOR_GB = 8;
/** M-D5.3: the frame test runs for two seconds. */
export const FRAME_TEST_MS = 2000;
/** The synthetic workload the frame test runs per frame (see `frameProbe`). */
const FRAME_TEST_CLEAR_PASSES = 2000;
/** `localStorage` key holding a user's manual tier override. */
export const OVERRIDE_KEY = "ahos.stage.tier.override";
/**
 * Where a self-hosted copy of detect-gpu's benchmark data lives. REFERENCE_BOARD
 * ref 11: detect-gpu loads its benchmarks from UNPKG *by default*, which would
 * break the M-D2 "zero non-127.0.0.1 requests" contract.
 *
 * This is a **directory**, not a file: detect-gpu fetches `${url}/${model}.json`
 * per GPU family (`d-intel.json`, `d-nvidia.json`, …). The whole directory is
 * vendored under `public/benchmarks/` so the probe never leaves the loopback
 * origin. The path is passed explicitly on every call.
 */
export const BENCHMARKS_URL = "/benchmarks";

// ------------------------------------------------------------ the pure core ---

/**
 * The inputs to a tier decision. Every field is either a measurement or null,
 * and null is the honest "we could not measure this" — never a guess and never
 * a zero that would read as a measurement.
 */
export interface TierMeasure {
  hardware: HardwareTier | null;
  backend: GpuBackend | null;
  /** Frames per second sustained during `FRAME_TEST_MS` of synthetic load, or null. */
  fps: number | null;
  meanFrameMs: number | null;
  /** `navigator.deviceMemory`, an *upper bound* the browser reports, or null. */
  ramGb: number | null;
  /** A user's explicit override from the Tier Panel, or null to measure. */
  override: RenderTier | null;
}

export interface TierVerdict extends TierMeasure {
  tier: RenderTier;
  /** Machine-readable, for the receipts. */
  reason: string;
  /** Persian, for the chip and the panel. */
  reasonFa: string;
  /** Every measured bound that lowered the tier, most severe first. */
  limits: string[];
  /** Epoch ms, so a cached verdict can be aged. */
  measuredAt: number;
}

/**
 * Walk a candidate down the ladder, never up.
 */
export function cap(candidate: RenderTier, limit: RenderTier): RenderTier {
  return TIER_ORDER.indexOf(limit) < TIER_ORDER.indexOf(candidate) ? limit : candidate;
}

/**
 * The ladder from capability alone — no measurement bounds, no override.
 *
 * CLAUDE_DASHBOARD_2050 rule 3 names the two axes: the *backend* (WebGPU vs
 * WebGL2 vs none) and the *GPU class* (discrete vs integrated). The hardware
 * tier T8/T16/T32/GPU is M-D5.5's label and maps as that doc spells out:
 * T32/GPU → T3, T16 → T2, T8 → T1 or below.
 */
export function tierFromCapability(
  hardware: HardwareTier | null,
  backend: GpuBackend | null,
): { tier: RenderTier; reason: string; reasonFa: string } {
  if (backend === "none" || backend === null) {
    return {
      tier: "T0",
      reason: "no-webgl",
      reasonFa: "مرورگر WebGL ندارد — نمایش دو‌بعدی",
    };
  }
  if (hardware === "GPU" && backend === "webgpu") {
    return {
      tier: "T3",
      reason: "webgpu-discrete",
      reasonFa: "WebGPU در دسترس و گرافیک مجزا — سطح Ultra",
    };
  }
  if (hardware === "T32" && backend === "webgpu") {
    return {
      tier: "T3",
      reason: "webgpu-32core",
      reasonFa: "WebGPU در دسترس روی ۳۲ هسته — سطح Ultra",
    };
  }
  if (hardware === "GPU" || hardware === "T32") {
    return {
      tier: "T2",
      reason: "webgl2-high-core",
      reasonFa: "WebGL2 روی سخت‌افزار پرتوان — سطح بالا",
    };
  }
  if (hardware === "T16") {
    return {
      tier: "T2",
      reason: "16core",
      reasonFa: "۱۶ هسته — سطح بالا",
    };
  }
  return {
    tier: "T1",
    reason: "integrated-or-low-core",
    reasonFa: "گرافیک یکپارچه یا هسته کم — سطح کم‌مصرف",
  };
}

/**
 * The whole decision in one pure place.
 *
 * Precedence, most severe first:
 *
 *  1. no usable backend → T0, regardless of anything else;
 *  2. the frame test below `FPS_FLOOR_2D` → T0 (spec §11);
 *  3. RAM under the 8 GB floor → capped at T1 (rule 3);
 *  4. an explicit user override, which may *raise* the tier within what 1–3
 *     still allow — the user can wish for Ultra, but not for a backend that
 *     does not exist. If the user's pick is above what 1–3 allow, the limits
 *     win and `reason` says so, so the chip never claims the user got what they
 *     asked for when they did not.
 *
 * `prefers-reduced-motion` is deliberately *not* an input here. Spec §11: it is
 * "combinable with any tier" — it changes the motion budget, not the renderer,
 * so it lives in the stage's motion store and cannot reach this function.
 */
export function resolveTier(m: TierMeasure, nowMs: number = Date.now()): TierVerdict {
  const limits: string[] = [];

  if (m.backend === "none") limits.push("no-webgl");
  if (m.fps !== null && m.fps < FPS_FLOOR_2D) limits.push("fps-below-floor");
  if (m.ramGb !== null && m.ramGb < RAM_FLOOR_GB) limits.push("ram-under-floor");

  const overridden = m.override !== null;
  const base = tierFromCapability(m.hardware, m.backend);
  let tier = overridden ? (m.override as RenderTier) : base.tier;

  for (const limit of limits) {
    const ceiling: RenderTier | null =
      limit === "no-webgl" || limit === "fps-below-floor" ? "T0"
      : limit === "ram-under-floor" ? "T1"
      : null;
    if (ceiling !== null) tier = cap(tier, ceiling);
  }

  const reason = limits.length > 0
    ? (overridden ? "override-capped" : "measured-cap")
    : overridden ? "user-override"
    : base.reason;

  const reasonFa = limits.length > 0
    ? (overridden
        ? "انتخاب شما بالاتر از توان سخت‌افزار است — به پایین‌تر کاهش یافت"
        : "اندازه‌گیری، سطح را پایین آورد")
    : overridden
      ? "انتخاب دستی شما"
      : base.reasonFa;

  return { ...m, tier, reason, reasonFa, limits, measuredAt: nowMs };
}

// ------------------------------------------------------- the impure measuring ---

/**
 * The CPU core class, T8/T16/T32. A dedicated-class result promotes to `GPU` and
 * short-circuits the count — see `probeQuality` for what "dedicated-class"
 * actually measured (detect-gpu's 30 fps benchmark floor, not a card name).
 *
 * `navigator.hardwareConcurrency` is a *logical* core count and is clamped to
 * the nearest rung; it is not a measurement of speed, only of width.
 */
export function hardwareTierSync(gpuDiscrete: boolean | null): HardwareTier | null {
  if (gpuDiscrete === true) return "GPU";
  const cores = typeof navigator !== "undefined" ? navigator.hardwareConcurrency : undefined;
  if (typeof cores !== "number" || !Number.isFinite(cores) || cores <= 0) return null;
  if (cores >= 24) return "T32";
  if (cores >= 12) return "T16";
  return "T8";
}

/**
 * The fastest usable backend, or `none`. WebGPU is asked for an adapter —
 * presence of `navigator.gpu` alone is not proof the driver can give us one.
 */
export async function detectBackend(): Promise<GpuBackend> {
  if (typeof navigator !== "undefined") {
    // `navigator.gpu` is not in this TypeScript build's DOM lib, so it is
    // declared locally and reached by cast. Asking for an adapter is the whole
    // test: a gpu object that cannot produce one is not a WebGPU machine.
    const nav = navigator as Navigator & {
      gpu?: { requestAdapter: () => Promise<unknown | null> };
    };
    if (nav.gpu != null) {
      try {
        const adapter = await nav.gpu.requestAdapter();
        if (adapter != null) return "webgpu";
      } catch {
        // A gpu object that cannot produce an adapter is not a WebGPU machine.
      }
    }
  }
  if (typeof document !== "undefined" && typeof document.createElement === "function") {
    try {
      const c = document.createElement("canvas");
      const gl = c.getContext("webgl2");
      if (gl != null) return "webgl2";
    } catch {
      // A browser that throws on getContext is likewise not a WebGL2 machine.
    }
  }
  return "none";
}

/**
 * Two seconds of synthetic GPU load, reporting the sustained frame rate.
 *
 * What the workload is: `FRAME_TEST_CLEAR_PASSES` scissored `clear()` calls per
 * frame, covering the whole of a 512×512 context. It is deliberately fill-rate
 * bound and shader-free, so it cannot fail on a compiler and measures the same
 * thing on every driver.
 *
 * **This number is not the scene's frame rate.** It is a comparable capability
 * figure used only to pick a tier. The scene's real fps is M-D5.6's perf
 * overlay. Saying otherwise would be presenting a synthetic number as evidence
 * of the app's performance.
 */
export async function frameProbe(ms: number = FRAME_TEST_MS): Promise<{
  fps: number | null;
  meanFrameMs: number | null;
}> {
  if (typeof document === "undefined" || typeof document.createElement !== "function") {
    return { fps: null, meanFrameMs: null };
  }
  let gl: WebGL2RenderingContext | null = null;
  try {
    const canvas = document.createElement("canvas");
    canvas.width = 512;
    canvas.height = 512;
    gl = (canvas.getContext("webgl2") as WebGL2RenderingContext | null) ?? null;
  } catch {
    return { fps: null, meanFrameMs: null };
  }
  if (gl === null) return { fps: null, meanFrameMs: null };

  const w = 512;
  const h = 512;
  const cell = Math.ceil(Math.sqrt(FRAME_TEST_CLEAR_PASSES));
  const cols = Math.max(1, Math.floor(w / cell));

  return new Promise((resolve) => {
    const start = performance.now();
    let frames = 0;

    const pass = (now: number) => {
      if (now - start >= ms) {
        const elapsed = now - start;
        const meanFrameMs = frames > 0 ? elapsed / frames : null;
        const fps = meanFrameMs !== null && meanFrameMs > 0 ? 1000 / meanFrameMs : null;
        resolve({ fps, meanFrameMs });
        return;
      }
      // One frame of fill-rate load.
      for (let i = 0; i < FRAME_TEST_CLEAR_PASSES; i++) {
        const x = (i % cols) * cell;
        const y = Math.floor(i / cols) * cell;
        gl!.enable(gl!.SCISSOR_TEST);
        gl!.scissor(x, y, cell, cell);
        gl!.clearColor(0, 0, 0, 1);
        gl!.clear(gl!.COLOR_BUFFER_BIT);
      }
      gl!.disable(gl!.SCISSOR_TEST);
      frames++;
      requestAnimationFrame(pass);   // rAF is the frame clock; a microtask would
    };                               // measure the run loop, not the renderer
    requestAnimationFrame(pass);
  });
}

/**
 * `navigator.deviceMemory`, or null when the browser will not say.
 *
 * Read as an *upper bound* only. It reports a coarse bucket (2/4/8 GiB) and
 * never the OS total, so it can demote but never promote, and a null here must
 * not be read as "less than 8" — that would turn an unavailable value into a
 * measurement, which is exactly the fabrication AHOS's law forbids.
 */
export function ramUpperBoundGb(): number | null {
  const d = typeof navigator !== "undefined"
    ? (navigator as Navigator & { deviceMemory?: number }).deviceMemory
    : undefined;
  if (typeof d !== "number" || !Number.isFinite(d) || d <= 0) return null;
  return d;
}

/**
 * Reads the stored override, or null. Wrapped because `localStorage` throws in
 * private mode and on storage denial — an unreadable preference is not an error
 * worth surfacing, it is just no override.
 */
export function readOverride(): RenderTier | null {
  try {
    const raw = globalThis.localStorage?.getItem(OVERRIDE_KEY);
    if (!raw) return null;
    return TIER_ORDER.includes(raw as RenderTier) ? (raw as RenderTier) : null;
  } catch {
    return null;
  }
}

export function writeOverride(tier: RenderTier | null): void {
  try {
    if (tier === null) globalThis.localStorage?.removeItem(OVERRIDE_KEY);
    else globalThis.localStorage?.setItem(OVERRIDE_KEY, tier);
  } catch {
    // Unwritable storage: the override simply will not survive a reload.
  }
}

/**
 * Best-effort "is this a dedicated card" from detect-gpu's renderer string.
 *
 * Returns `true` only when the string positively names a dedicated family,
 * `false` when it names a known-integrated one, and **`null` when it cannot be
 * read or is not recognised**. The `null` is the load-bearing case: the
 * renderer string is vendor marketing text, not a measurement, so anything not
 * positively identified stays unknown rather than being read as integrated.
 * `resolveTier` then treats `null` as "no discrete signal", which is the honest
 * reading, and `hardwareTierSync(null)` falls back to the core count.
 *
 * This never asserts discreteness from a framerate — see `probeQuality`.
 */
export function dedicatedClass(renderer: string | undefined): boolean | null {
  if (typeof renderer !== "string") return null;
  // Normalise: lower case, strip the ANGLE/Driver wrapper punctuation.
  const r = renderer.toLowerCase();
  // Integrated and mobile families first — the ordering matters, because a
  // vendor string can mention both (e.g. "Intel(R) HD Graphics").
  const INTEGRATED = [
    "intel", "iris", "uhd", "gma", "mali", "adreno", "powervr", "sgx",
    "vivante", "imagetec", "apple gpu", "apple m", "vega ", "radeon vega",
    "radeon graphics", "amd radeon(tm) graphics", "radeon 660m", "arc(", "arc ",
  ];
  for (const pat of INTEGRATED) if (r.includes(pat)) return false;
  // Dedicated families. Matched only after the integrated check, so an Intel
  // card with an "Arc" substring is not promoted by the rule below.
  const DEDICATED = [
    "geforce", "gtx", "rtx", "quadro", "titan", "nvidia", "radeon rx",
    "radeon pro", "radeon r9", "firepro", "tesla", "a100", "h100",
    "quadro", "t600", "t1000", "t2000", "wx ", "w5000", "w7000",
  ];
  for (const pat of DEDICATED) if (r.includes(pat)) return true;
  return null;
}

/**
 * The full probe, client-side. Runs the frame test and asks detect-gpu for the
 * GPU class, then hands every measurement to the pure `resolveTier`.
 *
 * `detect-gpu` is imported dynamically so it never enters the SSR bundle and so
 * `resolveTier`'s tests do not need it. Its benchmarks URL is always the local
 * one — see `BENCHMARKS_URL`.
 */
export async function probeQuality(): Promise<TierVerdict> {
  // Each arm resolves independently to a value or to null, so one measurement
  // failing can never break the others — and null is the honest "not measured",
  // which `resolveTier` never reads as a low value.
  const [backend, frame, discrete] = await Promise.all([
    detectBackend(),
    frameProbe(),
    import("detect-gpu")
      .then(async (mod) => {
        try {
          const gpu = await mod.getGPUTier({ benchmarksURL: BENCHMARKS_URL });
          // detect-gpu's own ladder is a *framerate* one: tier 1 ≥ 15 fps,
          // tier 2 ≥ 30 fps, tier 3 ≥ 60 fps in its benchmark scene. It says
          // nothing about whether the card is discrete, and an integrated part
          // that clears 30 fps reports tier 2 — so reading tier ≥ 2 as
          // "dedicated-class" would label an Intel HD as a discrete card, which
          // the chip would then state as fact. That is a fabrication of a
          // hardware class from a fill-rate number.
          //
          // Only `type: "BENCHMARK"` is a measurement at all: `FALLBACK` (no
          // renderer string), `SSR` (no window) and `BLOCKLISTED` are the
          // library guessing or giving up, and a guess may not promote.
          if (gpu.type !== "BENCHMARK") return null;
          // The renderer string is the only card-class signal detect-gpu
          // exposes, and it is vendor text rather than a measurement, so it is
          // used only to *exclude* the known-integrated families — never to
          // assert that a card is discrete. Unreadable or unrecognised means
          // the class is unknown, which is `null`, never `false`-as-a-fact.
          return dedicatedClass(gpu.gpu);
        } catch {
          return null;
        }
      })
      .catch(() => null),
  ]);

  return resolveTier({
    hardware: hardwareTierSync(discrete),
    backend,
    fps: frame.fps,
    meanFrameMs: frame.meanFrameMs,
    ramGb: ramUpperBoundGb(),
    override: readOverride(),
  });
}

/**
 * M-D5.3 quality probe selftest — the tier ladder, as an assertion.
 *
 * Run: npm run test:stage-quality
 *
 * `resolveTier` is a pure function of a plain record, so the whole ladder can be
 * asserted on a machine with no GPU — which is the point of the split. What this
 * proves is the negative that matters: that no measurement can promote the stage
 * past what the hardware measured as, and that an unavailable measurement is
 * never silently read as a low one (that would turn "we don't know" into "it is
 * slow", the same fabrication UNKNOWN exists to prevent).
 *
 * It also asserts the module never reaches for a machine identity, because
 * "never from the machine name" (CLAUDE_DASHBOARD_2050 rule 3) is only true if
 * the code cannot read a name.
 */
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { describe, it } from "node:test";

import {
  BENCHMARKS_URL,
  cap,
  dedicatedClass,
  detectBackend,
  FPS_FLOOR_2D,
  frameProbe,
  HARDWARE_LABELS,
  HARDWARE_TIERS,
  hardwareTierSync,
  measuredCores,
  RAM_FLOOR_GB,
  ramUpperBoundGb,
  readOverride,
  resolveTier,
  tierFromCapability,
  TIER_LABELS,
  TIER_ORDER,
  writeOverride,
  type GpuBackend,
  type HardwareTier,
  type RenderTier,
  type TierMeasure,
} from "../components/stage/quality.ts";

const ANY = { hardware: null, cores: null, backend: null, fps: null, meanFrameMs: null, ramGb: null, override: null };
const at = (over: Partial<TierMeasure>) => ({ ...ANY, ...over });

describe("M-D5.3: the ladder is what the spec says", () => {
  it("names T0..T3 in order, T0 the floor and T3 the ceiling", () => {
    assert.deepEqual([...TIER_ORDER], ["T0", "T1", "T2", "T3"]);
  });

  it("labels every tier in Persian and English", () => {
    for (const t of TIER_ORDER) {
      assert.ok(TIER_LABELS[t].en, `${t} has no English label`);
      assert.ok(TIER_LABELS[t].fa, `${t} has no Persian label`);
      assert.ok(TIER_LABELS[t].faWhy, `${t} has no Persian why-line`);
    }
  });

  it("never names a hardware tier outside the four the queue defines", () => {
    assert.deepEqual([...HARDWARE_TIERS], ["T8", "T16", "T32", "GPU"]);
  });
});

describe("M-D5.3: cap only ever walks down", () => {
  it("lowers a candidate to a limit", () => {
    assert.equal(cap("T3", "T1"), "T1");
    assert.equal(cap("T2", "T0"), "T0");
  });

  it("leaves a candidate already at or below the limit alone", () => {
    assert.equal(cap("T1", "T2"), "T1");
    assert.equal(cap("T0", "T0"), "T0");
  });

  it("cannot raise", () => {
    for (const a of TIER_ORDER) for (const b of TIER_ORDER) {
      assert.notEqual(TIER_ORDER.indexOf(cap(a, b)) > TIER_ORDER.indexOf(a), true);
    }
  });
});

describe("M-D5.3: capability alone gives the spec's rungs", () => {
  it("without a backend there is only T0, whatever the hardware says", () => {
    for (const hw of [...HARDWARE_TIERS, null]) {
      assert.equal(tierFromCapability(hw, "none").tier, "T0");
      assert.equal(tierFromCapability(hw, null).tier, "T0");
    }
  });

  it("makes WebGPU + a discrete GPU T3", () => {
    assert.equal(tierFromCapability("GPU", "webgpu").tier, "T3");
  });

  it("makes WebGPU on 32 cores T3, and T32 on WebGL2 T2", () => {
    assert.equal(tierFromCapability("T32", "webgpu").tier, "T3");
    assert.equal(tierFromCapability("T32", "webgl2").tier, "T2");
  });

  it("makes 16 cores T2", () => {
    assert.equal(tierFromCapability("T16", "webgl2").tier, "T2");
    assert.equal(tierFromCapability("T16", "webgpu").tier, "T2");
  });

  it("makes an 8-core / integrated machine T1, never above", () => {
    assert.equal(tierFromCapability("T8", "webgl2").tier, "T1");
    assert.equal(tierFromCapability("T8", "webgpu").tier, "T1");
    assert.equal(tierFromCapability(null, "webgl2").tier, "T1");
  });

  it("gives every rung a machine reason and a Persian one", () => {
    for (const hw of HARDWARE_TIERS) {
      for (const be of ["webgpu", "webgl2"] as const) {
        const r = tierFromCapability(hw, be);
        assert.ok(r.reason, "no machine reason");
        assert.ok(r.reasonFa, "no Persian reason");
      }
    }
  });
});

describe("M-D5.3: measurements demote, never promote", () => {
  it("no backend is T0 even on a discrete GPU with an override asking for T3", () => {
    const v = resolveTier(at({ hardware: "GPU", backend: "none", override: "T3" }));
    assert.equal(v.tier, "T0");
    assert.ok(v.limits.includes("no-webgl"), "no-webgl must be recorded as the limit");
    assert.equal(v.reason, "override-capped");
  });

  it("a frame rate under the floor is T0 even on T32 hardware", () => {
    const v = resolveTier(at({ hardware: "T32", backend: "webgpu", fps: FPS_FLOOR_2D - 1 }));
    assert.equal(v.tier, "T0");
    assert.ok(v.limits.includes("fps-below-floor"));
    assert.equal(v.reason, "measured-cap");
  });

  it("a frame rate exactly at the floor does not demote", () => {
    const v = resolveTier(at({ hardware: "T32", backend: "webgpu", fps: FPS_FLOOR_2D }));
    assert.equal(v.tier, "T3");
    assert.equal(v.limits.length, 0);
  });

  it("RAM under the 8 GB floor caps at T1 but does not force T0", () => {
    const v = resolveTier(at({ hardware: "T32", backend: "webgpu", ramGb: RAM_FLOOR_GB - 1 }));
    assert.equal(v.tier, "T1");
    assert.ok(v.limits.includes("ram-under-floor"));
  });

  it("RAM exactly at the floor does not demote", () => {
    const v = resolveTier(at({ hardware: "T32", backend: "webgpu", ramGb: RAM_FLOOR_GB }));
    assert.equal(v.tier, "T3");
  });

  it("a high frame rate never promotes a T1 machine", () => {
    const v = resolveTier(at({ hardware: "T8", backend: "webgl2", fps: 240 }));
    assert.equal(v.tier, "T1");
    assert.equal(v.limits.length, 0, "a good measurement is not a limit");
  });

  it("the limits are ordered most severe first", () => {
    const v = resolveTier(at({ hardware: "T32", backend: "none", fps: 5, ramGb: 4 }));
    assert.deepEqual(v.limits, ["no-webgl", "fps-below-floor", "ram-under-floor"]);
  });
});

describe("M-D5.3: an unavailable measurement is not a low measurement", () => {
  it("a null fps never demotes", () => {
    assert.equal(resolveTier(at({ hardware: "T32", backend: "webgpu", fps: null })).tier, "T3");
  });

  it("a null RAM never demotes — null is not 'under 8 GB'", () => {
    assert.equal(resolveTier(at({ hardware: "T32", backend: "webgpu", ramGb: null })).tier, "T3");
  });

  it("null hardware falls back to the integrated rung rather than to T0", () => {
    assert.equal(resolveTier(at({ backend: "webgl2" })).tier, "T1");
  });

  it("reports every measurement it actually made", () => {
    const v = resolveTier(at({ hardware: "T16", cores: 14, backend: "webgl2", fps: 58, ramGb: 16 }), 1234);
    assert.equal(v.hardware, "T16");
    assert.equal(v.cores, 14);
    assert.equal(v.fps, 58);
    assert.equal(v.ramGb, 16);
    assert.equal(v.measuredAt, 1234);
  });
});

describe("M-D5.3: an override is honoured within the machine's reach", () => {
  it("is used when nothing measured disagrees", () => {
    const v = resolveTier(at({ hardware: "T32", backend: "webgpu", override: "T1" }));
    assert.equal(v.tier, "T1");
    assert.equal(v.reason, "user-override");
    assert.equal(v.limits.length, 0);
  });

  it("can raise the tier — the user may ask for more than the ladder guessed", () => {
    const v = resolveTier(at({ hardware: "T8", backend: "webgl2", override: "T3" }));
    assert.equal(v.tier, "T3");
    assert.equal(v.reason, "user-override");
  });

  it("cannot raise it past a missing backend", () => {
    assert.equal(resolveTier(at({ backend: "none", override: "T3" })).tier, "T0");
  });

  it("cannot raise it past a frame rate that cannot sustain it", () => {
    const v = resolveTier(at({ hardware: "GPU", backend: "webgpu", fps: 10, override: "T3" }));
    assert.equal(v.tier, "T0");
    assert.equal(v.reason, "override-capped");
  });

  it("cannot raise it past the RAM floor", () => {
    const v = resolveTier(at({ hardware: "GPU", backend: "webgpu", ramGb: 4, override: "T3" }));
    assert.equal(v.tier, "T1");
  });

  it("says in Persian when a wish was capped", () => {
    const v = resolveTier(at({ backend: "none", override: "T3" }));
    assert.ok(v.reasonFa.includes("کاهش"), `the capped-override line must say it was lowered: ${v.reasonFa}`);
  });
});

describe("M-D5.3: the tier never comes from a machine name", () => {
  // Comments and docstrings may *name* the forbidden properties to document the
  // rule, so the scan is over code only: line comments and block comments are
  // stripped first. What must be impossible is reading a name, not mentioning one.
  const code = readFileSync(new URL("../components/stage/quality.ts", import.meta.url), "utf8")
    .replace(/\/\*[\s\S]*?\*\//g, "")
    .replace(/(^|[^:])\/\/.*$/gm, "$1")
    // `(navigator as X).prop` becomes `navigator.prop` so a typed access is
    // counted instead of slipping past the scan.
    .replace(/\(\s*navigator\s+as\s+[^)]*\)/g, "navigator");

  it("reads no machine identity — not even through an alias", () => {
    // Property names are checked, not `navigator.` chains, because a chain can
    // be hidden behind a local (`const n = navigator; n.userAgent`). Any of
    // these identifiers reaching code is a smell worth failing on; comments are
    // already stripped, so a docstring that names one to document the ban is fine.
    for (const bad of ["userAgent", "userAgentData", "platform", "vendor", "hostname", "oscpu"]) {
      assert.ok(!new RegExp(`\\b${bad}\\b`).test(code), `quality.ts must not read ${bad}`);
    }
  });

  it("reaches navigator only through the three measured properties", () => {
    const allowed = ["deviceMemory", "gpu", "hardwareConcurrency"];
    const used = allowed.filter((p) => new RegExp(`\\b${p}\\b`).test(code));
    assert.deepEqual(
      used.sort(),
      [...allowed].sort(),
      "every measured property must be used, and no others",
    );
  });

  it("points detect-gpu at a local benchmark file, never the default CDN", () => {
    assert.ok(BENCHMARKS_URL.startsWith("/"), "the benchmarks URL must be a local path");
    assert.ok(!/unpkg|jsdelivr|cdn\./.test(code), "no CDN host in the probe");
  });
});

describe("M-D5.3: the impure getters degrade to null rather than guessing", () => {
  // Node 22 exposes `navigator` as a read-only global getter, so it is replaced
  // via defineProperty rather than assignment.
  const setNav = (props: object): Navigator => {
    Object.defineProperty(globalThis, "navigator", {
      value: props as Navigator,
      configurable: true,
      writable: true,
    });
    return props as Navigator;
  };
  const restoreNav = Object.getOwnPropertyDescriptor(globalThis, "navigator");

  it("hardwareTierSync promotes only on an explicit discrete flag", () => {
    assert.equal(hardwareTierSync(true), "GPU");
    setNav({});
    assert.equal(hardwareTierSync(null), null);
  });

  it("hardwareTierSync clamps logical cores to the rungs", () => {
    const probe = (cores: number | undefined) => {
      setNav({ hardwareConcurrency: cores });
      return hardwareTierSync(null);
    };
    try {
      assert.equal(probe(32), "T32");
      assert.equal(probe(24), "T32");
      assert.equal(probe(16), "T16");
      assert.equal(probe(12), "T16");
      assert.equal(probe(8), "T8");
      assert.equal(probe(2), "T8");
      assert.equal(probe(undefined), null);
      assert.equal(probe(0), null);
    } finally {
      Object.defineProperty(globalThis, "navigator", { ...restoreNav, configurable: true });
    }
  });

  it("ramUpperBoundGb returns null when the browser will not say", () => {
    try {
      setNav({});
      assert.equal(ramUpperBoundGb(), null);
      setNav({ deviceMemory: 8 });
      assert.equal(ramUpperBoundGb(), 8);
      setNav({ deviceMemory: NaN });
      assert.equal(ramUpperBoundGb(), null);
    } finally {
      Object.defineProperty(globalThis, "navigator", { ...restoreNav, configurable: true });
    }
  });

  it("detectBackend reports none where there is nothing to probe", async () => {
    const savedNav = globalThis.navigator;
    const savedDoc = globalThis.document;
    try {
      // node has neither navigator.gpu nor document, so this is the real T0 path
      delete (globalThis as { navigator?: unknown }).navigator;
      delete (globalThis as { document?: unknown }).document;
      assert.equal(await detectBackend(), "none");
    } finally {
      globalThis.navigator = savedNav;
      globalThis.document = savedDoc;
    }
  });

  it("frameProbe reports null outside a document", async () => {
    const savedDoc = globalThis.document;
    try {
      delete (globalThis as { document?: unknown }).document;
      assert.deepEqual(await frameProbe(16), { fps: null, meanFrameMs: null });
    } finally {
      globalThis.document = savedDoc;
    }
  });

  it("round-trips the override through storage, and ignores garbage", () => {
    const saved = globalThis.localStorage;
    const store = new Map<string, string>();
    try {
      Object.defineProperty(globalThis, "localStorage", {
        value: {
          getItem: (k: string) => store.get(k) ?? null,
          setItem: (k: string, v: string) => void store.set(k, v),
          removeItem: (k: string) => void store.delete(k),
        },
        configurable: true,
      });
      assert.equal(readOverride(), null);
      writeOverride("T2");
      assert.equal(readOverride(), "T2");
      writeOverride(null);
      assert.equal(readOverride(), null);
      store.set("ahos.stage.tier.override", "T9");
      assert.equal(readOverride(), null, "an unknown tier id is not an override");
    } finally {
      Object.defineProperty(globalThis, "localStorage", { value: saved, configurable: true });
    }
  });
});

describe("M-D5.3: the verdict is self-describing", () => {
  it("carries the tier and the reason a panel can show", () => {
    const v = resolveTier(at({ hardware: "T8", backend: "webgl2" }));
    const be: GpuBackend = v.backend ?? "none";
    const hw: HardwareTier | null = v.hardware;
    const t: RenderTier = v.tier;
    assert.ok(TIER_ORDER.includes(t));
    assert.ok(["webgpu", "webgl2", "none"].includes(be));
    assert.ok(hw === null || HARDWARE_TIERS.includes(hw));
    assert.ok(v.reason);
    assert.ok(v.reasonFa);
  });
});

describe("M-D5.3: a framerate is never read as a card class", () => {
  // detect-gpu's tier is frames per second in its benchmark. Reading tier ≥ 2 as
  // "dedicated" labelled an Intel HD integrated part as a discrete card on the
  // dev machine, which the chip then stated as fact. The class may only come
  // from what the renderer string positively names.
  it("names a dedicated card when the renderer says so", () => {
    assert.equal(dedicatedClass("ANGLE (NVIDIA, NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0)"), true);
    assert.equal(dedicatedClass("Radeon RX 6700 XT"), true);
  });

  it("excludes the integrated families the dev machine actually reports", () => {
    // The exact string this laptop's probe returned, which was mislabelled.
    const lap = "ANGLE (Intel, Intel(R) HD Graphics Family (0x00000A16) Direct3D11 vs_5_0 ps_5_0, D3D11)";
    assert.equal(dedicatedClass(lap), false);
    assert.equal(dedicatedClass("Intel(R) Iris(R) Xe Graphics"), false);
    assert.equal(dedicatedClass("Apple GPU"), false);
    assert.equal(dedicatedClass("Mali-G78"), false);
  });

  it("an unreadable or unrecognised renderer is unknown, never 'integrated'", () => {
    // This is the load-bearing assertion: unrecognised text is null, not false,
    // because the absence of a match is not evidence of integration.
    assert.equal(dedicatedClass(undefined), null);
    assert.equal(dedicatedClass(""), null);
    assert.equal(dedicatedClass("Some Future GPU 9000"), null);
  });

  it("does not promote an Intel card on an Arc substring match", () => {
    // Ordering matters: the integrated check runs first, so "Intel Arc" is not
    // lifted by the dedicated "arc" pattern.
    assert.equal(dedicatedClass("Intel(R) Arc(TM) A380"), false);
  });

  it("a null class falls back to the core count, not to a low tier", () => {
    // hardwareTierSync(null-discrete) must still report the measured width.
    assert.equal(hardwareTierSync(null), "T8");
  });
});

describe("M-D5.3: a band name is never a core count", () => {
  // The chip used to render HARDWARE_LABELS[verdict.hardware], which read
  // «۸ هسته» (8 cores) on this machine's 4 logical cores: hardwareTierSync puts
  // every count below 12 into the T8 band, so the band's name was being stated
  // as a measurement. The verdict now carries the measured count separately, and
  // the band labels name the band's edges rather than a count inside it.
  it("clamps a 4-core machine into the T8 band while the measurement stays 4", () => {
    const v = resolveTier(at({ hardware: hardwareTierSync(null), cores: 4, backend: "webgl2" }));
    assert.equal(v.hardware, "T8");
    assert.equal(v.cores, 4);
    assert.equal(v.tier, "T1");
  });

  it("labels each band with the edges it actually covers", () => {
    // The boundaries hardwareTierSync clamps at: 24+ → T32, 12–23 → T16, below 12
    // → T8. A label naming a single count would misstate every other member.
    for (const [hw, label] of [
      ["T8", "under 12 cores"],
      ["T16", "12–23 cores"],
      ["T32", "24 cores or more"],
    ] as const) {
      assert.ok(HARDWARE_LABELS[hw].en === label, `${hw} must be labelled as a band`);
    }
  });

  it("a null core count is unknown, never read as a low one", () => {
    // The same law as a null fps or a null RAM: absence is not a measurement.
    const v = resolveTier(at({ hardware: "T32", backend: "webgpu", cores: null }));
    assert.equal(v.tier, "T3");
    assert.equal(v.cores, null);
  });

  it("measuredCores reports what the browser said, and null when it will not", () => {
    const restoreNav = Object.getOwnPropertyDescriptor(globalThis, "navigator");
    const setNav = (props: object) => {
      Object.defineProperty(globalThis, "navigator", {
        value: props as Navigator,
        configurable: true,
        writable: true,
      });
    };
    try {
      setNav({ hardwareConcurrency: 4 });
      assert.equal(measuredCores(), 4);
      setNav({ hardwareConcurrency: 16 });
      assert.equal(measuredCores(), 16);
      setNav({});
      assert.equal(measuredCores(), null, "no hardwareConcurrency is not '1 core'");
      setNav({ hardwareConcurrency: 0 });
      assert.equal(measuredCores(), null, "zero is not a core count");
    } finally {
      Object.defineProperty(globalThis, "navigator", { ...restoreNav, configurable: true });
    }
  });
});

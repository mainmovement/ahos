/**
 * M-D6.1 globe geometry selftest — evenness, as an assertion.
 *
 * Run: npm run test:globe
 * Self-test, not independent verification.
 *
 * The claim worth proving here is not "there are N points" — that is a length —
 * but that the field is *even*: the owner's list asks for a dotted globe, and a
 * layout that clumps or rows would look broken at a glance while every trivial
 * property (count, radius, determinism) still passed. So this checks the two
 * failure modes a spiral layout actually has: a centroid that drifts off the
 * origin (lopsided), and a point that lands on top of its neighbour (clumping).
 *
 * Everything is asserted without a GPU, without `window`, and without three.js —
 * `fibonacciSphere` is pure arithmetic, which is the reason it can be proven at
 * all.
 */
import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  fibonacciSphere,
  GLOBE_RADIUS,
  pointShades,
} from "../components/stage/globeGeometry.ts";

/** Length of a vector, for the on-the-sphere check. */
const len = (x: number, y: number, z: number): number => Math.hypot(x, y, z);

describe("M-D6.1: the layout is on the sphere", () => {
  it("places every point on the radius it was asked for", () => {
    for (const radius of [GLOBE_RADIUS, 0.5, 3]) {
      const p = fibonacciSphere(500, radius);
      for (let i = 0; i < p.length; i += 3) {
        assert.ok(
          Math.abs(len(p[i]!, p[i + 1]!, p[i + 2]!) - radius) < 1e-5,
          `point ${i / 3} is not on the radius ${radius}`,
        );
        for (const c of [p[i]!, p[i + 1]!, p[i + 2]!]) {
          assert.ok(Number.isFinite(c), "a coordinate is NaN");
        }
      }
    }
  });

  it("emits exactly three floats per point, for the count asked", () => {
    assert.equal(fibonacciSphere(0).length, 0);
    assert.equal(fibonacciSphere(1).length, 3);
    assert.equal(fibonacciSphere(6000).length, 18000);
    assert.equal(fibonacciSphere(24000).length, 72000);
  });

  it("reaches both poles, so the globe is a whole sphere and not a band", () => {
    const p = fibonacciSphere(2000);
    let top = -Infinity;
    let bottom = Infinity;
    for (let i = 1; i < p.length; i += 3) {
      top = Math.max(top, p[i]!);
      bottom = Math.min(bottom, p[i]!);
    }
    assert.ok(top > GLOBE_RADIUS * 0.999, "no point near the top pole");
    assert.ok(bottom < -GLOBE_RADIUS * 0.999, "no point near the bottom pole");
  });
});

describe("M-D6.1: the field is even, not clumped or rowed", () => {
  it("centres on the origin, so the mass is not lopsided", () => {
    // A Fibonacci spiral is symmetric by construction; a centroid far from zero
    // would mean the spiral is accumulating on one side — which is what a wrong
    // golden-angle constant or a bad ring radius looks like.
    for (const count of [64, 4000, 24000]) {
      const p = fibonacciSphere(count);
      const mean = [0, 1, 2].map((axis) => {
        let sum = 0;
        for (let i = axis; i < p.length; i += 3) sum += p[i]!;
        return sum / count;
      });
      for (const m of mean) {
        assert.ok(Math.abs(m) < GLOBE_RADIUS * 0.02, `centroid drifts ${m} off the origin`);
      }
    }
  });

  it("keeps neighbouring points apart, so the dots do not pile up", () => {
    // Consecutive points on the spiral are the two that would visibly clump if
    // the angle were wrong. Their spacing is bounded *below* by the spacing a
    // perfectly even shell of the same count would have, within the spiral's
    // own tolerance.
    for (const count of [1000, 8000]) {
      const p = fibonacciSphere(count);
      // The mean area per point on the unit sphere, and the chord it implies.
      const evenSpacing = Math.sqrt((4 * Math.PI) / count);
      let minGap = Infinity;
      for (let i = 0; i < count; i++) {
        const a = i * 3;
        const b = ((i + 1) % count) * 3;
        const d = len(p[a]! - p[b]!, p[a + 1]! - p[b + 1]!, p[a + 2]! - p[b + 2]!);
        minGap = Math.min(minGap, d);
      }
      assert.ok(
        minGap > evenSpacing * 0.5,
        `neighbouring points sit ${minGap.toFixed(4)} apart, closer than half the even spacing`,
      );
    }
  });

  it("does not row into latitude bands, which a lat/long grid would", () => {
    // A latitude grid stacks points into rings at a few discrete heights; the
    // spiral should spread heights instead. Counting the distinct heights that
    // hold a meaningful share of the points catches a grid masquerading as a
    // spiral: with 2000 points, rowing would concentrate them into tens of
    // bands, not the ~1000 the spiral uses.
    const count = 2000;
    const p = fibonacciSphere(count);
    const bands = new Set<number>();
    for (let i = 1; i < p.length; i += 3) {
      bands.add(Math.round(p[i]! * 1000));
    }
    assert.ok(bands.size > count * 0.4, `only ${bands.size} distinct heights — the points are rowing`);
  });
});

describe("M-D6.1: the field is deterministic", () => {
  it("gives the same globe on every machine and every reload", () => {
    const a = fibonacciSphere(3000);
    const b = fibonacciSphere(3000);
    assert.equal(a.length, b.length);
    for (let i = 0; i < a.length; i++) {
      assert.equal(a[i], b[i], "two runs disagree about a point");
    }
  });

  it("shades every point, in range, with no flicker between renders", () => {
    const s = pointShades(2000);
    assert.equal(s.length, 2000);
    for (const v of s) {
      assert.ok(v >= 0.72 && v <= 1.0, `shade ${v} outside [0.72, 1.0]`);
    }
    const again = pointShades(2000);
    for (let i = 0; i < s.length; i++) assert.equal(s[i], again[i], "the shading is not stable");
  });
});

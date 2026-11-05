import { describe, expect, it } from "vitest";
import { intBetween, mulberry32, pick, randomWalk, seedFrom } from "@/lib/data/rng";

describe("deterministic RNG", () => {
  it("produces identical sequences for identical seeds", () => {
    const a = mulberry32(seedFrom("ahos-demo"));
    const b = mulberry32(seedFrom("ahos-demo"));
    const seqA = Array.from({ length: 50 }, () => a());
    const seqB = Array.from({ length: 50 }, () => b());
    expect(seqA).toEqual(seqB);
  });

  it("produces values in [0,1)", () => {
    const rng = mulberry32(42);
    for (let i = 0; i < 1000; i += 1) {
      const v = rng();
      expect(v).toBeGreaterThanOrEqual(0);
      expect(v).toBeLessThan(1);
    }
  });

  it("randomWalk stays within bounds and returns the requested length", () => {
    const walk = randomWalk(mulberry32(7), 120, 100_000, 0.01, 0.0005, 50_000, 200_000);
    expect(walk).toHaveLength(120);
    for (const v of walk) {
      expect(v).toBeGreaterThanOrEqual(50_000);
      expect(v).toBeLessThanOrEqual(200_000);
    }
  });

  it("intBetween and pick are deterministic", () => {
    const rng = mulberry32(seedFrom("pick"));
    const items = ["a", "b", "c"] as const;
    const first = [intBetween(rng, 0, 10), pick(rng, items)];
    const rng2 = mulberry32(seedFrom("pick"));
    expect([intBetween(rng2, 0, 10), pick(rng2, items)]).toEqual(first);
  });
});

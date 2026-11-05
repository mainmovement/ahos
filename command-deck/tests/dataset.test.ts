import { describe, expect, it } from "vitest";
import { DATASET, POSITIONS, closedWinRate, validateDataset } from "@/lib/data";
import { sample } from "@/lib/provenance/envelope";

describe("frozen dataset integrity", () => {
  it("validates against the Zod contracts", () => {
    const report = validateDataset();
    expect(report.failures).toEqual([]);
    expect(report.ok).toBe(true);
  });

  it("anchors to the frozen dataset instant, not the wall clock", () => {
    expect(DATASET.asOf).toBe("2026-10-31T14:30:00Z");
    expect(new Date(DATASET.asOf).getTime()).toBeLessThan(Date.parse("2026-11-01T00:00:00Z"));
  });

  it("keeps the NET = GROSS − FEES + FUNDING identity everywhere", () => {
    for (const p of POSITIONS) {
      if (p.pnl.fees !== null && p.pnl.funding !== null) {
        expect(p.pnl.net).toBeCloseTo(p.pnl.gross - p.pnl.fees + p.pnl.funding, 6);
      } else {
        expect(p.pnl.net).toBeNull();
      }
    }
  });

  it("win rate uses only closed positions with computable net", () => {
    const win = closedWinRate();
    expect(win.closed).toBeGreaterThan(0);
    expect(win.rate).not.toBeNull();
    expect(win.computable).toBeLessThanOrEqual(win.closed);
    expect(win.rate ?? 0).toBeGreaterThanOrEqual(0);
    expect(win.rate ?? 0).toBeLessThanOrEqual(1);
  });

  it("sample envelopes always expose a dataset-anchored timestamp", () => {
    const env = sample(1, "sample://test");
    expect(env.provenance.observedAt).toBe(DATASET.asOf);
  });
});

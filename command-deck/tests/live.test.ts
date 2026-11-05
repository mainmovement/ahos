import { describe, expect, it } from "vitest";
import { classifyWmo, computePortfolio, fmtPct, fmtQty, fmtUsd, skyPhaseFromHour, tzClockParts } from "@/lib/live/derive";

describe("live data derivations", () => {
  it("computePortfolio sums only live-priced holdings and marks P&L null without changes", () => {
    const quotes = {
      BTC: { price: 100_000, change24h: 2 },
      ETH: { price: 4_000, change24h: -10 },
      XAU: { price: 4_000, change24h: 0 },
    };
    const totals = computePortfolio(quotes);
    // BTC 12.5×100k = 1.25M, ETH 180×4k = 720k, XAU 850×4k = 3.4M → 5.37M
    expect(totals.totalUsd).toBeCloseTo(5_370_000, 0);
    // pnl = 1.25M×2% − 720k×10% + 0 = 25k − 72k = −47k
    expect(totals.pnlTodayUsd).toBeCloseTo(-47_000, 0);
    expect(totals.liveAssets).toBe(3);
    expect(totals.totalAssets).toBe(7);
  });

  it("computePortfolio returns nulls when nothing is live", () => {
    const totals = computePortfolio({});
    expect(totals.totalUsd).toBeNull();
    expect(totals.pnlTodayUsd).toBeNull();
    expect(totals.liveAssets).toBe(0);
  });

  it("classifies WMO weather codes", () => {
    expect(classifyWmo(0)).toBe("clear");
    expect(classifyWmo(2)).toBe("partly");
    expect(classifyWmo(3)).toBe("cloudy");
    expect(classifyWmo(48)).toBe("fog");
    expect(classifyWmo(63)).toBe("rain");
    expect(classifyWmo(95)).toBe("rain");
    expect(classifyWmo(73)).toBe("snow");
    expect(classifyWmo(null)).toBe("cloudy");
  });

  it("maps local hours to sky phases", () => {
    expect(skyPhaseFromHour(6)).toBe("dawn");
    expect(skyPhaseFromHour(12)).toBe("day");
    expect(skyPhaseFromHour(18)).toBe("dusk");
    expect(skyPhaseFromHour(23)).toBe("night");
    expect(skyPhaseFromHour(3)).toBe("night");
  });

  it("formats wall-clock parts per timezone", () => {
    const at = new Date("2026-10-31T14:30:05Z");
    expect(tzClockParts("UTC", at)).toEqual({ h: "14", m: "30", s: "05" });
    const tehran = tzClockParts("Asia/Tehran", at);
    expect(tehran.h).toBe("18");
    expect(tehran.m).toBe("00");
  });

  it("formats financial numbers", () => {
    expect(fmtUsd(107_512.34)).toBe("107,512");
    expect(fmtUsd(1.2345)).toBe("1.2345");
    expect(fmtPct(2.456)).toBe("+2.46%");
    expect(fmtPct(-0.4)).toBe("-0.40%");
    expect(fmtPct(null)).toBe("—");
    expect(fmtQty(9_000_000)).toBe("9.00M");
    expect(fmtQty(1234)).toBe("1.2K");
  });
});

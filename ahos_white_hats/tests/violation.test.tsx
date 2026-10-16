import { describe, expect, it } from "vitest";
import { render } from "@testing-library/react";
import { PaperOnlyGuard } from "@/features/white-hats/components/PaperOnlyGuard";
import { isViolation } from "@/features/white-hats/predicates";
import type { WhiteHatsSnapshot } from "@/features/white-hats/types";
import { buildFixture } from "@/mock/white_hats/fixtures";

function withOverrides(
  patch: Partial<Pick<WhiteHatsSnapshot, "executionMode" | "realTrading">>,
): WhiteHatsSnapshot {
  return { ...buildFixture("calm"), ...patch };
}

describe("truth rule: VIOLATION bar logic", () => {
  it("flags realTrading=true as a violation even in PAPER_ONLY", () => {
    expect(isViolation(withOverrides({ executionMode: "PAPER_ONLY", realTrading: true }))).toBe(true);
  });

  it("flags any execution mode other than PAPER_ONLY", () => {
    expect(isViolation(withOverrides({ executionMode: "LIVE", realTrading: false }))).toBe(true);
    expect(isViolation(withOverrides({ executionMode: "SIMULATION", realTrading: false }))).toBe(true);
  });

  it("accepts PAPER_ONLY with realTrading=false", () => {
    expect(isViolation(withOverrides({ executionMode: "PAPER_ONLY", realTrading: false }))).toBe(false);
  });

  it("renders the red bar only for violating snapshots", () => {
    const ok = render(<PaperOnlyGuard snapshot={withOverrides({ executionMode: "PAPER_ONLY", realTrading: false })} />);
    expect(ok.queryByTestId("violation-bar")).toBeNull();

    const bad = render(<PaperOnlyGuard snapshot={withOverrides({ executionMode: "LIVE", realTrading: true })} />);
    const bar = bad.getByTestId("violation-bar");
    expect(bar.getAttribute("role")).toBe("alert");
    expect(bar.textContent).toContain("نقض سیاست اجرا");
    expect(bar.textContent).toContain("LIVE");
    expect(bar.textContent).toContain("true");
  });

  it("the calm fixture never violates", () => {
    expect(isViolation(buildFixture("calm"))).toBe(false);
  });

  it("the violation fixture violates on both triggers", () => {
    const snapshot = buildFixture("violation");
    expect(snapshot.executionMode).not.toBe("PAPER_ONLY");
    expect(snapshot.realTrading).toBe(true);
    expect(isViolation(snapshot)).toBe(true);
  });
});

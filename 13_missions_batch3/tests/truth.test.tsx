// FILE: 13_missions_batch3/tests/truth.test.tsx
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { TruthChip } from "@/components/truth/TruthChip";
import { ViolationBar } from "@/components/shell/ViolationBar";
import { effectiveReview, newsFreshness, nonDemo, truthFromSnapshot } from "@/lib/stats";
import type { ChipStatus, SnapshotMeta } from "@/contract/types";

describe("TruthChip", () => {
  it("UNKNOWN is grey and never green", () => {
    render(<TruthChip status="UNKNOWN" />);
    const chip = screen.getByTestId("truth-chip");
    expect(chip.className).toContain("ah-chip-unknown");
    expect(chip.className).not.toContain("ah-chip-live");
  });

  it("only LIVE is green; DEMO is visibly striped", () => {
    const { unmount } = render(<TruthChip status="LIVE" />);
    expect(screen.getByTestId("truth-chip").className).toContain("ah-chip-live");
    unmount();
    render(<TruthChip status="DEMO" />);
    expect(screen.getByTestId("truth-chip").className).toContain("ah-chip-demo");
  });

  it("renders every documented status without throwing", () => {
    const all: ChipStatus[] = [
      "LIVE", "STALE", "UNKNOWN", "DEMO", "CONFLICT", "REJECTED",
      "UNAVAILABLE", "ERROR", "PARTIAL", "SIMULATED", "LOADING", "EMPTY",
      "PLANNED", "MISSING",
    ];
    for (const s of all) {
      const { unmount } = render(<TruthChip status={s} />);
      expect(screen.getByTestId("truth-chip").textContent).toBe(s);
      unmount();
    }
  });
});

describe("ViolationBar", () => {
  it("is hidden only for PAPER_ONLY + realTrading=false", () => {
    const { container, unmount } = render(<ViolationBar executionMode="PAPER_ONLY" realTrading={false} />);
    expect(container.querySelector('[data-testid="violation-bar"]')).toBeNull();
    unmount();
  });

  it("shows for LIVE mode, for realTrading, and for UNKNOWN mode (fail loud)", () => {
    const a = render(<ViolationBar executionMode="LIVE" realTrading={false} />);
    expect(screen.getByTestId("violation-bar")).toBeTruthy();
    a.unmount();
    const b = render(<ViolationBar executionMode="PAPER_ONLY" realTrading={true} />);
    expect(screen.getByTestId("violation-bar")).toBeTruthy();
    b.unmount();
    const c = render(<ViolationBar executionMode="UNKNOWN" realTrading={false} />);
    expect(screen.getByTestId("violation-bar")).toBeTruthy();
    c.unmount();
  });
});

describe("display-rule helpers", () => {
  it("DEMO rows are excluded from totals", () => {
    const rows = [{ demo: true }, { demo: false }, { demo: true }, { demo: false }];
    expect(nonDemo(rows).length).toBe(2);
  });

  it("no timestamp ⇒ UNKNOWN; demo dominates", () => {
    const meta: SnapshotMeta = { executionMode: "PAPER_ONLY", realTrading: false, source: "s", generatedAt: null };
    expect(truthFromSnapshot(meta, [{ demo: false }])).toBe("UNKNOWN");
    const demoMeta: SnapshotMeta = { ...meta, generatedAt: "2026-10-16T12:00:00+03:30" };
    expect(truthFromSnapshot(demoMeta, [{ demo: true }])).toBe("DEMO");
  });

  it("news freshness: no timestamp ⇒ UNKNOWN", () => {
    expect(newsFreshness({ time: null }, "2026-10-16T12:00:00+03:30", 30)).toBe("UNKNOWN");
    expect(newsFreshness({ time: "2026-10-16T11:58:00+03:30" }, "2026-10-16T12:00:00+03:30", 30)).toBe("LIVE");
    expect(newsFreshness({ time: "2026-10-16T09:00:00+03:30" }, "2026-10-16T12:00:00+03:30", 30)).toBe("STALE");
  });

  it("REVIEWED/REJECTED without reason renders UNREVIEWED + note", () => {
    expect(effectiveReview({ reviewState: "REVIEWED", reason: null }).state).toBe("UNREVIEWED");
    expect(effectiveReview({ reviewState: "REJECTED", reason: "  " }).note).toBe("دلیل ثبت نشده");
    expect(effectiveReview({ reviewState: "REVIEWED", reason: "دلیل" }).state).toBe("REVIEWED");
    expect(effectiveReview({ reviewState: "UNREVIEWED", reason: null }).state).toBe("UNREVIEWED");
  });
});

import { describe, expect, it } from "vitest";
import { render } from "@testing-library/react";
import { FindingsLog } from "@/features/white-hats/components/FindingsLog";
import { DecisionQueue } from "@/features/white-hats/components/DecisionQueue";
import { countNonDemo, telemetryRowCount } from "@/features/white-hats/predicates";
import { buildFixture } from "@/mock/white_hats/fixtures";

describe("truth rule: DEMO is excluded from totals", () => {
  it("counts only non-demo items in the util", () => {
    const snapshot = buildFixture("calm");
    expect(snapshot.decisions.length).toBe(7);
    expect(countNonDemo(snapshot.decisions)).toBe(6);
    expect(snapshot.findings.length).toBe(7);
    expect(countNonDemo(snapshot.findings)).toBe(6);

    const rows = telemetryRowCount(snapshot);
    expect(rows).toEqual({ total: 20, nonDemo: 18 });
  });

  it("shows the non-demo total in the findings log and keeps demo rows striped", () => {
    const snapshot = buildFixture("calm");
    const { container, getByTestId } = render(
      <FindingsLog
        findings={snapshot.findings}
        inspectors={snapshot.inspectors}
        state={{ kind: "content" }}
        demo={false}
        onOpenFinding={() => undefined}
      />,
    );

    const log = getByTestId("findings-log");
    expect(log.textContent).toMatch(/بدون دمو:\s*6/);
    expect(log.textContent).toMatch(/از\s*7/);

    const demoRows = container.querySelectorAll('[data-demo="true"]');
    expect(demoRows.length).toBe(1);
    expect(demoRows[0]!.className).toContain("ah-demo-stripes");
  });

  it("shows the non-demo total in the decision queue", () => {
    const snapshot = buildFixture("calm");
    const { getByTestId } = render(
      <DecisionQueue
        decisions={snapshot.decisions}
        selectedId={null}
        onSelect={() => undefined}
        state={{ kind: "content" }}
        demo={false}
      />,
    );
    expect(getByTestId("decision-totals").textContent).toMatch(/بدون دمو:\s*6/);
  });

  it("never shows a totals badge when the panel itself is fully demo-backed", () => {
    const snapshot = buildFixture("calm");
    const { getByTestId, queryByTestId } = render(
      <FindingsLog
        findings={snapshot.findings}
        inspectors={snapshot.inspectors}
        state={{ kind: "content" }}
        demo={true}
        onOpenFinding={() => undefined}
      />,
    );
    // In the shipped screen every panel is mock-backed (demo) — the DEMO
    // badge replaces the totals chip so demo numbers are never presented
    // as real sums. (The filter line keeps its honest per-view count.)
    expect(queryByTestId("findings-totals")).toBeNull();
    expect(getByTestId("findings-log")).toBeInTheDocument();
  });
});

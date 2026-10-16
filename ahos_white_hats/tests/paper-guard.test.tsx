import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { DecisionQueue } from "@/features/white-hats/components/DecisionQueue";
import { InspectorsPanel } from "@/features/white-hats/components/InspectorsPanel";
import { CanaryTile } from "@/features/white-hats/components/CanaryTile";
import { buildFixture } from "@/mock/white_hats/fixtures";

describe("read-only surface details", () => {
  it("shows «غیرمجاز» for paperAllowed=false rows", () => {
    const snapshot = buildFixture("calm");
    const forbidden = snapshot.decisions.filter((d) => !d.paperAllowed);
    expect(forbidden.length).toBeGreaterThan(0);

    render(
      <DecisionQueue
        decisions={snapshot.decisions}
        selectedId={null}
        onSelect={() => undefined}
        state={{ kind: "content" }}
        demo={false}
      />,
    );
    expect(screen.getByText("غیرمجاز")).toBeInTheDocument();
  });

  it("a missing timestamp renders «—» and UNKNOWN, never a fabricated time", () => {
    const snapshot = buildFixture("calm");
    const undated = snapshot.decisions.find((d) => d.proposedAt === null);
    expect(undated).toBeDefined();
    expect(undated!.verdict).toBe("UNKNOWN");

    const { container } = render(
      <DecisionQueue
        decisions={[undated!]}
        selectedId={null}
        onSelect={() => undefined}
        state={{ kind: "content" }}
        demo={false}
      />,
    );
    expect(container.textContent).toContain("—");
    expect(container.querySelector('[data-status="UNKNOWN"]')).not.toBeNull();
  });

  it("the healthy canary result is FAIL with the «سالم» note", () => {
    const snapshot = buildFixture("calm");
    render(
      <CanaryTile
        canary={snapshot.canary}
        state={{ kind: "content" }}
        demo={false}
      />,
    );
    expect(document.querySelector('[data-status="FAIL"]')).not.toBeNull();
    expect(screen.getByText(/قناری سالم است/)).toBeInTheDocument();
  });

  it("a blind canary (PASS) is rendered as a danger alarm", () => {
    const snapshot = buildFixture("calm");
    render(
      <CanaryTile
        canary={{ ...snapshot.canary!, result: "PASS", caught: null }}
        state={{ kind: "content" }}
        demo={false}
      />,
    );
    const chip = document.querySelector('[data-status="PASS"]') as HTMLElement;
    expect(chip).not.toBeNull();
    expect(chip.getAttribute("data-tone")).toBe("danger");
  });

  it("STALE inspectors display their last-run time", () => {
    const snapshot = buildFixture("calm");
    const stale = snapshot.inspectors.filter((i) => i.status === "STALE");
    expect(stale.length).toBeGreaterThan(0);

    render(
      <InspectorsPanel
        inspectors={snapshot.inspectors}
        state={{ kind: "content" }}
        demo={false}
      />,
    );
    expect(document.querySelector('[data-status="STALE"]')).not.toBeNull();
    expect(screen.getAllByText(/دقیقه پیش/).length).toBeGreaterThan(0);
  });
});

import { describe, expect, it } from "vitest";
import { render } from "@testing-library/react";
import { StatusChip } from "@/components/truth/StatusChip";
import {
  STATUS_TONE,
  TRUTH_STATUSES,
  type ChipStatus,
} from "@/components/truth/status";
import { DecisionQueue } from "@/features/white-hats/components/DecisionQueue";
import { BreakerCard } from "@/features/white-hats/components/BreakerCard";
import { buildFixture } from "@/mock/white_hats/fixtures";

const chip = (status: string) =>
  document.querySelector(`[data-status="${status}"]`) as HTMLElement | null;

describe("truth rule: UNKNOWN is grey, never green", () => {
  it("renders the UNKNOWN chip with the grey tone", () => {
    render(<StatusChip status="UNKNOWN" />);
    const el = chip("UNKNOWN");
    expect(el).not.toBeNull();
    expect(el!.getAttribute("data-tone")).toBe("grey");
    expect(el!.className).toContain("ah-tone-grey");
    expect(el!.className).not.toContain("ah-tone-live");
  });

  it("reserves the live (green) tone for LIVE only across every chip status", () => {
    const statuses = Object.keys(STATUS_TONE) as ChipStatus[];
    const greenStatuses = statuses.filter((s) => STATUS_TONE[s] === "live");
    expect(greenStatuses).toEqual(["LIVE"]);
  });

  it("defines a tone for every truth status", () => {
    for (const s of TRUTH_STATUSES) {
      expect(STATUS_TONE[s]).toBeDefined();
    }
  });

  it("renders an unjudged decision as UNKNOWN and never as CLEAN", () => {
    const snapshot = buildFixture("calm");
    const unjudged = snapshot.decisions.find((d) => d.verdict === "UNKNOWN");
    expect(unjudged).toBeDefined();

    const { container } = render(
      <DecisionQueue
        decisions={[unjudged!]}
        selectedId={null}
        onSelect={() => undefined}
        state={{ kind: "content" }}
        demo={false}
      />,
    );
    expect(container.querySelector('[data-status="UNKNOWN"]')).not.toBeNull();
    expect(container.textContent).not.toContain("CLEAN");
    expect(container.textContent).not.toContain("پاک");
  });

  it("renders an UNKNOWN breaker state with the grey tone", () => {
    const snapshot = buildFixture("empty");
    render(
      <BreakerCard
        breaker={snapshot.breaker}
        state={{ kind: "content" }}
        demo={false}
      />,
    );
    const breakerChip = document.querySelector(
      '[data-testid="breaker-card"] [data-status="UNKNOWN"]',
    ) as HTMLElement | null;
    expect(breakerChip).not.toBeNull();
    expect(breakerChip!.getAttribute("data-tone")).toBe("grey");
  });
});

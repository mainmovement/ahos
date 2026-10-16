import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { WhiteHatsScreen } from "@/features/white-hats/WhiteHatsScreen";
import { buildFixture } from "@/mock/white_hats/fixtures";

/* Verbs allowed: view, filter, export (read-only), open evidence, copy ID.
   Everything else — buy, sell, approve, override, enable-trading, sizing —
   must not exist anywhere in the interactive surface. */

const ALLOWED_BUTTON_TEXT =
  /(کپی|جزئیات|بستن|بازخوانی|برون‌بری|CSV|JSON|مشاهده شواهد|همه|باز|برطرف|کپی شد)/;

const FORBIDDEN =
  /(خرید|فروش|approve|override|enable[\s-]?trading|place[\s-]?order|سفارش گذاشتن|فعال[\s-]?سازی معامله)/i;

describe("forbidden controls never render", () => {
  it("every rendered button is an allowed read-only verb", async () => {
    render(<WhiteHatsScreen />);

    // Wait for the mock adapter to resolve and the queue to render.
    await screen.findByTestId("decision-queue");
    await screen.findAllByRole("button", { name: /کپی شناسه/ });

    const buttons = screen.getAllByRole("button");
    expect(buttons.length).toBeGreaterThan(5);

    for (const button of buttons) {
      const text = `${button.textContent ?? ""} ${button.getAttribute("aria-label") ?? ""}`;
      expect(text).toMatch(ALLOWED_BUTTON_TEXT);
    }
  });

  it("page text never contains trading verbs or order actions", async () => {
    const { container } = render(<WhiteHatsScreen />);
    await screen.findByTestId("decision-queue");
    await screen.findAllByRole("button", { name: /کپی شناسه/ });

    expect(container.textContent ?? "").not.toMatch(FORBIDDEN);
  });

  it("has no forms, number inputs or range sliders (no sizing possible)", async () => {
    const { container } = render(<WhiteHatsScreen />);
    await screen.findByTestId("decision-queue");

    expect(container.querySelectorAll("form")).toHaveLength(0);
    expect(container.querySelectorAll('input[type="number"]')).toHaveLength(0);
    expect(container.querySelectorAll('input[type="range"]')).toHaveLength(0);
  });

  it("exposes the permanent paper pill and paper copy on the screen", async () => {
    render(<WhiteHatsScreen />);
    await screen.findByTestId("decision-queue");

    expect(screen.getByTestId("paper-only-pill")).toBeInTheDocument();
    expect(screen.getByTestId("telemetry-strip").textContent).toContain(
      "موقعیت کاغذی؛ پول واقعی در کار نیست",
    );
  });

  it("fixtures themselves carry no forbidden verbs", () => {
    for (const scenario of ["calm", "violation", "empty"] as const) {
      const text = JSON.stringify(buildFixture(scenario));
      expect(text).not.toMatch(FORBIDDEN);
    }
  });
});

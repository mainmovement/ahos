// FILE: 13_missions_batch3/tests/pages.test.tsx
import { afterEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { ScienceRadarView } from "@/features/science-radar/ScienceRadarView";
import { SelfDebugView } from "@/features/self-debug/SelfDebugView";
import { WeeklyExamView } from "@/features/weekly-exam/WeeklyExamView";
import { SkillMarketView } from "@/features/skill-market/SkillMarketView";
import { NewsCenterView } from "@/features/news-center/NewsCenterView";
import { bodyText, cloneExample, controlTexts, loadExample, mockFetch } from "./helpers";

const FORBIDDEN_CONTROL =
  /\b(buy|sell|purchase|install|enable|update|remove|restart|patch|apply-fix|place-order|approve|override|deploy|send-message|token)\b|نصب|فعال‌سازی|به‌روزرسانی|حذف|راه‌اندازی|خرید|فروش|ارسال پیام|تأیید|استقرار|توکن/i;

function renderWith(view: React.ReactElement, payload: unknown = loadExample()) {
  mockFetch(payload);
  return render(view);
}

afterEach(() => {
  vi.unstubAllGlobals();
  window.history.replaceState({}, "", "/");
});

describe("forbidden controls (every page)", () => {
  const pages: Array<[string, () => React.ReactElement]> = [
    ["science-radar", () => <ScienceRadarView />],
    ["self-debug", () => <SelfDebugView />],
    ["weekly-exam", () => <WeeklyExamView />],
    ["skill-market", () => <SkillMarketView />],
    ["news-center", () => <NewsCenterView />],
  ];

  for (const [name, el] of pages) {
    it(`${name}: no buy/sell/install/enable/... control exists`, async () => {
      const { container } = renderWith(el());
      await screen.findAllByTestId("shell");
      const controls = controlTexts(container);
      for (const text of controls) {
        expect(text, `forbidden control text on ${name}: ${text}`).not.toMatch(FORBIDDEN_CONTROL);
      }
    });
  }
});

describe("science-radar page rules", () => {
  it("shows the honest line and never claims proven/score/ranking", async () => {
    const { container } = renderWith(<ScienceRadarView />);
    await screen.findAllByTestId("shell");
    expect(bodyText(container)).toContain("رادار فقط یافته‌ها را نشان می‌دهد؛ ادعا نیست");
    expect(bodyText(container)).not.toMatch(/proven|اثبات‌شده|score|امتیاز|ranking/i);
  });

  it("DEMO rows are excluded from source-type counts", async () => {
    const payload = cloneExample();
    const section = payload.scienceRadar as Record<string, unknown>;
    const items = section.items as Array<Record<string, unknown>>;
    items[0].demo = false; // sr-01 → paper
    items[1].demo = false; // sr-02 → repo
    renderWith(<ScienceRadarView />, payload);
    await screen.findAllByTestId("shell");
    const paper = document.querySelector('[data-count="paper"]');
    const repo = document.querySelector('[data-count="repo"]');
    const blog = document.querySelector('[data-count="blog"]');
    expect(paper!.textContent).toContain("۱");
    expect(repo!.textContent).toContain("۱");
    expect(blog!.textContent).toContain("۰");
  });
});

describe("self-debug page rules", () => {
  it("marks missing evidence as «بدون شواهد» and never claims fixed", async () => {
    const { container } = renderWith(<SelfDebugView />);
    await screen.findAllByTestId("shell");
    expect(bodyText(container)).toContain("بدون شواهد");
    expect(bodyText(container)).toContain("فقط نمایش؛ اقدام در جای دیگر");
    expect(bodyText(container)).not.toMatch(/fixed|رفع شد|رفع‌شده/i);
    expect(bodyText(container)).toContain("evidence/sd-01/trace.txt");
  });

  it("open/diagnosed counts exclude DEMO rows", async () => {
    const payload = cloneExample();
    const section = payload.selfDebug as Record<string, unknown>;
    const incidents = section.incidents as Array<Record<string, unknown>>;
    incidents[0].demo = false; // sd-01 DIAGNOSED
    renderWith(<SelfDebugView />, payload);
    await screen.findAllByTestId("shell");
    const diagnosed = document.querySelector('[data-count="diagnosed"]');
    expect(diagnosed!.textContent).toContain("۱");
  });
});

describe("weekly-exam page rules", () => {
  it("NOT_RUN is grey, small samples show «نمونه ناکافی», no verdicts", async () => {
    const { container } = renderWith(<WeeklyExamView />);
    await screen.findAllByTestId("shell");
    const notRun = document.querySelector('[data-exam-state="NOT_RUN"]');
    expect(notRun).toBeTruthy();
    expect(notRun!.className).toContain("ah-chip-unknown");
    expect(notRun!.className).not.toContain("ah-chip-live");
    expect(bodyText(container)).toContain("نمونه ناکافی");
    expect(bodyText(container)).toContain("آزمون توصیفی است، نه اثبات توانایی");
    expect(bodyText(container)).not.toMatch(/\bpass\b|\bfail\b|قبول|مردود|leaderboard|بهترین عامل/i);
  });
});

describe("skill-market page rules", () => {
  it("REVIEWED/REJECTED without reason renders UNREVIEWED + «دلیل ثبت نشده»", async () => {
    const { container } = renderWith(<SkillMarketView />);
    await screen.findAllByTestId("shell");
    expect(bodyText(container)).toContain("دلیل ثبت نشده");
    expect(bodyText(container)).toContain("کاتالوگ نمایشی است؛ نصب در این صفحه ممکن نیست");
    // sk-04 (REVIEWED, no reason) must render as UNREVIEWED in the highlights
    const chips = Array.from(container.querySelectorAll(".ah-chip")).map((c) => c.textContent);
    expect(chips.filter((t) => t === "UNREVIEWED").length).toBeGreaterThanOrEqual(2);
    // never implies a plugin is safe
    expect(bodyText(container)).not.toMatch(/safe|ایمن است|تایید شده است/i);
  });
});

describe("news-center page rules", () => {
  it("no timestamp ⇒ UNKNOWN freshness; non-Oil/Gold are PLANNED; reliability نامشخص", async () => {
    const { container } = renderWith(<NewsCenterView />);
    await screen.findAllByTestId("shell");
    const unknownFresh = container.querySelectorAll('[data-freshness="UNKNOWN"]');
    expect(unknownFresh.length).toBeGreaterThanOrEqual(1);
    expect(bodyText(container)).toContain("PLANNED · متصل نیست");
    expect(bodyText(container)).toContain("نامشخص");
    expect(bodyText(container)).toContain("اخبار اطلاعاتی است، نه سیگنال معاملاتی");
    expect(bodyText(container)).not.toMatch(/bullish|bearish|صعودی|نزولی|سیگنال خرید|سیگنال فروش/i);
  });
});

describe("VIOLATION bar integration", () => {
  it("appears when realTrading is true in the contract", async () => {
    const payload = cloneExample();
    payload.realTrading = true;
    for (const key of ["scienceRadar", "selfDebug", "weeklyExam", "skillMarket", "newsCenter"]) {
      (payload[key] as Record<string, unknown>).realTrading = true;
    }
    renderWith(<ScienceRadarView />, payload);
    const bar = await screen.findByTestId("violation-bar");
    expect(bar.textContent).toContain("VIOLATION");
  });
});

describe("forced display states (?state=empty)", () => {
  it("renders the EMPTY state block", async () => {
    window.history.replaceState({}, "", "/arena/science-radar?state=empty");
    renderWith(<ScienceRadarView />);
    const block = await screen.findByTestId("state-block");
    expect(block.getAttribute("data-state")).toBe("EMPTY");
  });
});

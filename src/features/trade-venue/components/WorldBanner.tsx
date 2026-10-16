"use client";

import { TruthChip } from "@/src/components/truth/TruthChip";
import type { ViewState, World } from "@/src/features/trade-venue/logic/model";

/**
 * The banner stack above the work area. It answers, in order:
 *   1. is this data demo/simulated at all? (DEMO / SIMULATED ribbon line)
 *   2. is the current `?state=` variant something other than the calm default?
 *   3. what does the adapter know about freshness right now?
 * Every banner is informational — none of them is a dismissal target.
 */
export interface WorldBannerProps {
  world: World;
  state: ViewState;
  demoForced: boolean;
  isFixture: boolean;
}

const STATE_NOTES: Partial<Record<ViewState, string>> = {
  LOADING: "حالت بازرسی: در حال خواندن — هیچ عددی تا پایان خواندن نمایش داده نمی‌شود.",
  EMPTY: "حالت بازرسی: خالی — خواندن موفق بوده اما هیچ ردیفی برنگشته است.",
  ERROR: "حالت بازرسی: خطا — صفحه عمداً هیچ عددی نشان نمی‌دهد.",
  UNKNOWN: "حالت بازرسی: نامشخص — همهٔ ردیف‌ها نامشخص‌اند و مقدارها «—» می‌شوند.",
  UNAVAILABLE: "حالت بازرسی: در دسترس نیست — هیچ بخشی داده ندارد و نباید حدس زده شود.",
  STALE: "حالت بازرسی: کهنه — ردیف‌ها با زمان آخرین به‌روزرسانی نمایش داده می‌شوند.",
  PARTIAL: "حالت بازرسی: ناقص — بخشی از ردیف‌ها کنار گذاشته شده و شمارش آن‌ها اعلام می‌شود.",
  HISTORICAL: "حالت بازرسی: تاریخی — دفتر مُهرشده و تغییرناپذیر.",
};

export function WorldBanner({ world, state, demoForced, isFixture }: WorldBannerProps) {
  const isSim = world === "SIMULATION";
  const stateNote = STATE_NOTES[state];

  return (
    <div className="ah-banners" data-banners="">
      {isSim ? (
        <div className="ah-banner ah-banner--sim" data-banner="simulation">
          <span className="ah-banner__code" dir="ltr">
            SIMULATED
          </span>
          <span>
            این کتاب شبیه‌سازی است و از جمع‌های «کاغذی واقعی» کنار گذاشته می‌شود؛ حتی همین‌جا هم
            هیچ معاملهٔ واقعی رخ نمی‌دهد.
          </span>
          <TruthChip status="SIMULATED" size="sm" />
        </div>
      ) : null}

      {isFixture ? (
        <div className="ah-banner" data-banner="demo">
          <span className="ah-banner__code" dir="ltr">
            DEMO
          </span>
          <span>
            همهٔ ردیف‌های این صفحه از آداپتور نمایشی می‌آیند
            {demoForced ? " (برچسب DEMO به‌صورت دستی/محیطی روشن شده است)" : ""}. هیچ عدد زندهٔ
            قابل استنادی روی این میز نیست.
          </span>
          <TruthChip status="DEMO" size="sm" />
        </div>
      ) : null}

      {stateNote ? (
        <div className="ah-banner ah-banner--state" data-banner="state" data-state={state}>
          <span className="ah-banner__code" dir="ltr">
            {state}
          </span>
          <span>{stateNote}</span>
        </div>
      ) : null}

    </div>
  );
}

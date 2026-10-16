"use client";

import { useState } from "react";
import { TruthChip } from "@/src/components/truth/TruthChip";
import { PaperOnlyPill } from "./PaperOnlyGuard";
import { TehranClock } from "./TehranClock";
import type { ChipStatus, QualityTier, World } from "@/src/features/trade-venue/logic/model";
import { WORLD_LABEL_EN } from "@/src/features/trade-venue/logic/model";

/**
 * Common frame topbar: page title, page truth chip, the permanent PAPER_ONLY
 * pill, a mute toggle, the quality-tier chip and the Tehran clock.
 *
 * Mute is deliberately narrow: it can silence *informational* notices only.
 * The PAPER_ONLY pill, the DEMO chip, the VIOLATION bar and every truth chip
 * stay on screen no matter what — which is asserted by the tests.
 */
export interface TopbarProps {
  world: World;
  pageStatus: ChipStatus;
  tier: QualityTier;
  notices: readonly string[];
  demoForced: boolean;
}

export function Topbar({ world, pageStatus, tier, notices, demoForced }: TopbarProps) {
  const [muted, setMuted] = useState(false);

  return (
    <header className="ah-topbar" data-topbar="">
      <div className="ah-topbar__row">
        <div className="ah-brand">
          <span className="ah-brand__title">میدان معامله</span>
          <span className="ah-brand__sub">
            کاغذی · {WORLD_LABEL_EN[world]}
            {demoForced ? " · DEMO FORCED" : ""}
          </span>
        </div>

        <TruthChip status={pageStatus} title="وضعیت خود این صفحه: دادهٔ نمایشی/کاغذی" />
        <PaperOnlyPill />

        <span className="ah-spacer" />

        <div className="ah-topbar__meta">
          <button
            type="button"
            className="ah-pill ah-pill--mute ah-pill--btn"
            data-verb="mute"
            aria-pressed={muted}
            data-muted={muted ? "true" : "false"}
            onClick={() => setMuted((value) => !value)}
            title="بی‌صدا کردن اطلاعیه‌های غیرحیاتی (برچسب‌های حقیقت هرگز خاموش نمی‌شوند)"
          >
            <span aria-hidden="true">{muted ? "◼" : "◻"}</span>
            {muted ? "بی‌صدا" : "صدا"}
            <span className="ah-btn__en" dir="ltr">
              notices
            </span>
          </button>

          <span className="ah-pill ah-pill--tier" data-tier-chip={tier} dir="ltr" title="رتبهٔ کیفی این نمایش">
            TIER {tier}
          </span>

          <TehranClock />
        </div>
      </div>

      {notices.length > 0 && !muted ? (
        <div className="ah-topbar__row" data-notices="">
          <span className="ah-work__hint ah-topbar__notices">
            {notices.map((notice) => (
              <span key={notice} className="ah-notice">
                {notice}
              </span>
            ))}
          </span>
        </div>
      ) : null}
    </header>
  );
}

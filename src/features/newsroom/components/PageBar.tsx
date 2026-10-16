"use client";
import { tr } from "@/src/lib/i18n";

import { trf } from '@/src/features/newsroom/lib/trf';
import { useEffect, useState } from 'react';

import { TruthChip } from '@/src/features/newsroom/truth';
import { COPY } from '@/src/features/newsroom/lib/labels';
import { formatClockFa } from '@/src/features/newsroom/lib/format';
import type { Tier } from '@/src/features/newsroom/lib/tier';
import { IconLock, MarkDiamond } from './icons';

function TehranClock() {
  // Rendered only after mount: the server has no "now", and a placeholder
  // keeps hydration deterministic.
  const [now, setNow] = useState<Date | null>(null);

  useEffect(() => {
    const tick = () => setNow(new Date());
    // First paint after mount (never during render) so SSR and hydration agree.
    const frame = requestAnimationFrame(tick);
    const timer = window.setInterval(tick, 1000);
    return () => {
      cancelAnimationFrame(frame);
      window.clearInterval(timer);
    };
  }, []);

  return (
    <div className="flex items-center gap-2" data-testid="tehran-clock">
      <span className="nw-label">{tr("fa", "newsroom.ui.PageBar_1")}</span>
      <span className="nw-mono text-[13px] text-nw-text-dim">
        {now ? formatClockFa(now) : '--:--:--'}
      </span>
    </div>
  );
}

export interface PageBarProps {
  pageStatus: 'DEMO' | 'PARTIAL' | 'LIVE' | 'UNKNOWN';
  tier: Tier;
  onTierChange: (tier: Tier) => void;
}

export function PageBar({ pageStatus, tier, onTierChange }: PageBarProps) {
  return (
    <header
      className="flex shrink-0 flex-wrap items-center justify-between gap-x-4 gap-y-2 border-b border-nw-gold-hairline px-4 py-3"
      data-testid="newsroom-topbar"
    >
      {/* Brand / right side */}
      <div className="flex min-w-0 items-center gap-3">
        <MarkDiamond size={22} className="text-nw-gold" />
        <div className="min-w-0">
          <div className="flex items-baseline gap-2">
            <h2 className="text-[16px] font-semibold leading-none tracking-tight text-nw-text">
              {COPY.pageTitle}
            </h2>
            <span className="text-[12px] leading-none text-nw-gold/80">{COPY.pageSubtitle}</span>
          </div>
          <p className="mt-1 truncate text-[12px] leading-none text-nw-text-faint" data-testid="focus-note">
            {COPY.focusNote}
          </p>
        </div>
      </div>

      {/* Controls / left side */}
      <div className="flex shrink-0 items-center gap-2">
        <TruthChip status={pageStatus} size="md" showFa data-testid="page-truth-chip" />

        <span
          className="inline-flex items-center gap-1.5 rounded-full border border-nw-gold/45 bg-nw-gold/10 px-2.5 py-1 text-[12px] text-nw-gold"
          data-testid="paper-only-pill"
          title={tr("fa", "newsroom.ui.PageBar_2")}
        >
          <IconLock size={12} />
          <span className="font-nw-fa">{COPY.paperOnly}</span>
        </span>


        <div className="flex items-center gap-1 rounded-[6px] border border-nw-line p-[2px]">
          {([0, 1, 2] as const).map((t) => (
            <button
              key={t}
              type="button"
              onClick={() => onTierChange(t)}
              aria-pressed={tier === t}
              title={trf("newsroom.fmt.tierTitle", { t })}
              data-testid={`tier-button-${t}`}
              className={[
                'rounded-[4px] px-2 py-[3px] font-nw-en text-[12px] tracking-wider transition-colors',
                tier === t ? 'bg-nw-gold/15 text-nw-gold' : 'text-nw-text-faint hover:text-nw-text-dim',
              ].join(' ')}
            >
              T{t}
            </button>
          ))}
        </div>

        <TehranClock />
      </div>
    </header>
  );
}

export default PageBar;
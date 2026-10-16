'use client';

import { useEffect, useState } from 'react';

import { TruthChip } from '@/components/truth';
import { COPY } from '@/features/newsroom/lib/labels';
import { formatClockFa } from '@/features/newsroom/lib/format';
import type { Tier } from '@/features/newsroom/lib/tier';
import { IconLock, IconMute, IconSound, MarkDiamond } from './icons';
import { IconButton } from './primitives';

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
      <span className="ah-label">تهران</span>
      <span className="ah-mono text-[12px] text-ah-text-dim">
        {now ? formatClockFa(now) : '--:--:--'}
      </span>
    </div>
  );
}

export interface TopbarProps {
  pageStatus: 'DEMO' | 'PARTIAL' | 'LIVE' | 'UNKNOWN';
  tier: Tier;
  onTierChange: (tier: Tier) => void;
  muted: boolean;
  onToggleMute: () => void;
}

export function Topbar({ pageStatus, tier, onTierChange, muted, onToggleMute }: TopbarProps) {
  return (
    <header
      className="flex shrink-0 items-center justify-between gap-4 border-b border-ah-gold-hairline px-4 py-2.5"
      data-testid="newsroom-topbar"
    >
      {/* Brand / right side */}
      <div className="flex min-w-0 items-center gap-3">
        <MarkDiamond size={22} className="text-ah-gold" />
        <div className="min-w-0">
          <div className="flex items-baseline gap-2">
            <h1 className="text-[15px] font-semibold leading-none tracking-tight text-ah-text">
              {COPY.pageTitle}
            </h1>
            <span className="text-[11px] leading-none text-ah-gold/80">{COPY.pageSubtitle}</span>
          </div>
          <p className="mt-1 truncate text-[10.5px] leading-none text-ah-text-faint" data-testid="focus-note">
            {COPY.focusNote}
          </p>
        </div>
      </div>

      {/* Controls / left side */}
      <div className="flex shrink-0 items-center gap-2">
        <TruthChip status={pageStatus} size="md" showFa data-testid="page-truth-chip" />

        <span
          className="inline-flex items-center gap-1.5 rounded-full border border-ah-gold/45 bg-ah-gold/10 px-2.5 py-1 text-[10.5px] text-ah-gold"
          data-testid="paper-only-pill"
          title="این نشان همیشه ثابت است و بسته نمی‌شود"
        >
          <IconLock size={12} />
          <span className="font-ah-fa">{COPY.paperOnly}</span>
        </span>

        <IconButton
          onClick={onToggleMute}
          aria-label={muted ? 'برداشتن بی‌صدایی' : 'بی‌صدا کردن'}
          title={muted ? 'بی‌صدا' : 'صدا روشن'}
          data-testid="mute-toggle"
          active={muted}
        >
          {muted ? <IconMute size={13} /> : <IconSound size={13} />}
        </IconButton>

        <div className="flex items-center gap-1 rounded-[6px] border border-ah-line p-[2px]">
          {([0, 1, 2] as const).map((t) => (
            <button
              key={t}
              type="button"
              onClick={() => onTierChange(t)}
              aria-pressed={tier === t}
              title={`ردهٔ نمایش T${t}`}
              data-testid={`tier-button-${t}`}
              className={[
                'rounded-[4px] px-1.5 py-[2px] font-ah-en text-[10px] tracking-wider transition-colors',
                tier === t ? 'bg-ah-gold/15 text-ah-gold' : 'text-ah-text-faint hover:text-ah-text-dim',
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

export default Topbar;

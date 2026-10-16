'use client';

import { TruthChip } from '@/components/truth';
import { MARKET_LABEL_EN, MARKET_LABEL_FA, PANEL } from '@/features/newsroom/lib/labels';
import { renderCount } from '@/features/newsroom/lib/truth';
import type { MarketFocus } from '@/features/newsroom/lib/types';

export interface MarketFocusPillsProps {
  markets: readonly MarketFocus[];
  active: string | null;
  onSelect?: (marketId: 'OIL' | 'GOLD') => void;
}

/**
 * Oil & Gold are active; every other market is a grey «متصل نیست» / PLANNED
 * outline with **zero** invented headlines (`storyCount: null` ⇒ «—»).
 */
export function MarketFocusPills({ markets, active, onSelect }: MarketFocusPillsProps) {
  return (
    <div
      className="flex flex-wrap items-center gap-1.5"
      role="group"
      aria-label={PANEL.markets}
      data-testid="market-focus-pills"
    >
      {markets.map((market) => {
        const connected = market.connected;
        const isActive = connected && active === market.id;
        const label = `${MARKET_LABEL_FA[market.id]} · ${MARKET_LABEL_EN[market.id]}`;

        if (!connected) {
          return (
            <span
              key={market.id}
              aria-disabled="true"
              title={market.noteFa ?? 'متصل نیست · PLANNED'}
              data-testid={`market-pill-${market.id}`}
              data-connected="false"
              className="inline-flex cursor-not-allowed items-center gap-1.5 rounded-full border border-dashed border-ah-line px-2.5 py-1 text-[11px] text-ah-text-faint"
            >
              <span className="font-ah-fa">{MARKET_LABEL_FA[market.id]}</span>
              <span className="font-ah-en text-[9px] tracking-[0.12em] opacity-70">
                {MARKET_LABEL_EN[market.id]}
              </span>
              <span className="text-ah-text-faint">·</span>
              <span className="font-ah-fa text-[10px]">متصل نیست</span>
              <TruthChip status="PLANNED" size="xs" hideDot />
              <span className="ah-mono text-[10px] text-ah-unknown" title="تعداد خبر ساخته نمی‌شود">
                {renderCount(market.storyCount)}
              </span>
            </span>
          );
        }

        return (
          <button
            key={market.id}
            type="button"
            onClick={() => onSelect?.(market.id as 'OIL' | 'GOLD')}
            aria-pressed={isActive}
            title={market.noteFa ?? label}
            data-testid={`market-pill-${market.id}`}
            data-connected="true"
            className={[
              'inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] transition-colors duration-150',
              isActive
                ? 'border-ah-gold/60 bg-ah-gold/12 text-ah-gold-strong'
                : 'border-ah-line-strong bg-ah-surface-2 text-ah-text-dim hover:border-ah-gold/40 hover:text-ah-text',
            ].join(' ')}
          >
            <span className="font-ah-fa">{MARKET_LABEL_FA[market.id]}</span>
            <span className="font-ah-en text-[9px] tracking-[0.12em] opacity-70">
              {MARKET_LABEL_EN[market.id]}
            </span>
            <span className="ah-mono text-[10px] text-ah-text-faint">
              {renderCount(market.storyCount)}
            </span>
          </button>
        );
      })}
    </div>
  );
}

export default MarketFocusPills;

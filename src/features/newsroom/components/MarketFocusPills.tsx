"use client";
import { tr } from "@/src/lib/i18n";

import { TruthChip } from '@/src/features/newsroom/truth';
import { MARKET_LABEL_EN, MARKET_LABEL_FA, PANEL } from '@/src/features/newsroom/lib/labels';
import { renderCount } from '@/src/features/newsroom/lib/truth';
import type { MarketFocus } from '@/src/features/newsroom/lib/types';

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
              title={market.noteFa ?? tr("fa", "newsroom.ui.MarketFocusPills_1")}
              data-testid={`market-pill-${market.id}`}
              data-connected="false"
              className="inline-flex cursor-not-allowed items-center gap-1.5 rounded-full border border-dashed border-nw-line px-2.5 py-1 text-[12px] text-nw-text-faint"
            >
              <span className="font-nw-fa">{MARKET_LABEL_FA[market.id]}</span>
              <span className="font-nw-en text-[12px] tracking-[0.12em] opacity-70">
                {MARKET_LABEL_EN[market.id]}
              </span>
              <span className="text-nw-text-faint">·</span>
              <span className="font-nw-fa text-[12px]">{tr("fa", "newsroom.ui.MarketFocusPills_2")}</span>
              <TruthChip status="PLANNED" size="xs" hideDot />
              <span className="nw-mono text-[12px] text-nw-unknown" title={tr("fa", "newsroom.ui.MarketFocusPills_3")}>
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
              'inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[12px] transition-colors duration-150',
              isActive
                ? 'border-nw-gold/60 bg-nw-gold/12 text-nw-gold-strong'
                : 'border-nw-line-strong bg-nw-surface-2 text-nw-text-dim hover:border-nw-gold/40 hover:text-nw-text',
            ].join(' ')}
          >
            <span className="font-nw-fa">{MARKET_LABEL_FA[market.id]}</span>
            <span className="font-nw-en text-[12px] tracking-[0.12em] opacity-70">
              {MARKET_LABEL_EN[market.id]}
            </span>
            <span className="nw-mono text-[12px] text-nw-text-faint">
              {renderCount(market.storyCount)}
            </span>
          </button>
        );
      })}
    </div>
  );
}

export default MarketFocusPills;
'use client';

import { useSnap } from '@/components/ahos/use-command-snapshot';
import { Hero } from './hero';
import { KpiCards } from './kpi-cards';
import { GlobeStage } from './globe-stage';
import { MarketScan } from './market-scan';
import { DecisionCard } from './decision-card';
import { RiskGauge } from './risk-gauge';
import { IntelligenceFeed } from './intelligence-feed';
import { QuickActions } from './quick-actions';
import { BottomRow } from './bottom-row';
import { Dock } from './dock';

/**
 * The AHOS command-center overview (MASTER_SPEC "Layout to match").
 *
 * One fetch, one read model: `/api/command` is pulled once here and handed down
 * as props, so the panels stay presentational and the page makes a single round
 * trip per poll instead of ten. A failed fetch keeps the last good payload and
 * raises `stale`; the panels do not know the difference — they show what they
 * have, and the top bar's chips carry the freshness verdict (AGENTS.md
 * presentation-only rule).
 *
 * Layout: hero + KPI row full width, then a two-column body — the globe, the
 * market scan and the bottom row on the reading side; the authority rail
 * (decision, risk, feed, quick actions) on the other — then the dock.
 */
export function AhosOverview() {
  const { data, stale } = useSnap();

  return (
    <div className='flex flex-col gap-4 p-4' dir='rtl'>
      <Hero snap={data} />
      <KpiCards snap={data} />

      <div className='grid gap-4 xl:grid-cols-[minmax(0,1fr)_360px]'>
        <div className='flex min-w-0 flex-col gap-4'>
          <GlobeStage snap={data} />
          <MarketScan snap={data} />
        </div>

        <div className='flex min-w-0 flex-col gap-4'>
          <DecisionCard snap={data} />
          <RiskGauge snap={data} />
          <IntelligenceFeed snap={data} />
          <QuickActions />
        </div>
      </div>

      <BottomRow snap={data} />
      <Dock />

      {stale ? (
        <p dir='rtl' className='text-center text-[10px] text-[var(--ahos-status-stale)]'>
          دریافتِ تازه ناموفق بود — داده‌های بالا از آخرین دریافتِ موفق هستند.
        </p>
      ) : null}
    </div>
  );
}

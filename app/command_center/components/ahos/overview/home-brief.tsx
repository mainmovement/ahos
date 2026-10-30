'use client';

import type { Snap } from '@/dashboard_snapshot';

/**
 * The owner home. Numbers come from the Python status file. This view does not decide.
 */
export function HomeBrief({ snap }: { snap: Snap | null }) {
  const home = snap?.home;
  const equity = home?.equityUsd ?? snap?.paperLane?.markToMarketEquityUsd ?? null;
  const opens = home?.openNames ?? [];
  const lessons = home?.lessonsFa ?? [];
  const pct = home?.readinessPct;
  const equityText = typeof equity === 'number' ? `${equity.toFixed(2)} دلار` : 'نامشخص';
  const pctText = typeof pct === 'number' ? `${pct}٪` : 'نامشخص';

  return (
    <section dir='rtl' className='rounded-xl border border-[var(--ahos-line,rgba(255,255,255,0.12))] p-4'>
      <h1 className='text-xl'>خانه</h1>
      <p className='mt-2 text-sm'>معاملهٔ واقعی خاموش است.</p>
      <dl className='mt-4 grid gap-3 sm:grid-cols-2'>
        <div>
          <dt className='text-xs opacity-70'>سرمایهٔ کاغذی</dt>
          <dd className='text-lg'>{equityText}</dd>
        </div>
        <div>
          <dt className='text-xs opacity-70'>آمادگی پول واقعی</dt>
          <dd className='text-lg'>{pctText}</dd>
        </div>
        <div>
          <dt className='text-xs opacity-70'>موقعیت باز</dt>
          <dd>{opens.length ? opens.join('، ') : 'موقعیت بازی در این نما نیست'}</dd>
        </div>
        <div>
          <dt className='text-xs opacity-70'>درس امروز</dt>
          <dd>{lessons.length ? lessons.join(' ') : 'درس تازه‌ای در پرونده نیست.'}</dd>
        </div>
      </dl>
    </section>
  );
}

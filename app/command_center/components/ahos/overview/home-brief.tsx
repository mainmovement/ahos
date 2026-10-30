'use client';

import type { Snap } from '@/dashboard_snapshot';

/**
 * Minimal owner home. Numbers come from the Python status file (mehrdad_status.json
 * via the snapshot). This view does not decide and invents nothing: a missing value
 * shows as «—».
 */
export function HomeBrief({ snap, stale }: { snap: Snap | null; stale?: boolean }) {
  const home = snap?.home;
  const equity = home?.equityUsd ?? snap?.paperLane?.markToMarketEquityUsd ?? null;
  const opens = home?.openNames ?? [];
  const lesson = (home?.lessonsFa ?? [])[0] ?? null;
  const pct = typeof home?.readinessPct === 'number' ? home.readinessPct : null;
  const healthy = Boolean(snap) && !stale;

  return (
    <section dir='rtl' className='mx-auto flex w-full max-w-3xl flex-col gap-8 py-6'>
      <div className='flex items-center justify-between'>
        <span className='flex items-center gap-2 text-sm opacity-80'>
          <span
            aria-hidden
            className={`inline-block h-2.5 w-2.5 rounded-full ${healthy ? 'bg-emerald-400' : 'bg-red-500'}`}
          />
          {healthy ? 'سالم' : 'مشکل'}
        </span>
      </div>

      <div className='text-center'>
        <div className='text-sm opacity-60'>موجودی</div>
        <div className='mt-1 text-5xl font-light tabular-nums' dir='ltr'>
          {typeof equity === 'number' ? `$${equity.toFixed(2)}` : '—'}
        </div>
      </div>

      <div>
        <div className='mb-2 text-sm opacity-60'>معاملات باز · {opens.length}</div>
        <div className='flex flex-wrap gap-2'>
          {opens.length ? (
            opens.map((n) => (
              <span key={n} dir='ltr' className='rounded-full border border-white/15 px-3 py-1 text-sm'>
                {n}
              </span>
            ))
          ) : (
            <span className='opacity-50'>—</span>
          )}
        </div>
      </div>

      <div>
        <div className='mb-1 text-sm opacity-60'>درس امروز</div>
        <p className='truncate text-lg'>{lesson ?? '—'}</p>
      </div>

      <div>
        <div className='mb-2 flex justify-between text-sm opacity-60'>
          <span>آمادگی پول واقعی</span>
          <span>{pct === null ? '—' : `${pct}٪`}</span>
        </div>
        <div className='h-2 w-full overflow-hidden rounded-full bg-white/10'>
          <div className='h-full rounded-full bg-[#D4AF37]' style={{ width: `${Math.max(0, Math.min(100, pct ?? 0))}%` }} />
        </div>
      </div>
    </section>
  );
}

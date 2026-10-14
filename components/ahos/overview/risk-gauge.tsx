'use client';

import type { Snap, Dim } from '@/dashboard_snapshot';
import { faNum } from '@/dashboard_snapshot';
import { GlowCard, PanelTitle, Waiting } from './primitives';

/**
 * MASTER_SPEC "Security & Risk gauge".
 *
 * `health.dimensions` is the engine's own per-dimension verdict list; this card
 * tallies those verdicts for display and shows each dimension's evidence line.
 * The tally is arithmetic over emitted statuses — no dimension is re-evaluated
 * here, and a dimension the engine has not assessed is counted as unknown, not
 * as healthy.
 */

type Bucket = 'ok' | 'warn' | 'unknown';

function bucketOf(dim: Dim): Bucket {
  const s = (dim.status ?? '').toUpperCase();
  if (s.includes('OK') || s.includes('HEALTHY') || s.includes('PASS') || s.includes('VERIFIED')) return 'ok';
  if (s.includes('WARN') || s.includes('STALE') || s.includes('DEGRADED') || s.includes('FAIL')) return 'warn';
  return 'unknown';
}

const BUCKET_COLOR: Record<Bucket, string> = {
  ok: 'var(--ahos-status-verified)',
  warn: 'var(--ahos-status-stale)',
  unknown: 'var(--ahos-status-unknown)'
};

const BUCKET_LABEL: Record<Bucket, string> = {
  ok: 'سالم',
  warn: 'هشدار',
  unknown: 'نامشخص'
};

/** A donut of the three buckets; empty list draws a neutral grey ring. */
function HealthDonut({ dims }: { dims: Dim[] }) {
  const counts: Record<Bucket, number> = { ok: 0, warn: 0, unknown: 0 };
  dims.forEach((d) => (counts[bucketOf(d)] += 1));
  const total = dims.length;
  const R = 30;
  const C = 2 * Math.PI * R;

  let offset = 0;
  const arcs = (['ok', 'warn', 'unknown'] as Bucket[])
    .filter((b) => counts[b] > 0)
    .map((b) => {
      const frac = counts[b] / total;
      const seg = (
        <circle
          key={b}
          cx='44'
          cy='44'
          r={R}
          fill='none'
          stroke={BUCKET_COLOR[b]}
          strokeWidth='9'
          strokeDasharray={`${frac * C} ${C - frac * C}`}
          strokeDashoffset={-offset * C}
        />
      );
      offset += frac;
      return seg;
    });

  return (
    <div className='flex items-center gap-4' dir='ltr'>
      <div className='relative size-24 shrink-0'>
        {total === 0 ? (
          <svg viewBox='0 0 88 88' className='size-24'>
            <circle cx='44' cy='44' r={R} fill='none' stroke='var(--border)' strokeWidth='9' />
          </svg>
        ) : (
          <svg viewBox='0 0 88 88' className='size-24 -rotate-90'>
            {arcs}
          </svg>
        )}
        <div className='absolute inset-0 flex flex-col items-center justify-center'>
          <span className='font-mono text-lg font-semibold tabular-nums text-foreground'>
            {faNum(counts.ok, 0)}
          </span>
          <span className='text-[9px] text-muted-foreground'>از {faNum(total, 0)}</span>
        </div>
      </div>
      <div className='space-y-1.5'>
        {(['ok', 'warn', 'unknown'] as Bucket[]).map((b) => (
          <div key={b} className='flex items-center gap-2 text-[11px]'>
            <span
              className='inline-block size-2.5 rounded-sm'
              style={{ backgroundColor: BUCKET_COLOR[b] }}
              aria-hidden
            />
            <span className='text-muted-foreground'>{BUCKET_LABEL[b]}</span>
            <span className='font-mono tabular-nums text-foreground'>{faNum(counts[b], 0)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export function RiskGauge({ snap }: { snap: Snap | null }) {
  const dims = snap?.health?.dimensions ?? [];

  return (
    <GlowCard glow={dims.some((d) => bucketOf(d) === 'warn') ? 'cyan' : 'none'}>
      <PanelTitle icon={<span className='text-accent'>⛨</span>}>امنیت و ریسک</PanelTitle>
      {dims.length === 0 ? (
        <Waiting label={snap ? 'بُعدی ارزیابی نشده' : 'در انتظارِ داده'} className='h-52' />
      ) : (
        <div className='space-y-3 px-4 pb-4'>
          <HealthDonut dims={dims} />
          <ul className='space-y-1.5' dir='rtl'>
            {dims.slice(0, 5).map((d) => (
              <li key={d.nameFa} className='flex items-center justify-between gap-2 text-[11px]'>
                <span className='flex items-center gap-1.5 text-muted-foreground'>
                  <span
                    className='inline-block size-1.5 shrink-0 rounded-full'
                    style={{ backgroundColor: BUCKET_COLOR[bucketOf(d)] }}
                    aria-hidden
                  />
                  {d.nameFa}
                </span>
                <span
                  className='shrink-0 font-mono text-[10px]'
                  style={{ color: BUCKET_COLOR[bucketOf(d)] }}
                  title={d.evidenceFa}
                >
                  {d.status}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </GlowCard>
  );
}

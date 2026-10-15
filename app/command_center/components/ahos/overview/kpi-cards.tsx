'use client';

import { useEffect, useRef, useState } from 'react';
import { Area, AreaChart, ResponsiveContainer } from 'recharts';
import type { Snap, CanonicalDecision } from '@/dashboard_snapshot';
import { faNum } from '@/dashboard_snapshot';
import { GlowCard, faDigits } from './primitives';

/**
 * MASTER_SPEC "KPI cards row with sparklines (Total/Verified/Monitor/Rejected)".
 *
 * Presentation only (AGENTS.md). The four counts are *tallies of decisions the
 * Python authority already made* — they are not scored, ranked or decided here;
 * nothing is promoted, and a decision the canonical layer has not emitted does
 * not appear. When the snapshot has not arrived the card shows the waiting state
 * with no numbers, never a zero that would read as "nothing was found".
 *
 * The sparkline is the honest part: it is a rolling history of what this card
 * itself displayed across polls, appended whenever `/api/command` returns a new
 * `generatedAt`. A single poll draws a flat line rather than a plausible trend —
 * no series is invented to fill the chart.
 */

interface KpiPoint {
  t: number;
  total: number;
  verified: number;
  monitor: number;
  rejected: number;
}

const HISTORY = 24;

function tally(decisions: CanonicalDecision[] | undefined) {
  const list = decisions ?? [];
  return {
    verified: list.filter((d) => d.isPositive && d.paperAllowed).length,
    monitor: list.filter((d) => d.monitoringOnly).length,
    rejected: list.filter((d) => !d.isPositive).length
  };
}

export function KpiCards({ snap }: { snap: Snap | null }) {
  const [history, setHistory] = useState<KpiPoint[]>([]);
  const lastGen = useRef<string | null>(null);

  useEffect(() => {
    if (!snap || snap.generatedAt === lastGen.current) return;
    lastGen.current = snap.generatedAt;
    const t = tally(snap.canonicalDecisions);
    setHistory((prev) =>
      [...prev, { t: Date.now(), total: snap.opportunities.length, ...t }].slice(-HISTORY)
    );
  }, [snap]);

  const t = tally(snap?.canonicalDecisions);
  const total = snap?.opportunities.length ?? 0;
  const prev = history.length > 1 ? history[history.length - 2] : null;

  const cards: Array<{
    key: keyof Omit<KpiPoint, 't'>;
    label: string;
    value: number;
    tone: string;
    stroke: string;
  }> = [
    { key: 'total', label: 'کلِ فرصت‌ها', value: total, tone: 'text-foreground', stroke: 'var(--chart-3)' },
    { key: 'verified', label: 'تأییدِ کاغذی', value: t.verified, tone: 'text-primary', stroke: 'var(--chart-1)' },
    { key: 'monitor', label: 'پایش', value: t.monitor, tone: 'text-accent', stroke: 'var(--chart-2)' },
    { key: 'rejected', label: 'رد‌شده', value: t.rejected, tone: 'text-destructive', stroke: 'var(--destructive)' }
  ];

  return (
    <div className='grid grid-cols-2 gap-3 lg:grid-cols-4'>
      {cards.map((c) => {
        const series = history.map((p) => ({ v: p[c.key] }));
        const delta = prev ? c.value - prev[c.key] : null;
        return (
          <GlowCard key={c.key} glow={c.key === 'verified' ? 'gold' : 'none'} className='gap-0 px-4 py-3.5'>
            <div className='flex items-baseline justify-between gap-2'>
              <span className='text-[11px] font-medium text-muted-foreground'>{c.label}</span>
              {delta === null || delta === 0 ? null : (
                <span
                  dir='ltr'
                  className={`font-mono text-[10px] tabular-nums ${delta > 0 ? 'text-[var(--ahos-status-verified)]' : 'text-[var(--ahos-status-rejected)]'}`}
                >
                  {delta > 0 ? '▲' : '▼'} {faDigits(Math.abs(delta))}
                </span>
              )}
            </div>
            {snap ? (
              <>
                <div className={`mt-1 font-mono text-2xl font-semibold tabular-nums ${c.tone}`}>
                  {faNum(c.value, 0)}
                </div>
                <div className='-mx-1 mt-1 h-8' dir='ltr'>
                  <ResponsiveContainer width='100%' height='100%'>
                    <AreaChart data={series} margin={{ top: 2, right: 0, bottom: 0, left: 0 }}>
                      <defs>
                        <linearGradient id={`kpi-${c.key}`} x1='0' y1='0' x2='0' y2='1'>
                          <stop offset='0%' stopColor={c.stroke} stopOpacity={0.35} />
                          <stop offset='100%' stopColor={c.stroke} stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <Area
                        type='monotone'
                        dataKey='v'
                        stroke={c.stroke}
                        strokeWidth={1.5}
                        fill={`url(#kpi-${c.key})`}
                        isAnimationActive={false}
                        dot={false}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </>
            ) : (
              <div className='mt-1 flex h-12 items-center text-[11px] text-muted-foreground/70'>
                در حال دریافت…
              </div>
            )}
          </GlowCard>
        );
      })}
    </div>
  );
}

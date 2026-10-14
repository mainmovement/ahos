'use client';

import Link from 'next/link';
import { Bar, BarChart, Cell, ReferenceLine, ResponsiveContainer, XAxis } from 'recharts';
import type { Snap, PaperPosition } from '@/dashboard_snapshot';
import { faNum } from '@/dashboard_snapshot';
import { GlowCard, PanelTitle, Waiting } from './primitives';

/**
 * MASTER_SPEC "Bottom row: University/Research Lab, Agent Society, Auto Trading
 * performance chart, Chat with AHOS".
 *
 * Four panels, each on its own slice of the read model. The performance chart is
 * the paper ledger's open positions plotted by realised-on-paper percent — a
 * display of what the ledger already holds, never a prediction; a position
 * without both prices is skipped rather than plotted at zero.
 */

function pnlOf(p: PaperPosition): number | null {
  if (p.entryPrice === null || p.lastPrice === null || p.entryPrice === 0) return null;
  return ((p.lastPrice - p.entryPrice) / p.entryPrice) * 100;
}

function UniversityPanel({ snap }: { snap: Snap | null }) {
  const lessons = snap?.lessons ?? [];
  return (
    <GlowCard glow='none' className='min-h-44'>
      <PanelTitle icon={<span className='text-primary'>✧</span>} hint={lessons.length ? `${faNum(lessons.length, 0)} درس` : undefined}>
        دانشگاه / آزمایشگاه
      </PanelTitle>
      {lessons.length === 0 ? (
        <Waiting label={snap ? 'هنوز درسی ثبت نشده' : 'در انتظارِ داده'} className='flex-1' />
      ) : (
        <ul className='space-y-2 px-4 pb-4' dir='rtl'>
          {lessons.slice(0, 3).map((l) => (
            <li key={l.id} className='flex gap-2'>
              <span aria-hidden className='mt-1 size-1 shrink-0 rounded-full bg-primary/70' />
              <div className='min-w-0'>
                <p className='line-clamp-1 text-[11px] font-medium text-foreground'>{l.titleFa}</p>
                <p className='line-clamp-1 text-[10px] text-muted-foreground'>{l.bodyFa}</p>
              </div>
            </li>
          ))}
        </ul>
      )}
    </GlowCard>
  );
}

function SocietyPanel({ snap }: { snap: Snap | null }) {
  const teams = snap?.teams ?? [];
  const agents = teams.reduce((sum, t) => sum + (t.size ?? 0), 0);
  return (
    <GlowCard glow='cyan' className='min-h-44'>
      <PanelTitle icon={<span className='text-accent'>❖</span>} hint={agents ? `${faNum(agents, 0)} عامل` : undefined}>
        جامعهٔ عامل‌ها
      </PanelTitle>
      {teams.length === 0 ? (
        <Waiting label={snap ? 'تیمی فعال نیست' : 'در انتظارِ داده'} className='flex-1' />
      ) : (
        <ul className='flex flex-col gap-1.5 px-4 pb-4' dir='rtl'>
          {teams.slice(0, 4).map((t) => (
            <li key={t.id} className='flex items-center justify-between gap-2 text-[11px]'>
              <span className='text-muted-foreground'>{t.fa}</span>
              <span dir='ltr' className='font-mono tabular-nums text-foreground'>
                {faNum(t.size, 0)} agent
              </span>
            </li>
          ))}
        </ul>
      )}
    </GlowCard>
  );
}

function PerformancePanel({ snap }: { snap: Snap | null }) {
  const positions = (snap?.paper ?? [])
    .map((p) => ({ p, pnl: pnlOf(p) }))
    .filter((x) => x.pnl !== null) as Array<{ p: PaperPosition; pnl: number }>;
  const data = positions.slice(0, 8).map((x) => ({ symbol: x.p.symbol, pnl: x.pnl }));
  const open = snap?.paper?.length ?? 0;

  return (
    <GlowCard glow='gold' className='min-h-44'>
      <PanelTitle icon={<span className='text-primary'>▮</span>} hint={open ? `${faNum(open, 0)} موقعیت کاغذی` : undefined}>
        عملکردِ معاملهٔ خودکار
      </PanelTitle>
      {data.length === 0 ? (
        <Waiting label={snap ? 'موقعیتِ کاغذیِ بازی وجود ندارد' : 'در انتظارِ داده'} className='flex-1' />
      ) : (
        <div className='px-4 pb-4' dir='ltr'>
          <ResponsiveContainer width='100%' height={132}>
            <BarChart data={data} margin={{ top: 4, right: 0, bottom: 0, left: 0 }}>
              <ReferenceLine y={0} stroke='var(--border)' />
              <XAxis
                dataKey='symbol'
                tick={{ fill: 'var(--muted-foreground)', fontSize: 9 }}
                tickLine={false}
                axisLine={false}
                interval={0}
                height={16}
              />
              <Bar dataKey='pnl' radius={[3, 3, 0, 0]} maxBarSize={26}>
                {data.map((d) => (
                  <Cell
                    key={d.symbol}
                    fill={d.pnl >= 0 ? 'var(--ahos-status-verified)' : 'var(--ahos-status-rejected)'}
                    fillOpacity={0.75}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <p dir='rtl' className='mt-1 text-[10px] text-muted-foreground'>
            درصدِ تغییرِ قیمتِ ورود به آخرین قیمت — دفترِ کاغذی، نه پیش‌بینی.
          </p>
        </div>
      )}
    </GlowCard>
  );
}

function ChatPanel() {
  return (
    <GlowCard glow='cyan' className='min-h-44'>
      <PanelTitle icon={<span className='text-accent'>✆</span>}>گفت‌وگو با AHOS</PanelTitle>
      <div className='flex flex-1 flex-col justify-between gap-3 px-4 pb-4'>
        <p dir='rtl' className='text-[11px] leading-relaxed text-muted-foreground'>
          از AHOS دربارهٔ شواهد، دروازهٔ امنیتی و دلیلِ تصمین‌ها بپرسید. پاسخ‌ها
          توصیه‌ای هستند، نه مرجع.
        </p>
        <Link
          href='/chat'
          className='flex items-center justify-between gap-2 rounded-xl border border-accent/35 bg-accent/5 px-3 py-2 text-xs font-medium text-accent transition-colors hover:bg-accent/15'
        >
          <span dir='rtl'>شروعِ گفت‌وگو</span>
          <span aria-hidden>←</span>
        </Link>
      </div>
    </GlowCard>
  );
}

export function BottomRow({ snap }: { snap: Snap | null }) {
  return (
    <div className='grid gap-3 sm:grid-cols-2 xl:grid-cols-4'>
      <UniversityPanel snap={snap} />
      <SocietyPanel snap={snap} />
      <PerformancePanel snap={snap} />
      <ChatPanel />
    </div>
  );
}

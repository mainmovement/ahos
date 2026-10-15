'use client';

import { greeting } from '@/lib/operator';
import type { Snap } from '@/dashboard_snapshot';
import { faNum } from '@/dashboard_snapshot';
import { GlowCard } from './primitives';

/**
 * MASTER_SPEC "Hero banner: greeting + cinematic background".
 *
 * The greeting is computed on the client (the server's clock would be stale by
 * the time the markup lands). The status line is the snapshot's own engine state
 * — nothing here is asserted, only reported.
 */
export function Hero({ snap }: { snap: Snap | null }) {
  const regime = snap?.market?.regime ?? null;
  const cycle = snap?.state?.cycleCount ?? null;
  const tokens = snap?.cycle?.tokenCount ?? null;

  return (
    <GlowCard glow='gold' className='relative isolate min-h-32 overflow-hidden px-5 py-4'>
      {/* Cinematic backdrop: the brand's dark-to-gold light (owner ref 02),
          rendered with CSS only — no fetched texture, no external asset. */}
      <div aria-hidden className='absolute inset-0 -z-10'>
        <div className='absolute inset-0 bg-[radial-gradient(120%_140%_at_85%_0%,rgba(212,175,58,0.20),transparent_55%)]' />
        <div className='absolute inset-0 bg-[radial-gradient(90%_120%_at_10%_110%,rgba(63,208,255,0.14),transparent_60%)]' />
        <div className='absolute inset-0 bg-[conic-gradient(from_200deg_at_70%_30%,rgba(212,175,58,0.10),transparent_30%)]' />
        <div className='absolute inset-0 bg-[linear-gradient(to_left,transparent,rgba(4,7,20,0.35))] rtl:bg-[linear-gradient(to_right,transparent,rgba(4,7,20,0.35))]' />
      </div>

      <div className='flex flex-wrap items-end justify-between gap-4'>
        <div className='space-y-1.5'>
          <p className='text-[11px] font-medium uppercase tracking-[0.3em] text-primary/80'>AHOS · Command Center</p>
          <h2 className='font-serif text-2xl font-semibold text-foreground sm:text-3xl'>{greeting()}</h2>
          <p className='max-w-2xl text-xs leading-relaxed text-muted-foreground'>
            سامانهٔ هوشمندیِ فرصت — آرشیو و پایشِ روی کاغذ. هر تصمین کانونیکال از
            موتورِ پایتون می‌آید؛ این نمایش فقط گزارش می‌کند.
          </p>
        </div>

        <div dir='ltr' className='flex flex-wrap items-center gap-2 text-[11px]'>
          <StatChip label='REGIME' value={regime ?? '—'} tone={regime ? 'gold' : 'muted'} />
          <StatChip
            label='CYCLES'
            value={cycle === null ? '—' : faNum(cycle, 0)}
            tone={cycle === null ? 'muted' : 'cyan'}
          />
          <StatChip
            label='TOKENS'
            value={tokens === null ? '—' : faNum(tokens, 0)}
            tone={tokens === null ? 'muted' : 'cyan'}
          />
        </div>
      </div>
    </GlowCard>
  );
}

function StatChip({
  label,
  value,
  tone
}: {
  label: string;
  value: string;
  tone: 'gold' | 'cyan' | 'muted';
}) {
  const toneClass =
    tone === 'gold'
      ? 'border-primary/40 bg-primary/10 text-primary'
      : tone === 'cyan'
        ? 'border-accent/40 bg-accent/10 text-accent'
        : 'border-border/60 bg-muted/40 text-muted-foreground';
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 font-mono tabular-nums ${toneClass}`}
    >
      <span className='opacity-70'>{label}</span>
      <span className='font-semibold'>{value}</span>
    </span>
  );
}

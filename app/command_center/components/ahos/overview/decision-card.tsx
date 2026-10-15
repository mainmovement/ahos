'use client';

import type { Snap, CanonicalDecision } from '@/dashboard_snapshot';
import { faNum } from '@/dashboard_snapshot';
import { GlowCard, PanelTitle, Waiting } from './primitives';

/**
 * MASTER_SPEC "Canonical Decision card with score ring".
 *
 * The one card on the overview that carries an authority verdict, and every word
 * of it comes from `canonicalDecisions` — the Python decision authority wrapped
 * by the TS API. Nothing here upgrades, downgrades or interprets: the ring draws
 * the score the authority already computed, and the reason line is the
 * authority's own `primaryReason`. When the canonical layer has emitted no
 * decision, the card says so rather than picking a token to feature.
 */

function pick(decisions: CanonicalDecision[] | undefined): CanonicalDecision | null {
  const list = decisions ?? [];
  if (list.length === 0) return null;
  return list.slice().sort((a, b) => (b.opportunityScore ?? -1) - (a.opportunityScore ?? -1))[0];
}

function ScoreRing({ score }: { score: number | null }) {
  const r = 34;
  const c = 2 * Math.PI * r;
  const ok = score !== null && score !== undefined && Number.isFinite(score);
  const pct = ok ? Math.min(100, Math.max(0, score as number)) : 0;
  return (
    <div className='relative size-24 shrink-0' dir='ltr'>
      <svg viewBox='0 0 88 88' className='size-24 -rotate-90'>
        <circle cx='44' cy='44' r={r} fill='none' stroke='var(--muted)' strokeWidth='6' />
        <circle
          cx='44'
          cy='44'
          r={r}
          fill='none'
          stroke={ok ? 'url(#decision-ring)' : 'var(--border)'}
          strokeWidth='6'
          strokeLinecap='round'
          strokeDasharray={c}
          strokeDashoffset={ok ? c * (1 - pct / 100) : c}
        />
        <defs>
          <linearGradient id='decision-ring' x1='0' y1='0' x2='1' y2='1'>
            <stop offset='0%' stopColor='var(--primary)' />
            <stop offset='100%' stopColor='var(--accent)' />
          </linearGradient>
        </defs>
      </svg>
      <div className='absolute inset-0 flex flex-col items-center justify-center'>
        <span className='font-mono text-xl font-semibold tabular-nums text-foreground'>
          {faNum(score, 1)}
        </span>
        <span className='text-[9px] uppercase tracking-wider text-muted-foreground'>score</span>
      </div>
    </div>
  );
}

export function DecisionCard({ snap }: { snap: Snap | null }) {
  const d = pick(snap?.canonicalDecisions);
  const meta = snap?.canonicalReadModel ?? null;

  return (
    <GlowCard glow='gold'>
      <PanelTitle
        icon={<span className='text-primary'>◆</span>}
        hint={meta ? `${faNum(meta.decisionCount, 0)} تصمین` : undefined}
      >
        تصمینِ کانونیکال
      </PanelTitle>
      {d === null ? (
        <Waiting label={snap ? 'هنوز تصمین کانونیکالی صادر نشده' : 'در انتظارِ داده'} className='h-52' />
      ) : (
        <div className='flex gap-4 px-4 pb-4'>
          <ScoreRing score={d.opportunityScore} />
          <div className='min-w-0 flex-1 space-y-2'>
            <div className='flex items-baseline gap-2'>
              <span dir='ltr' className='font-mono text-base font-semibold text-foreground'>
                {d.symbol ?? '—'}
              </span>
              <span className='text-[11px] text-muted-foreground'>{d.chain}</span>
            </div>
            <div className='flex flex-wrap gap-1.5' dir='ltr'>
              <span
                className={`rounded-full border px-2 py-0.5 text-[10px] font-medium ${d.isPositive ? 'border-primary/40 bg-primary/10 text-primary' : 'border-destructive/40 bg-destructive/10 text-destructive'}`}
              >
                {d.outcome}
              </span>
              <span
                className={`rounded-full border px-2 py-0.5 text-[10px] font-medium ${d.paperAllowed ? 'border-[var(--ahos-status-verified)]/40 bg-[var(--ahos-status-verified)]/10 text-[var(--ahos-status-verified)]' : 'border-border/60 bg-muted/40 text-muted-foreground'}`}
              >
                {d.paperAllowed ? 'PAPER OK' : 'PAPER BLOCKED'}
              </span>
              {d.confidence ? (
                <span className='rounded-full border border-border/60 bg-muted/40 px-2 py-0.5 text-[10px] text-muted-foreground'>
                  {d.confidence}
                </span>
              ) : null}
            </div>
            <p dir='rtl' className='line-clamp-3 text-[11px] leading-relaxed text-muted-foreground'>
              {d.primaryReason ?? 'دلیلی توسط مرجع صادر نشده.'}
            </p>
            <div className='flex flex-wrap gap-2 text-[10px] text-muted-foreground/80'>
              <span>هویت: {d.identityState ?? '—'}</span>
              <span>·</span>
              <span>امنیت: {d.securityState ?? '—'}</span>
            </div>
          </div>
        </div>
      )}
    </GlowCard>
  );
}

'use client';

import { useCallback, useEffect, useState } from 'react';
import StageLazy from '@/components/stage/StageLazy';
import { useStageStore } from '@/components/stage/store';
import { probeQuality, TIER_LABELS, type TierVerdict } from '@/components/stage/quality';
import type { Snap, Opp } from '@/dashboard_snapshot';
import { GlowCard, PanelTitle, Waiting } from './primitives';

/**
 * MASTER_SPEC "CENTER: holographic 3D globe with orbit rings and floating
 * opportunity badges, on a glowing pedestal".
 *
 * The globe itself is the existing `components/stage` observatory — reused, not
 * rebuilt (owner order 2026-10-13 23:03). It is gated behind the same hardware
 * probe the Dashi shell uses, so a machine without WebGL gets the 2D notice
 * instead of a broken canvas, and a lost context is recoverable with one click.
 *
 * The floating badges are the snapshot's top opportunities; each badge states
 * what the canonical layer said about that token (security state), nothing more.
 * Badge colour follows the truth tokens, never a re-score.
 */

const BADGE_SLOTS = [
  { top: '8%', start: '6%' },
  { top: '22%', start: '78%' },
  { top: '52%', start: '3%' },
  { top: '66%', start: '80%' },
  { top: '84%', start: '30%' }
];

function badgeTone(opp: Opp): string {
  const s = (opp.securityState ?? opp.securityStatus ?? '').toUpperCase();
  if (s.includes('PASS') || s.includes('VERIFIED')) return 'border-[var(--ahos-status-verified)]/50 text-[var(--ahos-status-verified)]';
  if (s.includes('REJECT')) return 'border-[var(--ahos-status-rejected)]/50 text-[var(--ahos-status-rejected)]';
  if (s.includes('CONFLICT')) return 'border-[var(--ahos-status-conflict)]/50 text-[var(--ahos-status-conflict)]';
  return 'border-[var(--ahos-status-unknown)]/50 text-[var(--ahos-status-unknown)]';
}

export function GlobeStage({ snap }: { snap: Snap | null }) {
  const verdict = useStageStore((s) => s.verdict);
  const setVerdict = useStageStore((s) => s.setVerdict);
  const contextLost = useStageStore((s) => s.contextLost);
  const setContextLost = useStageStore((s) => s.setContextLost);
  const [probing, setProbing] = useState(verdict === null);

  useEffect(() => {
    if (verdict !== null) return;
    let cancelled = false;
    void probeQuality().then((v) => {
      if (cancelled) return;
      setVerdict(v);
      setProbing(false);
    });
    return () => {
      cancelled = true;
    };
  }, [verdict, setVerdict]);

  const onContextLost = useCallback(() => setContextLost(true), [setContextLost]);
  const retry = useCallback(() => {
    setContextLost(false);
    void probeQuality().then(setVerdict);
  }, [setContextLost, setVerdict]);

  const tier = verdict?.tier ?? 'T1';
  const allowStage = verdict !== null && tier !== 'T0' && !contextLost;

  const top = (snap?.opportunities ?? [])
    .slice()
    .sort((a, b) => (b.rankScore ?? -1) - (a.rankScore ?? -1))
    .slice(0, BADGE_SLOTS.length);

  return (
    <GlowCard glow='cyan' className='min-h-[460px]'>
      <PanelTitle
        icon={<span className='text-accent'>◈</span>}
        hint={verdict ? `${TIER_LABELS[tier].fa} · ${snap?.opportunities.length ?? 0} token` : 'در حال سنجش'}
      >
        صحنهٔ رصدخانه
      </PanelTitle>

      <div className='relative flex-1'>
        {/* The glowing pedestal: a radial bloom under the globe. */}
        <div
          aria-hidden
          className='pointer-events-none absolute inset-x-0 bottom-6 h-40 bg-[radial-gradient(50%_100%_at_50%_100%,rgba(63,208,255,0.22),transparent_70%)]'
        />

        {probing ? (
          <Waiting label='در حال سنجشِ توانِ گرافیکی' className='h-[380px]' />
        ) : allowStage ? (
          <StageLazy verdict={verdict} onContextLost={onContextLost} />
        ) : (
          <div className='flex h-[380px] flex-col items-center justify-center gap-3 px-6 text-center' dir='rtl'>
            <p className='text-sm font-medium text-foreground'>نمای دو‌بعدی</p>
            <p className='max-w-sm text-xs text-muted-foreground'>
              {contextLost
                ? 'صحنهٔ سه‌بعدی از دسترس خارج شد؛ داده‌ها از بین نرفته‌اند.'
                : 'این ماشین WebGL ندارد یا طبقهٔ نمایش آن T0 است.'}
            </p>
            <button
              type='button'
              onClick={retry}
              className='rounded-lg border border-accent/40 bg-accent/10 px-3 py-1.5 text-xs font-medium text-accent transition-colors hover:bg-accent/20'
            >
              اندازه‌گیریِ دوباره
            </button>
          </div>
        )}

        {/* Floating opportunity badges — DOM, not three.js, so they stay crisp
            at every tier and remain clickable. */}
        {top.map((opp, i) => {
          const slot = BADGE_SLOTS[i % BADGE_SLOTS.length];
          return (
            <div
              key={opp.id}
              dir='ltr'
              className={`absolute flex items-center gap-2 rounded-xl border bg-popover/80 px-2.5 py-1.5 text-[11px] shadow-lg backdrop-blur-md ${badgeTone(opp)}`}
              style={{ top: slot.top, insetInlineStart: slot.start }}
            >
              <span className='font-mono font-semibold text-foreground'>{opp.symbol}</span>
              <span className='text-muted-foreground'>{opp.chain}</span>
              <span className='font-mono tabular-nums opacity-90'>
                {opp.securityState ?? opp.securityStatus ?? '—'}
              </span>
            </div>
          );
        })}
      </div>
    </GlowCard>
  );
}

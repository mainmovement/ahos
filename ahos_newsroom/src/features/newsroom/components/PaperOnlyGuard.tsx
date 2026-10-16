'use client';

import type { ReactNode } from 'react';

import { COPY } from '@/features/newsroom/lib/labels';
import { isPaperOnlyViolation } from '@/features/newsroom/lib/truth';
import type { NewsroomSnapshot } from '@/features/newsroom/lib/types';
import { IconLock } from './icons';
import { ViolationBar } from './ViolationBar';

/**
 * The permanent, non-dismissible «فقط کاغذی · PAPER_ONLY» pill.
 * It is always rendered — it never depends on data being friendly.
 */
export function PaperOnlyPill({ compact = false }: { compact?: boolean }) {
  return (
    <span
      className={[
        'inline-flex items-center gap-1.5 rounded-full border border-ah-gold/45 bg-ah-gold/10 text-ah-gold',
        compact ? 'px-2 py-[3px] text-[10px]' : 'px-2.5 py-1 text-[10.5px]',
      ].join(' ')}
      data-testid="paper-only-pill"
      title="این نشان همیشه ثابت است و بسته نمی‌شود"
    >
      <IconLock size={12} />
      <span className="font-ah-fa">{COPY.paperOnly}</span>
    </span>
  );
}

export interface PaperOnlyGuardProps {
  snapshot: NewsroomSnapshot;
  /** `?violation=1` — force the bar even on a compliant snapshot. */
  forced?: boolean;
  children: ReactNode;
}

/**
 * Renders the full-width VIOLATION bar above the page whenever the snapshot is
 * not unambiguously paper-only, then renders the page. Never offers a trading
 * control and never lets the user dismiss the bar away.
 */
export function PaperOnlyGuard({ snapshot, forced = false, children }: PaperOnlyGuardProps) {
  const violation = isPaperOnlyViolation(snapshot) || forced;

  return (
    <div
      className="flex h-screen min-h-0 flex-col overflow-hidden"
      data-testid="paper-only-guard"
      data-violation={String(violation)}
    >
      {violation ? (
        <ViolationBar
          executionMode={snapshot.executionMode}
          realTrading={snapshot.realTrading}
          forced={forced}
        />
      ) : null}
      {children}
    </div>
  );
}

export default PaperOnlyGuard;

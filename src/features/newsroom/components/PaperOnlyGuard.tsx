"use client";
import { tr } from "@/src/lib/i18n";

import type { ReactNode } from 'react';

import { COPY } from '@/src/features/newsroom/lib/labels';
import { isPaperOnlyViolation } from '@/src/features/newsroom/lib/truth';
import type { NewsroomSnapshot } from '@/src/features/newsroom/lib/types';
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
        'inline-flex items-center gap-1.5 rounded-full border border-nw-gold/45 bg-nw-gold/10 text-nw-gold',
        compact ? 'px-2 py-[3px] text-[12px]' : 'px-2.5 py-1 text-[12px]',
      ].join(' ')}
      data-testid="paper-only-pill"
      title={tr("fa", "newsroom.ui.PageBar_2")}
    >
      <IconLock size={12} />
      <span className="font-nw-fa">{COPY.paperOnly}</span>
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
      className="flex flex-col"
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
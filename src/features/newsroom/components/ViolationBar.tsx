'use client';

import { TruthChip } from '@/src/features/newsroom/truth';
import { COPY } from '@/src/features/newsroom/lib/labels';
import type { ExecutionMode } from '@/src/features/newsroom/lib/types';
import { IconWarning } from './icons';

export interface ViolationBarProps {
  executionMode: ExecutionMode;
  realTrading: boolean;
  forced?: boolean;
}

/**
 * Full-width VIOLATION bar.
 *
 * Shown whenever the snapshot is not unambiguously paper-only:
 *   `executionMode !== 'PAPER_ONLY' || realTrading === true`
 * It is never dismissible and never offers a trading control.
 */
export function ViolationBar({ executionMode, realTrading, forced = false }: ViolationBarProps) {
  return (
    <div
      role="alert"
      data-testid="violation-bar"
      data-forced={forced ? 'true' : 'false'}
      className="flex shrink-0 flex-wrap items-center gap-x-3 gap-y-1.5 border-y border-nw-danger/45 bg-nw-danger/[0.09] px-4 py-2"
    >
      <span className="flex items-center gap-1.5 text-nw-danger">
        <IconWarning size={15} />
        <span className="font-nw-en text-[12px] font-semibold tracking-[0.16em]">
          {COPY.violationTitle}
        </span>
      </span>

      <span className="text-[12px] leading-relaxed text-nw-danger/85">{COPY.violationBody}</span>

      <span className="ms-auto flex items-center gap-1.5">
        <span className="nw-mono rounded-[6px] border border-nw-danger/40 px-1.5 py-[2px] text-[12px] text-nw-danger">
          executionMode={executionMode}
        </span>
        <span className="nw-mono rounded-[6px] border border-nw-danger/40 px-1.5 py-[2px] text-[12px] text-nw-danger">
          realTrading={String(realTrading)}
        </span>
        <TruthChip status="REJECTED" size="xs" />
      </span>
    </div>
  );
}

export default ViolationBar;
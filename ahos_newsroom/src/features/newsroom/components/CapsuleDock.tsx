'use client';

import { COPY } from '@/features/newsroom/lib/labels';
import { IconGlobe, IconPulse, MarkDiamond } from './icons';

/**
 * Right-hand capsule dock (RTL: it sits on the far right of the shell).
 * «جهان AHOS» is a reserved slot — a placeholder for the world capsule, with a
 * PLANNED chip so nobody mistakes it for something wired up.
 */
export function CapsuleDock() {
  return (
    <nav
      aria-label={COPY.worldCapsule}
      data-testid="capsule-dock"
      className="flex w-12 shrink-0 flex-col items-center gap-3 border-l border-ah-line-soft py-3"
    >
      <MarkDiamond size={16} className="text-ah-gold/80" />

      <div className="flex flex-1 flex-col items-center justify-center gap-2">
        <span
          className="font-ah-fa text-[11px] tracking-tight text-ah-text-faint"
          style={{ writingMode: 'vertical-rl' }}
          title={`${COPY.worldCapsule} · PLANNED`}
        >
          {COPY.worldCapsule}
        </span>
        <span className="h-px w-4 bg-ah-line" aria-hidden="true" />
        <span
          className="font-ah-en text-[8.5px] tracking-[0.18em] text-ah-text-faint"
          style={{ writingMode: 'vertical-rl' }}
        >
          PLANNED
        </span>
      </div>

      <span className="text-ah-cyan/70" title="دورسنجیِ زنده">
        <IconPulse size={14} />
      </span>
      <span className="text-ah-text-faint" title="منطقهٔ جهان (برنامه‌ریزی‌شده)">
        <IconGlobe size={14} />
      </span>
    </nav>
  );
}

export default CapsuleDock;

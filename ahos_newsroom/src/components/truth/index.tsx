'use client';

import type { ReactNode } from 'react';

import { MISSING, MISSING_FA } from '@/features/newsroom/lib/format';

export { TruthChip, default as default, resolveLabelEn, resolveLabelFa, resolveTone } from './TruthChip';
export type { ChipStatus, TruthChipProps } from './TruthChip';

/**
 * Renders a missing value as «—» (or «ناموجود» when `fa`), never as 0 and
 * never as a fabricated placeholder.
 */
export function MissingValue({ fa = false, title }: { fa?: boolean; title?: string }) {
  return (
    <span className="ah-mono text-ah-unknown" title={title ?? 'مقدار ناموجود · UNKNOWN'} data-missing="true">
      {fa ? MISSING_FA : MISSING}
    </span>
  );
}

/** Small uppercase section label. */
export function MicroLabel({ children, className = '' }: { children: ReactNode; className?: string }) {
  return <span className={`ah-label ${className}`}>{children}</span>;
}

/** Hairline divider used between dense rows. */
export function Divider({ className = '' }: { className?: string }) {
  return <div className={`h-px w-full bg-ah-line-soft ${className}`} aria-hidden="true" />;
}

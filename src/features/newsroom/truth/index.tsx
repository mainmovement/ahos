"use client";
import { tr } from "@/src/lib/i18n";

import type { ReactNode } from 'react';

import { MISSING, MISSING_FA } from '@/src/features/newsroom/lib/format';

export { TruthChip, default as default, resolveLabelEn, resolveLabelFa, resolveTone } from './TruthChip';
export type { ChipStatus, TruthChipProps } from './TruthChip';

/**
 * Renders a missing value as «—» (or «ناموجود» when `fa`), never as 0 and
 * never as a fabricated placeholder.
 */
export function MissingValue({ fa = false, title }: { fa?: boolean; title?: string }) {
  return (
    <span className="nw-mono text-nw-unknown" title={title ?? tr("fa", "newsroom.ui.index_1")} data-missing="true">
      {fa ? MISSING_FA : MISSING}
    </span>
  );
}

/** Small uppercase section label. */
export function MicroLabel({ children, className = '' }: { children: ReactNode; className?: string }) {
  return <span className={`nw-label ${className}`}>{children}</span>;
}

/** Hairline divider used between dense rows. */
export function Divider({ className = '' }: { className?: string }) {
  return <div className={`h-px w-full bg-nw-line-soft ${className}`} aria-hidden="true" />;
}
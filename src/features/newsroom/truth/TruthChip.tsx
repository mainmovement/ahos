'use client';

import type { ReactNode } from 'react';

import {
  COMPONENT_LABEL_EN,
  COMPONENT_LABEL_FA,
  COMPONENT_TONE,
  TONE,
  TRUTH_LABEL_EN,
  TRUTH_LABEL_FA,
  TRUTH_TONE,
  VERIFICATION_LABEL_EN,
  VERIFICATION_LABEL_FA,
  VERIFICATION_TONE,
  type Tone,
  type VerificationLevel,
} from '@/src/features/newsroom/lib/truth';
import type { ComponentState, TruthStatus } from '@/src/features/newsroom/lib/types';

export type ChipStatus = TruthStatus | ComponentState | VerificationLevel;

/**
 * Resolve a status to a tone. Data statuses win over component states so a
 * component can never "promote" UNKNOWN into something reassuring.
 */
export function resolveTone(status: ChipStatus): Tone {
  if (status in TRUTH_TONE) return TRUTH_TONE[status as TruthStatus];
  if (status in VERIFICATION_TONE) return VERIFICATION_TONE[status as VerificationLevel];
  if (status in COMPONENT_TONE) return COMPONENT_TONE[status as ComponentState];
  return 'neutral';
}

export function resolveLabelEn(status: ChipStatus): string {
  if (status in TRUTH_LABEL_EN) return TRUTH_LABEL_EN[status as TruthStatus];
  if (status in VERIFICATION_LABEL_EN) return VERIFICATION_LABEL_EN[status as VerificationLevel];
  if (status in COMPONENT_LABEL_EN) return COMPONENT_LABEL_EN[status as ComponentState];
  return String(status);
}

export function resolveLabelFa(status: ChipStatus): string | null {
  if (status in TRUTH_LABEL_FA) return TRUTH_LABEL_FA[status as TruthStatus];
  if (status in VERIFICATION_LABEL_FA) return VERIFICATION_LABEL_FA[status as VerificationLevel];
  if (status in COMPONENT_LABEL_FA) return COMPONENT_LABEL_FA[status as ComponentState];
  return null;
}

export interface TruthChipProps {
  status: ChipStatus;
  /** EN code (LIVE / UNKNOWN / …) — always rendered, never translated away. */
  label?: string;
  size?: 'xs' | 'sm' | 'md';
  shape?: 'pill' | 'box';
  /** Renders the Persian translation before the EN code. */
  showFa?: boolean;
  /** DEMO renders with a diagonal-stripe ribbon. */
  ribbon?: boolean;
  /** Hide the status dot (used inside dense tables). */
  hideDot?: boolean;
  title?: string;
  className?: string;
  children?: ReactNode;
  'data-testid'?: string;
}

const SIZE: Record<NonNullable<TruthChipProps['size']>, string> = {
  xs: 'text-[12px] px-1.5 py-[2px] gap-1',
  sm: 'text-[12px] px-2 py-[3px] gap-1.5',
  md: 'text-[12px] px-2.5 py-1 gap-1.5',
};

export function TruthChip({
  status,
  label,
  size = 'sm',
  shape = 'pill',
  showFa = false,
  ribbon = false,
  hideDot = false,
  title,
  className = '',
  children,
  'data-testid': testId,
}: TruthChipProps) {
  const tone = resolveTone(status);
  const style = TONE[tone];
  const labelEn = label ?? resolveLabelEn(status);
  const labelFa = resolveLabelFa(status);
  const isDemo = status === 'DEMO' || status === 'SIMULATED';

  const radius = shape === 'pill' ? 'rounded-full' : 'rounded-[6px]';

  return (
    <span
      data-testid={testId}
      data-status={status}
      data-tone={tone}
      title={title ?? `${labelEn} — ${labelFa ?? ''}`.trim()}
      className={[
        'inline-flex items-center border align-middle whitespace-nowrap font-nw-en tracking-[0.12em] uppercase',
        radius,
        SIZE[size],
        style.text,
        style.border,
        isDemo || ribbon ? 'nw-demo-stripes' : style.bg,
        className,
      ]
        .filter(Boolean)
        .join(' ')}
    >
      {!hideDot ? (
        <span
          aria-hidden="true"
          className={[
            'inline-block h-[5px] w-[5px] rounded-full',
            tone === 'unknown' || tone === 'planned' || tone === 'unavailable' || tone === 'missing'
              ? 'bg-nw-unknown'
              : tone === 'live'
                ? 'bg-nw-live'
                : tone === 'conflict' || tone === 'rejected' || tone === 'error'
                  ? 'bg-nw-danger'
                  : tone === 'partial' || tone === 'info'
                    ? 'bg-nw-cyan'
                    : tone === 'stale'
                      ? 'bg-nw-stale'
                      : 'bg-nw-gold',
          ].join(' ')}
        />
      ) : null}
      {showFa && labelFa ? <span className="font-nw-fa tracking-normal">{labelFa}</span> : null}
      <span>{labelEn}</span>
      {children}
    </span>
  );
}

export default TruthChip;
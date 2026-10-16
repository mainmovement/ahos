'use client';

import { MissingValue, TruthChip } from '@/components/truth';
import { COPY, PANEL } from '@/features/newsroom/lib/labels';
import { formatStampFa, formatTimeFa, toPersianDigits } from '@/features/newsroom/lib/format';
import type { NewsroomSnapshot } from '@/features/newsroom/lib/types';
import type { Tier } from '@/features/newsroom/lib/tier';
import { IconGlobe } from './icons';
import { PaperOnlyPill } from './PaperOnlyGuard';

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <span className="flex items-baseline gap-1.5 whitespace-nowrap">
      <span className="ah-label">{label}</span>
      <span className="text-[10.5px] text-ah-text-dim">{children}</span>
    </span>
  );
}

export interface TelemetryStripProps {
  snapshot: NewsroomSnapshot;
  tier: Tier;
}

/**
 * Bottom telemetry strip: source id · last read · story count (+ DEMO and
 * CONFLICT counters) · adapter id · tier · PAPER_ONLY · Reality Map link.
 */
export function TelemetryStrip({ snapshot, tier }: TelemetryStripProps) {
  const { telemetry } = snapshot;

  return (
    <footer
      className="flex shrink-0 flex-wrap items-center gap-x-4 gap-y-1.5 border-t border-ah-line px-4 py-1.5"
      data-testid="telemetry-strip"
    >
      <span className="flex items-center gap-1.5">
        <span className="ah-label">{PANEL.telemetry}</span>
        <span className="h-1 w-1 rounded-full bg-ah-live" aria-hidden="true" />
      </span>

      <Field label="آخرین منبع">
        {telemetry.lastSourceId ? (
          <span className="ah-mono text-ah-gold/80">{telemetry.lastSourceId}</span>
        ) : (
          <MissingValue fa />
        )}
      </Field>

      <Field label="آخرین خوانش">
        {telemetry.lastReadAt ? (
          <span className="ah-mono" title={formatStampFa(telemetry.lastReadAt)}>
            {formatTimeFa(telemetry.lastReadAt)}
          </span>
        ) : (
          <MissingValue fa />
        )}
      </Field>

      <Field label="تعداد خبر">
        <span className="ah-mono">{toPersianDigits(telemetry.storyCount)}</span>
      </Field>

      <Field label="دمو">
        <span className="ah-mono text-ah-gold/80">{toPersianDigits(telemetry.demoCount)}</span>
      </Field>

      <Field label="تعارض">
        <span className="ah-mono text-ah-danger/85">{toPersianDigits(telemetry.conflictCount)}</span>
      </Field>

      <Field label="منبع داده">
        <span className="ah-mono text-[10px] text-ah-text-faint">{telemetry.adapter}</span>
      </Field>

      <Field label="رده">
        <span className="ah-mono">T{tier}</span>
      </Field>

      <span className="ms-auto flex items-center gap-2">
        <button
          type="button"
          aria-disabled="true"
          data-testid="reality-map-link"
          title={`${COPY.realityMap} · برنامه‌ریزی‌شده`}
          className="inline-flex items-center gap-1.5 rounded-[6px] border border-dashed border-ah-line px-2 py-[3px] text-[10.5px] text-ah-text-faint"
        >
          <IconGlobe size={12} />
          <span className="font-ah-fa">{COPY.realityMap}</span>
          <TruthChip status="PLANNED" size="xs" hideDot />
        </button>
        <PaperOnlyPill compact />
      </span>
    </footer>
  );
}

export default TelemetryStrip;

"use client";
import { tr } from "@/src/lib/i18n";

import { trf } from '@/src/features/newsroom/lib/trf';
import { MissingValue, TruthChip } from '@/src/features/newsroom/truth';
import { COPY, PANEL } from '@/src/features/newsroom/lib/labels';
import { formatStampFa, formatTimeFa, toPersianDigits } from '@/src/features/newsroom/lib/format';
import type { NewsroomSnapshot } from '@/src/features/newsroom/lib/types';
import type { Tier } from '@/src/features/newsroom/lib/tier';
import { IconGlobe } from './icons';
import { PaperOnlyPill } from './PaperOnlyGuard';

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <span className="flex items-baseline gap-1.5 whitespace-nowrap">
      <span className="nw-label">{label}</span>
      <span className="text-[12px] text-nw-text-dim">{children}</span>
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
      className="flex shrink-0 flex-wrap items-center gap-x-4 gap-y-1.5 border-t border-nw-line px-4 py-1.5"
      data-testid="telemetry-strip"
    >
      <span className="flex items-center gap-1.5">
        <span className="nw-label">{PANEL.telemetry}</span>
        <span className="h-1 w-1 rounded-full bg-nw-live" aria-hidden="true" />
      </span>

      <Field label={tr("fa", "newsroom.ui.TelemetryStrip_1")}>
        {telemetry.lastSourceId ? (
          <span className="nw-mono text-nw-gold/80">{telemetry.lastSourceId}</span>
        ) : (
          <MissingValue fa />
        )}
      </Field>

      <Field label={tr("fa", "newsroom.ui.TelemetryStrip_2")}>
        {telemetry.lastReadAt ? (
          <span className="nw-mono" title={formatStampFa(telemetry.lastReadAt)}>
            {formatTimeFa(telemetry.lastReadAt)}
          </span>
        ) : (
          <MissingValue fa />
        )}
      </Field>

      <Field label={tr("fa", "newsroom.ui.TelemetryStrip_3")}>
        <span className="nw-mono">{toPersianDigits(telemetry.storyCount)}</span>
      </Field>

      <Field label={tr("fa", "newsroom.ui.TelemetryStrip_4")}>
        <span className="nw-mono text-nw-gold/80">{toPersianDigits(telemetry.demoCount)}</span>
      </Field>

      <Field label={tr("fa", "newsroom.ui.TelemetryStrip_5")}>
        <span className="nw-mono text-nw-danger/85">{toPersianDigits(telemetry.conflictCount)}</span>
      </Field>

      <Field label={tr("fa", "newsroom.ui.TelemetryStrip_6")}>
        <span className="nw-mono text-[12px] text-nw-text-faint">{telemetry.adapter}</span>
      </Field>

      <Field label={tr("fa", "newsroom.ui.TelemetryStrip_7")}>
        <span className="nw-mono">T{tier}</span>
      </Field>

      <span className="ms-auto flex items-center gap-2">
        <button
          type="button"
          aria-disabled="true"
          data-testid="reality-map-link"
          title={trf("newsroom.fmt.realityPlanned", { x: COPY.realityMap })}
          className="inline-flex items-center gap-1.5 rounded-[6px] border border-dashed border-nw-line px-2 py-[3px] text-[12px] text-nw-text-faint"
        >
          <IconGlobe size={12} />
          <span className="font-nw-fa">{COPY.realityMap}</span>
          <TruthChip status="PLANNED" size="xs" hideDot />
        </button>
        <PaperOnlyPill compact />
      </span>
    </footer>
  );
}

export default TelemetryStrip;
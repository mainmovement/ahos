"use client";
import { tr } from "@/src/lib/i18n";

import { trf } from '@/src/features/newsroom/lib/trf';
import { TruthChip } from '@/src/features/newsroom/truth';
import { PANEL } from '@/src/features/newsroom/lib/labels';
import { formatTimeFa } from '@/src/features/newsroom/lib/format';
import { currentStageIndex } from '@/src/features/newsroom/lib/pipeline';
import type { PipelineStage } from '@/src/features/newsroom/lib/types';
import { Panel } from './primitives';

const STATE_CHIP: Record<PipelineStage['state'], 'LIVE' | 'PLANNED' | 'UNKNOWN' | 'PARTIAL'> = {
  DONE: 'LIVE',
  CURRENT: 'PARTIAL',
  PLANNED: 'PLANNED',
  UNKNOWN: 'UNKNOWN',
};

const STATE_LABEL: Record<PipelineStage['state'], string> = {
  DONE: tr("fa", "newsroom.ui.VerificationPipeline_1"),
  CURRENT: tr("fa", "newsroom.ui.VerificationPipeline_2"),
  PLANNED: tr("fa", "newsroom.ui.VerificationPipeline_3"),
  UNKNOWN: tr("fa", "newsroom.ui.VerificationPipeline_4"),
};

function StageGlyph({ state }: { state: PipelineStage['state'] }) {
  if (state === 'DONE') {
    return (
      <svg width="12" height="12" viewBox="0 0 24 24" aria-hidden="true" className="text-nw-live">
        <path d="m5 12.5 4.5 4.5L19 7" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    );
  }
  if (state === 'CURRENT') {
    return (
      <span className="relative inline-flex h-2 w-2">
        <span className="nw-pulse-soft absolute inline-flex h-2 w-2 rounded-full bg-nw-gold" />
        <span className="relative inline-flex h-2 w-2 rounded-full bg-nw-gold" />
      </span>
    );
  }
  if (state === 'UNKNOWN') {
    return <span className="inline-block h-[7px] w-[7px] rounded-full border border-dashed border-nw-unknown" />;
  }
  return <span className="inline-block h-[7px] w-[7px] rounded-full border border-nw-line-strong" />;
}

export interface VerificationPipelineProps {
  stages: readonly PipelineStage[];
  demo: boolean;
  className?: string;
}

/**
 * INGEST → TRIAGE → TWO_SOURCE_CHECK → CONFLICT_SCAN → JUDGE_HANDOFF
 *
 * A stage that has not run is PLANNED or UNKNOWN — never a fake COMPLETE.
 */
export function VerificationPipeline({ stages, demo, className = '' }: VerificationPipelineProps) {
  const current = currentStageIndex(stages);

  return (
    <Panel
      title={PANEL.pipeline}
      titleEn="VERIFICATION PIPELINE"
      demo={demo}
      data-testid="verification-pipeline"
      className={className}
      chips={
        <span className="nw-label">
          {current >= 0 ? trf("newsroom.fmt.currentStage", { s: stages[current]?.labelEn ?? "—" }) : tr("fa", "newsroom.ui.VerificationPipeline_5")}
        </span>
      }
    >
      <ol className="flex items-stretch gap-1 p-2.5" data-testid="pipeline-stages">
        {stages.map((stage, index) => {
          const isCurrent = stage.state === 'CURRENT';
          return (
            <li key={stage.id} className="flex min-w-0 flex-1 items-stretch gap-1">
              <div
                data-testid={`pipeline-stage-${stage.id}`}
                data-stage-state={stage.state}
                className={[
                  'flex min-w-0 flex-1 flex-col gap-1 rounded-[6px] border px-1.5 py-1.5',
                  isCurrent
                    ? 'border-nw-gold/60 bg-nw-gold/[0.09]'
                    : stage.state === 'DONE'
                      ? 'border-nw-cyan/25 bg-nw-cyan/[0.05]'
                      : stage.state === 'UNKNOWN'
                        ? 'border-dashed border-nw-unknown/35 bg-transparent'
                        : 'border-dashed border-nw-line bg-transparent',
                ].join(' ')}
              >
                <div className="flex items-center justify-between gap-1">
                  <span className="flex items-center gap-1">
                    <StageGlyph state={stage.state} />
                  </span>
                  <TruthChip status={STATE_CHIP[stage.state]} size="xs" hideDot label={stage.state} />
                </div>
                <p className="truncate text-[12px] leading-tight text-nw-text" title={stage.labelFa}>
                  {stage.labelFa}
                </p>
                <p
                  className="break-words font-nw-en text-[12px] leading-[1.15] tracking-normal text-nw-text-faint"
                  title={stage.labelEn}
                >
                  {stage.labelEn}
                </p>
                <p
                  className="mt-auto line-clamp-2 text-[12px] leading-tight text-nw-text-faint"
                  title={stage.detailFa ?? ''}
                >
                  {stage.detailFa ?? '—'}
                </p>
                <p className="nw-mono text-[12px] leading-tight text-nw-text-faint">
                  {stage.completedAt ? formatTimeFa(stage.completedAt) : '—'}
                </p>
              </div>
              {index < stages.length - 1 ? (
                <span
                  aria-hidden="true"
                  className={[
                    'mt-[18px] w-[6px] shrink-0 self-start border-t',
                    stage.state === 'DONE' ? 'border-nw-cyan/40' : 'border-dashed border-nw-line',
                  ].join(' ')}
                />
              ) : null}
            </li>
          );
        })}
      </ol>
      <p className="border-t border-nw-line-soft px-3 py-1.5 text-[12px] leading-relaxed text-nw-text-faint">
        {tr("fa", "newsroom.ui.VerificationPipeline_6")}
      </p>
    </Panel>
  );
}

export default VerificationPipeline;

export { STATE_LABEL };
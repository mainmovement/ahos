'use client';

import { TruthChip } from '@/components/truth';
import { PANEL } from '@/features/newsroom/lib/labels';
import { formatTimeFa } from '@/features/newsroom/lib/format';
import { currentStageIndex } from '@/features/newsroom/lib/pipeline';
import type { PipelineStage } from '@/features/newsroom/lib/types';
import { Panel } from './primitives';

const STATE_CHIP: Record<PipelineStage['state'], 'LIVE' | 'PLANNED' | 'UNKNOWN' | 'PARTIAL'> = {
  DONE: 'LIVE',
  CURRENT: 'PARTIAL',
  PLANNED: 'PLANNED',
  UNKNOWN: 'UNKNOWN',
};

const STATE_LABEL: Record<PipelineStage['state'], string> = {
  DONE: 'اجرا شده',
  CURRENT: 'در جریان',
  PLANNED: 'اجرا نشده',
  UNKNOWN: 'نامعلوم',
};

function StageGlyph({ state }: { state: PipelineStage['state'] }) {
  if (state === 'DONE') {
    return (
      <svg width="12" height="12" viewBox="0 0 24 24" aria-hidden="true" className="text-ah-live">
        <path d="m5 12.5 4.5 4.5L19 7" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    );
  }
  if (state === 'CURRENT') {
    return (
      <span className="relative inline-flex h-2 w-2">
        <span className="ah-pulse-soft absolute inline-flex h-2 w-2 rounded-full bg-ah-gold" />
        <span className="relative inline-flex h-2 w-2 rounded-full bg-ah-gold" />
      </span>
    );
  }
  if (state === 'UNKNOWN') {
    return <span className="inline-block h-[7px] w-[7px] rounded-full border border-dashed border-ah-unknown" />;
  }
  return <span className="inline-block h-[7px] w-[7px] rounded-full border border-ah-line-strong" />;
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
        <span className="ah-label">
          {current >= 0 ? `مرحلهٔ جاری: ${stages[current]?.labelEn ?? '—'}` : 'مرحلهٔ جاری ندارد'}
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
                    ? 'border-ah-gold/60 bg-ah-gold/[0.09]'
                    : stage.state === 'DONE'
                      ? 'border-ah-cyan/25 bg-ah-cyan/[0.05]'
                      : stage.state === 'UNKNOWN'
                        ? 'border-dashed border-ah-unknown/35 bg-transparent'
                        : 'border-dashed border-ah-line bg-transparent',
                ].join(' ')}
              >
                <div className="flex items-center justify-between gap-1">
                  <span className="flex items-center gap-1">
                    <StageGlyph state={stage.state} />
                  </span>
                  <TruthChip status={STATE_CHIP[stage.state]} size="xs" hideDot label={stage.state} />
                </div>
                <p className="truncate text-[10.5px] leading-tight text-ah-text" title={stage.labelFa}>
                  {stage.labelFa}
                </p>
                <p
                  className="break-words font-ah-en text-[8px] leading-[1.15] tracking-normal text-ah-text-faint"
                  title={stage.labelEn}
                >
                  {stage.labelEn}
                </p>
                <p
                  className="mt-auto line-clamp-2 text-[9.5px] leading-tight text-ah-text-faint"
                  title={stage.detailFa ?? ''}
                >
                  {stage.detailFa ?? '—'}
                </p>
                <p className="ah-mono text-[9.5px] leading-tight text-ah-text-faint">
                  {stage.completedAt ? formatTimeFa(stage.completedAt) : '—'}
                </p>
              </div>
              {index < stages.length - 1 ? (
                <span
                  aria-hidden="true"
                  className={[
                    'mt-[18px] w-[6px] shrink-0 self-start border-t',
                    stage.state === 'DONE' ? 'border-ah-cyan/40' : 'border-dashed border-ah-line',
                  ].join(' ')}
                />
              ) : null}
            </li>
          );
        })}
      </ol>
      <p className="border-t border-ah-line-soft px-3 py-1.5 text-[10.5px] leading-relaxed text-ah-text-faint">
        مراحلِ اجرانشده PLANNED/UNKNOWN می‌مانند و هیچ‌وقت «تکمیل» نشان داده نمی‌شوند.
      </p>
    </Panel>
  );
}

export default VerificationPipeline;

export { STATE_LABEL };

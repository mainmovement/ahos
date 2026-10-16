/**
 * Verification pipeline derivation.
 *
 * INGEST → TRIAGE → TWO_SOURCE_CHECK → CONFLICT_SCAN → JUDGE_HANDOFF
 *
 * Hard rule: a stage that has not run is `PLANNED` (or `UNKNOWN`), never
 * `DONE`. The pipeline is derived from evidence already present on the story,
 * so the UI can never claim a check that did not happen.
 */

import { independentSourceCount } from './truth';
import { parseIso } from './format';
import type { NewsSource, PipelineStage, PipelineStageId, Story } from './types';

export const PIPELINE_ORDER: readonly PipelineStageId[] = [
  'INGEST',
  'TRIAGE',
  'TWO_SOURCE_CHECK',
  'CONFLICT_SCAN',
  'JUDGE_HANDOFF',
] as const;

function minutesAfter(iso: string | null, minutes: number): string | null {
  const date = parseIso(iso);
  if (!date) return null;
  return new Date(date.getTime() + minutes * 60_000).toISOString();
}

export interface PipelineInput {
  story: Story;
  sources: readonly NewsSource[];
  hasConflict: boolean;
}

export function derivePipeline({ story, sources, hasConflict }: PipelineInput): PipelineStage[] {
  const base = story.publishedAt;

  // DEMO rows never run real checks: they stay UNKNOWN rather than faking DONE.
  const isDemo = story.demo || story.status === 'DEMO' || sources.some((s) => s.status === 'DEMO');

  const ingested = base !== null;
  const independent = independentSourceCount(sources);
  const sourceCheckDone = !isDemo && independent >= 2;
  const sourceCheckCurrent = !isDemo && independent === 1;
  const scanDone = !isDemo && sourceCheckDone && !hasConflict;

  const stages: PipelineStage[] = [
    {
      id: 'INGEST',
      labelFa: 'دریافت',
      labelEn: 'INGEST',
      state: ingested ? 'DONE' : 'UNKNOWN',
      completedAt: ingested ? base : null,
      detailFa: ingested
        ? `${sources.length} منبع پیوست شد`
        : 'زمان انتشار نامعلوم ⇒ دریافت تأیید نشده',
    },
    {
      id: 'TRIAGE',
      labelFa: 'غربال',
      labelEn: 'TRIAGE',
      state: ingested ? 'DONE' : 'UNKNOWN',
      completedAt: ingested ? minutesAfter(base, 1) : null,
      detailFa: ingested ? 'بازار و نوع ادعا تعیین شد' : 'اجرا نشده',
    },
    {
      id: 'TWO_SOURCE_CHECK',
      labelFa: 'بررسی دومنبعی',
      labelEn: 'TWO_SOURCE_CHECK',
      state: isDemo ? 'UNKNOWN' : sourceCheckDone ? 'DONE' : sourceCheckCurrent ? 'CURRENT' : 'PLANNED',
      completedAt: sourceCheckDone ? minutesAfter(base, 2) : null,
      detailFa: isDemo
        ? 'دادهٔ دمو ⇒ مرحله اجرا نمی‌شود'
        : sourceCheckDone
          ? `${independent} منبعِ مستقل و زنده`
          : sourceCheckCurrent
            ? 'تنها یک منبع ⇒ در انتظار منبع دوم (PARTIAL)'
            : 'اجرا نشده',
    },
    {
      id: 'CONFLICT_SCAN',
      labelFa: 'پویش تعارض',
      labelEn: 'CONFLICT_SCAN',
      state: isDemo ? 'UNKNOWN' : hasConflict ? 'CURRENT' : scanDone ? 'DONE' : 'PLANNED',
      completedAt: scanDone ? minutesAfter(base, 3) : null,
      detailFa: isDemo
        ? 'دادهٔ دمو ⇒ مرحله اجرا نمی‌شود'
        : hasConflict
          ? 'تعارضِ باز؛ حلِ خودکار ممنوع'
          : scanDone
            ? 'هیچ تعارضی یافت نشد'
            : 'اجرا نشده',
    },
    {
      id: 'JUDGE_HANDOFF',
      labelFa: 'تحویل به قاضی',
      labelEn: 'JUDGE_HANDOFF',
      // Always manual and read-only: never auto-completed.
      state: 'PLANNED',
      completedAt: null,
      detailFa: 'در انتظار اپراتور · فقط‌خواندنی',
    },
  ];

  return stages;
}

/** Index of the stage that should be highlighted, or -1 when none is current. */
export function currentStageIndex(stages: readonly PipelineStage[]): number {
  return stages.findIndex((s) => s.state === 'CURRENT');
}
"use client";
import { tr } from "@/src/lib/i18n";

import { useMemo, useState } from 'react';

import { TruthChip } from '@/src/features/newsroom/truth';
import { ACTION, PANEL } from '@/src/features/newsroom/lib/labels';
import { formatStampFa } from '@/src/features/newsroom/lib/format';
import { evidenceId, type StoryView } from '@/src/features/newsroom/lib/selectors';
import type { NewsroomSnapshot } from '@/src/features/newsroom/lib/types';
import { Panel } from './primitives';
import { IconCheck, IconCopy, IconDownload, IconEye, IconLayers } from './icons';

type Eligibility = 'READY' | 'BLOCKED_BY_CONFLICT' | 'INCOMPLETE' | 'NOT_ELIGIBLE';

const ELIGIBILITY_STATE: Record<Eligibility, 'LIVE' | 'CONFLICT' | 'PARTIAL' | 'DEMO'> = {
  READY: 'LIVE',
  BLOCKED_BY_CONFLICT: 'CONFLICT',
  INCOMPLETE: 'PARTIAL',
  NOT_ELIGIBLE: 'DEMO',
};

const ELIGIBILITY_NOTE_FA: Record<Eligibility, string> = {
  READY: tr("fa", "newsroom.ui.JudgeHandoffTile_1"),
  BLOCKED_BY_CONFLICT: tr("fa", "newsroom.ui.JudgeHandoffTile_2"),
  INCOMPLETE: tr("fa", "newsroom.ui.JudgeHandoffTile_3"),
  NOT_ELIGIBLE: tr("fa", "newsroom.ui.JudgeHandoffTile_4"),
};

function eligibilityFor(view: StoryView | null): Eligibility {
  if (!view) return 'INCOMPLETE';
  switch (view.verification) {
    case 'DEMO':
      return 'NOT_ELIGIBLE';
    case 'CONFLICT':
      return 'BLOCKED_BY_CONFLICT';
    case 'VERIFIED':
      return 'READY';
    default:
      return 'INCOMPLETE';
  }
}

export interface JudgeHandoffTileProps {
  view: StoryView | null;
  snapshot: NewsroomSnapshot;
  onCopyId: (id: string) => void;
  copiedId: string | null;
  demo: boolean;
  className?: string;
}

/**
 * Handoff to the White Hats / Judge queue.
 *
 * Verbs: view · copy ID · export read-only. There is deliberately no approve,
 * override, size or "trade this" control anywhere in this component.
 */
export function JudgeHandoffTile({
  view,
  snapshot,
  onCopyId,
  copiedId,
  demo,
  className = '',
}: JudgeHandoffTileProps) {
  const [showEvidence, setShowEvidence] = useState(false);
  const eligibility = eligibilityFor(view);

  const payload = useMemo(() => {
    if (!view) return null;
    return {
      evidenceId: evidenceId(view.story),
      storyId: view.story.id,
      market: view.story.market,
      headlineFa: view.story.headlineFa,
      headlineEn: view.story.headlineEn,
      publishedAt: view.story.publishedAt,
      verification: view.verification,
      independentSources: view.independentSources,
      totalSources: view.totalSources,
      sources: view.sources.map((s) => ({
        id: s.id,
        nameFa: s.nameFa,
        urlPlaceholder: s.urlPlaceholder,
        credibility: s.credibility,
        status: s.status,
        lastReadAt: s.lastReadAt,
        independenceGroup: s.independenceGroup,
      })),
      conflictId: view.conflict?.id ?? null,
      executionMode: snapshot.executionMode,
      realTrading: snapshot.realTrading,
      dataSource: snapshot.telemetry.adapter,
      readOnly: true,
      generatedAt: snapshot.generatedAt,
    };
  }, [view, snapshot]);

  const exportReadOnly = () => {
    if (!payload) return;
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = `${payload.evidenceId.replace(/:/g, '-')}.json`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
  };

  const id = view ? evidenceId(view.story) : null;
  const copied = id !== null && copiedId === id;

  return (
    <Panel
      title={PANEL.handoff}
      titleEn="WHITE HATS HANDOFF"
      demo={demo || (view?.story.demo ?? false)}
      data-testid="judge-handoff-tile"
      className={className}
      chips={
        <>
          {snapshot.telemetry.adapter.startsWith('mock:') ? (
            <TruthChip status="SIMULATED" size="xs" showFa />
          ) : null}
          <TruthChip status={ELIGIBILITY_STATE[eligibility]} size="xs" label={eligibility} />
        </>
      }
    >
      <div className="p-2.5">
        <div className="mb-2 flex items-center justify-between gap-2">
          <span className="flex min-w-0 items-center gap-1.5">
            <IconLayers size={13} className="shrink-0 text-nw-gold/80" />
            <span className="nw-label shrink-0">{tr("fa", "newsroom.ui.JudgeHandoffTile_5")}</span>
          </span>
          <span className="nw-mono truncate text-[12px] text-nw-gold/85" title={id ?? '—'}>
            {id ?? '—'}
          </span>
        </div>

        <p className="mb-2 text-[12px] leading-relaxed text-nw-text-faint">
          {ELIGIBILITY_NOTE_FA[eligibility]}
        </p>

        <div className="flex flex-wrap items-center gap-1.5">
          <button
            type="button"
            onClick={() => setShowEvidence((v) => !v)}
            disabled={!payload}
            data-testid="handoff-view"
            title={ACTION.openEvidence}
            className="inline-flex items-center gap-1 rounded-[6px] border border-nw-line px-2 py-[4px] text-[12px] text-nw-text-dim transition-colors hover:border-nw-gold/40 hover:text-nw-text disabled:cursor-not-allowed disabled:opacity-45"
          >
            <IconEye size={12} />
            <span>{ACTION.openEvidence}</span>
          </button>
          <button
            type="button"
            onClick={() => id && onCopyId(id)}
            disabled={!id}
            data-testid="handoff-copy-id"
            title={ACTION.copyId}
            className="inline-flex items-center gap-1 rounded-[6px] border border-nw-line px-2 py-[4px] text-[12px] text-nw-text-dim transition-colors hover:border-nw-gold/40 hover:text-nw-text disabled:cursor-not-allowed disabled:opacity-45"
          >
            {copied ? <IconCheck size={12} /> : <IconCopy size={12} />}
            <span>{copied ? ACTION.copied : ACTION.copyId}</span>
          </button>
          <button
            type="button"
            onClick={exportReadOnly}
            disabled={!payload}
            data-testid="handoff-export"
            title={ACTION.exportReadOnly}
            className="inline-flex items-center gap-1 rounded-[6px] border border-nw-line px-2 py-[4px] text-[12px] text-nw-text-dim transition-colors hover:border-nw-gold/40 hover:text-nw-text disabled:cursor-not-allowed disabled:opacity-45"
          >
            <IconDownload size={12} />
            <span>{ACTION.exportReadOnly}</span>
          </button>
        </div>

        {showEvidence && payload ? (
          <pre
            dir="ltr"
            data-testid="handoff-evidence-json"
            className="nw-scroll mt-2 max-h-40 overflow-auto rounded-[6px] border border-nw-line-soft bg-nw-bg/70 p-2 text-left font-nw-en text-[12px] leading-relaxed text-nw-text-dim"
          >
            {JSON.stringify(payload, null, 2)}
          </pre>
        ) : null}

        <p className="mt-2 border-t border-nw-line-soft pt-1.5 text-[12px] leading-relaxed text-nw-text-faint">
          {tr("fa", "newsroom.ui.dataUpdated")} {formatStampFa(snapshot.generatedAt)} · {tr("fa", "newsroom.ui.readOnlyNoPrefix")}
          {tr("fa", "newsroom.ui.JudgeHandoffTile_6")}
        </p>
      </div>
    </Panel>
  );
}

export default JudgeHandoffTile;

export { eligibilityFor, type Eligibility };
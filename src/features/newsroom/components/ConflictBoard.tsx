"use client";
import { tr } from "@/src/lib/i18n";

import { trf } from '@/src/features/newsroom/lib/trf';
import { TruthChip, MissingValue } from '@/src/features/newsroom/truth';
import { ACTION, PANEL } from '@/src/features/newsroom/lib/labels';
import { formatStampFa } from '@/src/features/newsroom/lib/format';
import { sourceById, type StoryView } from '@/src/features/newsroom/lib/selectors';
import type { ClaimSide, Conflict, NewsroomSnapshot } from '@/src/features/newsroom/lib/types';
import { Panel, StateBlock } from './primitives';
import { IconCheck, IconCopy, IconEye, IconWarning } from './icons';

function ClaimSideRow({
  side,
  snapshot,
  sideKey,
}: {
  side: ClaimSide;
  snapshot: NewsroomSnapshot;
  sideKey: 'A' | 'B';
}) {
  const source = sourceById(snapshot, side.sourceId);
  return (
    <div
      className="rounded-[6px] border border-nw-line-soft bg-nw-surface-2/50 px-2 py-1.5"
      data-testid={`claim-${sideKey}`}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="truncate text-[12px] text-nw-text" title={source?.nameFa ?? side.sourceId}>
          {source?.nameFa ?? side.sourceId}
        </span>
        <span className="font-nw-en text-[12px] tracking-[0.12em] text-nw-text-faint">
          CLAIM {sideKey}
        </span>
      </div>
      <p className="mt-0.5 text-[12px] leading-snug text-nw-text-dim">{side.claimFa}</p>
      <div className="mt-1 flex items-center justify-between gap-2">
        <span className="nw-mono text-[12px] text-nw-cyan/85" title={tr("fa", "newsroom.ui.ConflictBoard_1")}>
          {side.value ?? <MissingValue fa />}
        </span>
        <span className="nw-mono text-[12px] text-nw-text-faint">
          {side.reportedAt ? formatStampFa(side.reportedAt) : <MissingValue />}
        </span>
      </div>
    </div>
  );
}

export interface ConflictBoardProps {
  snapshot: NewsroomSnapshot;
  views: readonly StoryView[];
  onSelectStory: (id: string) => void;
  onCopyId: (id: string) => void;
  copiedId: string | null;
  demo: boolean;
  className?: string;
}

export function ConflictBoard({
  snapshot,
  views,
  onSelectStory,
  onCopyId,
  copiedId,
  demo,
  className = '',
}: ConflictBoardProps) {
  const conflicts = snapshot.conflicts;
  const viewByStory = new Map(views.map((v) => [v.story.id, v]));

  return (
    <Panel
      title={PANEL.conflicts}
      titleEn="CONFLICT BOARD"
      demo={demo}
      data-testid="conflict-board"
      className={className}
      chips={
        conflicts.length > 0 ? (
          <TruthChip status="CONFLICT" size="xs" label={`${conflicts.length} OPEN`} />
        ) : (
          <TruthChip status="UNKNOWN" size="xs" label="0 OPEN" />
        )
      }
      bodyClassName="nw-scroll min-h-0 overflow-auto"
    >
      {conflicts.length === 0 ? (
        <StateBlock
          title={tr("fa", "newsroom.ui.ConflictBoard_2")}
          body={tr("fa", "newsroom.ui.ConflictBoard_3")}
          glyph={<IconWarning size={20} />}
        />
      ) : (
        <ul className="p-2">
          {(conflicts as readonly Conflict[]).map((conflict) => {
            const view = viewByStory.get(conflict.storyId);
            const copied = copiedId === conflict.id;
            return (
              <li
                key={conflict.id}
                className="mb-2 rounded-[6px] border border-nw-danger/30 bg-nw-danger/[0.04] p-2 last:mb-0"
                data-testid={`conflict-card-${conflict.id}`}
                data-status="CONFLICT"
              >
                <div className="mb-1.5 flex items-center justify-between gap-2">
                  <span className="flex min-w-0 items-center gap-1.5">
                    <IconWarning size={12} className="shrink-0 text-nw-danger" />
                    <span className="truncate text-[12px] text-nw-text" title={conflict.topicFa}>
                      {conflict.topicFa}
                    </span>
                  </span>
                  <TruthChip status="CONFLICT" size="xs" />
                </div>

                <div className="mb-1.5 flex items-center justify-between gap-2">
                  <span className="nw-mono truncate text-[12px] text-nw-text-faint">
                    {conflict.id} · {conflict.storyId}
                  </span>
                  <span className="flex shrink-0 items-center gap-1">
                    <button
                      type="button"
                      onClick={() => onSelectStory(conflict.storyId)}
                      data-testid={`conflict-view-${conflict.id}`}
                      title={ACTION.view}
                      className="inline-flex items-center gap-1 rounded-[5px] border border-nw-line px-1.5 py-[2px] text-[12px] text-nw-text-dim transition-colors hover:border-nw-gold/40 hover:text-nw-text"
                    >
                      <IconEye size={11} />
                      <span>{ACTION.view}</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => onCopyId(conflict.id)}
                      data-testid={`conflict-copy-${conflict.id}`}
                      title={ACTION.copyId}
                      className="inline-flex items-center gap-1 rounded-[5px] border border-nw-line px-1.5 py-[2px] text-[12px] text-nw-text-dim transition-colors hover:border-nw-gold/40 hover:text-nw-text"
                    >
                      {copied ? <IconCheck size={11} /> : <IconCopy size={11} />}
                      <span>{copied ? ACTION.copied : tr("fa", "newsroom.ui.ConflictBoard_4")}</span>
                    </button>
                  </span>
                </div>

                <div className="flex flex-col gap-1">
                  <ClaimSideRow side={conflict.claimA} snapshot={snapshot} sideKey="A" />
                  <div className="flex items-center gap-1.5 px-1">
                    <span className="h-px flex-1 bg-nw-danger/25" aria-hidden="true" />
                    <span className="font-nw-en text-[12px] tracking-[0.14em] text-nw-danger/70">VS</span>
                    <span className="h-px flex-1 bg-nw-danger/25" aria-hidden="true" />
                  </div>
                  <ClaimSideRow side={conflict.claimB} snapshot={snapshot} sideKey="B" />
                </div>

                <p className="mt-1.5 text-[12px] leading-relaxed text-nw-text-faint">
                  {conflict.noteFa ?? '—'}
                  {conflict.detectedAt ? (
                    <span className="nw-mono ms-1"> · {formatStampFa(conflict.detectedAt)}</span>
                  ) : null}
                </p>

                {view ? (
                  <p className="mt-1 font-nw-en text-[12px] tracking-[0.1em] text-nw-text-faint">
                    {trf("newsroom.fmt.verificationLevel", { level: view.verification })}
                  </p>
                ) : null}
              </li>
            );
          })}
        </ul>
      )}
    </Panel>
  );
}

export default ConflictBoard;
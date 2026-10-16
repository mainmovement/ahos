"use client";
import { tr } from "@/src/lib/i18n";

import { trf } from '@/src/features/newsroom/lib/trf';
import { TruthChip, MissingValue } from '@/src/features/newsroom/truth';
import {
  ACTION,
  CLAIM_STRENGTH_LABEL_EN,
  CLAIM_STRENGTH_LABEL_FA,
  MARKET_LABEL_EN,
  MARKET_LABEL_FA,
  PANEL,
} from '@/src/features/newsroom/lib/labels';
import {
  FRESHNESS_LABEL_EN,
  formatRelativeFa,
  formatStampFa,
  freshnessBucket,
} from '@/src/features/newsroom/lib/format';
import type { StoryView } from '@/src/features/newsroom/lib/selectors';
import { DataRow, Panel, StateBlock } from './primitives';
import { IconCheck, IconClose, IconCopy, IconEye, IconWarning } from './icons';

export interface StoryDossierProps {
  view: StoryView | null;
  onClose: () => void;
  onCopyId: (id: string) => void;
  copiedId: string | null;
  demo: boolean;
  /** Reference 'now' (snapshot.generatedAt) — freshness is never wall-clock based. */
  nowIso: string | null;
  className?: string;
}

/** Read-only dossier for the selected story. No action here changes the world. */
export function StoryDossier({
  view,
  onClose,
  onCopyId,
  copiedId,
  demo,
  nowIso,
  className = '',
}: StoryDossierProps) {
  if (!view) {
    return (
      <Panel
        title={PANEL.dossier}
        accent="gold"
        demo={demo}
        className={className}
        data-testid="story-dossier"
      >
        <StateBlock
          title={tr("fa", "newsroom.ui.StoryDossier_1")}
          body={tr("fa", "newsroom.ui.StoryDossier_2")}
          glyph={<IconEye size={22} />}
        />
      </Panel>
    );
  }

  const { story, verification, independentSources, totalSources, conflict } = view;
  const bucket = freshnessBucket(story.publishedAt, nowIso);
  const copied = copiedId === story.id;

  return (
    <Panel
      title={PANEL.dossier}
      accent="gold"
      demo={demo || story.demo}
      className={className}
      data-testid="story-dossier"
      chips={
        <>
          <span className="nw-mono text-[12px] text-nw-gold/80">{story.id}</span>
          <TruthChip status={verification} size="xs" />
        </>
      }
      actions={
        <>
          <button
            type="button"
            onClick={() => onCopyId(story.id)}
            data-testid="dossier-copy-id"
            title={ACTION.copyId}
            className="inline-flex items-center gap-1 rounded-[6px] border border-nw-line px-2 py-[4px] text-[12px] text-nw-text-dim transition-colors hover:border-nw-gold/40 hover:text-nw-text"
          >
            {copied ? <IconCheck size={12} /> : <IconCopy size={12} />}
            <span>{copied ? ACTION.copied : ACTION.copyId}</span>
          </button>
          <button
            type="button"
            onClick={onClose}
            data-testid="dossier-close"
            aria-label={ACTION.close}
            title={ACTION.close}
            className="inline-flex h-[22px] w-[22px] items-center justify-center rounded-[6px] border border-nw-line text-nw-text-dim transition-colors hover:border-nw-line-strong hover:text-nw-text"
          >
            <IconClose size={12} />
          </button>
        </>
      }
      bodyClassName="nw-scroll min-h-0 overflow-auto"
    >
      <div className="nw-drawer-in p-3" key={story.id}>
        <h3 className="text-[15px] font-semibold leading-snug text-nw-text">{story.headlineFa}</h3>
        {story.headlineEn ? (
          <p className="mt-1 font-nw-en text-[12px] leading-snug text-nw-text-faint">{story.headlineEn}</p>
        ) : (
          <p className="mt-1 flex items-center gap-1.5">
            <TruthChip status="MISSING" size="xs" hideDot />
            <span className="text-[12px] text-nw-text-faint">{tr("fa", "newsroom.ui.StoryDossier_3")}</span>
          </p>
        )}

        <div className="mt-2.5 grid grid-cols-2 gap-x-4">
          <DataRow label={tr("fa", "newsroom.ui.StoryDossier_4")}>
            <span className="font-nw-fa">{MARKET_LABEL_FA[story.market]}</span>
            <span className="ms-1 font-nw-en text-[12px] text-nw-text-faint">
              {MARKET_LABEL_EN[story.market]}
            </span>
          </DataRow>
          <DataRow label={tr("fa", "newsroom.ui.StoryDossier_5")}>
            <TruthChip status={verification} size="xs" />
          </DataRow>
          <DataRow label={tr("fa", "newsroom.ui.StoryDossier_6")}>
            {story.publishedAt ? (
              <span
                className="nw-mono"
                title={`${formatStampFa(story.publishedAt)} · ${formatRelativeFa(story.publishedAt, nowIso)}`}
              >
                {formatStampFa(story.publishedAt)}
              </span>
            ) : (
              <MissingValue fa />
            )}
          </DataRow>
          <DataRow label={tr("fa", "newsroom.ui.StoryDossier_7")}>
            <TruthChip
              status={bucket === 'UNKNOWN' ? 'UNKNOWN' : 'LIVE'}
              size="xs"
              label={FRESHNESS_LABEL_EN[bucket]}
            />
          </DataRow>
          <DataRow label={tr("fa", "newsroom.ui.StoryDossier_8")}>
            <span className="font-nw-fa">{CLAIM_STRENGTH_LABEL_FA[story.claimStrength]}</span>
            <span className="ms-1 font-nw-en text-[12px] text-nw-text-faint">
              {CLAIM_STRENGTH_LABEL_EN[story.claimStrength]}
            </span>
          </DataRow>
          <DataRow label={tr("fa", "newsroom.ui.StoryDossier_9")}>
            <span className="nw-mono">
              {trf("newsroom.fmt.indepOfTotal", { a: independentSources, b: totalSources })}
            </span>
          </DataRow>
        </div>

        {story.marketImpactNoteFa ? (
          <p className="mt-2.5 rounded-[6px] border border-nw-line-soft bg-nw-surface-2/60 px-2.5 py-2 text-[12px] leading-relaxed text-nw-text-dim">
            {story.marketImpactNoteFa}
          </p>
        ) : null}

        {conflict ? (
          <div
            className="mt-2.5 rounded-[6px] border border-nw-danger/40 bg-nw-danger/[0.06] px-2.5 py-2"
            data-testid="dossier-conflict-notice"
          >
            <p className="flex items-center gap-1.5 text-[12px] text-nw-danger">
              <IconWarning size={13} />
              <span className="font-nw-fa">{trf("newsroom.fmt.openConflict", { topic: conflict.topicFa })}</span>
              <TruthChip status="CONFLICT" size="xs" />
            </p>
            <p className="mt-1 text-[12px] leading-relaxed text-nw-danger/80">
              {tr("fa", "newsroom.ui.StoryDossier_10")}
            </p>
          </div>
        ) : null}

        <p className="mt-3 border-t border-nw-line-soft pt-2 text-[12px] leading-relaxed text-nw-text-faint">
          {tr("fa", "newsroom.ui.StoryDossier_11")}
          {tr("fa", "newsroom.ui.StoryDossier_12")}
        </p>
      </div>
    </Panel>
  );
}

export default StoryDossier;
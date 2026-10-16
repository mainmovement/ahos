'use client';

import { TruthChip, MissingValue } from '@/components/truth';
import {
  ACTION,
  CLAIM_STRENGTH_LABEL_EN,
  CLAIM_STRENGTH_LABEL_FA,
  MARKET_LABEL_EN,
  MARKET_LABEL_FA,
  PANEL,
} from '@/features/newsroom/lib/labels';
import {
  FRESHNESS_LABEL_EN,
  formatRelativeFa,
  formatStampFa,
  freshnessBucket,
} from '@/features/newsroom/lib/format';
import type { StoryView } from '@/features/newsroom/lib/selectors';
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
          title="هیچ خبری انتخاب نشده"
          body="برای گشودنِ پرونده، یک خبر از کارتابل انتخاب کنید. این صفحه فقط خواندنی است."
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
          <span className="ah-mono text-[10px] text-ah-gold/80">{story.id}</span>
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
            className="inline-flex items-center gap-1 rounded-[6px] border border-ah-line px-2 py-[4px] text-[11px] text-ah-text-dim transition-colors hover:border-ah-gold/40 hover:text-ah-text"
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
            className="inline-flex h-[22px] w-[22px] items-center justify-center rounded-[6px] border border-ah-line text-ah-text-dim transition-colors hover:border-ah-line-strong hover:text-ah-text"
          >
            <IconClose size={12} />
          </button>
        </>
      }
      bodyClassName="ah-scroll min-h-0 overflow-auto"
    >
      <div className="ah-drawer-in p-3" key={story.id}>
        <h3 className="text-[15px] font-semibold leading-snug text-ah-text">{story.headlineFa}</h3>
        {story.headlineEn ? (
          <p className="mt-1 font-ah-en text-[11px] leading-snug text-ah-text-faint">{story.headlineEn}</p>
        ) : (
          <p className="mt-1 flex items-center gap-1.5">
            <TruthChip status="MISSING" size="xs" hideDot />
            <span className="text-[10.5px] text-ah-text-faint">تیتر انگلیسی برای این خبر موجود نیست.</span>
          </p>
        )}

        <div className="mt-2.5 grid grid-cols-2 gap-x-4">
          <DataRow label="بازار">
            <span className="font-ah-fa">{MARKET_LABEL_FA[story.market]}</span>
            <span className="ms-1 font-ah-en text-[9.5px] text-ah-text-faint">
              {MARKET_LABEL_EN[story.market]}
            </span>
          </DataRow>
          <DataRow label="تأیید">
            <TruthChip status={verification} size="xs" />
          </DataRow>
          <DataRow label="انتشار">
            {story.publishedAt ? (
              <span
                className="ah-mono"
                title={`${formatStampFa(story.publishedAt)} · ${formatRelativeFa(story.publishedAt, nowIso)}`}
              >
                {formatStampFa(story.publishedAt)}
              </span>
            ) : (
              <MissingValue fa />
            )}
          </DataRow>
          <DataRow label="تازگی">
            <TruthChip
              status={bucket === 'UNKNOWN' ? 'UNKNOWN' : 'LIVE'}
              size="xs"
              label={FRESHNESS_LABEL_EN[bucket]}
            />
          </DataRow>
          <DataRow label="قدرت ادعا">
            <span className="font-ah-fa">{CLAIM_STRENGTH_LABEL_FA[story.claimStrength]}</span>
            <span className="ms-1 font-ah-en text-[9.5px] text-ah-text-faint">
              {CLAIM_STRENGTH_LABEL_EN[story.claimStrength]}
            </span>
          </DataRow>
          <DataRow label="منابع">
            <span className="ah-mono">
              {independentSources} مستقل / {totalSources} کل
            </span>
          </DataRow>
        </div>

        {story.marketImpactNoteFa ? (
          <p className="mt-2.5 rounded-[6px] border border-ah-line-soft bg-ah-surface-2/60 px-2.5 py-2 text-[11px] leading-relaxed text-ah-text-dim">
            {story.marketImpactNoteFa}
          </p>
        ) : null}

        {conflict ? (
          <div
            className="mt-2.5 rounded-[6px] border border-ah-danger/40 bg-ah-danger/[0.06] px-2.5 py-2"
            data-testid="dossier-conflict-notice"
          >
            <p className="flex items-center gap-1.5 text-[11.5px] text-ah-danger">
              <IconWarning size={13} />
              <span className="font-ah-fa">تعارضِ باز: {conflict.topicFa}</span>
              <TruthChip status="CONFLICT" size="xs" />
            </p>
            <p className="mt-1 text-[10.5px] leading-relaxed text-ah-danger/80">
              حلِ خودکار ممنوع است. هر دو ادعا در تختهٔ تعارض نگه داشته می‌شوند تا قاضی تصمیم بگیرد.
            </p>
          </div>
        ) : null}

        <p className="mt-3 border-t border-ah-line-soft pt-2 text-[10px] leading-relaxed text-ah-text-faint">
          این تیتر اطلاع است، نه سیگنال. هیچ قیمتِ لحظه‌ای از آن استخراج نشده و هیچ کنترل معاملاتی در
          این صفحه وجود ندارد.
        </p>
      </div>
    </Panel>
  );
}

export default StoryDossier;

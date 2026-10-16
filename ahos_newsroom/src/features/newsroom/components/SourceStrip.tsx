'use client';

import { TruthChip } from '@/components/truth';
import { MissingValue } from '@/components/truth';
import { PANEL } from '@/features/newsroom/lib/labels';
import { formatRelativeFa, formatStampFa } from '@/features/newsroom/lib/format';
import type { NewsSource, NewsroomSnapshot } from '@/features/newsroom/lib/types';
import { Panel } from './primitives';

const CREDIBILITY_TONE: Record<NewsSource['credibility'], string> = {
  A: 'border-ah-cyan/40 text-ah-cyan',
  B: 'border-ah-gold/40 text-ah-gold/85',
  C: 'border-ah-line-strong text-ah-text-dim',
  UNKNOWN: 'border-ah-unknown/40 text-ah-unknown',
};

function CredibilityBadge({ tier }: { tier: NewsSource['credibility'] }) {
  return (
    <span
      data-testid="credibility-badge"
      data-credibility={tier}
      title={`ردهٔ اعتبار منبع: ${tier}`}
      className={`inline-flex h-[18px] w-[18px] shrink-0 items-center justify-center rounded-[4px] border font-ah-en text-[10px] font-semibold ${CREDIBILITY_TONE[tier]}`}
    >
      {tier === 'UNKNOWN' ? '?' : tier}
    </span>
  );
}

export interface SourceStripProps {
  sources: readonly NewsSource[];
  nowIso: string | null;
  demo: boolean;
  independentSources: number;
  className?: string;
}

/**
 * The source strip for one story.
 *
 * Two independent, live, tiered sources ⇒ VERIFIED. One source ⇒ PARTIAL and
 * the VERIFIED chip is never rendered. URLs are printed as plain text: this
 * screen performs no outbound request.
 */
export function SourceStrip({ sources, nowIso, demo, independentSources, className = '' }: SourceStripProps) {
  const twoSourceRuleMet = independentSources >= 2;

  return (
    <Panel
      title={PANEL.sources}
      titleEn="SOURCE STRIP"
      demo={demo}
      data-testid="source-strip"
      className={className}
      chips={
        <>
          <span className="ah-mono text-[10px] text-ah-text-faint">{sources.length} منبع</span>
          <span className="ah-mono text-[10px] text-ah-text-faint">{independentSources} مستقل</span>
        </>
      }
      bodyClassName="flex min-h-0 flex-col"
    >
      {sources.length === 0 ? (
        <p className="px-3 py-4 text-center text-[11.5px] text-ah-text-faint">
          منبعی به این خبر پیوست نشده است.
        </p>
      ) : (
        <ul className="ah-scroll min-h-0 flex-1 overflow-auto" data-testid="source-list">
          {sources.map((source) => (
            <li
              key={source.id}
              className="flex items-start gap-2 border-b border-ah-line-soft/70 px-3 py-2 last:border-b-0"
              data-testid={`source-row-${source.id}`}
            >
              <CredibilityBadge tier={source.credibility} />
              <div className="min-w-0 flex-1">
                <p className="truncate text-[12px] leading-tight text-ah-text" title={source.nameFa}>
                  {source.nameFa}
                </p>
                <p
                  className="mt-0.5 truncate font-ah-en text-[10px] leading-tight text-ah-text-faint"
                  title={`آدرس فقط نمایش داده می‌شود و هرگز فراخوانی نمی‌شود: ${source.urlPlaceholder}`}
                >
                  {source.urlPlaceholder}
                </p>
                <p className="mt-1 text-[10.5px] leading-tight text-ah-text-faint">
                  {source.noteFa ?? '—'}
                </p>
              </div>
              <div className="flex shrink-0 flex-col items-end gap-1">
                <TruthChip status={source.status} size="xs" />
                {source.lastReadAt ? (
                  <span
                    className="ah-mono text-[10px] text-ah-text-dim"
                    title={formatStampFa(source.lastReadAt)}
                  >
                    {formatRelativeFa(source.lastReadAt, nowIso)}
                  </span>
                ) : (
                  <span className="ah-mono text-[10px] text-ah-unknown" title="زمانِ خوانش نامعلوم">
                    <MissingValue fa />
                  </span>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}

      <div className="shrink-0 border-t border-ah-line-soft px-3 py-1.5">
        <p className="text-[10.5px] leading-relaxed text-ah-text-faint">
          {twoSourceRuleMet
            ? `دو منبعِ مستقل و زنده ⇒ سطح تأیید «VERIFIED» مجاز است.`
            : independentSources === 1
              ? 'تنها یک منبعِ مستقل ⇒ هرگز «VERIFIED» نیست (PARTIAL).'
              : 'هیچ منبعِ مستقلِ زنده‌ای ندارد ⇒ UNKNOWN است، نه صفر.'}
        </p>
      </div>
    </Panel>
  );
}

export default SourceStrip;

/** Convenience selector used by the dossier. */
export function sourcesForStory(snapshot: NewsroomSnapshot, sourceIds: readonly string[]): NewsSource[] {
  return sourceIds
    .map((id) => snapshot.sources.find((s) => s.id === id))
    .filter((s): s is NewsSource => s !== undefined);
}

"use client";
import { tr } from "@/src/lib/i18n";

import { trf } from '@/src/features/newsroom/lib/trf';
import { TruthChip } from '@/src/features/newsroom/truth';
import { MissingValue } from '@/src/features/newsroom/truth';
import { PANEL } from '@/src/features/newsroom/lib/labels';
import { formatRelativeFa, formatStampFa } from '@/src/features/newsroom/lib/format';
import type { NewsSource, NewsroomSnapshot } from '@/src/features/newsroom/lib/types';
import { Panel } from './primitives';

const CREDIBILITY_TONE: Record<NewsSource['credibility'], string> = {
  A: 'border-nw-cyan/40 text-nw-cyan',
  B: 'border-nw-gold/40 text-nw-gold/85',
  C: 'border-nw-line-strong text-nw-text-dim',
  UNKNOWN: 'border-nw-unknown/40 text-nw-unknown',
};

function CredibilityBadge({ tier }: { tier: NewsSource['credibility'] }) {
  return (
    <span
      data-testid="credibility-badge"
      data-credibility={tier}
      title={trf("newsroom.fmt.credTier", { tier })}
      className={`inline-flex h-[18px] w-[18px] shrink-0 items-center justify-center rounded-[4px] border font-nw-en text-[12px] font-semibold ${CREDIBILITY_TONE[tier]}`}
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
          <span className="nw-mono text-[12px] text-nw-text-faint">{trf("newsroom.fmt.sourcesN", { n: sources.length })}</span>
          <span className="nw-mono text-[12px] text-nw-text-faint">{trf("newsroom.fmt.independentN", { n: independentSources })}</span>
        </>
      }
      bodyClassName="flex min-h-0 flex-col"
    >
      {sources.length === 0 ? (
        <p className="px-3 py-4 text-center text-[12px] text-nw-text-faint">
          {tr("fa", "newsroom.ui.SourceStrip_1")}
        </p>
      ) : (
        <ul className="nw-scroll min-h-0 flex-1 overflow-auto" data-testid="source-list">
          {sources.map((source) => (
            <li
              key={source.id}
              className="flex items-start gap-2 border-b border-nw-line-soft/70 px-3 py-2 last:border-b-0"
              data-testid={`source-row-${source.id}`}
            >
              <CredibilityBadge tier={source.credibility} />
              <div className="min-w-0 flex-1">
                <p className="truncate text-[13px] leading-tight text-nw-text" title={source.nameFa}>
                  {source.nameFa}
                </p>
                <p
                  className="mt-0.5 truncate font-nw-en text-[12px] leading-tight text-nw-text-faint"
                  title={trf("newsroom.fmt.urlNote", { url: source.urlPlaceholder })}
                >
                  {source.urlPlaceholder}
                </p>
                <p className="mt-1 text-[12px] leading-tight text-nw-text-faint">
                  {source.noteFa ?? '—'}
                </p>
              </div>
              <div className="flex shrink-0 flex-col items-end gap-1">
                <TruthChip status={source.status} size="xs" />
                {source.lastReadAt ? (
                  <span
                    className="nw-mono text-[12px] text-nw-text-dim"
                    title={formatStampFa(source.lastReadAt)}
                  >
                    {formatRelativeFa(source.lastReadAt, nowIso)}
                  </span>
                ) : (
                  <span className="nw-mono text-[12px] text-nw-unknown" title={tr("fa", "newsroom.ui.SourceStrip_2")}>
                    <MissingValue fa />
                  </span>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}

      <div className="shrink-0 border-t border-nw-line-soft px-3 py-1.5">
        <p className="text-[12px] leading-relaxed text-nw-text-faint">
          {twoSourceRuleMet
            ? tr("fa", "newsroom.ui.SourceStrip_3")
            : independentSources === 1
              ? tr("fa", "newsroom.ui.SourceStrip_4")
              : tr("fa", "newsroom.ui.SourceStrip_5")}
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
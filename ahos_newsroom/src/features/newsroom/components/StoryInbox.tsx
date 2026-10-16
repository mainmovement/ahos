'use client';

import { useMemo } from 'react';

import { TruthChip } from '@/components/truth';
import { CLAIM_STRENGTH_LABEL_EN, CLAIM_STRENGTH_LEVEL, MARKET_LABEL_EN, PANEL, ACTION } from '@/features/newsroom/lib/labels';
import {
  FRESHNESS_LABEL_EN,
  formatRelativeFa,
  formatTimeFa,
  freshnessBucket,
  toPersianDigits,
} from '@/features/newsroom/lib/format';
import { computeTotals } from '@/features/newsroom/lib/truth';
import { buildStoryView, filterStories, type StoryFilterId, type StoryView } from '@/features/newsroom/lib/selectors';
import type { ClaimStrength, NewsroomSnapshot } from '@/features/newsroom/lib/types';
import { Panel, StateBlock } from './primitives';
import { IconEye } from './icons';

/** ~7 highlighted items on the calm default view; the rest live behind «جزئیات». */
export const CALM_STORY_LIMIT = 7;

function ClaimStrengthMeter({ strength }: { strength: ClaimStrength }) {
  const level = CLAIM_STRENGTH_LEVEL[strength];
  return (
    <span
      className="inline-flex items-center gap-1"
      title={`قدرت ادعا: ${CLAIM_STRENGTH_LABEL_EN[strength]}`}
      data-testid="claim-strength"
      data-strength={strength}
    >
      <span className="inline-flex items-center gap-[2px]" aria-hidden="true">
        {[0, 1, 2, 3].map((i) => (
          <span
            key={i}
            className={[
              'inline-block h-[7px] w-[3px] rounded-[1px]',
              i < level ? (strength === 'STRONG' ? 'bg-ah-cyan/80' : 'bg-ah-gold/70') : 'bg-ah-line-strong',
            ].join(' ')}
          />
        ))}
      </span>
      <span className="font-ah-en text-[9px] tracking-[0.1em] text-ah-text-faint">
        {CLAIM_STRENGTH_LABEL_EN[strength]}
      </span>
    </span>
  );
}

const FILTERS: readonly { id: StoryFilterId; label: string }[] = [
  { id: 'ALL', label: ACTION.filterAll },
  { id: 'OIL', label: 'نفت' },
  { id: 'GOLD', label: 'طلا' },
  { id: 'CONFLICT', label: ACTION.filterConflict },
  { id: 'DEMO', label: ACTION.filterDemo },
];

export interface StoryInboxProps {
  snapshot: NewsroomSnapshot;
  filter: StoryFilterId;
  onFilterChange: (filter: StoryFilterId) => void;
  selectedId: string | null;
  onSelect: (id: string) => void;
  showDetails: boolean;
  onToggleDetails: () => void;
  demo: boolean;
}

export function StoryInbox({
  snapshot,
  filter,
  onFilterChange,
  selectedId,
  onSelect,
  showDetails,
  onToggleDetails,
  demo,
}: StoryInboxProps) {
  const views = useMemo<StoryView[]>(
    () => filterStories(snapshot, filter).map((story) => buildStoryView(snapshot, story)),
    [snapshot, filter],
  );

  const totals = useMemo(() => computeTotals(snapshot), [snapshot]);
  const visible = showDetails ? views : views.slice(0, CALM_STORY_LIMIT);
  const hidden = Math.max(0, views.length - visible.length);

  return (
    <Panel
      title={PANEL.inbox}
      accent="gold"
      demo={demo}
      data-testid="story-inbox"
      chips={
        <>
          <span className="ah-mono text-[10px] text-ah-text-faint" title="تعداد کل خبرها">
            {toPersianDigits(views.length)}
          </span>
          <TruthChip status={totals.verified > 0 ? 'LIVE' : 'UNKNOWN'} size="xs" label={`${totals.verified} VERIFIED`} />
          {totals.conflict > 0 ? (
            <TruthChip status="CONFLICT" size="xs" label={`${totals.conflict} CONFLICT`} />
          ) : null}
          {totals.demo > 0 ? <TruthChip status="DEMO" size="xs" label={`${totals.demo} DEMO`} ribbon /> : null}
        </>
      }
      bodyClassName="flex min-h-0 flex-col"
    >
      <div className="flex shrink-0 flex-wrap items-center gap-1.5 border-b border-ah-line-soft px-3 py-2">
        {FILTERS.map((f) => (
          <button
            key={f.id}
            type="button"
            onClick={() => onFilterChange(f.id)}
            aria-pressed={filter === f.id}
            data-testid={`inbox-filter-${f.id}`}
            className={[
              'rounded-[6px] border px-2 py-[3px] text-[11px] transition-colors duration-150',
              filter === f.id
                ? 'border-ah-gold/55 bg-ah-gold/12 text-ah-gold-strong'
                : 'border-ah-line text-ah-text-dim hover:border-ah-line-strong hover:text-ah-text',
            ].join(' ')}
          >
            {f.label}
          </button>
        ))}
        <button
          type="button"
          onClick={onToggleDetails}
          data-testid="inbox-details-toggle"
          className="ms-auto rounded-[6px] border border-ah-line px-2 py-[3px] text-[11px] text-ah-text-dim transition-colors hover:border-ah-line-strong hover:text-ah-text"
        >
          {showDetails ? ACTION.detailsOff : ACTION.details}
        </button>
      </div>

      {views.length === 0 ? (
        <StateBlock
          title="هیچ خبری با این پالایه نیست"
          body="پالایه را عوض کنید. ردیفِ ساختگی اضافه نمی‌شود."
          glyph={<IconEye size={22} />}
        />
      ) : showDetails ? (
        <div className="ah-scroll min-h-0 flex-1 overflow-auto">
          <table className="text-[11px]" data-testid="story-table">
            <thead className="sticky top-0 bg-ah-surface">
              <tr className="border-b border-ah-line-soft text-ah-text-faint">
                {['شناسه', 'بازار', 'تیتر', 'انتشار', 'منابع', 'مستقل', 'تأیید', 'وضعیت'].map((h) => (
                  <th key={h} className="whitespace-nowrap px-2 py-1.5 text-right font-normal">
                    <span className="ah-label">{h}</span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {views.map((view) => (
                <tr
                  key={view.story.id}
                  onClick={() => onSelect(view.story.id)}
                  data-testid={`story-row-${view.story.id}`}
                  className={[
                    'cursor-pointer border-b border-ah-line-soft/70 transition-colors',
                    selectedId === view.story.id ? 'bg-ah-gold/[0.07]' : 'hover:bg-ah-surface-2/70',
                  ].join(' ')}
                >
                  <td className="ah-mono whitespace-nowrap px-2 py-1.5 text-ah-gold/80">{view.story.id}</td>
                  <td className="whitespace-nowrap px-2 py-1.5 font-ah-en text-[10px] text-ah-text-dim">
                    {MARKET_LABEL_EN[view.story.market]}
                  </td>
                  <td className="max-w-[280px] truncate px-2 py-1.5 text-ah-text" title={view.story.headlineFa}>
                    {view.story.headlineFa}
                  </td>
                  <td className="whitespace-nowrap px-2 py-1.5 text-ah-text-dim">
                    {view.story.publishedAt ? formatTimeFa(view.story.publishedAt) : 'ناموجود'}
                  </td>
                  <td className="ah-mono whitespace-nowrap px-2 py-1.5 text-ah-text-dim">
                    {view.totalSources}
                  </td>
                  <td className="ah-mono whitespace-nowrap px-2 py-1.5 text-ah-text-dim">
                    {view.independentSources}
                  </td>
                  <td className="whitespace-nowrap px-2 py-1.5">
                    <TruthChip status={view.verification} size="xs" hideDot />
                  </td>
                  <td className="whitespace-nowrap px-2 py-1.5">
                    <TruthChip status={view.story.status} size="xs" />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <ul className="ah-scroll min-h-0 flex-1 overflow-auto p-2" data-testid="story-list">
          {visible.map((view) => {
            const selected = selectedId === view.story.id;
            const bucket = freshnessBucket(view.story.publishedAt, snapshot.generatedAt);
            return (
              <li key={view.story.id} className="mb-1.5 last:mb-0">
                <button
                  type="button"
                  onClick={() => onSelect(view.story.id)}
                  data-testid={`story-card-${view.story.id}`}
                  aria-pressed={selected}
                  className={[
                    'w-full rounded-[6px] border px-2.5 py-2 text-right transition-colors duration-150',
                    selected
                      ? 'border-ah-gold/50 bg-ah-gold/[0.07]'
                      : 'border-ah-line-soft bg-transparent hover:border-ah-line-strong hover:bg-ah-surface-2/60',
                  ].join(' ')}
                >
                  <div className="mb-1 flex items-center justify-between gap-2">
                    <span className="flex min-w-0 items-center gap-1.5">
                      <span className="rounded-[4px] border border-ah-line px-1 py-[1px] font-ah-en text-[9px] tracking-[0.1em] text-ah-text-dim">
                        {MARKET_LABEL_EN[view.story.market]}
                      </span>
                      <span className="ah-mono truncate text-[10px] text-ah-text-faint">{view.story.id}</span>
                    </span>
                    <TruthChip
                      status={bucket === 'UNKNOWN' ? 'UNKNOWN' : bucket === 'STALE' ? 'STALE' : 'LIVE'}
                      size="xs"
                      label={FRESHNESS_LABEL_EN[bucket]}
                      title={`${formatRelativeFa(view.story.publishedAt, snapshot.generatedAt)}`}
                    />
                  </div>

                  <p className="mb-0.5 line-clamp-2 text-[12.5px] leading-snug text-ah-text">
                    {view.story.headlineFa}
                  </p>
                  {view.story.headlineEn ? (
                    <p className="mb-1.5 line-clamp-1 font-ah-en text-[10px] leading-snug text-ah-text-faint">
                      {view.story.headlineEn}
                    </p>
                  ) : null}

                  <div className="flex items-center justify-between gap-2">
                    <span className="flex items-center gap-2">
                      <ClaimStrengthMeter strength={view.story.claimStrength} />
                      <span className="ah-mono text-[10px] text-ah-text-faint">
                        {view.independentSources}/{view.totalSources} منبع
                      </span>
                    </span>
                    <TruthChip status={view.verification} size="xs" />
                  </div>
                </button>
              </li>
            );
          })}
          {hidden > 0 ? (
            <li className="px-1 pt-1 text-center">
              <span className="ah-label">
                {hidden} خبرِ دیگر · «{ACTION.details}» را بزنید
              </span>
            </li>
          ) : null}
        </ul>
      )}
    </Panel>
  );
}

export default StoryInbox;

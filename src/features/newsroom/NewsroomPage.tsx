"use client";
import { tr } from "@/src/lib/i18n";

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

import { TruthChip } from '@/src/features/newsroom/truth';
import { COPY, PANEL } from '@/src/features/newsroom/lib/labels';
import { newsroomAdapter, type NewsroomScenario } from '@/src/mock/newsroom';
import { buildStoryView, filterStories, type StoryFilterId, type StoryView } from '@/src/features/newsroom/lib/selectors';
import { type Tier } from '@/src/features/newsroom/lib/tier';
import { demoteLiveOnMock } from '@/src/features/newsroom/lib/normalize';
import { computeTotals } from '@/src/features/newsroom/lib/truth';
import type { NewsroomLoadState, NewsroomSnapshot } from '@/src/features/newsroom/lib/types';
import { ConflictBoard } from './components/ConflictBoard';
import { JudgeHandoffTile } from './components/JudgeHandoffTile';
import { MarketFocusPills } from './components/MarketFocusPills';
import { PaperOnlyGuard, PaperOnlyPill } from './components/PaperOnlyGuard';
import { ReporterRoster } from './components/ReporterRoster';
import { SourceStrip } from './components/SourceStrip';
import { StoryDossier } from './components/StoryDossier';
import { StoryInbox } from './components/StoryInbox';
import { VerificationPipeline } from './components/VerificationPipeline';
import { IconRefresh, IconWarning } from './components/icons';
import { StateBlock } from './components/primitives';
import { TelemetryStrip } from './components/TelemetryStrip';
import { PageBar } from './components/PageBar';

const GRID =
  'grid min-w-0 flex-1 items-start gap-3.5 p-3.5 grid-cols-1 xl:grid-cols-[minmax(320px,1.1fr)_minmax(380px,1.3fr)_minmax(300px,1fr)]';

interface LoadResult {
  key: string;
  state: Extract<NewsroomLoadState, 'READY' | 'ERROR'>;
  snapshot: NewsroomSnapshot | null;
  error: string | null;
}

function useCopyId(): [string | null, (id: string) => void] {
  const [copied, setCopied] = useState<string | null>(null);
  const timer = useRef<number | null>(null);

  const copy = useCallback((id: string) => {
    try {
      void navigator.clipboard?.writeText(id);
    } catch {
      /* clipboard is optional — the chip still confirms the intent */
    }
    setCopied(id);
    if (timer.current !== null) window.clearTimeout(timer.current);
    timer.current = window.setTimeout(() => setCopied(null), 1600);
  }, []);

  useEffect(() => () => {
    if (timer.current !== null) window.clearTimeout(timer.current);
  }, []);

  return [copied, copy];
}

function DemoBanner() {
  return (
    <div
      className="nw-demo-stripes flex shrink-0 flex-wrap items-center gap-x-3 gap-y-1 border-b border-nw-gold/30 px-4 py-1.5"
      data-testid="demo-banner"
    >
      <span className="font-nw-en text-[12px] font-semibold tracking-[0.16em] text-nw-gold">
        {COPY.demoBannerTitle}
      </span>
      <span className="text-[12px] leading-relaxed text-nw-gold/85">{COPY.demoBannerBody}</span>
    </div>
  );
}

function PageStateBanner({ state }: { state: Extract<NewsroomLoadState, 'EMPTY' | 'UNAVAILABLE'> }) {
  const isEmpty = state === 'EMPTY';
  return (
    <div
      className={[
        'flex shrink-0 items-center gap-2 border-b px-4 py-1.5',
        isEmpty ? 'border-nw-line bg-nw-surface-2/60' : 'border-nw-unknown/30 bg-nw-unknown/[0.07]',
      ].join(' ')}
      data-testid={`page-state-${state}`}
    >
      <TruthChip status={isEmpty ? 'UNKNOWN' : 'UNAVAILABLE'} size="xs" showFa />
      <span className="text-[12px] text-nw-text-dim">
        {isEmpty ? COPY.emptyBody : COPY.unavailableBody}
      </span>
    </div>
  );
}

export interface NewsroomPageProps {
  /** `?state=` — view-only demo scenario. */
  scenario?: NewsroomScenario;
  /** `?demo=1` — force every row to DEMO. */
  forceDemo?: boolean;
  /** `?violation=1` — force the VIOLATION bar. */
  forceViolation?: boolean;
  /** `?tier=0|1|2`. */
  tier?: Tier;
  /** `?story=<id>` deep link. */
  story?: string | null;
  /** `?details=1` — open the dense tables. */
  details?: boolean;
}

export function NewsroomPage({
  scenario = 'calm',
  forceDemo = false,
  forceViolation = false,
  tier: urlTier = 1,
  story: deepLinkedStory = null,
  details = false,
}: NewsroomPageProps = {}) {
  const [tier, setTier] = useState<Tier>(urlTier);
  const [filter, setFilter] = useState<StoryFilterId>('ALL');
  const [showDetails, setShowDetails] = useState(details);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [copiedId, copyId] = useCopyId();
  const [reloadKey, setReloadKey] = useState(0);

  /**
   * One request = one key. The render below treats a result whose key no longer
   * matches as "not loaded yet", so switching scenario (or retrying) falls back
   * to LOADING without a synchronous setState inside an effect.
   */
  const requestKey = `${scenario}|${String(forceDemo)}|${String(forceViolation)}|${reloadKey}`;

  const [result, setResult] = useState<LoadResult | null>(null);
  const current = result !== null && result.key === requestKey ? result : null;

  const loadState: NewsroomLoadState = current ? current.state : 'LOADING';
  const snapshot = current?.state === 'READY' ? current.snapshot : null;
  const error = current?.state === 'ERROR' ? current.error : null;

  useEffect(() => {
    let cancelled = false;

    newsroomAdapter
      .load({ scenario, forceDemo, forceViolation })
      .then((next) => {
        if (cancelled) return;
        const safe = newsroomAdapter.kind === 'mock' ? demoteLiveOnMock(next) : next;
        setResult({ key: requestKey, state: 'READY', snapshot: safe, error: null });
        setSelectedId((selected) => selected ?? deepLinkedStory ?? safe.stories[0]?.id ?? null);
      })
      .catch((cause: unknown) => {
        if (cancelled) return;
        setResult({
          key: requestKey,
          state: 'ERROR',
          snapshot: null,
          error: cause instanceof Error ? cause.message : 'unknown error',
        });
      });

    return () => {
      cancelled = true;
    };
    // `deepLinkedStory` is only a deep-link seed, deliberately not a dependency.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scenario, forceDemo, forceViolation, requestKey]);

  const views = useMemo<StoryView[]>(
    () => (snapshot ? filterStories(snapshot, filter).map((s) => buildStoryView(snapshot, s)) : []),
    [snapshot, filter],
  );

  const selectedView = useMemo<StoryView | null>(() => {
    if (!snapshot || !selectedId) return null;
    const story = snapshot.stories.find((s) => s.id === selectedId);
    return story ? buildStoryView(snapshot, story) : null;
  }, [snapshot, selectedId]);

  const totals = useMemo(() => (snapshot ? computeTotals(snapshot) : null), [snapshot]);

  const isMock = newsroomAdapter.kind === 'mock';
  const showDemoBanner = forceDemo || isMock;

  const derivedPageState = (): Extract<NewsroomLoadState, 'EMPTY' | 'UNAVAILABLE'> | null => {
    if (!snapshot) return null;
    if (snapshot.stories.length === 0) return 'EMPTY';
    const readable = snapshot.sources.some((s) => s.lastReadAt !== null && s.status !== 'UNKNOWN');
    return readable ? null : 'UNAVAILABLE';
  };
  const pageState = derivedPageState();

  const pageStatus: 'DEMO' | 'PARTIAL' | 'LIVE' | 'UNKNOWN' =
    loadState === 'LOADING'
      ? 'UNKNOWN'
      : loadState === 'ERROR'
        ? 'UNKNOWN'
        : showDemoBanner
          ? 'DEMO'
          : totals && totals.verified > 0
            ? 'LIVE'
            : 'PARTIAL';

  if (loadState === 'ERROR' || loadState === 'LOADING') {
    return (
      <div className="nw-root" data-tier={tier} dir="rtl">
        <div className="nw-shell flex flex-col">
          <PageBar pageStatus="UNKNOWN" tier={tier} onTierChange={setTier} />
          <div className="flex flex-1">
            <main className={`${GRID} items-start`}>
              {[PANEL.inbox, PANEL.dossier, PANEL.conflicts].map((label) => (
                <section key={label} className="nw-panel min-h-[220px]">
                  <header className="border-b border-nw-line-soft px-3 py-2">
                    <h2 className="text-[13px] font-semibold text-nw-text-dim">{label}</h2>
                  </header>
                  <StateBlock
                    tone={loadState === 'ERROR' ? 'error' : 'neutral'}
                    title={loadState === 'ERROR' ? COPY.errorTitle : COPY.loading}
                    body={loadState === 'ERROR' ? (error ?? COPY.errorBody) : tr("fa", "newsroom.ui.NewsroomPage_1")}
                    glyph={<IconWarning size={20} />}
                    action={
                      loadState === 'ERROR' ? (
                        <button
                          type="button"
                          onClick={() => setReloadKey((k) => k + 1)}
                          className="inline-flex items-center gap-1.5 rounded-[6px] border border-nw-line px-2 py-[4px] text-[12px] text-nw-text-dim hover:border-nw-line-strong hover:text-nw-text"
                        >
                          <IconRefresh size={12} />
                          <span>{tr("fa", "newsroom.ui.retry")}</span>
                        </button>
                      ) : null
                    }
                  />
                </section>
              ))}
            </main>
          </div>
          <div className="flex shrink-0 items-center gap-2 border-t border-nw-line px-4 py-2">
            <TruthChip status={loadState === 'ERROR' ? 'REJECTED' : 'UNKNOWN'} size="xs" />
            <span className="nw-mono text-[12px] text-nw-text-faint">
              {loadState === 'ERROR' ? error : 'LOADING'}
            </span>
            <span className="ms-auto">
              <PaperOnlyPill compact />
            </span>
          </div>
        </div>
      </div>
    );
  }

  if (!snapshot || !totals) return null;

  return (
    <div className="nw-root" data-tier={tier} dir="rtl">
      <PaperOnlyGuard snapshot={snapshot} forced={forceViolation}>
        <div className="nw-shell flex flex-col">
          <PageBar pageStatus={pageStatus} tier={tier} onTierChange={setTier} />

          {showDemoBanner ? <DemoBanner /> : null}
          {pageState ? <PageStateBanner state={pageState} /> : null}

          <div className="border-b border-nw-line-soft px-4 py-1.5">
            <MarketFocusPills
              markets={snapshot.markets}
              active={filter === 'OIL' || filter === 'GOLD' ? filter : null}
              onSelect={(id) => setFilter(id)}
            />
          </div>

          <div className="flex flex-1">
            <main className={GRID}>
              {/* 1 · RIGHT — story inbox */}
              <div className="flex min-h-0 flex-col">
                <StoryInbox
                  snapshot={snapshot}
                  filter={filter}
                  onFilterChange={setFilter}
                  selectedId={selectedId}
                  onSelect={setSelectedId}
                  showDetails={showDetails}
                  onToggleDetails={() => setShowDetails((v) => !v)}
                  demo={showDemoBanner}
                />
              </div>

              {/* 2 · CENTRE — dossier + source strip + pipeline */}
              <div className="flex min-h-0 flex-col gap-3">
                <StoryDossier
                  view={selectedView}
                  onClose={() => setSelectedId(null)}
                  onCopyId={copyId}
                  copiedId={copiedId}
                  demo={showDemoBanner}
                  nowIso={snapshot.generatedAt}
                  
                />
                {selectedView ? (
                  <>
                    <SourceStrip
                      sources={selectedView.sources}
                      nowIso={snapshot.generatedAt}
                      demo={showDemoBanner || selectedView.story.demo}
                      independentSources={selectedView.independentSources}
                      
                    />
                    <VerificationPipeline
                      stages={selectedView.pipeline}
                      demo={showDemoBanner}
                      className="shrink-0"
                    />
                  </>
                ) : null}
              </div>

              {/* 3 · LEFT — conflicts + reporters + handoff */}
              <aside className="flex min-h-0 flex-col gap-3">
                <ConflictBoard
                  snapshot={snapshot}
                  views={views}
                  onSelectStory={setSelectedId}
                  onCopyId={copyId}
                  copiedId={copiedId}
                  demo={showDemoBanner}
                  
                />
                <ReporterRoster
                  reporters={snapshot.reporters}
                  nowIso={snapshot.generatedAt}
                  demo={showDemoBanner}
                  
                />
                <JudgeHandoffTile
                  view={selectedView}
                  snapshot={snapshot}
                  onCopyId={copyId}
                  copiedId={copiedId}
                  demo={showDemoBanner}
                  className="shrink-0"
                />
              </aside>
            </main>

          </div>

          <TelemetryStrip snapshot={snapshot} tier={tier} />
        </div>
      </PaperOnlyGuard>
    </div>
  );
}

export default NewsroomPage;
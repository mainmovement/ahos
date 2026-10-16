'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useSearchParams } from 'next/navigation';

import { TruthChip } from '@/components/truth';
import { COPY, PANEL } from '@/features/newsroom/lib/labels';
import { newsroomAdapter, type NewsroomScenario } from '@/mock/newsroom';
import { buildStoryView, filterStories, type StoryFilterId, type StoryView } from '@/features/newsroom/lib/selectors';
import { parseTier, type Tier } from '@/features/newsroom/lib/tier';
import { computeTotals } from '@/features/newsroom/lib/truth';
import type { NewsroomLoadState, NewsroomSnapshot } from '@/features/newsroom/lib/types';
import { CapsuleDock } from './components/CapsuleDock';
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
import { Topbar } from './components/Topbar';

const GRID =
  'grid min-h-0 flex-1 gap-3 p-3 grid-cols-1 lg:grid-cols-[minmax(300px,1.05fr)_minmax(360px,1.3fr)_minmax(280px,0.95fr)]';

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
      className="ah-demo-stripes flex shrink-0 flex-wrap items-center gap-x-3 gap-y-1 border-b border-ah-gold/30 px-4 py-1.5"
      data-testid="demo-banner"
    >
      <span className="font-ah-en text-[10px] font-semibold tracking-[0.16em] text-ah-gold">
        {COPY.demoBannerTitle}
      </span>
      <span className="text-[10.5px] leading-relaxed text-ah-gold/85">{COPY.demoBannerBody}</span>
    </div>
  );
}

function PageStateBanner({ state }: { state: Extract<NewsroomLoadState, 'EMPTY' | 'UNAVAILABLE'> }) {
  const isEmpty = state === 'EMPTY';
  return (
    <div
      className={[
        'flex shrink-0 items-center gap-2 border-b px-4 py-1.5',
        isEmpty ? 'border-ah-line bg-ah-surface-2/60' : 'border-ah-unknown/30 bg-ah-unknown/[0.07]',
      ].join(' ')}
      data-testid={`page-state-${state}`}
    >
      <TruthChip status={isEmpty ? 'UNKNOWN' : 'UNAVAILABLE'} size="xs" showFa />
      <span className="text-[10.5px] text-ah-text-dim">
        {isEmpty ? COPY.emptyBody : COPY.unavailableBody}
      </span>
    </div>
  );
}

export function NewsroomPage() {
  const params = useSearchParams();

  const scenario = (params.get('state') as NewsroomScenario | null) ?? 'calm';
  const forceDemo = params.get('demo') === '1';
  const forceViolation = params.get('violation') === '1';
  const urlTier = parseTier(params.get('tier'));
  const deepLinkedStory = params.get('story');

  const [tier, setTier] = useState<Tier>(urlTier);
  const [muted, setMuted] = useState(true);
  const [filter, setFilter] = useState<StoryFilterId>('ALL');
  const [showDetails, setShowDetails] = useState(params.get('details') === '1');
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
        setResult({ key: requestKey, state: 'READY', snapshot: next, error: null });
        setSelectedId((selected) => selected ?? deepLinkedStory ?? next.stories[0]?.id ?? null);
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
      <div className="ahos-root" data-tier={tier}>
        <div className="ahos-shell flex h-screen flex-col overflow-hidden">
          <Topbar
            pageStatus="UNKNOWN"
            tier={tier}
            onTierChange={setTier}
            muted={muted}
            onToggleMute={() => setMuted((v) => !v)}
          />
          <div className="flex min-h-0 flex-1">
            <main className={`${GRID} items-start`}>
              {[PANEL.inbox, PANEL.dossier, PANEL.conflicts].map((label) => (
                <section key={label} className="ah-panel min-h-[220px]">
                  <header className="border-b border-ah-line-soft px-3 py-2">
                    <h2 className="text-[12.5px] font-semibold text-ah-text-dim">{label}</h2>
                  </header>
                  <StateBlock
                    tone={loadState === 'ERROR' ? 'error' : 'neutral'}
                    title={loadState === 'ERROR' ? COPY.errorTitle : COPY.loading}
                    body={loadState === 'ERROR' ? (error ?? COPY.errorBody) : 'در حال خواندنِ لایهٔ داده…'}
                    glyph={<IconWarning size={20} />}
                    action={
                      loadState === 'ERROR' ? (
                        <button
                          type="button"
                          onClick={() => setReloadKey((k) => k + 1)}
                          className="inline-flex items-center gap-1.5 rounded-[6px] border border-ah-line px-2 py-[4px] text-[11px] text-ah-text-dim hover:border-ah-line-strong hover:text-ah-text"
                        >
                          <IconRefresh size={12} />
                          <span>{'تلاشِ دوباره'}</span>
                        </button>
                      ) : null
                    }
                  />
                </section>
              ))}
            </main>
            <CapsuleDock />
          </div>
          <div className="flex shrink-0 items-center gap-2 border-t border-ah-line px-4 py-2">
            <TruthChip status={loadState === 'ERROR' ? 'REJECTED' : 'UNKNOWN'} size="xs" />
            <span className="ah-mono text-[10px] text-ah-text-faint">
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
    <div className="ahos-root" data-tier={tier} dir="rtl">
      <PaperOnlyGuard snapshot={snapshot} forced={forceViolation}>
        <div className="ahos-shell flex min-h-0 flex-1 flex-col overflow-hidden">
          <Topbar
            pageStatus={pageStatus}
            tier={tier}
            onTierChange={setTier}
            muted={muted}
            onToggleMute={() => setMuted((v) => !v)}
          />

          {showDemoBanner ? <DemoBanner /> : null}
          {pageState ? <PageStateBanner state={pageState} /> : null}

          <div className="border-b border-ah-line-soft px-4 py-1.5">
            <MarketFocusPills
              markets={snapshot.markets}
              active={filter === 'OIL' || filter === 'GOLD' ? filter : null}
              onSelect={(id) => setFilter(id)}
            />
          </div>

          <div className="flex min-h-0 flex-1">
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
                  className="max-h-[48%] shrink-0"
                />
                {selectedView ? (
                  <>
                    <SourceStrip
                      sources={selectedView.sources}
                      nowIso={snapshot.generatedAt}
                      demo={showDemoBanner || selectedView.story.demo}
                      independentSources={selectedView.independentSources}
                      className="min-h-0 flex-[1.15]"
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
                  className="min-h-0 flex-[1.25]"
                />
                <ReporterRoster
                  reporters={snapshot.reporters}
                  nowIso={snapshot.generatedAt}
                  demo={showDemoBanner}
                  className="min-h-0 flex-1"
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

            <CapsuleDock />
          </div>

          <TelemetryStrip snapshot={snapshot} tier={tier} />
        </div>
      </PaperOnlyGuard>
    </div>
  );
}

export default NewsroomPage;

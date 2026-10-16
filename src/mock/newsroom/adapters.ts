/**
 * Typed mock adapter for the Newsroom.
 *
 * The UI never imports fixtures directly — it only ever talks to an object that
 * satisfies `NewsroomAdapter`. Swapping in a real backend means implementing
 * the same interface (see `README_MERGE.md`); no component changes required.
 */

import type { NewsroomSnapshot } from '@/src/features/newsroom/lib/types';
import { CALM_SNAPSHOT, EMPTY_SNAPSHOT, UNAVAILABLE_SNAPSHOT, VIOLATION_SNAPSHOT } from './fixtures';

export type NewsroomScenario = 'calm' | 'empty' | 'unavailable' | 'violation' | 'error';

export interface NewsroomRequest {
  scenario?: NewsroomScenario;
  /** `?demo=1` — force every row to DEMO (excluded from all totals). */
  forceDemo?: boolean;
  /** `?violation=1` — force the VIOLATION bar even on a paper-only snapshot. */
  forceViolation?: boolean;
  signal?: AbortSignal;
}

export interface NewsroomAdapter {
  readonly id: string;
  readonly kind: 'mock' | 'http';
  load(request?: NewsroomRequest): Promise<NewsroomSnapshot>;
}

/** Simulated network latency so LOADING / skeleton states are reachable. */
const DEFAULT_DELAY_MS = 260;

function delay(ms: number, signal?: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    if (signal?.aborted) {
      reject(new DOMException('Aborted', 'AbortError'));
      return;
    }
    const timer = setTimeout(resolve, ms);
    signal?.addEventListener(
      'abort',
      () => {
        clearTimeout(timer);
        reject(new DOMException('Aborted', 'AbortError'));
      },
      { once: true },
    );
  });
}

function baseFor(scenario: NewsroomScenario): NewsroomSnapshot {
  switch (scenario) {
    case 'empty':
      return EMPTY_SNAPSHOT;
    case 'unavailable':
      return UNAVAILABLE_SNAPSHOT;
    case 'violation':
      return VIOLATION_SNAPSHOT;
    case 'error':
      return CALM_SNAPSHOT;
    case 'calm':
    default:
      return CALM_SNAPSHOT;
  }
}

/**
 * Recompute the market story counts from the story list. Disconnected markets
 * keep `storyCount: null` — we never print a number we cannot back with rows.
 */
function withMarketCounts(snapshot: NewsroomSnapshot): NewsroomSnapshot {
  return {
    ...snapshot,
    markets: snapshot.markets.map((market) =>
      market.connected
        ? { ...market, storyCount: snapshot.stories.filter((s) => s.market === market.id).length }
        : { ...market, storyCount: null },
    ),
  };
}

function withForcedDemo(snapshot: NewsroomSnapshot): NewsroomSnapshot {
  return {
    ...snapshot,
    stories: snapshot.stories.map((s) => ({ ...s, demo: true, status: 'DEMO' as const })),
    sources: snapshot.sources.map((s) =>
      s.status === 'REJECTED' ? s : { ...s, status: 'DEMO' as const },
    ),
    telemetry: { ...snapshot.telemetry, adapter: `${snapshot.telemetry.adapter}+demo` },
  };
}

function withForcedViolation(snapshot: NewsroomSnapshot): NewsroomSnapshot {
  return {
    ...snapshot,
    executionMode: 'LIVE',
    realTrading: true,
    telemetry: { ...snapshot.telemetry, adapter: `${snapshot.telemetry.adapter}+violation` },
  };
}

export const mockNewsroomAdapter: NewsroomAdapter = {
  id: 'mock:newsroom-fixtures',
  kind: 'mock',

  async load(request: NewsroomRequest = {}): Promise<NewsroomSnapshot> {
    const scenario = request.scenario ?? 'calm';
    await delay(DEFAULT_DELAY_MS, request.signal);

    if (scenario === 'error') {
      throw new Error('mock adapter: forced error (no data returned)');
    }

    let snapshot = withMarketCounts(baseFor(scenario));
    if (request.forceDemo) snapshot = withForcedDemo(snapshot);
    if (request.forceViolation) snapshot = withForcedViolation(snapshot);
    return snapshot;
  },
};

/** The adapter the page uses today. Replace this binding to go live. */
export const newsroomAdapter: NewsroomAdapter = mockNewsroomAdapter;
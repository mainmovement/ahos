/**
 * AHOS Newsroom — truth engine.
 *
 * Pure, dependency-free rules that decide what the UI is *allowed* to claim.
 * Everything here is unit-tested (`src/features/newsroom/lib/__tests__/truth.test.ts`):
 *
 *   1. UNKNOWN is never rendered green.
 *   2. DEMO rows are excluded from every total / verified count.
 *   3. VERIFIED requires two *independent* sources — one source is PARTIAL.
 *   4. A paper-only violation is `executionMode !== 'PAPER_ONLY' || realTrading`.
 */

import { toPersianDigits } from './format';
import type {
  ComponentState,
  CredibilityTier,
  MarketFocus,
  NewsSource,
  NewsroomSnapshot,
  Story,
  TruthStatus,
} from './types';

/* -------------------------------------------------------------------------- */
/* Vocabularies                                                                */
/* -------------------------------------------------------------------------- */

export const TRUTH_STATUSES = [
  'LIVE',
  'STALE',
  'UNKNOWN',
  'DEMO',
  'CONFLICT',
  'REJECTED',
] as const satisfies readonly TruthStatus[];

export const COMPONENT_STATES = [
  'LOADING',
  'EMPTY',
  'ERROR',
  'UNKNOWN',
  'UNAVAILABLE',
  'STALE',
  'PARTIAL',
  'LIVE',
  'SIMULATED',
  'PLANNED',
  'MISSING',
] as const satisfies readonly ComponentState[];

export const CREDIBILITY_TIERS = ['A', 'B', 'C', 'UNKNOWN'] as const satisfies readonly CredibilityTier[];

/** Markets the paper-only newsroom is allowed to gather. */
export const CONNECTED_MARKET_IDS = ['OIL', 'GOLD'] as const;

/* -------------------------------------------------------------------------- */
/* Tones                                                                       */
/* -------------------------------------------------------------------------- */

export type Tone =
  | 'live'
  | 'stale'
  | 'unknown'
  | 'demo'
  | 'conflict'
  | 'rejected'
  | 'planned'
  | 'partial'
  | 'unavailable'
  | 'missing'
  | 'error'
  | 'info'
  | 'neutral';

export interface ToneStyle {
  /** text / border / background utility classes (Tailwind v4). */
  text: string;
  border: string;
  bg: string;
  /** `true` for tones that must never be used on UNKNOWN data. */
  positive: boolean;
}

export const TONE: Record<Tone, ToneStyle> = {
  live: {
    text: 'text-ah-live',
    border: 'border-ah-live/40',
    bg: 'bg-ah-live/10',
    positive: true,
  },
  stale: {
    text: 'text-ah-stale',
    border: 'border-ah-stale/40',
    bg: 'bg-ah-stale/10',
    positive: false,
  },
  unknown: {
    text: 'text-ah-unknown',
    border: 'border-ah-unknown/40',
    bg: 'bg-ah-unknown/10',
    positive: false,
  },
  demo: {
    text: 'text-ah-gold',
    border: 'border-ah-gold/45',
    bg: 'bg-ah-gold/10',
    positive: false,
  },
  conflict: {
    text: 'text-ah-danger',
    border: 'border-ah-danger/45',
    bg: 'bg-ah-danger/10',
    positive: false,
  },
  rejected: {
    text: 'text-ah-danger/80',
    border: 'border-ah-danger/30',
    bg: 'bg-ah-danger/[0.05]',
    positive: false,
  },
  planned: {
    text: 'text-ah-text-faint',
    border: 'border-ah-line',
    bg: 'bg-transparent',
    positive: false,
  },
  partial: {
    text: 'text-ah-cyan',
    border: 'border-ah-cyan/35',
    bg: 'bg-ah-cyan/[0.08]',
    positive: false,
  },
  unavailable: {
    text: 'text-ah-text-faint',
    border: 'border-ah-line',
    bg: 'bg-ah-surface-2',
    positive: false,
  },
  missing: {
    text: 'text-ah-text-faint',
    border: 'border-dashed border-ah-line',
    bg: 'bg-transparent',
    positive: false,
  },
  error: {
    text: 'text-ah-danger',
    border: 'border-ah-danger/40',
    bg: 'bg-ah-danger/[0.07]',
    positive: false,
  },
  info: {
    text: 'text-ah-cyan',
    border: 'border-ah-cyan/30',
    bg: 'bg-ah-cyan/[0.06]',
    positive: false,
  },
  neutral: {
    text: 'text-ah-text-dim',
    border: 'border-ah-line',
    bg: 'bg-ah-surface-2',
    positive: false,
  },
};

export const TRUTH_TONE: Record<TruthStatus, Tone> = {
  LIVE: 'live',
  STALE: 'stale',
  UNKNOWN: 'unknown',
  DEMO: 'demo',
  CONFLICT: 'conflict',
  REJECTED: 'rejected',
};

export const COMPONENT_TONE: Record<ComponentState, Tone> = {
  LOADING: 'neutral',
  EMPTY: 'neutral',
  ERROR: 'error',
  UNKNOWN: 'unknown',
  UNAVAILABLE: 'unavailable',
  STALE: 'stale',
  PARTIAL: 'partial',
  LIVE: 'live',
  SIMULATED: 'demo',
  PLANNED: 'planned',
  MISSING: 'missing',
};

export const TRUTH_LABEL_FA: Record<TruthStatus, string> = {
  LIVE: 'زنده',
  STALE: 'کهنه',
  UNKNOWN: 'نامعلوم',
  DEMO: 'دمو',
  CONFLICT: 'تعارض',
  REJECTED: 'رد شده',
};

export const TRUTH_LABEL_EN: Record<TruthStatus, string> = {
  LIVE: 'LIVE',
  STALE: 'STALE',
  UNKNOWN: 'UNKNOWN',
  DEMO: 'DEMO',
  CONFLICT: 'CONFLICT',
  REJECTED: 'REJECTED',
};

export const COMPONENT_LABEL_EN: Record<ComponentState, string> = {
  LOADING: 'LOADING',
  EMPTY: 'EMPTY',
  ERROR: 'ERROR',
  UNKNOWN: 'UNKNOWN',
  UNAVAILABLE: 'UNAVAILABLE',
  STALE: 'STALE',
  PARTIAL: 'PARTIAL',
  LIVE: 'LIVE',
  SIMULATED: 'SIMULATED',
  PLANNED: 'PLANNED',
  MISSING: 'MISSING',
};

export const COMPONENT_LABEL_FA: Record<ComponentState, string> = {
  LOADING: 'در حال بارگذاری',
  EMPTY: 'خالی',
  ERROR: 'خطا',
  UNKNOWN: 'نامعلوم',
  UNAVAILABLE: 'در دسترس نیست',
  STALE: 'کهنه',
  PARTIAL: 'ناقص',
  LIVE: 'زنده',
  SIMULATED: 'شبیه‌سازی',
  PLANNED: 'برنامه‌ریزی‌شده',
  MISSING: 'گم‌شده',
};

/* -------------------------------------------------------------------------- */
/* Two-source rule                                                             */
/* -------------------------------------------------------------------------- */

/**
 * A source counts towards verification only when it is currently live and has
 * actually been read (no timestamp ⇒ UNKNOWN ⇒ does not count).
 */
export function isCorroboratingSource(source: NewsSource): boolean {
  if (source.status !== 'LIVE') return false;
  if (!source.lastReadAt) return false;
  if (source.credibility === 'UNKNOWN') return false;
  return true;
}

/**
 * Number of *independent* corroborating sources. Sources sharing an
 * `independenceGroup` (same wire / syndicated copy / same owner) count once.
 */
export function independentSourceCount(sources: readonly NewsSource[]): number {
  const groups = new Set<string>();
  for (const source of sources) {
    if (!isCorroboratingSource(source)) continue;
    groups.add(source.independenceGroup || source.id);
  }
  return groups.size;
}

export type VerificationLevel = 'VERIFIED' | 'PARTIAL' | 'UNKNOWN' | 'DEMO' | 'CONFLICT';

export const VERIFICATION_LABEL_EN: Record<VerificationLevel, string> = {
  VERIFIED: 'VERIFIED',
  PARTIAL: 'PARTIAL',
  UNKNOWN: 'UNKNOWN',
  DEMO: 'DEMO',
  CONFLICT: 'CONFLICT',
};

export const VERIFICATION_LABEL_FA: Record<VerificationLevel, string> = {
  VERIFIED: 'تأیید‌شده',
  PARTIAL: 'ناقص',
  UNKNOWN: 'نامعلوم',
  DEMO: 'دمو',
  CONFLICT: 'تعارض',
};

export const VERIFICATION_TONE: Record<VerificationLevel, Tone> = {
  VERIFIED: 'live',
  PARTIAL: 'partial',
  UNKNOWN: 'unknown',
  DEMO: 'demo',
  CONFLICT: 'conflict',
};

export interface VerificationInput {
  story: Story;
  sources: readonly NewsSource[];
  hasConflict: boolean;
}

/**
 * The one and only place where VERIFIED is decided.
 *
 * Precedence (never overridden by the UI):
 *   DEMO      — the story or any of its sources is fixture data.
 *   CONFLICT  — at least one open conflict references the story.
 *   VERIFIED  — ≥ 2 independent, live, read, tiered sources.
 *   PARTIAL   — exactly 1 corroborating source (or only untiered ones).
 *   UNKNOWN   — nothing usable.
 */
export function deriveStoryVerification({ story, sources, hasConflict }: VerificationInput): VerificationLevel {
  if (story.status === 'DEMO' || story.demo || sources.some((s) => s.status === 'DEMO')) {
    return 'DEMO';
  }
  if (hasConflict || story.status === 'CONFLICT') return 'CONFLICT';
  if (story.status === 'REJECTED') return 'UNKNOWN';

  const independent = independentSourceCount(sources);
  if (independent >= 2) return 'VERIFIED';
  if (independent === 1) return 'PARTIAL';
  return 'UNKNOWN';
}

/* -------------------------------------------------------------------------- */
/* Aggregates — DEMO is always excluded                                        */
/* -------------------------------------------------------------------------- */

export function isDemoStory(story: Story, sources: readonly NewsSource[]): boolean {
  return story.demo || story.status === 'DEMO' || sources.some((s) => s.status === 'DEMO');
}

export interface NewsroomTotals {
  /** All stories, including DEMO (used only for the DEMO counter). */
  total: number;
  /** Stories that passed the two-source rule. DEMO never lands here. */
  verified: number;
  partial: number;
  unknown: number;
  conflict: number;
  /** Fixture rows — reported separately, never inside `verified`. */
  demo: number;
}

export function computeTotals(snapshot: NewsroomSnapshot): NewsroomTotals {
  const byId = new Map(snapshot.sources.map((s) => [s.id, s]));
  const conflictStoryIds = new Set(snapshot.conflicts.map((c) => c.storyId));

  const totals: NewsroomTotals = {
    total: snapshot.stories.length,
    verified: 0,
    partial: 0,
    unknown: 0,
    conflict: 0,
    demo: 0,
  };

  for (const story of snapshot.stories) {
    const sources = story.sourceIds
      .map((id) => byId.get(id))
      .filter((s): s is NewsSource => s !== undefined);

    const level = deriveStoryVerification({
      story,
      sources,
      hasConflict: conflictStoryIds.has(story.id) || story.conflictId !== null,
    });

    switch (level) {
      case 'VERIFIED':
        totals.verified += 1;
        break;
      case 'PARTIAL':
        totals.partial += 1;
        break;
      case 'DEMO':
        totals.demo += 1;
        break;
      case 'CONFLICT':
        totals.conflict += 1;
        break;
      case 'UNKNOWN':
      default:
        totals.unknown += 1;
        break;
    }
  }

  return totals;
}

/* -------------------------------------------------------------------------- */
/* Paper-only guard                                                            */
/* -------------------------------------------------------------------------- */

/**
 * A VIOLATION bar is shown whenever the snapshot is not unambiguously
 * paper-only. `executionMode` must be exactly `PAPER_ONLY` and `realTrading`
 * must be false — anything else (including UNKNOWN) is a violation.
 */
export function isPaperOnlyViolation(snapshot: Pick<NewsroomSnapshot, 'executionMode' | 'realTrading'>): boolean {
  return snapshot.realTrading === true || snapshot.executionMode !== 'PAPER_ONLY';
}

export function isPaperOnly(snapshot: Pick<NewsroomSnapshot, 'executionMode' | 'realTrading'>): boolean {
  return !isPaperOnlyViolation(snapshot);
}

/* -------------------------------------------------------------------------- */
/* Market focus                                                                */
/* -------------------------------------------------------------------------- */

/** Oil & Gold only. Everything else is rendered «متصل نیست» / PLANNED. */
export function isConnectedMarket(market: MarketFocus): boolean {
  return market.connected && CONNECTED_MARKET_IDS.includes(market.id as (typeof CONNECTED_MARKET_IDS)[number]);
}

export function disconnectedMarkets(markets: readonly MarketFocus[]): MarketFocus[] {
  return markets.filter((m) => !isConnectedMarket(m));
}

export function connectedMarkets(markets: readonly MarketFocus[]): MarketFocus[] {
  return markets.filter(isConnectedMarket);
}

/* -------------------------------------------------------------------------- */
/* Misc truth helpers                                                          */
/* -------------------------------------------------------------------------- */

/** `null`, `undefined`, `''` and `'—'` are all missing values. */
export function isMissingValue(value: string | number | null | undefined): boolean {
  if (value === null || value === undefined) return true;
  if (typeof value === 'number') return !Number.isFinite(value);
  return value.trim() === '' || value.trim() === '—';
}

/** Never fabricate a zero: unknown numbers render as «—». */
export function renderCount(value: number | null | undefined): string {
  return value === null || value === undefined || !Number.isFinite(value) ? '—' : toPersianDigits(value);
}

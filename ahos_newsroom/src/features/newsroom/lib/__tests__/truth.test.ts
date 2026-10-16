import { describe, expect, it } from 'vitest';

import {
  COMPONENT_STATES,
  COMPONENT_TONE,
  TONE,
  TRUTH_LABEL_EN,
  TRUTH_STATUSES,
  TRUTH_TONE,
  computeTotals,
  deriveStoryVerification,
  disconnectedMarkets,
  independentSourceCount,
  isCorroboratingSource,
  isMissingValue,
  isPaperOnly,
  isPaperOnlyViolation,
  renderCount,
} from '../truth';
import { CALM_SNAPSHOT, FIXTURE_SOURCES, mockNewsroomAdapter, VIOLATION_SNAPSHOT } from '@/mock/newsroom';
import type { NewsSource, Story } from '../types';

function source(overrides: Partial<NewsSource> & { id: string }): NewsSource {
  return {
    nameFa: 'منبع',
    urlPlaceholder: 'https://example.invalid/x',
    credibility: 'A',
    status: 'LIVE',
    lastReadAt: '2026-10-16T11:58:00.000+03:30',
    independenceGroup: `grp-${overrides.id}`,
    noteFa: null,
    ...overrides,
  };
}

function story(overrides: Partial<Story> & { id: string }): Story {
  return {
    headlineFa: 'تیتر',
    headlineEn: null,
    market: 'OIL',
    publishedAt: '2026-10-16T11:52:00.000+03:30',
    claimStrength: 'STRONG',
    sourceIds: [],
    marketImpactNoteFa: null,
    demo: false,
    status: 'LIVE',
    conflictId: null,
    ...overrides,
  };
}

describe('truth vocabulary', () => {
  it('contains exactly the six allowed data statuses', () => {
    expect([...TRUTH_STATUSES].sort()).toEqual(
      ['CONFLICT', 'DEMO', 'LIVE', 'REJECTED', 'STALE', 'UNKNOWN'].sort(),
    );
  });

  it('keeps presentation-only states out of the data vocabulary', () => {
    const componentOnly: (typeof COMPONENT_STATES)[number][] = [
      'LOADING',
      'EMPTY',
      'ERROR',
      'UNAVAILABLE',
      'PARTIAL',
      'SIMULATED',
      'PLANNED',
      'MISSING',
    ];
    for (const state of componentOnly) {
      expect(TRUTH_STATUSES).not.toContain(state as never);
      expect(COMPONENT_STATES).toContain(state);
    }
    // The three shared words describe the same idea in both vocabularies and
    // must resolve to the same tone — a component may never upgrade UNKNOWN.
    for (const shared of ['LIVE', 'STALE', 'UNKNOWN'] as const) {
      expect(COMPONENT_TONE[shared]).toBe(TRUTH_TONE[shared]);
    }
  });

  it('labels every status in English so the code never disappears', () => {
    for (const status of TRUTH_STATUSES) {
      expect(TRUTH_LABEL_EN[status]).toBe(status);
    }
  });
});

describe('UNKNOWN is never green', () => {
  it('maps UNKNOWN to the grey tone (not live/positive)', () => {
    expect(TRUTH_TONE.UNKNOWN).toBe('unknown');
    const tone = TONE[TRUTH_TONE.UNKNOWN];
    expect(tone.positive).toBe(false);
    expect(tone.text).toBe('text-ah-unknown');
    expect(tone.text).not.toMatch(/live|green/i);
    expect(tone.bg).not.toMatch(/live|green/i);
  });

  it('maps every non-LIVE data status away from the live tone', () => {
    for (const status of TRUTH_STATUSES) {
      if (status === 'LIVE') continue;
      expect(TRUTH_TONE[status]).not.toBe('live');
    }
  });

  it('never lets a component state promote UNKNOWN into a positive tone', () => {
    expect(COMPONENT_TONE.UNKNOWN).toBe('unknown');
    expect(TONE[COMPONENT_TONE.UNKNOWN].positive).toBe(false);
    expect(TONE[COMPONENT_TONE.PLANNED].positive).toBe(false);
    expect(TONE[COMPONENT_TONE.UNAVAILABLE].positive).toBe(false);
  });

  it('treats a source without a read timestamp as UNKNOWN, never as evidence', () => {
    expect(isCorroboratingSource(source({ id: 'a', lastReadAt: null }))).toBe(false);
    expect(isCorroboratingSource(source({ id: 'b', status: 'UNKNOWN' }))).toBe(false);
    expect(isCorroboratingSource(source({ id: 'c', credibility: 'UNKNOWN' }))).toBe(false);
    expect(isCorroboratingSource(source({ id: 'd' }))).toBe(true);
  });
});

describe('two-source rule for VERIFIED', () => {
  it('requires two independent, live, tiered sources', () => {
    const two = [
      source({ id: 'x', independenceGroup: 'grp-a' }),
      source({ id: 'y', independenceGroup: 'grp-b' }),
    ];
    expect(deriveStoryVerification({ story: story({ id: 's' }), sources: two, hasConflict: false })).toBe(
      'VERIFIED',
    );
  });

  it('is only PARTIAL with a single source', () => {
    const one = [source({ id: 'x' })];
    expect(deriveStoryVerification({ story: story({ id: 's' }), sources: one, hasConflict: false })).toBe(
      'PARTIAL',
    );
  });

  it('is UNKNOWN with no usable source', () => {
    expect(deriveStoryVerification({ story: story({ id: 's' }), sources: [], hasConflict: false })).toBe(
      'UNKNOWN',
    );
  });

  it('counts syndicated copies (same independence group) as ONE source', () => {
    const syndicated = [
      source({ id: 'x', independenceGroup: 'grp-reuters' }),
      source({ id: 'y', independenceGroup: 'grp-reuters' }),
    ];
    expect(independentSourceCount(syndicated)).toBe(1);
    expect(deriveStoryVerification({ story: story({ id: 's' }), sources: syndicated, hasConflict: false })).toBe(
      'PARTIAL',
    );
  });

  it('does not count STALE or DEMO sources towards verification', () => {
    const stalePlusLive = [
      source({ id: 'x', status: 'STALE' }),
      source({ id: 'y', status: 'DEMO' }),
    ];
    expect(independentSourceCount(stalePlusLive)).toBe(0);
    expect(
      deriveStoryVerification({ story: story({ id: 's' }), sources: stalePlusLive, hasConflict: false }),
    ).toBe('DEMO');
  });

  it('never returns VERIFIED when a conflict is open, even with two sources', () => {
    const two = [
      source({ id: 'x', independenceGroup: 'grp-a' }),
      source({ id: 'y', independenceGroup: 'grp-b' }),
    ];
    expect(deriveStoryVerification({ story: story({ id: 's' }), sources: two, hasConflict: true })).toBe(
      'CONFLICT',
    );
  });

  it('treats fixture DEMO rows as DEMO regardless of source count', () => {
    const two = [
      source({ id: 'x', independenceGroup: 'grp-a' }),
      source({ id: 'y', independenceGroup: 'grp-b' }),
    ];
    expect(
      deriveStoryVerification({ story: story({ id: 's', demo: true }), sources: two, hasConflict: false }),
    ).toBe('DEMO');
  });
});

describe('DEMO is excluded from every total', () => {
  it('counts the calm fixture set exactly', () => {
    const totals = computeTotals(CALM_SNAPSHOT);
    expect(totals.total).toBe(10);
    expect(totals.verified).toBe(3);
    expect(totals.partial).toBe(2);
    expect(totals.conflict).toBe(2);
    expect(totals.unknown).toBe(2);
    expect(totals.demo).toBe(1);
  });

  it('never puts a DEMO story in the verified bucket', () => {
    const totals = computeTotals(CALM_SNAPSHOT);
    const verifiedSum = totals.verified + totals.partial + totals.unknown + totals.conflict + totals.demo;
    expect(verifiedSum).toBe(totals.total);
  });

  it('keeps the verified count unchanged when DEMO rows are added', () => {
    const before = computeTotals(CALM_SNAPSHOT);
    const withExtraDemo: typeof CALM_SNAPSHOT = {
      ...CALM_SNAPSHOT,
      stories: [
        ...CALM_SNAPSHOT.stories,
        story({ id: 'nws-demo-0002', demo: true, status: 'DEMO', sourceIds: ['src-simulator'] }),
        story({ id: 'nws-demo-0003', demo: true, status: 'DEMO', sourceIds: ['src-simulator'] }),
      ],
    };
    const after = computeTotals(withExtraDemo);
    expect(after.verified).toBe(before.verified);
    expect(after.partial).toBe(before.partial);
    expect(after.conflict).toBe(before.conflict);
    expect(after.demo).toBe(before.demo + 2);
  });

  it('drops the verified count to zero when every row is forced to DEMO', () => {
    const allDemo: typeof CALM_SNAPSHOT = {
      ...CALM_SNAPSHOT,
      stories: CALM_SNAPSHOT.stories.map((s) => ({ ...s, demo: true, status: 'DEMO' as const })),
    };
    const totals = computeTotals(allDemo);
    expect(totals.verified).toBe(0);
    expect(totals.demo).toBe(CALM_SNAPSHOT.stories.length);
  });
});

describe('paper-only guard', () => {
  it('is clean for PAPER_ONLY + realTrading false', () => {
    expect(isPaperOnlyViolation(CALM_SNAPSHOT)).toBe(false);
    expect(isPaperOnly(CALM_SNAPSHOT)).toBe(true);
  });

  it('violates when realTrading is true', () => {
    expect(isPaperOnlyViolation({ executionMode: 'PAPER_ONLY', realTrading: true })).toBe(true);
  });

  it('violates when executionMode is anything other than PAPER_ONLY', () => {
    expect(isPaperOnlyViolation({ executionMode: 'LIVE', realTrading: false })).toBe(true);
    expect(isPaperOnlyViolation({ executionMode: 'PAPER', realTrading: false })).toBe(true);
    expect(isPaperOnlyViolation({ executionMode: 'SHADOW', realTrading: false })).toBe(true);
    expect(isPaperOnlyViolation({ executionMode: 'UNKNOWN', realTrading: false })).toBe(true);
  });

  it('flags the shipped violation fixture', () => {
    expect(isPaperOnlyViolation(VIOLATION_SNAPSHOT)).toBe(true);
  });
});

describe('market focus: oil & gold only', () => {
  it('leaves crypto and equities disconnected', () => {
    const off = disconnectedMarkets(CALM_SNAPSHOT.markets).map((m) => m.id);
    expect(off).toEqual(['CRYPTO', 'EQUITIES']);
  });

  it('never invents a story count for a disconnected market', () => {
    for (const market of disconnectedMarkets(CALM_SNAPSHOT.markets)) {
      expect(market.storyCount).toBeNull();
      expect(market.connected).toBe(false);
      expect(renderCount(market.storyCount)).toBe('—');
    }
  });

  it('derives connected counts from real rows only', async () => {
    const snapshot = await mockNewsroomAdapter.load({ scenario: 'calm' });
    const byId = new Map(snapshot.markets.map((m) => [m.id, m]));
    expect(byId.get('OIL')?.storyCount).toBe(snapshot.stories.filter((s) => s.market === 'OIL').length);
    expect(byId.get('GOLD')?.storyCount).toBe(snapshot.stories.filter((s) => s.market === 'GOLD').length);
  });

  it('never fabricates counts for disconnected markets, even after loading', async () => {
    const snapshot = await mockNewsroomAdapter.load({ scenario: 'calm' });
    for (const market of disconnectedMarkets(snapshot.markets)) {
      expect(market.storyCount).toBeNull();
    }
  });
});

describe('missing values', () => {
  it('detects missing values instead of defaulting to zero', () => {
    expect(isMissingValue(null)).toBe(true);
    expect(isMissingValue(undefined)).toBe(true);
    expect(isMissingValue('')).toBe(true);
    expect(isMissingValue('—')).toBe(true);
    expect(isMissingValue(Number.NaN)).toBe(true);
    expect(isMissingValue(0)).toBe(false);
  });

  it('renders unknown counts as «—» and never as 0', () => {
    expect(renderCount(null)).toBe('—');
    expect(renderCount(undefined)).toBe('—');
    expect(renderCount(0)).toBe('۰');
    expect(renderCount(12)).toBe('۱۲');
  });

  it('ships at least one source with an UNKNOWN read and one REJECTED source', () => {
    expect(FIXTURE_SOURCES.some((s) => s.status === 'UNKNOWN' && s.lastReadAt === null)).toBe(true);
    expect(FIXTURE_SOURCES.some((s) => s.status === 'REJECTED')).toBe(true);
  });
});

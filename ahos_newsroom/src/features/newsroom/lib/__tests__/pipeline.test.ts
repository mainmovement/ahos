import { describe, expect, it } from 'vitest';

import { currentStageIndex, derivePipeline, PIPELINE_ORDER } from '../pipeline';
import { CALM_SNAPSHOT, FIXTURE_SOURCES } from '@/mock/newsroom';
import { buildStoryView } from '../selectors';
import type { NewsSource, Story } from '../types';

const src = (id: string, overrides: Partial<NewsSource> = {}): NewsSource => ({
  id,
  nameFa: id,
  urlPlaceholder: 'https://example.invalid/x',
  credibility: 'A',
  status: 'LIVE',
  lastReadAt: '2026-10-16T11:58:00.000+03:30',
  independenceGroup: `grp-${id}`,
  noteFa: null,
  ...overrides,
});

const story = (overrides: Partial<Story> = {}): Story => ({
  id: 'nws-test',
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
});

describe('verification pipeline', () => {
  it('always has the five canonical stages in order', () => {
    const stages = derivePipeline({ story: story(), sources: [], hasConflict: false });
    expect(stages.map((s) => s.id)).toEqual([...PIPELINE_ORDER]);
  });

  it('never marks JUDGE_HANDOFF as complete — handoff is a manual, read-only act', () => {
    const two = [src('a'), src('b')];
    const stages = derivePipeline({ story: story(), sources: two, hasConflict: false });
    const handoff = stages.find((s) => s.id === 'JUDGE_HANDOFF');
    expect(handoff?.state).toBe('PLANNED');
    expect(handoff?.completedAt).toBeNull();
  });

  it('leaves stages PLANNED or UNKNOWN until their evidence exists', () => {
    const stages = derivePipeline({ story: story(), sources: [], hasConflict: false });
    expect(stages.find((s) => s.id === 'TWO_SOURCE_CHECK')?.state).toBe('PLANNED');
    expect(stages.find((s) => s.id === 'CONFLICT_SCAN')?.state).toBe('PLANNED');
    expect(stages.every((s) => s.state !== 'DONE' || s.completedAt !== null)).toBe(true);
  });

  it('marks TWO_SOURCE_CHECK as CURRENT when only one source is attached', () => {
    const stages = derivePipeline({ story: story(), sources: [src('a')], hasConflict: false });
    const check = stages.find((s) => s.id === 'TWO_SOURCE_CHECK');
    expect(check?.state).toBe('CURRENT');
    expect(check?.completedAt).toBeNull();
    expect(currentStageIndex(stages)).toBe(2);
  });

  it('holds CONFLICT_SCAN at CURRENT while a conflict is open', () => {
    const stages = derivePipeline({ story: story(), sources: [src('a'), src('b')], hasConflict: true });
    expect(stages.find((s) => s.id === 'CONFLICT_SCAN')?.state).toBe('CURRENT');
    expect(currentStageIndex(stages)).toBe(3);
  });

  it('never claims a stage ran for a DEMO story', () => {
    const stages = derivePipeline({
      story: story({ demo: true }),
      sources: [src('a'), src('b')],
      hasConflict: false,
    });
    expect(stages.find((s) => s.id === 'TWO_SOURCE_CHECK')?.state).toBe('UNKNOWN');
    expect(stages.find((s) => s.id === 'CONFLICT_SCAN')?.state).toBe('UNKNOWN');
  });

  it('never invents timestamps when the story has no published time', () => {
    const stages = derivePipeline({ story: story({ publishedAt: null }), sources: [], hasConflict: false });
    expect(stages[0]?.state).toBe('UNKNOWN');
    expect(stages[0]?.completedAt).toBeNull();
  });

  it('highlights exactly one current stage for the fixture conflict story', () => {
    const conflictStory = CALM_SNAPSHOT.stories.find((s) => s.id === 'nws-oil-0143');
    expect(conflictStory).toBeDefined();
    const view = buildStoryView(CALM_SNAPSHOT, conflictStory!);
    const currents = view.pipeline.filter((s) => s.state === 'CURRENT');
    expect(currents).toHaveLength(1);
    expect(currents[0]?.id).toBe('CONFLICT_SCAN');
  });

  it('resolves every fixture source id referenced by stories', () => {
    const ids = new Set(FIXTURE_SOURCES.map((s) => s.id));
    for (const s of CALM_SNAPSHOT.stories) {
      for (const sourceId of s.sourceIds) {
        expect(ids.has(sourceId)).toBe(true);
      }
    }
  });
});

/**
 * Read-only selectors over a `NewsroomSnapshot`.
 * Pure functions — no mutation, no fetching, no fabrication.
 */

import { derivePipeline } from './pipeline';
import { deriveStoryVerification, independentSourceCount, type VerificationLevel } from './truth';
import type {
  Conflict,
  NewsSource,
  NewsroomSnapshot,
  PipelineStage,
  Story,
} from './types';

export function sourceById(snapshot: NewsroomSnapshot, id: string): NewsSource | undefined {
  return snapshot.sources.find((s) => s.id === id);
}

export function storySources(snapshot: NewsroomSnapshot, story: Story): NewsSource[] {
  return story.sourceIds
    .map((id) => sourceById(snapshot, id))
    .filter((s): s is NewsSource => s !== undefined);
}

export function storyConflict(snapshot: NewsroomSnapshot, story: Story): Conflict | null {
  if (story.conflictId) {
    const exact = snapshot.conflicts.find((c) => c.id === story.conflictId);
    if (exact) return exact;
  }
  return snapshot.conflicts.find((c) => c.storyId === story.id) ?? null;
}

export function conflictStory(snapshot: NewsroomSnapshot, conflict: Conflict): Story | null {
  return snapshot.stories.find((s) => s.id === conflict.storyId) ?? null;
}

export interface StoryView {
  story: Story;
  sources: NewsSource[];
  conflict: Conflict | null;
  verification: VerificationLevel;
  independentSources: number;
  pipeline: PipelineStage[];
  totalSources: number;
}

export function buildStoryView(snapshot: NewsroomSnapshot, story: Story): StoryView {
  const sources = storySources(snapshot, story);
  const conflict = storyConflict(snapshot, story);
  return {
    story,
    sources,
    conflict,
    verification: deriveStoryVerification({ story, sources, hasConflict: conflict !== null }),
    independentSources: independentSourceCount(sources),
    pipeline: derivePipeline({ story, sources, hasConflict: conflict !== null }),
    totalSources: sources.length,
  };
}

export type StoryFilterId = 'ALL' | 'OIL' | 'GOLD' | 'CONFLICT' | 'DEMO';

export function filterStories(snapshot: NewsroomSnapshot, filter: StoryFilterId): Story[] {
  switch (filter) {
    case 'ALL':
      return snapshot.stories;
    case 'OIL':
      return snapshot.stories.filter((s) => s.market === 'OIL');
    case 'GOLD':
      return snapshot.stories.filter((s) => s.market === 'GOLD');
    case 'CONFLICT':
      return snapshot.stories.filter((s) => storyConflict(snapshot, s) !== null);
    case 'DEMO':
      return snapshot.stories.filter(
        (s) => s.demo || s.status === 'DEMO' || storySources(snapshot, s).some((src) => src.status === 'DEMO'),
      );
    default:
      return snapshot.stories;
  }
}

/** Evidence id handed to the Judge queue — deterministic for a given story. */
export function evidenceId(story: Story): string {
  return `evd::${story.id}::${story.sourceIds.length}src`;
}
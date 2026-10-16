/**
 * Mock-source normalisation: a snapshot that comes from the mock adapter is
 * fixture data, so nothing in it may present itself as LIVE / VERIFIED.
 * LIVE (and any story that leans on a LIVE source) becomes DEMO, which is
 * excluded from every verified total. Other statuses are left untouched.
 */

import type { NewsroomSnapshot, TruthStatus } from "./types";

const demote = (status: TruthStatus): TruthStatus => (status === "LIVE" ? "DEMO" : status);

export function demoteLiveOnMock(snapshot: NewsroomSnapshot): NewsroomSnapshot {
  const sources = snapshot.sources.map((s) => ({ ...s, status: demote(s.status) }));
  const byId = new Map(sources.map((s) => [s.id, s]));
  const stories = snapshot.stories.map((story) => {
    const leansOnDemo =
      story.status === "LIVE" || story.sourceIds.some((id) => byId.get(id)?.status === "DEMO");
    return leansOnDemo ? { ...story, demo: true, status: "DEMO" as const } : story;
  });
  const reporters = snapshot.reporters.map((r) => ({ ...r, status: demote(r.status) }));
  return {
    ...snapshot,
    sources,
    stories,
    reporters,
    telemetry: { ...snapshot.telemetry, demoCount: stories.filter((s) => s.demo).length },
  };
}

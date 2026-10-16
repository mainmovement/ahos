"use client";
import { tr } from "@/src/lib/i18n";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
  SCENARIO_LABELS,
  type OpenTarget,
  type QualityTier,
  type WhiteHatsScenario,
} from "@/src/mock/white_hats/scenarios";
import {
  useWhiteHatsSnapshot,
  type SnapshotPhase,
} from "./hooks/useWhiteHatsSnapshot";
import type { PanelBodyState } from "./types";
import { PageBar } from "./components/PageBar";
import { PaperOnlyGuard } from "./components/PaperOnlyGuard";
import { TelemetryStrip } from "./components/TelemetryStrip";
import { DecisionQueue } from "./components/DecisionQueue";
import { InspectorsPanel } from "./components/InspectorsPanel";
import { BreakerCard } from "./components/BreakerCard";
import { CanaryTile } from "./components/CanaryTile";
import { FindingsLog } from "./components/FindingsLog";
import { ChallengeTimeline } from "./components/ChallengeTimeline";
import {
  EvidenceDrawer,
  type DrawerContent,
} from "./components/EvidenceDrawer";

/**
 * White Hats & Judge — کلاه‌سفیدها و ناظر.
 * Read-only audit screen: the independent inspection group that challenges
 * every decision before it can become a paper trade. No execution controls
 * exist anywhere in this tree — by construction, not by convention.
 */
export function WhiteHatsScreen({
  scenario = "calm",
  tier = "t1",
  openTarget = null,
}: {
  scenario?: WhiteHatsScenario;
  tier?: QualityTier;
  openTarget?: OpenTarget;
} = {}) {
  const router = useRouter();
  const [pickedDecisionId, setSelectedDecisionId] = useState<string | null>(null);
  // undefined = follow the ?open= deep link; null = user closed it; value = user opened it.
  const [drawerOverride, setDrawer] = useState<DrawerContent | undefined>(undefined);

  const phase = useWhiteHatsSnapshot(scenario);
  const snapshot = phase.phase === "ready" ? phase.snapshot : null;
  // DEMO is derived from the data, never hard-coded.
  const demo = snapshot?.demo ?? false;

  // Default selection: first non-demo decision (DEMO rows never lead totals).
  const selectedDecisionId =
    pickedDecisionId ??
    (snapshot ? (snapshot.decisions.find((d) => !d.demo) ?? snapshot.decisions[0])?.id ?? null : null);

  // Deep-link ?open=finding:<id> | evidence:<id>
  let deepDrawer: DrawerContent = null;
  if (snapshot && openTarget) {
    if (openTarget.kind === "finding") {
      const finding = snapshot.findings.find((f) => f.id === openTarget.id);
      if (finding) {
        deepDrawer = {
          kind: "finding",
          finding,
          inspectorTitle:
            snapshot.inspectors.find((i) => i.id === finding.inspectorId)?.title ?? finding.inspectorId,
        };
      }
    } else {
      const evidence = snapshot.evidence[openTarget.id];
      if (evidence) deepDrawer = { kind: "evidence", evidence };
    }
  }
  const drawer: DrawerContent = drawerOverride !== undefined ? drawerOverride : deepDrawer;

  const onScenarioChange = (next: WhiteHatsScenario) => {
    router.push(`/arena/white-hats?scenario=${next}${tier === "t0" ? "&tier=t0" : ""}`);
  };

  const inspectorTitle = (id: string) =>
    snapshot?.inspectors.find((i) => i.id === id)?.title ?? id;

  const selectedDecision =
    snapshot?.decisions.find((d) => d.id === selectedDecisionId) ?? null;
  const timelineEvents = useMemo(
    () => (snapshot && selectedDecisionId ? (snapshot.timelines[selectedDecisionId] ?? []) : []),
    [snapshot, selectedDecisionId],
  );

  const baseState = (emptyMessage: string, isEmpty: boolean): PanelBodyState => {
    if (phase.phase === "loading") return { kind: "loading" };
    if (phase.phase === "unavailable")
      return { kind: "unavailable", message: phase.message };
    return isEmpty ? { kind: "empty", message: emptyMessage } : { kind: "content" };
  };

  const timelineState: PanelBodyState =
    phase.phase === "loading"
      ? { kind: "loading" }
      : phase.phase === "unavailable"
        ? { kind: "unavailable", message: phase.message }
        : !snapshot || snapshot.decisions.length === 0 || !selectedDecision
          ? {
              kind: "empty",
              message: tr("fa", "whiteHats.ui.WhiteHatsScreen_1"),
            }
          : { kind: "content" };

  return (
    <div
      data-tier={tier}
      data-scenario={scenario}
      data-testid="white-hats-root"
      className="wh-root relative flex flex-col gap-3.5"
    >
      <PageBar
        scenario={scenario}
        freshness={snapshot ? snapshot.freshness : phase.phase === "unavailable" ? "UNAVAILABLE" : "LOADING"}
        demo={demo}
        onScenarioChange={onScenarioChange}
        onReload={phase.reload}
      />

      {/* Red VIOLATION bar when the mock claims LIVE / real trading. */}
      {snapshot && <PaperOnlyGuard snapshot={snapshot} />}

      <main className="relative z-10 flex w-full flex-1 flex-col gap-3.5 lg:flex-row">
        {/* RTL: the first column is the right dock. */}
        <div className="flex w-full shrink-0 flex-col gap-3.5 lg:w-[312px]">
          <InspectorsPanel
            inspectors={snapshot?.inspectors ?? []}
            state={baseState(tr("fa", "whiteHats.ui.WhiteHatsScreen_2"), (snapshot?.inspectors.length ?? 0) === 0)}
            demo={demo}
          />
          <BreakerCard
            breaker={
              snapshot?.breaker ?? {
                state: "UNKNOWN",
                updatedAt: null,
                limits: [],
              }
            }
            state={baseState(tr("fa", "whiteHats.ui.WhiteHatsScreen_3"), false)}
            demo={demo}
          />
          <CanaryTile
            canary={snapshot?.canary ?? null}
            state={baseState(tr("fa", "whiteHats.ui.WhiteHatsScreen_4"), false)}
            demo={demo}
          />
        </div>

        <div className="flex min-w-0 flex-1 flex-col gap-3.5">
          <DecisionQueue
            decisions={snapshot?.decisions ?? []}
            selectedId={selectedDecisionId}
            onSelect={setSelectedDecisionId}
            state={baseState(
              tr("fa", "whiteHats.ui.WhiteHatsScreen_5"),
              (snapshot?.decisions.length ?? 0) === 0,
            )}
            demo={demo}
          />

          <div className="grid grid-cols-1 gap-3.5 xl:grid-cols-[minmax(0,1fr)_360px]">
            <FindingsLog
              findings={snapshot?.findings ?? []}
              inspectors={snapshot?.inspectors ?? []}
              state={baseState(
                tr("fa", "whiteHats.ui.WhiteHatsScreen_6"),
                (snapshot?.findings.length ?? 0) === 0,
              )}
              demo={demo}
              onOpenFinding={(id) => {
                const finding = snapshot?.findings.find((f) => f.id === id);
                if (finding)
                  setDrawer({
                    kind: "finding",
                    finding,
                    inspectorTitle: inspectorTitle(finding.inspectorId),
                  });
              }}
            />
            <ChallengeTimeline
              decision={selectedDecision}
              events={timelineEvents}
              state={timelineState}
              demo={demo}
              onOpenEvidence={(id) => {
                const evidence = snapshot?.evidence[id];
                if (evidence) setDrawer({ kind: "evidence", evidence });
              }}
            />
          </div>
        </div>
      </main>

      <TelemetryStrip phase={phase} />

      <EvidenceDrawer
        content={drawer}
        onClose={() => setDrawer(null)}
        onOpenEvidence={(id) => {
          const evidence = snapshot?.evidence[id];
          if (evidence) setDrawer({ kind: "evidence", evidence });
        }}
      />

      {/* Accessible label for the demo scenario, for tests and screen readers. */}
      <span className="sr-only" data-testid="scenario-label">
        {SCENARIO_LABELS[scenario]}
      </span>
    </div>
  );
}

export type { SnapshotPhase };

"use client";

import { useEffect, useMemo, useState } from "react";
import {
  parseOpenTarget,
  parseScenario,
  parseTier,
  SCENARIO_LABELS,
  type OpenTarget,
  type QualityTier,
  type WhiteHatsScenario,
} from "@/mock/white_hats/scenarios";
import {
  useWhiteHatsSnapshot,
  type SnapshotPhase,
} from "./hooks/useWhiteHatsSnapshot";
import type { PanelBodyState } from "./types";
import { Topbar } from "./components/Topbar";
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
export function WhiteHatsScreen() {
  const [scenario, setScenarioState] = useState<WhiteHatsScenario>("calm");
  const [tier, setTier] = useState<QualityTier>("t1");
  const [openTarget, setOpenTarget] = useState<OpenTarget>(null);
  const [selectedDecisionId, setSelectedDecisionId] = useState<string | null>(null);
  const [drawer, setDrawer] = useState<DrawerContent>(null);

  // URL is the source of truth for the demo view (?scenario=&tier=&open=).
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    setScenarioState(parseScenario(params.get("scenario")));
    setTier(parseTier(params.get("tier")));
    setOpenTarget(parseOpenTarget(params.get("open")));
  }, []);

  const phase = useWhiteHatsSnapshot(scenario);
  const snapshot = phase.phase === "ready" ? phase.snapshot : null;

  // Default selection: first non-demo decision (DEMO rows never lead totals).
  useEffect(() => {
    if (phase.phase === "ready" && selectedDecisionId === null) {
      const first =
        phase.snapshot.decisions.find((d) => !d.demo) ?? phase.snapshot.decisions[0];
      if (first) setSelectedDecisionId(first.id);
    }
  }, [phase, selectedDecisionId]);

  // Deep-link ?open=finding:<id> | evidence:<id>
  useEffect(() => {
    if (phase.phase !== "ready" || !openTarget) return;
    const snap = phase.snapshot;
    if (openTarget.kind === "finding") {
      const finding = snap.findings.find((f) => f.id === openTarget.id);
      if (finding) {
        setDrawer({
          kind: "finding",
          finding,
          inspectorTitle:
            snap.inspectors.find((i) => i.id === finding.inspectorId)?.title ??
            finding.inspectorId,
        });
      }
    } else {
      const evidence = snap.evidence[openTarget.id];
      if (evidence) setDrawer({ kind: "evidence", evidence });
    }
  }, [openTarget, phase]);

  const onScenarioChange = (next: WhiteHatsScenario) => {
    const params = new URLSearchParams(window.location.search);
    params.set("scenario", next);
    window.location.assign(`${window.location.pathname}?${params.toString()}`);
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
              message: "تصمیمی برای بازبینی انتخاب نشده است؛ با انتخاب یک ردیف، زنجیره‌ی چالش نمایش داده می‌شود.",
            }
          : { kind: "content" };

  return (
    <div
      data-tier={tier}
      data-scenario={scenario}
      data-testid="white-hats-root"
      className="relative flex min-h-dvh flex-col"
    >
      {tier !== "t0" && (
        <div
          aria-hidden="true"
          className="ah-decor pointer-events-none fixed inset-0 z-0"
          style={{
            background:
              "radial-gradient(1100px 480px at 82% -12%, rgba(217,185,119,0.075), transparent 62%)," +
              "radial-gradient(900px 420px at 6% 110%, rgba(120,203,209,0.05), transparent 60%)",
          }}
        />
      )}

      <Topbar
        scenario={scenario}
        freshness={snapshot ? snapshot.freshness : phase.phase === "unavailable" ? "UNAVAILABLE" : "LOADING"}
        onScenarioChange={onScenarioChange}
        onReload={phase.reload}
      />

      {/* Red VIOLATION bar when the mock claims LIVE / real trading. */}
      {snapshot && <PaperOnlyGuard snapshot={snapshot} />}

      <main className="relative z-10 mx-auto flex w-full max-w-[1720px] flex-1 flex-col gap-3.5 px-4 py-3.5 lg:flex-row">
        {/* RTL: the first column is the right dock. */}
        <div className="flex w-full shrink-0 flex-col gap-3.5 lg:w-[312px]">
          <InspectorsPanel
            inspectors={snapshot?.inspectors ?? []}
            state={baseState("بازرسی ثبت نشده است.", (snapshot?.inspectors.length ?? 0) === 0)}
            demo={true}
          />
          <BreakerCard
            breaker={
              snapshot?.breaker ?? {
                state: "UNKNOWN",
                updatedAt: null,
                limits: [],
              }
            }
            state={baseState("گزارش فیوز در دسترس نیست.", false)}
            demo={true}
          />
          <CanaryTile
            canary={snapshot?.canary ?? null}
            state={baseState("اجرای قناری ثبت نشده است.", false)}
            demo={true}
          />
        </div>

        <div className="flex min-w-0 flex-1 flex-col gap-3.5">
          <DecisionQueue
            decisions={snapshot?.decisions ?? []}
            selectedId={selectedDecisionId}
            onSelect={setSelectedDecisionId}
            state={baseState(
              "هیچ تصمیمی در صف بازبینی نیست — خالی یعنی خالی؛ ردیف ساختگی نشان داده نمی‌شود.",
              (snapshot?.decisions.length ?? 0) === 0,
            )}
            demo={true}
          />

          <div className="grid grid-cols-1 gap-3.5 xl:grid-cols-[minmax(0,1fr)_360px]">
            <FindingsLog
              findings={snapshot?.findings ?? []}
              inspectors={snapshot?.inspectors ?? []}
              state={baseState(
                "یافته‌ای ثبت نشده است — بازرس‌ها تا این لحظه نقضی ندیده‌اند.",
                (snapshot?.findings.length ?? 0) === 0,
              )}
              demo={true}
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
              demo={true}
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

"use client";

import { useMemo, useState, type ReactNode } from "react";
import type { VenueBundle } from "@/src/mock/trade_venue";
import type { VenueQuery, World } from "./logic/model";
import { detectViolation } from "./logic/truth";
import { selectVenueTotals, summarizeTelemetry, DEFAULT_FILTERS, buildExportCsv, type VenueFilters } from "./logic/selectors";
import { Topbar } from "./components/Topbar";
import { ViolationBar } from "./components/ViolationBar";
import { WorldTabs } from "./components/WorldTabs";
import { WorldBanner } from "./components/WorldBanner";
import { PaperPositions } from "./components/PaperPositions";
import { FillLog } from "./components/FillLog";
import { PaperResultCard } from "./components/PaperResultCard";
import { WatchlistPanel } from "./components/WatchlistPanel";
import { MarketCentersStrip } from "./components/MarketCentersStrip";
import { OpportunityBook } from "./components/OpportunityBook";
import { TelemetryStrip } from "./components/TelemetryStrip";
import { EvidenceDrawer, type EvidencePayload } from "./components/EvidenceDrawer";
import type { StatusFilter } from "./logic/selectors";

/**
 * The live shell. Everything that depends on the selected world or on the
 * filter controls lives in this client tree; the decorative dock and the footer
 * are passed in as server-rendered slots so they stay out of the client bundle.
 *
 * All numbers come from the bundle prop — the client never fetches anything.
 */
export interface VenueClientRootProps {
  bundle: VenueBundle;
  query: VenueQuery;
  dock: ReactNode;
  footer: ReactNode;
  notices: readonly string[];
}

const STATUS_OPTIONS: StatusFilter[] = [
  "ALL",
  "LIVE",
  "STALE",
  "UNKNOWN",
  "DEMO",
  "CONFLICT",
  "REJECTED",
  "SIMULATED",
];

export function VenueClientRoot({ bundle, query, dock, footer, notices }: VenueClientRootProps) {
  const [world, setWorld] = useState<World>(query.world);
  const [filters, setFilters] = useState<VenueFilters>(DEFAULT_FILTERS);
  const [evidence, setEvidence] = useState<EvidencePayload | null>(null);
  const [exportedAt, setExportedAt] = useState<string | null>(null);

  const snapshot = world === "SIMULATION" ? bundle.simulation : bundle.realPaper;
  const otherWorld: World = world === "SIMULATION" ? "REAL_PAPER" : "SIMULATION";

  const violation = detectViolation({
    executionMode: snapshot.executionMode,
    realTrading: snapshot.realTrading,
  });

  const totals = useMemo(() => selectVenueTotals(snapshot, world), [snapshot, world]);
  const telemetry = useMemo(() => summarizeTelemetry(snapshot), [snapshot]);
  const referenceISO = snapshot.freshness.readAt;

  const pageStatus = violation ? "REJECTED" : world === "SIMULATION" ? "SIMULATED" : "DEMO";

  function handleExport() {
    const csv = buildExportCsv({
      positions: snapshot.paper,
      fillLog: snapshot.fillLog,
      asOf: snapshot.asOf,
      world,
      demoForced: snapshot.demoForced,
    });
    try {
      const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `ahos-trade-venue-${world.toLowerCase()}-demo.csv`;
      document.body.appendChild(anchor);
      anchor.click();
      document.body.removeChild(anchor);
      URL.revokeObjectURL(url);
      setExportedAt(snapshot.asOf ?? "نامشخص");
    } catch {
      setExportedAt(null);
    }
  }

  return (
    <>
      {violation ? (
        <div className="ah-violation-wrap">
          <ViolationBar report={violation} fixtureProvenance={bundle.provenance.isFixture} />
        </div>
      ) : null}

      <div className="ah-shell">
        {dock}

        <div className="ah-shell__content">
          <Topbar
            world={world}
            pageStatus={pageStatus}
            tier={query.tier}
            notices={notices}
            demoForced={snapshot.demoForced}
          />

          <section
            className={world === "SIMULATION" ? "ah-work ah-work--sim" : "ah-work"}
            data-work=""
            data-world={world}
          >
            <div className="ah-work__head">
              <WorldTabs value={world} onChange={setWorld} />
              <span className="ah-work__hint">
                هر دو جهان کاغذی‌اند؛ تفاوت فقط در دفتر است. شبیه‌سازی در جمع کاغذی واقعی نمی‌آید.
              </span>
              <span className="ah-spacer" />
              <TruthTierNote tier={query.tier} />
            </div>

            <WorldBanner
              world={world}
              state={query.state}
              demoForced={snapshot.demoForced}
              isFixture={bundle.provenance.isFixture}
            />

            <div className="ah-grid3">
              <PaperPositions
                rows={snapshot.paper}
                world={world}
                state={query.state}
                filters={filters}
                referenceISO={referenceISO}
                demoForced={snapshot.demoForced}
                onEvidence={setEvidence}
                onFiltersChange={setFilters}
                onExport={handleExport}
                exportedAt={exportedAt}
                statusOptions={STATUS_OPTIONS}
              />

              <FillLog
                rows={snapshot.fillLog}
                world={world}
                state={query.state}
                filters={filters}
                referenceISO={referenceISO}
                demoForced={snapshot.demoForced}
                onEvidence={setEvidence}
              />

              <div className="ah-column">
                <PaperResultCard
                  totals={totals}
                  world={world}
                  otherWorld={otherWorld}
                  state={query.state}
                  demoForced={snapshot.demoForced}
                />
                <WatchlistPanel
                  rows={snapshot.watchlist}
                  world={world}
                  state={query.state}
                  filters={filters}
                  referenceISO={referenceISO}
                />
              </div>
            </div>

            <div className="ah-work__secondary" data-work-secondary="">
              <MarketCentersStrip
                centers={snapshot.marketCenters}
                referenceISO={referenceISO}
              />

              <OpportunityBook
                rows={snapshot.opportunities}
                state={query.state}
                referenceISO={referenceISO}
                onEvidence={setEvidence}
              />
            </div>
          </section>

          <TelemetryStrip summary={telemetry} referenceISO={referenceISO} tier={query.tier} />
          {footer}
        </div>
      </div>

      <EvidenceDrawer payload={evidence} onClose={() => setEvidence(null)} />
    </>
  );
}

function TruthTierNote({ tier }: { tier: string }) {
  return (
    <span className="ah-pill ah-pill--tier" data-tier-note={tier} dir="ltr">
      {tier === "T0"
        ? "T0 · TABLES ONLY"
        : tier === "T1"
          ? "T1 · SOLID PANELS"
          : "T2 · GLASS + DECOR (OPTIONAL)"}
    </span>
  );
}

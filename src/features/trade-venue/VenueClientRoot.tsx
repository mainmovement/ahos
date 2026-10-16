"use client";

import { useMemo, useState } from "react";
import { tr } from "@/src/lib/i18n";
import type { VenueBundle } from "@/src/mock/trade_venue";
import type { VenueQuery, World } from "./logic/model";
import { detectViolation } from "./logic/truth";
import { selectVenueTotals, summarizeTelemetry, DEFAULT_FILTERS, buildExportCsv, type VenueFilters } from "./logic/selectors";
import { TruthChip } from "@/src/components/truth/TruthChip";
import { PaperOnlyPill } from "./components/PaperOnlyGuard";
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
import { Expander } from "./components/Expander";
import { SummaryView } from "./components/SummaryView";
import type { StatusFilter } from "./logic/selectors";

/**
 * Client tree of the venue. It renders *inside* the Arena shell (the shell owns
 * the topbar and sidebar), so there is no topbar/dock/footer here.
 * Default view = calm summary; «جزئیات» holds the tables behind expanders.
 * All numbers come from the bundle prop — the client never fetches anything.
 */
export interface VenueClientRootProps {
  bundle: VenueBundle;
  query: VenueQuery;
  notices: readonly string[];
}

const STATUS_OPTIONS: StatusFilter[] = ["ALL", "LIVE", "STALE", "UNKNOWN", "DEMO", "CONFLICT", "REJECTED", "SIMULATED"];

export function VenueClientRoot({ bundle, query, notices }: VenueClientRootProps) {
  const t = (key: string) => tr("fa", `tradeVenue.${key}`);
  const [world, setWorld] = useState<World>(query.world);
  const [view, setView] = useState<"summary" | "details">(query.view);
  const [filters, setFilters] = useState<VenueFilters>(DEFAULT_FILTERS);
  const [evidence, setEvidence] = useState<EvidencePayload | null>(null);
  const [exportedAt, setExportedAt] = useState<string | null>(null);

  const snapshot = world === "SIMULATION" ? bundle.simulation : bundle.realPaper;
  const otherWorld: World = world === "SIMULATION" ? "REAL_PAPER" : "SIMULATION";

  const violation = detectViolation({ executionMode: snapshot.executionMode, realTrading: snapshot.realTrading });
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
      setExportedAt(snapshot.asOf ?? t("unknown"));
    } catch {
      setExportedAt(null);
    }
  }

  const common = { world, state: query.state, demoForced: snapshot.demoForced } as const;

  return (
    <div className="tv-page" data-view-mode={view}>
      {violation ? (
        <div className="tv-violation-wrap">
          <ViolationBar report={violation} fixtureProvenance={bundle.provenance.isFixture} />
        </div>
      ) : null}

      <div className="tv-pagebar" data-pagebar="">
        <WorldTabs value={world} onChange={setWorld} />
        <div className="tv-viewtabs" role="tablist" aria-label={t("viewTabs")}>
          {(["summary", "details"] as const).map((v) => (
            <button
              key={v}
              type="button"
              role="tab"
              aria-selected={view === v}
              data-verb="tab"
              data-view-tab={v}
              className="tv-tab"
              onClick={() => setView(v)}
            >
              {t(v === "summary" ? "viewSummary" : "viewDetails")}
            </button>
          ))}
        </div>
        <span className="tv-spacer" />
        <TruthChip status={pageStatus} title={t("pageStatusTitle")} />
        <PaperOnlyPill />
      </div>

      <WorldBanner world={world} state={query.state} demoForced={snapshot.demoForced} isFixture={bundle.provenance.isFixture} />

      {view === "summary" ? (
        <SummaryView
          totals={totals}
          positions={snapshot.paper}
          centers={snapshot.marketCenters}
          world={world}
          referenceISO={referenceISO}
          demoForced={snapshot.demoForced}
          onShowDetails={() => setView("details")}
        />
      ) : (
        <div className="tv-details" data-view="details">
          <Expander id="positions" title={t("sec.positions")} meta={`${snapshot.paper.length}`} defaultOpen>
            <PaperPositions
              rows={snapshot.paper}
              {...common}
              filters={filters}
              referenceISO={referenceISO}
              onEvidence={setEvidence}
              onFiltersChange={setFilters}
              onExport={handleExport}
              exportedAt={exportedAt}
              statusOptions={STATUS_OPTIONS}
            />
          </Expander>
          <Expander id="result" title={t("sec.result")} defaultOpen>
            <PaperResultCard totals={totals} otherWorld={otherWorld} {...common} />
          </Expander>
          <Expander id="fill-log" title={t("sec.fillLog")} meta={`${snapshot.fillLog.length}`}>
            <FillLog rows={snapshot.fillLog} {...common} filters={filters} referenceISO={referenceISO} onEvidence={setEvidence} />
          </Expander>
          <Expander id="watchlist" title={t("sec.watchlist")} meta={`${snapshot.watchlist.length}`}>
            <WatchlistPanel rows={snapshot.watchlist} world={world} state={query.state} filters={filters} referenceISO={referenceISO} />
          </Expander>
          <Expander id="markets" title={t("sec.markets")}>
            <MarketCentersStrip centers={snapshot.marketCenters} referenceISO={referenceISO} />
          </Expander>
          <Expander id="opportunities" title={t("sec.opportunities")} meta={`${snapshot.opportunities.length}`}>
            <OpportunityBook rows={snapshot.opportunities} state={query.state} referenceISO={referenceISO} onEvidence={setEvidence} />
          </Expander>
          <Expander id="telemetry" title={t("sec.telemetry")}>
            <TelemetryStrip summary={telemetry} referenceISO={referenceISO} tier={query.tier} />
          </Expander>
          {notices.length > 0 ? (
            <Expander id="notes" title={t("sec.notes")} meta={`${notices.length}`}>
              <ul className="tv-notes">
                {notices.map((n) => (
                  <li key={n}>{n}</li>
                ))}
              </ul>
            </Expander>
          ) : null}
        </div>
      )}

      <EvidenceDrawer payload={evidence} onClose={() => setEvidence(null)} />
    </div>
  );
}

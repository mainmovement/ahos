import { TruthChip } from "@/src/components/truth/TruthChip";
import { tr } from "@/src/lib/i18n";
import type { MarketCenter, PaperPosition, World } from "@/src/features/trade-venue/logic/model";
import type { VenueTotals } from "@/src/features/trade-venue/logic/selectors";
import { MISSING_GLYPH, valueText } from "@/src/features/trade-venue/logic/truth";
import { rowDisplay } from "@/src/features/trade-venue/logic/rowStatus";
import { pickHighlights } from "@/src/features/trade-venue/logic/highlights";
import { RowStatusCell } from "./RowStatusCell";

/**
 * Calm default view: one paper result, one open-positions count, one market
 * status strip and at most 7 highlighted positions. Everything detailed lives
 * in the «جزئیات» tab. All truth rules still apply (DEMO per row, STALE with a
 * time, UNKNOWN without one, no real-money controls).
 */
export function SummaryView({
  totals,
  positions,
  centers,
  world,
  referenceISO,
  demoForced,
  onShowDetails,
}: {
  totals: VenueTotals;
  positions: readonly PaperPosition[];
  centers: readonly MarketCenter[];
  world: World;
  referenceISO: string | null;
  demoForced: boolean;
  onShowDetails: () => void;
}) {
  const t = (key: string) => tr("fa", `tradeVenue.sum.${key}`);
  const block = totals.closed;
  const total = block.singleUnitTotal;
  const isSim = world === "SIMULATION";
  const highlights = pickHighlights(positions, 7);

  return (
    <div className="tv-summary" data-view="summary">
      <div className="tv-hero">
        <section className="tv-hero__card tv-hero__card--result" data-panel="paper-result" data-world={world} aria-label={t("result")}>
          <header className="tv-hero__head">
            <h2>{isSim ? t("resultSim") : t("result")}</h2>
            <TruthChip status={isSim ? "SIMULATED" : "DEMO"} size="sm" />
          </header>
          <p className="tv-hero__value tv-mono" data-missing={total === null ? "true" : "false"}>
            {total === null ? MISSING_GLYPH : valueText(total, { fractionDigits: 2 })}
            {total !== null && block.singleUnit ? <span className="tv-hero__unit">{block.singleUnit}</span> : null}
          </p>
          <p className="tv-hero__note">{total === null ? t("resultMissing") : t("resultNote")}</p>
        </section>

        <section className="tv-hero__card" data-panel="open-count" aria-label={t("open")}>
          <header className="tv-hero__head">
            <h2>{t("open")}</h2>
          </header>
          <p className="tv-hero__value tv-mono" dir="ltr">{totals.counts.openRows}</p>
          <p className="tv-hero__note">
            {t("openNote")
              .replace("{demo}", String(demoForced ? totals.counts.openRows : positions.filter((p) => rowDisplay({ status: p.status, updatedAt: p.updatedAt, sourceId: p.sourceId }).demo).length))
              .replace("{na}", String(totals.counts.notAuthorizedRows))}
          </p>
        </section>

        <section className="tv-hero__card" data-panel="market-status" aria-label={t("markets")}>
          <header className="tv-hero__head">
            <h2>{t("markets")}</h2>
          </header>
          <ul className="tv-marketstrip">
            {centers.map((center) => (
              <li key={center.id} data-center={center.code}>
                <span className="tv-marketstrip__code" dir="ltr">{center.code}</span>
                <TruthChip
                  status={center.state === "LIVE" ? "DEMO" : center.state}
                  size="sm"
                  hideCode
                  labelFa={center.state === "PLANNED" ? tr("fa", "tradeVenue.sum.notConnected") : undefined}
                />
              </li>
            ))}
          </ul>
        </section>
      </div>

      <section className="tv-highlights" data-panel="highlights" aria-label={t("highlights")}>
        <header className="tv-highlights__head">
          <h2>{t("highlights")}</h2>
          <button type="button" className="tv-btn tv-btn--lg" data-verb="view" data-open-details="" onClick={onShowDetails}>
            {t("showDetails")}
          </button>
        </header>
        {highlights.length === 0 ? (
          <p className="tv-hero__note">{t("none")}</p>
        ) : (
          <ul className="tv-highlights__list">
            {highlights.map((row) => {
              const display = rowDisplay({ status: row.status, updatedAt: row.updatedAt, sourceId: row.sourceId, bundleDemo: demoForced });
              return (
                <li
                  key={row.id}
                  className={display.demo ? "tv-highlight tv-row--demo" : "tv-highlight"}
                  data-row-id={row.id}
                  data-row-demo={display.demo ? "true" : "false"}
                >
                  <span className="tv-highlight__sym">
                    <strong dir="ltr">{row.symbol}</strong>
                    <span>{row.symbolFa}</span>
                  </span>
                  <span className="tv-highlight__mark tv-mono" dir="ltr">
                    {valueText(row.mark, { fractionDigits: Math.abs(row.mark ?? 2) < 1 ? 4 : 2 })}
                  </span>
                  <RowStatusCell status={display.status} demo={display.demo} updatedAt={row.updatedAt} referenceISO={referenceISO} />
                </li>
              );
            })}
          </ul>
        )}
      </section>
      <p className="tv-summary__foot">{tr("fa", "tradeVenue.note")}</p>
    </div>
  );
}

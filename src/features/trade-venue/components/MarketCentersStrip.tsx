import { tr } from "@/src/lib/i18n";
import { TruthChip } from "@/src/components/truth/TruthChip";
import { NOT_CONNECTED_FA } from "@/src/features/trade-venue/logic/truth";
import { ageShort } from "@/src/features/trade-venue/logic/format";
import type { MarketCenter } from "@/src/features/trade-venue/logic/model";

/**
 * Per-market command centres.
 *
 * Rule of the strip: a market that is not connected shows **no numbers at all**.
 * Gold is the only connected feed and it is explicitly DEMO; every other market
 * is a grey outline marked «متصل نیست» / PLANNED. There is deliberately no
 * "estimate" or "last known" value anywhere in this component — the type
 * `MarketCenter` cannot even carry one.
 */
export function MarketCentersStrip({
  centers,
  referenceISO,
}: {
  centers: readonly MarketCenter[];
  referenceISO: string | null;
}) {
  return (
    <section className="tv-panel" data-panel="market-centers" aria-label={tr("fa", "tradeVenue.ui.MarketCentersStrip_1")}>
      <header className="tv-panel__head">
        <span className="tv-panel__title">{tr("fa", "tradeVenue.ui.MarketCentersStrip_2")}</span>
        <span className="tv-panel__title-en" dir="ltr">
          PER-MARKET COMMAND CENTRES
        </span>
        <div className="tv-panel__tools">
          <TruthChip status="DEMO" size="sm" title={tr("fa", "tradeVenue.ui.MarketCentersStrip_3")} />
        </div>
      </header>
      <div className="tv-panel__body">
        <div className="tv-centers" data-table="market-centers">
          {centers.map((center) => {
            const connected = center.state === "DEMO" || center.state === "STALE";
            return (
              <article
                className="tv-center"
                key={center.id}
                data-center={center.code}
                data-state={center.state}
              >
                <div className="tv-center__top">
                  <span className="tv-center__name">{center.nameFa}</span>
                  <span className="tv-center__chip">
                    <TruthChip
                      status={center.state === "LIVE" ? "DEMO" : center.state}
                      size="sm"
                      labelFa={center.state === "PLANNED" ? NOT_CONNECTED_FA : undefined}
                    />
                  </span>
                </div>

                {connected ? (
                  <div className="tv-center__metrics" dir="ltr" title={center.noteFa ?? undefined}>
                    <span className="tv-center__code">{center.code}</span>
                    <span title={tr("fa", "tradeVenue.ui.MarketCentersStrip_4")}>
                      rows={center.rows === null ? "—" : center.rows}
                    </span>
                    <span title={tr("fa", "tradeVenue.ui.MarketCentersStrip_5")}>
                      age={ageShort(center.lastReadAt, referenceISO)}
                    </span>
                    <span className="tv-faint" title={`منبع: ${center.feeds.join(", ") || "—"}`}>
                      src
                    </span>

                  </div>
                ) : (
                  <p
                    className="tv-center__na"
                    data-no-numbers="true"
                    title={`${center.code} — هیچ عددی برای این بازار ساخته نمی‌شود.`}
                  >
                    <span className="tv-center__code">{center.code}</span>{" "}
                    {center.noteFa ?? NOT_CONNECTED_FA}
                  </p>
                )}
              </article>
            );
          })}
        </div>
      </div>
      <footer className="tv-panel__foot">
        <span>
          {tr("fa", "tradeVenue.ui.MarketCentersStrip_6")}
          {tr("fa", "tradeVenue.ui.MarketCentersStrip_7")}
        </span>
      </footer>
    </section>
  );
}

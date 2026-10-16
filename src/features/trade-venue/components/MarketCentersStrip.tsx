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
    <section className="ah-panel" data-panel="market-centers" aria-label="مراکز فرمان بازارها">
      <header className="ah-panel__head">
        <span className="ah-panel__title">مرکز فرمان بازارها</span>
        <span className="ah-panel__title-en" dir="ltr">
          PER-MARKET COMMAND CENTRES
        </span>
        <div className="ah-panel__tools">
          <TruthChip status="DEMO" size="sm" title="فقط طلا اتصال دارد و آن هم نمایشی است" />
        </div>
      </header>
      <div className="ah-panel__body">
        <div className="ah-centers" data-table="market-centers">
          {centers.map((center) => {
            const connected = center.state === "DEMO" || center.state === "STALE";
            return (
              <article
                className="ah-center"
                key={center.id}
                data-center={center.code}
                data-state={center.state}
              >
                <div className="ah-center__top">
                  <span className="ah-center__name">{center.nameFa}</span>
                  <span className="ah-center__chip">
                    <TruthChip
                      status={center.state}
                      size="sm"
                      labelFa={center.state === "PLANNED" ? NOT_CONNECTED_FA : undefined}
                    />
                  </span>
                </div>

                {connected ? (
                  <div className="ah-center__metrics" dir="ltr" title={center.noteFa ?? undefined}>
                    <span className="ah-center__code">{center.code}</span>
                    <span title="تعداد ردیف خوانده‌شده">
                      rows={center.rows === null ? "—" : center.rows}
                    </span>
                    <span title="عمر آخرین خواندن در برابر لنگر داده">
                      age={ageShort(center.lastReadAt, referenceISO)}
                    </span>
                    <span className="ah-faint" title={`منبع: ${center.feeds.join(", ") || "—"}`}>
                      src
                    </span>

                  </div>
                ) : (
                  <p
                    className="ah-center__na"
                    data-no-numbers="true"
                    title={`${center.code} — هیچ عددی برای این بازار ساخته نمی‌شود.`}
                  >
                    <span className="ah-center__code">{center.code}</span>{" "}
                    {center.noteFa ?? NOT_CONNECTED_FA}
                  </p>
                )}
              </article>
            );
          })}
        </div>
      </div>
      <footer className="ah-panel__foot">
        <span>
          بازار بدون اتصال، عدد ندارد. برای هر بازار، فرماندهی نیازمند فید مستند است؛ تا آن زمان فقط
          دفتر کاغذی دیده می‌شود.
        </span>
      </footer>
    </section>
  );
}

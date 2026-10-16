import { tr } from "@/src/lib/i18n";
import { TruthChip } from "@/src/components/truth/TruthChip";
import { ageShort, tehranParts } from "@/src/features/trade-venue/logic/format";
import { MISSING_GLYPH, UNKNOWN_LABEL_FA } from "@/src/features/trade-venue/logic/truth";
import type { TelemetrySummary } from "@/src/features/trade-venue/logic/selectors";

/**
 * Bottom telemetry strip: source id, last read, row count — plus how many rows
 * the adapter withheld and whether the bundle is a fixture. The point of the
 * strip is that a reader can always answer "where did this screen come from?".
 */
export function TelemetryStrip({
  summary,
  referenceISO,
}: {
  summary: TelemetrySummary;
  referenceISO: string | null;
  tier?: string;
}) {
  const readParts = summary.lastReadAt ? tehranParts(summary.lastReadAt) : null;

  return (
    <footer className="tv-telemetry" data-telemetry="">
      <div className="tv-telemetry__group">
        <span className="tv-telemetry__k">{tr("fa", "tradeVenue.ui.TelemetryStrip_1")}</span>
        <span className="tv-telemetry__v" data-telemetry-source="">
          {summary.sourceId}
        </span>
        <TruthChip status="DEMO" size="sm" hideCode />
      </div>

      <div className="tv-telemetry__group">
        <span className="tv-telemetry__k">{tr("fa", "tradeVenue.ui.TelemetryStrip_2")}</span>
        <span className="tv-telemetry__v" data-telemetry-lastread="">
          {summary.lastReadAt ? `${readParts?.time ?? MISSING_GLYPH} · ${summary.lastReadAt}` : UNKNOWN_LABEL_FA}
        </span>
        <span className="tv-faint" dir="ltr">
          age={ageShort(summary.lastReadAt, referenceISO)}
        </span>
      </div>

      <div className="tv-telemetry__group">
        <span className="tv-telemetry__k">{tr("fa", "tradeVenue.ui.TelemetryStrip_3")}</span>
        <span className="tv-telemetry__v" data-telemetry-rows="">
          {summary.rows}
        </span>
        <span className="tv-faint">
          کنارگذاشته:{" "}
          <span className="tv-mono" dir="ltr">
            {summary.withheldRows === null ? MISSING_GLYPH : summary.withheldRows}
          </span>
        </span>
      </div>

      <div className="tv-telemetry__group">
        <span className="tv-telemetry__k">{tr("fa", "tradeVenue.ui.TelemetryStrip_4")}</span>
        <span className="tv-telemetry__v">
          demo={summary.demoRows} · sim={summary.simulationRows} · unknown={summary.unknownRows}
        </span>
      </div>

      <div className="tv-telemetry__group">
        <span className="tv-telemetry__k">{tr("fa", "tradeVenue.ui.TelemetryStrip_5")}</span>
        <span className="tv-telemetry__v" dir="ltr">
          {summary.world} · {summary.soldAs}
        </span>
      </div>
    </footer>
  );
}

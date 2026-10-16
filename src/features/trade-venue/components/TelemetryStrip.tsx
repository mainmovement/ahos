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
  tier,
}: {
  summary: TelemetrySummary;
  referenceISO: string | null;
  tier: string;
}) {
  const readParts = summary.lastReadAt ? tehranParts(summary.lastReadAt) : null;

  return (
    <footer className="ah-telemetry" data-telemetry="">
      <div className="ah-telemetry__group">
        <span className="ah-telemetry__k">منبع:</span>
        <span className="ah-telemetry__v" data-telemetry-source="">
          {summary.sourceId}
        </span>
        <TruthChip status="DEMO" size="sm" hideCode />
      </div>

      <div className="ah-telemetry__group">
        <span className="ah-telemetry__k">آخرین خواندن:</span>
        <span className="ah-telemetry__v" data-telemetry-lastread="">
          {summary.lastReadAt ? `${readParts?.time ?? MISSING_GLYPH} · ${summary.lastReadAt}` : UNKNOWN_LABEL_FA}
        </span>
        <span className="ah-faint" dir="ltr">
          age={ageShort(summary.lastReadAt, referenceISO)}
        </span>
      </div>

      <div className="ah-telemetry__group">
        <span className="ah-telemetry__k">ردیف‌ها:</span>
        <span className="ah-telemetry__v" data-telemetry-rows="">
          {summary.rows}
        </span>
        <span className="ah-faint">
          کنارگذاشته:{" "}
          <span className="ah-mono" dir="ltr">
            {summary.withheldRows === null ? MISSING_GLYPH : summary.withheldRows}
          </span>
        </span>
      </div>

      <div className="ah-telemetry__group">
        <span className="ah-telemetry__k">ترکیب:</span>
        <span className="ah-telemetry__v">
          demo={summary.demoRows} · sim={summary.simulationRows} · unknown={summary.unknownRows}
        </span>
      </div>

      <div className="ah-telemetry__group">
        <span className="ah-telemetry__k">جهان:</span>
        <span className="ah-telemetry__v" dir="ltr">
          {summary.world} · {summary.soldAs}
        </span>
        <span className="ah-faint">TIER {tier}</span>
      </div>
    </footer>
  );
}

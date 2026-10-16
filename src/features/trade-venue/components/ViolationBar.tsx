import { tr } from "@/src/lib/i18n";
import type { ViolationReport } from "@/src/features/trade-venue/logic/truth";

/**
 * Full-width VIOLATION bar (truth rule 6).
 *
 * Rendered whenever the adapter reports `realTrading === true` or an
 * `executionMode` other than PAPER_ONLY. It is not dismissible and carries no
 * control — its only job is to make an illegal state impossible to ignore.
 * `role="alert"` so assistive tech announces it immediately.
 */
export interface ViolationBarProps {
  report: ViolationReport;
  /** True when the report itself came from the fixture adapter. */
  fixtureProvenance?: boolean;
}

export function ViolationBar({ report, fixtureProvenance = false }: ViolationBarProps) {
  return (
    <div
      className="tv-violation"
      role="alert"
      data-violation={report.code}
      data-dismissible="false"
    >
      <span className="tv-violation__tag" dir="ltr">
        VIOLATION
      </span>
      <div className="tv-violation__body">
        <strong>{report.headlineFa}</strong>
        <span>{report.detailFa}</span>
        <span className="tv-violation__en">{report.detailEn}</span>
        {fixtureProvenance ? (
          <span className="tv-violation__en">
            {tr("fa", "tradeVenue.row.violationDemo")}
          </span>
        ) : null}
      </div>
    </div>
  );
}

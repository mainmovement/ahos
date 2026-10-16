import { TruthChip } from "@/src/components/truth/TruthChip";
import type { ChipStatus } from "@/src/features/trade-venue/logic/model";
import { ageShort, tehranClock } from "@/src/features/trade-venue/logic/format";
import { tr } from "@/src/lib/i18n";

/**
 * Per-row status: truth chip + (on demo rows) a DEMO tag with a striped marker,
 * + (on STALE rows) the last-update time. STALE without a timestamp never
 * reaches here: `rowDisplay` has already downgraded it to UNKNOWN.
 */
export function RowStatusCell({
  status,
  demo,
  updatedAt,
  referenceISO,
}: {
  status: ChipStatus;
  demo: boolean;
  updatedAt: string | null;
  referenceISO: string | null;
}) {
  return (
    <span className="tv-rowstatus" data-demo={demo ? "true" : "false"}>
      <TruthChip status={status} size="sm" hideCode />
      {demo ? (
        <span className="tv-demo-tag" data-demo-tag="" title={tr("fa", "tradeVenue.row.demoTitle")}>
          DEMO
        </span>
      ) : null}
      {status === "STALE" && updatedAt ? (
        <span className="tv-stale-time" data-stale-time="" dir="ltr" title={updatedAt}>
          {tehranClock(updatedAt)} · {ageShort(updatedAt, referenceISO)}
        </span>
      ) : null}
    </span>
  );
}

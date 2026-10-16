import { MISSING_GLYPH, MISSING_LABEL_FA } from "@/src/features/trade-venue/logic/truth";
import { valueText } from "@/src/features/trade-venue/logic/format";

/**
 * Truth rule 2 in one component: a number either exists, or the cell prints
 * «—» with the word «ناموجود». There is no third branch that could emit a
 * placeholder `0`, and `data-missing` lets the tests prove it.
 */
export interface ValueCellProps {
  value: number | null | undefined;
  fractionDigits?: number;
  signed?: boolean;
  /** Append a unit inside the cell (e.g. USDT). */
  unit?: string | null;
  /** Show the «ناموجود» word next to the dash. */
  labelMissing?: boolean;
  /** Put the unit on its own line — keeps narrow columns from clipping digits. */
  stacked?: boolean;
}

export function ValueCell({
  value,
  fractionDigits = 2,
  signed = false,
  unit,
  labelMissing = true,
  stacked = false,
}: ValueCellProps) {
  const formatted = valueText(value, { fractionDigits, signed });
  const missing = formatted === MISSING_GLYPH;

  if (missing) {
    return (
      <span className="ah-cell-na" data-missing="true" title={MISSING_LABEL_FA}>
        {MISSING_GLYPH}
        {labelMissing ? <small>{MISSING_LABEL_FA}</small> : null}
      </span>
    );
  }

  if (stacked) {
    return (
      <span className="ah-stack" data-missing="false">
        <span className="ah-mono">{formatted}</span>
        {unit ? <span className="ah-stack__unit">{unit}</span> : null}
      </span>
    );
  }

  return (
    <span className="ah-mono" data-missing="false">
      {formatted}
      {unit ? <span className="ah-kv__unit">{unit}</span> : null}
    </span>
  );
}

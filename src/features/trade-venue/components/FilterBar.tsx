"use client";
import { tr } from "@/src/lib/i18n";

import type { StatusFilter, VenueFilters } from "@/src/features/trade-venue/logic/selectors";
import { EXPORT_FA, EXPORT_NOTE_FA, READ_ONLY_FA } from "@/src/features/trade-venue/logic/labels";

/**
 * The only interactive controls on the page: filter (search / status /
 * permission) and a read-only CSV export. No control here can change state on
 * the backend; every one of them is tagged with `data-verb` so the truth tests
 * can prove the vocabulary stays read-only.
 */
export interface FilterBarProps {
  filters: VenueFilters;
  onChange: (filters: VenueFilters) => void;
  onExport: () => void;
  visible: number;
  total: number;
  statusOptions: readonly StatusFilter[];
}

export function FilterBar({
  filters,
  onChange,
  onExport,
  visible,
  total,
  statusOptions,
}: FilterBarProps) {
  return (
    <div className="tv-filterbar" data-filterbar="">
      <label className="tv-input-wrap">
        <span className="tv-sr">{tr("fa", "tradeVenue.ui.FilterBar_1")}</span>
        <input
          className="tv-input"
          type="search"
          value={filters.query}
          placeholder={tr("fa", "tradeVenue.ui.FilterBar_2")}
          data-verb="filter"
          onChange={(event) => onChange({ ...filters, query: event.target.value })}
        />
      </label>

      <label className="tv-input-wrap">
        <span className="tv-sr">{tr("fa", "tradeVenue.ui.FilterBar_3")}</span>
        <select
          className="tv-select"
          value={filters.status}
          data-verb="filter"
          onChange={(event) =>
            onChange({ ...filters, status: event.target.value as StatusFilter })
          }
        >
          {statusOptions.map((status) => (
            <option key={status} value={status}>
              {status === "ALL" ? tr("fa", "tradeVenue.ui.FilterBar_4") : status}
            </option>
          ))}
        </select>
      </label>

      <button
        type="button"
        className="tv-btn"
        data-verb="filter"
        aria-pressed={filters.onlyAllowed}
        onClick={() => onChange({ ...filters, onlyAllowed: !filters.onlyAllowed })}
        title={tr("fa", "tradeVenue.ui.FilterBar_5")}
      >
        {tr("fa", "tradeVenue.ui.FilterBar_6")}
      </button>

      <button
        type="button"
        className="tv-btn"
        data-kind="export"
        data-verb="export"
        onClick={onExport}
        title={EXPORT_NOTE_FA}
      >
        {EXPORT_FA}
        <span className="tv-btn__en" dir="ltr">
          read-only
        </span>
      </button>

      <span className="tv-filterbar__count" data-filter-count="" title={READ_ONLY_FA}>
        <span className="tv-mono" dir="ltr">
          {visible}/{total}
        </span>{" "}
        {tr("fa", "tradeVenue.ui.FilterBar_7")}
      </span>
    </div>
  );
}

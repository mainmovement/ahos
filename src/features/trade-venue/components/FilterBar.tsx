"use client";

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
    <div className="ah-filterbar" data-filterbar="">
      <label className="ah-input-wrap">
        <span className="ah-sr">جستجوی نماد</span>
        <input
          className="ah-input"
          type="search"
          value={filters.query}
          placeholder="جستجوی نماد یا منبع…"
          data-verb="filter"
          onChange={(event) => onChange({ ...filters, query: event.target.value })}
        />
      </label>

      <label className="ah-input-wrap">
        <span className="ah-sr">وضعیت</span>
        <select
          className="ah-select"
          value={filters.status}
          data-verb="filter"
          onChange={(event) =>
            onChange({ ...filters, status: event.target.value as StatusFilter })
          }
        >
          {statusOptions.map((status) => (
            <option key={status} value={status}>
              {status === "ALL" ? "همهٔ وضعیت‌ها" : status}
            </option>
          ))}
        </select>
      </label>

      <button
        type="button"
        className="ah-btn"
        data-verb="filter"
        aria-pressed={filters.onlyAllowed}
        onClick={() => onChange({ ...filters, onlyAllowed: !filters.onlyAllowed })}
        title="فقط ردیف‌هایی که مجوز کاغذی دارند"
      >
        فقط مجوزدار
      </button>

      <button
        type="button"
        className="ah-btn"
        data-kind="export"
        data-verb="export"
        onClick={onExport}
        title={EXPORT_NOTE_FA}
      >
        {EXPORT_FA}
        <span className="ah-btn__en" dir="ltr">
          read-only
        </span>
      </button>

      <span className="ah-filterbar__count" data-filter-count="" title={READ_ONLY_FA}>
        <span className="ah-mono" dir="ltr">
          {visible}/{total}
        </span>{" "}
        ردیف
      </span>
    </div>
  );
}

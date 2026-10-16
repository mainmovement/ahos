"use client";

import { DemoBadge } from "@/components/truth/DemoBadge";
import { PaperPill } from "@/components/truth/PaperPill";
import { StatusChip } from "@/components/truth/StatusChip";
import type { ChipStatus } from "@/components/truth/status";
import {
  SCENARIO_LABELS,
  WHITE_HATS_SCENARIOS,
  type WhiteHatsScenario,
} from "@/mock/white_hats/scenarios";
import { RefreshIcon, ShieldIcon } from "./icons";

export interface TopbarProps {
  scenario: WhiteHatsScenario;
  freshness: ChipStatus;
  onScenarioChange: (scenario: WhiteHatsScenario) => void;
  onReload: () => void;
}

/**
 * Topbar: brand, permanent PAPER_ONLY pill (never dismissible), DEMO badge,
 * freshness of the audit feed, and the demo scenario switcher (view-only).
 */
export function Topbar({
  scenario,
  freshness,
  onScenarioChange,
  onReload,
}: TopbarProps) {
  return (
    <header
      className="sticky top-0 z-30 flex h-14 shrink-0 items-center gap-3 border-b border-line bg-[color:var(--ah-bg)]/92 px-4 backdrop-blur-md"
      data-testid="topbar"
    >
      <div className="flex items-center gap-2.5">
        <span className="grid size-9 place-items-center rounded-md border border-line bg-surface">
          <ShieldIcon />
        </span>
        <div className="flex flex-col leading-tight">
          <span className="text-[14px] font-semibold tracking-tight text-ink">
            کلاه‌سفیدها و ناظر
          </span>
          <span className="ah-latin text-[8px] uppercase tracking-[0.22em] text-mute">
            AHOS · White Hats &amp; Judge — Read-only audit
          </span>
        </div>
      </div>

      <div className="mx-1 hidden h-6 w-px bg-line md:block" aria-hidden="true" />

      <div className="hidden items-center gap-1.5 md:flex">
        <StatusChip status={freshness} title="تازگی آخرین خوانش از منبع بازبینی" />
      </div>

      <div className="ms-auto flex items-center gap-2">
        <label className="flex items-center gap-1.5 text-[10.5px] text-mute">
          <span className="hidden sm:inline">نما:</span>
          <select
            className="ah-focus rounded-sm border border-line bg-surface px-1.5 py-[3px] text-[11px] text-dim hover:border-linestrong"
            value={scenario}
            onChange={(event) => onScenarioChange(event.target.value as WhiteHatsScenario)}
            aria-label="سناریوی نمایشی"
            data-testid="scenario-select"
          >
            {WHITE_HATS_SCENARIOS.map((s) => (
              <option key={s} value={s}>
                {SCENARIO_LABELS[s]}
              </option>
            ))}
          </select>
        </label>

        <button
          type="button"
          className="ah-focus inline-flex items-center gap-1.5 rounded-sm border border-line px-2 py-[3px] text-[11px] text-dim transition-colors hover:border-linestrong hover:text-gold"
          onClick={onReload}
          aria-label="بازخوانی فقط‌خواندنی منبع"
        >
          <RefreshIcon />
          بازخوانی
        </button>

        <DemoBadge />
        {/* Permanent, non-dismissible — the pill has no close path. */}
        <PaperPill />
      </div>
    </header>
  );
}

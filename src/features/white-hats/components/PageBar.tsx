"use client";

import { tr } from "@/src/lib/i18n";
import { DemoBadge } from "@/src/features/white-hats/truth/DemoBadge";
import { PaperPill } from "@/src/features/white-hats/truth/PaperPill";
import { StatusChip } from "@/src/features/white-hats/truth/StatusChip";
import type { ChipStatus } from "@/src/features/white-hats/truth/status";
import {
  SCENARIO_LABELS,
  WHITE_HATS_SCENARIOS,
  type WhiteHatsScenario,
} from "@/src/mock/white_hats/scenarios";
import { RefreshIcon } from "./icons";

/**
 * In-page bar (the Arena shell owns the real topbar): feed freshness, the
 * view-only scenario switcher, reload, the DEMO badge (only when the data is
 * demo) and the permanent PAPER_ONLY pill.
 */
export function PageBar({
  scenario,
  freshness,
  demo,
  onScenarioChange,
  onReload,
}: {
  scenario: WhiteHatsScenario;
  freshness: ChipStatus;
  demo: boolean;
  onScenarioChange: (scenario: WhiteHatsScenario) => void;
  onReload: () => void;
}) {
  return (
    <div className="flex flex-wrap items-center gap-3 px-1" data-testid="topbar">
      <StatusChip status={freshness} demo={demo} title={tr("fa", "whiteHats.freshnessTitle")} />
      <div className="ms-auto flex flex-wrap items-center gap-2">
        <label className="flex items-center gap-1.5 text-[13px] text-mute">
          <span>{tr("fa", "whiteHats.view")}</span>
          <select
            className="wh-focus rounded-sm border border-line bg-surface px-2 py-1 text-[13px] text-dim hover:border-linestrong"
            value={scenario}
            onChange={(event) => onScenarioChange(event.target.value as WhiteHatsScenario)}
            aria-label={tr("fa", "whiteHats.scenarioAria")}
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
          className="wh-focus inline-flex items-center gap-1.5 rounded-sm border border-line px-3 py-1 text-[13px] text-dim transition-colors hover:border-linestrong hover:text-gold"
          onClick={onReload}
          aria-label={tr("fa", "whiteHats.reloadAria")}
        >
          <RefreshIcon />
          {tr("fa", "whiteHats.reload")}
        </button>
        {demo ? <DemoBadge /> : null}
        <PaperPill />
      </div>
    </div>
  );
}

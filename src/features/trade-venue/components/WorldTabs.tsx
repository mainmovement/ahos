"use client";

import type { World } from "@/src/features/trade-venue/logic/model";
import { WORLD_LABEL_EN, WORLD_LABEL_FA } from "@/src/features/trade-venue/logic/model";
import { PAPER_ONLY_CODE } from "@/src/features/trade-venue/logic/truth";

/**
 * World switch: REAL-PAPER (default, sober ledger chrome) ⇄ SIMULATION
 * (distinct violet tint, SIMULATED ribbon, excluded from REAL-PAPER totals).
 *
 * Both worlds are paper-only — the tab is bookkeeping, not authority — which is
 * why the PAPER_ONLY code is printed next to the labels of both tabs.
 */
export interface WorldTabsProps {
  value: World;
  onChange: (world: World) => void;
}

export function WorldTabs({ value, onChange }: WorldTabsProps) {
  return (
    <div className="ah-tabs" role="tablist" aria-label="جهان معامله" data-world-tabs="">
      {(["REAL_PAPER", "SIMULATION"] as const).map((world) => {
        const selected = value === world;
        return (
          <button
            key={world}
            type="button"
            role="tab"
            aria-selected={selected}
            data-world={world}
            data-verb="tab"
            className={world === "SIMULATION" ? "ah-tab ah-tab--sim" : "ah-tab"}
            onClick={() => onChange(world)}
            title={`${WORLD_LABEL_FA[world]} · ${WORLD_LABEL_EN[world]} · ${PAPER_ONLY_CODE}`}
          >
            <span>{WORLD_LABEL_FA[world]}</span>
            <span className="ah-tab__en" dir="ltr">
              {WORLD_LABEL_EN[world]}
            </span>
          </button>
        );
      })}
    </div>
  );
}

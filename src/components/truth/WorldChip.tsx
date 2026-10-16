import type { World } from "@/src/features/trade-venue/logic/model";
import { WORLD_LABEL_EN, WORLD_LABEL_FA } from "@/src/features/trade-venue/logic/model";

/**
 * World label chip — a *book name*, not a status.
 *
 * "REAL-PAPER" is not live data and "SIMULATION" is not a failure: labelling
 * either with a truth chip would tell the reader something false. So the world
 * gets its own neutral vocabulary (`data-world-chip`) that no status rule reads.
 */
export function WorldChip({ world, size = "sm" }: { world: World; size?: "sm" | "md" }) {
  return (
    <span
      className={size === "sm" ? "tv-chip tv-chip--sm tv-chip--world" : "tv-chip tv-chip--world"}
      data-chip=""
      data-world-chip={world}
      data-tone="info"
      data-live="false"
      dir="rtl"
      title={`دفتر: ${WORLD_LABEL_FA[world]} · ${WORLD_LABEL_EN[world]}`}
    >
      <span className="tv-chip__fa">{WORLD_LABEL_FA[world]}</span>
      <span className="tv-chip__code tv-chip__en" dir="ltr">
        {WORLD_LABEL_EN[world]}
      </span>
    </span>
  );
}

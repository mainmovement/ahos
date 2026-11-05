"use client";

import { useLocale } from "@/components/providers/locale-provider";
import { GlobeStage } from "@/components/visualization/globe/globe-stage";
import { SystemOverviewHud } from "./hud/system-overview-hud";
import { LiveFeedHud } from "./hud/live-feed-hud";
import { OpportunitiesHud } from "./hud/opportunities-hud";
import { HealthRingsHud } from "./hud/health-rings-hud";
import { MarketMiniChart } from "./hud/market-mini-chart";
import { AiIntelligencePrompt } from "./hud/ai-intelligence-prompt";

/**
 * Cinematic command stage: a large holographic Earth chamber with floating
 * HUD wings overlaid on the scene (xl+); below xl the same wings flow under
 * the stage. All panels read from lib/data envelopes only; the scene is
 * decorative and simulation-labeled.
 */
export function CommandStage() {
  const { dict } = useLocale();

  const leftWing = (
    <>
      <LiveFeedHud />
      <SystemOverviewHud />
    </>
  );
  const rightWing = (
    <>
      <HealthRingsHud />
      <OpportunitiesHud />
    </>
  );

  return (
    <section aria-label={dict.command.heroTitle} className="relative">
      <GlobeStage className="h-[clamp(560px,76vh,840px)]" />

      {/* floating overlays on xl+ */}
      <div className="pointer-events-none absolute inset-0 z-20 hidden xl:block">
        <div className="pointer-events-auto absolute start-5 top-16 flex w-[236px] flex-col gap-4">
          {leftWing}
        </div>
        <div className="pointer-events-auto absolute end-5 top-16 flex w-[236px] flex-col gap-4">
          {rightWing}
        </div>
      </div>

      {/* stacked wings under the stage below xl */}
      <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2 xl:hidden">
        <div className="flex flex-col gap-4">{leftWing}</div>
        <div className="flex flex-col gap-4">{rightWing}</div>
      </div>

      {/* rich panels flow below the chamber */}
      <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2">
        <MarketMiniChart />
        <AiIntelligencePrompt />
      </div>
    </section>
  );
}

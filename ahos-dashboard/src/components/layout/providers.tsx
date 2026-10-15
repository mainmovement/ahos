"use client";

import type { ReactNode } from "react";
import { Direction } from "radix-ui";
import { SettingsProvider, useSettings } from "@/lib/settings/provider";
import type { Settings } from "@/lib/settings/types";
import { TooltipProvider } from "@/components/ui/tooltip";

function DirectionBridge({ children }: { children: ReactNode }) {
  const { dir } = useSettings();
  return (
    <Direction.Provider dir={dir}>
      <TooltipProvider delayDuration={250} skipDelayDuration={150}>
        {children}
      </TooltipProvider>
    </Direction.Provider>
  );
}

export function AppProviders({ initialSettings, children }: { initialSettings: Partial<Settings>; children: ReactNode }) {
  return (
    <SettingsProvider initial={initialSettings}>
      <DirectionBridge>{children}</DirectionBridge>
    </SettingsProvider>
  );
}

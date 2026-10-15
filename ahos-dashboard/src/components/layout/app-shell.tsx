"use client";

import type { ReactNode } from "react";
import type { AppNotification } from "@/lib/api/types";
import { useI18n } from "@/lib/i18n";
import { useSoundSync } from "@/lib/audio/use-sound";
import { AmbientParticles } from "./ambient-particles";
import { AssistantColumn, type AssistantData } from "./assistant-column";
import { CommandPalette } from "./command-palette";
import { PaletteProvider } from "./palette-context";
import { Sidebar } from "./sidebar";
import { Topbar } from "./topbar";
import type { NavItemKey } from "./nav-config";

export interface ShellData {
  badges: Partial<Record<NavItemKey, number>>;
  notifications: AppNotification[];
  assistant: AssistantData;
}

/**
 * Desktop-app shell: [sidebar @ inline-start] [topbar + main] [Kian column @ inline-end].
 * In RTL the sidebar sits on the right and the Kian column on the left.
 */
export function AppShell({ data, children }: { data: ShellData; children: ReactNode }) {
  const { t } = useI18n();
  useSoundSync();
  return (
    <PaletteProvider>
      <a href="#main" className="skip-link">
        {t.app.skipToContent}
      </a>
      <AmbientParticles />
      <div aria-hidden className="bg-grid pointer-events-none fixed inset-0 z-0" />
      <div aria-hidden className="bg-noise pointer-events-none fixed inset-0 z-0 opacity-60" />
      <div className="relative z-10 flex h-dvh overflow-hidden">
        <Sidebar badges={data.badges} />
        <div className="flex min-w-0 flex-1 flex-col">
          <Topbar notifications={data.notifications} />
          <div className="flex min-h-0 flex-1">
            <main id="main" tabIndex={-1} className="@container min-w-0 flex-1 overflow-y-auto overflow-x-hidden outline-none">
              {children}
            </main>
            <AssistantColumn data={data.assistant} />
          </div>
        </div>
      </div>
      <CommandPalette />
    </PaletteProvider>
  );
}

'use client';

import KBar from '@/components/kbar';
import AppSidebar from '@/components/app-sidebar';
import Header from '@/components/header';
import { InfoSidebar } from '@/components/info-sidebar';
import { InfobarProvider } from '@/components/ui/infobar';
import { SidebarInset, SidebarProvider } from '@/components/ui/sidebar';
import { TelemetryStrips } from '@/components/shell/TelemetryStrips';

/**
 * AHOS command-center shell, composed from the ported template's layout
 * primitives (MASTER_SPEC "template first" + "Layout to match").
 *
 * What the template's version did that this one does not:
 *  - `auth.protect()` — AHOS has no Clerk. The whole app already runs behind the
 *    launcher's bootstrap token; the API refuses unauthenticated callers itself
 *    (`web_api_auth`), so the shell renders and the data simply does not arrive.
 *  - The cookie read for `sidebar_state` happens in the server `app` layout.
 *
 * Everything else is the template's own composition: skip-link, sidebar,
 * header, infobar drawer, right info rail.
 */
export function AhosShell({ children }: { children: React.ReactNode }) {
  return (
    <KBar>
      <SidebarProvider>
        <a
          href='#main-content'
          className='sr-only rounded-md bg-background px-3 py-2 text-sm font-medium text-foreground shadow ring-2 ring-ring focus:not-sr-only focus:absolute focus:top-2 focus:start-2 focus:z-50'
        >
          Skip to content
        </a>
        <AppSidebar />
        <SidebarInset id='main-content' tabIndex={-1} className='scroll-mt-16'>
          <Header />
          <InfobarProvider defaultOpen={false}>
            {children}
            <InfoSidebar side='right' />
          </InfobarProvider>
          {/* Room for the pinned strip bar below so the page's own footer is
              never hidden under it. */}
          <div className='h-44 shrink-0' aria-hidden='true' />
          {/* M-D7 / SOLTAN item 3: the bottom telemetry strips — run, gates,
              spend, ledger. They fetch /api/command themselves and present the
              local M13 paper soak (labelled, with its own staleness) whenever
              the engine is not fresh, so the UNKNOWN cards read real data. The
              template port left these in the retired DashiShell; the main
              screen gets them back here. Pinned to the viewport bottom because
              this template's page is taller than the Dashi shell ever was —
              in-flow, the owner's window would scroll past the only place the
              soak is visible. */}
          <div className='fixed inset-x-0 bottom-0 z-40 border-t border-border/60'>
            <TelemetryStrips />
          </div>
        </SidebarInset>
      </SidebarProvider>
    </KBar>
  );
}

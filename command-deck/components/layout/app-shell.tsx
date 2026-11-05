"use client";

import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import { usePathname } from "next/navigation";
import { Database } from "lucide-react";
import { useLocale } from "@/components/providers/locale-provider";
import { Sidebar, SidebarNav } from "./sidebar";
import { TopBar } from "./topbar";
import { CommandPalette } from "./command-palette";
import { NAV_ITEMS } from "@/lib/nav";
import { DATASET } from "@/lib/data/config";
import { Emblem } from "@/components/brand/emblem";
import { Sheet, SheetContent, SheetTitle } from "@/components/ui/sheet";

const RAIL_KEY = "ahos-deck-rail-collapsed";

export function AppShell({ children }: { children: ReactNode }) {
  const { locale, dict } = useLocale();
  const pathname = usePathname() ?? `/${locale}`;
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [paletteOpen, setPaletteOpen] = useState(false);

  useEffect(() => {
    try {
      setCollapsed(window.localStorage.getItem(RAIL_KEY) === "1");
    } catch {
      /* ignore */
    }
  }, []);

  const toggleRail = useCallback(() => {
    setCollapsed((prev) => {
      const next = !prev;
      try {
        window.localStorage.setItem(RAIL_KEY, next ? "1" : "0");
      } catch {
        /* ignore */
      }
      return next;
    });
  }, []);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setPaletteOpen((v) => !v);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const activeId = useMemo(() => {
    const base = `/${locale}`;
    if (pathname === base) return "commandCenter";
    const item = NAV_ITEMS.find(
      (i) => i.path !== "" && pathname.startsWith(`${base}${i.path}`),
    );
    return item?.id ?? "commandCenter";
  }, [pathname, locale]);

  const closeMobile = useCallback(() => setMobileOpen(false), []);

  return (
    <div className="relative flex min-h-dvh">
      {/* ambient background layer */}
      <div aria-hidden className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
        <div className="absolute -top-40 start-[-10%] size-[480px] rounded-full bg-primary/[0.05] blur-3xl" />
        <div className="absolute bottom-[-20%] end-[-8%] size-[520px] rounded-full bg-accent/[0.05] blur-3xl" />
        <div className="absolute inset-x-0 top-0 h-[420px] grid-bg opacity-70" />
      </div>

      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:start-4 focus:top-4 focus:z-[100] focus:rounded-lg focus:bg-primary focus:px-3 focus:py-2 focus:text-sm focus:font-bold focus:text-primary-foreground"
      >
        {dict.common.skipToContent}
      </a>

      <Sidebar collapsed={collapsed} onToggle={toggleRail} activeId={activeId} />

      <div className="flex min-w-0 flex-1 flex-col">
        <TopBar
          activeId={activeId}
          onOpenMenu={() => setMobileOpen(true)}
          onOpenPalette={() => setPaletteOpen(true)}
        />
        <main
          id="main-content"
          tabIndex={-1}
          className="mx-auto w-full max-w-[1440px] flex-1 px-4 pb-16 pt-6 md:px-6 lg:px-8"
        >
          {children}
        </main>
        <footer className="border-t border-border/60 bg-panel/40">
          <div className="mx-auto flex w-full max-w-[1440px] flex-wrap items-center gap-x-4 gap-y-2 px-4 py-4 text-[11px] text-muted-foreground md:px-6 lg:px-8">
            <span className="inline-flex items-center gap-1.5">
              <Database className="size-3.5 text-violet" aria-hidden />
              <span>
                {dict.strip.dataset}: <span className="font-mono" dir="ltr">{DATASET.id}</span>
              </span>
            </span>
            <span className="tnum">
              {dict.common.asOf}: <span className="font-mono" dir="ltr">{DATASET.asOf} (UTC)</span>
            </span>
            <span className="ms-auto">{dict.common.footerNote}</span>
          </div>
        </footer>
      </div>

      {/* mobile navigation */}
      <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
        <SheetContent side="start" className="panel rounded-e-2xl p-0">
          <SheetTitle className="sr-only">{dict.nav.openMenu}</SheetTitle>
          <div className="flex items-center gap-3 border-b border-border/60 px-4 py-4">
            <Emblem className="size-8" animated={false} />
            <span className="flex flex-col leading-tight">
              <span className="gold-text text-base font-extrabold" dir="ltr">AHOS</span>
              <span className="text-[9px] font-semibold uppercase tracking-[0.16em] text-muted-foreground" dir="ltr">
                Command Deck
              </span>
            </span>
          </div>
          <div className="flex-1 overflow-y-auto px-2 py-3">
            <SidebarNav activeId={activeId} onNavigate={closeMobile} />
          </div>
        </SheetContent>
      </Sheet>

      <CommandPalette open={paletteOpen} onOpenChange={setPaletteOpen} />
    </div>
  );
}

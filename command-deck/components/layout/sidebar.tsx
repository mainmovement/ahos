"use client";

import Link from "next/link";
import { PanelLeftClose, PanelLeftOpen } from "lucide-react";
import { useLocale } from "@/components/providers/locale-provider";
import { NAV_GROUPS, NAV_ITEMS, navHref, type NavItem } from "@/lib/nav";
import { cn } from "@/lib/utils";
import { Emblem } from "@/components/brand/emblem";
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { DATASET } from "@/lib/data/config";

export function Sidebar({
  collapsed,
  onToggle,
  activeId,
}: {
  collapsed: boolean;
  onToggle: () => void;
  activeId: string;
}) {
  const { dict, locale } = useLocale();
  return (
    <aside
      className={cn(
        "sticky top-0 z-30 hidden h-dvh shrink-0 flex-col border-e border-border/70 bg-panel/70 backdrop-blur-sm transition-[width] duration-200 lg:flex",
        collapsed ? "w-[68px]" : "w-60",
      )}
    >
      <div className={cn("flex items-center gap-3 border-b border-border/60 px-4 py-4", collapsed && "justify-center px-0")}>
        <Link href={navHref(locale, "")} className="flex items-center gap-3" aria-label={dict.common.appName}>
          <Emblem className="size-9 shrink-0" animated={false} />
          {!collapsed ? (
            <span className="flex flex-col leading-tight">
              <span className="gold-text text-base font-extrabold" dir="ltr">AHOS</span>
              <span className="text-[9px] font-semibold uppercase tracking-[0.16em] text-muted-foreground" dir="ltr">
                Command Deck
              </span>
            </span>
          ) : null}
        </Link>
      </div>

      <nav aria-label={dict.common.appName} className="flex-1 overflow-y-auto px-2.5 py-4">
        <SidebarNav activeId={activeId} collapsed={collapsed} />
      </nav>

      <div className="border-t border-border/60 px-2.5 py-3">
        {!collapsed ? (
          <p className="mb-2 px-2 text-[10px] leading-relaxed text-subtle tnum" dir="ltr">
            PAPER-ONLY · {DATASET.id}
          </p>
        ) : null}
        <Button
          variant="ghost"
          size={collapsed ? "icon" : "sm"}
          onClick={onToggle}
          className="w-full justify-start text-muted-foreground"
          aria-label={collapsed ? dict.nav.expandRail : dict.nav.collapseRail}
        >
          {collapsed ? <PanelLeftOpen /> : <PanelLeftClose />}
          {!collapsed ? <span className="text-xs">{dict.nav.collapseRail}</span> : null}
        </Button>
      </div>
    </aside>
  );
}

export function SidebarNav({
  activeId,
  collapsed = false,
  onNavigate,
}: {
  activeId: string;
  collapsed?: boolean;
  onNavigate?: () => void;
}) {
  const { dict } = useLocale();
  return (
    <div className="flex flex-col gap-4">
      {NAV_GROUPS.map((group) => (
        <div key={group}>
          {!collapsed ? (
            <p className="mb-1.5 px-2 text-[10px] font-bold uppercase tracking-[0.14em] text-subtle" dir="ltr">
              {dict.nav[group === "command" ? "groupCommand" : group === "analysis" ? "groupAnalysis" : "groupSystem"]}
            </p>
          ) : (
            <div className="mx-auto mb-2 h-px w-6 bg-border" aria-hidden />
          )}
          <ul className="flex flex-col gap-0.5">
            {NAV_ITEMS.filter((i) => i.group === group).map((item) => (
              <SidebarItem
                key={item.id}
                item={item}
                active={activeId === item.id}
                collapsed={collapsed}
                onNavigate={onNavigate}
              />
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}

function SidebarItem({
  item,
  active,
  collapsed,
  onNavigate,
}: {
  item: NavItem;
  active: boolean;
  collapsed: boolean;
  onNavigate?: () => void;
}) {
  const { dict, locale } = useLocale();
  const Icon = item.icon;
  const label = dict.nav[item.id];
  const content = (
    <>
      {active ? (
        <span aria-hidden className="absolute inset-y-1 start-0 w-0.5 rounded-full bg-primary" />
      ) : null}
      <Icon className={cn("size-[18px] shrink-0", active ? "text-primary" : "text-muted-foreground")} />
      {!collapsed ? <span className="truncate text-[13px] font-semibold">{label}</span> : <span className="sr-only">{label}</span>}
    </>
  );

  const link = (
    <Link
      href={navHref(locale, item.path)}
      onClick={onNavigate}
      aria-current={active ? "page" : undefined}
      title={collapsed ? label : undefined}
      className={cn(
        "relative flex items-center gap-3 rounded-xl px-3 py-2 transition-colors",
        active
          ? "bg-primary/10 text-primary"
          : "text-muted-foreground hover:bg-muted/70 hover:text-foreground",
        collapsed && "justify-center px-0",
      )}
    >
      {content}
    </Link>
  );

  if (collapsed) {
    return (
      <li>
        <Tooltip>
          <TooltipTrigger asChild>{link}</TooltipTrigger>
          <TooltipContent side="bottom">{label}</TooltipContent>
        </Tooltip>
      </li>
    );
  }
  return <li>{link}</li>;
}

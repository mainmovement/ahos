"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ChevronDown, Lock, PanelRightClose, PanelRightOpen } from "lucide-react";
import { useI18n } from "@/lib/i18n";
import { useSettings } from "@/lib/settings/provider";
import { useFormat } from "@/lib/format";
import { useSound } from "@/lib/audio/use-sound";
import { cn } from "@/lib/utils";
import { Tip } from "@/components/ui/tooltip";
import { AhosLogo } from "./logo";
import { NAV, isActive, type NavGroupKey, type NavItemKey } from "./nav-config";

export function Sidebar({ badges }: { badges: Partial<Record<NavItemKey, number>> }) {
  const { t, dir } = useI18n();
  const f = useFormat();
  const pathname = usePathname();
  const { settings, update } = useSettings();
  const play = useSound();
  const collapsed = settings.sidebarCollapsed;
  const [closed, setClosed] = useState<Partial<Record<NavGroupKey, boolean>>>({});
  const tipSide = dir === "rtl" ? "left" : "right";
  const CollapseIcon = collapsed ? (dir === "rtl" ? PanelRightOpen : PanelRightClose) : dir === "rtl" ? PanelRightClose : PanelRightOpen;

  return (
    <aside
      className={cn(
        "relative z-20 flex h-dvh shrink-0 flex-col border-e border-[var(--line-hairline)] bg-[image:var(--surface-sidebar)] transition-[width] duration-[var(--dur-slow)] ease-[var(--ease-out-expo)]",
        collapsed ? "w-[var(--sidebar-w-collapsed)]" : "w-[var(--sidebar-w)]",
      )}
    >
      {/* gold hairline on the inner edge */}
      <div aria-hidden className="hairline-y pointer-events-none absolute inset-y-0 end-0 opacity-60" />

      {/* Brand */}
      <div className={cn("flex h-[var(--topbar-h)] shrink-0 items-center gap-2.5 border-b border-[var(--line-subtle)]", collapsed ? "justify-center px-0" : "px-4")}>
        <Link href="/" aria-label={`${t.app.name} — ${t.nav.items.commandCenter}`} className="rounded-full">
          <AhosLogo size={collapsed ? 34 : 38} />
        </Link>
        {!collapsed && (
          <div className="min-w-0 leading-tight">
            <div className="text-gold-gradient text-[1.05rem] font-bold tracking-[0.22em]" dir="ltr">
              AHOS
            </div>
            <div className="truncate text-3xs text-fg-4">{t.app.tagline}</div>
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav aria-label={t.nav.label} className="min-h-0 flex-1 overflow-y-auto overflow-x-hidden px-2 py-2">
        {NAV.map((group) => {
          const isClosed = !collapsed && closed[group.key];
          const listId = `nav-group-${group.key}`;
          return (
            <div key={group.key} className="mb-1.5">
              {collapsed ? (
                <div aria-hidden className="hairline-x mx-2 my-2 opacity-50" />
              ) : (
                <button
                  type="button"
                  aria-expanded={!isClosed}
                  aria-controls={listId}
                  onClick={() => setClosed((c) => ({ ...c, [group.key]: !c[group.key] }))}
                  className="group flex w-full items-center gap-2 rounded-[var(--radius-sm)] px-2 py-1.5 text-3xs font-semibold uppercase tracking-[0.14em] text-fg-4 transition-colors hover:text-fg-2"
                >
                  <span className="truncate">{t.nav.groups[group.key]}</span>
                  <span aria-hidden className="hairline-x flex-1 opacity-40" />
                  <ChevronDown aria-hidden className={cn("size-3 shrink-0 transition-transform duration-[var(--dur-base)]", isClosed && "-rotate-90 rtl:rotate-90")} />
                </button>
              )}
              <ul id={listId} hidden={isClosed} className="space-y-0.5">
                {group.items.map((item) => {
                  const active = isActive(pathname, item.href);
                  const label = t.nav.items[item.key];
                  const badge = badges[item.key];
                  const Icon = item.icon;
                  const link = (
                    <Link
                      href={item.href}
                      aria-current={active ? "page" : undefined}
                      aria-label={collapsed ? (badge ? `${label} — ${t.nav.badge(f.num(badge, 0))}` : label) : undefined}
                      onClick={() => play("tick")}
                      className={cn(
                        "group/item relative flex h-8 items-center gap-2.5 rounded-[var(--radius-md)] text-sm transition-[background-color,color,box-shadow] duration-[var(--dur-fast)]",
                        collapsed ? "mx-auto w-10 justify-center" : "px-2.5",
                        active
                          ? "bg-[var(--surface-active)] text-gold-100 shadow-[inset_0_0_0_1px_rgb(230_191_95/0.22),var(--shadow-glow-sm)]"
                          : "text-fg-3 hover:bg-[var(--surface-hover)] hover:text-fg-1",
                      )}
                    >
                      {active && <span aria-hidden className="absolute inset-y-1.5 -start-2 w-[3px] rounded-full bg-[image:var(--gradient-gold)] shadow-[var(--shadow-glow-md)]" />}
                      <Icon
                        aria-hidden
                        className={cn("size-4 shrink-0 transition-colors", active ? "text-gold-300 drop-shadow-[0_0_6px_rgb(230_191_95/0.65)]" : "text-fg-4 group-hover/item:text-gold-300")}
                      />
                      {!collapsed && <span className="min-w-0 flex-1 truncate">{label}</span>}
                      {badge !== undefined && badge > 0 && !collapsed && (
                        <span className={cn("num shrink-0 rounded-full border px-1.5 text-3xs leading-4", active ? "border-gold-400/50 bg-gold-400/15 text-gold-100" : "border-white/10 bg-white/[0.04] text-fg-3")} aria-label={t.nav.badge(f.num(badge, 0))}>
                          {f.num(badge, 0)}
                        </span>
                      )}
                      {badge !== undefined && badge > 0 && collapsed && <span aria-hidden className="absolute end-1 top-1 size-1.5 rounded-full bg-gold-400 shadow-[var(--shadow-glow-sm)]" />}
                    </Link>
                  );
                  return (
                    <li key={item.key}>
                      {collapsed ? (
                        <Tip content={badge ? `${label} · ${f.num(badge, 0)}` : label} side={tipSide}>
                          {link}
                        </Tip>
                      ) : (
                        link
                      )}
                    </li>
                  );
                })}
              </ul>
            </div>
          );
        })}
      </nav>

      {/* Footer: paper-only lock + collapse */}
      <div className="shrink-0 border-t border-[var(--line-subtle)] p-2">
        {!collapsed ? (
          <Tip content={t.app.paperOnlyHint} side={tipSide}>
            <div tabIndex={0} className="mb-2 flex items-center gap-2 rounded-[var(--radius-md)] border border-gold-400/25 bg-gold-400/[0.06] px-2.5 py-2">
              <Lock aria-hidden className="size-3.5 shrink-0 text-gold-300" />
              <div className="min-w-0 leading-tight">
                <div className="text-2xs font-semibold text-gold-100">PAPER ONLY · {t.app.paperOnly}</div>
                <div className="truncate text-3xs text-fg-4">{t.app.paperOnlyHint}</div>
              </div>
            </div>
          </Tip>
        ) : (
          <Tip content={t.app.paperOnlyHint} side={tipSide}>
            <div tabIndex={0} className="mx-auto mb-2 flex size-9 items-center justify-center rounded-[var(--radius-md)] border border-gold-400/25 bg-gold-400/[0.06]" aria-label={t.app.paperOnly}>
              <Lock aria-hidden className="size-3.5 text-gold-300" />
            </div>
          </Tip>
        )}
        <Tip content={collapsed ? t.nav.expand : t.nav.collapse} side={tipSide}>
          <button
            type="button"
            onClick={() => {
              update({ sidebarCollapsed: !collapsed });
              play("tick");
            }}
            aria-label={collapsed ? t.nav.expand : t.nav.collapse}
            aria-expanded={!collapsed}
            className={cn("flex h-8 items-center gap-2 rounded-[var(--radius-md)] text-xs text-fg-4 transition-colors hover:bg-[var(--surface-hover)] hover:text-fg-1", collapsed ? "mx-auto w-9 justify-center" : "w-full px-2.5")}
          >
            <CollapseIcon aria-hidden className="size-4" />
            {!collapsed && <span>{t.nav.collapse}</span>}
          </button>
        </Tip>
      </div>
    </aside>
  );
}

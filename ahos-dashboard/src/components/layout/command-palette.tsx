"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Command } from "cmdk";
import { Bot, Bitcoin, Gauge, Globe2, Languages, Newspaper, PanelLeft, PanelRight, Search, Volume2 } from "lucide-react";
import type { SearchEntry } from "@/lib/api/types";
import { getSearchIndex } from "@/lib/api/search";
import { useI18n } from "@/lib/i18n";
import { useSettings } from "@/lib/settings/provider";
import { useSound } from "@/lib/audio/use-sound";
import { Dialog, DialogContent, DialogDescription, DialogTitle } from "@/components/ui/dialog";
import { Kbd } from "@/components/ui/primitives";
import { ALL_NAV_ITEMS } from "./nav-config";
import { sendGlobeCommand, usePalette } from "./palette-context";

const KIND_ICON = { instrument: Bitcoin, token: Search, agent: Bot, news: Newspaper } as const;

const itemCls =
  "flex cursor-pointer items-center gap-2.5 rounded-[var(--radius-md)] px-2.5 py-2 text-sm text-fg-2 outline-none transition-colors [&_svg]:size-4 [&_svg]:shrink-0 [&_svg]:text-fg-4 data-[selected=true]:[&_svg]:text-gold-300";

export function CommandPalette() {
  const { open, setOpen } = usePalette();
  const { t, l, locale } = useI18n();
  const { settings, update } = useSettings();
  const router = useRouter();
  const play = useSound();
  const [index, setIndex] = useState<SearchEntry[] | null>(null);

  useEffect(() => {
    if (!open || index) return;
    let alive = true;
    void getSearchIndex().then((r) => {
      if (alive) setIndex(r.data);
    });
    return () => {
      alive = false;
    };
  }, [open, index]);

  const run = (fn: () => void) => {
    fn();
    play("tick");
    setOpen(false);
  };

  const groups: { key: SearchEntry["kind"]; heading: string }[] = [
    { key: "instrument", heading: t.palette.instruments },
    { key: "token", heading: t.palette.tokens },
    { key: "agent", heading: t.palette.agents },
    { key: "news", heading: t.palette.news },
  ];

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogContent hideClose className="overflow-hidden p-0">
        <DialogTitle className="sr-only">{t.palette.title}</DialogTitle>
        <DialogDescription className="sr-only">{t.palette.hint}</DialogDescription>
        <Command label={t.palette.title} loop className="flex flex-col">
          <div className="flex items-center gap-2.5 border-b border-[var(--line-hairline)] px-4">
            <Search aria-hidden className="size-4 text-gold-300" />
            <Command.Input autoFocus placeholder={t.palette.placeholder} className="h-12 flex-1 bg-transparent text-sm text-fg-1 placeholder:text-fg-5 focus:outline-none focus-visible:shadow-none" />
            <Kbd>Esc</Kbd>
          </div>
          <Command.List className="max-h-[52vh] overflow-y-auto p-1.5">
            <Command.Empty className="py-10 text-center text-sm text-fg-4">{t.palette.empty}</Command.Empty>

            <Command.Group heading={t.palette.actions}>
              <Command.Item className={itemCls} value={`lang ${t.palette.toggleLanguage}`} onSelect={() => run(() => update({ locale: locale === "fa" ? "en" : "fa" }))}>
                <Languages aria-hidden />
                {t.palette.toggleLanguage}
              </Command.Item>
              <Command.Item className={itemCls} value={`sound ${t.palette.toggleSound}`} onSelect={() => run(() => update({ muted: !settings.muted }))}>
                <Volume2 aria-hidden />
                {t.palette.toggleSound}
              </Command.Item>
              {(
                [
                  ["high", t.palette.qualityHigh],
                  ["balanced", t.palette.qualityBalanced],
                  ["low", t.palette.qualityLow],
                ] as const
              ).map(([q, label]) => (
                <Command.Item key={q} className={itemCls} value={`quality ${label}`} onSelect={() => run(() => update({ quality: q }))}>
                  <Gauge aria-hidden />
                  {label}
                </Command.Item>
              ))}
              <Command.Item
                className={itemCls}
                value={`iran globe ${t.palette.flyToIran}`}
                onSelect={() =>
                  run(() => {
                    if (window.location.pathname === "/" || window.location.pathname === "/earth") sendGlobeCommand("fly-iran");
                    else router.push("/earth?focus=iran");
                  })
                }
              >
                <Globe2 aria-hidden />
                {t.palette.flyToIran}
              </Command.Item>
              <Command.Item className={itemCls} value={`sidebar ${t.palette.toggleSidebar}`} onSelect={() => run(() => update({ sidebarCollapsed: !settings.sidebarCollapsed }))}>
                <PanelRight aria-hidden />
                {t.palette.toggleSidebar}
              </Command.Item>
              <Command.Item className={itemCls} value={`kian ${t.palette.toggleAssistant}`} onSelect={() => run(() => update({ assistantCollapsed: !settings.assistantCollapsed }))}>
                <PanelLeft aria-hidden />
                {t.palette.toggleAssistant}
              </Command.Item>
            </Command.Group>

            <Command.Group heading={t.palette.pages}>
              {ALL_NAV_ITEMS.map((item) => {
                const Icon = item.icon;
                return (
                  <Command.Item key={item.key} className={itemCls} value={`${t.nav.items[item.key]} ${item.href}`} onSelect={() => run(() => router.push(item.href))}>
                    <Icon aria-hidden />
                    <span className="flex-1">{t.nav.items[item.key]}</span>
                    <span dir="ltr" className="text-3xs text-fg-5">
                      {item.href}
                    </span>
                  </Command.Item>
                );
              })}
            </Command.Group>

            {index &&
              groups.map((g) => {
                const entries = index.filter((e) => e.kind === g.key);
                if (!entries.length) return null;
                const Icon = KIND_ICON[g.key];
                return (
                  <Command.Group key={g.key} heading={g.heading}>
                    {entries.map((e) => (
                      <Command.Item key={e.id} className={itemCls} value={`${e.label} ${e.sublabel.fa} ${e.sublabel.en}`} onSelect={() => run(() => router.push(e.href))}>
                        <Icon aria-hidden />
                        <bdi className="font-medium text-fg-1">{e.label}</bdi>
                        <span className="min-w-0 flex-1 truncate text-xs text-fg-4">{l(e.sublabel)}</span>
                      </Command.Item>
                    ))}
                  </Command.Group>
                );
              })}
          </Command.List>
          <div className="flex items-center gap-3 border-t border-[var(--line-subtle)] px-4 py-2 text-3xs text-fg-5">
            <span className="flex items-center gap-1" dir="ltr">
              <Kbd>↑</Kbd>
              <Kbd>↓</Kbd>
            </span>
            <span className="flex items-center gap-1" dir="ltr">
              <Kbd>Enter</Kbd>
            </span>
            <span>{t.palette.hint}</span>
          </div>
        </Command>
      </DialogContent>
    </Dialog>
  );
}

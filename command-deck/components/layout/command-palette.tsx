"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { usePathname } from "next/navigation";
import { Command } from "cmdk";
import { useTheme } from "next-themes";
import {
  Activity,
  Languages,
  LayoutGrid,
  Monitor,
  Moon,
  Newspaper,
  Radar,
  Rows3,
  Settings2,
  ShieldCheck,
  Sun,
  Table2,
} from "lucide-react";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { useLocale } from "@/components/providers/locale-provider";
import { useSettings } from "@/components/providers/settings-provider";
import { NAV_ITEMS, navHref } from "@/lib/nav";
import { localePath } from "@/lib/i18n/config";

const NAV_ICONS = {
  commandCenter: Radar,
  desks: LayoutGrid,
  positions: Table2,
  intelligence: Newspaper,
  readiness: ShieldCheck,
  health: Activity,
  settings: Settings2,
} as const;

export function CommandPalette({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const { locale, dict } = useLocale();
  const router = useRouter();
  const pathname = usePathname() ?? `/${locale}`;
  const { setTheme } = useTheme();
  const { prefs, setPref } = useSettings();
  const [search, setSearch] = useState("");

  useEffect(() => {
    if (!open) setSearch("");
  }, [open]);

  const go = (path: string) => {
    onOpenChange(false);
    router.push(navHref(locale, path));
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="top-[18%] max-w-xl translate-y-0 gap-0 overflow-hidden p-0">
        <DialogTitle className="sr-only">{dict.common.commandPalette}</DialogTitle>
        <Command label={dict.common.commandPalette} shouldFilter loop>
          <Command.Input
            value={search}
            onValueChange={setSearch}
            placeholder={dict.palette.placeholder}
            className="w-full border-b border-border bg-transparent px-4 py-3.5 text-sm outline-none placeholder:text-muted-foreground/60"
          />
          <Command.List className="max-h-[46vh] overflow-y-auto p-2">
            <Command.Empty className="px-3 py-6 text-center text-xs text-muted-foreground">
              {dict.palette.empty}
            </Command.Empty>

            <Command.Group
              heading={dict.palette.navigate}
              className="px-1 py-1 text-[10px] font-bold uppercase tracking-wider text-subtle [&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5"
            >
              {NAV_ITEMS.map((item) => {
                const Icon = NAV_ICONS[item.id];
                return (
                  <Command.Item
                    key={item.id}
                    value={`nav ${dict.nav[item.id]} ${item.path}`}
                    onSelect={() => go(item.path)}
                    className="flex cursor-pointer items-center gap-2.5 rounded-lg px-3 py-2.5 text-[13px] font-semibold text-foreground data-[selected=true]:bg-primary/15 data-[selected=true]:text-primary"
                  >
                    <Icon className="size-4 text-muted-foreground" aria-hidden />
                    {dict.nav[item.id]}
                  </Command.Item>
                );
              })}
            </Command.Group>

            <Command.Group
              heading={dict.palette.preferences}
              className="px-1 py-1 text-[10px] font-bold uppercase tracking-wider text-subtle [&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-1.5"
            >
              <Command.Item
                value={`theme dark ${dict.common.themeDark}`}
                onSelect={() => {
                  setTheme("dark");
                  onOpenChange(false);
                }}
                className="palette-item"
              >
                <Moon className="size-4 text-muted-foreground" aria-hidden />
                {dict.palette.themeLabel}: {dict.common.themeDark}
              </Command.Item>
              <Command.Item
                value={`theme light ${dict.common.themeLight}`}
                onSelect={() => {
                  setTheme("light");
                  onOpenChange(false);
                }}
                className="palette-item"
              >
                <Sun className="size-4 text-muted-foreground" aria-hidden />
                {dict.palette.themeLabel}: {dict.common.themeLight}
              </Command.Item>
              <Command.Item
                value={`theme system ${dict.common.themeSystem}`}
                onSelect={() => {
                  setTheme("system");
                  onOpenChange(false);
                }}
                className="palette-item"
              >
                <Monitor className="size-4 text-muted-foreground" aria-hidden />
                {dict.palette.themeLabel}: {dict.common.themeSystem}
              </Command.Item>
              <Command.Item
                value={`language persian fa ${dict.common.persian}`}
                onSelect={() => {
                  onOpenChange(false);
                  router.push(localePath(pathname, "fa"));
                }}
                className="palette-item"
              >
                <Languages className="size-4 text-muted-foreground" aria-hidden />
                {dict.palette.languageLabel}: {dict.common.persian}
              </Command.Item>
              <Command.Item
                value={`language english en ${dict.common.english}`}
                onSelect={() => {
                  onOpenChange(false);
                  router.push(localePath(pathname, "en"));
                }}
                className="palette-item"
              >
                <Languages className="size-4 text-muted-foreground" aria-hidden />
                {dict.palette.languageLabel}: {dict.common.english}
              </Command.Item>
              <Command.Item
                value={`density compact ${dict.common.compact}`}
                onSelect={() => {
                  setPref("density", "compact");
                  onOpenChange(false);
                }}
                className="palette-item"
              >
                <Rows3 className="size-4 text-muted-foreground" aria-hidden />
                {dict.palette.densityLabel}: {dict.common.compact}
                {prefs.density === "compact" ? <span className="ms-auto text-primary">✓</span> : null}
              </Command.Item>
              <Command.Item
                value={`density comfortable ${dict.common.comfortable}`}
                onSelect={() => {
                  setPref("density", "comfortable");
                  onOpenChange(false);
                }}
                className="palette-item"
              >
                <Rows3 className="size-4 text-muted-foreground" aria-hidden />
                {dict.palette.densityLabel}: {dict.common.comfortable}
                {prefs.density === "comfortable" ? <span className="ms-auto text-primary">✓</span> : null}
              </Command.Item>
            </Command.Group>
          </Command.List>
        </Command>
      </DialogContent>
    </Dialog>
  );
}

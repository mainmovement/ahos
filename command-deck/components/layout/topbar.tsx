"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { useTheme } from "next-themes";
import {
  Bell,
  CircleCheck,
  CircleQuestionMark,
  CircleX,
  FlaskConical,
  Info,
  Languages,
  Lock,
  Menu,
  Monitor,
  Moon,
  Search,
  Sun,
  User,
} from "lucide-react";
import { useLocale } from "@/components/providers/locale-provider";
import { NAV_ITEMS, navHref } from "@/lib/nav";
import { localePath } from "@/lib/i18n/config";
import { commandStrip, STRIP_DATASET_LABEL } from "@/lib/data/strip";
import { DATASET } from "@/lib/data/config";
import { ALERTS } from "@/lib/data/alerts";
import { Button } from "@/components/ui/button";
import { Kbd } from "@/components/ui/misc";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { StatusBadge } from "@/components/status/status-badge";
import { cn } from "@/lib/utils";

export function TopBar({
  activeId,
  onOpenMenu,
  onOpenPalette,
}: {
  activeId: string;
  onOpenMenu: () => void;
  onOpenPalette: () => void;
}) {
  const { locale, dict } = useLocale();
  const pathname = usePathname() ?? `/${locale}`;
  const activeItem = NAV_ITEMS.find((i) => i.id === activeId);

  return (
    <header className="sticky top-0 z-40 border-b border-border/70 bg-background/85 backdrop-blur-md">
      <div className="flex h-14 items-center gap-2 px-3 md:px-5">
        <Button
          variant="ghost"
          size="icon"
          className="lg:hidden"
          onClick={onOpenMenu}
          aria-label={dict.nav.openMenu}
        >
          <Menu />
        </Button>

        <nav aria-label="breadcrumb" className="hidden min-w-0 items-center gap-2 text-sm sm:flex">
          <Link href={navHref(locale, "")} className="gold-text shrink-0 font-extrabold" dir="ltr">
            AHOS
          </Link>
          <span aria-hidden className="text-border-strong">/</span>
          <span className="truncate font-semibold">
            {activeItem ? dict.nav[activeItem.id] : dict.nav.commandCenter}
          </span>
        </nav>

        <div className="flex-1" />

        <button
          type="button"
          onClick={onOpenPalette}
          className="hidden h-9 w-52 items-center gap-2 rounded-xl border border-border-strong bg-muted/40 px-3 text-xs text-muted-foreground transition-colors hover:bg-muted/70 md:flex xl:w-64"
          aria-label={dict.common.commandPalette}
        >
          <Search className="size-3.5" aria-hidden />
          <span className="truncate">{dict.common.commandPalette}</span>
          <Kbd className="ms-auto">{dict.common.commandPaletteHint}</Kbd>
        </button>
        <Button
          variant="ghost"
          size="icon"
          className="md:hidden"
          onClick={onOpenPalette}
          aria-label={dict.common.commandPalette}
        >
          <Search />
        </Button>

        <SamplePill />
        <PaperBadge />
        <Notifications />
        <LanguageToggle pathname={pathname} />
        <ThemeToggle />
        <OperatorMenu />
      </div>
      <StatusStrip />
    </header>
  );
}

function PaperBadge() {
  const { dict } = useLocale();
  return (
    <span
      title={dict.common.paperOnlyLong}
      className="inline-flex select-none items-center gap-1.5 rounded-full border border-primary/50 bg-primary/10 px-2.5 py-1 text-[11px] font-extrabold tracking-wide text-primary"
    >
      <Lock className="size-3" aria-hidden />
      <span dir="ltr">{dict.common.paperOnly}</span>
    </span>
  );
}

function SamplePill() {
  const { dict } = useLocale();
  return (
    <span
      tabIndex={0}
      title={`${dict.common.datasetBannerTitle} ${dict.common.datasetBannerBody}`}
      className="group relative hidden select-none items-center gap-1.5 rounded-full border border-violet/50 bg-violet/10 px-2.5 py-1 text-[11px] font-bold text-violet sm:inline-flex"
    >
      <FlaskConical className="size-3" aria-hidden />
      {dict.common.sample}
      <span
        role="tooltip"
        className="pointer-events-none absolute bottom-full end-0 z-40 mb-1.5 hidden w-72 rounded-lg border border-border-strong bg-navy-900 p-2.5 text-[11px] font-normal leading-relaxed text-foreground shadow-panel group-focus-within:block group-hover:block light:bg-white"
      >
        <span className="tnum block font-mono text-[10px] text-violet" dir="ltr">
          {STRIP_DATASET_LABEL} · {DATASET.asOf}
        </span>
        <span className="mt-1 block">{dict.common.datasetBannerBody}</span>
      </span>
    </span>
  );
}

function LanguageToggle({ pathname }: { pathname: string }) {
  const { locale, dict } = useLocale();
  const next: "fa" | "en" = locale === "fa" ? "en" : "fa";
  const label = next === "fa" ? dict.common.persian : dict.common.english;
  return (
    <Button variant="ghost" size="sm" asChild aria-label={`${dict.common.language}: ${label}`}>
      <Link href={localePath(pathname, next)} className="gap-1.5 px-2">
        <Languages className="size-4 text-muted-foreground" aria-hidden />
        <span className="text-xs font-bold">{next === "fa" ? "فا" : "EN"}</span>
      </Link>
    </Button>
  );
}

function ThemeToggle() {
  const { dict } = useLocale();
  const { theme, setTheme } = useTheme();
  const options = [
    { id: "dark", icon: Moon, label: dict.common.themeDark },
    { id: "light", icon: Sun, label: dict.common.themeLight },
    { id: "system", icon: Monitor, label: dict.common.themeSystem },
  ] as const;

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" aria-label={dict.common.theme}>
          <Sun className="hidden dark:block" />
          <Moon className="dark:hidden" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuLabel>{dict.common.theme}</DropdownMenuLabel>
        {options.map((option) => (
          <DropdownMenuItem key={option.id} onSelect={() => setTheme(option.id)}>
            <option.icon />
            {option.label}
            {theme === option.id ? <CircleCheck className="ms-auto text-primary" /> : null}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

function OperatorMenu() {
  const { dict } = useLocale();
  return (
    <Popover>
      <PopoverTrigger asChild>
        <button
          type="button"
          className="inline-flex size-9 items-center justify-center rounded-full border border-border-strong bg-muted/50 text-muted-foreground transition-colors hover:text-foreground"
          aria-label={dict.common.operator}
        >
          <User className="size-4" aria-hidden />
        </button>
      </PopoverTrigger>
      <PopoverContent align="end" className="w-72">
        <div className="flex items-center gap-3">
          <span className="inline-flex size-10 items-center justify-center rounded-full bg-primary/15 text-primary">
            <User className="size-5" aria-hidden />
          </span>
          <div className="min-w-0">
            <p className="truncate text-sm font-bold">{dict.common.operator}</p>
            <p className="text-[11px] text-muted-foreground">{dict.common.operatorRole}</p>
          </div>
        </div>
        <p className="mt-3 border-t border-border/60 pt-3 text-[11px] leading-relaxed text-muted-foreground">
          {dict.settings.aboutBody}
        </p>
      </PopoverContent>
    </Popover>
  );
}

/* ------------------------------------------------------------------ */

const SEVERITY_STYLE = {
  INFO: { icon: Info, cls: "text-accent border-accent/40 bg-accent/5" },
  WARN: { icon: CircleQuestionMark, cls: "text-warning border-warning/40 bg-warning/5" },
  CRITICAL: { icon: CircleX, cls: "text-danger border-danger/40 bg-danger/5" },
} as const;

function Notifications() {
  const { locale, dict } = useLocale();
  const [readIds, setReadIds] = useState<string[]>([]);
  const unread = ALERTS.filter((a) => !readIds.includes(a.id)).length;

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button variant="ghost" size="icon" className="relative" aria-label={dict.common.notifications}>
          <Bell />
          {unread > 0 ? (
            <span
              className="absolute -end-0.5 -top-0.5 inline-flex size-4 items-center justify-center rounded-full bg-violet text-[9px] font-extrabold text-white"
              aria-hidden
            >
              {unread}
            </span>
          ) : null}
        </Button>
      </PopoverTrigger>
      <PopoverContent align="end" className="w-96 max-w-[92vw]">
        <p className="mb-3 text-sm font-bold">{dict.common.notifications}</p>
        <ul className="flex max-h-80 flex-col gap-2.5 overflow-y-auto">
          {ALERTS.map((alert) => {
            const read = readIds.includes(alert.id);
            const sev = SEVERITY_STYLE[alert.severity];
            return (
              <li key={alert.id} className={cn("rounded-xl border p-3", sev.cls, read && "opacity-55")}>
                <div className="flex items-start gap-2">
                  <sev.icon className="mt-0.5 size-4 shrink-0" aria-hidden />
                  <div className="min-w-0">
                    <p className="text-xs font-bold leading-relaxed">{alert.title[locale]}</p>
                    <p className="mt-0.5 text-[11px] leading-relaxed text-muted-foreground">
                      {alert.body[locale]}
                    </p>
                  </div>
                </div>
                <div className="mt-2 flex items-center justify-between gap-2">
                  <StatusBadge status={alert.provenance.status} size="sm" />
                  {read ? (
                    <span className="text-[10px] font-semibold text-subtle">
                      {dict.common.markRead} ✓
                    </span>
                  ) : (
                    <button
                      type="button"
                      onClick={() => setReadIds((prev) => [...prev, alert.id])}
                      className="rounded-lg px-2 py-1 text-[11px] font-semibold text-muted-foreground hover:bg-muted hover:text-foreground"
                    >
                      {dict.common.markRead}
                    </button>
                  )}
                </div>
              </li>
            );
          })}
        </ul>
      </PopoverContent>
    </Popover>
  );
}

/* ------------------------------------------------------------------ */

function StatusStrip() {
  const { dict } = useLocale();
  const items = commandStrip();
  const labels: Record<string, string> = {
    execution: dict.strip.executionMode,
    killSwitch: dict.strip.killSwitch,
    soak: dict.strip.soakWindow,
    api: dict.strip.api,
    dashboard: dict.strip.dashboard,
    ram: dict.strip.freeRam,
    dataset: dict.strip.dataset,
  };

  return (
    <div
      role="region"
      aria-label={dict.common.provenance}
      className="flex items-center gap-4 overflow-x-auto border-t border-border/60 bg-panel/50 px-3 py-1.5 md:px-5"
    >
      {items.map((item) => (
        <span key={item.id} className="inline-flex shrink-0 items-center gap-1.5 text-[11px]">
          <span className="whitespace-nowrap text-muted-foreground">{labels[item.id]}</span>
          {item.id === "execution" ? (
            <span className="whitespace-nowrap font-bold text-danger" dir="ltr">
              {dict.strip.disabled}
            </span>
          ) : item.id === "dataset" ? (
            <span className="inline-flex items-center gap-1">
              <StatusBadge status="SAMPLE" size="sm" />
              <span className="font-mono text-[10px] text-violet" dir="ltr">
                {STRIP_DATASET_LABEL}
              </span>
            </span>
          ) : (
            <StatusBadge status={item.status} size="sm" />
          )}
        </span>
      ))}
      <span className="ms-auto hidden shrink-0 text-[10px] text-subtle tnum md:block" dir="ltr">
        UTC {DATASET.asOf.slice(11, 16)}
      </span>
    </div>
  );
}

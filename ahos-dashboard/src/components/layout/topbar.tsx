"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { Bell, CircleUser, Gauge, Keyboard, Lock, LogOut, Search, Settings2, Volume2, VolumeX } from "lucide-react";
import type { AppNotification } from "@/lib/api/types";
import { useI18n } from "@/lib/i18n";
import { useFormat } from "@/lib/format";
import { useSettings } from "@/lib/settings/provider";
import { useSound } from "@/lib/audio/use-sound";
import { useNow, useNowMinute } from "@/lib/time/now";
import { allSessions, formatCountdown } from "@/lib/time/sessions";
import type { QualityProfile } from "@/lib/settings/types";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Kbd, TimeAgo } from "@/components/ui/primitives";
import { Segmented } from "@/components/ui/segmented";
import { Tip } from "@/components/ui/tooltip";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { severityIcon } from "@/components/ui/status";
import { usePalette } from "./palette-context";

export function Topbar({ notifications }: { notifications: AppNotification[] }) {
  return (
    <header className="relative z-10 flex h-[var(--topbar-h)] shrink-0 items-center gap-2 border-b border-[var(--line-hairline)] bg-ink-950/55 px-3 backdrop-blur-[var(--glass-blur)]">
      <SearchTrigger />
      <PaperOnlyPill />
      <div className="min-w-2 flex-1" />
      <Clocks />
      <Sessions />
      <div aria-hidden className="hairline-y mx-0.5 h-6 opacity-50" />
      <QualityMenu />
      <SoundToggle />
      <LanguageSwitch />
      <Notifications items={notifications} />
      <UserMenu />
    </header>
  );
}

function SearchTrigger() {
  const { t } = useI18n();
  const { setOpen } = usePalette();
  const play = useSound();
  return (
    <button
      type="button"
      onClick={() => {
        setOpen(true);
        play("open");
      }}
      aria-label={`${t.topbar.search} (Ctrl+K)`}
      aria-haspopup="dialog"
      className="group flex h-8 w-[min(300px,24vw)] min-w-[150px] items-center gap-2 rounded-[var(--radius-md)] border border-[var(--line-subtle)] bg-[var(--surface-input)] px-2.5 text-start text-xs text-fg-4 transition-colors hover:border-gold-400/40 hover:text-fg-2"
    >
      <Search aria-hidden className="size-3.5 shrink-0 text-fg-4 group-hover:text-gold-300" />
      <span className="min-w-0 flex-1 truncate">{t.topbar.search}</span>
      <span className="hidden shrink-0 items-center gap-0.5 lg:flex" dir="ltr">
        <Kbd>Ctrl</Kbd>
        <Kbd>K</Kbd>
      </span>
    </button>
  );
}

function PaperOnlyPill() {
  const { t } = useI18n();
  return (
    <Tip content={t.app.paperOnlyHint} side="bottom">
      <span tabIndex={0} className="hidden h-7 shrink-0 items-center gap-1.5 rounded-full border border-gold-400/30 bg-gold-400/[0.07] px-2.5 text-2xs font-semibold text-gold-100 shadow-[var(--shadow-glow-sm)] md:inline-flex">
        <Lock aria-hidden className="size-3 text-gold-300" />
        <span dir="ltr" className="tracking-wider">
          PAPER ONLY
        </span>
        <span className="hidden text-fg-3 xl:inline">· {t.app.paperOnly}</span>
      </span>
    </Tip>
  );
}

function Clocks() {
  const { t, tx } = useI18n();
  const f = useFormat();
  const now = useNow();
  const zones = [
    { id: "tehran", label: t.topbar.tehran, tz: "Asia/Tehran" },
    { id: "utc", label: t.topbar.utc, tz: "UTC" },
    { id: "local", label: t.topbar.local, tz: undefined as string | undefined },
  ];
  return (
    <div role="group" aria-label={tx("ساعت‌ها", "Clocks")} className="hidden items-center gap-3 xl:flex">
      {zones.map((z, i) => (
        <Tip key={z.id} content={now ? f.date(now, { timeZone: z.tz, withYear: true }) + (z.tz ? ` · ${z.tz}` : "") : null} side="bottom">
          <div tabIndex={0} className={cn("flex flex-col items-end leading-none", i === 2 && "hidden 2xl:flex")}>
            <span className="text-3xs text-fg-4">{z.label}</span>
            <span dir="ltr" className={cn("num mt-0.5 text-sm font-medium", z.id === "tehran" ? "text-gold-200" : "text-fg-2")} suppressHydrationWarning>
              {now ? f.time(now, { seconds: true, timeZone: z.tz }) : "--:--:--"}
            </span>
          </div>
        </Tip>
      ))}
    </div>
  );
}

function Sessions() {
  const { t, l, tx } = useI18n();
  const f = useFormat();
  const minute = useNowMinute();
  const states = useMemo(() => (minute === null ? [] : allSessions(new Date(minute), ["tse-ir", "tse-jp", "lse", "nyse", "crypto"])), [minute]);
  const openCount = states.filter((s) => s.open && !s.exchange.alwaysOpen).length;
  const pills = states.map((s) => {
    const cd = formatCountdown(s.minutesToChange);
    const tip = s.exchange.alwaysOpen
      ? `${l(s.exchange.name)} · ${t.topbar.alwaysOpen}`
      : `${l(s.exchange.name)} · ${s.open ? t.topbar.open : t.topbar.closed} · ${s.open ? t.topbar.closesIn(f.digits(cd)) : t.topbar.opensIn(f.digits(cd))}`;
    return (
      <Tip key={s.exchange.id} content={<span>{tip}<br /><span className="text-fg-4">{t.topbar.estimated}</span></span>} side="bottom">
        <span
          tabIndex={0}
          aria-label={tip}
          className={cn(
            "inline-flex h-6 items-center gap-1.5 rounded-full border px-2 text-3xs font-semibold tracking-wide",
            s.open ? "border-up/30 bg-up/[0.08] text-fg-1" : "border-white/10 bg-white/[0.02] text-fg-4",
          )}
        >
          <span aria-hidden className={cn("size-1.5 rounded-full", s.open ? "bg-up shadow-[0_0_6px_var(--color-up)]" : "border border-fg-4")} />
          <span dir="ltr">{s.exchange.short}</span>
          <span className="sr-only">{s.open ? t.topbar.open : t.topbar.closed}</span>
        </span>
      </Tip>
    );
  });
  return (
    <div role="group" aria-label={t.topbar.sessions} className="flex items-center">
      <div className="hidden items-center gap-1 2xl:flex">{pills}</div>
      <Popover>
        <Tip content={t.topbar.sessions} side="bottom">
          <PopoverTrigger asChild>
            <button type="button" className="inline-flex h-7 items-center gap-1.5 rounded-full border border-white/10 px-2.5 text-2xs text-fg-3 hover:text-fg-1 2xl:hidden" aria-label={t.topbar.sessions}>
              <span aria-hidden className={cn("size-1.5 rounded-full", openCount ? "bg-up" : "border border-fg-4")} />
              <span className="num" dir="ltr">
                {f.digits(`${openCount}/${Math.max(states.length - 1, 0)}`)}
              </span>
              <span className="hidden lg:inline">{tx("بازار باز", "open")}</span>
            </button>
          </PopoverTrigger>
        </Tip>
        <PopoverContent className="w-60 p-3">
          <div className="mb-2 text-xs font-semibold text-fg-1">{t.topbar.sessions}</div>
          <div className="flex flex-wrap gap-1">{pills}</div>
          <p className="mt-2 text-3xs text-fg-4">{t.topbar.estimated}</p>
        </PopoverContent>
      </Popover>
    </div>
  );
}

function QualityMenu() {
  const { t } = useI18n();
  const { settings, update } = useSettings();
  const play = useSound();
  const options: { v: QualityProfile; label: string; desc: string }[] = [
    { v: "high", label: t.quality.high, desc: t.quality.highDesc },
    { v: "balanced", label: t.quality.balanced, desc: t.quality.balancedDesc },
    { v: "low", label: t.quality.low, desc: t.quality.lowDesc },
  ];
  const current = options.find((o) => o.v === settings.quality)!;
  return (
    <DropdownMenu>
      <Tip content={`${t.topbar.quality}: ${current.label}`} side="bottom">
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" size="sm" aria-label={`${t.topbar.quality}: ${current.label}`} className="gap-1 px-2">
            <Gauge aria-hidden />
            <span className="hidden text-2xs 2xl:inline">{current.label}</span>
          </Button>
        </DropdownMenuTrigger>
      </Tip>
      <DropdownMenuContent align="end" className="w-64">
        <DropdownMenuLabel>{t.topbar.quality}</DropdownMenuLabel>
        <DropdownMenuRadioGroup
          value={settings.quality}
          onValueChange={(v) => {
            update({ quality: v as QualityProfile });
            play("tick");
          }}
        >
          {options.map((o) => (
            <DropdownMenuRadioItem key={o.v} value={o.v} className="items-start">
              <div className="leading-tight">
                <div className="text-sm text-fg-1">{o.label}</div>
                <div className="text-3xs text-fg-4">{o.desc}</div>
              </div>
            </DropdownMenuRadioItem>
          ))}
        </DropdownMenuRadioGroup>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

function SoundToggle() {
  const { t } = useI18n();
  const { settings, update } = useSettings();
  const muted = settings.muted;
  return (
    <Tip content={muted ? `${t.topbar.soundOff} — ${t.topbar.unmute}` : `${t.topbar.soundOn} — ${t.topbar.mute}`} side="bottom">
      <Button
        variant={muted ? "ghost" : "active"}
        size="icon-sm"
        aria-pressed={!muted}
        aria-label={muted ? t.topbar.unmute : t.topbar.mute}
        onClick={() => update({ muted: !muted })}
      >
        {muted ? <VolumeX aria-hidden /> : <Volume2 aria-hidden />}
      </Button>
    </Tip>
  );
}

function LanguageSwitch() {
  const { t } = useI18n();
  const { settings, update } = useSettings();
  const play = useSound();
  return (
    <Segmented
      label={t.topbar.language}
      size="xs"
      value={settings.locale}
      onChange={(v) => {
        update({ locale: v });
        play("tick");
      }}
      options={[
        { value: "fa", label: "فا", title: "فارسی" },
        { value: "en", label: "EN", title: "English" },
      ]}
    />
  );
}

function Notifications({ items }: { items: AppNotification[] }) {
  const { t, l } = useI18n();
  const f = useFormat();
  const play = useSound();
  const [readIds, setReadIds] = useState<Set<string>>(() => new Set(items.filter((i) => i.read).map((i) => i.id)));
  const unread = items.filter((i) => !readIds.has(i.id)).length;
  return (
    <Popover onOpenChange={(o) => o && play("open")}>
      <Tip content={t.topbar.notifications} side="bottom">
        <PopoverTrigger asChild>
          <Button variant="ghost" size="icon-sm" aria-label={`${t.topbar.notifications} — ${t.topbar.unread(f.num(unread, 0))}`} className="relative">
            <Bell aria-hidden />
            {unread > 0 && (
              <span aria-hidden className="num absolute -end-0.5 -top-0.5 flex h-3.5 min-w-3.5 items-center justify-center rounded-full bg-gold-400 px-0.5 text-[9px] font-bold text-ink-950 shadow-[var(--shadow-glow-sm)]">
                {f.num(unread, 0)}
              </span>
            )}
          </Button>
        </PopoverTrigger>
      </Tip>
      <PopoverContent className="w-[340px] p-0">
        <div className="flex items-center justify-between border-b border-[var(--line-subtle)] px-3 py-2.5">
          <div>
            <div className="text-sm font-semibold text-fg-1">{t.topbar.notifications}</div>
            <div className="text-3xs text-fg-4">{t.topbar.unread(f.num(unread, 0))}</div>
          </div>
          <Button variant="ghost" size="xs" disabled={unread === 0} onClick={() => setReadIds(new Set(items.map((i) => i.id)))}>
            {t.topbar.markAllRead}
          </Button>
        </div>
        <ul className="max-h-[360px] overflow-y-auto py-1" aria-live="polite">
          {items.length === 0 && <li className="px-3 py-6 text-center text-xs text-fg-4">{t.topbar.noNotifications}</li>}
          {items.map((n) => {
            const Icon = severityIcon(n.severity);
            const isUnread = !readIds.has(n.id);
            return (
              <li key={n.id}>
                <Link
                  href={n.href ?? "#"}
                  onClick={() => setReadIds((s) => new Set(s).add(n.id))}
                  className="flex gap-2.5 px-3 py-2 transition-colors hover:bg-[var(--surface-hover)]"
                >
                  <Icon aria-hidden className={cn("mt-0.5 size-4 shrink-0", n.severity === "HIGH" || n.severity === "CRITICAL" ? "text-warn" : n.severity === "MEDIUM" ? "text-gold-300" : "text-info")} />
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-1.5">
                      <span className={cn("truncate text-xs", isUnread ? "font-semibold text-fg-1" : "text-fg-2")}>{l(n.title)}</span>
                      {isUnread && <span aria-label="unread" className="size-1.5 shrink-0 rounded-full bg-gold-400" />}
                    </div>
                    <p className="truncate text-2xs text-fg-3">{l(n.body)}</p>
                    <TimeAgo iso={n.at} className="text-3xs text-fg-5" />
                  </div>
                </Link>
              </li>
            );
          })}
        </ul>
      </PopoverContent>
    </Popover>
  );
}

function UserMenu() {
  const { t } = useI18n();
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button type="button" aria-label={t.topbar.userMenu} className="flex h-9 items-center gap-2 rounded-[var(--radius-md)] ps-1 pe-2 transition-colors hover:bg-[var(--surface-hover)]">
          <span aria-hidden className="relative flex size-7 items-center justify-center rounded-full bg-[image:var(--gradient-gold)] p-[1.5px] shadow-[var(--shadow-glow-sm)]">
            <span className="flex size-full items-center justify-center rounded-full bg-ink-900 text-xs font-bold text-gold-200">م</span>
          </span>
          <span className="hidden text-start leading-tight xl:block">
            <span className="block text-xs font-medium text-fg-1">{t.app.operatorName}</span>
            <span className="block text-3xs text-fg-4">{t.app.operatorRole}</span>
          </span>
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuLabel>
          {t.app.operatorName} · {t.app.operatorRole}
        </DropdownMenuLabel>
        <DropdownMenuItem>
          <CircleUser aria-hidden />
          {t.topbar.profile}
        </DropdownMenuItem>
        <DropdownMenuItem asChild>
          <Link href="/settings">
            <Settings2 aria-hidden />
            {t.nav.items.settings}
          </Link>
        </DropdownMenuItem>
        <DropdownMenuItem>
          <Keyboard aria-hidden />
          {t.topbar.shortcuts}
          <span className="ms-auto flex gap-0.5" dir="ltr">
            <Kbd>Ctrl</Kbd>
            <Kbd>K</Kbd>
          </span>
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem disabled>
          <LogOut aria-hidden />
          {t.topbar.signOut}
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

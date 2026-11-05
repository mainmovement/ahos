"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTheme } from "next-themes";
import { Braces, Globe, Monitor, Moon, RotateCcw, Sun } from "lucide-react";
import { useLocale } from "@/components/providers/locale-provider";
import { DEFAULT_PREFS, useSettings } from "@/components/providers/settings-provider";
import { Panel, PanelContent, PanelHeader, PanelTitle, PanelDescription } from "@/components/ui/panel";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { localePath } from "@/lib/i18n/config";
import { DATASET } from "@/lib/data/config";
import { cn } from "@/lib/utils";
import type { RefreshInterval } from "@/lib/types";

function Segmented<T extends string>({
  value,
  options,
  onChange,
  label,
}: {
  value: T;
  options: Array<{ id: T; label: string }>;
  onChange: (v: T) => void;
  label: string;
}) {
  return (
    <div role="radiogroup" aria-label={label} className="inline-flex rounded-xl border border-border-strong bg-muted/40 p-0.5">
      {options.map((option) => (
        <button
          key={option.id}
          type="button"
          role="radio"
          aria-checked={value === option.id}
          onClick={() => onChange(option.id)}
          className={cn(
            "rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors",
            value === option.id ? "bg-primary/15 text-primary" : "text-muted-foreground hover:text-foreground",
          )}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}

export function SettingsForm() {
  const { dict, locale } = useLocale();
  const pathname = usePathname() ?? `/${locale}`;
  const { theme, setTheme } = useTheme();
  const { prefs, setPref, resetPrefs, hydrated } = useSettings();

  return (
    <div className="grid gap-4 xl:grid-cols-2">
      {/* language */}
      <Panel>
        <PanelHeader>
          <PanelTitle>{dict.settings.languageTitle}</PanelTitle>
          <PanelDescription>{dict.settings.languageDesc}</PanelDescription>
        </PanelHeader>
        <PanelContent className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-sm">
            <Globe className="size-4 text-muted-foreground" aria-hidden />
            <span className="font-semibold">{locale === "fa" ? dict.common.persian : dict.common.english}</span>
          </div>
          <div className="flex gap-2">
            <Button variant={locale === "fa" ? "solid" : "outline"} size="sm" asChild>
              <Link href={localePath(pathname, "fa")}>{dict.common.persian}</Link>
            </Button>
            <Button variant={locale === "en" ? "solid" : "outline"} size="sm" asChild>
              <Link href={localePath(pathname, "en")}>{dict.common.english}</Link>
            </Button>
          </div>
        </PanelContent>
      </Panel>

      {/* appearance */}
      <Panel>
        <PanelHeader>
          <PanelTitle>{dict.settings.appearanceTitle}</PanelTitle>
          <PanelDescription>{dict.settings.appearanceDesc}</PanelDescription>
        </PanelHeader>
        <PanelContent className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-sm">
            {theme === "light" ? <Sun className="size-4 text-muted-foreground" aria-hidden /> : theme === "system" ? <Monitor className="size-4 text-muted-foreground" aria-hidden /> : <Moon className="size-4 text-muted-foreground" aria-hidden />}
            <span className="font-semibold">
              {theme === "light" ? dict.common.themeLight : theme === "system" ? dict.common.themeSystem : dict.common.themeDark}
            </span>
          </div>
          <Segmented
            label={dict.common.theme}
            value={(theme as "dark" | "light" | "system") ?? "dark"}
            options={[
              { id: "dark", label: dict.common.themeDark },
              { id: "light", label: dict.common.themeLight },
              { id: "system", label: dict.common.themeSystem },
            ]}
            onChange={setTheme}
          />
        </PanelContent>
      </Panel>

      {/* density + motion */}
      <Panel>
        <PanelHeader>
          <PanelTitle>{dict.common.density} · {dict.common.motion}</PanelTitle>
        </PanelHeader>
        <PanelContent className="flex flex-col gap-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <span className="text-sm font-semibold">{dict.common.density}</span>
            <Segmented
              label={dict.common.density}
              value={prefs.density}
              options={[
                { id: "comfortable", label: dict.common.comfortable },
                { id: "compact", label: dict.common.compact },
              ]}
              onChange={(v) => setPref("density", v)}
            />
          </div>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <span className="text-sm font-semibold">{dict.common.motion}</span>
            <Segmented
              label={dict.common.motion}
              value={prefs.motion}
              options={[
                { id: "system", label: dict.common.motionSystem },
                { id: "no_preference", label: dict.common.motionFull },
                { id: "reduce", label: dict.common.motionReduce },
              ]}
              onChange={(v) => setPref("motion", v)}
            />
          </div>
        </PanelContent>
      </Panel>

      {/* charts */}
      <Panel>
        <PanelHeader>
          <PanelTitle>{dict.settings.chartsTitle}</PanelTitle>
        </PanelHeader>
        <PanelContent className="flex flex-col gap-4">
          <label className="flex flex-wrap items-center justify-between gap-3">
            <span className="min-w-0">
              <span className="block text-sm font-semibold">{dict.settings.chartWatermark}</span>
              <span className="mt-0.5 block text-[11px] text-muted-foreground">{dict.settings.chartWatermarkDesc}</span>
            </span>
            <Switch checked={prefs.chartWatermark} onCheckedChange={(v) => setPref("chartWatermark", v)} />
          </label>
          <label className="flex flex-wrap items-center justify-between gap-3">
            <span className="text-sm font-semibold">{dict.settings.chartGrid}</span>
            <Switch checked={prefs.chartGrid} onCheckedChange={(v) => setPref("chartGrid", v)} />
          </label>
        </PanelContent>
      </Panel>

      {/* data refresh */}
      <Panel>
        <PanelHeader>
          <PanelTitle>{dict.settings.dataTitle}</PanelTitle>
          <PanelDescription>{dict.settings.dataDesc}</PanelDescription>
        </PanelHeader>
        <PanelContent className="flex flex-col gap-3">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <span className="text-sm font-semibold">{dict.common.refreshInterval}</span>
            <Select
              value={String(prefs.refreshInterval)}
              onValueChange={(v) => setPref("refreshInterval", (v === "off" ? "off" : Number(v)) as RefreshInterval)}
            >
              <SelectTrigger className="h-9 w-36" aria-label={dict.common.refreshInterval}>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="off">{dict.common.refreshOff}</SelectItem>
                <SelectItem value="30">30 {dict.common.refreshSeconds}</SelectItem>
                <SelectItem value="60">60 {dict.common.refreshSeconds}</SelectItem>
                <SelectItem value="300">5 {dict.common.refreshMinutes}</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <p className="rounded-lg border border-warning/30 bg-warning/5 p-2.5 text-[11px] leading-relaxed text-warning">
            {dict.common.refreshNote}
          </p>
        </PanelContent>
      </Panel>

      {/* 3D scene */}
      <Panel>
        <PanelHeader>
          <PanelTitle>{dict.settings.sceneTitle}</PanelTitle>
          <PanelDescription>{dict.settings.sceneDesc}</PanelDescription>
        </PanelHeader>
        <PanelContent className="flex flex-wrap items-center justify-between gap-3">
          <span className="text-sm font-semibold">{dict.settings.sceneEnable}</span>
          <Switch checked={prefs.sceneEnabled} onCheckedChange={(v) => setPref("sceneEnabled", v)} />
        </PanelContent>
      </Panel>

      {/* storage + about */}
      <Panel className="xl:col-span-2">
        <PanelHeader>
          <PanelTitle>{dict.settings.storageTitle}</PanelTitle>
          <PanelDescription>{dict.settings.storageDesc}</PanelDescription>
        </PanelHeader>
        <PanelContent className="flex flex-col gap-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="text-[11px] text-muted-foreground">{dict.settings.savedNote}</p>
            <Button variant="outline" size="sm" onClick={resetPrefs}>
              <RotateCcw aria-hidden />
              {dict.settings.resetPrefs}
            </Button>
          </div>
          <pre
            dir="ltr"
            className="tnum max-h-56 overflow-auto rounded-xl border border-border/70 bg-navy-950/50 p-3 font-mono text-[11px] leading-relaxed text-muted-foreground"
          >
            {hydrated ? JSON.stringify({ ...prefs, _defaults: DEFAULT_PREFS === prefs ? "defaults" : undefined }, null, 2) : "{}"}
          </pre>
          <div className="rounded-xl border border-border/70 bg-muted/20 p-3.5 text-xs leading-relaxed text-muted-foreground">
            <p className="mb-1 flex items-center gap-1.5 font-bold text-foreground">
              <Braces className="size-4" aria-hidden />
              {dict.settings.aboutTitle}
            </p>
            {dict.settings.aboutBody}
            <p className="tnum mt-2 font-mono text-[10px] text-subtle" dir="ltr">
              dataset: {DATASET.id} · as_of: {DATASET.asOf}
            </p>
          </div>
        </PanelContent>
      </Panel>
    </div>
  );
}

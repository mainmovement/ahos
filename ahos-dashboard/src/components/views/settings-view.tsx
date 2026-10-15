"use client";

import type { ReactNode } from "react";
import { Accessibility, AudioLines, Bell, Contrast, Database, Gauge, Languages, MonitorCog, Music, PanelsTopLeft, Play, Settings, Volume2 } from "lucide-react";
import { useI18n } from "@/lib/i18n";
import { useFormat } from "@/lib/format";
import { useSettings } from "@/lib/settings/provider";
import { QUALITY_BUDGETS, type QualityProfile } from "@/lib/settings/types";
import { soundEngine, type SoundName } from "@/lib/audio/engine";
import { useSound } from "@/lib/audio/use-sound";
import { useNowMinute } from "@/lib/time/now";
import { cn } from "@/lib/utils";
import { PageBody, PageHeader } from "@/components/layout/page-header";
import { DataCard } from "@/components/cards/data-card";
import { Notice } from "@/components/cards/blocks";
import { Button } from "@/components/ui/button";
import { Chip } from "@/components/ui/chip";
import { Segmented } from "@/components/ui/segmented";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Num } from "@/components/ui/primitives";

function Row({ title, hint, children, htmlFor }: { title: string; hint?: string; children: ReactNode; htmlFor?: string }) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--line-subtle)] py-3 last:border-0">
      <div className="min-w-0">
        <label htmlFor={htmlFor} className="text-xs font-medium text-fg-1">
          {title}
        </label>
        {hint && <p className="mt-0.5 text-3xs text-fg-4">{hint}</p>}
      </div>
      <div className="shrink-0">{children}</div>
    </div>
  );
}

export function SettingsView() {
  const { t, tx, locale } = useI18n();
  const f = useFormat();
  const { settings, update, reducedMotion } = useSettings();
  const play = useSound();
  const minute = useNowMinute();
  const tones: { name: SoundName; label: string }[] = [
    { name: "tick", label: tx("کلیک", "Tick") },
    { name: "open", label: tx("باز شدن", "Open") },
    { name: "notify", label: tx("اعلان", "Notify") },
    { name: "alert", label: tx("هشدار", "Alert") },
    { name: "success", label: tx("موفقیت", "Success") },
    { name: "whoosh", label: tx("پرواز دوربین", "Fly-to") },
  ];
  const qualities: QualityProfile[] = ["high", "balanced", "low"];

  return (
    <PageBody className="max-w-[1280px]">
      <PageHeader title={t.nav.items.settings} subtitle={tx("زبان، پوسته، حرکت، صدا و پروفایل کیفیت — ذخیره در localStorage", "Language, theme, motion, sound and quality profile — stored in localStorage")} icon={Settings} demo={false} />
      <div className="grid grid-cols-1 gap-3 @4xl:grid-cols-2">
        <DataCard title={tx("زبان و اعداد", "Language & numbers")} icon={Languages}>
          <Row title={t.topbar.language} hint={tx("جهت صفحه (RTL/LTR) خودکار تغییر می‌کند", "Page direction (RTL/LTR) switches automatically")}>
            <Segmented label={t.topbar.language} value={settings.locale} onChange={(v) => update({ locale: v })} options={[{ value: "fa", label: "فارسی" }, { value: "en", label: "English" }]} />
          </Row>
          <Row title={tx("ارقام", "Digits")} hint={tx("ارقام فارسی اختیاری است؛ پیش‌فرض لاتین برای خوانایی جدول‌ها", "Persian digits are optional; Latin is the default for dense tables")}>
            <Segmented label={tx("ارقام", "Digits")} value={settings.digits} onChange={(v) => update({ digits: v })} options={[{ value: "latin", label: "123" }, { value: "persian", label: "۱۲۳" }]} />
          </Row>
          <div className="mt-2 grid grid-cols-3 gap-2 rounded-[var(--radius-md)] border border-[var(--line-subtle)] bg-white/[0.02] p-2.5 text-center text-3xs text-fg-4">
            <div>
              {tx("عدد", "Number")}
              <Num className="block text-xs text-fg-1">{f.num(1234567.89, 2)}</Num>
            </div>
            <div>
              {tx("درصد", "Percent")}
              <Num className="block text-xs text-fg-1">{f.pct(2.41)}</Num>
            </div>
            <div>
              {tx("تاریخ", "Date")}
              <span className="block text-xs text-fg-1" suppressHydrationWarning>{minute ? f.date(minute, { timeZone: "Asia/Tehran", withYear: true }) : "—"}</span>
            </div>
          </div>
        </DataCard>

        <DataCard title={tx("پوسته و حرکت", "Theme & motion")} icon={Contrast}>
          <Row title={tx("پوسته", "Theme")} hint={tx("کنتراست بالا: سطوح مات و خطوط پررنگ‌تر برای دسترس‌پذیری", "High contrast: opaque surfaces and stronger lines for accessibility")}>
            <Segmented label={tx("پوسته", "Theme")} value={settings.theme} onChange={(v) => update({ theme: v })} options={[{ value: "gold", label: tx("طلایی شیشه‌ای", "Glass gold") }, { value: "contrast", label: tx("کنتراست بالا", "High contrast") }]} />
          </Row>
          <Row title={tx("حرکت", "Motion")} hint={tx("«سیستم» از prefers-reduced-motion پیروی می‌کند", "“System” follows prefers-reduced-motion")}>
            <Segmented label={tx("حرکت", "Motion")} value={settings.motion} onChange={(v) => update({ motion: v })} options={[{ value: "system", label: tx("سیستم", "System") }, { value: "full", label: tx("کامل", "Full") }, { value: "reduced", label: tx("کاهش‌یافته", "Reduced") }]} />
          </Row>
          <div className="mt-2 flex items-center gap-2 text-3xs text-fg-4">
            <Accessibility aria-hidden className="size-3.5" />
            {tx("وضعیت مؤثر", "Effective")}: <Chip tone={reducedMotion ? "info" : "gold"}>{reducedMotion ? tx("حرکت کاهش‌یافته", "Reduced motion") : tx("حرکت کامل", "Full motion")}</Chip>
          </div>
          <Row title={tx("نوار کناری جمع‌شده", "Collapsed sidebar")} htmlFor="sw-sidebar">
            <Switch id="sw-sidebar" checked={settings.sidebarCollapsed} onCheckedChange={(v) => update({ sidebarCollapsed: v })} />
          </Row>
          <Row title={tx("ستون کیان جمع‌شده", "Collapsed Kian column")} htmlFor="sw-assistant">
            <Switch id="sw-assistant" checked={settings.assistantCollapsed} onCheckedChange={(v) => update({ assistantCollapsed: v })} />
          </Row>
        </DataCard>

        <DataCard title={tx("صدا", "Sound")} subtitle={tx("فقط صداهای تولیدی WebAudio — بدون فایل صوتی؛ پیش‌فرض بی‌صدا", "Generated WebAudio tones only — no audio files; muted by default")} icon={AudioLines}>
          <Row title={tx("صدای اصلی", "Master sound")} hint={settings.muted ? t.topbar.soundOff : t.topbar.soundOn} htmlFor="sw-mute">
            <Switch id="sw-mute" checked={!settings.muted} onCheckedChange={(v) => update({ muted: !v })} />
          </Row>
          <Row title={tx("بلندی صدا", "Volume")}>
            <div className="flex w-48 items-center gap-2">
              <Volume2 aria-hidden className="size-3.5 text-fg-4" />
              <Slider value={settings.volume} onChange={(v) => update({ volume: v })} label={tx("بلندی صدا", "Volume")} disabled={settings.muted} />
              <Num className="w-8 text-3xs text-fg-3">{f.num(Math.round(settings.volume * 100), 0)}</Num>
            </div>
          </Row>
          <Row title={tx("صداهای رابط", "Interface sounds")} hint={tx("کلیک، باز/بسته شدن، ارسال پیام", "Ticks, open/close, message send")} htmlFor="sw-ui">
            <Switch id="sw-ui" checked={settings.uiSounds} onCheckedChange={(v) => update({ uiSounds: v })} disabled={settings.muted} />
          </Row>
          <Row title={tx("فضای صوتی محیطی", "Ambient pad")} hint={tx("پد آرام چند نوسان‌ساز با فیلتر پایین‌گذر", "Calm multi-oscillator pad with low-pass filter")} htmlFor="sw-ambient">
            <Switch id="sw-ambient" checked={settings.ambient} onCheckedChange={(v) => update({ ambient: v })} disabled={settings.muted} />
          </Row>
          <div className="mt-2 flex flex-wrap gap-1.5" aria-label={tx("آزمایش صدا", "Test tones")}>
            {tones.map((tn) => (
              <Button key={tn.name} size="xs" variant="outline" disabled={settings.muted} onClick={() => (settings.uiSounds ? play(tn.name) : soundEngine.play(tn.name))}>
                <Play aria-hidden />
                {tn.label}
              </Button>
            ))}
          </div>
          {settings.muted && <p className="mt-2 flex items-center gap-1 text-3xs text-fg-4"><Music aria-hidden className="size-3" />{tx("برای آزمایش، صدای اصلی را روشن کنید.", "Turn master sound on to test tones.")}</p>}
        </DataCard>

        <DataCard title={tx("پروفایل کیفیت", "Quality profile")} subtitle={tx("کنترل ذرات، شیشه مات، بلوم، وضوح رندر و بافت کره", "Controls particles, frosted glass, bloom, render scale and globe textures")} icon={Gauge}>
          <div className="grid grid-cols-1 gap-2 @lg:grid-cols-3" role="radiogroup" aria-label={t.topbar.quality}>
            {qualities.map((q) => {
              const b = QUALITY_BUDGETS[q];
              const active = settings.quality === q;
              return (
                <button
                  key={q}
                  type="button"
                  role="radio"
                  aria-checked={active}
                  onClick={() => update({ quality: q })}
                  className={cn("rounded-[var(--radius-lg)] border p-3 text-start transition-colors", active ? "border-gold-400/60 bg-gold-400/[0.08] shadow-[var(--shadow-glow-sm)]" : "border-[var(--line-subtle)] hover:border-gold-400/30")}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-semibold text-fg-1">{t.quality[q]}</span>
                    {active && <Chip tone="gold">{tx("فعال", "Active")}</Chip>}
                  </div>
                  <p className="mt-1 text-3xs text-fg-4">{t.quality[`${q}Desc` as const]}</p>
                  <dl className="mt-2 space-y-0.5 text-3xs text-fg-3" dir="ltr">
                    <div className="flex justify-between"><dt>bloom</dt><dd>{b.bloom ? "on" : "off"}</dd></div>
                    <div className="flex justify-between"><dt>DPR cap</dt><dd>{b.pixelRatioCap}× · {Math.round(b.renderScale * 100)}%</dd></div>
                    <div className="flex justify-between"><dt>texture</dt><dd>{b.textureSize / 1024}K · {b.geoDetail}</dd></div>
                    <div className="flex justify-between"><dt>stars / dust</dt><dd>{b.stars} / {b.particles}</dd></div>
                    <div className="flex justify-between"><dt>fps cap</dt><dd>{b.fpsCap}</dd></div>
                  </dl>
                </button>
              );
            })}
          </div>
          <p className="mt-2 flex items-center gap-1 text-3xs text-fg-4">
            <MonitorCog aria-hidden className="size-3" />
            {tx("در اولین اجرا، پروفایل بر اساس هسته‌های CPU، حافظه دستگاه و ترجیح حرکت به‌صورت خودکار انتخاب می‌شود.", "On first run the profile is auto-selected from CPU cores, device memory and motion preference.")}
          </p>
        </DataCard>

        <DataCard className="@4xl:col-span-2" title={tx("داده و یکپارچه‌سازی", "Data & integration")} icon={Database}>
          <Notice icon={<Database />} tone="info">
            {tx(
              "همه داده‌ها از توابع تایپ‌شده در src/lib/api/*.ts می‌آیند که فعلاً از src/mock می‌خوانند. هیچ فراخوانی شبکه، کلید یا API پولی در زمان اجرا وجود ندارد. جایگزینی با بک‌اند واقعی بدون تغییر کامپوننت‌ها ممکن است (README_MERGE.md).",
              "All data comes from typed functions in src/lib/api/*.ts that currently read from src/mock. There are no runtime network calls, keys or paid APIs. Swapping in the real backend needs no component changes (README_MERGE.md).",
            )}
          </Notice>
          <div className="mt-3 grid grid-cols-2 gap-2 text-3xs text-fg-3 @lg:grid-cols-4 @3xl:grid-cols-6" dir="ltr">
            {["dashboard", "markets", "equities", "commodities", "crypto", "tokens", "news", "security", "agents", "university", "research", "paper", "system", "chat", "org", "search"].map((m) => (
              <span key={m} className="mono rounded-[var(--radius-sm)] border border-[var(--line-subtle)] bg-white/[0.02] px-2 py-1">lib/api/{m}.ts</span>
            ))}
          </div>
          <div className="mt-3 flex flex-wrap items-center gap-2 text-3xs text-fg-4">
            <PanelsTopLeft aria-hidden className="size-3" />
            {tx("زبان فعلی", "Current locale")}: <bdi className="text-fg-2">{locale}</bdi>
            <Bell aria-hidden className="ms-3 size-3" />
            {tx("کلید ذخیره‌سازی", "Storage key")}: <bdi className="mono text-fg-2">ahos.settings.v1</bdi>
          </div>
        </DataCard>
      </div>
    </PageBody>
  );
}

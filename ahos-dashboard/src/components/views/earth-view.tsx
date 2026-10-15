"use client";

import { useMemo, useState } from "react";
import { Clock3, Earth, Map as MapIcon, Sun } from "lucide-react";
import type { DataEnvelope, EarthOverview } from "@/lib/api/types";
import { sunPosition, sunTimes } from "@/lib/astro/solar";
import { useFormat } from "@/lib/format";
import { useI18n } from "@/lib/i18n";
import { useNow, useNowMinute } from "@/lib/time/now";
import { EXCHANGES, formatCountdown, sessionState } from "@/lib/time/sessions";
import { PageBody, PageHeader } from "@/components/layout/page-header";
import { DataCard } from "@/components/cards/data-card";
import { StatTile } from "@/components/cards/blocks";
import { GlobeHero } from "@/components/globe/globe-hero";
import { GlobeFallback2D } from "@/components/globe/globe-fallback";
import { TEHRAN } from "@/components/globe/scene-constants";
import { Chip } from "@/components/ui/chip";
import { Delta, Num } from "@/components/ui/primitives";

export function EarthView({ earth, initialFocus }: { earth: DataEnvelope<EarthOverview>; initialFocus: "global" | "iran" }) {
  const { t, l, tx } = useI18n();
  const f = useFormat();
  const now = useNow();
  const minute = useNowMinute();
  const [mapIran, setMapIran] = useState(false);

  const astro = useMemo(() => {
    if (minute === null) return null;
    const d = new Date(minute);
    const s = sunPosition(d);
    const times = sunTimes(TEHRAN.lat, TEHRAN.lng, d);
    const dayLen = times.sunrise && times.sunset ? (times.sunset.getTime() - times.sunrise.getTime()) / 1000 : null;
    return { s, times, dayLen };
  }, [minute]);

  const computedMeta = { ...earth.meta, source: "local/astro", sourceLabel: { fa: "محاسبه محلی (NOAA)", en: "Computed locally (NOAA)" }, status: "LIVE" as const, isMock: false, retrievedAt: minute ? new Date(minute).toISOString() : null, ttlSec: 120 };

  return (
    <PageBody>
      <PageHeader title={t.nav.items.earth} subtitle={tx("کره سه‌بعدی با مرز واقعی روز و شب، ایران برجسته و مراکز مالی جهان", "3D globe with the real day/night terminator, Iran highlighted and global financial hubs")} icon={Earth} />
      <GlobeHero earth={earth.data} meta={earth.meta} variant="full" initialFocus={initialFocus} />

      <div className="grid grid-cols-1 gap-3 @4xl:grid-cols-12">
        <DataCard className="@4xl:col-span-7" title={tx("ساعت جهانی و جلسات بازار", "World clocks & sessions")} subtitle={t.topbar.estimated} icon={Clock3} meta={earth.meta} bodyClassName="px-0 pb-0">
          <div className="max-h-[420px] overflow-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th scope="col" className="ps-3.5">{tx("شهر", "City")}</th>
                  <th scope="col" className="num-cell">{tx("ساعت محلی", "Local time")}</th>
                  <th scope="col">{tx("بورس", "Exchange")}</th>
                  <th scope="col">{t.common.status}</th>
                  <th scope="col" className="num-cell pe-3.5">{tx("شاخص (نمایشی)", "Index (demo)")}</th>
                </tr>
              </thead>
              <tbody>
                {earth.data.centers.map((c) => {
                  const ex = c.exchangeId ? EXCHANGES.find((e) => e.id === c.exchangeId) : undefined;
                  const st = ex && minute !== null ? sessionState(ex, new Date(minute)) : null;
                  return (
                    <tr key={c.id}>
                      <td className="ps-3.5">
                        <span className="text-xs font-medium text-fg-1">{l(c.name)}</span>
                        <span className="ms-1.5 text-3xs text-fg-5" dir="ltr">
                          {c.timeZone}
                        </span>
                      </td>
                      <td className="num-cell">
                        <Num className="text-xs text-fg-1">
                          <span suppressHydrationWarning>{now ? f.time(now, { seconds: true, timeZone: c.timeZone }) : "--:--:--"}</span>
                        </Num>
                      </td>
                      <td className="text-2xs text-fg-3">{ex ? l(ex.name) : "—"}</td>
                      <td>
                        {st ? (
                          <span className="flex items-center gap-1.5">
                            <Chip tone={st.open ? "up" : "slate"}>{st.open ? t.topbar.open : t.topbar.closed}</Chip>
                            <span className="text-3xs text-fg-5">{f.digits(formatCountdown(st.minutesToChange))}</span>
                          </span>
                        ) : (
                          <Chip tone="muted">{tx("مدل نشده", "Not modelled")}</Chip>
                        )}
                      </td>
                      <td className="num-cell pe-3.5">
                        <bdi className="me-1.5 text-3xs text-fg-4">{c.indexSymbol ?? "—"}</bdi>
                        <Delta value={c.indexChange} size="xs" />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </DataCard>

        <DataCard className="@4xl:col-span-5" title={tx("خورشید و فصل", "Sun & season")} subtitle={tx("الگوریتم NOAA/Meeus — بدون شبکه", "NOAA/Meeus algorithm — no network")} icon={Sun} meta={computedMeta}>
          {astro && (
            <div className="grid grid-cols-2 gap-2">
              <StatTile label={tx("میل خورشید", "Solar declination")} value={`${f.num(astro.s.declination, 2)}°`} tone="gold" />
              <StatTile label={tx("معادله زمان", "Equation of time")} value={`${f.num(astro.s.equationOfTime, 1)} ${tx("دقیقه", "min")}`} />
              <StatTile label={t.globe.subsolar} value={`${f.num(astro.s.subsolarLat, 1)}°, ${f.num(astro.s.subsolarLng, 1)}°`} tone="data" />
              <StatTile label={tx("ظهر خورشیدی تهران", "Tehran solar noon")} value={f.time(astro.times.solarNoon, { timeZone: "Asia/Tehran" })} />
              <StatTile label={`${t.globe.sunrise} · ${t.topbar.tehran}`} value={f.time(astro.times.sunrise, { timeZone: "Asia/Tehran" })} />
              <StatTile label={`${t.globe.sunset} · ${t.topbar.tehran}`} value={f.time(astro.times.sunset, { timeZone: "Asia/Tehran" })} />
              <StatTile className="col-span-2" label={tx("طول روز در تهران", "Tehran day length")} value={f.duration(astro.dayLen)} hint={tx("زاویه سمت‌الرأس ۹۰٫۸۳۳° (شکست جوی + قطر خورشید)", "Zenith 90.833° (refraction + solar radius)")} />
            </div>
          )}
        </DataCard>
      </div>

      <DataCard
        title={tx("نقشه دوبعدی (جایگزین بدون WebGL)", "2D map (no-WebGL fallback)")}
        subtitle={tx("نیم‌کره شب = دایره ۹۰ درجه حول نقطه پادخورشیدی", "Night hemisphere = 90° circle around the antisolar point")}
        icon={MapIcon}
        meta={earth.meta}
        actions={
          <button type="button" onClick={() => setMapIran((v) => !v)} className="rounded-[var(--radius-sm)] border border-gold-400/30 px-2 py-0.5 text-3xs text-gold-100 hover:bg-[var(--surface-hover)]">
            {mapIran ? t.globe.backGlobal : t.globe.flyIran}
          </button>
        }
      >
        <div className="relative h-[380px] overflow-hidden rounded-[var(--radius-md)] border border-[var(--line-subtle)] bg-ink-950/40">
          <GlobeFallback2D centers={earth.data.centers} focusIran={mapIran} nowMs={minute} onIranClick={() => setMapIran(true)} showLabels showMarkers />
        </div>
      </DataCard>
    </PageBody>
  );
}

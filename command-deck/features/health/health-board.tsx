"use client";

import { CircleMinus, Cpu, Gauge, HardDrive, MemoryStick, Server, Waves } from "lucide-react";
import { useLocale } from "@/components/providers/locale-provider";
import { Panel, PanelContent, PanelHeader, PanelTitle, PanelDescription } from "@/components/ui/panel";
import { Badge } from "@/components/ui/badge";
import { StatusBadge } from "@/components/status/status-badge";
import { ProvenancePanel } from "@/components/status/provenance-panel";
import { EmptyState } from "@/components/status/empty-state";
import { HEALTH_CHECKS, PROCESS_INVENTORY, SERVICES, SOAK_STATUS } from "@/lib/data/health";
import { localizeDigits, formatNumber } from "@/lib/formatters/numbers";
import { formatDateTime } from "@/lib/formatters/dates";
import type { SoakSegmentKind } from "@/lib/types";
import { cn } from "@/lib/utils";

const SEG_CLASS: Record<SoakSegmentKind, string> = {
  MEASURED: "bg-accent/50",
  GAP: "bg-muted/70",
  EXCLUDED: "hatch-excluded bg-danger/15",
  QUARANTINED: "hatch-quarantined bg-warning/15",
};

export function HealthBoard() {
  const { dict, locale } = useLocale();
  const soak = SOAK_STATUS;
  const spanMs = new Date(soak.end ?? soak.start).getTime() - new Date(soak.start).getTime();
  const pct = (iso: string) =>
    ((new Date(iso).getTime() - new Date(soak.start).getTime()) / spanMs) * 100;

  const segLabels: Record<SoakSegmentKind, string> = {
    MEASURED: dict.health.segMeasured,
    GAP: dict.health.segGap,
    EXCLUDED: dict.health.segExcluded,
    QUARANTINED: dict.health.segQuarantined,
  };

  return (
    <div className="flex flex-col gap-4">
      {/* service inventory */}
      <Panel>
        <PanelHeader>
          <PanelTitle>{dict.health.servicesTitle}</PanelTitle>
        </PanelHeader>
        <PanelContent className="overflow-x-auto">
          <table className="w-full min-w-[640px] text-xs">
            <thead>
              <tr className="border-b border-border text-start text-[11px] text-muted-foreground">
                <th scope="col" className="px-2 py-2 text-start font-bold">{dict.positions.colStatus}</th>
                <th scope="col" className="px-2 py-2 text-start font-bold">{dict.health.endpoint}</th>
                <th scope="col" className="px-2 py-2 text-start font-bold">{dict.common.details}</th>
              </tr>
            </thead>
            <tbody>
              {SERVICES.map((svc) => (
                <tr key={svc.id} className="border-b border-border/40 last:border-0">
                  <td className="px-2 py-3">
                    <div className="flex flex-col gap-1">
                      <span className="font-bold">{svc.name[locale]}</span>
                      <span className="text-[10px] text-muted-foreground">{svc.role[locale]}</span>
                    </div>
                  </td>
                  <td className="px-2 py-3 align-top">
                    <div className="flex flex-col gap-1.5">
                      <StatusBadge status={svc.status} size="sm" />
                      {svc.endpoint ? (
                        <span className="font-mono text-[10px] text-subtle" dir="ltr">{svc.endpoint}</span>
                      ) : (
                        <span className="text-[10px] text-subtle">—</span>
                      )}
                    </div>
                  </td>
                  <td className="px-2 py-3 align-top text-[11px] leading-relaxed text-muted-foreground">
                    {svc.provenance.note ? svc.provenance.note[locale] : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </PanelContent>
      </Panel>

      <div className="grid gap-4 xl:grid-cols-2">
        {/* health checks */}
        <Panel>
          <PanelHeader>
            <PanelTitle>{dict.health.checksTitle}</PanelTitle>
          </PanelHeader>
          <PanelContent className="flex flex-col gap-2">
            {HEALTH_CHECKS.map((check) => (
              <div key={check.id} className="rounded-xl border border-border/60 bg-muted/20 p-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="text-xs font-bold">{check.name[locale]}</p>
                  <StatusBadge status={check.status} size="sm" />
                </div>
                <p className="mt-1 text-[11px] leading-relaxed text-muted-foreground">{check.detail[locale]}</p>
                <p className="tnum mt-1.5 text-[10px] text-subtle">
                  {dict.health.lastCheck}: {check.lastRunAt ? formatDateTime(check.lastRunAt, locale) : dict.health.never}
                  {" · "}
                  {dict.positions.colGross === "" ? "" : "latency: "}
                  {check.latencyMs.value !== null ? `${formatNumber(check.latencyMs.value, locale, 1)} ms` : dict.status[check.latencyMs.provenance.status]}
                </p>
              </div>
            ))}
          </PanelContent>
        </Panel>

        {/* processes + resources */}
        <div className="flex flex-col gap-4">
          <Panel>
            <PanelHeader>
              <PanelTitle>{dict.health.processTitle}</PanelTitle>
            </PanelHeader>
            <PanelContent>
              {PROCESS_INVENTORY.value === null ? (
                <div className="rounded-xl border border-dashed border-border-strong">
                  <EmptyState icon={Server} title={dict.status[PROCESS_INVENTORY.provenance.status]} body={dict.health.processesEmpty} />
                </div>
              ) : null}
            </PanelContent>
          </Panel>

          <Panel>
            <PanelHeader>
              <PanelTitle>{dict.health.resourcesTitle}</PanelTitle>
              <PanelDescription>{dict.health.ramBody}</PanelDescription>
            </PanelHeader>
            <PanelContent className="grid gap-2.5 sm:grid-cols-3">
              {[
                { icon: MemoryStick, label: dict.health.ramTitle },
                { icon: Cpu, label: dict.health.cpuTitle },
                { icon: HardDrive, label: dict.health.diskTitle },
              ].map((res) => (
                <div key={res.label} className="flex flex-col items-center gap-2 rounded-xl border border-border/60 bg-muted/20 p-4 text-center">
                  <res.icon className="size-5 text-muted-foreground" aria-hidden />
                  <p className="text-[11px] font-bold text-muted-foreground">{res.label}</p>
                  <StatusBadge status="NOT_MEASURED" size="sm" />
                </div>
              ))}
            </PanelContent>
          </Panel>
        </div>
      </div>

      {/* soak timeline */}
      <Panel>
        <PanelHeader>
          <div className="flex flex-wrap items-center justify-between gap-2">
            <PanelTitle>{dict.health.soakTitle}</PanelTitle>
            <Badge variant="violet">
              <Waves aria-hidden />
              {dict.common.sample}
            </Badge>
          </div>
          <PanelDescription>
            {formatDateTime(soak.start, locale)} → {soak.end ? formatDateTime(soak.end, locale) : "—"} (UTC)
          </PanelDescription>
        </PanelHeader>
        <PanelContent className="flex flex-col gap-4">
          <div className="flex flex-col gap-2">
            <div
              className="relative h-9 overflow-hidden rounded-xl border border-border bg-muted/30"
              role="img"
              aria-label={`Soak timeline: ${segLabels.MEASURED}, ${segLabels.GAP}, ${segLabels.EXCLUDED}, ${segLabels.QUARANTINED}`}
            >
              {soak.segments.map((seg) => {
                const startPct = pct(seg.start);
                const widthPct = pct(seg.end) - startPct;
                return (
                  <div
                    key={seg.id}
                    className={cn("absolute inset-y-0", SEG_CLASS[seg.kind])}
                    style={{ insetInlineStart: `${startPct}%`, width: `${widthPct}%` }}
                    title={seg.note ? seg.note[locale] : segLabels[seg.kind]}
                  >
                    {seg.kind !== "MEASURED" && widthPct > 4 ? (
                      <span className="tnum absolute inset-0 flex items-center justify-center truncate px-1 text-[8px] font-extrabold text-foreground/80">
                        {segLabels[seg.kind]}
                      </span>
                    ) : null}
                  </div>
                );
              })}
            </div>
            <div className="tnum flex justify-between text-[9px] text-subtle" dir="ltr">
              <span>{soak.start.slice(0, 10)}</span>
              <span>{soak.end?.slice(0, 10)}</span>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-[10px]">
            <span className="text-muted-foreground">{dict.health.legend}:</span>
            {(Object.keys(SEG_CLASS) as SoakSegmentKind[]).map((kind) => (
              <span key={kind} className="inline-flex items-center gap-1.5">
                <span aria-hidden className={cn("inline-block h-3 w-5 rounded", SEG_CLASS[kind])} />
                {segLabels[kind]}
              </span>
            ))}
          </div>

          <div className="grid gap-3 sm:grid-cols-3">
            <div className="rounded-xl border border-border/60 bg-muted/20 p-3 text-center">
              <Gauge className="mx-auto mb-1 size-4 text-accent" aria-hidden />
              <p className="text-[10px] text-muted-foreground">{dict.health.coverage}</p>
              <p className="tnum mt-0.5 text-lg font-extrabold text-accent" dir="ltr">
                {soak.coverage.value !== null ? `${formatNumber(soak.coverage.value, locale, 1)}%` : "—"}
              </p>
              <StatusBadge status={soak.coverage.provenance.status} size="sm" />
            </div>
            <div className="rounded-xl border border-border/60 bg-muted/20 p-3 text-center">
              <p className="text-[10px] text-muted-foreground">{dict.health.segGap}</p>
              <p className="tnum mt-1 text-lg font-extrabold">
                {localizeDigits(String(soak.segments.filter((s) => s.kind === "GAP").length), locale)}
              </p>
            </div>
            <div className="rounded-xl border border-border/60 bg-muted/20 p-3 text-center">
              <p className="text-[10px] text-muted-foreground">{dict.health.segExcluded} / {dict.health.segQuarantined}</p>
              <p className="tnum mt-1 text-lg font-extrabold text-warning">
                {localizeDigits(String(soak.segments.filter((s) => s.kind === "EXCLUDED" || s.kind === "QUARANTINED").length), locale)}
              </p>
            </div>
          </div>

          <ProvenancePanel provenance={soak.provenance} title={dict.health.soakTitle} />
        </PanelContent>
      </Panel>

      {/* retention */}
      <Panel>
        <PanelHeader>
          <PanelTitle>{dict.health.retentionTitle}</PanelTitle>
        </PanelHeader>
        <PanelContent className="flex items-start gap-3 text-xs leading-relaxed text-muted-foreground">
          <CircleMinus className="mt-0.5 size-4 shrink-0 text-muted-foreground" aria-hidden />
          {dict.health.retentionBody}
        </PanelContent>
      </Panel>
    </div>
  );
}

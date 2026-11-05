"use client";

import { useState } from "react";
import {
  Ban,
  CircleCheck,
  CircleSlash,
  CircleQuestionMark,
  CircleX,
  FileCheck2,
  Lock,
  OctagonX,
} from "lucide-react";
import { useLocale } from "@/components/providers/locale-provider";
import { Panel, PanelContent, PanelHeader, PanelTitle, PanelDescription } from "@/components/ui/panel";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { evaluateReadiness } from "@/lib/data/readiness";
import type { ReadinessItemState } from "@/lib/types";
import { cn } from "@/lib/utils";

const ITEM_STATE_META: Record<ReadinessItemState, { icon: typeof CircleCheck; cls: string }> = {
  PASS: { icon: CircleCheck, cls: "text-success" },
  FAIL: { icon: CircleX, cls: "text-danger" },
  NOT_MEASURED: { icon: CircleSlash, cls: "text-muted-foreground" },
  NOT_VERIFIED: { icon: CircleQuestionMark, cls: "text-warning" },
};

export function ReadinessGate() {
  const { dict, locale } = useLocale();
  const [demo, setDemo] = useState(false);
  const evaluation = evaluateReadiness(demo, {
    reasonAdapter: dict.readiness.reasonAdapter,
    reasonKillSwitch: dict.readiness.reasonKillSwitch,
    reasonJudge: dict.readiness.reasonJudge,
    reasonPaperOnly: dict.readiness.reasonPaperOnly,
    reasonCalibration: dict.readiness.reasonCalibration,
  });

  return (
    <div className="flex flex-col gap-4">
      {/* authorization banner */}
      <section
        aria-label={dict.readiness.bannerTitle}
        className="flex items-start gap-3 rounded-2xl border border-danger/45 bg-danger/[0.06] p-4"
      >
        <span className="mt-0.5 inline-flex size-9 shrink-0 items-center justify-center rounded-xl bg-danger/15 text-danger">
          <OctagonX className="size-5" aria-hidden />
        </span>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-extrabold text-danger">{dict.readiness.bannerTitle}</p>
          <p className="mt-1 text-xs leading-relaxed text-muted-foreground">{dict.readiness.bannerBody}</p>
        </div>
        <Badge variant="default" className="shrink-0">
          <Lock aria-hidden />
          {dict.common.paperOnly}
        </Badge>
      </section>

      {/* demonstration toggle */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-violet/35 bg-violet/[0.06] p-4">
        <div className="min-w-0">
          <p className="text-xs font-bold text-violet">{dict.readiness.demoToggle}</p>
          <p className="mt-0.5 text-[11px] text-muted-foreground">{dict.readiness.demoNote}</p>
        </div>
        <div className="flex items-center gap-2.5">
          <Switch id="demo-mode" checked={demo} onCheckedChange={(v) => setDemo(v)} aria-label={dict.readiness.demoToggle} />
          <Badge variant={demo ? "violet" : "muted"}>{demo ? "ON" : "OFF"}</Badge>
        </div>
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.5fr_1fr]">
        {/* checklist */}
        <Panel>
          <PanelHeader>
            <PanelTitle>{dict.readiness.checklistTitle}</PanelTitle>
            <PanelDescription>{dict.readiness.description}</PanelDescription>
          </PanelHeader>
          <PanelContent className="flex flex-col gap-2.5">
            {evaluation.items.map((item) => {
              const meta = ITEM_STATE_META[item.state];
              const demonstrated = demo && !item.hardBlocked && item.demonstrationState !== item.state;
              return (
                <div
                  key={item.id}
                  className={cn(
                    "rounded-xl border p-3.5",
                    item.state === "PASS"
                      ? "border-success/35 bg-success/[0.05]"
                      : item.state === "FAIL"
                        ? "border-danger/40 bg-danger/[0.05]"
                        : "border-border/70 bg-muted/20",
                  )}
                >
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <div className="flex min-w-0 items-start gap-2.5">
                      <meta.icon className={cn("mt-0.5 size-4 shrink-0", meta.cls)} aria-hidden />
                      <div className="min-w-0">
                        <p className="text-xs font-bold leading-relaxed">{item.title[locale]}</p>
                        <p className="mt-1 text-[11px] leading-relaxed text-muted-foreground">
                          <span className="font-semibold text-subtle">{dict.readiness.requirement}: </span>
                          {item.requirement[locale]}
                        </p>
                      </div>
                    </div>
                    <span
                      className={cn(
                        "inline-flex shrink-0 items-center gap-1.5 rounded-full border border-current/30 px-2 py-0.5 text-[10px] font-extrabold",
                        meta.cls,
                      )}
                    >
                      <span dir="ltr">{item.state}</span>
                    </span>
                  </div>
                  {item.evidence ? (
                    <p className="mt-2 border-t border-border/50 pt-2 text-[10px] leading-relaxed text-muted-foreground">
                      <span className="font-semibold text-subtle">{dict.readiness.evidence}: </span>
                      {item.evidence[locale]}
                    </p>
                  ) : null}
                  {demonstrated ? (
                    <p className="mt-1.5 text-[10px] font-semibold text-violet">↗ {dict.readiness.demoNote}</p>
                  ) : null}
                  {item.hardBlocked ? (
                    <p className="mt-1.5 text-[10px] font-semibold text-danger">{dict.readiness.hardBlockedNote}</p>
                  ) : null}
                </div>
              );
            })}
          </PanelContent>
        </Panel>

        {/* verdict */}
        <div className="flex min-w-0 flex-col gap-4">
          <Panel className="border-danger/40">
            <PanelHeader>
              <PanelTitle>{dict.readiness.verdictTitle}</PanelTitle>
            </PanelHeader>
            <PanelContent className="flex flex-col items-center gap-3 py-6 text-center">
              <span className="inline-flex size-14 items-center justify-center rounded-2xl border border-danger/40 bg-danger/10 text-danger">
                <Ban className="size-7" aria-hidden />
              </span>
              <p className="text-xl font-extrabold tracking-tight text-danger" dir="ltr">
                {dict.readiness.verdict}
              </p>
              <p className="max-w-sm text-[11px] leading-relaxed text-muted-foreground">{dict.readiness.verdictBody}</p>
            </PanelContent>
          </Panel>

          <Panel>
            <PanelHeader>
              <PanelTitle>{dict.readiness.reasonsTitle}</PanelTitle>
            </PanelHeader>
            <PanelContent>
              <ul className="flex flex-col gap-2">
                {evaluation.verdictReasons.map((reason) => (
                  <li
                    key={reason.key}
                    className="flex items-start gap-2 rounded-xl border border-border/60 bg-muted/20 p-2.5 text-[11px] leading-relaxed"
                  >
                    <FileCheck2 className="mt-0.5 size-3.5 shrink-0 text-muted-foreground" aria-hidden />
                    <span>{dict.readiness[`reason${reason.key.charAt(0).toUpperCase()}${reason.key.slice(1)}` as keyof typeof dict.readiness] as string}</span>
                  </li>
                ))}
              </ul>
            </PanelContent>
          </Panel>
        </div>
      </div>
    </div>
  );
}

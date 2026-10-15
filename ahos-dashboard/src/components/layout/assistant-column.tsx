"use client";

import { useState } from "react";
import { Activity, ChevronDown, MessagesSquare, PanelLeftClose, PanelLeftOpen, TriangleAlert } from "lucide-react";
import type { AgentEvent, AlertItem, ChatMessage, DataMeta } from "@/lib/api/types";
import { useI18n } from "@/lib/i18n";
import { useFormat } from "@/lib/format";
import { useSettings } from "@/lib/settings/provider";
import { useSound } from "@/lib/audio/use-sound";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Tip } from "@/components/ui/tooltip";
import { StatusChip } from "@/components/ui/status";
import { KianPanel } from "@/components/chat/kian-panel";
import { ActivityFeed, type AgentIndexEntry } from "@/components/agents/activity-feed";
import { AlertsList } from "@/components/cards/alerts-list";
import { CardFooter } from "@/components/cards/data-card";

export interface AssistantData {
  chatSeed: Record<"fa" | "en", ChatMessage[]>;
  activity: AgentEvent[];
  activityMeta: DataMeta;
  agentIndex: Record<string, AgentIndexEntry>;
  alerts: AlertItem[];
  alertsMeta: DataMeta;
}

export function AssistantColumn({ data }: { data: AssistantData }) {
  const { t, dir } = useI18n();
  const f = useFormat();
  const { settings, update } = useSettings();
  const play = useSound();
  const collapsed = settings.assistantCollapsed;
  const [feedOpen, setFeedOpen] = useState(true);
  const [alertsOpen, setAlertsOpen] = useState(true);
  const tipSide = dir === "rtl" ? "right" : "left";
  const toggle = () => {
    update({ assistantCollapsed: !collapsed });
    play(collapsed ? "open" : "close");
  };
  const OpenIcon = dir === "rtl" ? PanelLeftOpen : PanelLeftClose;
  const CloseIcon = dir === "rtl" ? PanelLeftClose : PanelLeftOpen;

  if (collapsed) {
    return (
      <aside aria-label={t.rail.label} className="relative flex w-[var(--assistant-w-collapsed)] shrink-0 flex-col items-center gap-1.5 border-s border-[var(--line-hairline)] bg-ink-950/50 py-3">
        <Tip content={t.kian.expand} side={tipSide}>
          <Button variant="ghost" size="icon" onClick={toggle} aria-label={t.kian.expand} aria-expanded={false}>
            <OpenIcon aria-hidden />
          </Button>
        </Tip>
        <div aria-hidden className="hairline-x my-1 w-6" />
        <Tip content={t.kian.name} side={tipSide}>
          <Button variant="ghost" size="icon" onClick={toggle} aria-label={t.kian.name} className="text-gold-300">
            <MessagesSquare aria-hidden />
          </Button>
        </Tip>
        <Tip content={t.rail.agentActivity} side={tipSide}>
          <Button variant="ghost" size="icon" onClick={toggle} aria-label={t.rail.agentActivity}>
            <Activity aria-hidden />
          </Button>
        </Tip>
        <Tip content={`${t.rail.alerts} · ${f.num(data.alerts.length, 0)}`} side={tipSide}>
          <Button variant="ghost" size="icon" onClick={toggle} aria-label={t.rail.alerts} className="relative">
            <TriangleAlert aria-hidden />
            <span aria-hidden className="absolute end-1.5 top-1.5 size-1.5 rounded-full bg-warn" />
          </Button>
        </Tip>
      </aside>
    );
  }

  return (
    <aside aria-label={t.rail.label} className="relative flex w-[var(--assistant-w)] shrink-0 flex-col border-s border-[var(--line-hairline)] bg-[linear-gradient(180deg,rgb(8_14_27/0.7),rgb(4_8_16/0.82))]">
      <div aria-hidden className="hairline-y pointer-events-none absolute inset-y-0 start-0 opacity-60" />
      <div className="absolute end-2 top-3 z-10">
        <Tip content={t.kian.collapse} side={tipSide}>
          <Button variant="ghost" size="icon-xs" onClick={toggle} aria-label={t.kian.collapse} aria-expanded>
            <CloseIcon aria-hidden />
          </Button>
        </Tip>
      </div>

      <KianPanel seed={data.chatSeed} className="min-h-[260px] flex-1 pe-6" />

      <RailSection
        title={t.rail.agentActivity}
        icon={<Activity aria-hidden className="size-3.5 text-gold-300" />}
        count={data.activity.length}
        open={feedOpen}
        onToggle={() => setFeedOpen((o) => !o)}
        meta={data.activityMeta}
      >
        <ActivityFeed events={data.activity} index={data.agentIndex} limit={6} dense />
      </RailSection>

      <RailSection
        title={t.rail.alerts}
        icon={<TriangleAlert aria-hidden className="size-3.5 text-warn" />}
        count={data.alerts.length}
        open={alertsOpen}
        onToggle={() => setAlertsOpen((o) => !o)}
        meta={data.alertsMeta}
      >
        <AlertsList alerts={data.alerts} dense />
      </RailSection>
    </aside>
  );
}

function RailSection({ title, icon, count, open, onToggle, children, meta }: { title: string; icon: React.ReactNode; count: number; open: boolean; onToggle: () => void; children: React.ReactNode; meta: DataMeta }) {
  const f = useFormat();
  const id = `rail-${title.replace(/\s+/g, "-")}`;
  return (
    <section className={cn("flex min-h-0 flex-col border-t border-[var(--line-hairline)]", open ? "max-h-[30%]" : "")}>
      <h2>
        <button type="button" onClick={onToggle} aria-expanded={open} aria-controls={id} className="flex w-full items-center gap-2 px-3 py-2 text-start transition-colors hover:bg-[var(--surface-hover)]">
          {icon}
          <span className="flex-1 text-xs font-semibold text-fg-1">{title}</span>
          <span className="num rounded-full border border-white/10 px-1.5 text-3xs text-fg-3">{f.num(count, 0)}</span>
          {meta.isMock && <StatusChip status="DEMO" showLabel={false} />}
          <ChevronDown aria-hidden className={cn("size-3.5 text-fg-4 transition-transform", !open && "-rotate-90 rtl:rotate-90")} />
        </button>
      </h2>
      {open && (
        <>
          <div id={id} className="min-h-0 flex-1 overflow-y-auto px-2 pb-1">
            {children}
          </div>
          <CardFooter meta={meta} compact />
        </>
      )}
    </section>
  );
}

"use client";

import { Bot } from "lucide-react";
import { useLocale } from "@/components/providers/locale-provider";
import { HudCard } from "./hud-card";
import { StatusBadge } from "@/components/status/status-badge";
import { Badge } from "@/components/ui/badge";
import { DESKS } from "@/lib/data/desks";
import { formatScore, localizeDigits } from "@/lib/formatters/numbers";

/**
 * AI INTELLIGENCE — an honest summary of what the sample model currently
 * ranks highest. No chat, no fabricated answers: only desk data restated.
 */
export function AiIntelligencePrompt({ className }: { className?: string }) {
  const { dict, locale } = useLocale();

  const top = DESKS.filter((d) => d.score.value !== null).sort(
    (a, b) => (b.score.value?.value ?? 0) - (a.score.value?.value ?? 0),
  )[0];
  const topScore = top?.score.value?.value ?? 0;
  const topSignal = top?.signal.value ?? "UNKNOWN";

  return (
    <HudCard
      icon={Bot}
      title="AI Intelligence"
      titleFa={dict.command.aiTitle}
      className={className}
      badge={<StatusBadge status="SAMPLE" size="sm" />}
    >
      <div className="flex items-start gap-2.5">
        <span aria-hidden className="mt-0.5 grid size-7 shrink-0 place-items-center rounded-xl border border-violet/40 bg-violet/10 text-[10px] font-extrabold text-violet">
          AI
        </span>
        <p className="text-[11px] leading-relaxed text-foreground/90">
          {dict.command.aiSummaryPrefix}{" "}
          <span className="font-bold text-primary">{top?.name[locale]}</span>{" "}
          <span className="tnum font-latin" dir="ltr">
            ({formatScore(topScore, locale)})
          </span>{" "}
          — {dict.command.aiSignalLabel}: <span className="font-bold">{topSignal}</span>.{" "}
          {dict.command.aiDisclaimer}
        </p>
      </div>
      <div className="mt-2.5 flex flex-wrap items-center gap-1.5 border-t border-border/50 pt-2.5">
        <Badge variant="muted" className="text-[9px]">
          {localizeDigits(String(DESKS.length), locale)} {dict.nav.desks}
        </Badge>
        <Badge variant="muted" className="text-[9px]">
          {dict.common.paperOnly}
        </Badge>
      </div>
    </HudCard>
  );
}

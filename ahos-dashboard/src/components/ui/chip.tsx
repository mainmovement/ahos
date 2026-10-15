import type { ComponentType, ReactNode, SVGProps } from "react";
import { cn } from "@/lib/utils";

export type ChipTone = "gold" | "up" | "down" | "warn" | "info" | "violet" | "slate" | "demo" | "data" | "muted";

const TONES: Record<ChipTone, string> = {
  gold: "text-gold-200 bg-gold-400/10 border-gold-400/30",
  up: "text-up bg-up/10 border-up/30",
  down: "text-down bg-down/10 border-down/35",
  warn: "text-warn bg-warn/10 border-warn/35",
  info: "text-info bg-info/10 border-info/30",
  violet: "text-violet bg-violet/10 border-violet/30",
  slate: "text-slate bg-slate/10 border-slate/25",
  demo: "text-status-demo bg-status-demo/[0.06] border-status-demo/40 border-dashed",
  data: "text-data-300 bg-data-400/10 border-data-400/30",
  muted: "text-fg-3 bg-white/[0.03] border-white/10",
};

export interface ChipProps {
  tone?: ChipTone;
  icon?: ComponentType<SVGProps<SVGSVGElement>>;
  children: ReactNode;
  size?: "xs" | "sm";
  pulse?: boolean;
  className?: string;
  title?: string;
}

/**
 * Status chip: ALWAYS icon + text so state is never conveyed by colour alone.
 */
export function Chip({ tone = "muted", icon: Icon, children, size = "xs", pulse, className, title }: ChipProps) {
  return (
    <span
      title={title}
      className={cn(
        "inline-flex shrink-0 items-center gap-1 whitespace-nowrap rounded-full border font-medium leading-none",
        size === "xs" ? "h-[18px] px-1.5 text-3xs" : "h-5 px-2 text-2xs",
        TONES[tone],
        className,
      )}
    >
      {Icon && (
        <span className="relative inline-flex">
          {pulse && <span aria-hidden className="absolute inset-0 rounded-full bg-current opacity-60 animate-ping-slow motion-off:hidden" />}
          <Icon aria-hidden className={size === "xs" ? "relative size-2.5" : "relative size-3"} strokeWidth={2.4} />
        </span>
      )}
      <span className="tracking-wide">{children}</span>
    </span>
  );
}

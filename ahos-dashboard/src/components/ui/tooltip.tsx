"use client";

import type { ReactNode } from "react";
import { Tooltip as T } from "radix-ui";
import { cn } from "@/lib/utils";

export const TooltipProvider = T.Provider;

interface TipProps {
  content: ReactNode;
  children: ReactNode;
  side?: "top" | "bottom" | "left" | "right";
  align?: "start" | "center" | "end";
  className?: string;
  delay?: number;
}

/** Accessible tooltip (Radix). The trigger must be focusable. */
export function Tip({ content, children, side = "top", align = "center", className, delay }: TipProps) {
  if (content === null || content === undefined || content === "") return <>{children}</>;
  return (
    <T.Root delayDuration={delay ?? 250}>
      <T.Trigger asChild>{children}</T.Trigger>
      <T.Portal>
        <T.Content
          side={side}
          align={align}
          sideOffset={6}
          collisionPadding={10}
          className={cn(
            "glass-strong gold-border z-50 max-w-[280px] rounded-[var(--radius-md)] px-2.5 py-1.5 text-xs leading-relaxed text-fg-2 data-[state=delayed-open]:animate-fade-in",
            className,
          )}
        >
          {content}
        </T.Content>
      </T.Portal>
    </T.Root>
  );
}

"use client";

import { forwardRef, type ComponentPropsWithoutRef, type ElementRef } from "react";
import { Popover as P } from "radix-ui";
import { cn } from "@/lib/utils";

export const Popover = P.Root;
export const PopoverTrigger = P.Trigger;
export const PopoverClose = P.Close;

export const PopoverContent = forwardRef<ElementRef<typeof P.Content>, ComponentPropsWithoutRef<typeof P.Content>>(function PopoverContent(
  { className, align = "end", sideOffset = 8, ...props },
  ref,
) {
  return (
    <P.Portal>
      <P.Content
        ref={ref}
        align={align}
        sideOffset={sideOffset}
        collisionPadding={10}
        className={cn("glass-strong gold-border z-50 rounded-[var(--radius-lg)] text-sm text-fg-2 shadow-[var(--shadow-pop)] outline-none animate-fade-in", className)}
        {...props}
      />
    </P.Portal>
  );
});
